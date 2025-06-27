from . import _Plotter
from . import _operators
from driver import greeter
import pytools as pyt
from dataclasses import dataclass, field
import traceback


def run(cases, dataDir, figDir, option):
    # loop over plot_sets
    #   1. derive auto configs
    #   2. loop over plot types
    #     - read data and average over axes
    #     - plot
    #   3. save
    n = len(option.plot_sets)
    for i, plot_set in enumerate(option.plot_sets):
        wrapped_func = greeter(_run_plot_set, '', f'-{i}/{n}')
        try:
            wrapped_func(plot_set, cases, dataDir, figDir)
        except Exception:
            print(traceback.format_exc())


def _run_plot_set(plot_set, cases, dataDir, figDir):
    plotter = _Plotter.Plotter(cases, plot_set, dataDir, figDir)
    plotter.run()


@dataclass
class Option(): # defalt options
    numCases: int 
    plot_sets: list[dict] = None

    def __post_init__(self):
        # default settings
        if self.plot_sets is None:
            self.plot_sets = [
                {},
            ]

        # type checking
        pyt.chkt.checkType(self.numCases, int , 'numCases')
        pyt.chkt.checkType(self.plot_sets, list, 'plot_sets')
        for plot_set in self.plot_sets:
            pyt.chkt.checkType(plot_set, dict, 'elements in plot_set')

        if self.numCases <= 0:
            raise ValueError('numCases cannot be less or equal to 0')
            

        # convert to class objects
        self.plot_sets = [
            Option_Plot_Set(_numCases=self.numCases, **plot_set) for plot_set in self.plot_sets
        ]

        # check for duplicate fig names
        fig_names = [fig.name for plot_set in self.plot_sets for fig in plot_set.figs]
        for i, fig_name in enumerate(fig_names):
            if fig_name in fig_names[:i]:
                raise ValueError(f'duplicate fig_name of {fig_name}')
                
        # did we set up successfully?
        if len(plot_set) == 0:
            raise ValueError('found 0 element for "plot_set"')


