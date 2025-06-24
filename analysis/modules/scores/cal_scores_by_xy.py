from driver import safe_runner
import pytools as pyt
from reader import Reader
import numpy as np
import os
from . import path
import copy

'''
todo: prec is limited to tropical bands for CMORPH but the values are extrapolated outside
'''


def run(cases, dataDir, option):
    # check out if the models have the same intitTimes
    for case in cases[1:]:
        if case.model.initTime0 != cases[0].model.initTime0:
            print(f'[fatal] the models with different "initTime0" is not allowed:')
            print(f'{case.name}, {cases[0].name}')
            return

        if case.model.numInitTimes != cases[0].model.numInitTimes:
            print(f'[fatal] the models with different "initTime0" is not allowed:')
            print(f'{case.name}, {cases[0].name}')
            return

    # create output directories
    for case in cases:
        for member in case.model.members:
            if option.do_data_1day:
                _create_output_dir(dataDir, case.model, member, '1day')
            if option.do_data_7dma:
                _create_output_dir(dataDir, case.model, member, '7dma')

    # run by variables
    for variable in option.variables:
        _run_variable(cases, dataDir, variable, option)


@safe_runner
def _run_variable(cases, dataDir, variable, option):
    print(f'         variable = {variable.name}')
    ndmas = []
    if option.do_data_1day:
        ndmas.append('1day')
    if option.do_data_7dma:
        ndmas.append('7dma')

    # check if we can skip this variable
    if option.force:
        canSkip = False
    else:
        canSkip = True
        for case in cases:
            for member in case.model.members:
                skipRaw, skipBC = _get_skips(dataDir, case.model, member, variable, ndmas)
                if not skipRaw or not skipBC:
                    canSkip = False
                    break
            if not canSkip:
                break


    if canSkip:
        print('all output paths are found')
        return

    reader = Reader(
        dataDir, 
        regrid_delta_x=option.regrid_delta_x,
        regrid_delta_y=option.regrid_delta_y, 
    )
    
    # read obs total, clim, and anomaly
    initTimes = [
        min([min(case.model.initTimes) for case in cases]),
        max([max(case.model.initTimes) for case in cases]),
    ]
    numLeads = max([case.model.numLeads for case in cases])
    obsTimeRange = reader.get_valid_time_range(initTimes, numLeads)

    OBSTOTAL = reader.read_obs_total(variable, obsTimeRange)
    OBSCLIM = reader.read_obs_clim(variable, obsTimeRange)
    OBSTOTAL, OBSCLIM = reader.conform_axis(OBSTOTAL, OBSCLIM, axis=-3)
    OBSANOM = OBSTOTAL - OBSCLIM

    @safe_runner
    def run_member(model, member, MODCLIM, OBSCLIM):
        print(f'        {variable.name}, {model.name}, {member=}')
        # skip if the file already exists
        if not option.force:
            skipRaw, skipBC = _get_skips(dataDir, model, member, variable, ndmas)
        else:
            skipRaw = False
            skipBC = not model.hasClim

        if skipRaw and skipBC and not option.force:
            print('all output files already exists')
            return

        # read model total
        MODTOTAL = reader.read_mod_total(case.model, member, variable, case.model.numLeads)
        if MODTOTAL is None:
            print('[fatal] no model total data is read')
            return

        for ndma in ndmas:
            obsAnom = copy.deepcopy(OBSANOM)
            obsClim = copy.deepcopy(OBSCLIM)
            modClim = copy.deepcopy(MODCLIM)
            modTotal = copy.deepcopy(MODTOTAL)

            # rearrange obs data to valid (time) -> (initTime, lead)
            validAnom, modTotal = reader.obs_to_valid(obsAnom, modTotal, model.initTimes)
            validClim, modTotal = reader.obs_to_valid(obsClim, modTotal, model.initTimes)

            if ndma == '7dma':
                validAnom.vals = pyt.ct.smooth(validAnom.vals, 7, 1)
                validClim.vals = pyt.ct.smooth(validClim.vals, 7, 1)
                modTotal.vals = pyt.ct.smooth(modTotal.vals, 7, 1)
                if not skipBC and modClim is not None:
                    modClim.vals = pyt.ct.smooth(modClim.vals, 7, 1)
            elif ndma != '1day':
                raise ValueError(f'what is {ndma=}????')

            if not skipRaw:
                modAnom = modTotal - validClim
                scoresRaw = _cal_scores(validAnom.vals, modAnom.vals)
                _save_output(dataDir, model, member, variable, modAnom.dims, scoresRaw, "raw", ndma)

            if not skipBC and modClim is not None:
                modAnom = modTotal - modClim
                scoresBC = _cal_scores(validAnom.vals, modAnom.vals)
                _save_output(dataDir, model, member, variable, modAnom.dims, scoresBC, "BC", ndma)


    # loop over case and members
    for case in cases:
        # read model clim
        if case.model.hasClim:
            MODCLIM = reader.read_mod_clim(
                case.model, 0, variable, case.model.numLeads, case.model.climYears
            )
            if MODCLIM is None:
                print('[fatal] no model clim data is read')
                return

            # make sure the level are consistent to the observation's
            if variable.ndim == 4:
                MODCLIM, obsClim = reader.conform_axis(MODCLIM, OBSCLIM, axis=-3)
            else:
                obsClim = copy.copy(OBSCLIM)
            MODCLIM.vals = pyt.ct.smooth(MODCLIM.vals, 7, 1)
        else:
            MODCLIM = None
            obsClim = copy.copy(OBSCLIM)

        for member in case.model.members:
            run_member(case.model, member, MODCLIM, obsClim)


