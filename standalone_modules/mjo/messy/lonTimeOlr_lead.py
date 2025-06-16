#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import pytools as pyt
from pytools.colormaps.colormaps import nclColormap
import numpy as np
import os
import matplotlib.pyplot as plt


def main():
    initTimes = [pyt.tt.ymd2float(2024, 1, 1) + l for l in range(31)]
    meanLeads = [slice(5*i, 5*(i+1)) for i in range(6)]
    varName = 'olr'
    modelNames = [
        'exp_gepsv3_da-off',
        'exp_gepsv3_da-sst',
        'exp_gepsv3_da-all',
    ]

    #
    # ---- post init
    maxLead = max([s.stop for s in meanLeads])
    obsTimeRange = [min(initTimes), max(initTimes)+maxLead]
    numModels = len(modelNames)
    numInits = len(initTimes)

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
    dataMod = np.nan * np.ones((numModels, numInits, maxLead, dataObs.shape[-1]))
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
    for ifg, meanLead in enumerate(meanLeads):
        fig = plt.figure(figsize=(9, 5), layout='constrained')
        x = dimsObs[-1]
        for iax in range(4):
            ax = fig.add_subplot(1, 4, iax+1)
            if iax == 0:
                y = dimsObs[-2]
                z = dataObs
                ax.set_title('obs')
            else:
                y = [(meanLead.start+meanLead.stop)/2 + i for i in initTimes]
                z = np.nanmean(dataMod[iax-1, :, meanLead, :], axis=-2)
                ax.set_title(modelNames[iax-1][-6:])
            if iax == 1:
                ax.set_xlabel('olr')
            if iax == 2:
                ax.set_xlabel(f'lead={meanLead.start+1}-{meanLead.stop}')
            ax.set_ylim([pyt.tt.ymd2float(2024, 1, 1), pyt.tt.ymd2float(2024, 3, 1)])
            ax.set_yticks(yticks)
            ax.set_yticklabels(yticklabels)
            ax.set_xlim([0, 360])
            pyt.pt.wmapaxisx(ax, 90)
            pyt.pt.contourf2(ax, x, y, z, clevs, cmap, plotColorbar=(iax==3))

        fig.savefig(f'../../figs/exp_gepsv3_da/MJO/{pyt.ft.getModuleName()}_l{ifg}.png')



            

if __name__ == '__main__':
    main()
