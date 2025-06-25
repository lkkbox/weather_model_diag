from pytools import timetools as tt
from enum import Enum

class BC_STATE(Enum):
    RAW = 'raw'
    BC = 'bc'


class PathGetter():
    def __init__(self, dataDir):
        self.dataDir = dataDir
        self.subDir = 'scores'

    def get_scores_path(self, modName, member, initTime, numInits, varName, ndma, rawOrBc):
        return tt.float2format(
            initTime,
            f'{self.dataDir}/{self.subDir}/{modName}/E{member:03d}/%y%m%d/{numInits:04d}/{ndma}/'
            + f'{varName}_{BC_STATE(rawOrBc).value}.nc'
        )

    def get_scoreCard_path(self, modName, member, initTime, numInits, rawOrBc):
        return tt.float2format(
            initTime,
            f'{self.dataDir}/{self.subDir}/{modName}/E{member:03d}/%y%m%d/{numInits:04d}/scoreCard'
            + f'_{BC_STATE(rawOrBc).value}.nc'
        )