def _get_skips(dataDir, model, member, variable, ndmas):
    skipRaw = True
    for ndma in ndmas:
        path = _get_output_path(dataDir, model, member, variable, "raw", ndma)
        if not os.path.exists(path):
            skipRaw = False

    if not model.hasClim:
        skipBC = True
    else:
        skipBC = True
        for ndma in ndmas:
            path = _get_output_path(dataDir, model, member, variable, "BC", ndma)
            if not os.path.exists(path):
                skipBC = False

    return skipRaw, skipBC


def _cal_scores(o, f):
    bias = np.nanmean(o - f, axis=0)
    rmse = np.sqrt(np.nanmean((o - f) ** 2, axis=0))
    acc = np.nansum(f * o, axis=0) \
        / np.sqrt(np.nansum(f ** 2, axis=0)) \
        / np.sqrt(np.nansum(o ** 2, axis=0))

    return {
        'bias': bias,
        'rmse': rmse,
        'acc': acc,
    }

    

def _create_output_dir(dataDir, model, member, ndma):
    scoresDir = f'{dataDir}/scores'

    if not os.path.exists(scoresDir):
        os.system(f'mkdir -p {scoresDir}')

    if not os.access(scoresDir, os.W_OK):
        raise PermissionError(f'permission denied to write to {dataDir}')

    outputDir = _get_output_dir(dataDir, model, member, ndma)
    if not os.path.exists(outputDir):
        os.system(f'mkdir -p {outputDir}')
    
    return


def _get_output_dir(dataDir, model, member, ndma):
    scoresDir = f'{dataDir}/scores'

    if not os.path.exists(scoresDir):
        os.system(f'mkdir -p {scoresDir}')

    if not os.access(scoresDir, os.W_OK):
        raise PermissionError(f'permission denied to write to {dataDir}')

    return pyt.tt.float2format(
        model.initTime0,
        f'{scoresDir}/{model.name}/E{member:03d}/%y%m%d/{model.numInitTimes:04d}/{ndma}'
    )

def _get_output_path(dataDir, model, member, variable, rawOrBC, ndma):
    if rawOrBC == 'raw':
        suffix = 'raw'
    elif rawOrBC == 'BC':
        suffix = 'bc'
    else:
        ValueError(f'unrecognized option {rawOrBC=}')
    outDir = _get_output_dir(dataDir, model, member, ndma)
    outPath = f'{outDir}/{variable.name}_{suffix}.nc'
    return outPath


def _save_output(dataDir, model, member, variable, dims, scores, rawOrBC, ndma):
    outPath = _get_output_path(dataDir, model, member, variable, rawOrBC, ndma)

    if variable.ndim == 4:
        dimStruct = {
            'lead': dims[-4],
            'lev': dims[-3],
            'lat': dims[-2],
            'lon': dims[-1],
        } 
    else:
        dimStruct = {
            'lead': dims[-3],
            'lat': dims[-2],
            'lon': dims[-1],
        } 


    for scoreName, score in list(scores.items()):
        pyt.nct.save(
            outPath, {
                scoreName: score,
                **dimStruct
            },
            overwrite=True
        )

    print(f'saved to {outPath}')

