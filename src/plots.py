"""
plots.py — Figures for the synthetic-record study.

The figures lead with the Hadejia River at Hadejia and carry the Conecuh
alongside as the contrasting climatic regime, because the comparison between
the two deseasonalising treatments is only evidence if it is seen on more than
one kind of river.

  fig1_monthly_series        -> discharge_time_series.png   monthly series, both basins, with
                                            the train/validation boundary
  fig2_acf_pacf              -> acf_pacf.png  ACF and PACF of each deseasonalised
                                            training series
  fig3_ensemble_vs_historical-> ensemble_vs_observed.png  stochastic ensemble against the
                                            observed validation record
  fig4_property_validation   -> property_validation.png  historical statistic against the
                                            ensemble envelope
  fig5_residual_diagnostics  -> residual_diagnostics.png  residual distribution and ACF
  fig6_parameter_estimates   -> parameter_estimates.png  AR/MA coefficients, 95% intervals
  fig10_method_comparison    -> method_comparison.png  the deseasonalisation comparison:
                                            the annual cycle, what each
                                            treatment leaves behind, what each
                                            generates over a thousand years,
                                            and the design curve that follows
                                            from the one that works

Figures are written to figures/ at 300 DPI.
"""

import textwrap
from pathlib import Path

import numpy as np
from scipy import stats as _stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .model import acf, pacf, conf_interval, seasonal_difference
from .preprocess import seasonal_profile, deseasonalise
from .validation import PROPERTY_KEYS

FIG_DIR = Path(__file__).resolve().parent.parent / "figures"
FIG_DIR.mkdir(exist_ok=True)

# Figures are drawn larger than they are placed, so the type is set larger
# than it needs to look: at the 0.76 reduction a portrait figure undergoes,
# 13 pt drawn arrives on the page at about 10 pt, a comfortable
# reading size.  Before this the labels arrived at about 5 pt.
FIG_WIDTH_IN = 8.0        # drawn width of a portrait figure
_H = 0.73                 # matching height factor, so aspect is preserved

plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 300,
    "font.size": 13,
    "axes.titlesize": 13,
    "axes.labelsize": 13,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 11.5,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "figure.constrained_layout.use": False,
})

_BLUE = "#1f77b4"
_RED = "#d62728"
_GREEN = "#2ca02c"
_GRAY = "#7f7f7f"
_ORANGE = "#ff7f0e"
_PURPLE = "#7b3fa0"

VARIABLE_LABELS = {
    "discharge": "Discharge (m$^3$/s)",
    "rainfall": "Rainfall (mm/month)",
    "stage": "Stage (m)",
}


# ---------------------------------------------------------------------------
# panels
# ---------------------------------------------------------------------------
def _river(meta):
    """The river's name on its own — 'Hadejia River at Hadejia' → 'Hadejia'.

    Panel titles in a two- or four-column grid have about 2.5 in of drawn
    width to work in; the full gauge name needs 3.5 in at this type
    size and so collides with its neighbour.  The gauge is identified in full
    in the captions, so the panels carry the river alone.
    """
    return meta["short_name"].split(" River")[0]


def _panel_title(art):
    return f"{_river(art['meta'])} — {art['variable']}"


# ---------------------------------------------------------------------------
# titles that stay inside their own axes
# ---------------------------------------------------------------------------
# matplotlib centres an axes title on its axes and reserves HEIGHT for it but
# never WIDTH: tight_layout() will not widen a margin or shrink an axes to stop
# a long title running into the next column.  Before this the titles of Figures
# 4.1-4.5 and 4.7 overlapped in the gutter and were clipped at the canvas edge.
# _fit_title measures the drawn text against the axes it belongs to, wraps it,
# and only then — if a single word still will not fit — steps the type down.
def _text_width_in(fig, text, size):
    """Width of ``text`` in inches, as it would be drawn."""
    t = fig.text(0, 0, text, fontsize=size)
    try:
        w = t.get_window_extent(fig.canvas.get_renderer()).width / fig.dpi
    finally:
        t.remove()
    return w


