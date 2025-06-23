#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
from path import PathGetter
import pytools as pyt
from matplotlib import pyplot as plt
import numpy as np
import os

'''

     lead1 - leadn
var1
var2
var3
 .
 .
 .

'''


import matplotlib
matplotlib.use('Agg') # don't start interactive plots

def main():
    region = [0, 360, -20, 20]
    models = [
        ('CWA_GEPSv3', 'bc', -21),
        ('CWA_GEPSv3', 'raw', -21),
        ('CWA_GEPSv2', 'raw', -33),
        ('NCEP_CTRL', 'raw', 0),
        ('NCEP_ENSAVG', 'raw', 0),
    ]
    variables = [
        *[
            (varName, lev)
            for lev in [100, 200, 300, 500, 700, 850, 925]
            for varName in ['u', 'v', 't']
        ],
        *[
            (varName, lev)
            for lev in [None]
            for varName in ['u10', 'v10', 't2m', 'prec', 'mslp', 'olr']
        ],
    ]
    # -------------------------

    models = [
        ('CWA_GEPSv3', 'bc', 0),
        ('CWA_GEPSv3', 'bc', -21),
        ('CWA_GEPSv3', 'raw', -21),
        ('CWA_GEPSv3', 'raw', 0),
        # ('CWA_GEPSv2', 'raw', -33),
        # ('NCEP_CTRL', 'raw', 0),
        ('NCEP_ENSAVG', 'raw', 0),
    ]
    variables = [
        *[
            (varName, lev)
            for lev in [200, 850]
            for varName in ['u']
        ],
        *[
            (varName, lev)
            for lev in [None]
            for varName in ['u10', 'olr', 'prec']
        ],
    ]

    scores = readScores(models, variables, region, 'acc')
    plot_score_card(models, variables, region, scores, 'acc')



def plot_score_card(models, variables, region, scores, scoreName):
    def plot_total_card(score, model):
        modelName, rawOrBc, member = model
        figName = f'../../../figs/op_2025q1/scores/scoreCardTotal_{modelName}_{rawOrBc}_{member}.png'
        ny, nx = score.shape
        x = list(range(nx))
        y = list(range(ny))
        z = score

        yt=y
        ytl=[]
        for variable in variables:
            varName, level = variable
            if varName in ['u10', 'v10']:
                ytl.append(f'{varName}m')
            elif level is None:
                ytl.append(f'{varName}')
            else:
                ytl.append(f'{varName}{level}')

        ytl = [f'{l:<5s}' for l in ytl]

        fig = plt.figure(layout='constrained')
        ax = fig.add_subplot()
        hsha = ax.pcolormesh(
            x, y, z, shading='nearest',
            cmap=pyt.colormaps.nclColormap('CBR_coldhot', reverse=True, numResampling=10),
            vmin=0, vmax=1,
        )
        ax.invert_yaxis()
        ax.set_yticks(yt)
        ax.set_yticklabels(ytl)

        title = modelName
        if member < 0 and modelName != 'NCEP_ENSAVG':
            title += f'_ENSAVG'
        elif member == 0 and modelName != 'NCEP_CTRL':
            title += f'_CTRL'
        if rawOrBc == 'bc':
            title += f' (BC)'

        fig.suptitle(title)
        cbar = fig.colorbar(hsha)
        cbar.ax.set_title(scoreName.upper())
        fig.savefig(figName)
        print(f'fig saved to {figName}')


    for iModel, model in enumerate(models):
        plot_total_card(scores[iModel], model)



def readScores(models, variables, region, scoreName):
    '''
    scores = scores[model][variable][day]
    '''
    initTime = pyt.tt.ymd2float(2025, 1, 1)
    numInits = 90
    

    def read(modelName, rawOrBc, member, varName, level, scoreName):
        print(f'reading {modelName}, {varName}, {level}, {scoreName}')
        path = pathGetter.get_scores_path(
            modelName, member, initTime, numInits, varName, rawOrBc
        )

        if not os.path.exists(path):
            print(f'path not found: {path}')
            return None

        if level is None:
            minMaxs = [[None]*2, region[2:], region[:2]]
        else:
            minMaxs = [[None]*2, [level]*2, region[2:], region[:2]]

        data, dims = pyt.nct.ncreadByDimRange(
            path, scoreName, minMaxs, decodeTime=False
        )

        if modelName == 'CWA_GEPSv3' and member == -21 and varName == 'u':
            data_3 = data[3, :]
            data_3[(data_3 < 0.15)] = np.nan
            data[3, :] = data_3

            data_4 = data[4, :]
            data_4[(data_4 < 0.15)] = np.nan
            data[4, :] = data_4

        coslat = np.cos(dims[-2] / 180 * np.pi)[:, None]
        data = np.nanmean(data * coslat, axis=(-1, -2)) / np.nanmean(coslat, axis=(-1, -2))
        data= np.squeeze(data)
        # print(dims[-3])
        # print(data)

        return data


    dataDir = '../../../data'
    pathGetter = PathGetter(dataDir)
    initTime = pyt.tt.ymd2float(2025, 1, 1)

    maxLead = 0
    scores = []
    for model in models:
        modelName, rawOrBc, member = model
        score_model = []
        for variable in variables:
            varName, level = variable
            score = read(modelName, rawOrBc, member, varName, level, scoreName)
            if score is not None:
                lead = len(score)
                if lead > maxLead:
                    maxLead = lead
            score_model.append(score)
        scores.append(score_model)

    scoresMatrix = np.nan * np.ones((len(models), len(variables), maxLead))
    for i in range(len(models)):
        for j in range(len(variables)):
            score = scores[i][j]
            if score is not None:
                scoresMatrix[i, j, :len(score)] = score

    return scoresMatrix


if __name__ == '__main__':
    main()
