#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import numpy as np
from pytools.modelreader.readTotal import readTotal as readModel
from pytools.filetools import canBeWritten
from pytools import timetools as tt
from pytools import nctools as nct
from calendar import isleap
import os

def main():
    regeps()

def recfs():
    for varName in ['u850']:
        for initTime in range(
            tt.ymd2int(2000, 1, 1),
            tt.ymd2int(2000, 2, 28)+1,
        ):
            calAndSaveClim(
                modelName='re_cfsv2_dm',
                dataType='global_daily_1p0',
                varName=varName,
                member=0,
                initDateAs366=tt.dayOfYear229(initTime),
                minMaxYear=[1991, 2020],
                forceUpdate=True
            )

def regeps():
    for varName in ['mslp', 'olr', 'prec', 'pw', 'q', 't', 't2m', 'u', 'u10', 'v', 'v10', 'z']:
        for iDay366 in range(31+29+1, 31+29+31+1):
            for dataType in ['analysis', 'global_daily_1p0']:
                if varName not in ['u', 'v', 'w', 't', 'q', 'z'] and dataType == 'analysis':
                    continue
                for climYear in [[2006, 2020]]:
                    calAndSaveClim(
                        modelName='re_GEPSv3_newCFSR',
                        dataType=dataType,
                        varName=varName,
                        member=0,
                        initDateAs366=iDay366,
                        minMaxYear=climYear,
                        forceUpdate=True
                    )


def calAndSaveClim(
    modelName,
    dataType,
    varName,
    member=0,
    initDateAs366=1,
    minMaxYear=[2001, 2020],
    forceUpdate=False
):

    #
    # ---- input settings
    #
    desdir = f'../processed/{modelName}/clim/E{member:03d}/1day/{varName}'
    __, month, day = tt.float2ymd(
        tt.ymd2float(2000, 1, 1) + initDateAs366 - 1
    )
    desname = f'{desdir}/' \
        + f'{dataType}_{varName}_{month:02d}{day:02d}' \
        + f'_{minMaxYear[0]}_{minMaxYear[1]}_1day.nc'
    numDims = get_numDims(varName)
    initTimes = [
        tt.ymd2float(year, month, day)
        for year in range(minMaxYear[0], minMaxYear[1]+1)
        if not (month==2 and day==29 and not isleap(year))
    ]
    minMaxX = [0, 360]
    minMaxY = [-90, 90]
    minMaxLead = [-np.inf, np.inf]

    #
    # ---- checking output status
    #
    if not os.path.isdir(desdir):
        os.system(f'mkdir -p {desdir}')

    if os.path.isfile(desname) and not forceUpdate:
        print(f' output file already exists, manually delete it to proceed:')
        print(f'   del {desname}')
        return

    if not canBeWritten(desname):
        print(f' permission denied to write the file: {desname}')
        return

    #
    # ---- dispay status
    #
    print(f'{modelName=}')
    print(f'{varName=}')
    print(f'month/day = {month:02d}/{day:02d}')
    print(f'{minMaxYear=}')

    #
    # ---- calculating
    #
    if dataType != 'analysis' and numDims == 3:
        minMaxs = [minMaxLead, minMaxY, minMaxX]
    elif dataType != 'analysis' and numDims == 4:
        minMaxs = [minMaxLead, [-np.inf, np.inf], minMaxY, minMaxX]
    elif dataType == 'analysis' and numDims == 3:
        minMaxs = [minMaxY, minMaxX]
    elif dataType == 'analysis' and numDims == 4:
        minMaxs = [[-np.inf, np.inf], minMaxY, minMaxX]

    data, dims = readModel(
        modelName=modelName,
        dataType=dataType,
        varName=varName,
        minMaxs=minMaxs,
        initTimes=initTimes,
        members=[member],
    )

    if data is None:
        print('[Fatal Error] model reader failed.')
        return

    if varName == 'w':
        data[(np.abs(data)>1e2)] = np.nan
    
    data = np.squeeze(data, axis=1)  # pop away the member dimension
    data = np.nanmean(data, axis=0)  # mean over years

    #
    # ---- saving
    #
    print(f' saving output to {desname}..')
    if dataType != 'analysis' and numDims == 4:
        dimNames = ['lead', 'plev', 'lat', 'lon']
    elif dataType != 'analysis' and numDims == 3:
        dimNames = ['lead', 'lat', 'lon']
    elif dataType == 'analysis' and numDims == 4:
        dimNames = ['plev', 'lat', 'lon']
    elif dataType == 'analysis' and numDims == 3:
        dimNames = ['lat', 'lon']

    nct.save(
        desname,
        {
            varName: data,
            **{dimName: dim for dimName, dim in zip(dimNames, dims)}
        },
        overwrite=True
    )
    return


