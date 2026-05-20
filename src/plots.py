"""
plots.py — Generate 7 publication-quality figures (300 DPI PNG).

Figures:
  Fig 3.1 — Study area map (Conecuh River basin, Alabama)
  Fig 3.2 — Two-bucket model schematic
  Fig 3.3 — Input data time series (P, Tmax, Tmin, Q)
  Fig 4.1 — Calibration hydrograph (obs vs sim)
  Fig 4.2 — Validation hydrograph (obs vs sim)
  Fig 4.3 — Scatter plot obs vs sim (validation)
  Fig 4.4 — Forecast skill bar chart (NSE vs lead time)
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")   # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patches as FancyBboxPatch
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from pathlib import Path
import pandas as pd

DPI = 300
FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

# Style
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "legend.fontsize": 9,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def fig31_study_area():
    """Schematic study area map of Conecuh River basin, Alabama."""
    fig, ax = plt.subplots(figsize=(7, 5))

    # Draw a simplified outline of Alabama
    # Approximate polygon vertices (longitude, latitude)
    alabama_lon = [-88.47, -85.61, -85.09, -84.89, -85.41, -87.32, -88.47, -88.47]
    alabama_lat = [35.00, 34.99, 32.84, 30.98, 30.23, 30.13, 30.24, 35.00]

    ax.fill(alabama_lon, alabama_lat, color="#d9e8f0", ec="steelblue", lw=1.5,
            label="Alabama", zorder=1)

    # Basin outline (approximate Conecuh River basin)
    basin_lon = [-86.4, -86.8, -87.0, -87.0, -86.8, -86.5, -86.2, -86.1, -86.3, -86.4]
    basin_lat = [32.0,  31.7,  31.4,  31.1,  30.9,  30.8,  30.9,  31.2,  31.6,  32.0]
    ax.fill(basin_lon, basin_lat, color="#a8d5a2", ec="#2d6a4f", lw=2.0,
            label="Conecuh River Basin", zorder=2, alpha=0.85)

    # River schematic
    river_lon = [-86.2, -86.5, -86.7, -87.0]
    river_lat = [31.8,  31.4,  31.1,  30.9]
    ax.plot(river_lon, river_lat, color="#1565C0", lw=2.5, label="Conecuh River", zorder=3)

    # Gauge location
    ax.plot(-87.0, 30.9, "rv", ms=10, zorder=5, label="USGS Gauge 02361000")

    # Compass rose
    ax.annotate("N", xy=(0.94, 0.92), xycoords="axes fraction", fontsize=13,
                ha="center", va="bottom", fontweight="bold")
    ax.annotate("", xy=(0.94, 0.92), xytext=(0.94, 0.85),
                xycoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.5))

    ax.set_xlim(-88.7, -84.7)
    ax.set_ylim(29.9, 35.3)
    ax.set_xlabel("Longitude (°W)")
    ax.set_ylabel("Latitude (°N)")
    ax.set_title("Figure 3.1: Study Area — Conecuh River Basin, Alabama, USA\n"
                 "(USGS Gauge 02361000, CAMELS Dataset)")
    ax.legend(loc="lower right", framealpha=0.9)
    ax.grid(ls="--", alpha=0.4)

    out = FIGURES_DIR / "Fig3_1_StudyAreaMap.png"
    fig.tight_layout()
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")
    return out


def fig32_model_schematic():
    """Two-bucket model schematic diagram."""
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.set_facecolor("white")

    # --- Boxes ---
    def box(x, y, w, h, label, color):
        rect = FancyBboxPatch((x, y), w, h,
                              boxstyle="round,pad=0.1",
                              fc=color, ec="black", lw=1.5)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
                fontsize=11, fontweight="bold")

    # Soil bucket
    box(2.5, 5.5, 5, 2.5, "SOIL STORE\nS(t)   [mm]", "#a8d5a2")
    # Groundwater bucket
    box(2.5, 1.5, 5, 2.5, "GROUNDWATER STORE\nG(t)   [mm]", "#a0c4ff")

    def arrow(x1, y1, x2, y2, label, color="black", lw=1.5):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=color,
                                   lw=lw, mutation_scale=15))
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.15, my, label, fontsize=8.5, color=color,
                ha="left", va="center")

    # Precipitation input
    ax.text(5, 9.3, "P(t)\n[Precipitation]", ha="center", va="top", fontsize=9,
            color="#1565C0", fontweight="bold")
    arrow(5, 8.9, 5, 8.05, "", color="#1565C0")

    # ET output
    arrow(7.5, 7, 9, 7.8, "ET(t) = cet·PET·S/Smax", color="#e63946")

    # Qquick (excess above Smax)
    arrow(7.5, 6, 9.2, 4.5, "Q_quick(t) = kq·max(0, S−Smax)", color="#f4a261")

    # Percolation (soil → GW)
    arrow(5, 5.5, 5, 4.05, "R_perc(t) = kp·S(t)", color="#6d4c41")

    # Baseflow (GW → outlet)
    arrow(7.5, 2.75, 9.2, 1.5, "Q_base(t) = kg·G(t)", color="#023e8a")

    # Merge Qquick + Qbase
    ax.text(9.4, 0.8, "Q_sim = Q_quick + Q_base", fontsize=9, va="center",
            ha="left", color="black",
            bbox=dict(fc="#ffe8a1", ec="orange", lw=1.2, boxstyle="round"))

    ax.set_title("Figure 3.2: Two-Bucket Lumped Conceptual Rainfall-Runoff Model Structure",
                 fontsize=10, pad=10)

    out = FIGURES_DIR / "Fig3_2_ModelSchematic.png"
    fig.tight_layout()
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")
    return out


def fig33_input_timeseries(df: pd.DataFrame):
    """Input data time series: precipitation, temperature, streamflow."""
    fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
    dates = df.index

    axes[0].bar(dates, df["prcp"], color="#1565C0", width=1, label="Precipitation")
    axes[0].set_ylabel("P (mm/day)")
    axes[0].legend(loc="upper right")
    axes[0].set_title("Figure 3.3: Input Data Time Series — CAMELS Basin 02361000 (1980–2014)")

    axes[1].plot(dates, df["tmax"], color="#e63946", lw=0.6, label="T_max")
    axes[1].plot(dates, df["tmin"], color="#457b9d", lw=0.6, label="T_min")
    axes[1].set_ylabel("Temperature (°C)")
    axes[1].legend(loc="upper right")

    axes[2].plot(dates, df["pet"], color="#f4a261", lw=0.6, label="PET (Hargreaves)")
    axes[2].set_ylabel("PET (mm/day)")
    axes[2].legend(loc="upper right")

    axes[3].plot(dates, df["q_obs"], color="#023e8a", lw=0.7, label="Q_obs")
    axes[3].set_ylabel("Q (m³/s)")
    axes[3].set_xlabel("Date")
    axes[3].legend(loc="upper right")

    fig.tight_layout()
    out = FIGURES_DIR / "Fig3_3_InputTimeSeries.png"
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")
    return out


def fig41_calibration_hydrograph(dates, q_obs, q_sim):
    """Calibration period: observed vs simulated hydrograph."""
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(dates, q_obs, color="#023e8a", lw=0.8, label="Observed", alpha=0.85)
    ax.plot(dates, q_sim, color="#e63946", lw=0.8, ls="--", label="Simulated", alpha=0.85)
    ax.set_xlabel("Date")
    ax.set_ylabel("Discharge (m³/s)")
    ax.set_title("Figure 4.1: Calibration Period Hydrograph — Observed vs. Simulated (1980–2003)")
    ax.legend()
    fig.tight_layout()
    out = FIGURES_DIR / "Fig4_1_CalibrationHydrograph.png"
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")
    return out


def fig42_validation_hydrograph(dates, q_obs, q_sim):
    """Validation period: observed vs simulated hydrograph."""
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(dates, q_obs, color="#023e8a", lw=0.8, label="Observed", alpha=0.85)
    ax.plot(dates, q_sim, color="#e63946", lw=0.8, ls="--", label="Simulated", alpha=0.85)
    ax.set_xlabel("Date")
    ax.set_ylabel("Discharge (m³/s)")
    ax.set_title("Figure 4.2: Validation Period Hydrograph — Observed vs. Simulated (2004–2014)")
    ax.legend()
    fig.tight_layout()
    out = FIGURES_DIR / "Fig4_2_ValidationHydrograph.png"
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")
    return out


def fig43_scatter(q_obs, q_sim):
    """Scatter plot: observed vs simulated discharge (validation period)."""
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.scatter(q_obs, q_sim, s=4, alpha=0.4, color="#023e8a", label="Daily values")
    # 1:1 line
    lim = max(q_obs.max(), q_sim.max()) * 1.05
    ax.plot([0, lim], [0, lim], "r--", lw=1.2, label="1:1 line")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("Observed Discharge (m³/s)")
    ax.set_ylabel("Simulated Discharge (m³/s)")
    ax.set_title("Figure 4.3: Observed vs. Simulated Discharge\nValidation Period (2004–2014)")
    ax.legend()
    fig.tight_layout()
    out = FIGURES_DIR / "Fig4_3_ScatterPlot.png"
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")
    return out


def fig44_forecast_skill(forecast_results: dict):
    """Bar chart: NSE for 1, 2, 3-day lead times."""
    lead_times = sorted(forecast_results.keys())
    nse_vals = [forecast_results[k]["nse"] for k in lead_times]
    labels = [f"{k}-day" for k in lead_times]
    colors = ["#2d6a4f", "#52b788", "#95d5b2"]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, nse_vals, color=colors, edgecolor="black", lw=0.8)
    # Threshold lines
    ax.axhline(0.75, ls="--", color="green", lw=1.0, label="Very Good (NSE>0.75)")
    ax.axhline(0.65, ls=":",  color="orange", lw=1.0, label="Good (NSE>0.65)")
    ax.axhline(0.50, ls="-.", color="red",   lw=1.0, label="Acceptable (NSE>0.50)")
    # Value labels
    for bar, v in zip(bars, nse_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.01,
                f"{v:.3f}", ha="center", va="bottom", fontsize=9)
    ax.set_xlabel("Forecast Lead Time")
    ax.set_ylabel("Nash-Sutcliffe Efficiency (NSE)")
    ax.set_title("Figure 4.4: Forecast Skill — NSE by Lead Time\n(Validation Period, 2004–2014)")
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=8, loc="lower left")
    fig.tight_layout()
    out = FIGURES_DIR / "Fig4_4_ForecastSkill.png"
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")
    return out
