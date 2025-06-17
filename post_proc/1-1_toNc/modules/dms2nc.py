from netCDF4 import Variable
from pytools import timetools as tt
from pytools import dmstools as dmst
from pytools import nctools as nct
from pytools import caltools as ct
from pytools import checktools as chkt
from dataclasses import dataclass
import numpy as np
import os


@dataclass
class Converter():
    srcDirRoot: str
    dmsSuffix: str
    gridPath: str
    desDirRoot: str
    dmsPrecision: str
    variables: list[Variable]


    def run(self, initTime, caseName, iMember):
        # update parameters
        self.initTime = initTime
        self.caseName = caseName
        self.iMember = iMember
        self.srcDir = tt.float2format(
            self.initTime, 
            f'{self.srcDirRoot}/{self.caseName}/OS_exp%Y%m%d%H',
        )
        # run each variabel
        for variable in self.variables:
            self._subrun(variable)


    def __post_init__(self):
        chkt.checkType(self.srcDirRoot,  str, 'srcDirRoot')
        chkt.checkType(self.dmsSuffix,  str, 'dmsSuffix')
        chkt.checkType(self.gridPath,  str, 'gridPath')
        chkt.checkType(self.desDirRoot,  str, 'desDirRoot')
        chkt.checkType(self.dmsPrecision,  str, 'dmsPrecision')
        chkt.checkType(self.variables,  list, 'variables')
        for variable in self.variables:
            chkt.checkType(variable, Variable, 'variable in variables')

        self.core_funcs = {# mapping outputtype to functions
           'global_daily_1p0': global_daily_1p0,
           'qbud-16d': qbud_16d,
        }


    def _subrun(self, variable):
        print(variable.name, end=' ', flush=True)
        outputTypes = variable.outputTypes.copy()

        def getDesPath(outputType):
            desRoot = f'{self.desDirRoot}/{self.caseName}'
            return tt.float2format(
                self.initTime,
                f'{desRoot}/%Y/%m/%dz%H/E{self.iMember:03d}/{outputType}_{variable.name}.nc'
            )

        allFound, notFounds = True, outputTypes.copy() # are we done?
        for outputType in outputTypes:
            print(outputType)
            path = getDesPath(outputType)
            if not os.path.exists(path):
                allFound = False
            else:
                print(f'skipping {outputType}', end='', flush=True)
                notFounds.remove(outputType)

            if not os.path.exists(os.path.dirname(path)):
                os.system(f'mkdir -p $(dirname {path})')

            if not os.access(os.path.dirname(path), os.W_OK):
                print(f'permission dinied to write {os.path.dirname(path)}')
                return

        if allFound:
            print('all skipped.')
            return
        else:
            outputTypes = notFounds
        
        lon = nct.read(self.gridPath, 'lon')
        lat = nct.read(self.gridPath, 'lat')

        print(f'reading..', flush=True, end='')
        if variable.levels is None:
            shape = (len(variable.leads), len(lat), len(lon),)
            dmsPrefix = dmst.varName2dmsPrefix(variable.name)
            srcPaths = [
                tt.float2format(
                    self.initTime,
                    f'{self.srcDir}/%Y%m%d%H%M{lead:04d}/{dmsPrefix}{self.dmsSuffix}',
                )
                for lead in variable.leads
            ]
        else:
            shape = (len(variable.leads), len(variable.levels), len(lat), len(lon),)
            srcPaths = [
                tt.float2format(
                    self.initTime,
                    f'{self.srcDir}/%Y%m%d%H%M{lead:04d}/{dmsPrefix}{self.dmsSuffix}',
                )
                for lead in variable.leads
                for dmsPrefix in [
                    dmst.varName2dmsPrefix(variable.name, level)
                    for level in variable.levels
                ]
            ]

        data = dmst.readNd(srcPaths, shape, precision=self.dmsPrecision)

        for outputType in outputTypes:
            desPath = getDesPath(outputType)
            if os.path.exists(desPath):
                print(f'skip {outputType} for existing {desPath}')
                continue
            func = self.core_funcs[outputType]
            func(self.initTime, desPath, lon, lat, data, variable)

        print('finished.')



def global_daily_1p0(initTime, desPath, lon, lat, data, variable):
    # constants
    LON = np.r_[0:360]
    LAT = np.r_[-90:90+1]

    # daily mean
    times = np.array([initTime + lead/24 + variable.shiftHour/24 for lead in variable.leads])
    dates = list(set([int(t) for t in times]))
    dates.sort()
    numDays = len(dates)
    globalDaily1p0 = np.nan * np.ones((numDays, *data.shape[1:]))
    for iDate, date in enumerate(dates):
        mask = ((date <= times) & (times < date+1))
        globalDaily1p0[iDate, :] = np.nanmean(data[mask, :], axis=0)

    print('interpolating..', flush=True, end='')
    globalDaily1p0 = ct.interp_1d(lon, globalDaily1p0, LON, -1, True)
    globalDaily1p0 = ct.interp_1d(lat, globalDaily1p0, LAT, -2, True)

    print('saving..', flush=True, end='')
    if variable.levels is None:
        dims = {'time':dates, 'lat':LAT, 'lon':LON}
    else:
        dims = {'time':dates, 'lev':[l*100 for l in variable.levels], 'lat':LAT, 'lon':LON}

    nct.save(desPath, {variable.name: globalDaily1p0, **dims}, overwrite=True)


def qbud_16d(initTime, desPath, lon, lat, data, variable):
    # constants
    LON = np.r_[30:210+1:0.25]
    LAT = np.r_[-20:20+1:0.25]

    # select 16 days
    mask = (np.array(variable.leads) <= 16 * 24)
    qbud = data[mask, :]
    times = np.array([initTime + lead/24 + variable.shiftHour/24 for lead in variable.leads])
    times = times[mask]

    print('interpolating..', flush=True, end='')
    qbud = ct.interp_1d(lon, qbud, LON, -1, True)
    qbud = ct.interp_1d(lat, qbud, LAT, -2, True)

    print('saving..', flush=True, end='')
    if variable.levels is None:
        dims = {'time':times, 'lat':LAT, 'lon':LON}
    else:
        dims = {'time':times, 'lev':[l*100 for l in variable.levels], 'lat':LAT, 'lon':LON}

    nct.save(desPath, {variable.name: qbud, **dims}, overwrite=True)


@dataclass
class Variable():
    name: str
    levels: list
    leads: list
    outputTypes: list
    shiftHour: int=0
    multipConst: int=1

    def __post_init__(self):
        checkType = chkt.checkType
        checkType(self.name, str, 'name')
        checkType(self.levels, [list, tuple, None], 'levels')
        checkType(self.leads, [list, tuple], 'leads')
        checkType(self.outputTypes, list, 'outputTypes')
        if self.levels is not None:
            for level in self.levels:
                checkType(level, int, 'level')
        for lead in self.leads:
            checkType(lead, int, 'lead')
        for outputType in self.outputTypes:
            checkType(outputType, str, 'outputType')
            if outputType not in [ # invalid output types
                'global_daily_1p0',
                'qbud-16d',
            ]:
                raise NotImplementedError(f'{outputType = }')
        if 0 in self.leads:
            raise ValueError('leads containing 0 would result in ambiguous daily mean')
