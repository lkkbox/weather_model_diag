from driver import greeter
from driver import safe_runner
from . import cal_scores_by_xy_1day
from . import cal_scores_by_xy_7dma
from . import plt_scores_by_xy

import pytools as pyt
from pytools.checktools import checkType
from dataclasses import dataclass


@dataclass
class Option_Variable():
    name: str
    obs_source: str = None
    ndim: int = None

    def __post_init__(self):
        checkType(self.name, str, 'name')
        checkType(self.obs_source, [str, None], 'obs_source')
        checkType(self.ndim, [int, None], 'ndim')
        self.isAccumulated = self.name in ['olr', 'prec']
        self.isMultiLevel = self.name in ['u', 'v', 'w', 't', 'q', 'z', 'r']

        if self.ndim is None:
            if self.name in ['u', 'v', 'w', 't', 'q', 'z', 'r']:
                self.ndim = 4
            else:
                self.ndim = 3


@dataclass
class Region():
    name: str
    boundary: list

    def __post_init__(self):
        pyt.chkt.checkType(self.name, str, 'name')
        pyt.chkt.checkType(self.boundary, list, 'boundary')
        [pyt.chkt.checkType(b, [int, float], 'element in boundary') for b in self.boundary]
        w, e, s, n = self.boundary

        if w >= e:
            raise ValueError(f'west should be less than east (name={self.name}, {w=}, {e=})')
        if s >= n:
            raise ValueError(f'south should be less than north (name={self.name}, {s=}, {n=})')

        for we in [w, e]:
            if not (0 <= we <= 360):
                raise ValueError(f'west should be between 0 and 360, (name={self.name}, w/e={we})')

        for sn in [s, n]:
            if not (-90 <= sn <= 90):
                raise ValueError(f'west should be between -90 and 90, (name={self.name}, s/n={sn})')

        self.lonw, self.lone, self.lats, self.latn = w, e, s, n


@dataclass
class Option_Plot():
    regions: dict
    levels: list

    def __post_init__(self):
        # set default values
        checkType(self.regions, dict, 'regions')
        self.regions = [Region(name, boundary) for name, boundary in self.regions.items()]



@dataclass
class Option(): 
    do_data_1day: bool = True
    do_data_7dma: bool = True
    do_plot: bool = True
    plot: dict = None
    variables: list = None
    regrid_delta_x: float = 1
    regrid_delta_y: float = 1
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = [
                {'name': name, 'obs_source': obs_source}
                for name, obs_source in [
                    ('u', 'era5_daymean_nrt'),
                    ('v', 'era5_daymean_nrt'),
                    ('w', 'era5_daymean_nrt'),
                    ('t', 'era5_daymean_nrt'),
                    ('q', 'era5_daymean_nrt'),
                    ('z', 'era5_daymean_nrt'),
                    ('mslp', 'era5_daymean_nrt'),
                    ('u10', 'era5_daymean_nrt'),
                    ('v10', 'era5_daymean_nrt'),
                    ('t2m', 'era5_daymean_nrt'),
                    ('olr', None),
                    ('prec', None),
                ]
            ]
        
        defaultRegions = {
            'Trop': [0, 360, -20,  20],
            'NH': [0, 360,  20,  60],
            'SH': [0, 360, -60, -20],
            'GLB': [0, 360, -90, 90],
        }

        if self.plot is None:
            self.plot = {}

        if 'regions' not in self.plot:
            self.plot['regions'] = defaultRegions

        if 'levels' not in self.plot:
            self.plot['levels'] = [10, 30, 50, 100, 200, 300, 500, 700, 850, 925, 1000]

        # check types
        checkType(self.do_data_1day, bool , 'do_data_1day')
        checkType(self.do_data_7dma, bool , 'do_data_7dma')
        checkType(self.do_plot, bool , 'do_plot')
        checkType(self.variables, list, 'variables')
        checkType(self.regrid_delta_x, [float, int], 'regrid_delta_x')
        checkType(self.regrid_delta_y, [float, int], 'regrid_delta_y')
        checkType(self.plot, [dict, None], 'plot')
        [checkType(variable, dict, 'variable') for variable in self.variables]


        # convert to the option class objects
        self.plot = Option_Plot(**self.plot)
        self.variables = [Option_Variable(**variable) for variable in self.variables]


def run(cases, dataDir, figDir, option: Option):
    if option.do_data_1day:
        run_data = safe_runner(greeter(cal_scores_by_xy_1day.run))
        run_data(cases, dataDir, option)

    if option.do_data_7dma:
        run_data = safe_runner(greeter(cal_scores_by_xy_7dma.run))
        run_data(cases, dataDir, option)

    if option.do_plot:
        run_figs = safe_runner(greeter(plt_scores_by_xy.run))
        run_figs(cases, dataDir, figDir, option)
