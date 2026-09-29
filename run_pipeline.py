"""
run_pipeline.py — End-to-end statistical synthetic-record pipeline.

Case study : Hadejia River at Hadejia, Jigawa State, Nigeria
             (GRDC 1837401 / GSIM NG_0000012; 30,435 km2; 1980-2006 monthly)
Contrast   : Conecuh River at Brantley, Alabama, USA (USGS 02371500, CAMELS)
Model      : univariate ARIMA(p, d, q) fitted by Box-Jenkins identification to
             the deseasonalised log-transformed monthly series, then used to
             GENERATE a synthetic monthly record of arbitrary length, from
             which design discharges are read by return period.

Design
------
1. TWO RIVERS. The case study is a Nigerian (Sahelian) gauge. The Conecuh
   is not a second subject: it is the contrasting climatic regime that makes the methodological comparison
   below meaningful. A result obtained on one river is an anecdote; the same
   comparison run on a Sahelian and a humid-subtropical river, with the same
   unmodified code, is evidence.

2. THE COMPARISON. The annual cycle in a monthly river record has to be
   removed before an ARIMA model can be identified, and there are two
   classical ways of doing it: differencing at lag 12, X(t) - X(t-12), and
   seasonal standardisation, z = (X(t) - m_month) / s_month. Textbooks present
   both; neither is usually preferred on evidence. This pipeline fits BOTH to
   BOTH rivers and judges them on six criteria that matter for the purpose at
   hand -- generating a long synthetic record for design -- rather than on
   goodness of fit to the observed record alone.

   The information criteria of the two branches are deliberately NOT compared.
   They are computed on different transformations of the series and are not
   commensurable; saying so is part of the result, not an omission.

Validation is stochastic and property-based: each fitted model generates an
ensemble of synthetic monthly sequences and validation compares the
DISTRIBUTION of hydrological summary statistics across that ensemble to the
historical record, rather than scoring one realisation against the one
sequence that happened to occur.

Run:
    python run_pipeline.py
"""

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from src.preprocess import (build_basin_monthly, split_basin_monthly, BASINS,
                            PRIMARY_BASIN, CONTRAST_BASIN, seasonal_profile,
                            deseasonalise, log_transform,
                            HADEJIA_OFFSET_FRACTION)
from src.calibrate import select_order, choose_differencing, seasonal_strength
from src.forecast import residual_diagnostics
from src.simulate import generate_synthetic_record, simulate_ensemble
from src.validation import compare_ensemble_to_historical, series_properties
from src.model import SEASONAL_PERIOD, seasonal_difference

RESULTS_FILE = Path(__file__).parent / "data" / "results.json"

# Which basin supplies which variables. The Nigerian gauge records discharge
# only; rainfall and stage stay on the contrast basin, where they serve the
# same purpose they always did -- showing that the procedure is indifferent to
# what the series measures.
PRIMARY_VARIABLES = ["discharge"]
CONTRAST_VARIABLES = ["discharge", "rainfall", "stage"]

UNITS = {"discharge": "m3/s", "rainfall": "mm/month", "stage": "m"}
N_REPS = 1000
SEED = 42

# Length of the synthetic record generated for the design application, and the
# return periods read off it. A specific number is needed for a worked
# example; the software itself accepts any.
RECORD_YEARS = 1000
RECORD_REPS = 50
RETURN_PERIODS = [2, 5, 10, 25, 50, 100, 500]

# Innovations are resampled from the model's own residuals rather than drawn
# from a Normal distribution. Jarque-Bera rejects normality decisively for the
# Hadejia residuals, and the extremes of the generated record are the numbers a
# design calculation reads off it, so the shape of the innovation distribution
# matters more here than it would for a mean forecast.
INNOVATIONS = "bootstrap"

# Stationarity margin imposed on order selection (see calibrate.select_order).
# The model exists to generate a record forty times longer than the one it was
# fitted to, so a candidate whose autoregressive roots sit on the unit circle
# is inadmissible however well it scores on AIC.
MIN_AR_ROOT = 1.05


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def design_summary(record: np.ndarray, months: np.ndarray,
                   period: int = SEASONAL_PERIOD) -> dict:
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
            out[k] = None if not np.isfinite(v) else round(v, nd)
        elif isinstance(v, dict):
            out[k] = round_dict(v, nd)
        elif isinstance(v, list):
            out[k] = [round(x, nd) if isinstance(x, float) else x for x in v]
        else:
            out[k] = v
    return out


