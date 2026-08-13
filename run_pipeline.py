"""
run_pipeline.py — End-to-end statistical hydrological-forecasting pipeline.

Basin     : Conecuh River at Brantley, Alabama, USA (USGS 02371500, CAMELS)
Model     : three INDEPENDENT univariate ARIMA(p, d, q) models -- discharge,
            rainfall, and stage -- each identified by Box-Jenkins analysis on
            its own past values only (no cross-variable input)
Timestep  : monthly (pivoted from daily 2026-08-12 on supervisor instruction:
            differencing removes seasonality at a monthly timestep, which it
            does not do anything useful for at a daily one)
Validation: stochastic / property-based. Each fitted model generates an
            ensemble of synthetic monthly sequences; validation compares the
            *distribution* of hydrological summary statistics (mean,
            variance, skew, persistence, seasonality, drought duration, peak)
            across that ensemble to the historical record, rather than
            scoring one forecast against the one sequence that happened to
            follow it -- which the supervisor pointed out is meaningless for
            a stochastic model ("you cannot compare... only the properties").

Run:
    python run_pipeline.py
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from src.preprocess import build_monthly_dataset, split_monthly, BASIN_NAME, GAUGE_ID
from src.calibrate import select_order
from src.forecast import residual_diagnostics
from src.simulate import simulate_ensemble
from src.validation import compare_ensemble_to_historical, series_properties
from src.model import difference

RESULTS_FILE = Path(__file__).parent / "data" / "results.json"

VARIABLES = ["discharge", "rainfall", "stage"]
UNITS = {"discharge": "m3/s", "rainfall": "mm/month", "stage": "m"}
N_REPS = 1000
SEED = 42


def round_list(x, nd=6):
    return [round(float(v), nd) for v in x]


def round_dict(d, nd=4):
    out = {}
    for k, v in d.items():
        if isinstance(v, float):
            out[k] = round(v, nd)
        elif isinstance(v, dict):
            out[k] = round_dict(v, nd)
        elif isinstance(v, list):
            out[k] = [round(x, nd) if isinstance(x, float) else x for x in v]
        else:
            out[k] = v
    return out


def run_variable(variable: str) -> dict:
    print(f"\n{'=' * 68}\n  VARIABLE: {variable.upper()} ({UNITS[variable]})\n{'=' * 68}")

    df = build_monthly_dataset(variable)
    train, valid = split_monthly(df)
    print(f"  Full record : {df.index[0].date()} to {df.index[-1].date()}  "
          f"({len(df)} months, {df.attrs['n_fully_missing_months']} interpolated)")
    print(f"  Training    : {train.index[0].date()} to {train.index[-1].date()}  ({len(train)} months)")
    print(f"  Validation  : {valid.index[0].date()} to {valid.index[-1].date()}  ({len(valid)} months)")

    y_train = train["log_value"].to_numpy()

    # ---- order selection (differencing chosen by ADF+KPSS, order by AIC) ----
    order, model, table, diff_info = select_order(
        y_train, p_range=range(0, 5), q_range=range(0, 3))
    d = diff_info["d"]
    se = model.standard_errors()
    print(f"  Differencing d = {d}  |  Selected ARIMA{order}  |  "
          f"AIC={model.aic_c:.1f} BIC={model.bic_c:.1f}")
    print(f"  phi   = {np.round(model.phi, 4).tolist()}  (se: {[round(x, 4) for x in se['phi']]})")
    print(f"  theta = {np.round(model.theta, 4).tolist()}  (se: {[round(x, 4) for x in se['theta']]})")
    print(f"  const = {model.c:.6f}  (se: {round(se['c'], 6)})")

    diag = residual_diagnostics(model)
    lb = diag["ljung_box"]
    print(f"  Ljung-Box(20) p={lb['pvalue']:.4f}  |  ARCH p={diag['arch']['pvalue']:.4f}  |  "
          f"Jarque-Bera p={diag['jarque_bera']['pvalue']:.4f}")

    # ---- stochastic ensemble over the validation window, vs held-out data --
    ens_valid = simulate_ensemble(model, y_train, len(valid), n_reps=N_REPS,
                                  method="gaussian", seed=SEED)
    val_summary = compare_ensemble_to_historical(
        valid["value"].to_numpy(), valid.index, ens_valid, valid.index)
    n_ok, n_tot = val_summary["_n_properties_within_envelope"], val_summary["_n_properties_total"]
    print(f"  Property-based validation: {n_ok}/{n_tot} statistics fall within the "
          f"synthetic ensemble's 90% envelope")

    # ---- full-record fit: illustrative long synthetic trace for the
    # reservoir/spillway-sizing application named by the supervisor ---------
    order_full, model_full, _, diff_info_full = select_order(
        df["log_value"].to_numpy(), p_range=range(0, 5), q_range=range(0, 3))
    long_trace = simulate_ensemble(model_full, df["log_value"].to_numpy(), len(df),
                                    n_reps=1, method="gaussian", seed=SEED)[0]
    long_trace_props = series_properties(long_trace)
    hist_full_props = series_properties(df["value"].to_numpy(), df.index)

    artifacts = {
        "df": df, "train": train, "valid": valid,
        "model": model, "w_train": difference(y_train, d), "d": d,
        "ens_valid": ens_valid, "val_summary": val_summary,
    }

    summary = {
        "unit": UNITS[variable],
        "n_months": int(len(df)),
        "n_interpolated_months": int(df.attrs["n_fully_missing_months"]),
        "train_period": [str(train.index[0].date()), str(train.index[-1].date())],
        "valid_period": [str(valid.index[0].date()), str(valid.index[-1].date())],
        "differencing_d": d,
        "stationarity_report": [
            {"d": r["d"],
             "adf_stat": round(r["adf"]["stat"], 4), "adf_stationary": r["adf"]["stationary_5pct"],
             "kpss_stat": round(r["kpss"]["stat"], 4), "kpss_stationary": r["kpss"]["stationary_5pct"]}
            for r in diff_info["report"]
        ],
        "order": list(order),
        "aic": round(model.aic_c, 2),
        "bic": round(model.bic_c, 2),
        "phi": round_list(model.phi),
        "theta": round_list(model.theta),
        "constant": round(float(model.c), 6),
        "standard_errors": {
            "c": round(se["c"], 6) if np.isfinite(se["c"]) else None,
            "phi": [round(x, 6) if np.isfinite(x) else None for x in se["phi"]],
            "theta": [round(x, 6) if np.isfinite(x) else None for x in se["theta"]],
        },
        "aic_ranking": [
            {"order": list(r["order"]), "aic": round(r["aic"], 2), "bic": round(r["bic"], 2)}
            for r in table[:5]
        ],
        "diagnostics": {
            "ljung_box": {"stat": round(lb["stat"], 3), "pvalue": round(lb["pvalue"], 4)},
            "arch": {"stat": round(diag["arch"]["stat"], 3), "pvalue": round(diag["arch"]["pvalue"], 4)},
            "jarque_bera": round_dict(diag["jarque_bera"]),
            "roots": {"ar": [round(x, 3) for x in diag["roots"]["ar"]],
                      "ma": [round(x, 3) for x in diag["roots"]["ma"]]},
            "smearing_factor": round(diag["smearing_factor"], 4),
        },
        "historical_stats": round_dict(series_properties(train["value"].to_numpy(), train.index)),
        "validation": round_dict({k: v for k, v in val_summary.items() if not k.startswith("_")}),
        "validation_n_within": n_ok,
        "validation_n_total": n_tot,
        "full_record": {
            "order": list(order_full),
            "historical_properties": round_dict(hist_full_props),
            "long_trace_properties": round_dict(long_trace_props),
        },
    }
    return summary, artifacts


def main():
    print("=" * 68)
    print("  STATISTICAL HYDROLOGICAL FORECASTING PIPELINE (monthly, 3-variable)")
    print(f"  Basin : {BASIN_NAME} (USGS {GAUGE_ID})")
    print("  Model : three independent ARIMA(p,d,q) models -- discharge,")
    print("          rainfall, stage -- each on its own past values only")
    print("=" * 68)

    out = {
        "basin": f"{BASIN_NAME} (USGS {GAUGE_ID})",
        "gauge_id": GAUGE_ID,
        "timestep": "monthly",
        "variables": {},
    }
    artifacts = {}
    for v in VARIABLES:
        summary, art = run_variable(v)
        out["variables"][v] = summary
        artifacts[v] = art

    RESULTS_FILE.parent.mkdir(exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nResults saved to {RESULTS_FILE}")

    print("\nGenerating figures...")
    from src.plots import (
        fig1_monthly_series, fig2_acf_pacf, fig3_ensemble_vs_historical,
        fig4_property_validation, fig5_residual_diagnostics, fig6_parameter_estimates,
    )
    figs = [
        fig1_monthly_series(artifacts),
        fig2_acf_pacf(artifacts),
        fig3_ensemble_vs_historical(artifacts),
        fig4_property_validation(artifacts),
        fig5_residual_diagnostics(artifacts),
        fig6_parameter_estimates(artifacts),
    ]
    for f in figs:
        print(f"  saved {Path(f).name}")

    print("\n" + "=" * 68)
    print("  SUMMARY")
    print("=" * 68)
    for v in VARIABLES:
        r = out["variables"][v]
        print(f"  {v:10s} ARIMA{tuple(r['order'])}  d={r['differencing_d']}  "
              f"validation {r['validation_n_within']}/{r['validation_n_total']} within envelope")
    print("=" * 68)
    return out


if __name__ == "__main__":
    main()
