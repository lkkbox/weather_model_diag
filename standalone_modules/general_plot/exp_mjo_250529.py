#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import pytools as pyt
import matplotlib.pyplot as plt
from dataclasses import dataclass
import numpy as np
import os


@dataclass
class Case():
    long_name: str
    short_name: str


@dataclass
class PlotData():
    data: np.array
    dims: list
    title: str
    isubplot: int
    plotColorbar: bool


def main():
    initTime = pyt.tt.ymd2float(2009, 1, 26)
    cases = [
        Case(long_name='exp_mjo-DEVM21', short_name='CTL'),
        Case(long_name='exp_mjo-DEVM21S9', short_name='S'),
        Case(long_name='exp_mjo-M22G3IKH', short_name='M'),
        Case(long_name='exp_mjo-M22G3IKHS9', short_name='MS'),
    ]
    figDir = '../../../figs/exp_mjo_250529'
    total_or_anomaly = 'anomaly'

    varName, ncVarName, source = 'olr', 'olr', None
    minMaxs = [
        [0, 30+0.99],   # lead days
        [-15, 15], # lat
        [40, 210],  # lon
    ]

    varName, ncVarName, source = 'u850', 'u', 'era5_prs_daymean'
    minMaxs = [
        [0, 30+0.99],   # lead days
        [850_00, 850_00],
        [-15, 15], # lat
        [40, 210],  # lon
    ]

    varName, ncVarName, source = 'u200', 'u', 'era5_prs_daymean'
    minMaxs = [
        [0, 30+0.99],   # lead days
        [200_00, 200_00],
        [-15, 15], # lat
        [40, 210],  # lon
    ]

    varName, ncVarName, source = 'prec', 'prec', None
    minMaxs = [
        [0, 30+0.99],   # lead days
        [-10, 10], # lat
        [40, 210],  # lon
    ]


    if total_or_anomaly == 'total':
        readFuncObs = pyt.rt.obsReader.total
        readFuncMod = pyt.modelreader.readTotal.readTotal
    elif total_or_anomaly == 'anomaly':
        readFuncObs = pyt.rt.obsReader.anomaly
        readFuncMod = pyt.modelreader.readAnomaly.readAnomaly

    figName = f'{figDir}/lon_time_{varName}_{total_or_anomaly}.png'
    if not os.path.exists(os.path.dirname(figName)):
        os.system(f'mkdir -p {os.path.dirname(figName)}')

    # ---- read data
    minMaxsObs = minMaxs.copy()
    minMaxsObs[0] = [initTime + lead for lead in minMaxs[0]]
    if len(minMaxsObs) == 4:
        minMaxsObs[1] = [level / 100 for level in minMaxsObs[1]]
    dataObs, dimsObs = readFuncObs(ncVarName, minMaxsObs, source)
    
    def readModel(caseName):
        dataType = 'global_daily_1p0'
        iMember = 0
        data, dims = readFuncMod(
            caseName, dataType, ncVarName, minMaxs, [initTime], [iMember],
        )
        return data, dims

    for iCase, case in enumerate(cases):
        data, dims = readModel(case.long_name)
        if iCase == 0:
            datas = np.nan * np.ones((len(cases), *data.shape))
        datas[iCase, :] = data
    del(data)

    datas = np.squeeze(datas, axis=(1, 2))

    datas = np.concatenate(
        (
            manipulate_data_dims(dataObs, dimsObs, minMaxs)[None, :, :],
            manipulate_data_dims(datas, dims, minMaxs),
        ), axis=0
    )


    # ---- plot
    nrows, ncols = 2, 3
    ispls = [0, 1, 2, 4, 5]
    if varName == 'olr' and total_or_anomaly == 'anomaly':
        clevs = pyt.ct.mirror([5, 10, 20, 30, 40])
        cmap = pyt.colormaps.nclColormap('sunshine_diff_12lev')
    elif varName == 'olr' and total_or_anomaly == 'total':
        clevs = [170, 190, 210, 220, 230, 240, 250, 270, 290, 310]
        cmap = pyt.colormaps.nclColormap('grads_rainbow')
    elif varName == 'u850' and total_or_anomaly == 'anomaly':
        clevs = pyt.ct.mirror([1, 3, 5, 7, 9, 12])
        cmap = pyt.colormaps.nclColormap('CBR_coldhot')
    elif varName == 'u200' and total_or_anomaly == 'anomaly':
        clevs = pyt.ct.mirror([2, 4, 6, 8, 12, 16, 20])
        cmap = pyt.colormaps.nclColormap('CBR_coldhot')
    elif varName == 'prec' and total_or_anomaly == 'anomaly':
        clevs = pyt.ct.mirror([0.5, 1, 2, 4, 8, 12])
        cmap = pyt.colormaps.nclColormap('CBR_drywet')


    cases = [Case('obs', 'obs'), *cases]
    plotDatas = []
    for iData, (data, case) in enumerate(zip(datas, cases)):
        plotDatas.append(PlotData(data, dims, case.short_name, ispls[iData], iData==len(datas)-1))
    fig, axs = plot(plotDatas, nrows, ncols, clevs, cmap)
    fig.savefig(figName)
    

def manipulate_data_dims(datas, dims, minMaxs):
    if len(dims) == 4:
        datas = np.squeeze(datas, axis=-3)
    LON = np.r_[minMaxs[-1][0]:minMaxs[-1][1]+1]
    datas = np.nanmean(datas, axis=-2)
    datas = pyt.ct.smooth(datas, numSmooths=5, axis=-2)
    datas = pyt.ct.smooth(datas, numSmooths=5, axis=-1)
    datas = pyt.ct.interp_1d(dims[-1], datas, LON, axis=-1, extrapolate=True)
    return datas


def plot(plotDatas, nrows, ncols, clevs, cmap):
    fig = plt.figure(layout='constrained')
    axs = []

    for plotData in plotDatas:
        ax = fig.add_subplot(nrows, ncols, plotData.isubplot+1)
        axs.append(ax)

        ax.set_title(plotData.title)
        pyt.pt.contourf2(
            ax, plotData.dims[-1], plotData.dims[0], plotData.data,
            clevs, cmap, plotColorbar=plotData.plotColorbar
        )
        pyt.pt.wmapaxisx(ax, 60)

    return fig, axs


if __name__ == '__main__':
    main()
