#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import pytools as pyt
import numpy as np
import os
import traceback

def main():
    for modelName, numMembers in [
        ('CWA_GEPSv3', 21),
        ('CWA_GEPSv2', 33),
    ]:
        run(modelName, numMembers)


def run(modelName, numMembers):
    # settings
    data_dir = '../../data/processed'

    initTime0 = pyt.tt.ymd2float(2025, 1, 1)
    numInits = 90

    dataType = 'global_daily_1p0'
    varNames = [
        'u10', 'v10', 't2m', 'prec', 'olr', 'pw', 'mslp',
        'u', 'v', 't', 'q', 'r', 'z',
    ]

    # auto settings
    initTimes = [initTime0 + d for d in range(numInits)]
    members = list(range(numMembers))


    def run(initTime, varName):
        # create dummy output path
        srcPath = get_path(data_dir, modelName, initTime, 0, dataType, varName)
        desPath = get_path(data_dir, modelName, initTime, -numMembers, dataType, varName)
        tmpPath = './tmp.nc'


        if os.path.exists(desPath):
            print(f'output path already exists {desPath}')
            return

        desDir = os.path.dirname(desPath)
        if not os.path.exists(desDir):
            os.system(f'mkdir -p {desDir}')

        if not os.access(desDir, os.W_OK):
            print(f'permission denied to write to {desDir}')
            return

        # let's write to tmpPath first. only copy the file to destination after complete success.
        os.system(f'cp {srcPath} {tmpPath}')

        ndim = get_ndim(varName)
        minMaxs = [[None]*2]*ndim

        # read data
        data, dims = pyt.modelreader.readTotal.readTotal(
            modelName, dataType, varName, minMaxs, [initTime],
            members, rootDir=data_dir,
        )

        if data is None:
            print('[fatal] No data is read')
            return

        data = np.squeeze(data, axis=0)         # init time
        dataEnsMean = np.nanmean(data, axis=0)  # ensemble

        # write, copy tmp to des, delete tmp
        pyt.nct.write(tmpPath, varName, dataEnsMean)
        os.system(f'cp {tmpPath} {desPath}')
        os.system(f'rm {tmpPath}')
    

    # main loop
    for initTime in initTimes:
        print(pyt.tt.float2format(initTime), end='..')
        for varName in varNames:
            print(varName, end='..')
            try:
                run(initTime, varName)
            except Exception:
                traceback.print_exc()
        print('')


def get_ndim(varName):
    if varName in ['u', 'v', 't', 'q', 'r', 'z']:
        return 4
    else:
        return 3


def get_path(data_dir, modelName, initTime, member, dataType, varName):
    return pyt.tt.float2format(
        initTime,
        f'{data_dir}/{modelName}/%Y/%m/%dz%H/E{member:03d}/{dataType}_{varName}.nc'
    )

if __name__ == '__main__':
    main()
