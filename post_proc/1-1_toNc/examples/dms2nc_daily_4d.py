#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
from pytools import timetools as tt
from pytools import dmstools as dmst
from pytools import nctools as nct
import numpy as np
import os


def main():
    for initTime in [
        tt.format2float(d, '%Y%m%d') for d in [
            '20010125', '20090126',
        ]
    ]:
        for caseName in [
            'DEVA17', 'M14SGSKHPF', 'DEVA17PS9', 'M14SGSKHPS9'
        ]:
            run(initTime, caseName)


def run(initTime, caseName):
    #
    # ---- settings
    srcDirRoot = './src'
    dmsSuffix = 'GI0GR1191936'
    gridPath = '/nwpr/gfs/com120/9_data/models/griddes/TCo383_lonlat.nc'

    desDir = './nc/day'

    leads = list(range(0, 1080, 6))
    levels = [100, 200, 300, 500, 700, 850, 925, 1000]
    varNames = ['u', 'v', 'w', 't', 'q',]# 'z']

    def subrun(varName):
        print(varName, end=' ', flush=True)
        srcDir = tt.float2format(
            initTime, 
            f'{srcDirRoot}/{caseName}/OS_exp%Y%m%d%H',
        )
        desPath = tt.float2format(
            initTime,
            f'{desDir}/{caseName}/%y%m%d/{varName}.nc'
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

        print(f'reading {varName}..', flush=True, end='')
        data = dmst.readNd(paths, shape, precision='single')
        data = np.reshape( # for day mean
            data, (4, int(shape[0]/4), *shape[1:])
        )
        data = np.mean(data, 0)

        print('saving..', flush=True, end='')
        nct.save(
            desPath,
            {
                varName: data,
                'time': [initTime + lead/24 for lead in leads[::4]],
                'lev': levels,
                'lat': lat,
                'lon': lon,
            },
            overwrite=True,
        )
        print('finished.')

    for varName in varNames:
        subrun(varName)

if __name__ == '__main__':
    main()