def get_numDims(varName):
    if varName in ['u', 'v', 'w', 't', 'q', 'z', 'vp', 'sf']:
        return 4
    elif varName in ['u10', 'v10', 't2m', 'pw', 'prec', 'mslp', 'olr', 'u850']:
        return 3
    else:
        raise ValueError(f'unrecognized variable name of "{varName}"')


if __name__ == '__main__':
    main()
    # ---- for testing ---- #
    # calAndSaveClim(
    #     modelName='re_CWA_CFSv2',
    #     dataType='global_daily_1p0',
    #     varName='u',
    #     member=0,
    #     initDateAs366=1,
    #     minMaxYear=[2006, 2018]
    # )
    #----  ----  ---- ---- #

    # tStart = tt.ymd2float(2000, 1, 31)
    # tEnd   = tt.ymd2float(2000, 1, 31)
    # t0     = tt.ymd2float(2000, 1, 1)

    # iDateStart = int(tStart - t0 + 1)
    # iDateEnd   = int(tEnd   - t0 + 1)

    # for varName in [
    #     't2m', 'mslp', 'u10', 'v10', 'olr', 'prec',
    #     'u', 'v', 't', 'q', 'z'
    # ]:
    #     for date in range(iDateStart, iDateEnd+1):
    #         calAndSaveClim(
    #             modelName='re_GEPSv3_CFSR',
    #             dataType='global_daily_1p0',
    #             varName=varName,
    #             member=0,
    #             initDateAs366=date,
    #             minMaxYear=[2001, 2020]
    #         )

    # c=clim(modelName='ana_CFSR', varName='olr', month=1, minMaxYear=[2001, 2020]).main()
    # c=clim(modelName='ana_CFSR', varName='u', month=1, minMaxYear=[2001, 2020]).main()
    # c=clim(modelName='ana_CFSR', varName='v', month=1, minMaxYear=[2001, 2020]).main()
    # c=clim(modelName='ana_CFSR', varName='z', month=1, minMaxYear=[2001, 2020]).main()
    # c=clim(modelName='ana_CFSR', varName='prec', month=1, minMaxYear=[2001, 2020]).main()
    # c=clim(modelName='ana_CFSR', varName='sf', month=1, minMaxYear=[2001, 2020]).main()
    # c=clim(modelName='ana_CFSR', varName='vp', month=1, minMaxYear=[2001, 2020]).main()

    # modelName = 'ana_CFSR'
    # numLeads = 1
    # numInits = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
    #           7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
    # for month in [8, 9]:
    #     for varName in ['u', 'v', 't', 'q', 'z', 'sf', 'vp']:
    #         c = clim(modelName=modelName, varName=varName,
    #                  numInits=numInits[month], numLeads=numLeads, month=month, minMaxYear=[2001, 2020]).main()

    # modelName = 're_GEPSv3_CFSR'
    # for month in [1, 7]:
    #   for varName in ['u', 'v', 't', 'q', 'z', 'sf', 'vp', 'u10', 'v10', 't2m', 'prec', 'mslp']:
    #     if varName == 'prec':
    #       numLeads = 45
    #     else:
    #       numLeads = 46
    #     c=clim(modelName=modelName, varName=varName, numLeads=numLeads, month=month, minMaxYear=[2006, 2020]).main()