def _fit_title(ax, text, size, min_size=10.0, pad=0.98):
    """Set ``text`` as ``ax``'s title, wrapped (then shrunk) so it fits.

    ``min_size`` is the floor: at the 0.76 reduction a portrait figure
    undergoes, 10 pt drawn arrives on the page at about 8 pt, the smallest
    that stays legible.
    """
    fig = ax.figure
    avail = ax.get_position().width * fig.get_figwidth() * pad
    while True:
        lines = []
        for line in text.split("\n"):
            w = _text_width_in(fig, line, size)
            if w <= avail or not line.strip():
                lines.append(line)
                continue
            budget = max(8, int(len(line) * avail / w))
            lines.extend(textwrap.wrap(line, budget) or [line])
        widest = max((_text_width_in(fig, ln, size) for ln in lines), default=0.0)
        if widest <= avail or size <= min_size:
            break
        size = max(min_size, size - 0.5)
    ax.set_title("\n".join(lines), fontsize=size)


def _fit_suptitle(fig, text, size, pad=0.96):
    """A figure title wrapped to the canvas — suptitles clip the same way."""
    avail = fig.get_figwidth() * pad
    w = _text_width_in(fig, text, size)
    if w > avail:
        text = textwrap.fill(text, max(12, int(len(text) * avail / w)))
    fig.suptitle(text, fontsize=size)


def _headroom(ax, fraction, log=False):
    """Extend the top of the y axis so a legend has somewhere to sit.

    Legends placed over the data are the other half of the overlap problem;
    giving the axes a band of empty space is preferable to moving the legend
    somewhere it hides a different line.
    """
    lo, hi = ax.get_ylim()
    if log:                      # ``fraction`` is read as decades to add
        ax.set_ylim(lo, hi * 10 ** fraction)
    else:
        ax.set_ylim(lo, hi + fraction * (hi - lo))


def _layout(fig, jobs, rect=None):
    """Lay the figure out, fit every title to its axes, then lay it out again.

    Two passes are needed: the first gives each axes its final width, which is
    what a title has to fit into; the second makes room for the extra lines
    wrapping may have added.
    """
    def tl():
        fig.tight_layout(rect=rect) if rect else fig.tight_layout()

    tl()
    for ax, text, size in jobs:
        _fit_title(ax, text, size)
    tl()


def _panels(artifacts, which="all"):
    """
    Flatten the nested artifacts into an ordered list of panels.

    ``which='discharge'`` keeps only the discharge series of both basins, the
    pairing the deseasonalisation comparison is made on; ``'all'`` adds the
    contrast basin's rainfall and stage, which exist to show the procedure
    does not care what the series measures.
    """
    out = []
    for group in ("primary", "contrast"):
        for v, art in artifacts.get(group, {}).items():
            if which == "discharge" and v != "discharge":
                continue
            out.append(art)
    return out


# ---------------------------------------------------------------------------
def fig1_monthly_series(artifacts, path=FIG_DIR / "discharge_time_series.png"):
    """Observed monthly series, with the training/validation boundary marked."""
    panels = _panels(artifacts, "discharge")
    fig, axes = plt.subplots(len(panels), 1, figsize=(FIG_WIDTH_IN, 3.1 * _H * len(panels)))
    axes = np.atleast_1d(axes)
    jobs = []
    for ax, art in zip(axes, panels):
        df, train = art["df"], art["train"]
        ax.plot(df.index, df["value"], color=_BLUE, lw=0.9)
        ax.axvline(train.index[-1], color=_RED, ls="--", lw=1.1)
        ax.set_ylabel(VARIABLE_LABELS[art["variable"]])
        jobs.append((
            ax,
            f"{art['meta']['short_name']} — monthly mean discharge "
            f"{df.index[0].year}–{df.index[-1].year}\n"
            f"{art['meta']['country']}; {art['meta']['climate'].split(',')[0]}",
            14.2))
        ax.text(0.012, 0.90, f"Training to {train.index[-1].date()}",
                transform=ax.transAxes, color=_RED, fontsize=11.5)
        ax.set_xlabel("Year")
    _layout(fig, jobs)
    fig.savefig(path)
    plt.close(fig)
    return path


