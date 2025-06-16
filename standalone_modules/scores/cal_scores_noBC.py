'''
calculate the acc scores of daily means on 1x1 deg
without bias correction
'''
from dataclasses import dataclass
import pytools as pyt
import numpy as np
import os


def run(model, variable, regions):
    # constants
    desRootDir = '../../data/scores'
    modelDataType = 'global_daily_1p0' # not configured for other types
    modelRootDir = '../../data/processed'
    scoreNames = [
        f'{score}_{stat}' 
        for score in ['acc', 'pcc', 'rmse'] 
        for stat in ['mean', 'std']
    ]
    LON = np.r_[0:360]
    LAT = np.r_[-90:90+1]

    # ---- post init
    fp = pyt.tmt.FlushPrinter()
    initTimes = [model.initTime0 + i for i in range(model.numInits)]
    boundary = [
        min([region.lonw for region in regions]),
        max([region.lone for region in regions]),
        min([region.lats for region in regions]),
        max([region.latn for region in regions]),
    ]

    # get one piece of model data
    ind = int(model.numInits/2) # let's use the middle one 
    dataModTotal, dimsModTotal = pyt.modelreader.readTotal.readTotal(
        model.name, modelDataType, variable.name, 
        getMinMaxs([None]*2, variable.isMultiLevel, boundary),
        [initTimes[ind]], [model.iMember], rootDir=modelRootDir,
    )
    leads, numLeads = dimsModTotal[0], len(dimsModTotal[0])
    obsTimeRange = [min(initTimes), max(initTimes) + numLeads - 1]

    # setup output and check
    desDir = pyt.tt.float2format(
        model.initTime0,
        f'{desRootDir}/{model.name}/E{model.iMember:03d}/%y%m%d/{model.numInits:04d}'
    )

    if not os.path.isdir(desDir):
        fp.print(f'mkdir -p {desDir}')
        os.system(f'mkdir -p {desDir}')

    for region in regions:
        region.desPath = f'{desDir}/{variable.name}_{region.name}.nc'
        if not pyt.ft.canBeWritten(region.desPath):
            raise PermissionError(f'denied to write {region.desPath}')

    allFound = True # check if we can skip it
    for region in regions:
        region.desPath = f'{desDir}/{variable.name}_{region.name}.nc'
        if not os.path.exists(region.desPath):
            allFound = False
            break

        existingVarNames = pyt.nct.getVarNames(region.desPath)
        for scoreName in scoreNames:
            if scoreName not in existingVarNames:
                allFound = False

    if allFound:
        fp.print(f'skip: scores already exists in desPaths {[r.desPath for r in regions]}')
        return


    # ---- talk to me
    fp.print(f'{model = }')
    fp.print(f'{variable = }')
    fp.print(f'{regions = }')
    fp.print(f'initTimes = {"-".join([pyt.tt.float2format(initTimes[i]) for i in [0, -1]])}')
    fp.print(f'{boundary  = }')
    fp.print(f'obsTimeRange = {"-".join([pyt.tt.float2format(d) for d in obsTimeRange])}')

    # ---- read data
    dataObsClim, dimsObsClim = pyt.rt.obsReader.clim(
        variable.name, getMinMaxs(obsTimeRange, variable.isMultiLevel, boundary), variable.source
    ) # reading obs climate
    
    dataObsTotal, dimsObsTotal = pyt.rt.obsReader.total(
        variable.name, getMinMaxs(obsTimeRange, variable.isMultiLevel, boundary), variable.source
    ) # reading obs total

    dataModTotal, dimsModTotal = pyt.modelreader.readTotal.readTotal(
        model.name, modelDataType, variable.name, 
        getMinMaxs([None]*2, variable.isMultiLevel, boundary),
        initTimes, [model.iMember], rootDir=modelRootDir,
    ) # reading model total
    dataModTotal = np.squeeze(dataModTotal, axis=1) # flatten the member dimension

    # ---- conform vertical grids
    if variable.isMultiLevel:
        dimsModTotal[-3] = [l / 100 for l in dimsModTotal[-3]] # Pa -> hPa
        dataObsClim, dataObsTotal, dataModTotal, LEVEL = conformLevels(
            dataObsClim, dataObsTotal, dataModTotal,
            dimsObsClim[-3], dimsObsTotal[-3], dimsModTotal[-3],
        )
    else:
        LEVEL = None

    # ---- conform horizontal grids
    dataObsClim = conformGrid_1p0(dataObsClim, dimsObsClim, LON, LAT)
    dataObsTotal = conformGrid_1p0(dataObsTotal, dimsObsTotal, LON, LAT)
    dataModTotal = conformGrid_1p0(dataModTotal, dimsModTotal, LON, LAT)

    # ---- calculate anomalies
    dataObsAnomalies = subtractClimate(
        dataObsTotal, dataObsClim, dimsObsTotal[0], dimsObsClim[0]
    )

    dataModAnomalies = np.nan * np.ones_like(dataModTotal)
    for iInit, initTime in enumerate(initTimes):
        validTime = [initTime + lead for lead in dimsModTotal[0]]
        dataModAnomalies[iInit, :] = subtractClimate(
            dataModTotal[iInit, :], dataObsClim, validTime, dimsObsClim[0]
        )

    del(dataObsTotal)
    del(dataModTotal)

    # align obs data to model time
    dataValidAnomalies = np.nan * np.ones_like(dataModAnomalies)
    for iInit, initTime in enumerate(initTimes):
        dataValidAnomalies[iInit, :] = dataObsAnomalies[iInit:iInit+numLeads, :]

    cal_write_acc(dataModAnomalies, dataValidAnomalies, LON, LAT, LEVEL, regions, leads)
    cal_write_pcc(dataModAnomalies, dataValidAnomalies, LON, LAT, LEVEL, regions, leads)
    cal_write_rmse(dataModAnomalies, dataValidAnomalies, LON, LAT, LEVEL, regions, leads)
    fp.print(f'files saved: {[r.desPath for r in regions]}')

