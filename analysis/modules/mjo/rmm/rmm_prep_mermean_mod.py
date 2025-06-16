#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
'''
    We prepare the meridional mean data of 
    OLR, U850, U200 on 2.5 degree over the 
    15S-15N band for calculating RMM indices.
'''
import pytools as pyt
import numpy as np
import os


def main():
    modelName = 'CWA_GEPSv3'
    initTimes = [
        pyt.tt.ymd2float(2025, 1, 1) + i
        for i in range(90)
    ]
    members = list(range(21))
    run(modelName, initTimes, members)


def run(modelName, initTimes, members, dataDir, climYears=[2006, 2020]):
    #
    # ---- init
    # settings
    processedRoot = f'{dataDir}/processed'
    desRoot = f'{dataDir}/MJO/mermean_15NS/{modelName}'

    # const
    dataType = 'global_daily_1p0'
    lats, latn = -15, 15
    LON = np.r_[0:360:2.5]
    varNames = ['olr', 'u850', 'u200']

    #
    # ---- post init
    fp = pyt.tmt.FlushPrinter()
    fp.print(f'> running {pyt.ft.getModuleName()}')

    if not os.path.exists(desRoot):
        os.system(f'mkdir -p {desRoot}')

    if not os.access(desRoot, os.W_OK):
        raise PermissionError(f'denied to write to {desRoot}')

    #
    # --- core
    def readcalsave(initTime, iMember, varName):
        fp.flush(f'running {
            pyt.tt.float2format(initTime, "%Y%m%d %Hz")
            }, member={iMember}, {varName} ')
        desPath = pyt.tt.float2format(
            initTime,
            f'{desRoot}/%Y/E{iMember:03d}/%y%m%d_{varName}.nc'
        )
        desDir = os.path.dirname(desPath)

        if not os.path.exists(desDir):
            os.system(f'mkdir -p {desDir}')

        if not pyt.ft.canBeWritten(desPath):
            raise PermissionError(f'{desPath}')

        if os.path.exists(desPath):
            fp.print(f'skip existing file {desPath}')
            return

        #
        # ---- variable dependent
        if varName == 'olr':
            ncVarName = 'olr'
            minMaxs = [[None]*2, [lats, latn], [None]*2]
        elif varName == 'u850':
            ncVarName = 'u'
            minMaxs = [[None]*2, [850_00]*2, [lats, latn], [None]*2]
        elif varName == 'u200':
            ncVarName = 'u'
            minMaxs = [[None]*2, [200_00]*2, [lats, latn], [None]*2]

        #
        # ---- read data
        data, dims = pyt.modelreader.readAnomaly.readAnomaly(
            modelName, dataType, ncVarName, minMaxs, [initTime], [iMember],
            climYears=climYears, rootDir=processedRoot
        )
        if data is None:
            return

        data = np.squeeze(data, axis=(0, 1)) # initTime and member dimension

        if ncVarName == 'u': # remove level
            data = np.squeeze(data, -3)
            dims = [dims[i] for i in [0, 2, 3]]

        data = np.nanmean(data, axis=-2) # meridional mean
        data = pyt.ct.interp_1d(dims[-1], data, LON, axis=-1, extrapolate=True)

        pyt.nct.save(
            desPath, {
                varName: data,
                'time': [initTime + lead for lead in dims[0]],
                'lon':LON
            }
        )

    #
    # --- loop over the core
    for initTime in initTimes:
        for iMember in members:
            for varName in varNames:
                readcalsave(initTime, iMember, varName)

    fp.print(f'< exiting {pyt.ft.getModuleName()}')


if __name__ == '__main__':
    main()

