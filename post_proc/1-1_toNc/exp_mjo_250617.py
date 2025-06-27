#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
from modules.dms2nc import Variable
from modules.dms2nc import Converter
from pytools import timetools as tt


def main():
    srcDirRoot = '/nwpr/gfs/com120/9_data/models/exp/MJO/run250617'
    dmsSuffix = 'GI0GR1191936'
    gridPath = '/nwpr/gfs/com120/9_data/models/griddes/TCo383_lonlat.nc'
    desDirRoot = f'../../../data/processed'
    dmsPrecision = 'single'
    variables = getVariables()

    converter = Converter(
        srcDirRoot = srcDirRoot,
        dmsSuffix = dmsSuffix,
        gridPath = gridPath,
        desDirRoot = desDirRoot,
        dmsPrecision = dmsPrecision,
        variables = variables,
    )

    for initTime in [
        tt.format2float(d, '%Y%m%d') for d in [
            '20010125',
            '20090126',
        ]
    ]:
        for caseName in [
            # 'exp_mjo-DEVM21',
            # 'exp_mjo-DEVM21S9',
            # 'exp_mjo-M22MPKH',
            # 'exp_mjo-M22MPKHS9',
            'exp_mjo-M22MPKHCM12',
        ]:
            converter.run(initTime, caseName, iMember=0)


def getVariables():
    leads_3d_inst = list(range(6, 1080, 6))
    leads_4d = list(range(6, 1080, 6))
    leads_3d_acc = list(range(24, 1080, 24))
    levels = [10, 20, 30, 50, 70, 100, 200, 300, 500, 700, 850, 925, 1000]
    outputType_daily = 'global_daily_1p0'
    outputType_6hr = 'qbud-16d'
    return [
        *[
            Variable(
                name=name,
                levels=None,
                leads=leads_3d_inst,
                outputTypes=[outputType_daily],
            )
            for name in ['u10', 'v10', 't2m', 'mslp', 'pw']
        ],
        *[
            Variable(
                name=name,
                levels=None,
                leads=leads_3d_inst,
                outputTypes=[outputType_daily, outputType_6hr],
            )
            for name in ['lh']
        ],
        *[
            Variable(
                name=name,
                levels=None,
                leads=leads_3d_acc,
                outputTypes=[outputType_daily],
                shiftHour=-12
            )
            for name in ['olr', 'prec']
        ],
        *[
            Variable(
                name=name,
                levels=levels,
                leads=leads_4d,
                outputTypes=[outputType_daily],
            )
            for name in ['t']
        ],
        *[
            Variable(
                name=name,
                levels=levels,
                leads=leads_4d,
                outputTypes=[outputType_daily, outputType_6hr],
            )
            for name in ['u', 'v', 'w', 'q']
        ],
    ]


if __name__ == '__main__':
    main()