def fig2_acf_pacf(artifacts, nlags=24, path=FIG_DIR / "acf_pacf.png"):
    """ACF/PACF of each deseasonalised training series — the identification
    evidence behind the selected orders."""
    panels = _panels(artifacts, "all")
    fig, axes = plt.subplots(len(panels), 2, figsize=(FIG_WIDTH_IN, 2.78 * _H * len(panels)))
    axes = np.atleast_2d(axes)
    jobs = []
    for row, art in enumerate(panels):
        w = art["w_train"]
        a, p = acf(w, nlags), pacf(w, nlags)
        ci = conf_interval(len(w))
        lags = np.arange(nlags + 1)
        ax1, ax2 = axes[row]
        for ax, series, color, name in ((ax1, a, _BLUE, "ACF"), (ax2, p, _GREEN, "PACF")):
            ax.bar(lags, series, width=0.3, color=color)
            ax.axhline(0, color="k", lw=0.8)
            ax.axhline(ci, color=_RED, ls="--", lw=1)
            ax.axhline(-ci, color=_RED, ls="--", lw=1)
            jobs.append((ax, f"{_panel_title(art)}\n{name}, deseasonalised", 12.8))
            ax.set_xlabel("Lag (months)")
            ax.set_ylabel(name)
    _layout(fig, jobs)
    fig.savefig(path)
    plt.close(fig)
    return path


def fig3_ensemble_vs_historical(artifacts,
                                path=FIG_DIR / "ensemble_vs_observed.png"):
    """Synthetic ensemble spread against the observed validation record.

    The band is what the model says the river can do over that window; the
    black line is what it happened to do. The model is not asked to trace the
    black line — it is asked to contain it and to have the right shape."""
    panels = _panels(artifacts, "discharge")
    fig, axes = plt.subplots(len(panels), 1, figsize=(FIG_WIDTH_IN, 3.1 * _H * len(panels)))
    axes = np.atleast_1d(axes)
    jobs = []
    for ax, art in zip(axes, panels):
        valid, ens = art["valid"], art["ens_valid"]
        lo, hi = np.percentile(ens, [5, 95], axis=0)
        med = np.median(ens, axis=0)
        ax.fill_between(valid.index, lo, hi, color=_BLUE, alpha=0.25,
                        label="Synthetic 5th–95th percentile")
        ax.plot(valid.index, med, color=_BLUE, lw=1.0, ls="--", label="Synthetic median")
        ax.plot(valid.index, valid["value"], color="k", lw=1.1, label="Observed")
        ax.set_ylabel(VARIABLE_LABELS[art["variable"]])
        jobs.append((ax, f"{_panel_title(art)}: ensemble vs observed, "
                         f"validation period", 14.2))
        _headroom(ax, 0.30)      # keep the legend off the ensemble band
        ax.legend(fontsize=10.8, loc="upper right", framealpha=0.92)
    axes[-1].set_xlabel("Year")
    _layout(fig, jobs)
    fig.savefig(path)
    plt.close(fig)
    return path


def fig4_property_validation(artifacts, path=FIG_DIR / "property_validation.png"):
    """Property-based validation, normalised to the ensemble median so that
    statistics in different units share one axis. A point inside the grey bar
    is a statistic the model reproduces."""
    panels = _panels(artifacts, "all")
    keys = [k for k in PROPERTY_KEYS if k != "seasonal_means"]
    # A 2 x 2 grid, not a 1 x 4 strip.  Four panels side by side made the
    # figure 13.6 in wide, which the 15.5 cm text column then reduced by 0.45
    # — the labels arrived on the page at about 6 pt, too small to read, and each axes was left too narrow for its own title.
    nrow = 2 if len(panels) > 2 else 1
    ncol = int(np.ceil(len(panels) / nrow))
    fig, axes = plt.subplots(nrow, ncol, figsize=(FIG_WIDTH_IN, 3.0 * nrow),
                             sharex=True)
    axes = np.atleast_1d(axes).ravel()
    for spare in axes[len(panels):]:
        spare.set_visible(False)
    jobs = []
    for i, (ax, art) in enumerate(zip(axes, panels)):
        summary = art["val_summary"]
        ys = np.arange(len(keys))
        for y, key in zip(ys, keys):
            s = summary.get(key)
            if s is None:
                continue
            med = s["ensemble_median"] if s["ensemble_median"] != 0 else 1e-9
            ax.plot([s["ensemble_p5"] / med, s["ensemble_p95"] / med], [y, y],
                    color=_GRAY, lw=4, alpha=0.4, solid_capstyle="round")
            ax.scatter([s["historical"] / med], [y], s=45, zorder=5,
                       color=_GREEN if s["within_90pct_envelope"] else _RED)
        ax.axvline(1.0, color="k", ls="--", lw=0.8)
        ax.set_yticks(ys)
        # The seven properties are the same in every panel, so they are named
        # once down the left-hand column; that returns about 1.6 in of width
        # per row to the plots and to their titles.
        ax.set_yticklabels([k.replace("_", " ") for k in keys] if i % ncol == 0
                           else [], fontsize=11.5)
        n_ok = art["val_summary"]["_n_properties_within_envelope"]
        n_tot = art["val_summary"]["_n_properties_total"]
        jobs.append((ax, f"{_panel_title(art)}\n{n_ok} of {n_tot} within envelope",
                     12.8))
    # One shared x label: the per-panel label was wider than its own axes and
    # ran off the right-hand edge of the canvas.
    fig.supxlabel("Historical / ensemble median", fontsize=13)
    _fit_suptitle(fig, "Property-based validation: observed statistic against the "
                       "synthetic ensemble (green = within the 90% envelope)", 13.5)
    _layout(fig, jobs)
    fig.savefig(path)
    plt.close(fig)
    return path


