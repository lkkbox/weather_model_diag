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
    run(pyt.tt.ymd2float(2024, 9, 3), pyt.tt.ymd2float(2025, 1, 1))


def run(dateStart, dateEnd):
    #
    # ---- init
    lats, latn = -15, 15
    LON = np.r_[0:360:2.5]
    obsRoot = '../../../data/obs'
    desRoot = '../../../data/MJO/mermean_15NS/obs'

    if pyt.tt.year(dateStart) <= 2020:
        era5_source = 'era5_prs_daymean'
    else:
        era5_source = 'era5_prs_daymean_nrt'

    dataSource = {
        'olr': None,
        'u': era5_source,
    }
    varNames = ['olr', 'u850', 'u200']

    # ---- auto settings
    fp = pyt.tmt.FlushPrinter()
    dates = np.r_[dateStart:dateEnd+1]

    #
    # ---- post init
    fp.print(f'> running {pyt.ft.getModuleName()}')
    fp.print(f'  dates = {"-".join([pyt.tt.float2format(dates[i]) for i in [0, -1]])}')

    if not os.path.exists(desRoot):
        os.system(f'mkdir -p {desRoot}')

    if not os.access(desRoot, os.W_OK):
        raise PermissionError(f'denied to write to {desRoot}')

    #
    # ---- core
    def readcalsave(date, varName):
        fp.flush(f'running {pyt.tt.float2format(date)} {varName} ')
        desPath = pyt.tt.float2format(date, f'{desRoot}/%Y/%y%m%d_{varName}.nc')
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
        if varName == 'olr': # date + 0.99 to include the time of daymean
            ncVarName = 'olr'
            minMaxs = [[date, date+0.99], [lats, latn], [None]*2]
        elif varName == 'u850':
            ncVarName = 'u'
            minMaxs = [[date, date+0.99], [850]*2, [lats, latn], [None]*2]
        elif varName == 'u200':
            ncVarName = 'u'
            minMaxs = [[date, date+0.99], [200]*2, [lats, latn], [None]*2]

        #
        # ---- read data
        try:
            data, dims = pyt.rt.obsReader.anomaly(
                ncVarName, minMaxs, dataSource[ncVarName], root=obsRoot,
            )
        except ValueError:
            fp.appendPrint(f'skipping because date not found in files')
            return
        except FileNotFoundError:
            fp.appendPrint(f'skipping because file not found')
            return

        # fix it: NOAA OLR data is corrupted on 2024-02-01
        if date == pyt.tt.ymd2float(2024, 2, 1) and varName == 'olr':
            tmp, _ = pyt.rt.obsReader.anomaly(
                ncVarName,
                [[pyt.tt.ymd2float(2024, 1, 31), pyt.tt.ymd2float(2024, 2, 2)], *minMaxs[1:]],
                dataSource[ncVarName], root=obsRoot,
            )
            data[0, :] = (tmp[0, :] + tmp[-1, :]) / 2

        if ncVarName == 'u': # remove level
            data = np.squeeze(data, -3)
            dims = [dims[i] for i in [0, 2, 3]]

        data = np.nanmean(data, axis=-2) # meridional mean
        data = pyt.ct.interp_1d(dims[-1], data, LON, axis=-1, extrapolate=True)

        pyt.nct.save(
            desPath, {
                varName: data,
                'time': [date],
                'lon':LON,
            }
        )

    # ---- loop over the core
    for date in dates:
        for varName in varNames:
            readcalsave(date, varName)

    fp.print(f'< exiting {pyt.ft.getModuleName()}')


if __name__ == '__main__':
    main()

