'''
The script to call diagnostic modules.
    - MJO

----
run
└ module - subdriver
    
'''
import pytools as pyt
from dataclasses import dataclass
import traceback
import os

@dataclass
class Model():
    name: str
    initTime0: float
    numInitTimes: int
    members: list
    numLeads: int
    hasClim: bool
    climYears: list = None

    def __post_init__(self):
        pyt.chkt.checkType(self.name, str, 'name')
        pyt.chkt.checkType(self.initTime0, float, 'initTime0')
        pyt.chkt.checkType(self.numInitTimes, int, 'numInitTimes')
        pyt.chkt.checkType(self.members, list, 'members')
        pyt.chkt.checkType(self.numLeads, int, 'numLeads')
        pyt.chkt.checkType(self.hasClim, bool, 'hasClim')
        pyt.chkt.checkType(self.climYears, [list, None], 'climYears')
        if not self.hasClim and self.climYears is not None:
            raise ValueError('hasClim=True but climYears is not None')
        self.initTimes = [self.initTime0 + i for i in range(self.numInitTimes)]
        self.numMembers = len(self.members)


@dataclass
class Case():
    name: str
    model: Model

    def __post_init__(self):
        pyt.chkt.checkType(self.name, str, 'name')
        pyt.chkt.checkType(self.model, Model, 'model')


def run(cases, modules, dataRootDir, figRootDir):
    # ---- validate inputs
    for module in modules:
        pyt.chkt.checkType(module, Module, 'module')

    for case in cases:
        pyt.chkt.checkType(case, Case, 'case')

    names = [case.name for case in cases]
    for i, name in enumerate(names):
        if name in names[:i]:
            raise ValueError(f'duplicated case name "{name}"')

    pyt.chkt.checkType(dataRootDir, str, 'dataRootDir')
    dataRootDir = os.path.realpath(dataRootDir)
    if not os.path.exists(dataRootDir):
        raise FileNotFoundError(f'{dataRootDir = }')

    pyt.chkt.checkType(figRootDir, str, 'figRootDir')
    figRootDir = os.path.realpath(figRootDir)
    if not os.path.exists(figRootDir):
        raise FileNotFoundError(f'{figRootDir = }')
    if not os.access(figRootDir, os.W_OK):
        raise PermissionError(f'{figRootDir = }')
    figDir = f'{figRootDir}/{pyt.ft.getPyName()}'

    # ---- run each module
    for module in modules:
        module.subdriver.run(cases, dataRootDir, figDir)


@dataclass
class Module():
    name: str
    option: dict

    def __post_init__(self):
        pyt.chkt.checkType(self.name, str, 'name')
        pyt.chkt.checkType(self.option, dict, 'option')
        subdriver_mapper = {
            'mjo': _SubDriver_MJO,
            'scores': _SubDriver_Scores,
            'general_plot': _SubDriver_General_Plot,
        }
        if self.name not in subdriver_mapper:
            raise NotImplementedError(f'module name = {self.name}')

        self.stat = True
        try: # nest the initiation with a safe wrapper
            self.subdriver = subdriver_mapper[self.name](self.name, self.option)
        except Exception:
            self.stat = False
            self.error = traceback.format_exc()

        if not self.stat:
            raise RuntimeError(f'module {self.name} is not loaded because\n {self.error}')


class _SubDriver():
    def __init__(self, name):
        self.stat = True
        self.error = ''
        self.name = name
        
    def run(self, cases, dataDir, figDir):
        print(f'[{self.name}] running')
        try: # nest the run with a  safe wrapper
            self.subdriver.run(cases, dataDir, figDir, self.option)
        except Exception as e:
            self.stat = False
            self.error = traceback.format_exc()
        if not self.stat:
            print(f'[{self.name}] error - {self.error}')
        else:
            print(f'[{self.name}] finished')


class _SubDriver_MJO(_SubDriver):
    def __init__(self, name, option):
        super().__init__(name)
        from modules.mjo import subdriver
        self.subdriver = subdriver
        self.option = subdriver.Option(**option) # dict -> dataclass and validate options


class _SubDriver_General_Plot(_SubDriver):
    def __init__(self, name, option):
        super().__init__(name)
        from modules.general_plot import subdriver
        self.subdriver = subdriver
        self.option = subdriver.Option(**option) # dict -> dataclass and validate options


class _SubDriver_Scores(_SubDriver):
    def __init__(self, name, option):
        super().__init__(name)
        from modules.scores import subdriver
        self.subdriver = subdriver
        self.option = subdriver.Option(**option) # dict -> dataclass and validate options
    

def greeter(func, prefix='', suffix=''):
    def wrapper(*args, **kwargs):
        print(f'    [{prefix}{func.__name__}{suffix}] running')
        func(*args, **kwargs)
        print(f'    [{prefix}{func.__name__}{suffix}] finished')
    return wrapper


def safe_runner(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception:
            traceback.print_exc()
    return wrapper
