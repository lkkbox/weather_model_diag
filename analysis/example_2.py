#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import driver as driver
import pytools as pyt

def main():
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
            ['CTL', 'S'],#, 'M', 'MS'],
            [
                'exp_mjo-DEVM21',
                'exp_mjo-DEVM21S9',
                'exp_mjo-M22G3IKH',
                'exp_mjo-M22G3IKHS9',
            ],
        )
    ]

    modules = [
        # driver.Module(
        #     name='mjo',
        #     option={
        #         'do_data': False,
        #         'do_plot': True,
        #         'score_diagram': {
        #             'xlim': [1, 28],
        #             'xticks': [1, 7, 14, 21, 28],
        #             'ylim_rmse': [0, 1.8],
        #             'do_acc': False,
        #         }
        #     }
        # ),
        driver.Module(
            name='general_plot',
            option={
                'numCases': len(cases),
                'plot_sets': [
                    *get_ps_prec_hov(),
                    # *get_ps_olr_map,
                ],
            },
        ),
    ]

    driver.run(cases, modules, dataDir, figDir)


def get_ps_prec_hov():
    return [
        {
            'figs': [
                {
                    'title': 'Prec init(2009-01-26) lat(10S-10N)',
                    'name': f'lon_time_prec_{total_anomaly}_10.png',
                    'mpl_opts': {'figsize': (6.4, 4.8), 'layout': 'constrained'},
                },
                {
                    'title': 'Prec init(2009-01-26) lat(15S-15N)',
                    'name': f'lon_time_prec_{total_anomaly}_15.png',
                    'mpl_opts': {'figsize': (6.4, 4.8), 'layout': 'constrained'},
                },
            ],
            'figs_dim_by': -2,
            'world_tick_dx': 30,
            'fontsize_ticks': 6,
            'fontsize_xlabel': 8,
            'fontsize_ylabel': 8,
            'ylabel': 'leads',
            'shadings': [
                {
                    'variable': 'prec',
                    'xy_axis': [-1, -3],
                    'minMaxs': [[0, 30], [-15, 15], [60, 210]],
                    'total_anomaly': total_anomaly,
                    'levels': levels,
                    'colormap': colormap,
                    'smooths': [7, 5],
                    'contour_opts': {'linestyles': '-', 'colors': 'grey', 'linewidths':0.5},
                }
            ],
        }
        for total_anomaly, levels, colormap in [
            # (
            #     'anomaly', 
            #     pyt.ct.mirror([1, 3, 5, 7, 9, 12]), 
            #     pyt.colormaps.nclColormap('precip_diff_12lev'),
            # ),
            (
                'total',
                [0.5, 1, 2, 3, 4, 6, 9, 12, 15, 20],
                pyt.colormaps.nclColormap('precip2_17lev'),
            ),
        ]
    ]

def get_ps_olr_map():
    return [
        {
            'fig_title': f'OLR init(2009-01-26), lead({pentad*5+1},{pentad*5+5})',
            'nrows_ncols': [3, 2],
            'world_tick_dx': 45,
            'world_tick_dy': 10,
            'coastline_opts': {},
            'fontsize_ticks': 8,
            'fig_name': f'map_olr_{total_anomaly}_p{pentad}.png',
            'fig_opts': {'figsize': (8, 6)},
            'ylim': [-30, 30],
            'shadings': [
                {
                    'variable': 'olr',
                    'xy_axis': [-1, -2],
                    'minMaxs': [[pentad*5, pentad*5+4], [-32, 32], [0, 360]],
                    'total_anomaly': total_anomaly,
                    'levels': levels,
                    'colormap': colormap,
                    'smooths': [5, 5],
                    'contour_opts': None,
                }
            ],
        } 
        for pentad in range(6)
        for total_anomaly, levels, colormap in [
            (
                'anomaly', 
                pyt.ct.mirror([10, 20, 30, 40, 60]),
                pyt.colormaps.nclColormap('sunshine_diff_12lev'),
            ),
            (
                'total',
                [170, 190, 210, 230, 250, 270, 290],
                pyt.colormaps.nclColormap('rainbow'),
            ),
        ]
    ]


if __name__ == '__main__':
    main()
