#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
from pytools import timetools as tt
from pytools import dmstools as dmst
from pytools import nctools as nct
from pytools import caltools as ct
import numpy as np
import os


def main():
    for initTime in [
        tt.format2float(d, '%Y%m%d') for d in [
            # '20010125',
            '20090126',
        ]
    ]:
        for caseName in [
            'DEVM21',
            'DEVM21S9',
            'M22G3IKH',
            'M22G3IKHS9',
        ]:
            run(initTime, caseName, iMember=0)


def run(initTime, caseName, iMember):
    #
    # ---- settings
    srcDirRoot = '/nwpr/gfs/com120/9_data/models/exp/MJO/run250528/'
    dmsSuffix = 'GI0GR1191936'
    gridPath = '/nwpr/gfs/com120/9_data/models/griddes/TCo383_lonlat.nc'
    desDir = f'../../../data/processed/{caseName}'
    varNames = ['u10', 'v10', 't2m', 'prec', 'olr'] #, 'pw', 'mslp']
    dmsPrecision = 'single'

    #
    # ---- constants
    LON = np.r_[0:360]
    LAT = np.r_[-90:90+1]

    def subrun(varName):
        print(varName, end=' ', flush=True)

        if varName in ['prec', 'olr']:
            leads = list(range(24, 1080, 24))
        else:
            leads = list(range(0, 1080, 6))

        srcDir = tt.float2format(
            initTime, 
            f'{srcDirRoot}/{caseName}/OS_exp%Y%m%d%H',
        )
        desPath = tt.float2format(
            initTime,
            f'{desDir}/%Y/%m/%dz%H/E{iMember:03d}/global_daily_1p0_{varName}.nc'
        )

        if os.path.exists(desPath):
            print(f'file already exists: {desPath}')
            return

        if not os.path.exists(os.path.dirname(desPath)):
            os.system(f'mkdir -p $(dirname {desPath})')

        if not os.access(os.path.dirname(desPath), os.W_OK):
            print(f'permission dinied to write {os.path.dirname(desPath)}')
            return
        
        lon = nct.read(gridPath, 'lon')
        lat = nct.read(gridPath, 'lat')
        shape = (len(leads), len(lat), len(lon),)

        dmsPrefix = dmst.varName2dmsPrefix(varName)
        paths = [
            tt.float2format(
                initTime,
                f'{srcDir}/%Y%m%d%H%M{lead:04d}/{dmsPrefix}{dmsSuffix}',
            )
            for lead in leads
        ]

        print(f'reading..', flush=True, end='')
        data = dmst.readNd(paths, shape, precision=dmsPrecision)
        if varName not in ['prec', 'olr']:
            data = np.reshape( # for day mean
                data, (4, int(shape[0]/4), *shape[1:])
            )
            data = np.mean(data, 0)
            time = [initTime + lead/24 for lead in leads[::4]]
        else:
            time = [initTime + lead/24 for lead in leads]

        print('interpolating..', flush=True, end='')
        data = ct.interp_1d(lon, data, LON, -1, True)
        data = ct.interp_1d(lat, data, LAT, -2, True)

        print('saving..', flush=True, end='')
        nct.save(
            desPath,
            {
                varName: data,
                'time': time,
                'lat': LAT,
                'lon': LON,
            },
            overwrite=True,
        )
        print('finished.')

    for varName in varNames:
        subrun(varName)

if __name__ == '__main__':
    main()
