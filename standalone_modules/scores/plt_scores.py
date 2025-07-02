#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
from path import PathGetter
from scoreCard_data import Region, Variable, Model
import pytools as pyt
from matplotlib import pyplot as plt
from dataclasses import dataclass
import numpy as np
import os


import matplotlib
matplotlib.use('Agg') # don't start interactive plots


@dataclass
class LeadTime:
    freq: str
    index: int | float

    def __post_init__(self):
        self.name = f'{self.freq}{self.index}'
        if self.freq == 'd':
            self.dispName = self.name.upper()
        elif self.freq == 'w':
            week = (self.index + 3)/7
            if week % 1 == 0:
                week = int(week)
            self.dispName = f'W{week}'

@dataclass
class Setting:
    dataDir: str
    figDir: str
    initTime0: float | int
    numInitTimes: int
    regions: list[Region]
    variables: list[Variable]
    leadTimes: list[LeadTime]


@dataclass
class ScoreCard:
    regions: list[Region]
    variables: list[Variable]
    leadTimes: list[LeadTime]
    acc: np.ndarray
    rmse: np.ndarray
    acc_std: np.ndarray
    rmse_std: np.ndarray


def main() -> None:
    models = [
        # Model('CWA_GEPSv3', 0, True),
        # Model('CWA_GEPSv3', 0, False),
        Model('CWA_GEPSv3', -21, True),
        Model('CWA_GEPSv3', -21, False),
        Model('CWA_GEPSv2', -33, False),
        # Model('CWA_GEPSv2', 0, False),
        # Model('CWA_TGFS', 0, False),
        # Model('NCEP_CTRL', 0, False),
        Model('NCEP_ENSAVG', 0, False),
    ]
    regions = [
        Region('Glb', [0, 360, -90, 90]),
        Region('Trop', [0, 360, -20, 20]),
        Region('NH', [0, 360, 20, 80]),
        Region('SH', [0, 360, -80, -20]),
    ]
    variables = [
        *[
            Variable(name, level)
            for name in ['u', 'v', 't']
            for level in [100, 200, 500, 700, 850, 925, 1000]
        ],
        *[
            Variable(name, None)
            # for name in ['u10', 'v10', 't2m', 'prec', 'mslp', 'olr']
            for name in ['mslp']
        ],
    ]
    leadTimes = [
        *[
            LeadTime('d', i)
            for i in [1, 3, 5, 7, 10]
        ],
        *[
            LeadTime('w', i)
            for i in [18, 25, 32, 39]
        ],
    ]

    setting = Setting(
        dataDir='../../../data',
        figDir='../../../figs',
        initTime0=pyt.tt.ymd2float(2025, 1, 1), 
        numInitTimes=90,
        regions=regions,
        variables=variables,
        leadTimes=leadTimes,
    )

    # ---- begins - read
    for model in models:
        model.scoreCard = read_score_card(setting, model) 

    # ---- plot total
    for i in range(len(models)):
        for j in range(len(models)):
            if i == j:
                continue
            plot_score_card(models[i], models[j], setting)


def plot_score_card(model1: Model, model2: Model, setting: Setting):
    scoreNames = ['acc', 'rmse']
    numScoreNames = len(scoreNames)
    numVariables = len(setting.variables)
    numRegions = len(setting.regions)
    numLeads = len(setting.leadTimes)

    sc1, sc2 = model1.scoreCard, model2.scoreCard
    deltaAcc = (sc1.acc - sc2.acc) / sc1.acc_std
    deltaRmse = (sc2.rmse - sc1.rmse) / sc1.rmse_std # flip sign
    figDir = f'{setting.figDir}/{pyt.ft.getPyName()}/scores'
    name1 = f'{model1.name}_{model1.member}_{model1.rawOrBc}'
    name2 = f'{model2.name}_{model2.member}_{model2.rawOrBc}'
    figName = f'{figDir}/scoreCard_{name1}-{name2}.png'
    
    if not os.path.exists(figDir):
        os.makedirs(figDir)

    scores = np.concatenate(
        (deltaAcc[None, :, :, :], deltaRmse[None, :, :, :]), axis=0
    )
    scores = np.swapaxes(scores, 1, 2)
    scores = np.reshape(scores, (numScoreNames * numVariables, numRegions * numLeads))

    x = list(range(numRegions * numLeads))
    y = list(range(numVariables * numScoreNames))
    z = scores

    fig, ax = plt.subplots(layout='constrained', figsize=(9, 7))
    ax.invert_yaxis()
    fig.suptitle(f'{name1} vs. {name2}')
    hsha = ax.pcolor(
        x, y, z, vmin=-3, vmax=3,
        cmap=pyt.colormaps.nclColormap('MPL_RdBu', 12, vRange=[0.08, 0.92]),
    )

    ax.set_xlim(ax.get_xlim())
    ax.set_ylim(ax.get_ylim())

    # set yticklabels
    ax.set_yticks(y)
    ax.set_yticklabels(
        [variable.varLev.upper() for variable in setting.variables] * numScoreNames,
        fontsize=8,
    )
    ax.text(-4, numVariables*0.5, 'ACC', rotation=90, fontsize=14, va='center')
    ax.text(-4, numVariables*1.5, 'RMSE', rotation=90, fontsize=14, va='center')

    # set xticklables
    ax.set_xticks(x)
    ax.set_xticklabels(
        [lt.dispName for lt in setting.leadTimes] * numRegions,
        fontsize=8,
        rotation=-90,
    )

    # plot horizontal lines
    numLevels = 7
    numPrsVars = 3
    numSfcVars = numVariables - numLevels * numPrsVars

    for i in range(1, numPrsVars+1):
        yy = i * numLevels - 0.5
        ax.plot(ax.get_xlim(), [yy, yy], color='k', linewidth=0.5)

        yy = i * numLevels + numLevels * numPrsVars + numSfcVars - 0.5
        ax.plot(ax.get_xlim(), [yy, yy], color='k', linewidth=0.5)

    ax.tick_params(axis='x', bottom=False, top=True, labelbottom=False, labeltop=True)

    # plot vertical lines
    for i in range(numRegions - 1):
        xx = (i+1) * numLeads - 0.5
        ax.plot([xx]*2, ax.get_ylim(), color='k', linewidth=1)
        
    for i, region in enumerate(setting.regions):
        ax.text(numLeads * (i+0.5), -4, region.name, fontsize=14, ha='center')


    ax.plot(ax.get_xlim(), [numVariables-0.5]*2, color='k', linewidth=2)

    bar = fig.colorbar(hsha, ax=ax)
    bar.ax.set_title(r'$\sigma$')
    fig.savefig(figName)
    print(f'saved to {figName}')


