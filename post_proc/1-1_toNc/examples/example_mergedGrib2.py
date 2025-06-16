#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
from pytools.modeldata.process import Processor, Variable, plevDmsKeys
import pytools.timetools as tt


def main():
    rootSrcDir = '/nwpr/gfs/com120/9_data/models/op'
    rootDesDir = '/nwpr/gfs/com120/9_data/models/processed'
    workDir    = '/nwpr/gfs/com120/9_data/models/code/wdir'
    initTimes  = [
        tt.today() - 0.5 - delayDay - delayHour
        for delayDay in range(7+1)
        for delayHour in [0, 0.5]
    ]    
    modelName  = 'NCEP_CTRL'
    gridFile   = f'/nwpr/gfs/com120/9_data/models/griddes/{modelName}.txt' 
    members = [0]
    srcPathLambda = lambda initTime, member, lead, fileNameKey: tt.float2format(
        initTime, f'%Y/%m/%d%Hz/gec00.pgrb2a.0p50.f{lead:03d}.%y%m%d%H'
    )

    # ==== ==== ==== ==== #
    processor = Processor(
        modelName=modelName,
        rootDesDir=rootDesDir,
        rootSrcDir=rootSrcDir,
        workDir=workDir,
        gridFile=gridFile,
        srcPathLambda=srcPathLambda,
        initTimes=initTimes,
        members=members,
        variables=getVariables(),
        printDesSummary=True,
    )
    processor.run()


def getVariables():
    
    levels_uvz    = [10, 50, 100, 200, 300, 500, 700, 850, 925, 1000]
    levels_t      = [10, 50, 100, 200,      500, 700, 850, 925, 1000]
    levels_r      = [500, 700, 850, 925, 1000]
    outputTypes_uvtrz   = ['analysis', 'global_daily_1p0']
    outputTypes_3d_inst = ['analysis', 'global_daily_1p0', 'WNP_highFreq_0p25']
    outputTypes_3d_acc  = [            'global_daily_1p0', 'WNP_highFreq_0p25']

    return [
        Variable(
            varName='u10',
            leads=list(range(6, 840+1, 6)),
            outputTypes=outputTypes_3d_inst,
            grib2Matches=[':UGRD:10 m above ground:'],
            numRecordsPerFile=1,
            cdoVarName='10u',
        ),
        Variable(
            varName='v10',
            leads=list(range(6, 840+1, 6)),
            outputTypes=outputTypes_3d_inst,
            grib2Matches=[':VGRD:10 m above ground:'],
            numRecordsPerFile=1,
            cdoVarName='10v',
        ),
        Variable(
            varName='t2m',
            leads=list(range(6, 840+1, 6)),
            outputTypes=outputTypes_3d_inst,
            grib2Matches=[':TMP:2 m above ground:'],
            numRecordsPerFile=1,
            cdoVarName='2t',
        ),
        Variable(
            varName='pw',
            leads=list(range(6, 840+1, 6)),
            outputTypes=outputTypes_3d_inst,
            grib2Matches=[':PWAT:entire atmosphere'],
            numRecordsPerFile=1,
            cdoVarName='pwat',
        ),
        Variable(
            varName='mslp',
            leads=list(range(6, 840+1, 6)),
            outputTypes=outputTypes_3d_inst,
            grib2Matches=[':PRMSL:mean sea level:'],
            numRecordsPerFile=1,
            cdoVarName='prmsl',
            multiplyConstant=0.01,
        ),
        Variable(
            varName='prec',
            leads=list(range(6, 840+1, 6)),
            outputTypes=outputTypes_3d_acc,
            grib2Matches=[':APCP:surface:'],
            numRecordsPerFile=1,
            cdoVarName='tp',
            shiftHour=3,
            multiplyConstant=4,
        ),
        Variable(
            varName='olr',
            leads=list(range(6, 840+1, 6)),
            outputTypes=outputTypes_3d_acc,
            grib2Matches=[':ULWRF:top of atmosphere:'],
            numRecordsPerFile=1,
            cdoVarName='sulwrf',
            shiftHour=3,
        ),
        Variable(
            varName='u',
            leads=list(range(6, 840+1, 6)),
            outputTypes=outputTypes_uvtrz,
            grib2Matches=[f':UGRD:{l} mb:' for l in levels_uvz],
            numRecordsPerFile=len(levels_uvz),
        ),
        Variable(
            varName='v',
            leads=list(range(6, 840+1, 6)),
            outputTypes=outputTypes_uvtrz,
            grib2Matches=[f':VGRD:{l} mb:' for l in levels_uvz],
            numRecordsPerFile=len(levels_uvz),
        ),
        Variable(
            varName='t',
            leads=list(range(6, 840+1, 6)),
            outputTypes=outputTypes_uvtrz,
            grib2Matches=[f':TMP:{l} mb:' for l in levels_t],
            numRecordsPerFile=len(levels_t),
        ),
        Variable(
            varName='z',
            leads=list(range(6, 840+1, 6)),
            outputTypes=outputTypes_uvtrz,
            grib2Matches=[f':HGT:{l} mb:' for l in levels_uvz],
            numRecordsPerFile=len(levels_uvz),
            cdoVarName='gh'
        ),
        Variable(
            varName='r',
            leads=list(range(6, 840+1, 6)),
            outputTypes=outputTypes_uvtrz,
            grib2Matches=[f':RH:{l} mb:' for l in levels_r],
            numRecordsPerFile=len(levels_r),
        ),
    ]


if __name__ == '__main__':
    main()
