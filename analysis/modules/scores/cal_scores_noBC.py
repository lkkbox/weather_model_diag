'''
calculate the acc scores of daily means on 1x1 deg
without bias correction
'''
import pytools as pyt
import numpy as np
import os


def run(model, variable, regions, dataDir):
    # constants
    desRootDir = f'{dataDir}/scores'
    modelDataType = 'global_daily_1p0' # not configured for other types
    modelRootDir = f'{dataDir}/processed'
    scoreNames = [
        f'{score}_{stat}' 
        for score in ['acc', 'pcc', 'rmse'] 
        for stat in ['mean', 'std']
    ]
    LON = np.r_[0:360]
    LAT = np.r_[-90:90+1]

    # ---- post init
    fp = pyt.tmt.FlushPrinter()
    initTimes = model.initTimes
    boundary = [
        min([region.lonw for region in regions]),
        max([region.lone for region in regions]),
        min([region.lats for region in regions]),
        max([region.latn for region in regions]),
    ]

    # get one piece of model data
    numLeads = pyt.modelreader.readTotal.getMaxNumLeads(
        model.name, modelDataType, variable.name, 
        model.initTimes, model.members,
        rootDir=modelRootDir, warning=True,
    )

    obsTimeRange = [min(initTimes), max(initTimes) + numLeads - 1]

    # setup output and check
    skipMembers = [True for __ in model.members]
    for iMember, member in enumerate(model.members):
        desPath = getDesPath(desRootDir, model, member, variable, regions[0])

        desDir = os.path.dirname(desPath)
        if not os.path.isdir(desDir):
            fp.print(f'mkdir -p {desDir}')
            os.system(f'mkdir -p {desDir}')

        for region in regions:
            desPath = getDesPath(desRootDir, model, member, variable, region)
            if not pyt.ft.canBeWritten(desPath):
                raise PermissionError(f'denied to write {desPath}')

        # check if we can skip it
        for region in regions:
            desPath = getDesPath(desRootDir, model, member, variable, region)
            if not os.path.exists(desPath):
                skipMembers[iMember] = False
                break

            existingVarNames = pyt.nct.getVarNames(desPath)
            for scoreName in scoreNames:
                if scoreName not in existingVarNames:
                    skipMembers[iMember] = False

    if all(skipMembers):
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
        variable.name, getMinMaxs(obsTimeRange, variable.isMultiLevel, boundary),
        variable.obs_source
    ) # reading obs climate
    
    dataObsTotal, dimsObsTotal = pyt.rt.obsReader.total(
        variable.name, getMinMaxs(obsTimeRange, variable.isMultiLevel, boundary),
        variable.obs_source
    ) # reading obs total

    for skip, member in zip(skipMembers, model.members):
        if skip:
            fp.print(f'skip member = {model.member}')
            continue

        _run_member(model, variable, regions, dataDir, member, boundary,
                    dataObsClim, dimsObsClim, dataObsTotal, dimsObsTotal)



        

def _run_member(model, variable, regions, dataDir, member, boundary,
                dataObsClim, dimsObsClim, dataObsTotal, dimsObsTotal):
    modelDataType = "global_daily_1p0" # not supported for others yet
    modelRootDir = f'{dataDir}/processed'

    dataModTotal, dimsModTotal = pyt.modelreader.readTotal.readTotal(
        model.name, modelDataType, variable.name, 
        getMinMaxs([None]*2, variable.isMultiLevel, boundary),
        model.initTimes, [member], rootDir=modelRootDir,
    ) # reading model total
    dataModTotal = np.squeeze(dataModTotal, axis=1) # flatten the member dimension
    exit()

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


def getDesPath(desRootDir, model, member, variable, region):
    desDir = pyt.tt.float2format(
        model.initTime0,
        f'{desRootDir}/{model.name}/E{member:03d}/%y%m%d/{model.numInitTimes:04d}'
    )
    return f'{desDir}/{variable.name}_{region.name}.nc'


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

