#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import pytools as pyt
import numpy as np
import os


def main():
    initTime0 = pyt.tt.ymd2float(2024, 1, 1)
    numInits = 31
    minMaxLeads = [1, 30]
    modelName = 'exp_gepsv3_da-all'
    varName = 'olr'
    iMember = 0


def run(initTime0, numInits, minMaxLeads, modelName, varName, iMember):
    leads = list(range(minMaxLeads[0], minMaxLeads[1]+1))
    initTimes = [initTime0 + i for i in range(numInits)]
    numLeads = minMaxLeads[1] - minMaxLeads[0] + 1
    desPath = pyt.tt.float2format(
        initTime0,
        f'../../data/MJO/mermean_15NS/{modelName}/score/E{iMember:03d}/%Y%m%d_n{numInits}_{varName}_l{minMaxLeads[0]}-{minMaxLeads[1]}.nc'
    )

    if os.path.exists(desPath):
        print(f'path already exists: {desPath}')
        return

    desDir = os.path.dirname(desPath)
    if not os.path.exists(desDir):
        os.system(f'mkdir -p {desDir}')


    # ---- read obs
    minObsTime = min(initTimes) + minMaxLeads[0]
    maxObsTime = max(initTimes) + minMaxLeads[1]
    paths = [
        pyt.tt.float2format(
            date,
            f'../../data/MJO/mermean_15NS/obs/%Y/%Y%m_{varName}.nc'
        ) for date in np.r_[minObsTime:maxObsTime+1]
    ]
    paths = [p for i, p in enumerate(paths) if p not in paths[:i]]
    dataObs, dimsObs = pyt.rt.multiNcRead.read(
        paths, varName, [[minObsTime, maxObsTime], [None]*2], stackedAlong=0
    )
    
    # ---- read model
    dataMod = np.nan * np.ones((numInits, numLeads, dataObs.shape[-1]))
    for iInit, initTime in enumerate(initTimes):
        path = pyt.tt.float2format(
            initTime,
            f'../../data/MJO/mermean_15NS/{modelName}/%Y/E{iMember:03d}/%y%m%d_{varName}.nc'
        )
        if not os.path.exists(path):
            continue
        data = pyt.nct.read(path, varName)
        dataMod[iInit, :data.shape[0], :] = data

    # ---- align obs to model 
    dataValid = np.nan * np.ones_like(dataMod)
    for iInit in range(numInits):
        dataValid[iInit, :, :] = dataObs[iInit:iInit+numLeads, :]

    # ---- cal scores
    fo = dataMod * dataValid
    f2 = dataMod ** 2
    o2 = dataValid ** 2
    acc = np.nansum(fo, axis=0, keepdims=True) \
        / np.sqrt(np.nansum(f2, axis=0, keepdims=True)) \
        / np.sqrt(np.nansum(o2, axis=0, keepdims=True)) 

    pcc = np.nansum(fo, axis=-1, keepdims=True) \
        / np.sqrt(np.nansum(f2, axis=-1, keepdims=True)) \
        / np.sqrt(np.nansum(o2, axis=-1, keepdims=True)) 

    errorSquare = (dataValid - dataMod)**2


    acc_mean = np.nanmean(acc, axis=-1).squeeze()
    acc_std = np.nanstd(acc, axis=-1).squeeze()
    pcc_mean = np.nanmean(pcc, axis=0).squeeze()
    pcc_std = np.nanstd(pcc, axis=0).squeeze()
    rmse_mean = np.nanmean(errorSquare, axis=(0, -1)).squeeze()
    rmse_std = np.nanstd(errorSquare, axis=(0, -1)).squeeze()

    for dataName, data in zip([
        'acc_mean', 'acc_std', 'pcc_mean', 'pcc_std', 'rmse_mean', 'rmse_std'
        ], [acc_mean, acc_std, pcc_mean, pcc_std, rmse_mean, rmse_std]
    ):
        pyt.nct.save(
            desPath, {
                dataName:data,
                'lead': leads,
            },
            overwrite=True,
        )
    

if __name__ == '__main__':
    main()