@dataclass
class Option_Plot_Set():
    _numCases: int # don't touch it from the driver

    shadings: list = None # see Option_Shading
    contours: list = None # see Option_Contour
    vectors: list = None # see Option_Vector
    lines: list = None # see Option_Line

    figs: list = None # see Option_Fig
    figs_dim_by: str | int = None # separate figures by? "case" (default) or axis:int or None

    subplots: list = None # see Option_Subplot
    subplots_dim_by: str | int = None # separate figures by? "case" (default) or axis:int or None

    with_obs: bool = True # True (default): add obs before case0

    draw_box: list = None # [lonw, lone, lats, latn, {line options}]
    coastline_opts: dict = None # None: dont't draw, {lineoptions}: draw

    xlim: list = None # [minx, maxx]
    ylim: list = None
    world_tick_dx: int = None # int: draw degrees as delta x; None: don't draw degrees
    world_tick_dy: int = None
    xlabel: str = None
    ylabel: str = None

    fontsize_ticks: int = None
    fontsize_xlabel: int = None
    fontsize_ylabel: int = None

    grid_on: bool = False

    def __post_init__(self):
        # set defaults
        if self.shadings is None: self.shadings = []
        if self.contours is None: self.contours = []
        if self.vectors is None: self.vectors = []
        if self.lines is None: self.lines = []
        if self.with_obs:
            self._numCases += 1

        # check types
        pyt.chkt.checkType(self.figs, list, 'figs')
        pyt.chkt.checkType(self.figs_dim_by, [str, int, None], 'figs_dim_by')
        pyt.chkt.checkType(self.subplots, [list, None], 'subplots')
        pyt.chkt.checkType(self.subplots_dim_by, [str, int, None], 'subplots_dim_by')

        pyt.chkt.checkType(self.with_obs, bool, 'with_obs')

        pyt.chkt.checkType(self.grid_on, bool , 'grid_on')

        pyt.chkt.checkType(self.shadings, list, 'shading')
        pyt.chkt.checkType(self.contours, list, 'contour')
        pyt.chkt.checkType(self.vectors, list, 'vector')
        pyt.chkt.checkType(self.lines, list, 'line')

        pyt.chkt.checkType(self.xlim, [list, None], 'xlim')
        pyt.chkt.checkType(self.ylim, [list, None], 'ylim')
        pyt.chkt.checkType(self.xlabel, [str, None], 'xlabel')
        pyt.chkt.checkType(self.ylabel, [str, None], 'ylabel')
        pyt.chkt.checkType(self.world_tick_dx, [int, None], 'world_tick_dx')
        pyt.chkt.checkType(self.world_tick_dy, [int, None], 'world_tick_dy')
        pyt.chkt.checkType(self.fontsize_ticks, [int, float, None], 'fontsize_xtick')
        pyt.chkt.checkType(self.fontsize_xlabel, [int, float, None], 'fontsize_xlabel')
        pyt.chkt.checkType(self.fontsize_ylabel, [int, float, None], 'fontsize_ylabel')
        pyt.chkt.checkType(self.coastline_opts, [dict, None], 'coastline_opts')
        pyt.chkt.checkType(self.draw_box, [list, None], 'draw_box')

        # check more types
        if not self.figs:
            raise ValueError('"figs" must contain at least 1 element.')

        if isinstance(self.figs_dim_by, str) and self.figs_dim_by != "case":
            raise ValueError(f'"figs_dim_by" only takes literal "case" or integers, (found "{self.figs_dim_by}")')

        if isinstance(self.subplots_dim_by, str) and self.subplots_dim_by != "case":
            raise ValueError(f'"subplots_dim_by" only takes literal "case" or integers, (found "{self.subplots_dim_by}")')

        if self.draw_box is not None:
            if len(self.draw_box) != 5:
                raise ValueError('"draw_box" must be 5 elements [lonw, lone, lats, latn, line_options]')
            for e in self.draw_box[:4]:
                pyt.chkt.checkType(e, [int, float], 'first 4 elements of "draw_box" (lon/lat bounds)')
            pyt.chkt.checkType(self.draw_box[4], dict, 'The 5th element of "draw_box" (line_options)')

        # find out the auto options for figures and subplots
        if self.figs_dim_by != "case" and self.subplots_dim_by is None:
            self.subplots_dim_by = "case"

        if self.figs_dim_by != "case" and self.subplots_dim_by != "case":
            raise ValueError('Unable to determine where to plot along cases. Specify "case" in either "figs_dim_by" or "subplots_dim_by"')

        if self.subplots_dim_by == "case" and self.subplots is None:
            numSubplots = self._numCases
            if numSubplots <= 6:
                nrows = 2
            else:
                nrows = 3
            ncols = numSubplots // (nrows + 1) + 1
            self.subplots = [
                {
                    'position': [nrows, ncols, i+1],
                    'dim_means': None,
                } 
                for i in range(self._numCases)
            ]

        if not self.subplots:
            raise ValueError('unable to figure out the auto configurations for "subplots", specify it explicitly')

        if not self.figs:
            raise ValueError('unable to figure out the auto configurations for "figs", specify it explicitly')

        # convert to class objects
        self.figs = [Option_Fig(**fig) for fig in self.figs]
        self.subplots = [Option_Subplot(**subplot) for subplot in self.subplots]
        self.shadings = [Option_Shading(**shading) for shading in self.shadings]
        self.contours = [Option_Contour(**contour) for contour in self.contours]
        self.vectors = [Option_Vector(**vector) for vector in self.vectors]
        self.lines = [Option_Line(**line) for line in self.lines]

        # check dims_by is setup for dim_means to work
        if self.figs_dim_by is None:
            for fig in self.figs:
                if fig.dim_means is not None:
                    raise ValueError(f'{fig.dim_means=} is specified by "figs_dim_by" is None.')
        if self.subplots_dim_by is None:
            for subplot in self.subplots:
                if subplot.dim_means is not None:
                    raise ValueError(f'{subplot.dim_means=} is specified by "subplots_dim_by" is None.')

        # make sure axis is not repeated for x, y, subplot and fig
        for plot_set in [
            *self.shadings,
            *self.contours,
            *self.vectors,
            *self.lines,
        ]:
            pos_figs_dim_by = self.figs_dim_by
            pos_subplots_dim_by = self.subplots_dim_by
            if isinstance(pos_figs_dim_by, int):
                if pos_figs_dim_by < 0:
                    pos_figs_dim_by += len(plot_set.minMaxs)
            if isinstance(pos_subplots_dim_by, int):
                if pos_subplots_dim_by < 0:
                    pos_subplots_dim_by += len(plot_set.minMaxs)
            idims = [pos_figs_dim_by, pos_subplots_dim_by, *plot_set.xy_axis]
            idimsNoNone = [idim for idim in idims if idim is not None]
            if len(idimsNoNone) != len(list(set(idimsNoNone))):
                raise ValueError(
                    'duplicate dimensions for "figs_dim_by", "subplots_dim_by", "xy_axis:'
                    + f'{idims}'
                )


