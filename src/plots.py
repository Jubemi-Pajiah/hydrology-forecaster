"""
plots.py — Figures for the synthetic-record study.

Rewritten 2026-08-25 for the Nigerian case study. The figures no longer
enumerate three variables of one American basin; they lead with the Hadejia
River at Hadejia and carry the Conecuh alongside as the contrasting climatic
regime, because the comparison between the two deseasonalising treatments is
only evidence if it is seen on more than one kind of river.

  Fig 1  : Monthly series, case study and contrast, train/validation split
  Fig 2  : ACF and PACF of each deseasonalised training series
  Fig 3  : Stochastic ensemble vs the observed validation record
  Fig 4  : Property-based validation, historical statistic vs ensemble envelope
  Fig 5  : Residual diagnostics (distribution and ACF)
  Fig 6  : Estimated AR/MA coefficients with 95% confidence intervals
  Fig 10 : The deseasonalisation comparison -- the annual cycle, what each
           treatment leaves behind, what each generates over a thousand years,
           and the design curve that follows from the one that works

Figures are written to figures/ at 300 DPI.
"""

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

plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 300,
    "font.size": 10.5,
    "axes.grid": True,
    "grid.alpha": 0.3,
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
def _panel_title(art):
    meta = art["meta"]
    return f"{meta['short_name']} — {art['variable']}"


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
def fig1_monthly_series(artifacts, path=FIG_DIR / "Fig1_DischargeTimeSeries.png"):
    """Observed monthly series, with the training/validation boundary marked."""
    panels = _panels(artifacts, "discharge")
    fig, axes = plt.subplots(len(panels), 1, figsize=(11, 3.1 * len(panels)))
    axes = np.atleast_1d(axes)
    for ax, art in zip(axes, panels):
        df, train = art["df"], art["train"]
        ax.plot(df.index, df["value"], color=_BLUE, lw=0.9)
        ax.axvline(train.index[-1], color=_RED, ls="--", lw=1.1)
        ax.set_ylabel(VARIABLE_LABELS[art["variable"]])
        ax.set_title(
            f"{art['meta']['short_name']} ({art['meta']['country']}), monthly mean "
            f"discharge {df.index[0].year}–{df.index[-1].year} — "
            f"{art['meta']['climate'].split(',')[0]}", fontsize=10.5)
        ax.text(0.012, 0.90, f"Training to {train.index[-1].date()}",
                transform=ax.transAxes, color=_RED, fontsize=8.5)
        ax.set_xlabel("Year")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig2_acf_pacf(artifacts, nlags=24, path=FIG_DIR / "Fig2_ACF_PACF.png"):
    """ACF/PACF of each deseasonalised training series — the identification
    evidence behind the selected orders."""
    panels = _panels(artifacts, "all")
    fig, axes = plt.subplots(len(panels), 2, figsize=(11, 2.5 * len(panels)))
    axes = np.atleast_2d(axes)
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
            ax.set_title(f"{_panel_title(art)}: {name} (deseasonalised)", fontsize=9.5)
            ax.set_xlabel("Lag (months)")
            ax.set_ylabel(name)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig3_ensemble_vs_historical(artifacts,
                                path=FIG_DIR / "Fig3_ForecastHydrograph.png"):
    """Synthetic ensemble spread against the observed validation record.

    The band is what the model says the river can do over that window; the
    black line is what it happened to do. The model is not asked to trace the
    black line — it is asked to contain it and to have the right shape."""
    panels = _panels(artifacts, "discharge")
    fig, axes = plt.subplots(len(panels), 1, figsize=(11, 3.1 * len(panels)))
    axes = np.atleast_1d(axes)
    for ax, art in zip(axes, panels):
        valid, ens = art["valid"], art["ens_valid"]
        lo, hi = np.percentile(ens, [5, 95], axis=0)
        med = np.median(ens, axis=0)
        ax.fill_between(valid.index, lo, hi, color=_BLUE, alpha=0.25,
                        label="Synthetic 5th–95th percentile")
        ax.plot(valid.index, med, color=_BLUE, lw=1.0, ls="--", label="Synthetic median")
        ax.plot(valid.index, valid["value"], color="k", lw=1.1, label="Observed")
        ax.set_ylabel(VARIABLE_LABELS[art["variable"]])
        ax.set_title(f"{_panel_title(art)}: ensemble vs observed, validation period",
                     fontsize=10.5)
        ax.legend(fontsize=8, loc="upper right")
    axes[-1].set_xlabel("Year")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig4_property_validation(artifacts, path=FIG_DIR / "Fig4_Scatter.png"):
    """Property-based validation, normalised to the ensemble median so that
    statistics in different units share one axis. A point inside the grey bar
    is a statistic the model reproduces."""
    panels = _panels(artifacts, "all")
    keys = [k for k in PROPERTY_KEYS if k != "seasonal_means"]
    fig, axes = plt.subplots(1, len(panels), figsize=(3.6 * len(panels), 5),
                             sharex=True)
    axes = np.atleast_1d(axes)
    for ax, art in zip(axes, panels):
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
        ax.set_yticklabels([k.replace("_", " ") for k in keys], fontsize=8.5)
        ax.set_xlabel("Historical / ensemble median")
        n_ok = art["val_summary"]["_n_properties_within_envelope"]
        n_tot = art["val_summary"]["_n_properties_total"]
        ax.set_title(f"{_panel_title(art)}\n{n_ok} of {n_tot} within envelope",
                     fontsize=9.5)
    fig.suptitle("Property-based validation: observed statistic against the synthetic "
                 "ensemble (green = within the 90% envelope)", fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(path)
    plt.close(fig)
    return path


def fig5_residual_diagnostics(artifacts,
                              path=FIG_DIR / "Fig5_ResidualDiagnostics.png"):
    """Residual distribution and autocorrelation for each fitted model."""
    panels = _panels(artifacts, "all")
    fig, axes = plt.subplots(len(panels), 2, figsize=(11, 2.5 * len(panels)))
    axes = np.atleast_2d(axes)
    for row, art in enumerate(panels):
        resid = art["model"].resid_
        ax1, ax2 = axes[row]
        ax1.hist(resid, bins=40, density=True, color=_GREEN, alpha=0.7)
        xs = np.linspace(resid.min(), resid.max(), 200)
        mu, sd = resid.mean(), resid.std()
        ax1.plot(xs, np.exp(-0.5 * ((xs - mu) / sd) ** 2) / (sd * np.sqrt(2 * np.pi)),
                 color=_RED, lw=1.5, label="Normal")
        ax1.set_title(f"{_panel_title(art)}: residual distribution", fontsize=9.5)
        ax1.set_xlabel("Residual")
        ax1.legend(fontsize=8)

        nlags = 24
        a = acf(resid, nlags)
        ci = conf_interval(len(resid))
        ax2.bar(np.arange(nlags + 1), a, width=0.3, color=_BLUE)
        ax2.axhline(ci, color=_RED, ls="--", lw=1)
        ax2.axhline(-ci, color=_RED, ls="--", lw=1)
        ax2.axhline(0, color="k", lw=0.8)
        ax2.set_title(f"{_panel_title(art)}: residual ACF", fontsize=9.5)
        ax2.set_xlabel("Lag (months)")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig6_parameter_estimates(artifacts, path=FIG_DIR / "Fig6_SkillVsLead.png"):
    """AR/MA coefficient estimates with 95% confidence intervals."""
    z = _stats.norm.ppf(0.975)
    panels = _panels(artifacts, "all")
    fig, axes = plt.subplots(1, len(panels), figsize=(3.6 * len(panels), 4.8))
    axes = np.atleast_1d(axes)
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
        ax.set_yticklabels(labels, fontsize=11)
        ax.set_xlabel("Coefficient value")
        ax.set_title(f"{_panel_title(art)}\n{model.label()}", fontsize=9.5)
        ax.invert_yaxis()
    fig.suptitle("Estimated AR/MA coefficients, 95% confidence intervals "
                 "(blue = excludes zero)", fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# the comparison figure
# ---------------------------------------------------------------------------
def fig10_method_comparison(artifacts, results,
                            path=FIG_DIR / "Fig10_MethodComparison.png"):
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

    fig, axes = plt.subplots(2, 2, figsize=(12.5, 9))
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
    ax.set_title(f"(a) The annual cycle, {primary['meta']['short_name']}\n"
                 f"mean cycle carries "
                 f"{cmp_primary['untreated']['seasonal_strength']:.0%} of the variance; "
                 f"monthly spread varies {sds.max() / sds.min():.1f}-fold", fontsize=10)
    ax.legend(fontsize=8.5, loc="upper left")

    # (b) leftover seasonal spread ----------------------------------------
    ax = axes[0, 1]
    styles = [(cmp_primary, primary["meta"]["short_name"], "-", _BLUE),
              (cmp_contrast, contrast["meta"]["short_name"], "--", _ORANGE)]
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
    ax.set_title("(b) Seasonal structure left in the variance\n"
                 "flat = none left; sloping = the constant-variance "
                 "assumption is still violated", fontsize=10)
    ax.legend(fontsize=7.5, loc="upper right")

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
    ax.set_title("(c) A 1,000-year synthetic record from each treatment\n"
                 f"standardisation drift ratio "
                 f"{cmp_primary['standardisation']['drift_ratio']:.2f}; "
                 f"differencing "
                 f"{cmp_primary['seasonal_differencing']['drift_ratio_scientific']}",
                 fontsize=10)
    ax.legend(fontsize=8, loc="upper left")

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
    ax.set_title("(d) Design discharge by return period\n"
                 "read off 50,000 synthetic years, checked against "
                 f"{n} observed ones", fontsize=10)
    ax.legend(fontsize=8.5, loc="upper left")

    fig.tight_layout()
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
