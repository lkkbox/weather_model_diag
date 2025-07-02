#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
from path import PathGetter
import pytools as pyt
import numpy as np
from dataclasses import dataclass
import os


@dataclass
class Model():
    name: str
    member: int
    bc: bool

    def __post_init__(self):
        if self.bc:
            self.rawOrBc = 'bc'
        else:
            self.rawOrBc = 'raw'


@dataclass
class Region():
    name: str
    boundary: list[int]

    def __post_init__(self) -> None:
        self.lonw, self.lone, self.lats, self.latn = self.boundary


@dataclass
class Variable():
    name: str
    level: int | None

    def __post_init__(self):
        if self.level:
            self.varLev = f'{self.name}{self.level}'
        elif self.name in ['u10', 'v10']:
            self.varLev = f'{self.name}m'
        else:
            self.varLev = f'{self.name}'


@dataclass
class Settings():
    overwrite: bool
    initTime0: float
    numInitTimes: int
    regions: list[Region]
    variables: list[Variable]
    ind_1day: list[int]
    ind_7dma: list[int]
    scoreNames: list[int]

    def __post_init__(self):
        self.numScoreNames = len(self.scoreNames)
        self.numVariables = len(self.variables)
        self.numRegions = len(self.regions)
        self.numLeads = len(self.ind_1day) + len(self.ind_7dma)
        self.timeName = [
            *[f'd{i}' for i in self.ind_1day],
            *[f'w{i}' for i in self.ind_7dma],
        ]


def main() -> None:
    settings = Settings(
        overwrite=True,
        initTime0=pyt.tt.ymd2float(2025, 1, 1),
        numInitTimes=90,
        regions = [
            Region('Glb', [0, 360, -90, 90]),
            Region('Trop', [0, 360, -20, 20]),
            Region('NH', [0, 360, 20, 80]),
            Region('SH', [0, 360, -80, -20]),
        ],
        variables=[
            *[
                Variable(name, level)
                for name in ['u', 'v', 't', 'z']
                for level in [100, 200, 500, 700, 850, 925, 1000]
            ],
            Variable('u10', None),
            Variable('v10', None),
            Variable('t2m', None),
            Variable('olr', None),
            Variable('mslp', None),
        ],
        ind_1day=[1, 3, 5, 7, 10],
        ind_7dma=[4 + w * 7 for w in [2, 3, 4, 5]],
        scoreNames=['acc', 'rmse', 'bias'],
    )

    models = [
        Model('CWA_GEPSv3', -21, True),
        Model('CWA_GEPSv3', -21, False),
        Model('CWA_GEPSv3', 0, True),
        Model('CWA_GEPSv3', 0, False),
        Model('CWA_GEPSv2', -33, False),
        Model('CWA_GEPSv2', 0, False),
        Model('CWA_TGFS', 0, False),
        Model('NCEP_CTRL', 0, False),
        Model('NCEP_ENSAVG', 0, False),
    ]



    for model in models:
        print(f'{model.name}, E{model.member:03d}, {model.rawOrBc}:', end='', flush=True)
        run(settings, model)


