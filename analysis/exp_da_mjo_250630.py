#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import driver as driver
import pytools as pyt


def main():
    initTime0 = pyt.tt.ymd2float(2024, 1, 1)
    numInitTimes = 30
     
    climYears = [2006, 2020]

    mpl_line_opts = [
        # # ---- gepsv3
        # {'label': 'GEPSv3 CTL (BC)', 'color': 'tab:red', 'linestyle': '--'},
        # {'label': 'GEPSv3 ENS (BC)', 'color': 'tab:red', 'linestyle': '-'},
        #
        # # ---- gepsv2
        # {'label': 'GEPSv2 CTL', 'color': 'tab:orange', 'linestyle': '--'},
        # {'label': 'GEPSv2 ENS', 'color': 'tab:orange', 'linestyle': '-'},
        #
        # # ---- ncep ctrl
        # {'label': 'NCEP CTL', 'color': 'tab:blue', 'linestyle': '--'},
        #
        # # ---- ncep ens
        # {'label': 'NCEP ENS', 'color': 'tab:blue', 'linestyle': '-'},
    ]
    modules = [
        driver.Module(
            name='mjo',
            option={
                'do_data': True,
                'do_plot': True,
                'phase_diagram': {
                    # 'mpl_line_opts': mpl_line_opts,
                    'lead_means': [],
                    'init_means': [slice(i*5, i*5 + 5) for i in range(18)]
                },
                'score_diagram': {
                    'fig_opts': {'figsize': (9, 6)},
                    # 'mpl_line_opts': mpl_line_opts,
                },
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
                hasClim=True,
                numLeads=31,
                climYears=[2001, 2020],
            ),
        )
        for caseName, modelName, members in [
            ('noDA', 'exp_gepsv3_da-off', [0]),
            ('DA.ALL', 'exp_gepsv3_da-sst', [0]),
            ('DA.SST', 'exp_gepsv3_da-all', [0]),
        ]
        

    ]

    driver.run(cases, modules, dataDir, figDir)


if __name__ == '__main__':
    main()

