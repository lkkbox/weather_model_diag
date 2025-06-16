from .rmm.rmm_cal_indices_mod import run as indices_mod
from .rmm.rmm_cal_indices_obs import run as indices_obs
from .rmm.rmm_prep_mermean_obs import run as mermean_obs
from .rmm.rmm_prep_mermean_mod import run as mermean_mod
from .rmm.rmm_prep_mermean_mod_nobc import run as mermean_mod_nobc
from dataclasses import dataclass

@dataclass
class Model():
    modelName: str
    initTimes: list
    members: int
    numLeads: int
    hasClim: bool
    climYears: list = (2006, 2020)


def run(models):
    # prepare data
    # ---- constants
    numPrevDays = 120 # we need previous 120 days of observation for rmm
    minInitTimes = min([min(model.initTimes) for model in models])
    maxInitTimes = max([max(model.initTimes) for model in models])
    maxNumLeads = max([model.numLeads for model in models])

    # ---- auto
    obsDateStart = minInitTimes
    obsDateEnd = maxInitTimes + maxNumLeads

    # ---- runs
    mermean_obs(obsDateStart - numPrevDays, obsDateEnd)
    indices_obs(obsDateStart, obsDateEnd)

    for model in models:
        # ---- inputs
        modelName = model.modelName
        initTimes = model.initTimes
        members = model.members

        mermean_mod_nobc(modelName, initTimes, members)
        indices_mod(modelName, initTimes, members, clim_bc=False)
        if model.hasClim:
            mermean_mod(modelName, initTimes, members, model.climYears)
            indices_mod(modelName, initTimes, members, clim_bc=True)

