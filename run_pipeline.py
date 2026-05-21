"""
run_pipeline.py — End-to-end hydrological forecasting pipeline.

Basin: Ogun-Osun River Basin, Nigeria (ungauged prediction)
Model: Two-bucket lumped conceptual rainfall-runoff model
Parameters: Transferred from Conecuh River donor basin (Alabama)
Data: NASA POWER MERRA-2 daily meteorological forcing (1990-2020)
Mode: No calibration — parameters used directly from transfer

Run:
    python run_pipeline.py
"""

import sys
import json
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from src.preprocess import build_dataset, split_dataset, MMDAY_TO_M3S
from src.model import run_model
from src.forecast import forecast_horizon

RESULTS_FILE = Path(__file__).parent / "data" / "results.json"

# Transferred parameters from Conecuh River donor basin calibration
TRANSFERRED_PARAMS = {
    "Smax": 275.323022,
    "kq":   0.496622,
    "kp":   0.006545,
    "kg":   0.300000,
    "cet":  1.630660,
}


def main():
    print("=" * 65)
    print("  HYDROLOGICAL FORECASTING PIPELINE")
    print("  Basin  : Ogun-Osun River Basin, Nigeria")
    print("  Mode   : Ungauged prediction with transferred parameters")
    print("  Donor  : Conecuh River, Alabama (CAMELS 02361000)")
    print("=" * 65)

    # ------------------------------------------------------------------
    # 1. Load NASA POWER data
    # ------------------------------------------------------------------
    print("\n[1/4] Loading and preprocessing NASA POWER data...")
    df = build_dataset()
    hist, recent = split_dataset(df)
    print(f"  Full dataset : {df.index[0].date()} to {df.index[-1].date()}  ({len(df)} days)")
    print(f"  Historical   : {hist.index[0].date()} to {hist.index[-1].date()}  ({len(hist)} days)")
    print(f"  Recent       : {recent.index[0].date()} to {recent.index[-1].date()}  ({len(recent)} days)")

    # ------------------------------------------------------------------
    # 2. Use transferred parameters (no calibration)
    # ------------------------------------------------------------------
    print("\n[2/4] Using transferred parameters from donor basin...")
    best_params = TRANSFERRED_PARAMS.copy()
    print(f"\n  Transferred Parameters (Conecuh River -> Ogun-Osun Basin):")
    for name, val_p in best_params.items():
        print(f"    {name:6s} = {val_p:.6f}")

    # ------------------------------------------------------------------
    # 3. Run model on full dataset
    # ------------------------------------------------------------------
    print("\n[3/4] Running model on full Ogun-Osun dataset (1990-2020)...")
    prcp_all = df["prcp"].to_numpy()
    pet_all  = df["pet"].to_numpy()

    q_sim_mm = run_model(prcp_all, pet_all, best_params)
    q_sim    = q_sim_mm * MMDAY_TO_M3S   # convert mm/day → m³/s

    n_hist      = len(hist)
    hist_qsim   = q_sim[:n_hist]
    recent_qsim = q_sim[n_hist:]

    print(f"  Mean simulated discharge (full period) : {q_sim.mean():.2f} m³/s")
    print(f"  Max simulated discharge                : {q_sim.max():.2f} m³/s")
    print(f"  Min simulated discharge                : {q_sim.min():.2f} m³/s")
    print(f"  Std simulated discharge                : {q_sim.std():.2f} m³/s")

    # ------------------------------------------------------------------
    # 4. Generate forecasts (ungauged — no NSE computation)
    # ------------------------------------------------------------------
    print("\n  Running 1-, 2-, 3-day ahead forecasts on recent period (2004-2020)...")
    prcp_recent = recent["prcp"].to_numpy()
    pet_recent  = recent["pet"].to_numpy()

    forecast_results_mm = forecast_horizon(
        prcp_recent, pet_recent, None,  # q_obs=None for ungauged basin
        params=best_params,
        lead_times=[1, 2, 3],
    )
    forecast_results = {}
    for k, v in forecast_results_mm.items():
        q_fcst_m3s = v["q_forecast"] * MMDAY_TO_M3S
        forecast_results[k] = {
            "q_forecast": q_fcst_m3s,
            "mean": float(q_fcst_m3s.mean()),
        }
        print(f"  Lead {k} day: mean forecast Q = {q_fcst_m3s.mean():.2f} m³/s")

    # ------------------------------------------------------------------
    # 5. Generate figures
    # ------------------------------------------------------------------
    print("\n[4/4] Generating figures...")
    try:
        from src.plots import (
            fig31_study_area, fig32_model_schematic, fig33_input_timeseries,
            fig41_calibration_hydrograph, fig42_validation_hydrograph,
            fig43_scatter, fig44_forecast_skill,
        )
        fig31_study_area()
        fig32_model_schematic()
        fig33_input_timeseries(df)
        fig41_calibration_hydrograph(hist.index, None, hist_qsim)
        fig42_validation_hydrograph(recent.index, None, recent_qsim)
        fig43_scatter(df.index, q_sim)
        fig44_forecast_skill(forecast_results)
        print("All 7 figures saved to figures/")
    except ImportError as e:
        print(f"  WARNING: Could not generate figures ({e})")
        print("  Install matplotlib to generate figures.")

    # ------------------------------------------------------------------
    # Save results JSON
    # ------------------------------------------------------------------
    results = {
        "params": {k: round(v, 6) for k, v in best_params.items()},
        "q_sim_mean": round(float(q_sim.mean()), 4),
        "q_sim_max":  round(float(q_sim.max()),  4),
        "q_sim_min":  round(float(q_sim.min()),  4),
        "q_sim_std":  round(float(q_sim.std()),  4),
        "data_stats": {
            col: {
                "mean": round(float(df[col].mean()), 4),
                "std":  round(float(df[col].std()),  4),
                "min":  round(float(df[col].min()),  4),
                "max":  round(float(df[col].max()),  4),
            }
            for col in ["prcp", "tmax", "tmin", "pet"]
        },
        "fcst_1d_mean": round(float(forecast_results[1]["mean"]), 4),
        "fcst_2d_mean": round(float(forecast_results[2]["mean"]), 4),
        "fcst_3d_mean": round(float(forecast_results[3]["mean"]), 4),
    }
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {RESULTS_FILE}")

    print("\n" + "=" * 65)
    print("  SIMULATION SUMMARY — OGUN-OSUN RIVER BASIN")
    print("=" * 65)
    print(f"  Transferred Smax          : {best_params['Smax']:.2f} mm")
    print(f"  Mean simulated discharge  : {q_sim.mean():.2f} m³/s")
    print(f"  Peak simulated discharge  : {q_sim.max():.2f} m³/s")
    print(f"  1-day mean forecast Q     : {forecast_results[1]['mean']:.2f} m³/s")
    print(f"  2-day mean forecast Q     : {forecast_results[2]['mean']:.2f} m³/s")
    print(f"  3-day mean forecast Q     : {forecast_results[3]['mean']:.2f} m³/s")
    print("=" * 65)

    return results


if __name__ == "__main__":
    main()