def _decade_trajectory(record: np.ndarray, n_points: int = 100) -> list:
    """
    Mean level of a generated record in each of n_points equal blocks, so the
    two branches can be plotted against each other over the whole thousand
    years rather than compared only at their ends. Reported on the natural
    scale where that is finite and clipped to the floating-point range where
    it is not, since the point of the plot is precisely that one branch leaves
    that range and the other does not.
    """
    r = np.asarray(record, dtype=float)
    n = r.shape[-1]
    block = max(1, n // n_points)
    usable = r[..., :block * n_points]
    with np.errstate(over="ignore", invalid="ignore"):
        means = usable.reshape(r.shape[0], n_points, block).mean(axis=2).mean(axis=0)
    means = np.nan_to_num(means, nan=0.0, posinf=1e300, neginf=0.0)
    return [float(f"{v:.6g}") for v in means]


def monthly_sd_spread(values: np.ndarray, months: np.ndarray) -> dict:
    """
    How unequal the twelve calendar months are in variability, after a
    deseasonalising transform has been applied.

    This is the criterion the two treatments part company on. Both remove the
    annual cycle in the MEAN. Only standardisation removes it from the
    VARIANCE, because only standardisation divides by a per-month standard
    deviation. On a river whose dry-season flow is four times as variable
    (on the log scale) as its wet-season flow, what differencing leaves behind
    is a residual series that is still visibly seasonal in spread, which
    violates the constant-variance assumption the ARIMA model rests on.
    """
    v = np.asarray(values, dtype=float)
    m = np.asarray(months, dtype=int)
    sds = np.array([v[m == k].std(ddof=1) for k in range(1, SEASONAL_PERIOD + 1)])
    finite = sds[np.isfinite(sds) & (sds > 0)]
    return {
        "by_month": round_list(sds, 4),
        "min": float(finite.min()) if finite.size else None,
        "max": float(finite.max()) if finite.size else None,
        "ratio": float(finite.max() / finite.min()) if finite.size else None,
    }


# ---------------------------------------------------------------------------
# the two deseasonalising treatments, fitted and judged side by side
# ---------------------------------------------------------------------------
def compare_deseasonalising_methods(df: pd.DataFrame, basin: str,
                                    variable: str) -> dict:
    """
    Fit the same series twice -- once with the annual cycle removed by
    seasonal standardisation, once with it removed by differencing at lag 12 --
    and report the six criteria that separate them.

    Criteria
    --------
    1. cycle removal      : share of variance still carried by the mean annual
                            cycle after the transform, and the autocorrelation
                            at lag 12.
    2. residual whiteness : Ljung-Box on the fitted model's residuals.
    3. seasonal variance  : how unequal the twelve monthly standard deviations
                            of the transformed series still are.
    4. generator stability: what a 1000-year synthetic record does. This is the
                            criterion the purpose of the study turns on.
    5. scale fidelity     : mean of the generated record against the observed
                            mean.
    6. parameter cost     : how many numbers each treatment needs to carry the
                            seasonality.

    AIC values are reported within each branch and never across them; the two
    branches model different transformations of the series and their
    likelihoods are not on a common footing.
    """
    offset = float(df.attrs.get("log_offset", 0.0))
    y = df["log_value"].to_numpy()
    months = df.index.month.to_numpy()
    observed_mean = float(df["value"].mean())

    out = {"basin": basin, "variable": variable,
           "observed_mean": round(observed_mean, 4),
           "record_years_generated": RECORD_YEARS}

    # -- before any treatment -------------------------------------------------
    raw_season = seasonal_strength(y)
    out["untreated"] = {
        "seasonal_strength": round(float(raw_season["strength"]), 4),
        "acf_at_lag12": round(float(raw_season["acf_at_period"]), 4),
        "monthly_sd_spread": monthly_sd_spread(y, months),
    }

    # -- Treatment A: seasonal standardisation --------------------------------
    profile = seasonal_profile(y, months)
    z = deseasonalise(y, months, profile)
    z_season = seasonal_strength(z)
    order_s, model_s, table_s, _ = select_order(
        z, p_range=range(0, 5), q_range=range(0, 3), d_values=(0,), D=0,
        min_ar_root=MIN_AR_ROOT)
    diag_s = residual_diagnostics(model_s)
    record_s, months_s = generate_synthetic_record(
        model_s, RECORD_YEARS, profile, n_reps=20, method=INNOVATIONS,
        seed=SEED, start_month=1, y_hist=z, offset=offset)

    out["standardisation"] = {
        "label": model_s.label(),
        "order": list(order_s),
        "aic": round(float(model_s.aic_c), 2),
        "seasonal_strength_after": round(float(z_season["strength"]), 6),
        "acf_at_lag12_after": round(float(z_season["acf_at_period"]), 4),
        "monthly_sd_spread": monthly_sd_spread(z, months),
        "ljung_box_pvalue": round(float(diag_s["ljung_box"]["pvalue"]), 4),
        "arch_pvalue": round(float(diag_s["arch"]["pvalue"]), 4),
        "min_ar_root": round(float(min(diag_s["roots"]["ar"]))
                             if diag_s["roots"]["ar"] else float("inf"), 4),
        "n_seasonal_parameters": 2 * SEASONAL_PERIOD,
        "observations_consumed_by_transform": 0,
        "record_mean": round(float(record_s.mean()), 4),
        "record_max": round(float(record_s.max()), 2),
        "record_mean_over_observed": round(float(record_s.mean()) / observed_mean, 4),
        "first_decade_mean": round(float(record_s[:, :120].mean()), 4),
        "last_decade_mean": round(float(record_s[:, -120:].mean()), 4),
        "drift_ratio": round(float(record_s[:, -120:].mean()
                                   / record_s[:, :120].mean()), 4),
        "decade_mean_trajectory": _decade_trajectory(record_s),
        "usable_as_generator": True,
    }

    # -- Treatment B: differencing at lag 12 ----------------------------------
    diff_info = choose_differencing(y)
    D = max(int(diff_info["D"]), 1)
    w = seasonal_difference(y, D)
    w_months = months[D * SEASONAL_PERIOD:]
    w_season = seasonal_strength(w)
    order_d, model_d, table_d, _ = select_order(
        y, p_range=range(0, 5), q_range=range(0, 3), D=D)
    diag_d = residual_diagnostics(model_d)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        log_trace = simulate_ensemble(
            model_d, y, RECORD_YEARS * SEASONAL_PERIOD, n_reps=20,
            method="gaussian", seed=SEED)
    # The level-scale record overflows the floating-point range for this
    # branch, so the drift is measured on the log scale as well, where it is
    # always finite and is the honest statement of the problem: the mean of
    # the generated log-flow walks away from its starting value instead of
    # fluctuating about it.
    with np.errstate(divide="ignore", invalid="ignore"):
        log_first = float(np.log(np.maximum(log_trace[:, :120], 1e-300)).mean())
        log_last = float(np.log(np.maximum(log_trace[:, -120:], 1e-300)).mean())
        lvl_first = float(log_trace[:, :120].mean())
        lvl_last = float(log_trace[:, -120:].mean())
        drift = lvl_last / lvl_first if np.isfinite(lvl_last) and lvl_first else float("inf")

    out["seasonal_differencing"] = {
        "label": model_d.label(),
        "order": list(order_d),
        "seasonal_order": list(model_d.seasonal_order),
        "D": int(D),
        "aic": round(float(model_d.aic_c), 2),
        "seasonal_strength_after": round(float(w_season["strength"]), 6),
        "acf_at_lag12_after": round(float(w_season["acf_at_period"]), 4),
        "monthly_sd_spread": monthly_sd_spread(w, w_months),
        "ljung_box_pvalue": round(float(diag_d["ljung_box"]["pvalue"]), 4),
        "arch_pvalue": round(float(diag_d["arch"]["pvalue"]), 4),
        "Theta": round_list(model_d.Theta),
        "n_seasonal_parameters": int(len(model_d.Theta)),
        "observations_consumed_by_transform": int(D * SEASONAL_PERIOD),
        "record_mean": None if not np.isfinite(lvl_last) else round(float(np.nanmean(log_trace)), 4),
        "record_mean_scientific": f"{np.nanmean(log_trace):.3g}",
        "first_decade_mean": float(f"{lvl_first:.6g}"),
        "last_decade_mean_scientific": f"{lvl_last:.3g}",
        "drift_ratio_scientific": f"{drift:.3g}",
        "log_scale_first_decade_mean": round(log_first, 4),
        "log_scale_last_decade_mean": round(log_last, 4),
        "decade_mean_trajectory": _decade_trajectory(log_trace),
        "usable_as_generator": False,
    }
    return out


def offset_sensitivity(df: pd.DataFrame, fractions=(0.0, 0.002, 0.005, 0.01,
                                                    0.02, 0.04)) -> list:
    """
    How much of the answer rests on the constant added before the log
    transform, for a river whose dry-season monthly means reach zero.

    Reported so that the choice of one per cent of the mean
    flow is visibly a convention with a measured consequence, not a tuned
    parameter.
    """
    values = df["value"].to_numpy()
    months = df.index.month.to_numpy()
    positive_mean = float(values[values > 0].mean())
    rows = []
    for frac in fractions:
        c = frac * positive_mean
        y = log_transform(values, offset=c)
        profile = seasonal_profile(y, months)
        z = deseasonalise(y, months, profile)
        order, model, _, _ = select_order(
            z, p_range=range(0, 5), q_range=range(0, 3), d_values=(0,), D=0,
            min_ar_root=MIN_AR_ROOT)
        diag = residual_diagnostics(model)
        record, rec_months = generate_synthetic_record(
            model, RECORD_YEARS, profile, n_reps=10, method=INNOVATIONS,
            seed=SEED, start_month=1, y_hist=z, offset=c)
        design = design_summary(record, rec_months)
        rows.append({
            "offset_fraction_of_mean": frac,
            "offset": round(c, 4),
            "label": model.label(),
            "monthly_sd_ratio": round(max(profile["sds"]) / min(profile["sds"]), 3),
            "ljung_box_pvalue": round(float(diag["ljung_box"]["pvalue"]), 4),
            "record_mean": round(design["mean"], 2),
            "T2": round(design["return_period_discharge"]["2"], 1),
            "T10": round(design["return_period_discharge"]["10"], 1),
            "T100": round(design["return_period_discharge"]["100"], 1),
            "T500": round(design["return_period_discharge"]["500"], 1),
        })
    return rows


# ---------------------------------------------------------------------------
# one basin, one variable
# ---------------------------------------------------------------------------
def run_variable(basin: str, variable: str) -> tuple:
    meta = BASINS[basin]
    print(f"\n{'=' * 72}\n  {meta['short_name']}  --  {variable.upper()} "
          f"({UNITS[variable]})\n{'=' * 72}")

    df = build_basin_monthly(basin, variable)
    train, valid = split_basin_monthly(df, basin)
    offset = float(df.attrs.get("log_offset", 0.0))
    print(f"  Full record : {df.index[0].date()} to {df.index[-1].date()}  "
          f"({len(df)} months, {df.attrs['n_fully_missing_months']} interpolated)")
    print(f"  Training    : {train.index[0].date()} to {train.index[-1].date()}  "
          f"({len(train)} months)")
    print(f"  Validation  : {valid.index[0].date()} to {valid.index[-1].date()}  "
          f"({len(valid)} months)")
    if offset:
        print(f"  Log offset  : {offset:.4f} {UNITS[variable]} "
              f"({HADEJIA_OFFSET_FRACTION:.0%} of mean flow)")

    y_train = train["log_value"].to_numpy()
    months_train = train.index.month.to_numpy()

    profile = seasonal_profile(y_train, months_train)
    z_train = deseasonalise(y_train, months_train, profile)
    print(f"  Seasonal profile: {SEASONAL_PERIOD} monthly means, log-scale range "
          f"{min(profile['means']):.2f} to {max(profile['means']):.2f}; "
          f"monthly SD ratio {max(profile['sds']) / min(profile['sds']):.2f}")

    order, model, table, diff_info = select_order(
        z_train, p_range=range(0, 5), q_range=range(0, 3), d_values=(0,), D=0,
        min_ar_root=MIN_AR_ROOT)
    d = diff_info["d"] if diff_info else 0
    stationarity_train = choose_differencing(z_train)
    se = model.standard_errors()
    print(f"  Selected {model.label()}  |  AIC={model.aic_c:.1f} BIC={model.bic_c:.1f}"
          f"  |  smallest AR root {min(model.roots()['ar']) if model.roots()['ar'] else float('inf'):.3f}")
    print(f"  phi   = {np.round(model.phi, 4).tolist()}  (se: {[round(x, 4) for x in se['phi']]})")
    print(f"  theta = {np.round(model.theta, 4).tolist()}  (se: {[round(x, 4) for x in se['theta']]})")

    diag = residual_diagnostics(model)
    lb = diag["ljung_box"]
    print(f"  Ljung-Box(20) p={lb['pvalue']:.4f}  |  ARCH p={diag['arch']['pvalue']:.4f}"
          f"  |  Jarque-Bera p={diag['jarque_bera']['pvalue']:.3g}")

    ens_valid, _ = generate_synthetic_record(
        model, n_years=0, profile=profile, n_reps=N_REPS, method=INNOVATIONS,
        seed=SEED, start_month=int(valid.index[0].month),
        n_periods=len(valid), offset=offset)
    val_summary = compare_ensemble_to_historical(
        valid["value"].to_numpy(), valid.index, ens_valid, valid.index)
    n_ok = val_summary["_n_properties_within_envelope"]
    n_tot = val_summary["_n_properties_total"]
    print(f"  Property-based validation: {n_ok}/{n_tot} statistics fall within "
          f"the synthetic ensemble's 90% envelope")

    # -- the operational output: a long synthetic record for design ----------
    y_full = df["log_value"].to_numpy()
    months_full = df.index.month.to_numpy()
    profile_full = seasonal_profile(y_full, months_full)
    z_full = deseasonalise(y_full, months_full, profile_full)
    stationarity_full = choose_differencing(z_full)
    order_full, model_full, _, _ = select_order(
        z_full, p_range=range(0, 5), q_range=range(0, 3), d_values=(0,), D=0,
        min_ar_root=MIN_AR_ROOT)

    record, rec_months = generate_synthetic_record(
        model_full, RECORD_YEARS, profile_full, n_reps=RECORD_REPS,
        method=INNOVATIONS, seed=SEED, start_month=1, y_hist=z_full,
        offset=offset)
    design = design_summary(record, rec_months)
    long_trace_props = series_properties(record[0], pd.date_range(
        "2015-01-01", periods=record.shape[1], freq="MS"))
    hist_full_props = series_properties(df["value"].to_numpy(), df.index)
    print(f"  Synthetic record: {RECORD_YEARS} yr x {RECORD_REPS} traces  "
          f"mean={design['mean']:.2f} (observed {hist_full_props['mean']:.2f})  "
          f"drift={design['drift_ratio']:.3f}")
    print("  Return periods : " + "  ".join(
        f"{T}yr {design['return_period_discharge'][str(T)]:.0f}"
        for T in RETURN_PERIODS))

    artifacts = {
        "basin": basin, "variable": variable, "meta": meta,
        "df": df, "train": train, "valid": valid,
        "model": model, "w_train": z_train, "d": d, "profile": profile,
        "ens_valid": ens_valid, "val_summary": val_summary,
        "record": record, "design": design,
    }

    summary = {
        "basin": basin,
        "basin_name": meta["name"],
        "unit": UNITS[variable],
        "n_months": int(len(df)),
        "n_interpolated_months": int(df.attrs["n_fully_missing_months"]),
        "log_offset": round(offset, 6),
        "record_period": [str(df.index[0].date()), str(df.index[-1].date())],
        "train_period": [str(train.index[0].date()), str(train.index[-1].date())],
        "valid_period": [str(valid.index[0].date()), str(valid.index[-1].date())],
        "differencing_d": d,
        "seasonal_period": SEASONAL_PERIOD,
        "seasonal_profile": {
            "means": round_list(profile["means"]),
            "sds": round_list(profile["sds"]),
            "period": profile["period"],
        },
        "stationarity_report": [
            {"d": r["d"],
             "adf_stat": round(r["adf"]["stat"], 4),
             "adf_stationary": r["adf"]["stationary_5pct"],
             "kpss_stat": round(r["kpss"]["stat"], 4),
             "kpss_stationary": r["kpss"]["stationary_5pct"]}
            for r in stationarity_train["report"]
        ],
        "order": list(order),
        "seasonal_order": list(model.seasonal_order),
        "label": model.label(),
        "aic": round(model.aic_c, 2),
        "bic": round(model.bic_c, 2),
        "phi": round_list(model.phi),
        "theta": round_list(model.theta),
        "constant": round(float(model.c), 6),
        "min_ar_root_constraint": MIN_AR_ROOT,
        "standard_errors": {
            "c": round(se["c"], 6) if np.isfinite(se["c"]) else None,
            "phi": [round(x, 6) if np.isfinite(x) else None for x in se["phi"]],
            "theta": [round(x, 6) if np.isfinite(x) else None for x in se["theta"]],
        },
        "aic_ranking": [
            {"order": list(r["order"]), "label": r["label"],
             "aic": round(r["aic"], 2), "bic": round(r["bic"], 2),
             "min_ar_root": round(r["min_ar_root"], 3)
             if np.isfinite(r["min_ar_root"]) else None,
             "admissible": r["stationary_margin_ok"]}
            for r in table[:8]
        ],
        "diagnostics": {
            "ljung_box": {"stat": round(lb["stat"], 3), "pvalue": round(lb["pvalue"], 4)},
            "arch": {"stat": round(diag["arch"]["stat"], 3),
                     "pvalue": round(diag["arch"]["pvalue"], 4)},
            "jarque_bera": round_dict(diag["jarque_bera"]),
            "roots": {"ar": [round(x, 3) for x in diag["roots"]["ar"]],
                      "ma": [round(x, 3) for x in diag["roots"]["ma"]]},
            "smearing_factor": round(diag["smearing_factor"], 4),
        },
        "historical_stats": round_dict(series_properties(train["value"].to_numpy(),
                                                         train.index)),
        "validation": round_dict({k: v for k, v in val_summary.items()
                                  if not k.startswith("_")}),
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
            "log_offset": round(offset, 6),
            "d_indicated_by_tests": stationarity_full["d"],
            "d_used": 0,
            "historical_properties": round_dict(hist_full_props),
            "long_trace_properties": round_dict(long_trace_props),
        },
        "synthetic_record": round_dict(design),
    }
    return summary, artifacts


