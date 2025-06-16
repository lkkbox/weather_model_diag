import pytools as pyt
import matplotlib.pyplot as plt


def plot(dims, datas, nrows, ncols, ispls, levels, cmap):
    fig = plt.figure(layout='constrained')
    axs = []

    for iData, data in enumerate(datas):
        iax = iData
        ax = fig.add_subplot(nrows, ncols, ispls[iax]+1)
        axs.append(ax)

        pyt.pt.contourf2(
            ax, dims[-1], dims[0], data, levels, cmap, plotColorbar=(iax==len(datas)-1)
        )
        pyt.pt.wmapaxisx(ax, 60)

    return fig, axs
