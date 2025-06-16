#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
from sys import exception
import pytools as pyt
from cal_scores_noBC import Model, Region, Variable, run


def main():
    # model settings
    initTime0 = pyt.tt.ymd2float(2025, 1, 1)
    numInits = 90
    models = [
        *[
            Model(
                name='NCEP_CTRL',
                iMember=iMember,
                initTime0=initTime0,
                numInits=numInits,
            )
            for iMember in range(1)
        ],
        *[
            Model(
                name='NCEP_ENSAVG',
                iMember=iMember,
                initTime0=initTime0,
                numInits=numInits,
            )
            for iMember in range(1)
        ],
        *[
            Model(
                name='CWA_GEPSv3',
                iMember=iMember,
                initTime0=initTime0,
                numInits=numInits,
            )
            for iMember in range(21)
        ],
        *[
            Model(
                name='CWA_GEPSv2',
                iMember=iMember,
                initTime0=initTime0,
                numInits=numInits,
            )
            for iMember in range(33)
        ],
    ]

    # variable settings
    variables = [
        Variable(name='olr', source=None),
        *[
            Variable(name=name, source='era5_daymean_nrt')
            for name in ['u', 'v', 'w', 't', 'q', 'z', 'mslp', 'u10', 'v10', 't2m']
        ],
    ]

    # region settings
    regions = [
        Region('Trop', [0, 360, -20, 20]),
        Region('NH', [0, 360, 20, 90]),
        Region('SH', [0, 360, -90, -20]),
        Region('GLB', [0, 360, -90, 90]),
    ]

    for variable in variables:
        for model in models:
            try:
                run(model, variable, regions)
            except Exception as e:
                print(e)



if __name__ == '__main__':
    main()