# ---------------------------------------------------------------------------
def main():
    primary_meta = BASINS[PRIMARY_BASIN]
    contrast_meta = BASINS[CONTRAST_BASIN]
    print("=" * 72)
    print("  SYNTHETIC MONTHLY RECORD GENERATION FOR DESIGN DISCHARGE")
    print(f"  Case study : {primary_meta['name']}")
    print(f"               GRDC {primary_meta['grdc_id']} / GSIM {primary_meta['gsim_id']}"
          f", {primary_meta['area_km2']:,.0f} km2")
    print(f"  Contrast   : {contrast_meta['name']} (USGS {contrast_meta['usgs_id']})")
    print("  Comparison : seasonal standardisation vs differencing at lag 12")
    print("=" * 72)

    out = {
        "case_study_basin": {**primary_meta, "role": "primary"},
        "contrast_basin": {**contrast_meta, "role": "contrast"},
        "basin": f"{primary_meta['name']} (GRDC {primary_meta['grdc_id']})",
        "gauge_id": primary_meta["grdc_id"],
        "timestep": "monthly",
        "min_ar_root_constraint": MIN_AR_ROOT,
        "record_years": RECORD_YEARS,
        "record_reps": RECORD_REPS,
        "innovations": INNOVATIONS,
        "variables": {},
        "contrast_variables": {},
        "method_comparison": {},
    }
    artifacts = {"primary": {}, "contrast": {}}

    for v in PRIMARY_VARIABLES:
        summary, art = run_variable(PRIMARY_BASIN, v)
        out["variables"][v] = summary
        artifacts["primary"][v] = art

    for v in CONTRAST_VARIABLES:
        summary, art = run_variable(CONTRAST_BASIN, v)
        out["contrast_variables"][v] = summary
        artifacts["contrast"][v] = art

    # ---- the head-to-head that makes the study original -------------------
    print(f"\n{'=' * 72}\n  DESEASONALISATION COMPARISON: STANDARDISATION vs "
          f"DIFFERENCING AT LAG 12\n{'=' * 72}")
    for basin in (PRIMARY_BASIN, CONTRAST_BASIN):
        df = build_basin_monthly(basin, "discharge")
        cmp_ = compare_deseasonalising_methods(df, basin, "discharge")
        out["method_comparison"][basin] = cmp_
        s, dd = cmp_["standardisation"], cmp_["seasonal_differencing"]
        print(f"\n  {BASINS[basin]['short_name']}")
        print(f"    cycle share of variance, untreated   : "
              f"{cmp_['untreated']['seasonal_strength']:.3f}")
        print(f"    after standardisation / differencing : "
              f"{s['seasonal_strength_after']:.4f} / {dd['seasonal_strength_after']:.4f}")
        print(f"    leftover monthly-SD ratio            : "
              f"{s['monthly_sd_spread']['ratio']:.2f} / {dd['monthly_sd_spread']['ratio']:.2f}")
        print(f"    Ljung-Box p                          : "
              f"{s['ljung_box_pvalue']:.4f} / {dd['ljung_box_pvalue']:.4f}")
        print(f"    {RECORD_YEARS}-yr record mean (observed {cmp_['observed_mean']:.2f}) : "
              f"{s['record_mean']:.2f} / {dd['record_mean_scientific']}")
        print(f"    drift over the record                : "
              f"{s['drift_ratio']:.3f} / {dd['drift_ratio_scientific']}")

    # ---- how much rests on the log offset ---------------------------------
    print(f"\n{'=' * 72}\n  SENSITIVITY TO THE LOG OFFSET (Hadejia)\n{'=' * 72}")
    df_primary = build_basin_monthly(PRIMARY_BASIN, "discharge")
    out["offset_sensitivity"] = offset_sensitivity(df_primary)
    hdr = f"  {'frac':>6} {'c':>7} {'model':>16} {'SDratio':>8} {'LB p':>7} " \
          f"{'mean':>7} {'T2':>7} {'T10':>7} {'T100':>8} {'T500':>8}"
    print(hdr)
    for r in out["offset_sensitivity"]:
        print(f"  {r['offset_fraction_of_mean']:>6.3f} {r['offset']:>7.3f} "
              f"{r['label']:>16} {r['monthly_sd_ratio']:>8.2f} "
              f"{r['ljung_box_pvalue']:>7.4f} {r['record_mean']:>7.2f} "
              f"{r['T2']:>7.1f} {r['T10']:>7.1f} {r['T100']:>8.1f} {r['T500']:>8.1f}")

    RESULTS_FILE.parent.mkdir(exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nResults saved to {RESULTS_FILE}")

    print("\nGenerating figures...")
    from src.plots import build_figures
    for f in build_figures(artifacts, out):
        print(f"  saved {Path(f).name}")

    print("\n" + "=" * 72)
    print("  SUMMARY")
    print("=" * 72)
    r = out["variables"]["discharge"]
    sr = r["synthetic_record"]
    print(f"  Case study : {primary_meta['short_name']}  {r['label']}")
    print(f"               validation {r['validation_n_within']}/{r['validation_n_total']}"
          f" properties within envelope; {RECORD_YEARS}-yr record mean "
          f"{sr['mean']:.2f} vs observed "
          f"{r['full_record']['historical_properties']['mean']:.2f}")
    print(f"               design discharges  " + "  ".join(
        f"{T}yr {sr['return_period_discharge'][str(T)]:.0f}" for T in RETURN_PERIODS))
    for v in CONTRAST_VARIABLES:
        c = out["contrast_variables"][v]
        print(f"  Contrast   : {v:10s} {c['label']:22s} "
              f"validation {c['validation_n_within']}/{c['validation_n_total']}")
    print("=" * 72)
    return out


if __name__ == "__main__":
    main()
