"""
plots.py — Figures for the statistical hydrological-forecasting study.

Rewritten 2026-08-12 for the monthly, three-variable (discharge, rainfall,
stage), stochastic-validation pipeline (see run_pipeline.py). All figures are
derived from the observed monthly series and the three independently fitted
ARIMA models; none depends on cross-variable input. Figures are written to
figures/ at 300 DPI.

  Fig 1 : Monthly time series, all three variables, train/validation split
  Fig 2 : ACF and PACF of each variable's (differenced) training series
  Fig 3 : Stochastic ensemble vs the historical validation record
  Fig 4 : Property-based validation -- historical value vs. synthetic
          ensemble envelope, normalised to the ensemble median
  Fig 5 : Residual diagnostics (histogram and ACF) per variable
  Fig 6 : Estimated AR/MA coefficients with 95% confidence intervals
          ("how do you estimate the parameters" -- shown, not just claimed)
"""

from pathlib import Path

import numpy as np
from scipy import stats as _stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .model import acf, pacf, conf_interval
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

VARIABLE_LABELS = {
    "discharge": "Discharge (m$^3$/s)",
    "rainfall": "Rainfall (mm/month)",
    "stage": "Stage (m)",
}
VARIABLES_ORDER = ["discharge", "rainfall", "stage"]


