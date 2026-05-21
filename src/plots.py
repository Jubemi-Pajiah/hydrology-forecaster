"""
plots.py — Generate 7 publication-quality figures (300 DPI PNG).

Figures:
  Fig 3.1 — Study area map (Ogun-Osun River Basin, Nigeria)
  Fig 3.2 — Two-bucket model schematic
  Fig 3.3 — Input data time series (P, Tmax, Tmin, PET)
  Fig 4.1 — Historical simulated hydrograph (1990–2003)
  Fig 4.2 — Recent simulated hydrograph (2004–2020)
  Fig 4.3 — Seasonal cycle of simulated discharge (monthly means)
  Fig 4.4 — Mean simulated discharge by forecast lead time
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from pathlib import Path
import pandas as pd

DPI = 300
FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

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
    """Schematic study area map — Ogun-Osun River Basin, southwestern Nigeria."""
    fig, ax = plt.subplots(figsize=(7, 5))

    # Simplified Nigeria polygon (approximate boundary)
    nigeria_lon = [2.7, 3.4, 4.2, 5.0, 5.5, 6.0, 6.8, 7.8, 9.0,
                   10.2, 11.0, 12.5, 13.3, 14.7, 14.5, 13.5,
                   12.5, 11.5, 10.5, 9.5, 8.5, 7.5, 7.0, 6.5, 5.8,
                   5.0, 4.5, 4.0, 3.5, 3.0, 2.7]
    nigeria_lat = [6.3, 5.0, 4.5, 4.3, 4.3, 4.5, 4.8, 5.0, 5.3,
                   5.8, 6.0, 6.5, 7.5, 6.5, 13.0, 13.9,
                   13.5, 13.2, 12.8, 12.0, 11.0, 10.2, 9.5, 8.5,
                   7.5, 7.0, 6.8, 7.0, 7.2, 7.5, 6.3]

    ax.fill(nigeria_lon, nigeria_lat, color="#d9e8f0", ec="steelblue", lw=1.5,
            label="Nigeria", zorder=1)

    # Ogun-Osun Basin approximate polygon (SW Nigeria)
    basin_lon = [2.8, 3.1, 3.6, 4.1, 4.4, 4.2, 3.8, 3.3, 2.9, 2.8]
    basin_lat = [6.5, 6.2, 6.3, 6.8, 7.5, 8.2, 8.5, 8.1, 7.4, 6.5]
    ax.fill(basin_lon, basin_lat, color="#a8d5a2", ec="#2d6a4f", lw=2.0,
            label="Ogun-Osun Basin (~22,800 km²)", zorder=2, alpha=0.85)

    # Basin centroid marker
    ax.plot(3.5, 7.5, "r*", ms=13, zorder=5, label="Basin Centroid (7.5°N, 3.5°E)")

    # Basin label
    ax.text(3.6, 7.6, "Ogun-Osun\nBasin", fontsize=8, va="bottom",
            color="#2d6a4f", fontweight="bold", zorder=6)

    # Country label
    ax.text(9.5, 9.5, "NIGERIA", fontsize=11, ha="center", va="center",
            color="steelblue", fontweight="bold", alpha=0.6, zorder=3)

    # Compass rose
    ax.annotate("N", xy=(0.93, 0.93), xycoords="axes fraction", fontsize=13,
                ha="center", va="bottom", fontweight="bold")
    ax.annotate("", xy=(0.93, 0.93), xytext=(0.93, 0.86),
                xycoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.5))

    ax.set_xlim(1.5, 15.5)
    ax.set_ylim(3.5, 14.5)
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.set_title("Figure 3.1: Study Area — Ogun-Osun River Basin, Southwestern Nigeria\n"
                 "(Basin Centroid: 7.5°N, 3.5°E; Drainage Area ≈ 22,800 km²)",
                 fontsize=10)
    ax.legend(loc="upper left", framealpha=0.9, fontsize=8)
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

    def box(x, y, w, h, label, color):
        rect = FancyBboxPatch((x, y), w, h,
                              boxstyle="round,pad=0.1",
                              fc=color, ec="black", lw=1.5)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
                fontsize=11, fontweight="bold")

    box(2.5, 5.5, 5, 2.5, "SOIL STORE\nS(t)   [mm]", "#a8d5a2")
    box(2.5, 1.5, 5, 2.5, "GROUNDWATER STORE\nG(t)   [mm]", "#a0c4ff")

    def arrow(x1, y1, x2, y2, label, color="black", lw=1.5):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=color,
                                   lw=lw, mutation_scale=15))
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.15, my, label, fontsize=8.5, color=color,
                ha="left", va="center")

    ax.text(5, 9.3, "P(t)\n[Precipitation]", ha="center", va="top", fontsize=9,
            color="#1565C0", fontweight="bold")
    arrow(5, 8.9, 5, 8.05, "", color="#1565C0")
    arrow(7.5, 7, 9, 7.8, "ET(t) = cet·PET·S/Smax", color="#e63946")
    arrow(7.5, 6, 9.2, 4.5, "Q_quick(t) = kq·max(0, S−Smax)", color="#f4a261")
    arrow(5, 5.5, 5, 4.05, "R_perc(t) = kp·S(t)", color="#6d4c41")
    arrow(7.5, 2.75, 9.2, 1.5, "Q_base(t) = kg·G(t)", color="#023e8a")

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
    """Input data time series: precipitation, temperature, PET (no discharge — ungauged)."""
    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
    dates = df.index

    axes[0].bar(dates, df["prcp"], color="#1565C0", width=1, label="Precipitation")
    axes[0].set_ylabel("P (mm/day)")
    axes[0].legend(loc="upper right")
    axes[0].set_title(
        "Figure 3.3: Input Data Time Series — Ogun-Osun River Basin, Nigeria (1990–2020)\n"
        "Source: NASA POWER MERRA-2 (7.5°N, 3.5°E)")

    axes[1].plot(dates, df["tmax"], color="#e63946", lw=0.6, label="T_max")
    axes[1].plot(dates, df["tmin"], color="#457b9d", lw=0.6, label="T_min")
    axes[1].set_ylabel("Temperature (°C)")
    axes[1].legend(loc="upper right")

    axes[2].plot(dates, df["pet"], color="#f4a261", lw=0.6, label="PET (Hargreaves)")
    axes[2].set_ylabel("PET (mm/day)")
    axes[2].set_xlabel("Date")
    axes[2].legend(loc="upper right")

    fig.tight_layout()
    out = FIGURES_DIR / "Fig3_3_InputTimeSeries.png"
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")
    return out


def fig41_calibration_hydrograph(dates, q_obs, q_sim):
    """Historical period simulated discharge hydrograph (1990–2003)."""
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(dates, q_sim, color="#e63946", lw=0.8, label="Simulated discharge", alpha=0.9)
    ax.fill_between(dates, q_sim, alpha=0.15, color="#e63946")
    ax.set_xlabel("Date")
    ax.set_ylabel("Simulated Discharge (m³/s)")
    ax.set_title(
        "Figure 4.1: Historical Period Simulated Discharge Hydrograph (1990–2003)\n"
        "Ogun-Osun River Basin — Two-Bucket Model with Transferred Parameters")
    ax.legend()
    ax.axhline(float(q_sim.mean()), ls="--", color="#023e8a", lw=1.0,
               label=f"Period mean ({float(q_sim.mean()):.1f} m³/s)", alpha=0.7)
    ax.legend()
    fig.tight_layout()
    out = FIGURES_DIR / "Fig4_1_CalibrationHydrograph.png"
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")
    return out


def fig42_validation_hydrograph(dates, q_obs, q_sim):
    """Recent period simulated discharge hydrograph (2004–2020)."""
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(dates, q_sim, color="#023e8a", lw=0.8, label="Simulated discharge", alpha=0.9)
    ax.fill_between(dates, q_sim, alpha=0.12, color="#023e8a")
    ax.set_xlabel("Date")
    ax.set_ylabel("Simulated Discharge (m³/s)")
    ax.set_title(
        "Figure 4.2: Recent Period Simulated Discharge Hydrograph (2004–2020)\n"
        "Ogun-Osun River Basin — Two-Bucket Model with Transferred Parameters")
    ax.axhline(float(q_sim.mean()), ls="--", color="#e63946", lw=1.0,
               label=f"Period mean ({float(q_sim.mean()):.1f} m³/s)", alpha=0.7)
    ax.legend()
    fig.tight_layout()
    out = FIGURES_DIR / "Fig4_2_ValidationHydrograph.png"
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")
    return out


def fig43_scatter(dates, q_sim):
    """Mean monthly simulated discharge — seasonal cycle (1990–2020)."""
    q_series = pd.Series(q_sim, index=dates)
    monthly_mean = q_series.groupby(q_series.index.month).mean()
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    colors = [
        "#457b9d", "#457b9d", "#457b9d",   # dry: Jan-Mar
        "#f4a261", "#f4a261",               # transitional: Apr-May
        "#2d6a4f", "#2d6a4f", "#2d6a4f", "#2d6a4f",  # wet: Jun-Sep
        "#f4a261", "#f4a261",               # transitional: Oct-Nov
        "#457b9d",                          # dry: Dec
    ]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(range(1, 13), monthly_mean.values,
                  color=colors, edgecolor="black", lw=0.6, alpha=0.88)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(months)
    ax.set_xlabel("Month")
    ax.set_ylabel("Mean Simulated Discharge (m³/s)")
    ax.set_title(
        "Figure 4.3: Seasonal Cycle of Simulated Discharge\n"
        "Mean Monthly Discharge — Ogun-Osun River Basin (1990–2020)")
    ann_mean = monthly_mean.mean()
    ax.axhline(ann_mean, ls="--", color="red", lw=1.3,
               label=f"Annual mean  {ann_mean:.1f} m³/s")
    # Value labels
    for bar, v in zip(bars, monthly_mean.values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.3,
                f"{v:.0f}", ha="center", va="bottom", fontsize=8)
    ax.legend()

    # Add season annotations
    ax.axvspan(5.5, 9.5, alpha=0.05, color="green", label="Main wet season")
    ax.text(7.5, monthly_mean.max() * 0.95, "Main wet season",
            ha="center", fontsize=8, color="#2d6a4f", style="italic")

    fig.tight_layout()
    out = FIGURES_DIR / "Fig4_3_ScatterPlot.png"
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")
    return out


def fig44_forecast_skill(forecast_results: dict):
    """Bar chart: mean simulated discharge by forecast lead time."""
    lead_times = sorted(forecast_results.keys())
    mean_vals = [forecast_results[k]["mean"] for k in lead_times]
    labels = [f"{k}-day" for k in lead_times]
    colors = ["#2d6a4f", "#52b788", "#95d5b2"]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, mean_vals, color=colors, edgecolor="black", lw=0.8)
    for bar, v in zip(bars, mean_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.5,
                f"{v:.1f}", ha="center", va="bottom", fontsize=9)
    ax.set_xlabel("Forecast Lead Time")
    ax.set_ylabel("Mean Simulated Discharge (m³/s)")
    ax.set_title(
        "Figure 4.4: Mean Simulated Discharge by Forecast Lead Time\n"
        "Ogun-Osun River Basin — Recent Period (2004–2020)")
    ax.set_ylim(0, max(mean_vals) * 1.25)
    fig.tight_layout()
    out = FIGURES_DIR / "Fig4_4_ForecastSkill.png"
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")
    return out
