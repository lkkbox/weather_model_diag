#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import pytools as pyt
import plotter
import numpy as np


def main():
    data, dims = pyt.rt.obsReader.anomaly(
        'olr', [
            [pyt.tt.ymd2float(2001, 1, 25), pyt.tt.ymd2float(2001, 2, 23)],
            [-30, 30],
            [60, 210]
        ]
    )
    time, lat, lon = dims

    nt, ny, nx = data.shape
    numFigs = 1
    numMeanDays = 5
    numSubplots = nt // numMeanDays

    shadingData = np.nan * np.ones((1, numSubplots, ny, nx))
    for iPanel in range(numSubplots):
        ts = iPanel * numMeanDays
        te = (iPanel + 1) * numMeanDays
        shadingData[0, iPanel, :] = np.mean(data[0, ts:te, :], axis=0)

    shading = plotter.Contourfill(
        shadingData, [lon, lat]
    )

if __name__ == '__main__':
    main()