@dataclass
class Option_Fig():
    name: str = 'out.png' # file name
    title: str = None
    dim_means: list = None
    mpl_opts: dict = field(default_factory=dict) # figure options sent to matplotlib

    def __post_init__(self):
        pyt.chkt.checkType(self.name, str , 'name')
        pyt.chkt.checkType(self.title, [str, None] , 'title')
        pyt.chkt.checkType(self.mpl_opts, dict , 'mpl_opts')
        pyt.chkt.checkType(self.dim_means, [list, None], 'dim_means')

        if "layout" not in self.mpl_opts:
            self.fig_opts = {'layout': 'constrained', **self.fig_opts}

        if '.' not in self.name:
            raise ValueError('no "." extension found in fig_name')

        if self.dim_means is not None:
            if len(self.dim_means) != 2:
                raise ValueError('values in dim_means bust be 2 elements')
            for e in self.dim_means:
                pyt.chkt.checkType(e, [int, float], 'elements in dim_mean must be float/int')
            

@dataclass
class Option_Subplot():
    position: list[int] = None # [nrows, ncols, index]
    dim_means: list = None
    title: str = None
    mpl_opts: dict = field(default_factory=dict) # ax options sent to matplotlib
    
    def __post_init__(self):
        if self.position is None:
            self.position = [1, 1, 1]

        pyt.chkt.checkType(self.position, list, 'position')
        pyt.chkt.checkType(self.dim_means, [list, None], 'dim_means')

        if len(self.position) != 3:
            raise ValueError('position must contains exactly 3 elements')

        for pos in self.position[:2]:
            pyt.chkt.checkType(pos, int, 'element in posistion')
            if pos <= 0:
                raise ValueError('elements in position must be >= 1')

        pyt.chkt.checkType(self.position[-1], [int, tuple], 'element in position')

        if self.dim_means is not None:
            if len(self.dim_means) != 2:
                raise ValueError('values in dim_means bust be 2 elements')
            for e in self.dim_means:
                pyt.chkt.checkType(e, [int, float], 'elements in dim_mean must be float/int')

        # set up useful constants
        self.nrows, self.ncols, self.index = self.position
        self.irow, self.icol = divmod(self.index-1, self.ncols)


