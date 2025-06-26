import numpy as np
import pytools as pyt


def get_mapper():
    return {
        'div2d_lonlat': div2d_lonlat,
        'vertical_pressure_mean': vertical_mean,
        'vertical_pressure_integration': vertical_inegration,
        'mask_by_surface_pressure': mask_by_surface_pressure,
        'time_tendency': time_tendency,
    }


def time_tendency(data, dims, data2):
    data = np.gradient(data, axis=0)
    if data2 is not None:
        data2 = np.gradient(data2, axis=0)
    return data, data2

def div2d_lonlat(data, dims, data2):
    dx, dy = pyt.ct.lonlat2dxdy(dims[-1], dims[-2])
    divu = np.gradient(data, axis=-1) / dx
    divv = np.gradient(data2, axis=-2) / dy
    return divu + divv, None
    

def vertical_mean(data, dims, data2):
    '''
    use hPa as the pressure unit
    '''
    DLEV = _calDLEV(dims)
    data = np.nansum(data * DLEV, axis=-3, keepdims=True) / np.nansum(DLEV, axis=-3, keepdims=True)
    if data2 is not None:
        data2 = np.nansum(data2 * DLEV, axis=-3, keepdims=True) / np.nansum(DLEV, axis=-3, keepdims=True)

    return data, data2

def vertical_inegration(data, dims, data2):
    '''
    use hPa as the pressure unit
    '''
    DLEV = _calDLEV(dims)
    data *= DLEV
    if data2 is not None:
        data2 *= DLEV
    return data, data2


def mask_by_surface_pressure(data, dims, data2):
    sp = _read_clim_sp(dims)
    ny, nx = sp.shape
    lev = np.tile(dims[-3][:, None, None], (1, ny, nx))
    data[np.tile((lev > sp), (len(dims[0]), 1, 1, 1))] = np.nan
    if data2 is not None:
        data2[(lev > sp)] = np.nan
    return data, data2


def _calDLEV(dims):
    sp = _read_clim_sp(dims)
    ny, nx = sp.shape
    lev = dims[-3]

    dlev = np.diff(lev)
    dlev = np.array([dlev[0], *(dlev[1:]+dlev[:-1]), dlev[-1]])/2

    DLEV = np.tile(dlev[:, None, None], (1, ny, nx))

    for ilev, level in enumerate(lev):
        mask = level > sp
        DLEV[ilev][mask] = 0.

        if ilev == 0:
            continue

        mask2 = ((lev[ilev - 1] < sp) & mask)
        DLEV[ilev-1][mask2] += sp[mask2] - \
            (lev[ilev-1] + lev[ilev])/2

    mask2 = (lev[-1] < sp)
    DLEV[-1][mask2] += sp[mask2] - lev[-1]

    return DLEV


def _read_clim_sp(dims):
    minMaxs = [
        [None, None],
        [float(s + d) for s, d in zip([-2, 2], [dims[-2][0], dims[-2][-1]])],
        [float(s + d) for s, d in zip([-2, 2], [dims[-1][0], dims[-1][-1]])],
    ]
    path = '/nwpr/gfs/com120/9_data/ERA5/clim_mon/era5_sp_clim_2001_2020_01.nc'
    sp, dims_sp = pyt.nct.ncreadByDimRange(path, 'sp', minMaxs, decodeTime=False)
    sp = np.squeeze(sp)
    dims = dims[1:] # get rid of time dimension

    for iDim in [-1, -2]:
        sp = pyt.ct.interp_1d(dims_sp[iDim], sp, dims[iDim], axis=iDim)

    return sp
