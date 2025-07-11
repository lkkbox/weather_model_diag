from driver import Case
from .rmmPhaseDiagram import phase_diagram
import pytools as pyt
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import os
from dataclasses import dataclass


@dataclass
class Rmm_plotter():
    dataRoot: str
    figDir: str
    cases: list[Case]
    option: dict


    def __post_init__(self):
        matplotlib.use('Agg') # don't start interactive plots
        self.numCases = len(self.cases)
        self.numInits = self.cases[0].model.numInitTimes
        self.numLeads = max([case.model.numLeads for case in self.cases])
        self.initTimes = self.cases[0].model.initTimes

        self.figDir = f'{self.figDir}'
        if not os.path.exists(self.figDir):
            os.system(f'mkdir -p {self.figDir}')
        self.fp = pyt.tmt.FlushPrinter()


    def run(self):
        self.fp.print(f'> entering {self.__class__.__name__}')
        self._read_indices()
        self._calculate_scores()
        self._plot_scores()
        self._plot_phase_diagram(meanOver='lead', drawMembers=True)
        self._plot_phase_diagram(meanOver='init', drawMembers=True)
        self._plot_phase_diagram(meanOver='lead', drawMembers=False)
        self._plot_phase_diagram(meanOver='init', drawMembers=False)
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
        def getModelPath(modelName, member, initTime, hasClim):
            if hasClim:
                nobc = ''
            else:
                nobc = '-noBC'
            return pyt.tt.float2format(
                initTime,
                f'{self.dataRoot}/{modelName}{nobc}/%Y/E{member:03d}/%y%m%d_RMM.nc'
            )

        # list[array]: [model][member, init, lead]
        pc1_cases = [None for __ in range(self.numCases)]
        pc2_cases = [None for __ in range(self.numCases)]
        for iCase, case in enumerate(self.cases):
            numMembers = case.model.numMembers
            pc1_cases[iCase] = np.nan * np.ones((numMembers, self.numInits, self.numLeads))
            pc2_cases[iCase] = np.nan * np.ones((numMembers, self.numInits, self.numLeads))
            for iMember, member in enumerate(case.model.members):
                for iInit, initTime in enumerate(self.initTimes):
                    path = getModelPath(case.model.name, member, initTime, case.model.hasClim)
                    if not os.path.exists(path):
                        print(f'path not found {path}')
                        continue
                    pc1 = pyt.nct.read(path, 'pc1')
                    pc2 = pyt.nct.read(path, 'pc2')

                    nt = min([len(pc1), self.numLeads])
                    pc1_cases[iCase][iMember, iInit, :nt] = pc1[:nt]
                    pc2_cases[iCase][iMember, iInit, :nt] = pc2[:nt]

        # ---- output
        self.pc1_valid, self.pc2_valid = pc1_valid, pc2_valid
        self.pc1_cases, self.pc2_cases = pc1_cases, pc2_cases


    def _calculate_scores(self):
        pc1_valid, pc2_valid = self.pc1_valid, self.pc2_valid
        pc1_cases, pc2_cases = self.pc1_cases, self.pc2_cases

        def cal_acc(pc1, pc2):
            acc = np.nansum((pc1 * pc1_valid + pc2 * pc2_valid), axis=-2)
            acc /= np.sqrt(np.nansum(pc1 ** 2 + pc2 ** 2, axis=-2))
            acc /= np.sqrt(np.nansum(pc1_valid ** 2 + pc2_valid ** 2, axis=-2))
            return acc

        def cal_rmse(pc1, pc2):
            rmse = np.sqrt(
                np.nanmean(
                    (pc1 - pc1_valid) ** 2 + (pc2 - pc2_valid) ** 2,
                    axis=-2
                )
            )
            return rmse

        accs = [cal_acc(pc1, pc2) for pc1, pc2 in zip(pc1_cases, pc2_cases)]
        rmses = [cal_rmse(pc1, pc2) for pc1, pc2 in zip(pc1_cases, pc2_cases)]

        # ---- output
        self.accs, self.rmses = accs, rmses


    def _plot_scores(self):
        x = list(range(1, self.numLeads+1))
        scores, names, ylims = [], [], []
        if self.option.score_diagram.do_rmse:
            scores.append(self.rmses)
            names.append('RMSE')
            ylims.append(self.option.score_diagram.ylim_rmse)

        if self.option.score_diagram.do_acc:
            scores.append(self.accs)
            names.append('ACC')
            ylims.append(self.option.score_diagram.ylim_acc)


        nrows = len(scores)
        if nrows == 2:
            figsize = (6.4, 4.8)
        elif nrows == 1:
            figsize = (6.4, 2.6)
        else:
            print('both "do_acc" and "do_rmse" are False, will not plot scores')
            return

        fig_opts = self.option.score_diagram.fig_opts
        if 'figsize' not in fig_opts:
            fig_opts['figsize'] = figsize
        if 'layout' not in fig_opts:
            fig_opts['layout'] = 'constrained'

        fig = plt.figure(**fig_opts)
        for iax, (score_cases, name, ylim) in enumerate(
            zip(scores, names, ylims)
        ):
            ax = fig.add_subplot(len(scores), 1, iax+1)
            ax.set_ylabel(name)
            if self.option.score_diagram.xlim is not None:
                ax.set_xlim(self.option.score_diagram.xlim)
            else:
                ax.set_xlim([1, self.numLeads])

            if ylim is not None:
                ax.set_ylim(ylim)

            if self.option.score_diagram.xticks is not None:
                ax.set_xticks(self.option.score_diagram.xticks)

            if self.option.score_diagram.yticks is not None:
                ax.set_yticks(self.option.score_diagram.yticks)

            ax.grid()
            if iax == 0:
                ax.set_title(f'Bivariate scores of RMM indices, IC={pyt.tt.times2string(self.initTimes)}')

            line_opts = self.option.score_diagram.mpl_line_opts
            line_opts.reset()
            for case, score_members in zip(self.cases, score_cases):
                # plot each member
                for score, member in zip(score_members, case.model.members): 
                    line_opt = line_opts()
                    if 'label' not in line_opt:
                        if member == 0:
                            member_name = 'CTL'
                        elif member < 0:
                            member_name = 'ENS'
                        else:
                            member_name = f'M{member:03d}'

                        label = f'{case.name} {member_name}'

                        if case.model.hasClim:
                            label += '(BC)'

                        line_opt['label'] =  label

                    ax.plot(x, score, **line_opt)

            if iax == 0:
                fig.legend(**self.option.score_diagram.legend_opts)

            if iax == nrows-1:
                ax.set_xlabel('lead (days)')

        figName = f'{self.figDir}/rmm_score.png'
        fig.savefig(figName)
        self.fp.print(f'saved to {figName}')
        plt.close()


    def _plot_phase_diagram(self, meanOver, drawMembers):
        if meanOver == 'init':
            slices = self.option.phase_diagram.init_means
            averager = lambda data, _slice: np.nanmean(data[_slice, :], axis=-2)
            slice_to_string = lambda _slice: f'{pyt.tt.times2string(self.initTimes[_slice])}'

        elif meanOver == 'lead':
            slices = self.option.phase_diagram.lead_means
            averager = lambda data, _slice: np.nanmean(data[:, _slice], axis=-1)
            slice_to_string = lambda _slice: f'{_slice.start+1}-{_slice.stop}'

        if drawMembers:
            ensName = 'ctl_ens'
        else:
            ensName = 'members'

        line_opts = self.option.phase_diagram.mpl_line_opts
        for _slice in slices:
            if meanOver == 'init':
                if _slice.start >= self.numInits:
                    self.fp.print(f'skipping slice={_slice} with numInits={self.numInits}')
                    continue
                if _slice.stop > self.numInits:
                    self.fp.print(f'overwriting {_slice} stop to numInits={self.numInits}')
                    _slice = slice(_slice.start, self.numInits)
            elif meanOver == 'lead':
                if _slice.start >= self.numLeads:
                    self.fp.print(f'skipping slice={_slice} with numLeads={self.numLeads}')
                    continue
                if _slice.stop > self.numLeads:
                    self.fp.print(f'overwriting {_slice} stop to numLeads={self.numLeads}')
                    _slice = slice(_slice.start, self.numLeads)

            fig, ax = phase_diagram()
            markerStep = 10
            markers = '^o*s>'

            line_opts.reset()
            # -- model
            for pc1, pc2, case  in zip(self.pc1_cases, self.pc2_cases, self.cases):
                for iMember, member in enumerate(case.model.members):
                    line_opt = line_opts()
                    if 'label' not in line_opt:
                        if member == 0:
                            member_name = 'CTL'
                        elif member < 0:
                            member_name = 'ENS'
                        else:
                            member_name = f'M{member:03d}'

                        label = f'{case.name} {member_name}'

                        if case.model.hasClim:
                            label += '(BC)'

                        line_opt['label'] =  label

                    x = averager(pc1[iMember, :], _slice)
                    y = averager(pc2[iMember, :], _slice)
                    hline, = ax.plot(x, y, **line_opt)
                    for xx, yy, marker in zip(x[::markerStep], y[::markerStep], markers):
                        ax.plot(xx, yy, color=hline.get_color(), marker=marker)

            # -- obs
            color = 'k'
            x = averager(self.pc1_valid, _slice)
            y = averager(self.pc2_valid, _slice)
            ax.plot(x, y, label='obs', color=color, linewidth=2)
            for xx, yy, marker in zip(x[::markerStep], y[::markerStep], markers):
                ax.plot(xx, yy, color=color, marker=marker)

            title = f'{meanOver}={slice_to_string(_slice)}'
            if _slice.stop - _slice.start > 1:
                title = f'mean({title})'
            ax.set_title(title)

            ax.legend()
            figName = f'{self.figDir}/rmm_phase_{ensName}_{meanOver}_{slice_to_string(_slice)}.png'
            fig.savefig(figName)
            self.fp.print(f'saved to {figName}')
            plt.close()
        

