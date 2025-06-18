from dataclasses import dataclass
import pytools as pyt
import numpy as np
import copy

@dataclass
class Data:
    vals: np.ndarray = None
    dims: list[np.array] = None

    def __sub__(self, other):
        return Data(self.vals - other.vals, self.dims)


class Reader:
    '''
    level: use hPa
    lon, lat: global
    '''


    def __init__(self, dataDir, obsSubDir='obs', modSubDir='processed',
                 regrid_delta_x=1, regrid_delta_y=1, modelDataType='global_daily_1p0'):
        self.obsDir = f'{dataDir}/{obsSubDir}'
        self.modDir = f'{dataDir}/{modSubDir}'
        self.regrid_lon = np.r_[0:360:regrid_delta_x]
        self.regrid_lat = np.r_[-90:90+1:regrid_delta_y]
        self.NX = len(self.regrid_lon)
        self.NY = len(self.regrid_lat)
        self.modelDataType = modelDataType


    def get_valid_time_range(self, initTimes, numLeads):
        return [min(initTimes), max(initTimes)+numLeads]


    def read_obs_total(self, variable, timeRange, source=None):
        minMaxs = self._get_glb_min_maxs(variable.ndim, timeRange)
        data = Data()
        data.vals, data.dims = pyt.rt.obsReader.total(variable.name, minMaxs, source)
        data.dims[0] = np.floor(data.dims[0]) # set all time to floor
        return self._regrid_xy(data)


    def read_obs_clim(self, variable, timeRange, climYears=[2001, 2020], source=None):
        minMaxs = self._get_glb_min_maxs(variable.ndim, timeRange)
        data = Data()
        data.vals, data.dims = pyt.rt.obsReader.clim(
            variable.name, minMaxs, source, climYears=climYears
        )

        timeClim = list(data.dims[0])
        timeRequest = np.r_[np.floor(timeRange[0]):np.floor(timeRange[1])+1]
        iDayRequest = [pyt.tt.dayOfYear229(t) - 1 for t in timeRequest]
        indClim = [timeClim.index(iday) for iday in iDayRequest]

        data.vals = data.vals[indClim, :]
        data.dims[0] = timeRequest
        return self._regrid_xy(data)


    def obs_to_valid(self, obs, model):
        data = Data()
        data.vals = np.nan * np.ones((model.numInitTimes, model.numLeads, self.NY, self.NX))
        obsTime = list(obs.dims[0])
        for iInit in range(model.numInitTimes):
            for iLead in range(model.numLeads):
                validDate = model.initTimes[iInit] + iLead
                index = obsTime.index(validDate)
                data.vals[iInit, iLead, :] = obs.vals[index, :]

        return data



    def read_mod_total(self, model, member, variable, numLeads):
        minMaxs = self._get_glb_min_maxs(variable.ndim, [0, numLeads-0.01])
        data = Data()
        data.vals, data.dims = pyt.modelreader.readTotal.readTotal(
            model.name, self.modelDataType, variable.name, minMaxs,
            model.initTimes, [member], rootDir=self.modDir
        )
        data.vals = np.squeeze(data.vals, axis=1) # member
        data.dims[0] = np.floor(data.dims[0]) # set all time to floor
        return self._regrid_xy(data)


    def read_mod_clim(self, model, member, variable, numLeads, climYears):
        minMaxs = self._get_glb_min_maxs(variable.ndim, [0, numLeads-0.01])
        data = Data()
        data.vals, data.dims = pyt.modelreader.readModelClim.readModelClim(
            model.name, self.modelDataType, variable.name, minMaxs,
            model.initTimes, [member], climYears, rootDir=self.modDir
        )
        data.vals = np.squeeze(data.vals, axis=1) # member
        data.dims[0] = np.floor(data.dims[0]) # set all time to floor
        return self._regrid_xy(data)


    def _get_glb_min_maxs(self, ndim, time):
        minMaxs = [[None] *2 ] * ndim
        minMaxs[0] = time
        return minMaxs


    def _regrid_xy(self, data):
        data.vals = pyt.ct.interp_1d(data.dims[-1], data.vals, self.regrid_lon, -1, True)
        data.vals = pyt.ct.interp_1d(data.dims[-2], data.vals, self.regrid_lat, -2, True)
        data.dims[-1] = copy.copy(self.regrid_lon)
        data.dims[-2] = copy.copy(self.regrid_lat)
        return data