def fig5_residual_diagnostics(artifacts,
                              path=FIG_DIR / "residual_diagnostics.png"):
    """Residual distribution and autocorrelation for each fitted model."""
    panels = _panels(artifacts, "all")
    fig, axes = plt.subplots(len(panels), 2, figsize=(FIG_WIDTH_IN, 2.78 * _H * len(panels)))
    axes = np.atleast_2d(axes)
    jobs = []
    for row, art in enumerate(panels):
        resid = art["model"].resid_
        ax1, ax2 = axes[row]
        ax1.hist(resid, bins=40, density=True, color=_GREEN, alpha=0.7)
        xs = np.linspace(resid.min(), resid.max(), 200)
        mu, sd = resid.mean(), resid.std()
        ax1.plot(xs, np.exp(-0.5 * ((xs - mu) / sd) ** 2) / (sd * np.sqrt(2 * np.pi)),
                 color=_RED, lw=1.5, label="Normal")
        jobs.append((ax1, f"{_panel_title(art)}\nResidual distribution", 12.8))
        ax1.set_xlabel("Residual")
        ax1.legend(fontsize=10.8)

        nlags = 24
        a = acf(resid, nlags)
        ci = conf_interval(len(resid))
        ax2.bar(np.arange(nlags + 1), a, width=0.3, color=_BLUE)
        ax2.axhline(ci, color=_RED, ls="--", lw=1)
        ax2.axhline(-ci, color=_RED, ls="--", lw=1)
        ax2.axhline(0, color="k", lw=0.8)
        jobs.append((ax2, f"{_panel_title(art)}\nResidual ACF", 12.8))
        ax2.set_xlabel("Lag (months)")
    _layout(fig, jobs)
    fig.savefig(path)
    plt.close(fig)
    return path


