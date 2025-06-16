#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import pytools as pyt
from rmm_runner import Model, run

def main():
    initTimes = [pyt.tt.ymd2float(2025, 1, 1) + i for i in range(90)]
    models = [
        # Model(
        #     modelName='CWA_GEPSv3', 
        #     initTimes=initTimes, 
        #     members=list(range(21)), 
        #     numLeads=45,
        #     hasClim=True,
        # ),
        Model(
            modelName='NCEP_CTRL', 
            initTimes=initTimes, 
            members=[0], 
            numLeads=31,
            hasClim=False,
        ),
        Model(
            modelName='NCEP_ENSAVG', 
            initTimes=initTimes, 
            members=[0], 
            numLeads=31,
            hasClim=False,
        ),
        Model(
            modelName='CWA_GEPSv2', 
            initTimes=initTimes, 
            members=list(range(33)), 
            numLeads=45,
            hasClim=False,
        ),
    ]
    run(models)


if __name__ == '__main__':
    main()
