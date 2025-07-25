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
    members = 21
    run(modelName, initTimes, members)


def run(modelName, initTimes, members):
    #
    # ---- init
    # settings
    processedRoot = '../../../data/processed'
    desRoot = f'../../../data/MJO/mermean_15NS/{modelName}-noBC'
    climYears = [2001, 2020]

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
            obsSource = None
            minMaxsObs = [[None]*2, [lats, latn], [None]*2]
            minMaxsMod = minMaxsObs
        elif varName == 'u850':
            ncVarName = 'u'
            obsSource = 'era5_prs_daymean'
            minMaxsObs = [[None]*2, [850]*2, [lats, latn], [None]*2]
            minMaxsMod = [[None]*2, [850_00]*2, [lats, latn], [None]*2]
        elif varName == 'u200':
            ncVarName = 'u'
            minMaxsObs = [[None]*2, [200]*2, [lats, latn], [None]*2]
            minMaxsMod = [[None]*2, [200_00]*2, [lats, latn], [None]*2]
            obsSource = 'era5_prs_daymean'

        def shapeManipulation(data, dims):
            if ncVarName == 'u': # remove level
                data = np.squeeze(data, -3)
                dims = [dims[i] for i in [0, 2, 3]]
            data = np.nanmean(data, axis=-2) # meridional mean
            data = pyt.ct.interp_1d(dims[-1], data, LON, axis=-1, extrapolate=True)
            return data, dims

        #
        # ---- read  model data
        data, dims = pyt.modelreader.readTotal.readTotal(
            modelName, dataType, ncVarName, minMaxsMod, [initTime], [iMember], rootDir=processedRoot
        )
        if data is None:
            return

        data = np.squeeze(data, axis=(0, 1)) # initTime and member dimension
        data, dims = shapeManipulation(data, dims)


        #
        # ---- read obs clim data
        validDates = [int(initTime + lead) for lead in dims[0]]
        minMaxsObs[0] = [min(validDates), max(validDates)]
        clim, dimsClim = pyt.rt.obsReader.clim(ncVarName, minMaxsObs, obsSource, climYears=climYears)
        clim, dimsClim = shapeManipulation(clim, dimsClim)

        #
        # ---- calculate anomalies
        climTime = list(dimsClim[0])
        iDateClim = [climTime.index(pyt.tt.dayOfYear229(vd)-1) for vd in validDates]
        data -= clim[iDateClim, :]

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

