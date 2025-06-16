#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
'''
    calculate the RMM indices from the mermean data
'''
from .RMM_Tool import RMM_Tool
import pytools as pyt
import numpy as np
import os


def main():
    modelName = 'CWA_GEPSv3'
    initTimes = [
        pyt.tt.ymd2float(2025, 1, 1) + i
        for i in range(90)
    ]
    numMembers = list(range(21))
    run(modelName, initTimes, numMembers)


def run(modelName, initTimes, members, dataDir, clim_bc=False):
    #
    # ---- init
    # const
    rmm_tool = RMM_Tool()
    numPrevDays = 120
    srcRootDir = f'{dataDir}/MJO/mermean_15NS'
    srcRootDirObs = f'{srcRootDir}/obs'
    if clim_bc:
        srcRootDirMod = f'{srcRootDir}/{modelName}'
        desRoot = f'{dataDir}/MJO/RMM/{modelName}'
    else:
        srcRootDirMod = f'{srcRootDir}/{modelName}-noBC'
        desRoot = f'{dataDir}/MJO/RMM/{modelName}-noBC'

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
    def readcalsave(initTime, iMember):
        fp.flush(f'running {pyt.tt.float2format(initTime, "%Y%m%d %Hz")}, member={iMember}')
        desPath = pyt.tt.float2format(
            initTime,
            f'{desRoot}/%Y/E{iMember:03d}/%y%m%d_RMM.nc'
        )
        desDir = os.path.dirname(desPath)

        if not os.path.exists(desDir):
            os.system(f'mkdir -p {desDir}')

        if not pyt.ft.canBeWritten(desPath):
            raise PermissionError(f'{desPath}')

        if os.path.exists(desPath):
            fp.print(f'skip existing file {desPath}')
            return

        timeRangeObs = [initTime - numPrevDays, initTime - 1]


        def modPathsExist():
            paths = [
                pyt.tt.float2format(
                    initTime,
                    f'{srcRootDirMod}/%Y/E{iMember:03d}/%y%m%d_{varName}.nc'
                ) for varName in ['olr', 'u850', 'u200']
            ]
            if not all([os.path.exists(p) for p in paths]):
                return False
            else:
                return True


        def readObs(varName):
            paths = [
                pyt.tt.float2format(date, f'{srcRootDirObs}/%Y/%y%m%d_{varName}.nc')
                for date in np.r_[timeRangeObs[0]:timeRangeObs[1]+1]
            ]

            data, _ = pyt.rt.multiNcRead.read(
                paths, varName, [timeRangeObs, [None]*2], stackedAlong=0
            )
            return data


        def readMod(varName):
            path = pyt.tt.float2format(
                initTime,
                f'{srcRootDirMod}/%Y/E{iMember:03d}/%y%m%d_{varName}.nc'
            )
            data = pyt.nct.read(path, varName)
            return data


        def read(varName):
            mod = readMod(varName)
            obs = readObs(varName)
            return np.concatenate((obs, mod), axis=0)

        if not modPathsExist():
            print('skip because paths are missing')
            return

        olr = read('olr')
        u850 = read('u850')
        u200 = read('u200')

        # remove extra time steps in u
        nt = min([olr.shape[0], u200.shape[0], u850.shape[0]])
        olr = olr[:nt, :]
        u200 = u200[:nt, :]
        u850 = u850[:nt, :]

        pc1, pc2 = rmm_tool.get_pcs(olr, u850, u200)

        pc1 = pc1[numPrevDays:]
        pc2 = pc2[numPrevDays:]
        time = [initTime + i + 1 for i in range(nt - numPrevDays)]

        for varName, data in zip(['pc1', 'pc2'], [pc1, pc2]):
            pyt.nct.save(
                desPath, {
                    varName: data,
                    'time': time,
                },
                overwrite=True
            )
        return

    #
    # --- loop over the core
    for initTime in initTimes:
        for iMember in members:
            readcalsave(initTime, iMember)

    fp.print(f'< exiting {pyt.ft.getModuleName()}')


if __name__ == '__main__':
    main()

