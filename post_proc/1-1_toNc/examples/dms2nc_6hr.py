#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
from pytools import timetools as tt
from pytools import dmstools as dmst
from pytools import nctools as nct
import os


def main():
    #
    # ---- settings
    initTime = tt.ymd2float(2009, 1, 26)
    srcDirRoot = './src'
    caseName = 'DEVA17'
    dmsSuffix = 'GI0GR1191936'
    gridPath = '/nwpr/gfs/com120/9_data/models/griddes/TCo383_lonlat.nc'

    desDir = './nc/6hr'

    leads = list(range(0, 384+1, 6))
    levels = [500, 700, 850, 925, 1000]
    varNames = ['u', 'v', 'w', 'q']

    def run(varName):
        print(varName, end=' ', flush=True)
        srcDir = tt.float2format(
            initTime, 
            f'{srcDirRoot}/{caseName}/%Y%m%d%H',
        )
        desPath = tt.float2format(
            initTime,
            f'{desDir}/{caseName}/%y%m%d/{varName}.nc'
        )

        if os.path.exists(desPath):
            print(f'file already exists: {desPath}')
            return

        if not os.access(os.path.dirname(desPath), os.W_OK):
            print(f'permission dinied to write {os.path.dirname(desPath)}')
            return
        
        lon = nct.read(gridPath, 'lon')
        lat = nct.read(gridPath, 'lat')
        shape = (len(leads), len(levels), len(lat), len(lon),)

        paths = [
            tt.float2format(
                initTime,
                f'{srcDir}/%Y%m%d%H%M{lead:04d}/{dmsPrefix}{dmsSuffix}',
            )
            for lead in leads
            for dmsPrefix in [
                dmst.varName2dmsPrefix(varName, level)
                for level in levels
            ]
        ]

        print(f'reading..', flush=True, end='')
        data = dmst.readNd(paths, shape, precision='single')

        print('saving..', flush=True, end='')
        nct.save(
            desPath,
            {
                varName: data,
                'time': [initTime + lead/24 for lead in leads],
                'lev': levels,
                'lat': lat,
                'lon': lon,
            },
            overwrite=True,
        )
        print('finished.')

    for varName in varNames:
        run(varName)

if __name__ == '__main__':
    main()