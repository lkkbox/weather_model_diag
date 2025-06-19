#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import driver as driver
import pytools as pyt

# do_plot: bool True
# do_score: True
# score_diagram: dict = {
#     xlim: list = None,
#     ylim_rmse: list = None,
#     ylim_acc: list = None,
#     xticks: list = None,
#     yticks: list = None,
#     do_rmse: bool = True,
#     do_acc: bool = True,
# }
# phase_diagram: dict = {
#     lead_means: list[slice],
#     init_means: list[slice],
# }

def main():
    modules = [
        driver.Module(
            name='mjo',
            option={
                'do_data': True, 
                'do_plot': True,
                'score_diagram': {
                    # 'xlim': [0, 30],
                    # 'ylim_rmse': [0, 3],
                    # 'ylim_acc': [0, 1],
                    'xticks': [1, *list(range(2, 20+1, 2))],
                    # 'yticks': None,
                    'do_rmse': True,
                    'do_acc': True,
                    'mpl_line_opts': [
                        *[
                            {'label': None, 'color': 'grey', 'linewidth': 0.5}
                            for i in range(20)
                        ],
                        {'color': 'k', 'linewidth': 1.5}
                    ],
                },
                'phase_diagram': {
                    'lead_means': [],
                    'init_means': [slice(i, i+1) for i in range(7)],
                }
            }
        )
    ]

    dataDir = '../../data'
    figDir = '../../figs'
    cases = [
        driver.Case(
            name='TGFS',
            model = driver.Model(
                name='exp_tgfsv2_250619',
                initTime0=pyt.tt.ymd2float(2025, 4, 16),
                numInitTimes=5,
                stepInitTimes=5,
                members=list(range(1, 20+1)),
                hasClim=False,
                numLeads=20,
            ),
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
