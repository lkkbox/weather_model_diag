#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
'''
    calculate the RMM indices from the mermean data
'''
from sys import exception
from RMM_Tool import RMM_Tool
import pytools as pyt
import numpy as np
import os


def main():
    dateStart = pyt.tt.ymd2float(2025, 1, 1)
    dateEnd = pyt.tt.ymd2float(2025, 1, 1)
    run(dateStart, dateEnd)


def run(dateStart, dateEnd):
    # ---- constants
    numPrevDays = 120 # we need the previous 120 days to calculate the indices
    srcRoot = '../../../data/MJO/mermean_15NS/obs'
    desRoot = '../../../data/MJO/RMM/obs'
    rmm_tool = RMM_Tool()

    # ---- auto settings
    dates = np.r_[dateStart:dateEnd+1]

    # ---- post init
    fp = pyt.tmt.FlushPrinter()
    fp.print(f'> running {pyt.ft.getModuleName()}')
    fp.print(f'  dates = {"-".join([pyt.tt.float2format(dates[i]) for i in [0, -1]])}')

    if not os.path.exists(desRoot):
        os.system(f'mkdir -p {desRoot}')

    if not os.access(desRoot, os.W_OK):
        raise PermissionError(f'denied to write to {desRoot}')

    #
    # --- core
    def readcalsave(date):
        fp.flush(f'running {pyt.tt.float2format(date)} ')
        desPath = pyt.tt.float2format(date, f'{desRoot}/%Y/%y%m%d_RMM.nc')
        desDir = os.path.dirname(desPath)

        if not os.path.exists(desDir):
            os.system(f'mkdir -p {desDir}')

        if not pyt.ft.canBeWritten(desPath):
            raise PermissionError(f'{desPath}')

        if os.path.exists(desPath):
            fp.print(f'skip existing file {desPath}')
            return

        timeStart = date - 120
        timeEnd = date

        def read(varName):
            paths = [
                pyt.tt.float2format(date, f'{srcRoot}/%Y/%y%m%d_{varName}.nc')
                for date in np.r_[timeStart:timeEnd+1]
            ]
            for path in paths:
                if not os.path.exists(path):
                    fp.appendPrint(
                        f'skip because file not found for reading {varName}' \
                        + f' {"-".join([pyt.tt.float2format(d) for d in [timeStart, timeEnd]])}'
                    )
                    return None, None

            data, dims = pyt.rt.multiNcRead.read(
                paths, varName, [[timeStart, timeEnd], [None]*2], stackedAlong=0
            )
            return data, dims

        olr, dims = read('olr')
        if olr is None: return

        u850, dims = read('u850')
        if u850 is None: return

        u200, dims = read('u200')
        if u200 is None: return

        pc1, pc2 = rmm_tool.get_pcs(olr, u850, u200)

        pc1 = pc1[numPrevDays:]
        pc2 = pc2[numPrevDays:]
        time = dims[0][numPrevDays:]

        for varName, data in zip(['pc1', 'pc2'], [pc1, pc2]):
            pyt.nct.save(
                desPath, {
                    varName: data,
                    'time': time,
                },
                overwrite=True
            )


    #
    # --- loop over the core
    for date in dates:
        readcalsave(date)

    fp.print(f'< exiting {pyt.ft.getModuleName()}')


if __name__ == '__main__':
    main()

