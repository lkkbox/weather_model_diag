#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import driver as driver
import pytools as pyt
from pytools.timetools import float2format as strDate

def main():
    dataDir = '../../data'
    figDir = '../../figs'
    caseDates = [
        # pyt.tt.ymd2float(2001, 1, 25),
        pyt.tt.ymd2float(2009, 1, 26),
    ]


    for caseDate in caseDates:
        cases = [
            driver.Case(
                name=caseName,
                model = driver.Model(
                    name=modelName,
                    initTime0=caseDate,
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

        plotSets = [
            *get_ps_lh_map(caseDate),
            # *get_ps_vintq_hov(caseDate),
            # *get_ps_vintq_map(caseDate),
            # *get_ps_vintq_ts(caseDate),
            # *get_ps_vintDivUv_map(caseDate),
            # *get_ps_t2m_map(caseDate),

            # *get_ps_vintqTend_map(caseDate),
            # get_ps_lonLevQ(caseDate),
            # *get_ps_olr_hov(caseDate),
            # *get_ps_prec_hov(caseDate),
        ]

        modules = [
            # driver.Module(
            #     name='mjo',
            #     option={
            #         'do_data': True,
            #         'do_plot': True,
            #         'score_diagram': {
            #             'xlim': [1, 45],
            #             'xticks': [1, *list(range(5, 40+5, 5)), 45],
            #             'ylim_rmse': [0, 3],
            #             'do_acc': False,
            #             'add_ensmean': False,
            #         },
            #         'phase_diagram': {
            #             'lead_means': [slice(i*5 , i*5+5) for i in range(9)]
            #         }
            #     }
            # ),
            driver.Module(
                name='general_plot',
                option={
                    'numCases': len(cases),
                    'plot_sets': plotSets,
                },
            ),
        ]

        driver.run(cases, modules, dataDir, figDir)


def get_ps_lonLevQ():
    return  {
        'figs': [
            {
                'title': f'q init(2009-01-26) lat(8S-5N), lead({leads}-{leade})',
                'name': f'lonLevQ_l{leads}-{leade}.png',
                'mpl_opts': {'figsize': (6.4, 4.8), 'layout': 'constrained'},
                'dim_means': [leads, leade],
            }
            for leads, leade in [(1, 5), (6, 10), (11, 15)]
        ],
        'subplots': [
            {'position': [3, 2, i+1]}
            for i in range(5)
        ],
        'figs_dim_by': 0,
        'world_tick_dx': 20,
        'fontsize_ticks': 6,
        'fontsize_xlabel': 8,
        'fontsize_ylabel': 8,
        'ylabel': 'hPa',
        'ylim': [1000, 500],
        'shadings': [
            {
                'variable': 'q',
                'xy_axis': [-1, -3],
                'minMaxs': [[0, 45], [500, 1000], [-8, 5], [80, 180]],
                'total_anomaly': 'anomaly',
                'math': lambda z: z * 1000,
                'levels': pyt.ct.mirror([0, 0.2, 0.5, 1, 2, 4]),
                'operators': ['mask_by_surface_pressure'],
                'colormap': pyt.colormaps.nclColormap('CBR_coldhot'),
                'smooths': [5, None],
                'contour_opts': {'colors': 'grey', 'linewidths':0.5, 'linestyles': '-'},
            }
        ],
    }
def get_ps_vintDivUv_map(caseDate):
    area = [120, 160, -8, 5]
    return [
        {
            'figs': [
                {
                    'title': fr'sfc-{levTop}hPa <$-\nabla\cdot$u> init({strDate(caseDate)}) lead({leads}, {leade}])',
                    'name': f'{strDate(caseDate, '%y%m%d')}/map_vintDiv_{levTop}_l{leads}-{leade}.png',
                    'mpl_opts': {'figsize': (8, 6), 'layout': 'constrained'},
                    'dim_means': [leads-1, leade-1],
                }
                for leads, leade in [
                    (1, 5), (6, 10)
                ]
            ],
            'subplots': [
                {'position': [3, 2, i+1]}
                for i in range(5)
            ],
            'figs_dim_by': 0,
            'world_tick_dx': 20,
            'world_tick_dy': 4,
            'ylim': [-12, 12],
            'fontsize_ticks': 6,
            'fontsize_xlabel': 8,
            'fontsize_ylabel': 8,
            'coastline_opts': {'color': 'k', 'linewidth': 0.9},
            'draw_box': [*area, {'color': 'k', 'linewidth': 1}],
            'shadings': [
                {
                    'variable': 'u',
                    'variable2': 'v',
                    'xy_axis': [-1, -2],
                    'minMaxs': [[0, 45], [levTop, 1000], [-15, 15], [80, 180]],
                    'total_anomaly': 'anomaly',
                    'math': lambda z: z * -1e6,
                    'operators': ['div2d_lonlat', 'vertical_pressure_mean'],
                    'levels': pyt.ct.mirror([0.5, 1, 2, 4, 7, 10]),
                    'colormap': pyt.colormaps.nclColormap('GreenMagenta16', reverse=True),
                    'smooths': [5, 5],
                    'contour_opts': {'linestyles': '-', 'colors': 'grey', 'linewidths':0.5},
                    'amean': area,
                }
            ],
            'vectors': [
                {
                    'variable': 'u',
                    'variable2': 'v',
                    'xy_axis': [-1, -2],
                    'minMaxs': [[0, 45], [levTop, 1000], [-15, 15], [80, 180]],
                    'total_anomaly': 'anomaly',
                    # 'smooths': [5, 5],
                }
            ],
        }
        for levTop in [700, 850]
    ]


def get_ps_lh_map(caseDate):
    area = [120, 160, -8, 5]
    return [
        {
            'figs': [
                {
                    'title': f'LH init({strDate(caseDate)}) lead({leads}, {leade}])',
                    'name': f'{strDate(caseDate, '%y%m%d')}/map_lh_l{leads}-{leade}.png',
                    'mpl_opts': {'figsize': (8, 6), 'layout': 'constrained'},
                    'dim_means': [leads-1, leade-1],
                }
                for leads, leade in [
                    (1, 5), (6, 10), (11, 15)
                ]
            ],
            'subplots': [
                {'position': [3, 2, i+1]}
                for i in range(4)
            ],
            'figs_dim_by': 0,
            'world_tick_dx': 20,
            'world_tick_dy': 4,
            'ylim': [-12, 12],
            'fontsize_ticks': 6,
            'fontsize_xlabel': 8,
            'fontsize_ylabel': 8,
            'coastline_opts': {'color': 'k', 'linewidth': 0.9},
            'draw_box': [*area, {'color': 'k', 'linewidth': 1}],
            'with_obs': False,
            'shadings': [
                {
                    'variable': 'lh',
                    'xy_axis': [-1, -2],
                    'minMaxs': [[0, 45], [-15, 15], [80, 180]],
                    'total_anomaly': 'total',
                    'operators': ['vertical_pressure_integration'],
                    'levels': [1, 2, 3, 4, 5, 6, 7, 8],
                    'math': lambda z: z * 86400 / 2.5E6,
                    'colormap': pyt.colormaps.nclColormap('cmp_flux', reverse=True),
                    'smooths': [2.5, 2.5],
                    'contour_opts': {'linestyles': '-', 'colors': 'grey', 'linewidths':0.5},
                    'amean': area,
                }
            ],
        }
    ]


def get_ps_t2m_map(caseDate):
    area = [120, 160, -8, 5]
    return [
        {
            'figs': [
                {
                    'title': f't2m init({strDate(caseDate)}) lead({leads}, {leade}])',
                    'name': f'{strDate(caseDate, '%y%m%d')}/map_t2m_l{leads}-{leade}.png',
                    'mpl_opts': {'figsize': (8, 6), 'layout': 'constrained'},
                    'dim_means': [leads-1, leade-1],
                }
                for leads, leade in [
                    (1, 5), (6, 10), (11, 15)
                ]
            ],
            'subplots': [
                {'position': [3, 2, i+1]}
                for i in range(5)
            ],
            'figs_dim_by': 0,
            'world_tick_dx': 20,
            'world_tick_dy': 4,
            'ylim': [-12, 12],
            'fontsize_ticks': 6,
            'fontsize_xlabel': 8,
            'fontsize_ylabel': 8,
            'coastline_opts': {'color': 'k', 'linewidth': 0.9},
            'draw_box': [*area, {'color': 'k', 'linewidth': 1}],
            'shadings': [
                {
                    'variable': 't2m',
                    'xy_axis': [-1, -2],
                    'minMaxs': [[0, 45], [-15, 15], [80, 180]],
                    'total_anomaly': 'anomaly',
                    'operators': ['vertical_pressure_integration'],
                    'levels': pyt.ct.mirror([0.2, 0.5, 1, 1.5, 2, 2.5]),
                    'colormap': pyt.colormaps.nclColormap('temp_diff_18lev'),
                    'smooths': [2.5, 2.5],
                    'contour_opts': {'linestyles': '-', 'colors': 'grey', 'linewidths':0.5},
                    'amean': area,
                }
            ],
        }
    ]



def get_ps_vintq_map(caseDate):
    area = [120, 160, -8, 5]
    return [
        {
            'figs': [
                {
                    'title': f'sfc-{levTop}hPa <q> init({strDate(caseDate)}) lead({leads}, {leade}])',
                    'name': f'{strDate(caseDate, '%y%m%d')}/map_vintq{levTop}_l{leads}-{leade}.png',
                    'mpl_opts': {'figsize': (8, 6), 'layout': 'constrained'},
                    'dim_means': [leads-1, leade-1],
                }
                for leads, leade in [
                    (1, 5), (6, 10), (11, 15), (16, 20), (21, 25), (26, 30),
                ]
            ],
            'subplots': [
                {'position': [3, 2, i+1]}
                for i in range(5)
            ],
            'figs_dim_by': 0,
            'world_tick_dx': 20,
            'world_tick_dy': 4,
            'ylim': [-12, 12],
            'fontsize_ticks': 6,
            'fontsize_xlabel': 8,
            'fontsize_ylabel': 8,
            'coastline_opts': {'color': 'k', 'linewidth': 0.9},
            'draw_box': [*area, {'color': 'k', 'linewidth': 1}],
            'shadings': [
                {
                    'variable': 'q',
                    'xy_axis': [-1, -2],
                    'minMaxs': [[0, 45], [levTop, 1000], [-15, 15], [80, 180]],
                    'total_anomaly': 'anomaly',
                    # 'math': lambda z: z * 1000,
                    'math': lambda z: z / 9.8,
                    'operators': ['vertical_pressure_integration'],
                    'levels': pyt.ct.mirror([0.2, 0.5, 1, 2, 3, 4]),
                    'colormap': pyt.colormaps.nclColormap('CBR_coldhot'),
                    'smooths': [2.5, 2.5],
                    'contour_opts': {'linestyles': '-', 'colors': 'grey', 'linewidths':0.5},
                    'amean': area,
                }
            ],
        }
        for levTop in [850, 700]
    ]


def get_ps_vintq_hov(caseDate):
    clev_tend = pyt.ct.mirror([0.2])
    return [
        {
            'figs': [
                {
                    'title': fr'sfc-{levTop}hPa <q>, <$q_t$> init({strDate(caseDate)}) lat(8S-5N)',
                    'name': f'{strDate(caseDate, '%y%m%d')}/lon_time_vintq_{levTop}.png',
                    'mpl_opts': {'figsize': (6.4, 4.8), 'layout': 'constrained'},
                },
            ],
            'ylim': [0, 30],
            'world_tick_dx': 30,
            'fontsize_ticks': 6,
            'fontsize_xlabel': 8,
            'fontsize_ylabel': 8,
            'ylabel': 'leads',
            'shadings': [
                {
                    'variable': 'q',
                    'xy_axis': [-1, -4],
                    'minMaxs': [[0, 45], [levTop, 1000], [-8, 5], [60, 210]],
                    'total_anomaly': 'anomaly',
                    'math': lambda z: z / 9.8,
                    'operators': ['vertical_pressure_integration'],
                    'levels': pyt.ct.mirror([0.2, 0.5, 1, 2, 3, 4]),
                    'colormap': pyt.colormaps.nclColormap('CBR_coldhot'),
                    'smooths': [5, 5],
                    'contour_opts': None,
                }
            ],
            'contours': [
                {
                    'variable': 'q',
                    'xy_axis': [-1, -4],
                    'minMaxs': [[0, 45], [levTop, 1000], [-8, 5], [60, 210]],
                    'total_anomaly': 'anomaly',
                    'math': lambda z: z / 9.8,
                    'operators': ['time_tendency', 'vertical_pressure_integration'],
                    'mpl_opts_list': [
                        {
                            'levels': [l for l in clev_tend if l > 0],
                            'colors': 'tab:green',
                            'linewidths': 0.8,
                            'linestyles': '-',
                        },
                        # {
                        #     'levels': [l for l in clev_tend if l < 0],
                        #     'colors': 'k',
                        #     'linewidths': 0.5,
                        #     'linestyles': '--',
                        # }
                    ],
                    'smooths': [5, 5],
                }
            ],
        }
        for levTop in [850, 700]
    ]


def get_ps_vintq_ts(caseDate):
    area = [120, 160, -8, 5]
    return [
        {
            'figs': [
                {
                    'title': fr'sfc-{levTop}hPa q, $q_t$, $-\nabla\cdot$u, init({strDate(caseDate)}) {area=}',
                    'name': f'{strDate(caseDate, '%y%m%d')}/time_vintq_{levTop}.png',
                    'mpl_opts': {'figsize': (6.4, 4.8), 'layout': 'constrained'},
                },
            ],
            'subplots': [
                {'position': [3, 2, i]}
                for i in [1, 3, 4, 5, 6]
            ],
            'xlim': [0, 16],
            'ylim': [-2.5, 2],
            'grid_on': True,
            'fontsize_ticks': 6,
            'fontsize_xlabel': 8,
            'fontsize_ylabel': 8,
            'xlabel': 'leads',
            'ylabel': 'mm,  0.5 mm/d',
            'lines': [
                {
                    'variable': 'q',
                    'xy_axis': [0, None],
                    'minMaxs': [[0, 45], [levTop, 1000], area[2:], area[:2]],
                    'total_anomaly': 'anomaly',
                    'math': lambda z: z / 9.8,
                    'operators': ['vertical_pressure_integration'],
                    'smooths': [3, None],
                    'mpl_opts': {'color': 'tab:blue'},
                },
                {
                    'variable': 'q',
                    'xy_axis': [0, None],
                    'minMaxs': [[0, 45], [levTop, 1000], area[2:], area[:2]],
                    'total_anomaly': 'anomaly',
                    'math': lambda z: z / 9.8 * 2,
                    'operators': ['time_tendency', 'vertical_pressure_integration'],
                    'smooths': [3, None],
                    'mpl_opts': {'color': 'tab:blue', 'linestyle': '--'},
                },
            ],
        }
        for levTop in [850, 700]
    ]


def get_ps_vintq_700_hov():
    return [
        {
            'figs': [
                {
                    'title': 'sfc-700hPa <q> init(2009-01-26) lat(8S-5N)',
                    'name': f'lon_time_vintq_700.png',
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
                    'variable': 'q',
                    'xy_axis': [-1, -4],
                    'minMaxs': [[0, 45], [700, 1000], [-8, 5], [60, 210]],
                    'total_anomaly': 'anomaly',
                    'math': lambda z: z / 9.8,
                    'operators': ['vertical_pressure_integration'],
                    'levels': pyt.ct.mirror([0.2, 0.5, 1, 2, 3, 4]),
                    'colormap': pyt.colormaps.nclColormap('CBR_coldhot'),
                    'smooths': [5, 5],
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
                    'smooths': [5, 5],
                    'contour_opts': {'colors': 'grey', 'linewidths':0.5},
                }
            ],
        }
        for total_anomaly, levels, colormap in [
            (
                'anomaly', 
                pyt.ct.mirror([10, 20, 30, 45, 60]), 
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
    return  [
        {
            'figs': [
                {
                    'title': 'Prec init(2009-01-26) lat(15S-15N)',
                    'name': f'lon_time_prec_{total_anomaly}.png',
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
                    'variable': 'prec',
                    'xy_axis': [-1, -3],
                    'minMaxs': [[0, 45], [-15, 15], [60, 210]],
                    'total_anomaly': total_anomaly,
                    'levels': levels,
                    'colormap': colormap,
                    'smooths': [5, 5],
                    'contour_opts': {'colors': 'grey', 'linewidths':0.5},
                }
            ],
        }
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
