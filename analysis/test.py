#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import driver as driver
import pytools as pyt


def main():
    initTime0 = pyt.tt.ymd2float(2025, 2, 1)
    numInitTimes = 10
     
    climYears = [2006, 2020]

    modules = [
        driver.Module(
            name='scores',
            option={
                'do_data_1day': True,
                'do_data_7dma': False,
                'do_plot': False,
                'force': True,
                'variables':[
                    # {'name': 'u10', 'obs_source': 'era5_daymean_nrt'},
                    # {'name': 'v10', 'obs_source': 'era5_daymean_nrt'},
                    # {'name': 't2m', 'obs_source': 'era5_daymean_nrt'},
                    # {'name': 'mslp', 'obs_source': 'era5_daymean_nrt'},
                    # {'name': 'olr', 'obs_source': None},
                    # {'name': 'prec', 'obs_source': None},
                    # {'name': 'u'},
                    # {'name': 'v'},
                    # {'name': 'w'},
                    # {'name': 't'},
                    {'name': 'q'},
                    # {'name': 'z'},
                ],
            },
        ),
    ]

    dataDir = '../../data'
    figDir = '../../figs'
    cases = [
        driver.Case(
            name=caseName,
            model = driver.Model(
                name=modelName,
                initTime0=initTime0,
                numInitTimes=numInitTimes,
                members=members,
                hasClim=hasClim,
                numLeads=numLeads,
                climYears=climYears,
            ),
        )
        for caseName, modelName, members, numLeads, hasClim, climYears in [
            ('CWA_TGFS', 'CWA_TGFS', [0], 17, False, None),  
            # ('NCEP_CTRL', 'NCEP_CTRL', [0], 36, False, None),
            # ('NCEP_ENSAVG', 'NCEP_ENSAVG', [0], 36, False, None),
            # ('CWA_GEPSv3', 'CWA_GEPSv3', [-21, 0], 45, True, climYears),
            # ('CWA_GEPSv2', 'CWA_GEPSv2', [-33, 0], 45, False, None),

            # ('CWA_GEPSv3', 'CWA_GEPSv3', [-21], 45, True, climYears),
        ]
    ]

    driver.run(cases, modules, dataDir, figDir)


if __name__ == '__main__':
    main()

