#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import pytools as pyt
import os


def getPath(modelName, member, initTime, varName):
    root = f'../../data/processed/{modelName}'
    return pyt.tt.float2format(
        initTime,
        f'{root}/%Y/%m/%dz%H/E{member:03d}/global_daily_1p0_{varName}.nc'
    )


def main():
    initTimes = [
        pyt.tt.ymd2float(2024, 1, 1) + i 
        for i in range(31)
    ]
    modelNames = [
        'exp_gepsv3_da-off',
        'exp_gepsv3_da-all',
        'exp_gepsv3_da-sst',
    ]
    numMembers = 1
    for initTime in initTimes:
        for modelName in modelNames:
            for iMember in range(numMembers):
                run(initTime, modelName, iMember)


def run(initTime, modelName, member):
    path_u = getPath(modelName, member, initTime, "u")
    path_v = getPath(modelName, member, initTime, "v")
    path_vp = getPath(modelName, member, initTime, "vp")
    command = '/nwpr/gfs/com120/0_tools/bashtools/cdo_uv2vpsf'
    command += f' {path_u} {path_v} {path_vp} u v r360x181'
    print(command)
    os.system(command)


if __name__ == '__main__':
    main()
