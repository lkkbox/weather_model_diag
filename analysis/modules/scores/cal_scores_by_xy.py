from driver import safe_runner
import pytools as pyt
from reader import Reader
import numpy as np
import os

'''
todo: prec is limited to tropical bands for CMORPH but the values are extrapolated outside
'''


def run(cases, dataDir, option):
    # check out if the models have the same intitTimes
    for case in cases[1:]:
        if case.model.initTime0 != cases[0].model.initTime0:
            print(f'[fatal] the models with different "initTim0" is not allowed:')
            print(f'{case.name}, {cases[0].name}')
            return

        if case.model.numInitTimes != cases[0].model.numInitTimes:
            print(f'[fatal] the models with different "initTim0" is not allowed:')
            print(f'{case.name}, {cases[0].name}')
            return

    # create output directories
    for case in cases:
        for member in case.model.members:
            _create_output_dir(dataDir, case.model, member)


    # run by variables
    for variable in option.variables:
        _run_variable(cases, dataDir, variable, option)


@safe_runner
def _run_variable(cases, dataDir, variable, option):
    print(f'         variable = {variable.name}')

    # check if we can skip this variable
    canSkip = True
    for case in cases:
        for member in case.model.members:
            skipRaw, skipBC = _get_skips(dataDir, case.model, member, variable)
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

    obsTotal = reader.read_obs_total(variable, obsTimeRange)
    obsClim = reader.read_obs_clim(variable, obsTimeRange)
    obsAnom = obsTotal - obsClim

    @safe_runner
    def run_member(model, member, modClim):
        print(f'        {variable.name}, {model.name}, {member}')
        # skip if the file already exists
        skipRaw, skipBC = _get_skips(dataDir, model, member, variable)
        if skipRaw and skipBC:
            print('all output files already exists')
            return

        # rearrange obs data to valid (time) -> (initTime, lead)
        validAnom = reader.obs_to_valid(obsAnom, model)
        validClim = reader.obs_to_valid(obsClim, model)

        # read model total
        modTotal = reader.read_mod_total(case.model, member, variable, case.model.numLeads)
        if modTotal is None:
            print('[fatal] no model total data is read')
            return

        if not skipRaw:
            scoresRaw = _cal_scores(validAnom.vals, (modTotal - validClim).vals)
            _save_output(dataDir, model, member, variable, modTotal.dims, scoresRaw, "raw")

        if not skipBC and modClim is not None:
            scoresBC = _cal_scores(validAnom.vals, (modTotal - modClim).vals)
            _save_output(dataDir, model, member, variable, modTotal.dims, scoresBC, "BC")


    # loop over case and members
    for case in cases:
        # read model clim
        if case.model.hasClim:
            modClim = reader.read_mod_clim(
                case.model, 0, variable, case.model.numLeads, case.model.climYears
            )
            if modClim is None:
                print('[fatal] no model clim data is read')
                return
        else:
            modClim = None

        for member in case.model.members:
            run_member(case.model, member, modClim)


def _get_skips(dataDir, model, member, variable):
    outPathRaw = _get_output_path(dataDir, model, member, variable, "raw")
    outPathBC = _get_output_path(dataDir, model, member, variable, "BC")
    skipRaw = os.path.exists(outPathRaw)
    skipBC = os.path.exists(outPathBC) or (not model.hasClim)
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

    

def _create_output_dir(dataDir, model, member):
    scoresDir = f'{dataDir}/scores'

    if not os.path.exists(scoresDir):
        os.system(f'mkdir -p {scoresDir}')

    if not os.access(scoresDir, os.W_OK):
        raise PermissionError(f'permission denied to write to {dataDir}')

    outputDir = _get_output_dir(dataDir, model, member)
    if not os.path.exists(outputDir):
        os.system(f'mkdir -p {outputDir}')
    
    return


def _get_output_dir(dataDir, model, member):
    scoresDir = f'{dataDir}/scores'

    if not os.path.exists(scoresDir):
        os.system(f'mkdir -p {scoresDir}')

    if not os.access(scoresDir, os.W_OK):
        raise PermissionError(f'permission denied to write to {dataDir}')

    return pyt.tt.float2format(
        model.initTime0,
        f'{scoresDir}/{model.name}/E{member:03d}/%y%m%d/{model.numInitTimes:04d}'
    )

def _get_output_path(dataDir, model, member, variable, rawOrBC):
    if rawOrBC == 'raw':
        suffix = 'raw'
    elif rawOrBC == 'BC':
        suffix = 'bc'
    else:
        ValueError(f'unrecognized option {rawOrBC=}')
    outDir = _get_output_dir(dataDir, model, member)
    outPath = f'{outDir}/{variable.name}_{suffix}.nc'
    return outPath


def _save_output(dataDir, model, member, variable, dims, scores, rawOrBC):
    outPath = _get_output_path(dataDir, model, member, variable, rawOrBC)

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