def read_score_card(setting: Setting, model: Model) -> ScoreCard:
    scoreNames = ['acc', 'rmse', 'acc_std', 'rmse_std']
    pathGetter = PathGetter(setting.dataDir)
    path = pathGetter.get_scoreCard_path(
        model.name, model.member, setting.initTime0, setting.numInitTimes, model.rawOrBc
    )

    # read attributes of regions, variables, and leads
    scoreShape = pyt.nct.getVarShape(path, scoreNames[0])
    numRegions, numVariables, numLeads = scoreShape

    regions = [
        Region(
            pyt.nct.ncreadattt(path, 'iRegion', f'{i}_name'),
            list(pyt.nct.ncreadattt(path, 'iRegion', f'{i}_boundary')),
        )
        for i in range(numRegions)
    ]

    def translateVarName(shortName):
        if shortName[0] in ['u', 'v', 'w', 't', 'q', 'z'] and shortName[-1] != 'm':
            name, lev = shortName[0], int(shortName[1:])
        else:
            name, lev = shortName, None
        return name, lev

    variables = [
        Variable(*translateVarName(pyt.nct.ncreadattt(path, 'iVariable', f'{i}')))
        for i in range(numVariables)
    ]

    def translateLeadTimes(shortName):
        return shortName[0], int(shortName[1:])

    leadTimes = [
        LeadTime(*translateLeadTimes(pyt.nct.ncreadattt(path, 'iLead', f'{i}')))
        for i in range(numLeads)
    ]

    scores = {name: pyt.nct.read(path, name) for name in scoreNames}

    scoreCard =  ScoreCard(
        regions=regions,
        variables=variables,
        leadTimes=leadTimes,
        **scores,
    )

    return select_dimension(scoreCard, setting, scoreNames)


def select_dimension(sc: ScoreCard, setting: Setting, scoreNames: list[str]):
    numRegions = len(setting.regions)
    numVariables = len(setting.variables)
    numLeads = len(setting.leadTimes)

    mapRegion = { # setting: scoreCard
        iRegion: sc.regions.index(region) 
        if region in sc.regions
        else None
        for iRegion, region in enumerate(setting.regions)
    }

    mapVariable = { # setting: scoreCard
        iVariable: sc.variables.index(variable) 
        if variable in sc.variables
        else None
        for iVariable, variable in enumerate(setting.variables)
    }

    mapLeadTime = { # setting: scoreCard
        iLeadTime: sc.leadTimes.index(leadTime) 
        if leadTime in sc.leadTimes
        else None
        for iLeadTime, leadTime in enumerate(setting.leadTimes)
    }

    def map_data(data):
        out = np.nan * np.ones((numRegions, numVariables, numLeads))
        for iRegion in range(numRegions):
            if mapRegion[iRegion] is None:
                continue
            for iVariable in range(numVariables):
                if mapVariable[iVariable] is None:
                    continue
                for iLead in range(numLeads):
                    if mapLeadTime[iLead] is None:
                        continue
                    out[iRegion, iVariable, iLead] = \
                        data[mapRegion[iRegion], mapVariable[iVariable], mapLeadTime[iLead]]
        return out


    return ScoreCard(
        regions=setting.regions,
        variables=setting.variables,
        leadTimes=setting.leadTimes,
        **{scoreName: map_data(getattr(sc, scoreName)) for scoreName in scoreNames}
    )


if __name__ == '__main__':
    main()
