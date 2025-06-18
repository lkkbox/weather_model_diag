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
                initTime0=pyt.tt.ymd2float(2001, 1, 25),
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
                'exp_mjo-M22MPKH',
                'exp_mjo-M22MPKHS9',
            ],
        )
    ]

    modules = [
        driver.Module(
            name='mjo',
            option={
                'do_data': False,
                'do_plot': True,
                'score_diagram': {
                    'xlim': [1, 44],
                    'xticks': [1, *list(range(5, 40+5, 5)), 44],
                    'ylim_rmse': [0, 3],
                    'do_acc': False,
                },
                'phase_diagram': {
                    'lead_means': [slice(i*5 , i*5+5) for i in range(9)]
                }
            }
        ),
        # driver.Module(
        #     name='general_plot',
        #     option={
        #         'numCases': len(cases),
        #         'plot_sets': [
        #             *get_ps_olr_hov(),
        #             # *get_ps_vintDivUv_map(),
        #             # *get_ps_vintq_map(),
        #             # *get_ps_vintq_hov(),
        #         ],
        #     },
        # ),
    ]

    driver.run(cases, modules, dataDir, figDir)

def get_ps_vintDivUv_map():
    return [
        {
            'fig_title': rf'sfc-700hPa <$\nabla$u> [1E-6] init(2009-01-26) lead({leads}, {leade})',
            'fig_name': f'map_vintDiv_l{leads}-{leade}.png',
            'fig_opts': {'figsize': (8, 6), 'layout': 'constrained'},
            'nrows_ncols': [3, 2],
            'world_tick_dx': 20,
            'world_tick_dy': 4,
            'ylim': [-12, 12],
            'fontsize_ticks': 6,
            'fontsize_xlabel': 8,
            'fontsize_ylabel': 8,
            'coastline_opts': {'color': 'k', 'linewidth': 0.9},
            'draw_box': [110, 140, -8, 0, {'color': 'k', 'linewidth': 1}],
            'shadings': [
                {
                    'variable': 'u',
                    'variable2': 'v',
                    'xy_axis': [-1, -2],
                    'minMaxs': [[leads-1, leade-1], [700, 1000], [-15, 15], [80, 180]],
                    'total_anomaly': 'anomaly',
                    'math': lambda z: z * -1e6,
                    'operators': ['div2d_lonlat', 'vertical_pressure_mean'],
                    'levels': pyt.ct.mirror([0.5, 1, 2, 4, 7, 10]),
                    'colormap': pyt.colormaps.nclColormap('GreenMagenta16'),
                    'smooths': [5, 5],
                    'contour_opts': {'linestyles': '-', 'colors': 'grey', 'linewidths':0.5},
                    'amean': [110, 140, -8, 0],
                }
            ],
            'vectors': [
                {
                    'variable': 'u',
                    'variable2': 'v',
                    'xy_axis': [-1, -2],
                    'minMaxs': [[leads-1, leade-1], [700, 1000], [-15, 15], [80, 180]],
                    'total_anomaly': 'anomaly',
                    # 'smooths': [5, 5],
                }
            ],
        }
        for leads, leade in [(1, 5), (6, 10), (11, 15),]
    ]

def get_ps_vintq_map():
    return [
        {
            'fig_title': f'sfc-700hPa <q> init(2009-01-26) lead({leads}, {leade}])',
            'fig_name': f'map_vintq_d{d}.png',
            'fig_opts': {'figsize': (8, 6), 'layout': 'constrained'},
            'nrows_ncols': [3, 2],
            'world_tick_dx': 20,
            'world_tick_dy': 4,
            'ylim': [-12, 12],
            'fontsize_ticks': 6,
            'fontsize_xlabel': 8,
            'fontsize_ylabel': 8,
            'coastline_opts': {'color': 'k', 'linewidth': 0.9},
            'draw_box': [120, 140, -5, 5, {'color': 'k', 'linewidth': 1}],
            'shadings': [
                {
                    'variable': 'q',
                    'xy_axis': [-1, -2],
                    'minMaxs': [[leads-1, leade-1], [700, 1000], [-15, 15], [80, 180]],
                    'total_anomaly': 'anomaly',
                    # 'math': lambda z: z * 1000,
                    'math': lambda z: z / 9.8,
                    'operators': ['vertical_pressure_integration'],
                    'levels': pyt.ct.mirror([0.2, 0.5, 1, 2, 3, 4]),
                    'colormap': pyt.colormaps.nclColormap('CBR_coldhot'),
                    'smooths': [2.5, 2.5],
                    'contour_opts': {'linestyles': '-', 'colors': 'grey', 'linewidths':0.5},
                    'amean': [120, 140, -5, 5],
                }
            ],
        }
        for d in range(2)
    ]


