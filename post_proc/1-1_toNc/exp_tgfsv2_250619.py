#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
from pytools.modeldata.process import Processor, Variable, plevDmsKeys
import pytools.timetools as tt


def main():
    rootDir = '/nwpr/gfs/com120/6_weatherModelDiag'
    rootSrcDir = f'{rootDir}/data/source'
    rootDesDir = f'{rootDir}/data/processed'
    workDir    = f'{rootDir}/wdir'
    initTimes  = [
        tt.format2float(strDate, '%y%m%d') for strDate in [
            '250416',
            '250421',
            '250426',
            '250501',
            '250506',
            '250511',
            '250516',
        ]
    ]
    modelName = 'exp_tgfsv2_250619'
    gridFile = f'/nwpr/gfs/com120/9_data/models/griddes/CWA_GEPSv2.txt'
    members = list(range(1, 21))
    srcPathLambda = \
        lambda initTime, member, lead, fileNameKey: tt.float2format(
            initTime, f'%y%m%d%H_{member:03d}.ufs/TCo383/%Y%m%d%H{lead:04d}/{fileNameKey}'
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
    levels = [200, 850]
    outputTypes = ['global_daily_1p0']

    leads  = list(range(24, 480+1, 24))

    return [
            Variable(
                varName='olr',
                fileNameKeys=['X0034FGI0G'],
                leads=leads,
                outputTypes=outputTypes,
                grib2Matches=[':NLWRF:top of atmosphere:'],
                cdoVarName='avg_tnlwrf',
                shiftHour=-12,
            ),
            Variable(
                varName='u',
                fileNameKeys=plevDmsKeys('200GI0G', levels),
                leads=leads,
                outputTypes=outputTypes,
                grib2Matches=[f':UGRD:{l} mb:' for l in levels],
            ),
            # ###################
            # Variable(
            #     varName='u10',
            #     fileNameKeys=['B10200GI0G'],
            #     leads=leads_3d_inst,
            #     outputTypes=outputTypes_3d_inst,
            #     grib2Matches=[':UGRD:10 m above ground:'],
            #     cdoVarName='10u',
            # ),
            # Variable(
            #     varName='v10',
            #     fileNameKeys=['B10210GI0G'],
            #     leads=leads_3d_inst,
            #     outputTypes=outputTypes_3d_inst,
            #     grib2Matches=[':VGRD:10 m above ground:'],
            #     cdoVarName='10v',
            # ),
            # Variable(
            #     varName='t2m',
            #     fileNameKeys=['B02100GI0G'],
            #     leads=leads_3d_inst,
            #     outputTypes=outputTypes_3d_inst,
            #     grib2Matches=[':TMP:2 m above ground:'],
            #     cdoVarName='2t',
            # ),
            # Variable(
            #     varName='pw',
            #     fileNameKeys=['X00590GI0G'],
            #     leads=leads_pw,
            #     outputTypes=outputTypes_3d_inst,
            #     grib2Matches=[':PWAT:entire atmosphere'],
            #     cdoVarName='pwat',
            # ),
            # Variable(
            #     varName='mslp',
            #     fileNameKeys=['SSL010GI0G'],
            #     leads=leads_3d_inst,
            #     outputTypes=outputTypes_3d_inst,
            #     grib2Matches=[':PRMSL:mean sea level:'],
            #     cdoVarName='prmsl',
            # ),
            # Variable(
            #     varName='prec',
            #     fileNameKeys=['B00623GI0G'],
            #     leads=leads_prec,
            #     outputTypes=outputTypes_3d_acc,
            #     grib2Matches=[':APCP:0 m above ground:'],
            #     cdoVarName='param8.1.0',
            #     shiftHour=-3,
            #     multiplyConstant=4,
            # ),
            # Variable(
            #     varName='v',
            #     fileNameKeys=plevDmsKeys('210GI0G', levels_uvtz),
            #     leads=leads_uv,
            #     outputTypes=outputTypes_uvtqz,
            #     grib2Matches=[f':VGRD:{l} mb:' for l in levels_uvtz],
            # ),
            # Variable(
            #     varName='t',
            #     fileNameKeys=plevDmsKeys('100GI0G', levels_uvtz),
            #     leads=leads_tqz,
            #     outputTypes=outputTypes_uvtqz,
            #     grib2Matches=[f':TMP:{l} mb:' for l in levels_uvtz],
            # ),
            # Variable(
            #     varName='q',
            #     fileNameKeys=plevDmsKeys('500GI0G', levels_q),
            #     leads=leads_tqz,
            #     outputTypes=outputTypes_uvtqz,
            #     grib2Matches=[f':SPFH:{l} mb:' for l in levels_q],
            # ),
            # Variable(
            #     varName='z',
            #     fileNameKeys=plevDmsKeys('000GI0G', levels_uvtz),
            #     leads=leads_tqz,
            #     outputTypes=outputTypes_uvtqz,
            #     grib2Matches=[f':HGT:{l} mb:' for l in levels_uvtz],
            #     cdoVarName='gh'
            # ),
    ]


if __name__ == '__main__':
    main()
