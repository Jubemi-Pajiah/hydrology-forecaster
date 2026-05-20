"""
run_pipeline.py — End-to-end hydrological forecasting pipeline.

Basin: CAMELS US 02361000 (Conecuh River, Alabama)
Model: Two-bucket lumped conceptual rainfall-runoff model
Calibration period: 1980-2003  |  Validation period: 2004-2014
Forecasts: 1-day, 2-day, 3-day ahead discharge

Run:
    python run_pipeline.py
"""

import sys
import json
from pathlib import Path

import numpy as np

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent))

from src.preprocess import build_dataset, split_dataset, MMDAY_TO_M3S
from src.model import run_model, PARAM_NAMES, PARAM_BOUNDS
from src.calibrate import calibrate, WARMUP_DAYS
from src.metrics import evaluate, nse
from src.forecast import forecast_horizon

RESULTS_FILE = Path(__file__).parent / "data" / "results.json"


def main():
    print("=" * 65)
    print("  HYDROLOGICAL FORECASTING PIPELINE")
    print("  Basin: CAMELS US 02361000 — Conecuh River, Alabama")
    print("=" * 65)

    # ------------------------------------------------------------------
    # 1. Load and preprocess data
    # ------------------------------------------------------------------
    print("\n[1/5] Loading and preprocessing data...")
    df = build_dataset()
    cal, val = split_dataset(df)
    print(f"  Full dataset : {df.index[0].date()} to {df.index[-1].date()}  ({len(df)} days)")
    print(f"  Calibration  : {cal.index[0].date()} to {cal.index[-1].date()}  ({len(cal)} days)")
    print(f"  Validation   : {val.index[0].date()} to {val.index[-1].date()}  ({len(val)} days)")

    # Numpy arrays  — model works in mm/day; q_obs in m³/s is for plotting only
    cal_prcp = cal["prcp"].to_numpy()
    cal_pet  = cal["pet"].to_numpy()
    cal_qobs_mm = cal["q_obs_mm"].to_numpy()   # mm/day — for calibration
    cal_qobs    = cal["q_obs"].to_numpy()       # m³/s   — for plotting

    val_prcp = val["prcp"].to_numpy()
    val_pet  = val["pet"].to_numpy()
    val_qobs_mm = val["q_obs_mm"].to_numpy()   # mm/day — for metrics
    val_qobs    = val["q_obs"].to_numpy()       # m³/s   — for plotting

    # ------------------------------------------------------------------
    # 2. Calibration
    # ------------------------------------------------------------------
    print("\n[2/5] Calibrating model...")
    best_params, cal_nse_reported, opt_result = calibrate(
        cal_prcp, cal_pet, cal_qobs_mm,
        seed=42, maxiter=3000, popsize=15, tol=1e-8,
    )

    print(f"\n  Optimisation converged: {opt_result.success}")
    print(f"\n  Calibrated Parameters:")
    for name, val_p in best_params.items():
        print(f"    {name:6s} = {val_p:.6f}")

    print(f"\n  Calibration NSE (warm-up excluded) = {cal_nse_reported:.4f}")
    if cal_nse_reported < 0.50:
        print("  WARNING: Calibration NSE < 0.50 — model performance is Unsatisfactory.")
        print("  Attempting re-calibration with larger population and more iterations...")
        best_params, cal_nse_reported, opt_result = calibrate(
            cal_prcp, cal_pet, cal_qobs_mm,
            seed=99, maxiter=5000, popsize=20, tol=1e-9,
        )
        print(f"  Re-calibration NSE = {cal_nse_reported:.4f}")

    # ------------------------------------------------------------------
    # 3. Validation
    # ------------------------------------------------------------------
    print("\n[3/5] Running model on validation period...")
    # Model outputs in mm/day; convert to m³/s for reporting
    val_qsim_mm  = run_model(val_prcp, val_pet, best_params)
    val_qsim     = val_qsim_mm * MMDAY_TO_M3S   # m³/s for plots/metrics
    val_metrics  = evaluate(val_qobs, val_qsim, label="Validation")

    # Full calibration run (for plotting)
    cal_qsim_mm  = run_model(cal_prcp, cal_pet, best_params)
    cal_qsim     = cal_qsim_mm * MMDAY_TO_M3S   # m³/s for plots
    cal_metrics_full = evaluate(cal_qobs[WARMUP_DAYS:], cal_qsim[WARMUP_DAYS:],
                                label="Calibration (post-warmup)")

    # ------------------------------------------------------------------
    # 4. Forecasting
    # ------------------------------------------------------------------
    print("\n[4/5] Generating 1-, 2-, 3-day ahead forecasts (validation period)...")
    # Forecasting in mm/day vs q_obs_mm; convert forecast results back to m³/s
    forecast_results_mm = forecast_horizon(
        val_prcp, val_pet, val_qobs_mm,
        params=best_params,
        lead_times=[1, 2, 3],
    )
    # Convert forecast arrays to m³/s and recompute NSE vs q_obs (m³/s)
    forecast_results = {}
    for k, v in forecast_results_mm.items():
        q_fcst_m3s = v["q_forecast"] * MMDAY_TO_M3S
        q_obs_k    = val_qobs[k:]
        from src.metrics import nse as nse_fn
        nse_k = nse_fn(q_obs_k, q_fcst_m3s)
        forecast_results[k] = {"nse": nse_k, "q_forecast": q_fcst_m3s}
        print(f"  Lead {k} day (m³/s): NSE = {nse_k:.4f}")

    # ------------------------------------------------------------------
    # 5. Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 65)
    print("  PERFORMANCE SUMMARY")
    print("=" * 65)
    print(f"  Calibration NSE        : {cal_nse_reported:.4f}")
    print(f"  Validation NSE         : {val_metrics['NSE']:.4f}")
    print(f"  Validation RMSE        : {val_metrics['RMSE']:.4f} m³/s")
    print(f"  Validation PBIAS       : {val_metrics['PBIAS']:.2f} %")
    for k in [1, 2, 3]:
        print(f"  {k}-day Forecast NSE    : {forecast_results[k]['nse']:.4f}")
    print("=" * 65)

    # ------------------------------------------------------------------
    # 6. Generate figures
    # ------------------------------------------------------------------
    print("\n[5/5] Generating figures...")
    try:
        from src.plots import (
            fig31_study_area, fig32_model_schematic, fig33_input_timeseries,
            fig41_calibration_hydrograph, fig42_validation_hydrograph,
            fig43_scatter, fig44_forecast_skill,
        )
        fig31_study_area()
        fig32_model_schematic()
        fig33_input_timeseries(df)
        fig41_calibration_hydrograph(
            cal.index[WARMUP_DAYS:], cal_qobs[WARMUP_DAYS:], cal_qsim[WARMUP_DAYS:]
        )
        fig42_validation_hydrograph(val.index, val_qobs, val_qsim)
        fig43_scatter(val_qobs, val_qsim)
        fig44_forecast_skill(forecast_results)
        print("All 7 figures saved to figures/")
    except ImportError as e:
        print(f"  WARNING: Could not generate figures ({e})")
        print("  Install matplotlib to generate figures.")

    # ------------------------------------------------------------------
    # Save results JSON for document generation
    # ------------------------------------------------------------------
    results = {
        "cal_nse":    round(cal_nse_reported, 4),
        "val_nse":    round(val_metrics["NSE"], 4),
        "val_rmse":   round(val_metrics["RMSE"], 4),
        "val_pbias":  round(val_metrics["PBIAS"], 2),
        "fcst_1d_nse": round(forecast_results[1]["nse"], 4),
        "fcst_2d_nse": round(forecast_results[2]["nse"], 4),
        "fcst_3d_nse": round(forecast_results[3]["nse"], 4),
        "params": {k: round(v, 6) for k, v in best_params.items()},
        "data_stats": {
            col: {
                "mean": round(float(df[col].mean()), 4),
                "std":  round(float(df[col].std()),  4),
                "min":  round(float(df[col].min()),  4),
                "max":  round(float(df[col].max()),  4),
            }
            for col in ["prcp", "tmax", "tmin", "pet", "q_obs"]
        },
    }
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {RESULTS_FILE}")

    return results


if __name__ == "__main__":
    main()
