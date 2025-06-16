#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import pytools as pyt
from rmm_runner import Model, run

def main():
    initTimes = [pyt.tt.ymd2float(2009, 1, 26)]
    models = [
        Model(
            modelName=modelName, 
            initTimes=initTimes, 
            members=[0], 
            numLeads=44,
            hasClim=True,
            climYears=[2001, 2020],
        )
        for modelName in [
            'exp_mjo-DEVM21',
            'exp_mjo-DEVM21S9',
            'exp_mjo-M22G3IKH',
            'exp_mjo-M22G3IKHS9',
        ]
    ]
    run(models)


if __name__ == '__main__':
    main()
