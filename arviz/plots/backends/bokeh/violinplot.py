"""Bokeh Violinplot."""
import numpy as np
from bokeh.models.annotations import Title

from ....stats import hdi
from ....stats.density_utils import get_bins, histogram, kde
from ...plot_utils import _scale_fig_size, make_label
from .. import show_layout
from . import backend_kwarg_defaults, create_axes_grid


def plot_violin(
    ax,
    plotters,
    figsize,
    rows,
    cols,
    sharex,
    sharey,
    shade_kwargs,
    shade,
    rug,
    rug_kwargs,
    bw,
    textsize,
    circular,
    hdi_prob,
    quartiles,
    backend_kwargs,
    show,
):
    """Bokeh violin plot."""
    if backend_kwargs is None:
        backend_kwargs = {}

    backend_kwargs = {
        **backend_kwarg_defaults(
            ("dpi", "plot.bokeh.figure.dpi"),
        ),
        **backend_kwargs,
    }
    (figsize, *_, linewidth, _) = _scale_fig_size(figsize, textsize, rows, cols)

    shade_kwargs = {} if shade_kwargs is None else shade_kwargs
    rug_kwargs = {} if rug_kwargs is None else rug_kwargs
    rug_kwargs.setdefault("fill_alpha", 0.1)
    rug_kwargs.setdefault("line_alpha", 0.1)
    if ax is None:
        ax = create_axes_grid(
            len(plotters),
            rows,
            cols,
            sharex=sharex,
            sharey=sharey,
            figsize=figsize,
            backend_kwargs=backend_kwargs,
        )
    else:
        ax = np.atleast_2d(ax)

    for (var_name, selection, x), ax_ in zip(
        plotters, (item for item in ax.flatten() if item is not None)
    ):
        val = x.flatten()
        if val[0].dtype.kind == "i":
            dens = cat_hist(val, rug, shade, ax_, **shade_kwargs)
        else:
            dens = _violinplot(val, rug, shade, bw, circular, ax_, **shade_kwargs)

        if rug:
            rug_x = -np.abs(np.random.normal(scale=max(dens) / 3.5, size=len(val)))
            ax_.scatter(rug_x, val, **rug_kwargs)

        per = np.nanpercentile(val, [25, 75, 50])
	hdi_probs = hdi(val, hdi_prob, multimodal=False, skipna=True)
	
        if quartiles:
            ax_.line(
                [0, 0], per[:2], line_width=linewidth * 3, line_color="black", line_cap="round"
            )
        ax_.line([0, 0], hdi_probs, line_width=linewidth, line_color="black", line_cap="round")
        ax_.circle(
            0,
            per[-1],
            line_color="white",
            fill_color="white",
            size=linewidth * 1.5,
            line_width=linewidth,
        )

        _title = Title()
        _title.text = make_label(var_name, selection)
        ax_.title = _title
        ax_.xaxis.major_tick_line_color = None
        ax_.xaxis.minor_tick_line_color = None
        ax_.xaxis.major_label_text_font_size = "0pt"

    show_layout(ax, show)

    return ax


def _violinplot(val, rug, shade, bw, circular, ax, **shade_kwargs):
    """Auxiliary function to plot violinplots."""
    if bw == "default":
        if circular:
            bw = "taylor"
        else:
            bw = "experimental"
    x, density = kde(val, circular=circular, bw=bw)

    if not rug:
        x = np.concatenate([x, x[::-1]])
        density = np.concatenate([-density, density[::-1]])

    ax.harea(y=x, x1=density, x2=np.zeros_like(density), fill_alpha=shade, **shade_kwargs)

    return density


def cat_hist(val, rug, shade, ax, **shade_kwargs):
    """Auxiliary function to plot discrete-violinplots."""
    bins = get_bins(val)
    _, binned_d, _ = histogram(val, bins=bins)

    bin_edges = np.linspace(np.min(val), np.max(val), len(bins))
    heights = np.diff(bin_edges)
    centers = bin_edges[:-1] + heights.mean() / 2
    right = 0.5 * binned_d

    if rug:
        left = 0
    else:
        left = -right

    ax.hbar(
        y=centers,
        left=left,
        right=right,
        height=heights,
        fill_alpha=shade,
        line_alpha=shade,
        line_color=None,
        **shade_kwargs
    )

    return binned_d
