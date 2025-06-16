#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import pytools as pyt
from pytools.colormaps.colormaps import nclColormap
import numpy as np
import os
import matplotlib.pyplot as plt


def main():
    numInitsPerGroup = 5
    numInitGroups = 6
    minMaxLeads = [1, 30]
    varName = 'olr'
    modelNames = [
        'exp_gepsv3_da-off',
        'exp_gepsv3_da-sst',
        'exp_gepsv3_da-all',
    ]

    #
    # ---- post init
    initTimes = [pyt.tt.ymd2float(2024, 1, 1) + l for l in range(numInitsPerGroup * numInitGroups)]
    obsTimeRange = [min(initTimes), max(initTimes)+minMaxLeads[1]]
    numModels = len(modelNames)
    numInits= len(initTimes)

    #
    # ---- read obs
    paths = [
        pyt.tt.float2format(
            date,
            f'../../data/MJO/mermean_15NS/obs/%Y/%Y%m_olr.nc'
        )
        for date in np.r_[obsTimeRange[0]:obsTimeRange[1]+1]
    ]
    paths = [p for i, p in enumerate(paths) if p not in paths[:i]]
    dataObs, dimsObs = pyt.rt.multiNcRead.read(
        paths, varName, [obsTimeRange, [None]*2], stackedAlong=0
    )
    dataObs = pyt.ct.smooth(dataObs, 5, axis=0)

    #
    # ---- read model
    dataMod = np.nan * np.ones((numModels, numInits, minMaxLeads[1], dataObs.shape[-1]))
    for iModel, modelName in enumerate(modelNames):
        for iInit, initTime in enumerate(initTimes):
            path = pyt.tt.float2format(
                initTime,
                f'../../data/MJO/mermean_15NS/{modelName}/%Y/E000/%y%m%d_olr.nc'
            )
            if not os.path.exists(path):
                continue
            data = pyt.nct.read(path, 'olr')
            dataMod[iModel, iInit, :data.shape[0], :] = data

    #
    # ---- plot
    clevs = pyt.ct.mirror([0, 15, 30, 45])
    cmap = nclColormap('sunshine_diff_12lev')
    yticks = [
        *[pyt.tt.ymd2float(2024, 1, 1) + 5 * i for i in range(6)],
        *[pyt.tt.ymd2float(2024, 2, 1) + 5 * i for i in range(6)],
        pyt.tt.ymd2float(2024, 3, 1),
    ]
    yticklabels = [pyt.tt.float2format(y, '%m%d') for y in yticks]
    x = dimsObs[-1]
    y = list(range(minMaxLeads[0], minMaxLeads[1]+1))
    for iGroup in range(numInitGroups):
        iFig = iGroup
        fig = plt.figure(figsize=(9, 5), layout='constrained')
        for iax in range(4):
            ax = fig.add_subplot(1, 4, iax+1)
            its = int(iGroup*numInitsPerGroup + (numInitsPerGroup-1)/2) + minMaxLeads[0]
            ite = its + minMaxLeads[1] - minMaxLeads[0] + 1
            iInits = int(iGroup * numInitsPerGroup)
            iInite = int((iGroup+1) * numInitsPerGroup)
            if iax == 0:
                z = dataObs[its:ite, :]
                ax.set_title('obs')
            else:
                z = np.nanmean(dataMod[iax-1, iInits:iInite, :, :], axis=-3)
                ax.set_title(modelNames[iax-1][-6:])
            if iax == 1:
                ax.set_xlabel('olr')
            if iax == 2:
                ax.set_xlabel(
                    f'init={"-".join(
                        [pyt.tt.float2format(initTimes[i], "%m-%d") for i in [iInits, iInite-1]]
                    )}'
                )
            ax.set_ylim(minMaxLeads)
            # ax.set_ylim([pyt.tt.ymd2float(2024, 1, 1), pyt.tt.ymd2float(2024, 3, 1)])
            # ax.set_yticks(yticks)
            # ax.set_yticklabels(yticklabels)
            ax.set_xlim([0, 360])
            pyt.pt.wmapaxisx(ax, 90)
            pyt.pt.contourf2(ax, x, y, z, clevs, cmap, plotColorbar=(iax==3))

        fig.savefig(f'../../figs/exp_gepsv3_da/MJO/{pyt.ft.getModuleName()}_i{iFig}.png')
            

if __name__ == '__main__':
    main()
