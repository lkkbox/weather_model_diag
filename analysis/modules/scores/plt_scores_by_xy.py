from .path import PathGetter
import os
from pytools import nctools as nct
from pytools import caltools as ct
import numpy as np

def run(cases, dataDir, figDir, option):
    for variable in option.variables:

        if variable.ndim == 4:
            levels = option.levels
        else:
            levels = [None]

        for region in option.plot.regions:
            for level in levels:
                _run_region(cases, dataDir, figDir, option, variable, level, region)


def _run_region(cases, dataDir, figDir, option, variable, level, region):
    pathGetter = PathGetter(dataDir)

    # read score data -> [icase][imember][raw/bc]
    print('reading..', flush=True)
    scores = [None] * len(cases)
    for iCase, case in enumerate(cases):
        model = case.model
        scores[iCase] = list([None] * len(case.model.members))

        for iMember, member in enumerate(case.model.members):
            scores[iCase][iMember] = [None] * 2

            for iBc, rawOrBc in enumerate(['raw', 'bc']):
                # should we read?
                if not model.hasClim and rawOrBc == 'bc':
                    continue

                path = pathGetter.get_scores_path(
                    model.name, member, model.initTime0, model.numInitTimes,
                    variable.name, rawOrBc
                )
                
                if not os.path.exists(path):
                    print(f'[warning] path not found: {path}')
                    continue

                # yes, we should.
                scoreNames = ['bias', 'rmse', 'acc']
                scores[iCase][iMember][iBc] = [None] * len(scoreNames)
                if variable.ndim == 3:
                    minMaxs = [[None]*2, region.boundary[-2:], region.boundary[:2]]
                elif variable.ndim == 4:
                    minMaxs = [[None]*2, [level, level], region.boundary[-2:], region.boundary[:2]]
                else:
                    raise ValueError(f'cannot handle ndim={variable.ndim} (name={variable.name})')
                
                for iScore, scoreName in enumerate(scoreNames):
                    data, dims = nct.ncreadByDimRange(
                        path, scoreName, minMaxs, decodeTime=False
                    )
                    if data is None:
                        print('[Error] unable to read {path}, {scoreName}')
                        continue

                    area = ct.lonlat2area(dims[-1], dims[-2])
                    s_mean = np.nanmean(data * area, axis=(-1, -2)) / np.nanmean(area, axis=(-1, -2))
                    s_std = np.nanstd(data * area, axis=(-1, -2)) / np.nanmean(area, axis=(-1, -2))
                    scores[iCase][iMember][iBc][iScore] = data
                    print(data.shape)

