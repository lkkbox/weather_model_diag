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

        data = self._post_proc(data, variable)
        return data


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

        data = self._post_proc(data, variable)
        return data


    def obs_to_valid(self, obs, model, initTimes):
        valid = Data()
        valid.vals = np.nan * np.ones((*model.vals.shape[:2], *obs.vals.shape[1:]))
        obsTime = list(obs.dims[0])
        for iInit in range(model.vals.shape[0]):
            for iLead in range(model.vals.shape[1]):
                validDate = initTimes[iInit] + iLead
                index = obsTime.index(validDate)
                # print(validDate)
                # print(obsTime)
                # exit()
                valid.vals[iInit, iLead, :] = obs.vals[index, :]

        valid.dims = obs.dims

        if model.vals.ndim == 4: # 3d variables
            return valid, model

        elif model.vals.ndim != 5:
            raise NotImplementedError(f'help, how to deal with ndim = {model.vals.ndim}')

        valid, model = self.conform_axis(valid, model, -3) # find the shared level
        return valid, model


    def read_mod_total(self, model, member, variable, numLeads):
        minMaxs = self._get_glb_min_maxs(variable.ndim, [0, numLeads-0.01])
        data = Data()
        data.vals, data.dims = pyt.modelreader.readTotal.readTotal(
            model.name, self.modelDataType, variable.name, minMaxs,
            model.initTimes, [member], rootDir=self.modDir
        )
        if data.vals is None:
            return None
        data.vals = np.squeeze(data.vals, axis=1) # member
        data.dims[0] = np.floor(data.dims[0]) # set all time to floor

        if variable.ndim == 4:
            data.dims[1] /= 100 # Pa -> hPa

        # padding nans for lead dimension
        if data.vals.shape[1] < numLeads: # not enough lead (TGFS PW :(( )
            print(f'[warning] data is padded by nans because expecting {numLeads=}, but only received {data.vals.shape[1]}')
            delta = numLeads - data.vals.shape[1]
            nanShape = (data.vals.shape[0], delta, *data.vals.shape[2:])
            data.vals = np.concatenate(
                (data.vals, np.nan * np.ones((nanShape))),
                axis = 1
            )
            data.dims[0] = np.concatenate(
                (data.dims[0], np.nan * np.ones((delta))),
                axis = 0
            )

        data = self._post_proc(data, variable)
        return data

    def read_mod_clim(self, model, member, variable, numLeads, climYears):
        minMaxs = self._get_glb_min_maxs(variable.ndim, [0, numLeads-0.01])
        data = Data()
        data.vals, data.dims = pyt.modelreader.readModelClim.readModelClim(
            model.name, self.modelDataType, variable.name, minMaxs,
            model.initTimes, [member], climYears, rootDir=self.modDir
        )
        if data.vals is None:
            return None
        data.vals = np.squeeze(data.vals, axis=1) # member
        data.dims[0] = np.floor(data.dims[0]) # set all time to floor

        if variable.ndim == 4:
            data.dims[1] /= 100 # Pa -> hPa

        data = self._post_proc(data, variable)
        return data


    def conform_axis(self, data1, data2, axis):
        # find the shared dimension values
        dim1 = list(data1.dims[axis])
        dim2 = list(data2.dims[axis])
        dimShared = [d for d in dim1 if d in dim2]
        
        # get the index for each data
        ind1 = [dim1.index(d) for d in dimShared]
        ind2 = [dim2.index(d) for d in dimShared]

        # extract the indices of each data
        data1.vals = np.swapaxes(data1.vals, 0, axis)
        data2.vals = np.swapaxes(data2.vals, 0, axis)
        data1.vals = data1.vals[ind1, :]
        data2.vals = data2.vals[ind2, :]
        data1.vals = np.swapaxes(data1.vals, 0, axis)
        data2.vals = np.swapaxes(data2.vals, 0, axis)

        # overwrite the dimension values
        data1.dims[axis] = dimShared
        data2.dims[axis] = dimShared

        return data1, data2

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


    def _post_proc(self, data, variable):
        data = self._regrid_xy(data)

        if variable.name == 'mslp': # fix the mslp value/units :((
            for i in range(data.vals.shape[0]):
                mean = np.nanmean(data.vals[i, :])
                if mean > 1000 * 10:
                    data.vals[i, :] /= 100 # -> hPa
                elif mean < 1000 / 10: # GEPSv3 correction :((
                    data.vals[i, :] *= 100 

        return data
