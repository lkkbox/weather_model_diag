### module options ###
mjo
    do_data: bool = True # calculate data
    do_plot: bool = True # draw plots only
    score_diagram: dict = {
        xlim: list = None,
        ylim_rmse: list = None,
        ylim_acc: list = None,
        xticks: list = None,
        yticks: list = None,
        do_rmse: bool = True,
        do_acc: bool = True,
    }
    phase_diagram: dict = {
        lead_means: list[slice],
        init_means: list[slice],
    }


TODO
- calculate bias correction base
- draw lon time diagram...
- draw maps...
- rmm index