def fig6_parameter_estimates(artifacts, path=FIG_DIR / "parameter_estimates.png"):
    """AR/MA coefficient estimates with 95% confidence intervals."""
    z = _stats.norm.ppf(0.975)
    panels = _panels(artifacts, "all")
    nrow = 2 if len(panels) > 2 else 1          # see fig4 — a strip is reduced
    ncol = int(np.ceil(len(panels) / nrow))     # too far by the text column
    fig, axes = plt.subplots(nrow, ncol, figsize=(FIG_WIDTH_IN, 3.0 * nrow))
    axes = np.atleast_1d(axes).ravel()
    for spare in axes[len(panels):]:
        spare.set_visible(False)
    jobs = []
    for ax, art in zip(axes, panels):
        model = art["model"]
        se = model.standard_errors()
        labels, vals, errs = [], [], []
        for i, ph in enumerate(model.phi):
            labels.append(f"$\\phi_{{{i + 1}}}$")
            vals.append(ph)
            e = se["phi"][i]
            errs.append(z * e if e is not None and np.isfinite(e) else 0.0)
        for i, th in enumerate(model.theta):
            labels.append(f"$\\theta_{{{i + 1}}}$")
            vals.append(th)
            e = se["theta"][i]
            errs.append(z * e if e is not None and np.isfinite(e) else 0.0)
        ys = np.arange(len(labels))
        for val, err, y in zip(vals, errs, ys):
            ax.errorbar([val], [y], xerr=[err], fmt="o", color="k",
                        ecolor=_BLUE if abs(val) > err else _GRAY,
                        elinewidth=2.5, capsize=4, markersize=5)
        ax.axvline(0, color="k", lw=0.8, ls=":")
        ax.set_yticks(ys)
        ax.set_yticklabels(labels, fontsize=14.9)
        jobs.append((ax, f"{_panel_title(art)}\n{model.label()}", 12.8))
        ax.invert_yaxis()
    fig.supxlabel("Coefficient value", fontsize=13)
    _fit_suptitle(fig, "Estimated AR/MA coefficients, 95% confidence intervals "
                       "(blue = excludes zero)", 13.5)
    _layout(fig, jobs)
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# the comparison figure
# ---------------------------------------------------------------------------
def fig10_method_comparison(artifacts, results,
                            path=FIG_DIR / "method_comparison.png"):
    """
    The four panels the study's contribution rests on.

    (a) The annual cycle of the Nigerian river on the log scale: twelve
        monthly means, and the twelve monthly standard deviations around them.
        The mean cycle is the part both treatments remove; the unequal spread
        is the part only one of them does.
    (b) What each treatment leaves behind, month by month, on both rivers.
        A flat line is a series with no seasonal structure left in its
        variance.
    (c) The decade-by-decade mean of a thousand-year synthetic record from each
        treatment, on a logarithmic axis. One stays on the river's scale; the
        other walks off it.
    (d) The design curve that follows from the treatment that works, with the
        observed annual maxima marked for comparison.
    """
    primary = artifacts["primary"]["discharge"]
    contrast = artifacts["contrast"]["discharge"]
    cmp_primary = results["method_comparison"][primary["basin"]]
    cmp_contrast = results["method_comparison"][contrast["basin"]]

    # Drawn wider than the old 12.5 x 9: this figure is placed landscape at
    # 26 cm, where 12.5 x 9 came to 18.7 cm tall and overran the text block,
    # and its two-line panel titles needed more width than a 6.25 in column.
    fig, axes = plt.subplots(2, 2, figsize=(14.0, 8.8))
    jobs = []
    months = np.arange(1, 13)
    month_names = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]

    # (a) the annual cycle -------------------------------------------------
    ax = axes[0, 0]
    df = primary["df"]
    prof = seasonal_profile(df["log_value"].to_numpy(), df.index.month.to_numpy())
    means = np.array(prof["means"])
    sds = np.array(prof["sds"])
    ax.plot(months, means, "o-", color=_BLUE, lw=2, label="Monthly mean, log flow")
    ax.fill_between(months, means - sds, means + sds, color=_BLUE, alpha=0.20,
                    label="± one monthly standard deviation")
    ax.set_xticks(months)
    ax.set_xticklabels(month_names)
    ax.set_ylabel("ln(discharge + c)")
    jobs.append((ax, f"(a) The annual cycle, {primary['meta']['short_name']}\n"
                     f"cycle = "
                     f"{cmp_primary['untreated']['seasonal_strength']:.0%} of the "
                     f"variance; spread varies "
                     f"{sds.max() / sds.min():.1f}-fold", 13.5))
    _headroom(ax, 0.30)
    ax.legend(fontsize=11.5, loc="upper left", framealpha=0.92)

    # (b) leftover seasonal spread ----------------------------------------
    ax = axes[0, 1]
    styles = [(cmp_primary, _river(primary["meta"]), "-", _BLUE),
              (cmp_contrast, _river(contrast["meta"]), "--", _ORANGE)]
    for cmp_, name, ls, colour in styles:
        ax.plot(months, cmp_["seasonal_differencing"]["monthly_sd_spread"]["by_month"],
                ls, color=colour, marker="s", ms=4, lw=1.8,
                label=f"{name}: differencing at lag 12")
        ax.plot(months, cmp_["standardisation"]["monthly_sd_spread"]["by_month"],
                ls, color=colour, marker="o", ms=4, lw=1.8, alpha=0.45,
                label=f"{name}: standardisation")
    ax.set_xticks(months)
    ax.set_xticklabels(month_names)
    ax.set_ylabel("Standard deviation of the transformed series")
    jobs.append((ax, "(b) Seasonal structure left in the variance\n"
                     "flat = none left; sloping = constant variance violated",
                 13.5))
    # Four entries at 'upper right' sat on top of the Conecuh differenced
    # curve at its August peak; the legend now has its own band above the data.
    _headroom(ax, 0.72)
    ax.legend(fontsize=10.1, loc="upper center", ncol=2, framealpha=0.92)

    # (c) what a thousand-year record does --------------------------------
    ax = axes[1, 0]
    std_traj = np.array(cmp_primary["standardisation"]["decade_mean_trajectory"])
    dif_traj = np.array(cmp_primary["seasonal_differencing"]["decade_mean_trajectory"])
    span = np.linspace(0, cmp_primary["record_years_generated"], len(std_traj))
    ax.plot(span, np.maximum(std_traj, 1e-3), color=_GREEN, lw=1.4,
            label="Standardisation: mean of the generated record")
    ax.plot(span, np.maximum(dif_traj, 1e-3), color=_RED, lw=1.8, ls=":",
            label="Differencing at lag 12: same, same model family")
    observed_mean = cmp_primary["observed_mean"]
    ax.axhline(observed_mean, color="k", ls="--", lw=1.2,
               label=f"Observed mean, {observed_mean:.1f} m$^3$/s")
    ax.set_yscale("log")
    ax.set_xlabel("Year of the generated record")
    ax.set_ylabel("Mean discharge (m$^3$/s, log axis)")
    jobs.append((ax, "(c) A 1,000-year record from each treatment\n"
                     f"standardisation drift ratio "
                     f"{cmp_primary['standardisation']['drift_ratio']:.2f}; "
                     f"differencing "
                     f"{cmp_primary['seasonal_differencing']['drift_ratio_scientific']}",
                 13.5))
    # The differenced trace climbs into the top-left corner, so the legend is
    # given decades of its own above it rather than being laid over the line.
    _headroom(ax, 4.0, log=True)   # four decades
    ax.legend(fontsize=10.8, loc="upper left", framealpha=0.92)

    # (d) the design curve --------------------------------------------------
    ax = axes[1, 1]
    design = results["variables"]["discharge"]["synthetic_record"]
    rp = design["return_period_discharge"]
    Ts = sorted(int(t) for t in rp)
    qs = [rp[str(t)] for t in Ts]
    ax.plot(Ts, qs, "o-", color=_PURPLE, lw=2, label="Generated design discharge")
    obs = df["value"]
    # Complete calendar years only: a partial year at either end of the record
    # yields an annual maximum that is not comparable with the others.
    by_year = obs.groupby(obs.index.year)
    annual_max = by_year.max()[by_year.size() == 12].sort_values().to_numpy()
    n = len(annual_max)
    plotting_T = (n + 1) / (n - np.arange(n))          # Weibull plotting position
    ax.scatter(plotting_T, annual_max, color="k", s=28, zorder=5,
               label=f"Observed annual maxima ({n} years, Weibull)")
    ax.set_xscale("log")
    ax.set_xlabel("Return period (years, log axis)")
    ax.set_ylabel("Discharge (m$^3$/s)")
    jobs.append((ax, "(d) Design discharge by return period\n"
                     f"50,000 synthetic years, checked against {n} observed",
                 13.5))
    _headroom(ax, 0.12)
    ax.legend(fontsize=11.5, loc="upper left", framealpha=0.92)

    _layout(fig, jobs)
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
def build_figures(artifacts, results):
    """Build every figure and return the paths written."""
    return [
        fig1_monthly_series(artifacts),
        fig2_acf_pacf(artifacts),
        fig3_ensemble_vs_historical(artifacts),
        fig4_property_validation(artifacts),
        fig5_residual_diagnostics(artifacts),
        fig6_parameter_estimates(artifacts),
        fig10_method_comparison(artifacts, results),
    ]
