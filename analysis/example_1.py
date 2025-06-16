#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import driver as driver
import pytools as pyt


def main():
    modules = [
        driver.Module(
            name='mjo',
            option={'do_data': False, 'do_plot': True,}
        )
    ]

    dataDir = '../../data'
    figDir = '../../figs'
    cases = [
        driver.Case(
            name=caseName,
            model = driver.Model(
                name=modelName,
                initTime0=pyt.tt.ymd2float(2009, 1, 26),
                numInitTimes=1,
                members=[0],
                hasClim=True,
                numLeads=45,
                climYears=[2001, 2020],
            ),
        )
        for caseName, modelName in zip(
            ['CTL', 'S', 'M', 'MS'],
            [
                'exp_mjo-DEVM21',
                'exp_mjo-DEVM21S9',
                'exp_mjo-M22G3IKH',
                'exp_mjo-M22G3IKHS9',
            ],
        )
    ]

    driver.run(cases, modules, dataDir, figDir)

    # initTime = pyt.tt.ymd2float(2009, 1, 26)
    # cases = [
    #     Case(long_name='exp_mjo-DEVM21', short_name='CTL'),
    #     Case(long_name='exp_mjo-DEVM21S9', short_name='S'),
    #     Case(long_name='exp_mjo-M22G3IKH', short_name='M'),
    #     Case(long_name='exp_mjo-M22G3IKHS9', short_name='MS'),
    # ]
    # figDir = '../../../figs/exp_mjo_250529'
    # total_or_anomaly = 'anomaly'


if __name__ == '__main__':
    main()
