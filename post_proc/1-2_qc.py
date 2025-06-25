#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
'''
check the quality of processed data
'''
import pytools.timetools as tt
import pytools.modelreader.readTotal as mrt
import numpy as np


def main():
    #
    # ---- settings
    modelName = 'CWA_GEPSv3'
    varName = 'mslp'
    initTimes = [tt.ymd2float(2025, 1, 1) + i for i in range(90)]
    initTimes = [tt.ymd2float(2025, 3, 14) + i for i in range(2)]
    dataType = 'global_daily_1p0'
    minMaxs = [
        [0, 10],
        [-5, 5],
        [120, 160],
    ]
    members = [*list(range(21)), -21]



    #
    # ----
    data, dims = mrt.readTotal(
        modelName,
        dataType,
        varName,
        minMaxs,
        initTimes,
        members,
    )

    means = np.mean(data, axis=tuple([-(i+1) for i in range(len(minMaxs))]))
    nanmeans = np.nanmean(data, axis=tuple([-(i+1) for i in range(len(minMaxs))]))
    nanstds = np.nanstd(data, axis=tuple([-(i+1) for i in range(len(minMaxs))]))

    means_norm = means - np.nanmean(means)
    nanstds_norm = nanstds - np.nanmean(nanstds)
    stdmeans = np.nanstd(means_norm)
    stdstds = np.nanstd(nanstds_norm)
    cri = 1
    suspicous = ((np.isnan(means)) | (means_norm > cri * stdmeans) | (nanstds_norm > cri * stdstds))

    for iInit, init  in enumerate(initTimes):
        for iMem, mem in enumerate(members):
            mn = means[iInit, iMem]
            nmn = nanmeans[iInit, iMem]
            nstd = nanstds[iInit, iMem]
            sus = suspicous[iInit, iMem]

            print(f'{tt.float2format(init, '%y-%m-%d')}, E{mem:03d}, {mn:.1f}, {nmn:.1f}, {nstd:.1f}', end='')
            if sus:
                print(' ***SUSPICIOUS***')
            else:
                print('')

    print(f'nSus = {np.sum(suspicous)}')

if __name__ == '__main__':
    main()