def get_ps_vintq_hov():
    return [
        {
            'fig_title': 'sfc-700hPa <q> init(2009-01-26) lat(5S-5N)',
            'fig_name': f'lon_time_vintq.png',
            'fig_opts': {'figsize': (6.4, 4.8), 'layout': 'constrained'},
            'world_tick_dx': 30,
            'fontsize_ticks': 6,
            'fontsize_xlabel': 8,
            'fontsize_ylabel': 8,
            'ylabel': 'leads',
            'shadings': [
                {
                    'variable': 'q',
                    'xy_axis': [-1, -4],
                    'minMaxs': [[0, 30], [700, 1000], [-5, 5], [60, 210]],
                    'total_anomaly': 'anomaly',
                    'math': lambda z: z / 9.8,
                    'operators': ['vertical_pressure_integration'],
                    'levels': pyt.ct.mirror([0.2, 0.5, 1, 2, 3, 4]),
                    'colormap': pyt.colormaps.nclColormap('CBR_coldhot'),
                    'smooths': [7, 5],
                    'contour_opts': {'linestyles': '-', 'colors': 'grey', 'linewidths':0.5},
                }
            ],
        }
    ]

def get_ps_olr_hov():
    return  [
        {
            'figs': [
                {
                    'title': 'OLR init(2009-01-26) lat(15S-15N)',
                    'name': f'lon_time_olr_{total_anomaly}.png',
                    'mpl_opts': {'figsize': (6.4, 4.8), 'layout': 'constrained'},
                },
            ],
            'world_tick_dx': 30,
            'fontsize_ticks': 6,
            'fontsize_xlabel': 8,
            'fontsize_ylabel': 8,
            'ylabel': 'leads',
            'shadings': [
                {
                    'variable': 'olr',
                    'xy_axis': [-1, -3],
                    'minMaxs': [[0, 45], [-15, 15], [60, 210]],
                    'total_anomaly': total_anomaly,
                    'levels': levels,
                    'colormap': colormap,
                    # 'smooths': [5, 5],
                    'contour_opts': {'colors': 'grey', 'linewidths':0.5},
                }
            ],
        }
        for total_anomaly, levels, colormap in [
            (
                'anomaly', 
                pyt.ct.mirror([5, 10, 20, 30, 60]), 
                pyt.colormaps.nclColormap('sunshine_diff_12lev'),
            ),
            (
                'total',
                [170, 190, 210, 230, 250, 270, 290],
                pyt.colormaps.nclColormap('rainbow'),
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

def get_ps_prec_hov():
    return [
        {
            'fig_title': 'Prec init(2009-01-26) lat(10S-10N)',
            'fig_name': f'lon_time_prec_{total_anomaly}.png',
            'fig_opts': {'figsize': (6.4, 4.8), 'layout': 'constrained'},
            'world_tick_dx': 30,
            'fontsize_ticks': 6,
            'fontsize_xlabel': 8,
            'fontsize_ylabel': 8,
            'ylabel': 'leads',
            'shadings': [
                {
                    'variable': 'prec',
                    'xy_axis': [-1, -3],
                    'minMaxs': [[0, 30], [-10, 10], [60, 210]],
                    'total_anomaly': total_anomaly,
                    'levels': levels,
                    'colormap': colormap,
                    'smooths': [7, 5],
                    'contour_opts': {'linestyles': '-', 'colors': 'grey', 'linewidths':0.5},
                }
            ],
        }
        for total_anomaly, levels, colormap in [
            (
                'anomaly', 
                pyt.ct.mirror([1, 3, 5, 7, 9, 12]), 
                pyt.colormaps.nclColormap('precip_diff_12lev'),
            ),
            (
                'total',
                [0.5, 1, 2, 3, 4, 6, 9, 12, 15, 20],
                pyt.colormaps.nclColormap('precip2_17lev'),
            ),
        ]
    ]

def get_ps_prec_map():
    return [
        {
            'fig_title': f'Prec init(2009-01-26), lead({pentad*5+1},{pentad*5+5})',
            'nrows_ncols': [3, 2],
            'world_tick_dx': 45,
            'world_tick_dy': 10,
            'coastline_opts': {},
            'fontsize_ticks': 8,
            'fig_name': f'map_prec_{total_anomaly}_p{pentad}.png',
            'fig_opts': {'figsize': (8, 6)},
            'ylim': [-30, 30],
            'shadings': [
                {
                    'variable': 'prec',
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
                pyt.ct.mirror([1, 3, 5, 9, 14, 20]), 
                pyt.colormaps.nclColormap('precip_diff_12lev'),
            ),
            (
                'total',
                [0.5,  2,  4, 8, 12, 16, 20, 25],
                pyt.colormaps.nclColormap('precip2_17lev'),
            ),
        ]
    ]

def get_ps_u850_hov():
    return [
        {
            'fig_title': 'u850 init(2009-01-26) lat(15S-15N)',
            'fig_name': f'lon_time_u850_{total_anomaly}.png',
            'fig_opts': {'figsize': (6.4, 4.8), 'layout': 'constrained'},
            'world_tick_dx': 30,
            'fontsize_ticks': 6,
            'fontsize_xlabel': 8,
            'fontsize_ylabel': 8,
            'ylabel': 'leads',
            'shadings': [
                {
                    'variable': 'u',
                    'xy_axis': [-1, -4],
                    'minMaxs': [[0, 30], [850]*2, [-15, 15], [60, 210]],
                    'total_anomaly': total_anomaly,
                    'levels': levels,
                    'colormap': colormap,
                    'smooths': [5, 5],
                    'contour_opts': {'linestyles': '-', 'colors': 'grey', 'linewidths':0.5},
                }
            ],
        }
        for total_anomaly, levels, colormap in [
            (
                'anomaly', 
                pyt.ct.mirror([1, 3, 5, 7, 9, 12]), 
                pyt.colormaps.nclColormap('CBR_coldhot'),
            ),
            (
                'total',
                pyt.ct.mirror([0, 2, 4, 6, 8, 12, 15]),
                pyt.colormaps.nclColormap('ncview_default'),
            ),
        ]
    ]

def get_ps_u850_map():
    return [
        {
            'fig_title': f'U850 init(2009-01-26), lead({pentad*5+1},{pentad*5+5})',
            'nrows_ncols': [3, 2],
            'world_tick_dx': 45,
            'world_tick_dy': 10,
            'coastline_opts': {},
            'fontsize_ticks': 8,
            'fig_name': f'map_u850_{total_anomaly}_p{pentad}.png',
            'fig_opts': {'figsize': (8, 6)},
            'ylim': [-30, 30],
            'shadings': [
                {
                    'variable': 'u',
                    'xy_axis': [-1, -2],
                    'minMaxs': [[pentad*5, pentad*5+4], [850]*2, [-32, 32], [0, 360]],
                    'total_anomaly': total_anomaly,
                    'levels': levels,
                    'colormap': colormap,
                    'smooths': [5, 5],
                    'contour_opts': None,
                }
            ],
        } 
        for total_anomaly, levels, colormap in [
            (
                'total',
                pyt.ct.mirror([2, 4, 6, 8, 12, 15, 20]),
                pyt.colormaps.nclColormap('ncview_default'),
            ),
            (
                'anomaly', 
                pyt.ct.mirror([1, 2, 4, 8, 12, 16]), 
                pyt.colormaps.nclColormap('CBR_coldhot'),
            ),
        ]
        for pentad in range(6)
    ]

def get_ps_u200_hov():
    return [
        {
            'fig_title': 'u200 init(2009-01-26) lat(15S-15N)',
            'fig_name': f'lon_time_u200_{total_anomaly}.png',
            'fig_opts': {'figsize': (6.4, 4.8), 'layout': 'constrained'},
            'world_tick_dx': 30,
            'fontsize_ticks': 6,
            'fontsize_xlabel': 8,
            'fontsize_ylabel': 8,
            'ylabel': 'leads',
            'shadings': [
                {
                    'variable': 'u',
                    'xy_axis': [-1, -4],
                    'minMaxs': [[0, 30], [200]*2, [-15, 15], [60, 210]],
                    'total_anomaly': total_anomaly,
                    'levels': levels,
                    'colormap': colormap,
                    'smooths': [5, 5],
                    'contour_opts': {'linestyles': '-', 'colors': 'grey', 'linewidths':0.5},
                }
            ],
        }
        for total_anomaly, levels, colormap in [
            (
                'anomaly', 
                pyt.ct.mirror([2, 4, 8, 16, 20, 25]), 
                pyt.colormaps.nclColormap('CBR_coldhot'),
            ),
            (
                'total',
                pyt.ct.mirror([3, 6, 9, 12, 18, 24]),
                pyt.colormaps.nclColormap('ncview_default'),
            ),
        ]
    ]


if __name__ == '__main__':
    main()
