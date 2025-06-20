from driver import greeter
from .rmm.rmm_cal_indices_mod import run as indices_mod
from .rmm.rmm_cal_indices_obs import run as indices_obs
from .rmm.rmm_prep_mermean_obs import run as mermean_obs
from .rmm.rmm_prep_mermean_mod import run as mermean_mod
from .rmm.rmm_prep_mermean_mod_nobc import run as mermean_mod_nobc
from .rmm.rmm_plot import Rmm_plotter
import pytools as pyt
from dataclasses import dataclass, field


def run(cases, dataDir, figDir, option):
    if option.do_data:
        _run_data(cases, dataDir)

    if option.do_plot:
        _run_plot(cases, dataDir, figDir, option)


@greeter
def _run_data(cases, dataDir):
    # takle with inputs
    models = [case.model for case in cases]
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
    mermean_obs(obsDateStart - numPrevDays, obsDateEnd, dataDir)
    indices_obs(obsDateStart, obsDateEnd, dataDir)

    for model in models:
        # ---- inputs
        initTimes = model.initTimes
        members = model.members

        mermean_mod_nobc(model.name, initTimes, members, dataDir)
        indices_mod(model.name, initTimes, members, dataDir, clim_bc=False)
        if model.hasClim:
            mermean_mod(model.name, initTimes, members, dataDir, model.climYears)
            indices_mod(model.name, initTimes, members, dataDir, clim_bc=True)

@greeter
def _run_plot(cases, dataDir, figDir, option):
    stat = True
    for case in cases[1:]:
        if case.model.initTime0 != cases[0].model.initTime0:
            stat = False
        if case.model.numInitTimes != cases[0].model.numInitTimes:
            stat = False
    if not stat:
        raise RuntimeError(f'mjo plot does not allow different initTimes between models ({cases[0].name}:{cases[0].model.name}, {case.name}:{case.model.name})')


    plotter = Rmm_plotter(
        dataRoot=f'{dataDir}/MJO/RMM',
        figDir=f'{figDir}/MJO',
        cases=cases,
        option=option,
    )
    plotter.run()


@dataclass
class Option_Phase_Diagram():
    lead_means: list = None
    init_means: list = None
    colors: list = None

    def __post_init__(self):
        # set defaults
        if self.lead_means is None:
            self.lead_means = [slice(i * 5, (i+1) * 5) for i in range(6)]
        if self.init_means is None:
            self.init_means = [slice(i * 5, (i+1) * 5) for i in range(6)]
        if self.colors is None:
            self.colors = [
                'tab:blue', 'tab:orange', 'tab:green', 'tab:red', 
                'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray',
                'tab:olive', 'tab:cyan'
            ]


        # check types
        pyt.chkt.checkType(self.lead_means, list, 'lead_means')
        pyt.chkt.checkType(self.init_means, list, 'init_means')
        pyt.chkt.checkType(self.colors, list , 'colors')
        for lead_mean in self.lead_means:
            pyt.chkt.checkType(lead_mean, slice, 'lead_mean')
        for init_mean in self.init_means:
            pyt.chkt.checkType(init_mean, slice, 'init_mean')

        self.colors = CircularYielder(self.colors)
            

@dataclass
class Option_Score_Diagram():
    xlim: list = None
    ylim_rmse: list = None
    ylim_acc: list = None
    xticks: list = None
    yticks: list = None
    do_rmse: bool = True
    do_acc: bool = True
    mpl_line_opts: list = None
    legend_opts: dict = None
    add_ensmean: bool = True

    def __post_init__(self):
        if self.mpl_line_opts is None:
            self.mpl_line_opts = [
                {'color': f'tab:{color}','linestyle': linestyle}
                for linestyle in ['-', '--', '-.', ':']
                for color in [
                    'blue', 'orange', 'green', 'red', 
                    # 'purple', 'brown', 'pink', 'gray', 
                    # 'olive', 'cyan', 
                ]
            ]
        if self.legend_opts is None:
            self.legend_opts = {'loc': 'outside right upper'}

        pyt.chkt.checkType(self.legend_opts, dict , 'legend_opts')
        pyt.chkt.checkType(self.mpl_line_opts, list , 'mpl_line_opts')
        pyt.chkt.checkType(self.xlim, [list, None], 'xlim')
        pyt.chkt.checkType(self.ylim_rmse, [list, None], 'ylim_rmse')
        pyt.chkt.checkType(self.ylim_acc, [list, None], 'ylim_acc')
        pyt.chkt.checkType(self.xticks, [list, None], 'xticks')
        pyt.chkt.checkType(self.yticks, [list, None], 'yticks')
        pyt.chkt.checkType(self.do_acc, bool, 'do_acc')
        pyt.chkt.checkType(self.do_rmse, bool, 'do_rmse')
        pyt.chkt.checkType(self.add_ensmean, bool , 'add_ensmean')
        for e in self.mpl_line_opts:
            pyt.chkt.checkType(e, dict, 'elements in mpl_line_opts')
        if isinstance(self.xlim, list):
            if len(self.xlim) != 2:
                raise ValueError('len(xlim) must be 2')
        if isinstance(self.ylim_acc, list):
            if len(self.ylim_acc) != 2:
                raise ValueError('len(ylim_acc) must be 2')
        if isinstance(self.ylim_rmse, list):
            if len(self.ylim_rmse) != 2:
                raise ValueError('len(ylim_rmse) must be 2')
        self.mpl_line_opts = CircularYielder(self.mpl_line_opts)


@dataclass
class Option(): # defalt options
    do_data: bool = True
    do_plot: bool = True
    phase_diagram: dict = field(default_factory=dict)
    score_diagram: dict = field(default_factory=dict)

    def __post_init__(self):
        # convert to class objects
        pyt.chkt.checkType(self.phase_diagram, dict, 'phase_diagram')
        pyt.chkt.checkType(self.score_diagram, dict, 'score_diagram')
        self.phase_diagram = Option_Phase_Diagram(**self.phase_diagram)
        self.score_diagram = Option_Score_Diagram(**self.score_diagram)

        # check types
        pyt.chkt.checkType(self.do_data, bool, 'do_data')
        pyt.chkt.checkType(self.do_plot, bool, 'do_plot')
    

class CircularYielder():
    def __init__(self, items):
        self.items = items
        self.numItems = len(items)
        self.nextInd = 0

    def __call__(self):
        output = self.items[self.nextInd]
        self.nextInd += 1

        if self.nextInd == self.numItems:
            self.nextInd = 0

        return output

    def reset(self):
        self.nextInd = 0

