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
    modelName = 'CWA_GEPSv2'
    gridFile = f'/nwpr/gfs/com120/9_data/models/griddes/{modelName}.txt'
    members = list(range(32+1))
    srcPathLambda = \
        lambda initTime, member, lead, fileNameKey: tt.float2format(
            initTime, f'%y%m%d%H/E{member:03d}/%Y%m%d%H{lead:04d}/{fileNameKey}'
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
    levels_uvtz = [10, 50, 100, 200, 300, 500, 700, 850, 925, 1000]
    levels_q = [500, 700, 850, 925, 1000]
    outputTypes_uvtqz = ['analysis', 'global_daily_1p0']
    outputTypes_3d_inst = ['analysis', 'global_daily_1p0', 'WNP_highFreq_0p25']
    outputTypes_3d_acc = ['global_daily_1p0', 'WNP_highFreq_0p25']

    leads_3d_inst = [1, *list(range(6, 1080+1, 6))]
    leads_pw = [1, *list(range(6, 96+1, 6)), *list(range(108, 1080+1, 12))]
    leads_uv = [1, *list(range(6, 384+1, 6)), *list(range(396, 1080+1, 12))]
    leads_tqz = [*list(range(6, 384+1, 6)), *list(range(396, 1080+1, 12))]   
    leads_prec = [*list(range(6, 1080+1, 6))]
    leads_olr = [1, *list(range(6, 96, 6)), *list(range(96, 1080+1, 12))]

    return [
            Variable(
                varName='u10',
                fileNameKeys=['B10200GI0G'],
                leads=leads_3d_inst,
                outputTypes=outputTypes_3d_inst,
                grib2Matches=[':UGRD:10 m above ground:'],
                cdoVarName='10u',
            ),
            Variable(
                varName='v10',
                fileNameKeys=['B10210GI0G'],
                leads=leads_3d_inst,
                outputTypes=outputTypes_3d_inst,
                grib2Matches=[':VGRD:10 m above ground:'],
                cdoVarName='10v',
            ),
            Variable(
                varName='t2m',
                fileNameKeys=['B02100GI0G'],
                leads=leads_3d_inst,
                outputTypes=outputTypes_3d_inst,
                grib2Matches=[':TMP:2 m above ground:'],
                cdoVarName='2t',
            ),
            Variable(
                varName='pw',
                fileNameKeys=['X00590GI0G'],
                leads=leads_pw,
                outputTypes=outputTypes_3d_inst,
                grib2Matches=[':PWAT:entire atmosphere'],
                cdoVarName='pwat',
            ),
            Variable(
                varName='mslp',
                fileNameKeys=['SSL010GI0G'],
                leads=leads_3d_inst,
                outputTypes=outputTypes_3d_inst,
                grib2Matches=[':PRMSL:mean sea level:'],
                cdoVarName='prmsl',
            ),
            Variable(
                varName='prec',
                fileNameKeys=['B00623GI0G'],
                leads=leads_prec,
                outputTypes=outputTypes_3d_acc,
                grib2Matches=[':APCP:0 m above ground:'],
                cdoVarName='param8.1.0',
                shiftHour=-3,
                multiplyConstant=4,
            ),
            Variable(
                varName='olr',
                fileNameKeys=['X00340GI0G'],
                leads=leads_olr,
                outputTypes=outputTypes_3d_acc,
                grib2Matches=[':NLWRF:top of atmosphere:'],
                cdoVarName='tnlwrf',
            ),
            Variable(
                varName='u',
                fileNameKeys=plevDmsKeys('200GI0G', levels_uvtz),
                leads=leads_uv,
                outputTypes=outputTypes_uvtqz,
                grib2Matches=[f':UGRD:{l} mb:' for l in levels_uvtz],
            ),
            Variable(
                varName='v',
                fileNameKeys=plevDmsKeys('210GI0G', levels_uvtz),
                leads=leads_uv,
                outputTypes=outputTypes_uvtqz,
                grib2Matches=[f':VGRD:{l} mb:' for l in levels_uvtz],
            ),
            Variable(
                varName='t',
                fileNameKeys=plevDmsKeys('100GI0G', levels_uvtz),
                leads=leads_tqz,
                outputTypes=outputTypes_uvtqz,
                grib2Matches=[f':TMP:{l} mb:' for l in levels_uvtz],
            ),
            Variable(
                varName='q',
                fileNameKeys=plevDmsKeys('500GI0G', levels_q),
                leads=leads_tqz,
                outputTypes=outputTypes_uvtqz,
                grib2Matches=[f':SPFH:{l} mb:' for l in levels_q],
            ),
            Variable(
                varName='z',
                fileNameKeys=plevDmsKeys('000GI0G', levels_uvtz),
                leads=leads_tqz,
                outputTypes=outputTypes_uvtqz,
                grib2Matches=[f':HGT:{l} mb:' for l in levels_uvtz],
                cdoVarName='gh'
            ),
    ]


if __name__ == '__main__':
    main()