def fig1_monthly_series(artifacts, path=FIG_DIR / "Fig1_DischargeTimeSeries.png"):
    """Monthly series for all three variables, train/validation split marked."""
    fig, axes = plt.subplots(3, 1, figsize=(11, 8.5), sharex=True)
    for ax, v in zip(axes, VARIABLES_ORDER):
        df = artifacts[v]["df"]
        train_end = artifacts[v]["train"].index[-1]
        ax.plot(df.index, df["value"], color=_BLUE, lw=0.9)
        ax.axvline(train_end, color=_RED, ls="--", lw=1.1)
        ax.set_ylabel(VARIABLE_LABELS[v])
        ax.set_title(f"{v.capitalize()}, monthly, USGS 02371500 (1980-2014)", fontsize=10.5)
    axes[0].text(0.02, 0.92, "Training 1980-2003", transform=axes[0].transAxes,
                 color=_RED, fontsize=9)
    axes[0].text(0.75, 0.92, "Validation 2004-2014", transform=axes[0].transAxes,
                 color=_RED, fontsize=9)
    axes[-1].set_xlabel("Year")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig2_acf_pacf(artifacts, nlags=24, path=FIG_DIR / "Fig2_ACF_PACF.png"):
    """ACF/PACF of each variable's (differenced) training series -- model
    identification evidence, one row per variable."""
    fig, axes = plt.subplots(3, 2, figsize=(11, 9.5))
    for row, v in enumerate(VARIABLES_ORDER):
        w = artifacts[v]["w_train"]
        a = acf(w, nlags)
        p = pacf(w, nlags)
        ci = conf_interval(len(w))
        lags = np.arange(nlags + 1)

        ax1, ax2 = axes[row]
        ax1.bar(lags, a, width=0.3, color=_BLUE)
        ax1.axhline(0, color="k", lw=0.8)
        ax1.axhline(ci, color=_RED, ls="--", lw=1)
        ax1.axhline(-ci, color=_RED, ls="--", lw=1)
        ax1.set_title(f"{v.capitalize()}: ACF (d={artifacts[v]['d']})", fontsize=10)
        ax1.set_xlabel("Lag (months)"); ax1.set_ylabel("ACF")

        ax2.bar(lags, p, width=0.3, color=_GREEN)
        ax2.axhline(0, color="k", lw=0.8)
        ax2.axhline(ci, color=_RED, ls="--", lw=1)
        ax2.axhline(-ci, color=_RED, ls="--", lw=1)
        ax2.set_title(f"{v.capitalize()}: PACF", fontsize=10)
        ax2.set_xlabel("Lag (months)"); ax2.set_ylabel("PACF")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig3_ensemble_vs_historical(artifacts, path=FIG_DIR / "Fig3_ForecastHydrograph.png"):
    """Stochastic ensemble spread (5th-95th percentile band + median) against
    the actual historical validation-period record, per variable."""
    fig, axes = plt.subplots(3, 1, figsize=(11, 8.5), sharex=False)
    for ax, v in zip(axes, VARIABLES_ORDER):
        valid = artifacts[v]["valid"]
        ens = artifacts[v]["ens_valid"]
        dates = valid.index
        lo, hi = np.percentile(ens, [5, 95], axis=0)
        med = np.median(ens, axis=0)
        ax.fill_between(dates, lo, hi, color=_BLUE, alpha=0.25, label="Synthetic 5th-95th pct")
        ax.plot(dates, med, color=_BLUE, lw=1.0, ls="--", label="Synthetic median")
        ax.plot(dates, valid["value"], color="k", lw=1.1, label="Observed")
        ax.set_ylabel(VARIABLE_LABELS[v])
        ax.set_title(f"{v.capitalize()}: synthetic ensemble vs. observed, validation period",
                     fontsize=10.5)
        if v == "discharge":
            ax.legend(fontsize=8, loc="upper right")
    axes[-1].set_xlabel("Year")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig4_property_validation(artifacts, path=FIG_DIR / "Fig4_Scatter.png"):
    """Property-based validation: historical value vs. synthetic ensemble
    envelope, normalised to the ensemble median so every property (different
    units, different scales) sits on one comparable axis. A point on the
    dashed vertical line at 1.0 means the historical statistic equals the
    ensemble median exactly; inside the shaded band means it falls within the
    ensemble's 90% spread."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharex=True)
    keys = [k for k in PROPERTY_KEYS if k != "seasonal_means"]
    for ax, v in zip(axes, VARIABLES_ORDER):
        summary = artifacts[v]["val_summary"]
        ys = np.arange(len(keys))
        for y, key in zip(ys, keys):
            s = summary.get(key)
            if s is None:
                continue
            med = s["ensemble_median"] if s["ensemble_median"] != 0 else 1e-9
            lo_r, hi_r = s["ensemble_p5"] / med, s["ensemble_p95"] / med
            hist_r = s["historical"] / med
            color = _GREEN if s["within_90pct_envelope"] else _RED
            ax.plot([lo_r, hi_r], [y, y], color=_GRAY, lw=4, alpha=0.4, solid_capstyle="round")
            ax.scatter([hist_r], [y], color=color, s=45, zorder=5)
        ax.axvline(1.0, color="k", ls="--", lw=0.8)
        ax.set_yticks(ys)
        ax.set_yticklabels([k.replace("_", " ") for k in keys], fontsize=8.5)
        ax.set_xlabel("Historical / ensemble median")
        ax.set_title(v.capitalize(), fontsize=11)
    fig.suptitle("Property-based validation: historical statistic vs. synthetic ensemble "
                  "(green = within 90% envelope, red = outside)", fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(path)
    plt.close(fig)
    return path


def fig5_residual_diagnostics(artifacts, path=FIG_DIR / "Fig5_ResidualDiagnostics.png"):
    """Residual histogram and ACF per variable."""
    fig, axes = plt.subplots(3, 2, figsize=(11, 9.5))
    for row, v in enumerate(VARIABLES_ORDER):
        resid = artifacts[v]["model"].resid_
        ax1, ax2 = axes[row]

        ax1.hist(resid, bins=40, density=True, color=_GREEN, alpha=0.7)
        xs = np.linspace(resid.min(), resid.max(), 200)
        mu, sd = resid.mean(), resid.std()
        ax1.plot(xs, np.exp(-0.5 * ((xs - mu) / sd) ** 2) / (sd * np.sqrt(2 * np.pi)),
                  color=_RED, lw=1.5, label="Normal")
        ax1.set_title(f"{v.capitalize()}: residual distribution", fontsize=10)
        ax1.set_xlabel("Residual"); ax1.legend(fontsize=8)

        nlags = 24
        a = acf(resid, nlags); ci = conf_interval(len(resid))
        lags = np.arange(nlags + 1)
        ax2.bar(lags, a, width=0.3, color=_BLUE)
        ax2.axhline(ci, color=_RED, ls="--", lw=1)
        ax2.axhline(-ci, color=_RED, ls="--", lw=1)
        ax2.axhline(0, color="k", lw=0.8)
        ax2.set_title(f"{v.capitalize()}: residual ACF", fontsize=10)
        ax2.set_xlabel("Lag (months)")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig6_parameter_estimates(artifacts, path=FIG_DIR / "Fig6_SkillVsLead.png"):
    """AR/MA coefficient point estimates with 95% confidence intervals, one
    panel per variable -- the direct answer to "how do you estimate the
    parameters"."""
    z = _stats.norm.ppf(0.975)
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8))
    for ax, v in zip(axes, VARIABLES_ORDER):
        model = artifacts[v]["model"]
        se = model.standard_errors()
        labels, vals, errs = [], [], []
        for i, ph in enumerate(model.phi):
            labels.append(f"$\\phi_{{{i+1}}}$")
            vals.append(ph)
            e = se["phi"][i]
            errs.append(z * e if e is not None and np.isfinite(e) else 0.0)
        for i, th in enumerate(model.theta):
            labels.append(f"$\\theta_{{{i+1}}}$")
            vals.append(th)
            e = se["theta"][i]
            errs.append(z * e if e is not None and np.isfinite(e) else 0.0)
        ys = np.arange(len(labels))
        for val, err, y in zip(vals, errs, ys):
            color = _BLUE if abs(val) > err else _GRAY
            ax.errorbar([val], [y], xerr=[err], fmt="o", color="k", ecolor=color,
                        elinewidth=2.5, capsize=4, markersize=5)
        ax.axvline(0, color="k", lw=0.8, ls=":")
        ax.set_yticks(ys); ax.set_yticklabels(labels, fontsize=11)
        ax.set_xlabel("Coefficient value")
        ax.set_title(f"{v.capitalize()}: ARIMA{model.order}", fontsize=11)
        ax.invert_yaxis()
    fig.suptitle("Estimated AR/MA coefficients, 95% confidence intervals "
                  "(blue = excludes zero)", fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(path)
    plt.close(fig)
    return path
