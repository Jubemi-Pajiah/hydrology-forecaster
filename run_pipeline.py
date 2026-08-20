"""
run_pipeline.py — End-to-end statistical hydrological-forecasting pipeline.

Basin     : Conecuh River at Brantley, Alabama, USA (USGS 02371500, CAMELS)
Model     : three INDEPENDENT univariate ARIMA(p, d, q) models -- discharge,
            rainfall, and stage -- each identified by Box-Jenkins analysis on
            its own past values only (no cross-variable input)
Timestep  : monthly (pivoted from daily 2026-08-12 on supervisor instruction).
            Stated precisely, since the shorthand is easy to overstate:
            ordinary differencing, X(t)-X(t-1), removes trend or slow drift,
            NOT an annual cycle -- that would need X(t)-X(t-12) or SARIMA.
            A daily river does not trend within a day, so differencing has
            nothing to do there; monthly aggregation strips daily noise and
            exposes the annual cycle and any drift, which is what makes the
            differencing order d a meaningful thing to test. In the event
            ADF/KPSS select d = 0 for all three variables here.
Validation: stochastic / property-based. Each fitted model generates an
            ensemble of synthetic monthly sequences; validation compares the
            *distribution* of hydrological summary statistics (mean,
            variance, skew, persistence, seasonality, drought duration, peak)
            across that ensemble to the historical record, rather than
            scoring one forecast against the one sequence that happened to
            follow it -- which the supervisor pointed out is the wrong test
            for a stochastic model ("you cannot compare... only the
            properties"). Note the precise claim: what is inappropriate is
            judging a SINGLE realisation as if it were deterministic. The
            observation can still be scored against the full predictive
            distribution (coverage, CRPS, log score, rank histograms); the
            property comparison below is one such distribution-level check.

Run:
    python run_pipeline.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from src.preprocess import (build_monthly_dataset, split_monthly, BASIN_NAME,
                            GAUGE_ID, seasonal_profile, deseasonalise)
from src.calibrate import select_order, choose_differencing
from src.forecast import residual_diagnostics
from src.simulate import generate_synthetic_record
from src.validation import compare_ensemble_to_historical, series_properties
from src.model import SEASONAL_PERIOD

RESULTS_FILE = Path(__file__).parent / "data" / "results.json"

VARIABLES = ["discharge", "rainfall", "stage"]
UNITS = {"discharge": "m3/s", "rainfall": "mm/month", "stage": "m"}
N_REPS = 1000
SEED = 42

# Length of the synthetic record generated for the design application, and the
# return periods read off it. A specific number is needed for a worked example;
# the software itself accepts any.
RECORD_YEARS = 1000
RECORD_REPS = 50
RETURN_PERIODS = [2, 5, 10, 25, 50, 100, 500]

# Innovations are resampled from the model's own residuals rather than drawn
# from a Normal distribution. Jarque-Bera rejects normality for the residuals
# of the discharge and stage models, and the extremes of the generated record
# are the numbers a design calculation reads off it, so the shape of the
# innovation distribution matters more here than it would for a mean forecast.
INNOVATIONS = "bootstrap"


def design_summary(record: np.ndarray, months: np.ndarray, period: int = SEASONAL_PERIOD) -> dict:
    """
    The numbers a design calculation actually reads off a synthetic record:
    the overall extremes, and the annual maxima expressed as return periods.

    Annual maxima are pooled across every generated year of every realisation,
    so a 1000-year record simulated 50 times supplies 50,000 annual maxima --
    the reason for generating a long record in the first place.
    """
    n_years = record.shape[-1] // period
    usable = record[..., :n_years * period]
    annual_max = usable.reshape(record.shape[0], n_years, period).max(axis=2).ravel()
    annual_min = usable.reshape(record.shape[0], n_years, period).min(axis=2).ravel()
    return {
        "n_months": int(record.shape[-1]),
        "n_realisations": int(record.shape[0]),
        "n_annual_maxima": int(annual_max.size),
        "mean": float(record.mean()),
        "std": float(record.std(ddof=1)),
        "min": float(record.min()),
        "max": float(record.max()),
        "p95": float(np.percentile(record, 95)),
        "p99": float(np.percentile(record, 99)),
        "annual_max_mean": float(annual_max.mean()),
        "annual_min_mean": float(annual_min.mean()),
        "return_period_discharge": {
            str(T): float(np.percentile(annual_max, 100.0 * (1.0 - 1.0 / T)))
            for T in RETURN_PERIODS
        },
        "drift_ratio": float(record[:, -120:].mean() / record[:, :120].mean()),
    }


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


def fit_seasonal_difference_alternative(y_train: np.ndarray, df) -> dict:
    """
    Fit the model that results from removing the annual cycle by differencing
    at lag 12, rather than by seasonal standardisation, and measure what
    happens when it is used to generate a long record.

    Both treatments remove the cycle and both fit the observed record well.
    They differ in what they imply beyond it: seasonal differencing leaves an
    integrated process, whose variance grows without bound, so the synthetic
    record it generates drifts away from the observed scale instead of
    remaining a sample of the same river. The drift ratio returned here is the
    evidence for that, and it is reported in Section 4.2.
    """
    from src.simulate import simulate_ensemble

    diff_info = choose_differencing(y_train)
    D = diff_info["D"]
    if D == 0:
        return {"applicable": False, "D": 0,
                "seasonal_report": diff_info["seasonal_report"]}

    order, model, table, _ = select_order(
        y_train, p_range=range(0, 5), q_range=range(0, 3), D=D)
    diag = residual_diagnostics(model)

    # Generate the same length of record the standardised model is asked for.
    y_full = df["log_value"].to_numpy()
    trace = simulate_ensemble(model, y_full, RECORD_YEARS * SEASONAL_PERIOD,
                              n_reps=5, method="gaussian", seed=SEED)
    first, last = trace[:, :120].mean(), trace[:, -120:].mean()

    return {
        "applicable": True,
        "D": int(D),
        "period": int(SEASONAL_PERIOD),
        "label": model.label(),
        "order": list(order),
        "seasonal_order": list(model.seasonal_order),
        "aic": round(float(model.aic_c), 2),
        "ljung_box_pvalue": round(float(diag["ljung_box"]["pvalue"]), 4),
        "Theta": round_list(model.Theta),
        "seasonal_report": diff_info["seasonal_report"],
        "record_years": RECORD_YEARS,
        "record_mean": float(trace.mean()),
        "record_max": float(trace.max()),
        "first_decade_mean": float(first),
        "last_decade_mean": float(last),
        "drift_ratio": float(last / first),
    }


def run_variable(variable: str) -> dict:
    print(f"\n{'=' * 68}\n  VARIABLE: {variable.upper()} ({UNITS[variable]})\n{'=' * 68}")

    df = build_monthly_dataset(variable)
    train, valid = split_monthly(df)
    print(f"  Full record : {df.index[0].date()} to {df.index[-1].date()}  "
          f"({len(df)} months, {df.attrs['n_fully_missing_months']} interpolated)")
    print(f"  Training    : {train.index[0].date()} to {train.index[-1].date()}  ({len(train)} months)")
    print(f"  Validation  : {valid.index[0].date()} to {valid.index[-1].date()}  ({len(valid)} months)")

    y_train = train["log_value"].to_numpy()
    months_train = train.index.month.to_numpy()

    # ---- seasonal component: twelve monthly means and standard deviations,
    # estimated on the training period only --------------------------------
    profile = seasonal_profile(y_train, months_train)
    z_train = deseasonalise(y_train, months_train, profile)
    print(f"  Seasonal profile: {SEASONAL_PERIOD} monthly means, "
          f"log-scale range {min(profile['means']):.2f} to {max(profile['means']):.2f}")

    # ---- order selection on the deseasonalised series ----------------------
    order, model, table, diff_info = select_order(
        z_train, p_range=range(0, 5), q_range=range(0, 3), D=0)
    d = diff_info["d"]
    se = model.standard_errors()
    print(f"  Differencing d = {d}  |  Selected {model.label()}  |  "
          f"AIC={model.aic_c:.1f} BIC={model.bic_c:.1f}")
    print(f"  phi   = {np.round(model.phi, 4).tolist()}  (se: {[round(x, 4) for x in se['phi']]})")
    print(f"  theta = {np.round(model.theta, 4).tolist()}  (se: {[round(x, 4) for x in se['theta']]})")
    print(f"  const = {model.c:.6f}  (se: {round(se['c'], 6)})")

    diag = residual_diagnostics(model)
    lb = diag["ljung_box"]
    print(f"  Ljung-Box(20) p={lb['pvalue']:.4f}  |  ARCH p={diag['arch']['pvalue']:.4f}  |  "
          f"Jarque-Bera p={diag['jarque_bera']['pvalue']:.4f}")

    # ---- the alternative the supervisor asked for: difference at lag 12
    # instead of removing the cycle by standardisation. Fitted on the same
    # data so the two can be compared directly in Section 4.2. -------------
    seasonal_alt = fit_seasonal_difference_alternative(y_train, df)

    # ---- stochastic ensemble over the validation window, vs held-out data --
    ens_valid, _ = generate_synthetic_record(
        model, n_years=0, profile=profile, n_reps=N_REPS, method=INNOVATIONS,
        seed=SEED, start_month=int(valid.index[0].month),
        n_periods=len(valid))
    val_summary = compare_ensemble_to_historical(
        valid["value"].to_numpy(), valid.index, ens_valid, valid.index)
    n_ok, n_tot = val_summary["_n_properties_within_envelope"], val_summary["_n_properties_total"]
    print(f"  Property-based validation: {n_ok}/{n_tot} statistics fall within the "
          f"synthetic ensemble's 90% envelope")

    # ---- the operational output: a long synthetic record for design -------
    y_full = df["log_value"].to_numpy()
    months_full = df.index.month.to_numpy()
    profile_full = seasonal_profile(y_full, months_full)
    z_full = deseasonalise(y_full, months_full, profile_full)
    # d is pinned to zero for the generating model. A record of arbitrary
    # length is only meaningful if the process generating it is stationary:
    # any differencing leaves an integrated process whose spread widens
    # without limit, so a thousand-year record would drift away from the
    # river's observed scale rather than sample it (Section 4.2). The
    # stationarity evidence for each series is reported either way.
    stationarity_full = choose_differencing(z_full)
    order_full, model_full, _, _ = select_order(
        z_full, p_range=range(0, 5), q_range=range(0, 3), d_values=(0,), D=0)

    record, rec_months = generate_synthetic_record(
        model_full, RECORD_YEARS, profile_full, n_reps=RECORD_REPS,
        method=INNOVATIONS, seed=SEED, start_month=1, y_hist=z_full)
    design = design_summary(record, rec_months)
    long_trace_props = series_properties(record[0], pd.date_range(
        "2015-01-01", periods=record.shape[1], freq="MS"))
    hist_full_props = series_properties(df["value"].to_numpy(), df.index)
    print(f"  Synthetic record: {RECORD_YEARS} years x {RECORD_REPS} traces  "
          f"mean={design['mean']:.2f} max={design['max']:.2f} "
          f"(historical mean={hist_full_props['mean']:.2f} max={hist_full_props['peak']:.2f})")

    artifacts = {
        "df": df, "train": train, "valid": valid,
        "model": model, "w_train": z_train, "d": d, "profile": profile,
        "ens_valid": ens_valid, "val_summary": val_summary,
        "record": record, "design": design, "seasonal_alt": seasonal_alt,
    }

    summary = {
        "unit": UNITS[variable],
        "n_months": int(len(df)),
        "n_interpolated_months": int(df.attrs["n_fully_missing_months"]),
        "train_period": [str(train.index[0].date()), str(train.index[-1].date())],
        "valid_period": [str(valid.index[0].date()), str(valid.index[-1].date())],
        "differencing_d": d,
        "seasonal_period": SEASONAL_PERIOD,
        "seasonal_profile": {
            "means": round_list(profile["means"]),
            "sds": round_list(profile["sds"]),
            "period": profile["period"],
        },
        "seasonal_difference_alternative": round_dict(seasonal_alt),
        "stationarity_report": [
            {"d": r["d"],
             "adf_stat": round(r["adf"]["stat"], 4), "adf_stationary": r["adf"]["stationary_5pct"],
             "kpss_stat": round(r["kpss"]["stat"], 4), "kpss_stationary": r["kpss"]["stationary_5pct"]}
            for r in diff_info["report"]
        ],
        "order": list(order),
        "seasonal_order": list(model.seasonal_order),
        "label": model.label(),
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
            "label": model_full.label(),
            "seasonal_profile": {
                "means": round_list(profile_full["means"]),
                "sds": round_list(profile_full["sds"]),
                "period": profile_full["period"],
            },
            "constant": round(float(model_full.c), 6),
            "phi": round_list(model_full.phi),
            "theta": round_list(model_full.theta),
            "innovations": INNOVATIONS,
            "d_indicated_by_tests": stationarity_full["d"],
            "d_used": 0,
            "historical_properties": round_dict(hist_full_props),
            "long_trace_properties": round_dict(long_trace_props),
        },
        "synthetic_record": round_dict(design),
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
        sr = r["synthetic_record"]
        print(f"  {v:10s} {r['label']:24s} "
              f"validation {r['validation_n_within']}/{r['validation_n_total']} within envelope"
              f" | {RECORD_YEARS}-yr record max={sr['max']:.1f} drift={sr['drift_ratio']:.2f}")
    print("=" * 68)
    return out


if __name__ == "__main__":
    main()
