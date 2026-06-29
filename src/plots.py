"""
plots.py — Figures for the statistical streamflow-forecasting study.

All figures are derived from observed discharge and the fitted ARIMA model;
none depends on rainfall or meteorological forcing. Figures are written to
figures/ at 300 DPI.

  Fig 1 : Observed discharge time series with train/validation split
  Fig 2 : ACF and PACF of differenced log-discharge (model identification)
  Fig 3 : Observed vs 1-day-ahead forecast hydrograph (validation window)
  Fig 4 : Observed vs predicted scatter (1-day, validation)
  Fig 5 : Residual diagnostics (series, histogram, ACF)
  Fig 6 : Forecast skill vs lead time (NSE and persistence skill score)
"""

from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .model import acf, pacf, conf_interval

FIG_DIR = Path(__file__).resolve().parent.parent / "figures"
FIG_DIR.mkdir(exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 300,
    "font.size": 11,
    "axes.grid": True,
    "grid.alpha": 0.3,
})

_BLUE = "#1f77b4"
_RED = "#d62728"
_GREEN = "#2ca02c"


def fig1_discharge_series(df, train_end, path=FIG_DIR / "Fig1_DischargeTimeSeries.png"):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True)
    ax1.plot(df.index, df["flow"], color=_BLUE, lw=0.5)
    ax1.axvline(train_end, color=_RED, ls="--", lw=1.2)
    ax1.set_ylabel("Discharge (m$^3$/s)")
    ax1.set_title("Conecuh River daily discharge, USGS 02361000 (1980-2014)")
    ax1.text(df.index[len(df)//6], df["flow"].max()*0.9, "Training\n1980-2003",
             color=_RED, fontsize=9)
    ax1.text(df.index[int(len(df)*0.82)], df["flow"].max()*0.9, "Validation\n2004-2014",
             color=_RED, fontsize=9)

    ax2.plot(df.index, df["log_flow"], color=_GREEN, lw=0.5)
    ax2.axvline(train_end, color=_RED, ls="--", lw=1.2)
    ax2.set_ylabel("ln Discharge")
    ax2.set_xlabel("Year")
    ax2.set_title("Log-transformed discharge (variance-stabilised)")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig2_acf_pacf(diff_series, nlags=40, path=FIG_DIR / "Fig2_ACF_PACF.png"):
    a = acf(diff_series, nlags)
    p = pacf(diff_series, nlags)
    ci = conf_interval(len(diff_series))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    lags = np.arange(nlags + 1)
    ax1.bar(lags, a, width=0.3, color=_BLUE)
    ax1.axhline(0, color="k", lw=0.8)
    ax1.axhline(ci, color=_RED, ls="--", lw=1)
    ax1.axhline(-ci, color=_RED, ls="--", lw=1)
    ax1.set_title("ACF of differenced log-discharge")
    ax1.set_xlabel("Lag (days)"); ax1.set_ylabel("Autocorrelation")

    ax2.bar(lags, p, width=0.3, color=_GREEN)
    ax2.axhline(0, color="k", lw=0.8)
    ax2.axhline(ci, color=_RED, ls="--", lw=1)
    ax2.axhline(-ci, color=_RED, ls="--", lw=1)
    ax2.set_title("PACF of differenced log-discharge")
    ax2.set_xlabel("Lag (days)"); ax2.set_ylabel("Partial autocorrelation")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig3_forecast_hydrograph(dates, q_obs, q_pred, q_persist=None,
                             path=FIG_DIR / "Fig3_ForecastHydrograph.png"):
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(dates, q_obs, color="k", lw=1.1, label="Observed")
    ax.plot(dates, q_pred, color=_RED, lw=1.0, ls="--", label="ARIMA 1-day forecast")
    if q_persist is not None:
        ax.plot(dates, q_persist, color="gray", lw=0.7, alpha=0.6, label="Persistence")
    ax.set_ylabel("Discharge (m$^3$/s)")
    ax.set_xlabel("Date")
    ax.set_title("Observed vs 1-day-ahead forecast (validation sample)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig4_scatter(q_obs, q_pred, lead=1, path=FIG_DIR / "Fig4_Scatter.png"):
    fig, ax = plt.subplots(figsize=(5.6, 5.6))
    ax.scatter(q_obs, q_pred, s=6, alpha=0.3, color=_BLUE)
    lim = max(q_obs.max(), q_pred.max())
    ax.plot([0, lim], [0, lim], color=_RED, ls="--", lw=1.2, label="1:1 line")
    ax.set_xlabel("Observed discharge (m$^3$/s)")
    ax.set_ylabel("Forecast discharge (m$^3$/s)")
    ax.set_title(f"Observed vs {lead}-day forecast (validation)")
    ax.legend()
    ax.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig5_residual_diagnostics(resid, path=FIG_DIR / "Fig5_ResidualDiagnostics.png"):
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4))
    axes[0].plot(resid, color=_BLUE, lw=0.4)
    axes[0].axhline(0, color="k", lw=0.8)
    axes[0].set_title("Residual series")
    axes[0].set_xlabel("Observation"); axes[0].set_ylabel("Residual")

    axes[1].hist(resid, bins=60, density=True, color=_GREEN, alpha=0.7)
    xs = np.linspace(resid.min(), resid.max(), 200)
    mu, sd = resid.mean(), resid.std()
    axes[1].plot(xs, np.exp(-0.5*((xs-mu)/sd)**2)/(sd*np.sqrt(2*np.pi)),
                 color=_RED, lw=1.5, label="Normal")
    axes[1].set_title("Residual distribution")
    axes[1].set_xlabel("Residual"); axes[1].legend()

    nlags = 30
    a = acf(resid, nlags); ci = conf_interval(len(resid))
    lags = np.arange(nlags + 1)
    axes[2].bar(lags, a, width=0.3, color=_BLUE)
    axes[2].axhline(ci, color=_RED, ls="--", lw=1)
    axes[2].axhline(-ci, color=_RED, ls="--", lw=1)
    axes[2].axhline(0, color="k", lw=0.8)
    axes[2].set_title("Residual ACF")
    axes[2].set_xlabel("Lag (days)")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig6_skill_vs_lead(results, path=FIG_DIR / "Fig6_SkillVsLead.png"):
    leads = sorted(results.keys())
    nse_model = [results[k]["model"]["NSE"] for k in leads]
    nse_persist = [results[k]["persistence"]["NSE"] for k in leads]
    pss = [results[k]["model"]["PSS"] for k in leads]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    x = np.arange(len(leads)); w = 0.35
    ax1.bar(x - w/2, nse_model, w, color=_BLUE, label="ARIMA")
    ax1.bar(x + w/2, nse_persist, w, color="gray", label="Persistence")
    ax1.set_xticks(x); ax1.set_xticklabels([f"{k}-day" for k in leads])
    ax1.set_ylabel("NSE"); ax1.set_title("Forecast NSE by lead time")
    ax1.legend()

    ax2.bar(x, pss, 0.5, color=_GREEN)
    ax2.axhline(0, color="k", lw=0.8)
    ax2.set_xticks(x); ax2.set_xticklabels([f"{k}-day" for k in leads])
    ax2.set_ylabel("Persistence skill score")
    ax2.set_title("Skill beyond persistence")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path
