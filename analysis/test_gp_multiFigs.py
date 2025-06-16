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
            ['CTL', 'S', 'M', 'MS'],
            [
                'exp_mjo-DEVM21',
                'exp_mjo-DEVM21S9',
                'exp_mjo-M22G3IKH',
                'exp_mjo-M22G3IKHS9',
            ],
        )
    ]

    modules = [
        driver.Module(
            name='general_plot',
            option={
                'numCases': len(cases),
                'plot_sets': [
                    *get_ps(),
                ],
            },
        ),
    ]

    driver.run(cases, modules, dataDir, figDir)


def get_ps():
    return [*get_ps_by_time()]

def get_ps_by_lat():
    return [
        {
            'figs': [
                {
                    'title': 'Prec init(2009-01-26) lat(10S-10N)',
                    'name': f'lon_time_prec_{total_anomaly}_10.png',
                    'mpl_opts': {'figsize': (6.4, 4.8), 'layout': 'constrained'},
                    'dim_means': [-10, 10],
                },
                {
                    'title': 'Prec init(2009-01-26) lat(15S-15N)',
                    'name': f'lon_time_prec_{total_anomaly}_15.png',
                    'mpl_opts': {'figsize': (6.4, 4.8), 'layout': 'constrained'},
                    'dim_means': [-15, 15],
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
            (
                'total',
                [0.5, 1, 2, 3, 4, 6, 9, 12, 15, 20],
                pyt.colormaps.nclColormap('precip2_17lev'),
            ),
        ]
    ]


def get_ps_by_time():
    pos = [1, 3, 5, 2, 4, 6]
    caseNames = ['obs', 'CTL', 'S', 'M', 'MS']
    return [
        {
            'figs': [
                {
                    'title': f'OLR init(2009-01-26) lead(1-5), case={caseName}',
                    'name': f'map_olr_{total_anomaly}_case{icase}_l1-5.png',
                    'mpl_opts': {'figsize': (5.4, 4.8), 'layout': 'constrained'},
                    'dim_means': [icase, icase],
                }
                for icase, caseName in enumerate(caseNames)
            ],
            'subplots':[
                {
                    'position': [3, 2, pos[i]],
                    'dim_means': [i*5, i*5+4],
                    'title': f'({chr(97+i)}) lead=({i*5}, {i*5+4})'
                }
                for i in range(6)
            ],
            'figs_dim_by': 'case',
            'subplots_dim_by': 0,
            'world_tick_dx': 30,
            'world_tick_dy': 10,
            'fontsize_ticks': 6,
            'coastline_opts': {'color': 'k'},
            'shadings': [
                {
                    'variable': 'olr',
                    'xy_axis': [-1, -2],
                    'minMaxs': [[0, 30], [-30, 30], [60, 210]],
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
                pyt.ct.mirror([0, 15, 30, 45, 60]),
                pyt.colormaps.nclColormap('sunshine_diff_12lev'),
            ),
        ]
    ]


if __name__ == '__main__':
    main()
