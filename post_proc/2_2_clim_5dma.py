#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import pytools.timetools as tt
from pytools.modelreader.readModelClim import readModelClim
from pytools.filetools import canBeWritten
from pytools.nctools import save
import os
import numpy as np


def main():
    model = 're_GEPSv3_CFSR'
    member = 0
    dataType = 'global_daily_1p0'
    climYears = (2006, 2020)
    for varName in [
         't2m', 'mslp', 'u', 'z',
         't2m', 'u10', 'v10', 'mslp', 'prec', 'olr',
         'u', 'v', 't', 'q', 'z',
    ]:
        for iDay in range(31):
            print(f'-- {varName=}, {iDay+1=}')
            initTime = tt.ymd2float(2001, 1, 1) + iDay
            run(model, member, dataType, varName, initTime, climYears)


def run(model, member, dataType, varName, initTime, climYears):
    def getPath(date, climType): return tt.float2format(
        date, f'/nwpr/gfs/com120/9_data/models/processed/{model}/clim/'
        f'E{member:03d}/{climType}/{varName}/{dataType}_{varName}_'
        f'%m%d_{'_'.join([str(y) for y in climYears])}_{climType}.nc'
    )

    def getNumDims():
        if varName in ['u10', 'v10', 't2m', 'pw', 'mslp', 'prec', 'olr', 'u850']:
            return 3
        elif varName in ['u', 'v', 't', 'q', 'z', 'w']:
            return 4
        else:
            raise ValueError(f'unrecognized {varName=}')
    #
    # ---- input settings
    #
    numDims = getNumDims()
    minMaxs = [[-np.inf, np.inf]]*numDims
    initTimes = [initTime + delta for delta in [-2, -1, 0, 1, 2]]

    #
    # ---- output settings
    #
    desPath = getPath(initTime, '5dma')

    if os.path.isfile(desPath):
        print(f' output file already exists, manually delete it to proceed:')
        print(f'   del {desPath}')
        return

    if not os.path.exists(os.path.dirname(desPath)):
        os.system(f'mkdir -p {os.path.dirname(desPath)}')

    if not canBeWritten(desPath):
        print(f'permission denied to write to {desPath}')
        return

    #
    # ---- read data
    #
    data, dims = readModelClim(
        model,
        dataType,
        varName,
        minMaxs,
        initTimes,
        [member],
        climYears,
        climType='1day',
    )
    data = np.squeeze(data, axis=1)  # pop away member
    data = np.nanmean(data, 0)

    #
    # ---- save output
    #
    if numDims == 3:
        dimNames = ['lead', 'lat', 'lon']
    elif numDims == 4:
        dimNames = ['lead', 'plev', 'lat', 'lon']
    save(
        desPath,
        {
            varName: data,
            **{dimName: dimVal for dimName, dimVal in zip(dimNames, dims)}
        }
    )


if __name__ == '__main__':
    main()