def save(path, names, datas, leads, level, region): 
    for name, data in zip(names, datas):
        if level is None: 
            pyt.nct.save(path, {name: data, 'lead': leads}, overwrite=True)
        else:
            pyt.nct.save(path, {name: data, 'lead': leads, 'level': level}, overwrite=True)

    pyt.nct.ncwriteatt(path, '/', 'boundary', '_'.join([str(b) for b in region.boundary]))


def cal_write_acc(f, o, LON, LAT, LEVEL, regions, leads):
    acc = np.nansum(f * o, axis=0) \
        / np.sqrt(np.nansum(f ** 2, axis=0)) \
        / np.sqrt(np.nansum(o ** 2, axis=0)) # [lead, (lev,) lat, lon]

    slices = [slice(None)] * acc.ndim
    for region in regions: # area mean, std and save separately
        # crop out the region 
        latSlice = pyt.ct.value2Slice(LAT, region.lats, region.latn)
        lonSlice = pyt.ct.value2Slice(LON, region.lonw, region.lone)
        slices[-1], slices[-2] = lonSlice, latSlice
        cosdlat = np.cos(LAT[latSlice] / 180 * np.pi)[:, None] # weighted by latitude

        # cal mean and std
        acc_mean = np.nanmean(acc[*slices] * cosdlat, axis=(-1, -2), keepdims=True) \
            / np.nanmean(cosdlat)
        acc_std = np.sqrt(
            np.nanmean((acc[*slices] - acc_mean) ** 2 * cosdlat, axis=(-1, -2)) \
            / np.nanmean(cosdlat)
        )

        # flatten
        acc_mean = acc_mean.squeeze()
        acc_std = acc_std.squeeze()

        # save
        save(region.desPath, ['acc_mean', 'acc_std'], [acc_mean, acc_std], leads, LEVEL, region)


