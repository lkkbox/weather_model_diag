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

    # ---- begins -- read data
    minMaxTime = [caseDate, caseDate + numDates - 0.01]
    minMaxs = [minMaxTime, [levelTop, 1000], area[2:], area[:2]]
    uTotal, uClim, uAnom, dims = readData('u', minMaxs)
    vTotal, vClim, vAnom, dims = readData('v', minMaxs)
    wTotal, wClim, wAnom, dims = readData('w', minMaxs)
    qTotal, qClim, qAnom, dims = readData('q', minMaxs)

    time, lev, lat, lon = dims
    dy, dx = pyt.ct.lonlat2dxdy(lon, lat)
    dlev = np.gradient(lev)[:, None, None]

    totalAdvTotal = np.nan * np.ones((3, *uTotal.shape))
    for iCoord, (wind, axis, coord) in enumerate(zip(
        (uTotal, vTotal, wTotal),
        (-1,     -2,     -3),
        (dx,     dy,     dlev),
    )):
        totalAdvTotal[iCoord, :] = wind * np.gradient(qTotal, axis=axis) / coord

    anomAdvTotal = np.nan * np.ones((3, *uTotal.shape))
    for iCoord, (wind, axis, coord) in enumerate(zip(
        (uAnom, vAnom, wAnom),
        (-1,    -2,    -3),
        (dx,    dy,    dlev),
    )):
        anomAdvTotal[iCoord, :] = wind * np.gradient(qTotal, axis=axis) / coord

    totalAdvAnom = np.nan * np.ones((3, *uTotal.shape))
    for iCoord, (wind, axis, coord) in enumerate(zip(
        (uTotal, vTotal, wTotal),
        (-1,     -2,     -3),
        (dx,     dy,     dlev),
    )):
        totalAdvAnom[iCoord, :] = wind * np.gradient(qTotal, axis=axis) / coord


    # vTotal, dims = readTotal('v', minMaxs)
    # wTotal, dims = readTotal('w', minMaxs)
    # qTotal, dims = readTotal('q', minMaxs)


    fp.print(f'{uAnom.shape = }')
    
    # print(dims[0])
    # print(uc.shape)


def readData(varName, minMaxs):
    total, dims = readTotal(varName, minMaxs)
    clim = readClim(varName, dims)
    anom = total - clim
    return total, clim, anom, dims


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
