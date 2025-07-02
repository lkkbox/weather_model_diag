#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import pytools as pyt
import numpy as np
import os


def main():
    caseDate = pyt.tt.ymd2float(2009, 1, 26)
    numDates = 3
    area = [100, 180, -15, 15]
    levelTop = 700
    overwrite = True

    # ---- check write permission and if the output already exists
    desDirRoot = '/nwpr/gfs/com120/6_weatherModelDiag/data/q_budget/obs'
    if not os.path.exists(desDirRoot):
        raise FileNotFoundError(f'{desDirRoot=}')

    desSubDir = pyt.tt.float2format(caseDate, '%y%m%d')
    desDir = f'{desDirRoot}/{desSubDir}'
    desBaseName = f'a{'_'.join([str(a) for a in area])}_l{levelTop}_d{numDates}.nc'
    desPath = f'{desDir}/{desBaseName}'

    if os.path.exists(desPath) and not overwrite:
        print(f'desPath already exists and overwrite=False. {desPath=}')
        return

    if not os.path.exists(desDir):
        os.makedirs(desDir)

    # ---- begins
    minMaxTime = [caseDate, caseDate + numDates - 0.01]
    minMaxs = [minMaxTime, [levelTop, 1000], area[2:], area[:2]]

    gradClim = [] # ---- read clim grad
    for fluxName in ['uqx', 'vqy', 'wqp']:
        flux, dims = readGradClim(fluxName, minMaxs)
        gradClim.append(flux)
    gradClim = np.array(gradClim)


    windTotal, windClim, windAnom = [], [], [] # ---- read widns
    for varName in ['u', 'v', 'w']:
        total, clim, anom, dims = readVariable(varName, minMaxs)
        windTotal.append(total)
        windClim.append(clim)
        windAnom.append(anom)

    windTotal = np.array(windTotal)
    windClim = np.array(windClim)
    windAnom = np.array(windAnom)


    qTotal, qClim, qAnom, dims = readVariable('q', minMaxs) # ---- read q

    time, lev, lat, lon = dims
    dy, dx = pyt.ct.lonlat2dxdy(lon, lat)
    dlev = np.gradient(lev)[:, None, None]
    dtime = np.gradient(time)[:, None, None, None] / 86400 # ---- per second

    # ---- calculate moisture tendency
    print(qAnom.shape)
    qAnomTend = np.gradient(qAnom, axis=0) / dtime # ---- per second

    # ---- calculate gradient terms
    totalGradTotal = np.nan * np.ones((windTotal.shape))
    anomGradClim = np.nan * np.ones((windTotal.shape))
    climGradAnom = np.nan * np.ones((windTotal.shape))
    for iCoord, (deltaCoord, axis) in enumerate(zip([dx, dy, dlev], [-1, -2, -3])):
        totalGradTotal = windTotal[iCoord, :] * np.gradient(qTotal, axis=axis) / deltaCoord
        anomGradClim = windAnom[iCoord, :] * np.gradient(qClim, axis=axis) / deltaCoord
        climGradAnom = windClim[iCoord, :] * np.gradient(qAnom, axis=axis) / deltaCoord

    anomGradAnom = totalGradTotal - anomGradClim - climGradAnom - gradClim
    q2 = -qAnomTend - anomGradClim - climGradAnom - anomGradAnom



def readVariable(varName, minMaxs):
    total, dims = readTotal(varName, minMaxs)
    clim = readClim(varName, dims)
    anom = total - clim
    return total, clim, anom, dims


def readGradClim(varName, minMaxs):
    fp.flush(f'reading {varName}..')
    if varName not in ['uqx', 'vqy', 'wqp']:
        raise ValueError(f'unrecognized {varName = }')

    root = '/nwpr/gfs/com120/9_data/ERA5/q_budget/clim_5dma'
    dates = np.r_[minMaxs[0][0]:minMaxs[0][1]]
    paths = [
        pyt.tt.float2format(
            date,
            f'{root}/{varName}/ERA5_PRS_{varName}_%m%d.nc'
        )
        for date in dates
    ]

    minMaxs2 = [
        [None, None],
        *minMaxs[1:],
    ]

    data, dims = pyt.rt.multiNcRead.read(paths, varName, minMaxs2, iDimT=0, stackedAlong=0)
    dims[0] = dates

    data = data[:, None, :, :, :]
    data = np.tile(data, (1, 4, 1, 1, 1))
    data = np.reshape(data, (data.shape[0] * data.shape[1], *data.shape[2:]))

    dims[0] = np.r_[dates[0]:dates[-1]+1:0.25]

    data, dims = selectLevels(data, dims)

    return data, dims


def readTotal(varName, minMaxs):
    fp.flush(f'reading total {varName}.. ')
    source = 'era5_prs_6hr'
    data, dims = pyt.rt.obsReader.total(varName, minMaxs, source=source)
    data, dims = selectLevels(data, dims)
    return data, dims


def readClim(varName, dimsTotal):
    fp.flush(f'reading clim {varName}.. ')

    minMaxs = [
        [float(d + s) for d, s in zip([dim[i] for i in [0, -1]], [-2, 2])]
        for dim in dimsTotal
    ]
    source = 'era5_prs_daymean'
    data, dims = pyt.rt.obsReader.clim(varName, minMaxs, source=source)
    data, dims = selectLevels(data, dims)

    # select time axis
    retreivedDates = list(dims[0])
    requestedDates = np.r_[minMaxs[0][0]:minMaxs[0][1]]
    iClims = [retreivedDates.index(pyt.tt.dayOfYear229(r) - 1) for r in requestedDates]
    data = data[iClims, :]
    dims[0] = requestedDates

    # interpolated t, y, x
    for iaxis in [-2, -1, 0]:
        data = pyt.ct.interp_1d(dims[iaxis], data, dimsTotal[iaxis], iaxis)
        dims[iaxis] = dimsTotal[iaxis]

    return data

def selectLevels(data, dims):
    requestedLevs = getRequestedLevs()
    retreivedLevs = list(dims[-3])
    iLevs = [retreivedLevs.index(l) for l in requestedLevs]
    data = data[:, iLevs, :, :]
    dims[-3] = np.array(dims[-3])[iLevs]
    return data, dims


def getRequestedLevs():
    return [700, 850, 925, 1000]


if __name__ == '__main__':
    fp = pyt.tmt.FlushPrinter()
    main()
