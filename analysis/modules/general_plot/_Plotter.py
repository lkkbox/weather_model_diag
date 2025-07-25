import pytools as pyt 
import copy
from matplotlib import pyplot as plt
import matplotlib
import numpy as np
from dataclasses import dataclass
import os


class Plotter():
    def __init__(self, cases, plot_set, data_dir, fig_dir_root):
        matplotlib.use('Agg') # don't start interactive plots
        from .subdriver import Option_Shading
        from .subdriver import Option_Vector
        from .subdriver import Option_Contour
        from .subdriver import Option_Line

        # spamming settings to local space
        self.cases = cases
        self.plot_set = plot_set
        self.data_dir = data_dir
        self.figs = plot_set.figs

        self.Option_Shading = Option_Shading
        self.Option_Vector = Option_Vector
        self.Option_Contour = Option_Contour
        self.Option_Line = Option_Line
        self.plot_types = [
            *self.plot_set.shadings,
            *self.plot_set.vectors,
            *self.plot_set.contours,
            *self.plot_set.lines,
        ]
        self.read_methods = {
            'auto': self._read_auto,
        }
        self.fn_map = {
            self.Option_Shading: self.shading,
            self.Option_Contour: self.contour,
            self.Option_Line:   self.line,
            self.Option_Vector: self.vector,
        }

        # ---- validate the read_method
        for plot_type in self.plot_types:
            if plot_type.read_method not in self.read_methods:
                raise ValueError(f'unrecognized {plot_type.read_method=}')

        # ---- figure out auto configurations for plot_set
        if self.plot_set.xlim is None:
            if plot_type.auto_xlim is not None:
                self.plot_set.xlim =  [
                    min([plot_type.auto_xlim[0] for plot_type in self.plot_types]),
                    max([plot_type.auto_xlim[1] for plot_type in self.plot_types]),
                ]
            else:
                self.plot_set.xlim = None

        if self.plot_set.ylim is None:
            if plot_type.auto_ylim is not None:
                self.plot_set.ylim =  [
                    min([plot_type.auto_ylim[0] for plot_type in self.plot_types]),
                    max([plot_type.auto_ylim[1] for plot_type in self.plot_types]),
                ]
            else:
                self.plot_set.ylim = None

        # initialize fig (and axes inside)
        fig_dir = f'{fig_dir_root}/general_plot'
        self.figs = [self._init_fig(fig_dir, fig, ifig) for ifig, fig in enumerate(self.figs)]

        # validating dim_means for case
        dim_means = [subplot.dim_means for subplot in self.plot_set.subplots]
        if self.plot_set.subplots_dim_by == 'case':
            for isubplot, dim_mean in enumerate(dim_means):
                if dim_mean is None:
                    dim_mean = [isubplot, isubplot]
                elif dim_mean[0] != dim_means[1]:
                    raise ValueError(f'Not supporting average over different cases: "subplot_dim_by=case", {dim_mean=}')
                elif not isinstance(dim_mean[0], int) or not (0<=dim_mean[0]<self.plot_set._numCases):
                    raise ValueError(f'dim_mean for cases must be between 0 and {len(self.cases)}, but found {dim_mean[0]} instead.')


        dim_means = [fig.dim_means for fig in self.plot_set.figs]
        if self.plot_set.figs_dim_by == 'case':
            for ifig, dim_mean in enumerate(dim_means):
                if dim_mean is None:
                    dim_mean = [ifig, ifig]
                elif dim_mean[0] != dim_mean[1]:
                    raise ValueError(f'Not supporting average over different cases: "fig_dim_by=case", {dim_mean=}')
                elif not isinstance(dim_mean[0], int) or not (0<=dim_mean[0]<self.plot_set._numCases):
                    raise ValueError(f'dim_mean for cases must be between 0 and {len(self.cases)}, but found {dim_mean[0]} instead.')


    def _init_fig(self, fig_dir, fig, ifig):
        if not os.path.exists(fig_dir):
            os.makedirs(fig_dir)

        fig.ifig = ifig
        fig.path = f'{fig_dir}/{fig.name}'
        fig.fig = plt.figure(**fig.mpl_opts)
        fig.subplots = [copy.copy(subplot) for subplot in self.plot_set.subplots]

        for isubplot, subplot in enumerate(fig.subplots):
            subplot.ax = fig.fig.add_subplot(*subplot.position, **subplot.mpl_opts)
            subplot.isubplot = isubplot
            subplot.topRightTitle = ''

        return fig


    def run(self):
        # read and draw each plot type
        for plot_type in self.plot_types:
            self._run_plot_type(plot_type)


        # draw post plot types
        for fig in self.figs:
            for subplot in fig.subplots:
                self._post_draw_ax_features(subplot)

        # decorating
        for fig in self.figs:
            self._draw_fig_features(fig)

            for subplot in fig.subplots:
                self._draw_ax_features(subplot)

        for fig in self.figs:
            print(f'saving to {fig.path}')
            fig.fig.savefig(fig.path)
            plt.close(fig.fig)

        
    def _run_plot_type(self, plot_type):
        isVecPlot = isinstance(plot_type, self.Option_Vector)

        # read data
        datas1 = self._read_datas(plot_type, i_variable=0)
        datas2 = self._read_datas(plot_type, i_variable=1)

        # perform operators on datas
        for data1, data2 in zip(datas1, datas2):
            for operator in plot_type.operators:
                if data1.vals is None:
                    continue
                data1.vals, data2.vals = operator(data1.vals, data1.dims, data2.vals)

        # average over none plot axes
        for data1, data2 in zip(datas1, datas2):
            data1 = self._average_non_plot_axis(data1, plot_type)
            data2 = self._average_non_plot_axis(data2, plot_type)

        # regrid data for the plotting x, y axis
        idimx = plot_type.xy_axis[0]
        idimy = plot_type.xy_axis[1]
        if idimx is not None:
            regrid_x = np.r_[
                plot_type.minMaxs[idimx][0]:
                plot_type.minMaxs[idimx][1]+1:
                plot_type.regrid_delta_x
            ]
        if idimy is not None:
            regrid_y = np.r_[
                plot_type.minMaxs[idimy][0]:
                plot_type.minMaxs[idimy][1]+1:
                plot_type.regrid_delta_y
            ]

        for data1, data2 in zip(datas1, datas2):
            if idimx is not None:
                data1 = self._regrid_data(data1, regrid_x, idimx)
                data2 = self._regrid_data(data2, regrid_x, idimx)
            if idimy is not None:
                data1 = self._regrid_data(data1, regrid_y, idimy)
                data2 = self._regrid_data(data2, regrid_y, idimy)

        # dimension average for x, y axis
        # [case][raw dims] -> [fig][subplot][y, x]
        datas1 = self._manipulate_dims(datas1, plot_type, self.plot_set)
        datas2 = self._manipulate_dims(datas2, plot_type, self.plot_set)

        # draw
        draw_fn = self.fn_map.get(type(plot_type))
        for fig, datas1_fig, datas2_fig in zip(self.figs, datas1, datas2):
            for subplot, data1, data2 in zip(
                fig.subplots, datas1_fig, datas2_fig
            ):
                if data1.vals is None:
                    print('warning: no data is drawn')
                    continue

                x, y, z, v = data1.dims[0], data1.dims[1], data1.vals, data2.vals
                z = self._smooth(plot_type.smooths, x, y, z)
                z = self._math(plot_type.math, z)
                v = self._smooth(plot_type.smooths, x, y, v)
                v = self._math(plot_type.math, v)

                if plot_type.amean:
                    slicex = pyt.ct.value2Slice(x, *plot_type.amean[:2])
                    slicey = pyt.ct.value2Slice(y, *plot_type.amean[-2:])
                    subplot.topRightTitle += f' amean={np.nanmean(z[slicey, slicex]):+.1E}'

                # plot
                if not isVecPlot:
                    draw_fn(subplot, x, y, z, plot_type)
                else:
                    draw_fn(subplot, x, y, z, v, plot_type)
                    

    def _draw_fig_features(self, fig):
        if fig.title is not None:
            fig.fig.suptitle(fig.title)


    def _draw_ax_features(self, subplot):
        # xlim, ylim
        if self.plot_set.xlim is not None:
            subplot.ax.set_xlim(self.plot_set.xlim)
        if self.plot_set.ylim is not None:
            subplot.ax.set_ylim(self.plot_set.ylim)

        if subplot.irow == subplot.nrows - 1:
            subplot.ax.set_xlabel(self.plot_set.xlabel, fontsize=self.plot_set.fontsize_xlabel)

        if subplot.icol == 0:
            subplot.ax.set_ylabel(self.plot_set.ylabel, fontsize=self.plot_set.fontsize_ylabel)

        # map ticks
        if self.plot_set.world_tick_dx is not None:
            pyt.pt.wmapaxisx(subplot.ax, self.plot_set.world_tick_dx)
        if self.plot_set.world_tick_dy is not None:
            pyt.pt.wmapaxisy(subplot.ax, self.plot_set.world_tick_dy)

        # tick font size
        if self.plot_set.fontsize_ticks is not None:
            subplot.ax.tick_params(axis='both', labelsize=self.plot_set.fontsize_ticks)

        # title: do not set it before xlim/ylim
        if subplot.title is None and self.plot_set.subplots_dim_by == "case":

            if self.plot_set.with_obs:
                if subplot.isubplot == 0:
                    name = 'obs'
                else:
                    name = self.cases[subplot.isubplot - 1].name
            else:
                name = self.cases[subplot.isubplot].name

            subplot.title = f'({chr(subplot.isubplot+97)}) {name}'

        pyt.pt.titleCorner(subplot.ax, subplot.title)

        if self.plot_set.grid_on:
            subplot.ax.grid()
    
                
    def _post_draw_ax_features(self, subplot):
        if self.plot_set.coastline_opts is not None:
            pyt.pt.plotcoast(subplot.ax, **self.plot_set.coastline_opts)

        if subplot.topRightTitle is not None:
            pyt.pt.titleCorner(
                subplot.ax, subplot.topRightTitle, cornerIndex=[1, 1],
                horizontalalignment='right',
            )

        if self.plot_set.draw_box is not None:
            x = [self.plot_set.draw_box[i  ] for i in [0, 0, 1, 1, 0]]
            y = [self.plot_set.draw_box[i+2] for i in [0, 1, 1, 0, 0]]
            opts = self.plot_set.draw_box[-1]
            subplot.ax.plot(x, y, **opts)


    def shading(self, subplot, x, y, z, plot_type):
        if plot_type.levels is None:
            levels = pyt.ct.nearest_nice_number(np.percentile(z, np.r_[0:110:10]))
            plot_type.levels = [
                clev for i, clev in enumerate(levels) if clev not in levels[:i]
            ]
            

        if plot_type.colormap is None:
            plot_type.colormap = 'viridis'


        plot_colorbar = subplot.irow==0 and subplot.icol==subplot.ncols-1

        pyt.pt.contourf2(
            subplot.ax, x, y, z,
            plot_type.levels, plot_type.colormap,
            plotColorbar=plot_colorbar
        )

        if plot_type.contour_opts is not None:
            if 'levels' not in plot_type.contour_opts:
                plot_type.contour_opts = {
                    'levels': plot_type.levels,
                    **plot_type.contour_opts
                }
            subplot.ax.contour(x, y, z, **plot_type.contour_opts)


    def contour(self, subplot, x, y, z, plot_type):
        for mpl_opts in plot_type.mpl_opts_list:
            subplot.ax.contour(x, y, z, **mpl_opts)


    def line(self, subplot, x, y, z, plot_type):
        if plot_type.xy_axis[0] is None:
            linex = z.squeeze()
            liney = y
        elif plot_type.xy_axis[1] is None:
            linex = x
            liney = z.squeeze()

        subplot.ax.plot(linex, liney, **plot_type.mpl_opts)


    def vector(self, subplot, x, y, u, v, plot_type):
        xskip= int(len(x) / plot_type.nxPerPanel)
        yskip= int(len(y) / plot_type.nyPerPanel)
        xx = x[::xskip]
        yy = y[::yskip]
        uu = pyt.ct.smooth( pyt.ct.smooth(u, yskip, -2), xskip, -1)[::yskip, ::xskip]
        vv = pyt.ct.smooth( pyt.ct.smooth(v, yskip, -2), xskip, -1)[::yskip, ::xskip]

        handle = subplot.ax.quiver(xx, yy, uu, vv, **plot_type.matplotlib_opts)
        
        # set up the vector size to follow the first panel
        if subplot.index == 1:
            attrs = ['angles', 'pivot', 'scale', 'scale_units', 'units',
                     'width', 'headwidth', 'headlength', 'headaxislength',
                     'minshaft', 'minlength']
            add_settings = {
                attr: getattr(handle, attr) 
                for attr in attrs 
                if attr not in plot_type.matplotlib_opts
            }
            plot_type.matplotlib_opts = {**plot_type.matplotlib_opts, **add_settings}

        # if irow == 0 and icol == self.ncols - 1:
        #     ax.quiverkey(handle, 1.05, 1.05, 3, label='3', labelpos='E',)


    def _smooth(self, smooths, x, y, z):
        if smooths is None or z is None:
            return z
        smooth_x, smooth_y = smooths
        if smooth_x is not None:
            n_smooth_x = int(round(smooth_x / (x[1] - x[0])))
            z = pyt.ct.smooth(z, n_smooth_x, 1)
        if smooth_y is not None:
            n_smooth_y = int(round(smooth_y / (y[1] - y[0])))
            z = pyt.ct.smooth(z, n_smooth_y, 0)
        return z


    def _math(self, math, z):
        if not math or z is None:
            return z
        return math(z)


    def _read_datas(self, plot_type, i_variable):
        if i_variable == 0:
            variable = plot_type.variable
        elif i_variable == 1:
            variable = plot_type.variable2
        else:
            raise NotImplementedError(f'{i_variable = }')

        if variable is None:
            return [_Data(None, None) for _ in range(len(self.plot_set.subplots))]

        read_func = self.read_methods[plot_type.read_method]
        data = read_func(plot_type, variable)
        return data


    def _read_auto(self, plot_type, variable):
        def read_obs():
            obs_data_dir = f'{self.data_dir}/obs'
            # calculating valid time
            minInit = min([min(case.model.initTimes) for case in self.cases])
            maxInit = max([max(case.model.initTimes) for case in self.cases])
            obsTimeRange = [
                init + lead for init, lead in zip(
                    [minInit, maxInit], plot_type.minMaxs[0]
                )
            ]
            minMaxs = [obsTimeRange, *plot_type.minMaxs[1:]]
            
            if plot_type.total_anomaly == 'anomaly':
                data, dims = pyt.rt.obsReader.anomaly(
                    variable, minMaxs, plot_type.obs_source,
                    climYears=plot_type.obs_clim_yr, root=obs_data_dir
                )

            else:
                data, dims = pyt.rt.obsReader.total(
                    plot_type.variable, minMaxs, plot_type.obs_source,
                )
            dims[0] = [t - dims[0][0] for t in dims[0]] # from time to lead
            return data, dims


        def read_mod(case):
            data_type = "global_daily_1p0"
            mod_data_dir = f'{self.data_dir}/processed'
            minMaxs = plot_type.minMaxs.copy()
            if len(minMaxs) == 4: # hPa -> Pa
                minMaxs[1] = [hPa * 100 for hPa in minMaxs[1]]
            if plot_type.total_anomaly == 'anomaly':
                data, dims = pyt.modelreader.readAnomaly.readAnomaly(
                    case.model.name,  data_type, variable, minMaxs,
                    case.model.initTimes, case.model.members, case.model.climYears,
                    rootDir=mod_data_dir,
                )
            else:
                data, dims = pyt.modelreader.readTotal.readTotal(
                    case.model.name,  data_type, variable, minMaxs,
                    case.model.initTimes, case.model.members,
                    rootDir=mod_data_dir,
                )

            if data is None:
                print('warning: no data is read')
                return None, None

            if len(minMaxs) == 4: # Pa -> hPa
                dims[-3] /= 100

            data = np.squeeze(data, axis=(0, 1))
            return data, dims

        datas = []
        if self.plot_set.with_obs:
            data, dims = read_obs()
            datas.append(_Data(data, dims))
            

        for case in self.cases:
            data, dims = read_mod(case)
            datas.append(_Data(data, dims))

        return datas


    def _average_non_plot_axis(self, data, plot_type):
        if data.vals is None:
            return data

        # change negative figs/subplots_dim_by to positive
        figs_dim = _sanitize_negative_axis(self.plot_set.figs_dim_by, data.vals.ndim)
        subplots_dim = _sanitize_negative_axis(self.plot_set.subplots_dim_by, data.vals.ndim)

        axis_to_average = [*list(range(data.vals.ndim)), "case"]
        for do_not_average in [
            plot_type.xy_axis[0],
            plot_type.xy_axis[1],
            figs_dim,
            subplots_dim,
        ]:
            if do_not_average is not None:
                axis_to_average.remove(do_not_average)

        data.vals = np.nanmean(data.vals, axis=tuple(axis_to_average), keepdims=True)
        return data


    def _regrid_data(self, data, x, idimx):
        if data.vals is None:
            return data

        data.vals = pyt.ct.interp_1d(data.dims[idimx], data.vals, x, idimx, extrapolate=True)
        data.dims[idimx] = x
        return data

    def _manipulate_dims(self, datas, plot_type, plot_set):
        # [case][y, x] -> [fig][subplot][y, x]
        if all((d.vals is None for d in datas)):
            return [
                [_Data(None, None)] * len(plot_set.subplots)
            ] * len(self.figs)

        for d in datas:
            if d.vals is not None:
                data = d

        figs_dim_by = _sanitize_negative_axis(plot_set.figs_dim_by, d.vals.ndim)
        subplots_dim_by = _sanitize_negative_axis(plot_set.subplots_dim_by, d.vals.ndim)

        datas_out = []
        for ifig in range(len(self.figs)):
            datas_sublist = []
            for isubplot in range(len(self.plot_set.subplots)):
                if plot_set.figs_dim_by == 'case':
                    icase = ifig
                elif plot_set.subplots_dim_by == 'case':
                    icase = isubplot
                else:
                    # should be caught in Option and would not happen though
                    raise RuntimeError('help! cannot identify "icase"')

                if datas[icase].vals is None:
                    datas_sublist.append(_Data(None, None))
                    continue

                slices = [slice(None)] * datas[icase].vals.ndim

                if isinstance(figs_dim_by, int):
                    slices[figs_dim_by] = pyt.ct.value2Slice(
                        datas[icase].dims[figs_dim_by], *self.figs[ifig].dim_means
                    )

                if isinstance(subplots_dim_by, int):
                    slices[subplots_dim_by] = pyt.ct.value2Slice(
                        datas[icase].dims[subplots_dim_by], *plot_set.subplots[isubplot].dim_means
                    )

                data = _Data(None, None)
                mean_over = (i for i in range(datas[icase].vals.ndim) if i not in plot_type.xy_axis)
                data.vals = np.nanmean(
                    datas[icase].vals[*slices], axis=tuple(mean_over)
                )
                if (
                    None not in plot_type.xy_axis \
                    and plot_type.xy_axis[1] > plot_type.xy_axis[0] # swap xy axis if reversed
                ):
                    data.vals = np.swapaxes(data.vals, 0, 1)

                elif plot_type.xy_axis[0] is None:
                    data.vals = data.vals[:, None]

                elif plot_type.xy_axis[1] is None:
                    data.vals = data.vals[None, :]

                data.dims = [
                    datas[icase].dims[i] 
                    if i is not None else None 
                    for i in plot_type.xy_axis
                ]

                datas_sublist.append(data)
            datas_out.append(datas_sublist)

        return datas_out


def _sanitize_negative_axis(axis, ndim):
    if axis == "case" or axis is None:
        return axis
    if axis < 0:
        axis = axis + ndim
    return axis


@dataclass
class _Data:
    vals: np.ndarray
    dims: list

