from driver import greeter
from . import cal_scores_by_xy
import pytools as pyt
from dataclasses import dataclass
import traceback


def run(cases, dataDir, figDir, option):
    subrun = greeter(cal_scores_by_xy.run)
    try:
        subrun(cases, dataDir, option)
    except Exception:
        traceback.print_exc()


@dataclass
class Option_Variable():
    name: str
    obs_source: str
    ndim: int = None

    def __post_init__(self):
        pyt.chkt.checkType(self.name, str, 'name')
        pyt.chkt.checkType(self.obs_source, str, 'obs_source')
        pyt.chkt.checkType(self.ndim, [int, None], 'ndim')
        self.isAccumulated = self.name in ['olr', 'prec']
        self.isMultiLevel = self.name in ['u', 'v', 'w', 't', 'q', 'z', 'r']

        if self.ndim is None:
            if self.name in ['u', 'v', 'w', 't', 'q', 'z', 'r']:
                self.ndim = 4
            else:
                self.ndim = 3


@dataclass
class Option(): 
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
                ]
            ]
        
        # check types
        pyt.chkt.checkType(self.variables, list, 'variables')
        pyt.chkt.checkType(self.regrid_delta_x, [float, int], 'regrid_delta_x')
        pyt.chkt.checkType(self.regrid_delta_y, [float, int], 'regrid_delta_y')
        [pyt.chkt.checkType(variable, dict, 'variable') for variable in self.variables]


        # convert to the option class objects
        self.variables = [Option_Variable(**variable) for variable in self.variables]