@dataclass
class _Option_Plot_Type():
    variable: str
    xy_axis: int
    minMaxs: list

    variable2: str = None

    math: callable = None
    smooths: list = None
    operators: list = None

    read_method: str = 'auto'

    obs_source: str = None
    obs_clim_yr: list = None
    total_anomaly: str = 'anomaly'

    amean: list = None # calculate and display area mean [lonw, lone, lats, latn]

    regrid_delta_x: float = 1.0 # regrid delta x
    regrid_delta_y: float = 1.0

    def __post_init__(self):
        # set defaults
        if self.obs_clim_yr is None: self.obs_clim_yr = [2001, 2020]

        # check types
        pyt.chkt.checkType(self.xy_axis, list, 'xy_axis')
        pyt.chkt.checkType(self.variable, str, 'variable')
        pyt.chkt.checkType(self.minMaxs, list, 'minMaxs')
        pyt.chkt.checkType(self.obs_source, [str, None], 'obs_source')
        pyt.chkt.checkType(self.total_anomaly, str, 'total_anomaly')
        pyt.chkt.checkType(self.obs_clim_yr, list, 'obs_clim_yr')
        pyt.chkt.checkType(self.smooths, [list, None], 'smooths')
        pyt.chkt.checkType(self.math, ['lambda', None], 'math')
        pyt.chkt.checkType(self.operators, [list, None], 'operators')
        pyt.chkt.checkType(self.amean, [list, None], 'amean')
        pyt.chkt.checkType(self.read_method, [str, None], 'read_method')
        pyt.chkt.checkType(self.variable2, [str, None], 'variable2')

        pyt.chkt.checkType(self.regrid_delta_x, [float, int], 'regrid_delta_x')
        pyt.chkt.checkType(self.regrid_delta_y, [float, int], 'regrid_delta_y')

        if self.math is not None:
            pyt.chkt.checkLambdaArgs(self.math, 'z', 'math', raiseError=True)
        if self.minMaxs is not None:
            for minMax in self.minMaxs:
                pyt.chkt.checkType(minMax, list, 'minMax in minMaxs')
                for e in minMax:
                    pyt.chkt.checkType(e, [int, float], 'min or max in minMax')
        if self.total_anomaly not in ['total', 'anomaly']:
            raise ValueError('"total_anomaly" only accepts literal "total" or "anomaly"')
        if len(self.obs_clim_yr) != 2:
            raise ValueError('"obs_clim_yr" only allow 2 integers')
        for e in self.obs_clim_yr:
            pyt.chkt.checkType(e, int, 'elements in obs_clim_yr')
        if self.smooths is not None:
            if len(self.smooths) != 2:
                raise ValueError('"smooths" only allow 2 integers/floats')

        if self.operators is None:
            self.operators = []
        else:
            operator_mapper = _operators.get_mapper()
            for operator in self.operators:
                if operator not in operator_mapper:
                    raise ValueError(f'unknown operator "{operator}". available: {list(operator_mapper.keys())}')
            self.operators = [operator_mapper[operator] for operator in self.operators]

        if self.amean is not None:
            if len(self.amean) != 4:
                raise ValueError('"amean" must contains 4 int/floats')

            for e in self.amean:
                pyt.chkt.checkType(e, [int, float], 'elements in "amean"')

        # figure out negative values of axes
        ndim = len(self.minMaxs)
        self.xy_axis = [ndim + i if i is not None and i <0 else i for i in self.xy_axis]
        if self.xy_axis[0] is not None:
            self.auto_xlim = self.minMaxs[self.xy_axis[0]]
        else:
            self.auto_xlim = None

        if self.xy_axis[1] is not None:
            self.auto_ylim = self.minMaxs[self.xy_axis[1]]
        else:
            self.auto_ylim = None

@dataclass
class Option_Line(_Option_Plot_Type):
    mpl_opts: dict = field(default_factory=dict)
    def __post_init__(self):
        super().__post_init__()
        pyt.chkt.checkType(self.mpl_opts, dict , 'mpl_opts')

        if sum((e is None for e in self.xy_axis)) != 1:
            raise ValueError(f'"xy_axis" requires exactly 1 element to be None (found {self.xy_axis})')

    

@dataclass
class Option_Shading(_Option_Plot_Type):
    levels: list = None
    colormap: str = None
    contour_opts: dict = None

    def __post_init__(self):
        super().__post_init__()
        pyt.chkt.checkType(self.contour_opts, [dict, None], 'contour_opts')


@dataclass
class Option_Contour(_Option_Plot_Type):
    mpl_opts_list: list = None

    def __post_init__(self):
        super().__post_init__()
        pyt.chkt.checkType(self.mpl_opts_list, list , 'levels')


@dataclass
class Option_Vector(_Option_Plot_Type):
    nxPerPanel: int = 15
    nyPerPanel: int = 15
    matplotlib_opts: dict = field(default_factory=dict)

    def __post_init__(self):
        super().__post_init__()
        pyt.chkt.checkType(self.nxPerPanel, int , 'nxPerPanel')
        pyt.chkt.checkType(self.nyPerPanel, int , 'nyPerPanel')
        pyt.chkt.checkType(self.matplotlib_opts, dict , 'matplotlib_opts')

