#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
''' 
    calculate the climatology for experiment
    using reforecast as baseline and add on the gap with the control experiment
    clim_exp = clim_reforecast + 5-days_smoothed(control - reforecast)@initTime

    - read reforecast climate
    - read reforecast run
    - read control run
    - calculate
    - save

    clim years is now hard coded as 2001-2020
'''
import pytools as pyt
import numpy as np
import os

def main():
    for varname, ndim in [
        ('u', 4),
        ('v', 4),
        ('w', 4),
        ('q', 4),
        ('olr', 3),
        ('prec', 3),
    ]:
        run(varname, ndim)

def run(varname, ndim):
    dataRootDir = '../../data/processed'
    initTime = pyt.tt.ymd2float(2001, 1, 25)
    ctl_name = 'exp_mjo-DEVM21' # adjusting target
    rfc_name = 're_GEPSv3_CFSR' # base line
    iMember = 0
    climYears = [2001, 2020]
    climType = '5dma'

    # constants
    numSmooths = 5 # steps
    dataType = 'global_daily_1p0'
    dimNames = ['lead', 'plev', 'lat', 'lon']

    # read reforecast clim
    rfc_clim_data, rfc_clim_dims = pyt.modelreader.readModelClim.readModelClim(
        rfc_name, dataType, varname, [[None]*2]*ndim, [initTime], [iMember],
        rootDir=dataRootDir, climYears=climYears, climType=climType
    )

    # read reforecast run
    rfc_run_data, rfc_run_dims = pyt.modelreader.readTotal.readTotal(
        rfc_name, dataType, varname, 
        [[None]*2]*ndim, [initTime], [iMember], rootDir=dataRootDir
    )

    # read control run
    ctl_data, ctl_dims = pyt.modelreader.readTotal.readTotal(
        ctl_name, dataType, varname, 
        [[None]*2]*ndim, [initTime], [iMember], rootDir=dataRootDir
    )

    # pop out inittime and member dimension
    rfc_clim_data = rfc_clim_data.squeeze(axis=(0, 1))
    rfc_run_data = rfc_run_data.squeeze(axis=(0, 1))
    ctl_data = ctl_data.squeeze(axis=(0, 1))

    # regridding
    rfc_clim_data = conform_grids(rfc_clim_data, rfc_clim_dims, ctl_dims)
    rfc_run_data = conform_grids(rfc_run_data, rfc_run_dims, ctl_dims)

    # calculating
    corrected_clim = rfc_clim_data + pyt.ct.smooth(ctl_data - rfc_run_data, numSmooths, axis=0)

    # save output
    desDir = f'{dataRootDir}/{ctl_name}/clim/E{iMember:03d}/5dma/{varname}'
    desName = f'{dataType}_{varname}_%m%d_{"_".join([str(y) for y in climYears])}_5dma.nc'
    desPath = pyt.tt.float2format(initTime, f'{desDir}/{desName}')
    if not os.path.exists(desDir):
        os.system(f'mkdir -p {desDir}')

    if ndim == 4:
        idims = [0, 1, 2, 3]
    else:
        idims = [0, 2, 3]
    pyt.nct.save(
        desPath, {
            varname: corrected_clim,
            **{dimNames[idim]: dimVal for idim, dimVal in zip(idims, ctl_dims)},
        }, overwrite=True
    )



def conform_grids(data_from, dims_from, dims_to):
    if data_from.ndim == 4:
        space_dims = [-1, -2, -3]
    elif data_from.ndim == 3:
        space_dims = [-1, -2]

    for idim in space_dims:
        data_from = pyt.ct.interp_1d(dims_from[idim], data_from, dims_to[idim], idim, True)

    nt_from = len(dims_from[0])
    nt_to = len(dims_to[0])

    if nt_from > nt_to:
        data_from = data_from[:nt_to, :]
    else:
        padding_shape = (nt_to - nt_from, *data_from.shape[1:])
        data_from = np.concatenate(
            (data_from, np.nan * np.ones(padding_shape)),
            axis=0
        )

    return data_from



     # ../../../data/processed/exp_mjo-DEVM21/2009/01/26z00/E000/global_daily_1p0_u.nc


if __name__ == '__main__':
    main()