def run(settings: Settings, model: Model) -> None:
    pathGetter = PathGetter('../../../data')
    outPath = pathGetter.get_scoreCard_path(
        model.name, model.member, settings.initTime0, settings.numInitTimes, model.rawOrBc
    )

    if os.path.exists(outPath) and not settings.overwrite:
        print(f'file already exists but overwrite is False: {outPath}')
        return

    ndmas = ['1day', '7dma']
    indices_map = {
        '1day': settings.ind_1day,
        '7dma': settings.ind_7dma,
    }
    ileadse_map = {
        '1day': (0, len(settings.ind_1day)),
        '7dma': (len(settings.ind_1day), settings.numLeads),
    }

    lonw = min([r.lonw for r in settings.regions])
    lone = max([r.lone for r in settings.regions])
    lats = min([r.lats for r in settings.regions])
    latn = max([r.latn for r in settings.regions])
    areaRead = [[lats, latn], [lonw, lone]]

    scores = np.nan * np.ones(
        (settings.numScoreNames, settings.numRegions, settings.numVariables, settings.numLeads)
    )
    stds = np.nan * np.ones(
        (settings.numScoreNames, settings.numRegions, settings.numVariables, settings.numLeads)
    )

    # ---- read data by variables
    for iVariable, variable in enumerate(settings.variables):
        print(f'{variable.varLev}..', end='', flush=True)

        if variable.level:
            minMaxs = [[None]*2, [variable.level]*2, *areaRead]
        else:
            minMaxs = [[None]*2, *areaRead]

        for ndma in ndmas:
            ileads, ileade = ileadse_map[ndma]
            indices = indices_map[ndma]

            path = pathGetter.get_scores_path(
                initTime=settings.initTime0,
                numInits=settings.numInitTimes,
                modName=model.name,
                member=model.member,
                rawOrBc=model.rawOrBc,
                varName=variable.name,
                ndma=ndma,
            )

            if not os.path.exists(path):
                print(f'file not found: {path}')
                continue

            for iScore, scoreName in enumerate(settings.scoreNames):
                data, dims = pyt.nct.ncreadByDimRange(
                    path, scoreName, minMaxs, decodeTime=False
                )

                if data is None:
                    continue

                if iScore == 0:
                    std_data, std_dims = read_clim_std(settings, variable, areaRead)
                    std_data = pyt.ct.interp_1d(
                        std_dims[-1], std_data, dims[-1], axis=-1, extrapolate=True,
                    )
                    std_data = pyt.ct.interp_1d(
                        std_dims[-2], std_data, dims[-2], axis=-2, extrapolate=True,
                    )

                if scoreName in ['bias', 'rmse']:
                    data /= std_data

                if variable.level:
                    data = np.squeeze(data, axis=1)
                    dims = [dims[i] for i in [0, 2, 3]]

                for iRegion, region in enumerate(settings.regions):
                    lonSlice = pyt.ct.value2Slice(dims[-1], region.lonw, region.lone)
                    latSlice = pyt.ct.value2Slice(dims[-2], region.lats, region.latn)
                    coslat = np.cos(dims[-2][latSlice] / 180 * np.pi)[:, None]
                    score_all = np.nanmean(data[:, latSlice, lonSlice] * coslat, axis=(-1, -2)) \
                        / np.nanmean(coslat, axis=(-1, -2))

                    std_all = (data[:, latSlice, lonSlice] - score_all[:, None, None]) ** 2
                    std_all = np.nanmean(std_all * coslat, axis=(-1, -2)) \
                        / np.nanmean(coslat, axis=(-1, -2))
                    std_all = np.sqrt(std_all)

                    score, std = [], []
                    for index in indices:
                        if index > len(score_all):
                            score.append(np.nan)
                            std.append(np.nan)
                        else:
                            score.append(score_all[index])
                            std.append(std_all[index])

                    scores[iScore, iRegion, iVariable, ileads:ileade] = score
                    stds[iScore, iRegion, iVariable, ileads:ileade] = std


    print(f'saving to {outPath}..')
    if os.path.exists(outPath):
        os.system(f'mv {outPath} {outPath}.bkp')
    # ---- save the dimensions
    pyt.nct.save(
        outPath, {
            'iRegion': list(range(settings.numRegions)),
        },
        overwrite=True
    )

    pyt.nct.save(
        outPath, {
            'iVariable': list(range(settings.numVariables)),
        },
        overwrite=True
    )

    pyt.nct.save(
        outPath, {
            'iLead': list(range(settings.numLeads)),
        },
        overwrite=True
    )

    for iRegion, region in enumerate(settings.regions):
        pyt.nct.ncwriteatt(outPath, 'iRegion', f'{iRegion}_name', region.name)
        pyt.nct.ncwriteatt(outPath, 'iRegion', f'{iRegion}_boundary', region.boundary)

    for iVariable, variable in enumerate(settings.variables):
        pyt.nct.ncwriteatt(outPath, 'iVariable', f'{iVariable}', variable.varLev)

    for iLead, timeName in enumerate(settings.timeName):
        pyt.nct.ncwriteatt(outPath, 'iLead', f'{iLead}', timeName)

    # ---- save the variable
    for iScore, scoreName in enumerate(settings.scoreNames):
        stdName = f'{scoreName}_std'
        pyt.nct.save(
            outPath, {
                scoreName: scores[iScore, :],
                'iRegion': list(range(settings.numRegions)),
                'iVariable': list(range(settings.numVariables)),
                'iLead': list(range(settings.numLeads)),
            },
            overwrite=True
        )
        pyt.nct.save(
            outPath, {
                stdName: stds[iScore, :],
                'iRegion': list(range(settings.numRegions)),
                'iVariable': list(range(settings.numVariables)),
                'iLead': list(range(settings.numLeads)),
            },
            overwrite=True
        )
                    

def read_clim_std(settings: Settings, variable: Variable, areaRead):
    # set path
    root = '/nwpr/gfs/com120/9_data'
    if variable.name in ['u', 'v', 't', 'z']:
        path = f'{root}/ERA5/clim_1day/ERA5_{variable.name}_stdClim_2001_2020_r720x360_1day.nc'
    elif variable.name in ['u10', 'v10', 't2m', 'mslp']:
        path = f'{root}/ERA5/clim_1day/ERA5_sfc_stdClim_2001_2020_1day.nc'
    elif variable.name == 'olr':
        path = f'{root}/NOAA_OLR/olr_stdClim_2001_2020_1p0_1day.nc'
    elif variable.name == 'prec':
        path = f'{root}/CMORPH/clim/CMORPH_stdClim_2011_2020_0p5_1day.nc'
    else:
        raise NotImplementedError(f'varName = {variable.name}')

    # set read variable name
    ncVarName = variable.name
    if variable.name == 'mslp':
        ncVarName = 'msl'
    elif variable.name == 'prec':
        ncVarName = 'cmorph'

    # set units
    scale = 1
    if variable.name == 'mslp':
        scale = 1/100
    elif variable.name == 'z':
        scale = 1/9.80665

    timeRead = [
        pyt.tt.dayOfYear229(t) - 1 for t in [
            settings.initTime0, 
            settings.initTime0 + settings.numInitTimes - 1,
        ]
    ]

    if variable.level:
        minMaxs = [timeRead, [variable.level]*2, *areaRead]
    else:
        minMaxs = [timeRead, *areaRead]

    data, dims = pyt.nct.ncreadByDimRange(path, ncVarName, minMaxs)
    data = data * scale

    if variable.level:
        data = np.squeeze(data, axis=1)
        dims = [dims[i] for i in [0, 2, 3]]

    data = np.nanmean(data, axis=0)
    dims = [dims[i] for i in [-2, -1]]


    return data, dims



if __name__ == '__main__':
    main()