def cal_write_pcc(f, o, LON, LAT, LEVEL, regions, leads):
    for region in regions: 
        # crop out the region
        slices = [slice(None)] * f.ndim
        latSlice = pyt.ct.value2Slice(LAT, region.lats, region.latn)
        lonSlice = pyt.ct.value2Slice(LON, region.lonw, region.lone)
        slices[-1], slices[-2] = lonSlice, latSlice
        cosdlat = np.cos(LAT[latSlice] / 180 * np.pi)[:, None] # weighted by latitude

        # [init, lead, (lev,)]
        pcc = np.nansum(f[*slices] * o[*slices] * cosdlat, axis=(-1, -2)) \
                / np.sqrt(np.nansum(f[*slices] ** 2 * cosdlat, axis=(-1, -2))) \
                / np.sqrt(np.nansum(o[*slices] ** 2 * cosdlat, axis=(-1, -2))) 

        pcc_mean = np.nanmean(pcc, axis=0)
        pcc_std = np.nanstd(pcc, axis=0)

        # flatten
        pcc_mean = pcc_mean.squeeze()
        pcc_std = pcc_std.squeeze()

        # save
        save(region.desPath, ['pcc_mean', 'pcc_std'], [pcc_mean, pcc_std], leads, LEVEL, region)


def cal_write_rmse(f, o, LON, LAT, LEVEL, regions, leads):
    for region in regions: 
        # crop out the region
        slices = [slice(None)] * f.ndim
        latSlice = pyt.ct.value2Slice(LAT, region.lats, region.latn)
        lonSlice = pyt.ct.value2Slice(LON, region.lonw, region.lone)
        slices[-1], slices[-2] = lonSlice, latSlice
        cosdlat = np.cos(LAT[latSlice] / 180 * np.pi)[:, None] # weighted by latitude

        # [init, lead, (lev,)]
        rmse = np.sqrt(
            np.nanmean((f[*slices] - o[*slices]) ** 2 * cosdlat, axis=(-1, -2)) 
        )

        rmse_mean = np.nanmean(rmse, axis=0)
        rmse_std = np.nanstd(rmse, axis=0)

        # flatten
        rmse_mean = rmse_mean.squeeze()
        rmse_std = rmse_std.squeeze()

        # save
        save(region.desPath, ['rmse_mean', 'rmse_std'], [rmse_mean, rmse_std], leads, LEVEL, region)


def conformGrid_1p0(data, dims, LON, LAT):
    data = pyt.ct.interp_1d(dims[-1], data, LON, -1, extrapolate=True)
    data = pyt.ct.interp_1d(dims[-2], data, LAT, -2, extrapolate=True)
    return data
    

def conformLevels(data1, data2, data3, level1, level2, level3):
    level = list(set(level1) & set(level2) & set(level3))
    level.sort()
    data1 = pyt.ct.interp_1d(level1, data1, level, -3)
    data2 = pyt.ct.interp_1d(level2, data2, level, -3)
    data3 = pyt.ct.interp_1d(level3, data3, level, -3)
    return data1, data2, data3, level


def subtractClimate(dataTotal, dataClim, timeTotal, timeClim):
    timeClim = list(timeClim)
    index_time = [timeClim.index(pyt.tt.dayOfYear229(t)-1) for t in timeTotal]
    anomalies = dataTotal - dataClim[index_time, :]
    return anomalies


def getMinMaxs(timeRange, isMultiLevel, boundary):
    if isMultiLevel:
        return [timeRange, [None]*2, boundary[2:], boundary[:2]]
    else:
        return  [timeRange, boundary[2:], boundary[:2]]


@dataclass
class Region():
    name: str
    boundary: list

    def __post_init__(self):
        self.desPath = ''
        self.lonw, self.lone, self.lats, self.latn = self.boundary
        if self.lonw > self.lone:
            raise ValueError('lon west cannot be greater than east')
        if self.lats > self.latn:
            raise ValueError('lat south cannot be greater than north')


@dataclass
class Variable():
    name: str
    source: str

    def __post_init__(self):
        self.isAccumulated = self.name in ['olr', 'prec']
        self.isMultiLevel = self.name in ['u', 'v', 'w', 't', 'q', 'z', 'r']


@dataclass
class Model():
    name: str
    iMember: int
    initTime0: float
    numInits: int 
    
