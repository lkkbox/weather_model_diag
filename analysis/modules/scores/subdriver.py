from driver import greeter
import pytools as pyt
from . import cal_scores_noBC as cal_nobc
from dataclasses import dataclass, field
import traceback


def run(cases, dataDir, figDir, option):
    _cal_scores_nobc(cases, dataDir, option)


def _cal_scores_nobc(cases, dataDir, option):
    for variable in option.variables:
        for case in cases:
            try:
                cal_nobc.run(case.model, variable, option.regions, dataDir)
            except Exception:
                print(traceback.format_exc())
    # # model settings
    # initTime0 = pyt.tt.ymd2float(2025, 1, 1)
    # numInits = 90
    # models = [
    #     *[
    #         Model(
    #             name='NCEP_CTRL',
    #             iMember=iMember,
    #             initTime0=initTime0,
    #             numInits=numInits,
    #         )
    #         for iMember in range(1)
    #     ],
    #     *[
    #         Model(
    #             name='NCEP_ENSAVG',
    #             iMember=iMember,
    #             initTime0=initTime0,
    #             numInits=numInits,
    #         )
    #         for iMember in range(1)
    #     ],
    #     *[
    #         Model(
    #             name='CWA_GEPSv3',
    #             iMember=iMember,
    #             initTime0=initTime0,
    #             numInits=numInits,
    #         )
    #         for iMember in range(21)
    #     ],
    #     *[
    #         Model(
    #             name='CWA_GEPSv2',
    #             iMember=iMember,
    #             initTime0=initTime0,
    #             numInits=numInits,
    #         )
    #         for iMember in range(33)
    #     ],
    # ]
    #
    # # variable settings
    # variables = [
    #     Variable(name='olr', source=None),
    #     *[
    #         Variable(name=name, source='era5_daymean_nrt')
    #         for name in ['u', 'v', 'w', 't', 'q', 'z', 'mslp', 'u10', 'v10', 't2m']
    #     ],
    # ]
    #
    # # region settings
    # regions = [
    #     Region('Trop', [0, 360, -20, 20]),
    #     Region('NH', [0, 360, 20, 90]),
    #     Region('SH', [0, 360, -90, -20]),
    #     Region('GLB', [0, 360, -90, 90]),
    # ]
    #
    # for variable in variables:
    #     for model in models:
    #         try:
    #             run(model, variable, regions)
    #         except Exception as e:
    #             print(e)


@dataclass
class Option_Region():
    name: str
    boundary: list[int|float]

    def __post_init__(self):
        # check types
        pyt.chkt.checkType(self.name, str, 'name')
        pyt.chkt.checkType(self.boundary, list, 'boundary')
        for bound in self.boundary:
            pyt.chkt.checkType(bound, [int, float], 'elements in boundary')

        # set lonw, lone, lats, latn
        self.lonw, self.lone, self.lats, self.latn = self.boundary
        if self.lonw > self.lone:
            raise ValueError('lon west cannot be greater than east')
        if self.lats > self.latn:
            raise ValueError('lat south cannot be greater than north')


@dataclass
class Option_Variable():
    name: str
    obs_source: str

    def __post_init__(self):
        pyt.chkt.checkType(self.name, str, 'name')
        pyt.chkt.checkType(self.obs_source, str, 'obs_source')
        self.isAccumulated = self.name in ['olr', 'prec']
        self.isMultiLevel = self.name in ['u', 'v', 'w', 't', 'q', 'z', 'r']


@dataclass
class Option(): # defalt options
    regions: list = None
    variables: list = None
    
    def __post_init__(self):
        # set default values
        if not self.regions is None:
            self.regions = [
                {'name': name, 'boundary': boundary}
                for name, boundary in [
                    ('Trop', [0, 360, -20, 20]),
                    ('NH', [0, 360, 20, 90]),
                    ('SH', [0, 360, -90, -20]),
                    ('GLB', [0, 360, -90, 90]),
                ]
            ]

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
        pyt.chkt.checkType(self.regions, list, 'regions')
        pyt.chkt.checkType(self.variables, list, 'variables')
        [pyt.chkt.checkType(region, dict, 'region') for region in self.regions]
        [pyt.chkt.checkType(variable, dict, 'variable') for variable in self.variables]


        # convert to the option class objects
        self.regions = [Option_Region(**region) for region in self.regions]
        self.variables = [Option_Variable(**variable) for variable in self.variables]

