#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
from rmmPhaseDiagram import phase_diagram
import pytools as pyt
import matplotlib.pyplot as plt
import numpy as np
import os
from dataclasses import dataclass


def main():
    plotter = Rmm_plotter(
        dataRoot='../../../data/MJO/RMM',
        members=[0],
        numLeads=30,
        initTimes=[pyt.tt.ymd2float(2009, 1, 26)],
        models={
            'exp_mjo-DEVM21': 'CTL',
            'exp_mjo-DEVM21S9': 'S',
            'exp_mjo-M22G3IKH': 'M',
            'exp_mjo-M22G3IKHS9': 'MS',
        },
        figset='exp_mjo_250529',
        leadMeans=[], #[slice(0, 5), slice(5, 10), slice(10, 15), slice(15,20), slice(20, 30)],
        initMeans=[slice(0, 1)],
    )
    plotter.run()


@dataclass
class Rmm_plotter():
    dataRoot: str
    initTimes: list
    members: int
    numLeads: int
    models: dict
    figset: str
    leadMeans: list
    initMeans: list


    def __post_init__(self):
        self.numModels = len(self.models)
        self.numInits = len(self.initTimes)
        self.numMembers = len(self.members)
        self.figDir = f'../../../figs/{self.figset}/MJO'
        if not os.path.exists(self.figDir):
            os.system(f'mkdir -p {self.figDir}')
        self.fp = pyt.tmt.FlushPrinter()


    def run(self):
        self.fp.print(f'> entering {self.__class__.__name__}')
        self._read_indices()
        self._calculate_scores()
        self._plot_scores()
        self._plot_phase_diagram(meanOver='lead')
        self._plot_phase_diagram(meanOver='init')
        self.fp.print(f'> exiting {self.__class__.__name__}')


    def _read_indices(self):
        # ---- obs
        self.fp.flush('reading obs')
        timeRange = [min(self.initTimes), max(self.initTimes) + self.numLeads]
        paths = [
            pyt.tt.float2format(
                date,
                f'{self.dataRoot}/obs/%Y/%y%m%d_RMM.nc',
            )
            for date in np.r_[timeRange[0]:timeRange[1]+1]
        ]
        paths = [p for i, p in enumerate(paths) if p not in paths[:i]]
        pc1_obs, dims_obs = pyt.rt.multiNcRead.read(paths, 'pc1', [[None]*2], stackedAlong=0)
        pc2_obs, dims_obs = pyt.rt.multiNcRead.read(paths, 'pc2', [[None]*2], stackedAlong=0)

        # ---- align the obs to valid dates
        pc1_valid = np.nan * np.ones((self.numInits, self.numLeads))
        pc2_valid = np.nan * np.ones((self.numInits, self.numLeads))
        date_obs = list(dims_obs[0])
        for iInit, initTime in enumerate(self.initTimes):
            validDates = [initTime + lead for lead in range(self.numLeads)]
            iDates = [date_obs.index(vd) for vd in validDates]
            pc1_valid[iInit, :] = pc1_obs[iDates]
            pc2_valid[iInit, :] = pc2_obs[iDates]

        # ---- model
        def getModelPath(modelName, iMember, initTime):
            return pyt.tt.float2format(
                initTime,
                f'{self.dataRoot}/{modelName}/%Y/E{iMember:03d}/%y%m%d_RMM.nc'
            )

        pc1_model = np.nan * np.ones((self.numModels, self.numMembers, self.numInits, self.numLeads))
        pc2_model = np.nan * np.ones((self.numModels, self.numMembers, self.numInits, self.numLeads))

        for iModel, modelName in enumerate(self.models):
            for iInit, initTime in enumerate(self.initTimes):
                for iMember in range(self.numMembers):
                    path = getModelPath(modelName, iMember, initTime)
                    if not os.path.exists(path):
                        print(f'path not found {path}')
                        continue
                    pc1 = pyt.nct.read(path, 'pc1')
                    pc2 = pyt.nct.read(path, 'pc2')

                    nt = min([len(pc1), self.numLeads])
                    pc1_model[iModel, iMember, iInit, :nt] = pc1[:nt]
                    pc2_model[iModel, iMember, iInit, :nt] = pc2[:nt]

        # ---- output
        self.pc1_valid, self.pc2_valid = pc1_valid, pc2_valid
        self.pc1_model, self.pc2_model = pc1_model, pc2_model


    def _calculate_scores(self):
        pc1_valid, pc2_valid = self.pc1_valid, self.pc2_valid
        pc1_model, pc2_model = self.pc1_model, self.pc2_model

        acc = np.nansum((pc1_model * pc1_valid + pc2_model * pc2_valid), axis=-2)
        acc /= np.sqrt(np.nansum(pc1_model ** 2 + pc2_model ** 2, axis=-2))
        acc /= np.sqrt(np.nansum(pc1_valid ** 2 + pc2_valid ** 2, axis=-2))

        rmse = np.sqrt(
            np.nanmean(
                (pc1_model - pc1_valid) ** 2 + (pc2_model - pc2_valid) ** 2,
                axis=-2
            )
        )
        acc = np.nanmean(acc, axis=1) # score mean over ensemble
        rmse = np.nanmean(rmse, axis=1) # score mean over ensemble

        # ---- output
        self.acc, self.rmse = acc, rmse


    def _plot_scores(self):
        x = list(range(1, self.numLeads+1))
        fig = plt.figure()
        for iax, (scores, name) in enumerate(zip([self.rmse, self.acc], ['RMSE', 'ACC'])):
            ax = fig.add_subplot(2, 1, iax+1)
            for score, model in zip(scores, self.models): 
                ax.plot(x, score, label=self.models[model])
            ax.set_ylabel(name)
            ax.set_xlim([1, self.numLeads])
            ax.grid()
            if iax == 0:
                ax.set_title('Bivariate scores of RMM indices')
            if iax == 1:
                ax.set_xlabel('lead (days)')
                ax.legend()

        figName = f'{self.figDir}/rmm_score.png'
        fig.savefig(figName)
        self.fp.print(f'saved to {figName}')
        plt.close()


    def _plot_phase_diagram(self, meanOver):
        def initSlices_to_string(_slice):
            start, stop = _slice.start, _slice.stop
            str_start = pyt.tt.float2format(self.initTimes[start], '%Y%m%d')
            str_end = pyt.tt.float2format(self.initTimes[stop-1], '%Y%m%d')
            if str_start != str_end:
                str_time = '-'.join([str_start, str_end])
            else:
                str_time = str_start
            return str_time

        if meanOver == 'init':
            slices = self.initMeans
            averager = lambda data, _slice: np.nanmean(data[_slice, :], axis=-2)
            slice_to_string = lambda _slice: f'{pyt.tt.times2string(self.initTimes[_slice])}'

        elif meanOver == 'lead':
            slices = self.leadMeans
            averager = lambda data, _slice: np.nanmean(data[:, _slice], axis=-1)
            slice_to_string = lambda _slice: f'{_slice.start+1}-{_slice.stop}'

        for _slice in slices:
            fig, ax = phase_diagram()
            # -- model
            for pc1, pc2, model in zip(self.pc1_model, self.pc2_model, self.models):
                for iMember in range(self.numMembers):
                    x = averager(pc1[iMember, :], _slice)
                    y = averager(pc2[iMember, :], _slice)
                    if iMember == 0:
                        line, = ax.plot(x, y, label=self.models[model])
                        color = line.get_color()
                    else:
                        ax.plot(x, y, color=color)
                    ax.plot(x[0], y[0], marker='o', color='k')

            # -- obs
            x = averager(self.pc1_valid, _slice)
            y = averager(self.pc2_valid, _slice)
            ax.plot(x, y, label='obs', color='k', linewidth=2)
            ax.plot(x[0], y[0], marker='o', color='k')

            ax.set_title(f'{meanOver}={slice_to_string(_slice)}')
            ax.legend()
            figName = f'{self.figDir}/rmm_phase_{meanOver}_{slice_to_string(_slice)}.png'
            fig.savefig(figName)
            self.fp.print(f'saved to {figName}')
            plt.close()
        

if __name__ == '__main__':
    main()
