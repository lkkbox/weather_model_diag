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
                'regions':[
                    {'name': 'Trop', 'boundary': [0, 360, -20, 20]}
                ],
                'variables':[
                    {'name': 'u', 'obs_source': 'era5_daymean_nrt'}
                ],
            },
        ),
        # driver.Module(
        #     name='mjo',
        #     option={
        #         'do_data': False, 
        #         'do_plot': True, 
        #         'phase_diagram': {
        #             'init_means': [slice(0, 1)],
        #             # 'lead_means': [slice(0, 5)],
        #         },
        #     },
        # ),
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
                members=list(range(numMembers)),
                hasClim=hasClim,
                numLeads=numLeads,
                climYears=climYears,
            ),
        )
        for caseName, modelName, numMembers, numLeads, hasClim, climYears in [
            ('CWA_GEPSv3', 'CWA_GEPSv3', 3, 45, True, climYears),
            ('CWA_GEPSv2', 'CWA_GEPSv2', 3, 45, False, None),
            ('NCEP_CTRL', 'NCEP_CTRL', 1, 31, False, None),
            ('NCEP_ENSAVG', 'NCEP_ENSAVG', 1, 31, False, None),
        ]
    ]

    driver.run(cases, modules, dataDir, figDir)


if __name__ == '__main__':
    main()
