"""
validation.py — Property-based (stochastic) validation.

Added 2026-08-12, replacing point-forecast-vs-observed comparison per
supervisor instruction: "we don't need the answers to be the same. We just
need the properties of the things you forecasted to be similar to the
original... it's the variability that we want to see, not the exact value...
[for] sizing reservoirs, sizing spillways."

Rather than scoring one forecast against the one sequence that happened to
follow, this module characterises the historical record by a set of
hydrologically meaningful summary statistics, characterises every member of a
synthetic ensemble (see simulate.py) the same way, and reports whether the
historical value falls inside the ensemble's spread -- i.e. whether the model
reproduces the right VARIABILITY, not the right trajectory.
"""

import numpy as np
import pandas as pd

from .model import acf


def series_properties(values: np.ndarray, dates=None) -> dict:
    """
    Summary statistics for one monthly series (historical or one synthetic
    realisation).

    mean, std, skew         : first three moments
    lag1_acf                : month-to-month persistence
    seasonal_amplitude      : range of the 12 calendar-month means (needs
                               `dates`; measures how strongly seasonal the
                               series is). This is the property the
                               timestep argument is really about -- note
                               that ordinary differencing does not remove an
                               annual cycle anyway (that needs X(t)-X(t-12)
                               or SARIMA), so this statistic checks whether
                               the AR/MA structure reproduces the seasonality
                               on its own.
    max_dry_spell           : longest run of months below the 20th
                               percentile of the series itself (a drought /
                               low-flow duration proxy)
    peak                    : maximum monthly value
    """
    v = np.asarray(values, dtype=float)
    n = len(v)
    vc = v - v.mean()
    props = {
        "mean": float(v.mean()),
        "std": float(v.std(ddof=1)) if n > 1 else float("nan"),
        "skew": float(np.mean(vc ** 3) / (np.mean(vc ** 2) ** 1.5 + 1e-12)),
        "lag1_acf": float(acf(v, nlags=1)[1]),
        "peak": float(v.max()),
    }

    thresh = np.percentile(v, 20)
    below = v < thresh
    run = max_run = 0
    for b in below:
        run = run + 1 if b else 0
        max_run = max(max_run, run)
    props["max_dry_spell_months"] = int(max_run)

    if dates is not None:
        s = pd.Series(v, index=pd.to_datetime(dates))
        seasonal_means = s.groupby(s.index.month).mean()
        props["seasonal_amplitude"] = float(seasonal_means.max() - seasonal_means.min())
        props["seasonal_means"] = {int(m): float(x) for m, x in seasonal_means.items()}

    return props


PROPERTY_KEYS = ["mean", "std", "skew", "lag1_acf", "max_dry_spell_months", "peak",
                  "seasonal_amplitude"]


def compare_ensemble_to_historical(hist_values: np.ndarray, hist_dates,
                                    ensemble: np.ndarray, ensemble_dates=None) -> dict:
    """
    Compare one historical series to an ensemble of synthetic realisations
    (rows of `ensemble`, same length as hist_values).

    For each property, reports the historical value, the ensemble's median
    and 90% envelope (5th-95th percentile across realisations), and whether
    the historical value falls inside that envelope -- the pass/fail
    criterion for "the model reproduces the right variability".
    """
    hist_props = series_properties(hist_values, hist_dates)
    ens_dates = ensemble_dates if ensemble_dates is not None else hist_dates
    ens_props = [series_properties(row, ens_dates) for row in ensemble]

    summary = {}
    for key in PROPERTY_KEYS:
        if key not in hist_props:
            continue
        ens_vals = np.array([ep[key] for ep in ens_props if key in ep])
        lo, hi = np.percentile(ens_vals, [5, 95])
        med = float(np.median(ens_vals))
        h = hist_props[key]
        summary[key] = {
            "historical": h,
            "ensemble_median": med,
            "ensemble_p5": float(lo),
            "ensemble_p95": float(hi),
            "within_90pct_envelope": bool(lo <= h <= hi),
        }

    n_within = sum(1 for v in summary.values() if v["within_90pct_envelope"])
    n_total = len(summary)
    summary["_n_properties_within_envelope"] = n_within
    summary["_n_properties_total"] = n_total
    return summary


if __name__ == "__main__":
    from .preprocess import build_monthly_dataset, split_monthly
    from .calibrate import select_order
    from .simulate import simulate_ensemble

    df = build_monthly_dataset("discharge")
    train, valid = split_monthly(df)
    order, model, table, diff_info = select_order(train["log_value"].to_numpy())

    ens = simulate_ensemble(model, train["log_value"].to_numpy(), len(valid),
                             n_reps=300, seed=42)
    summary = compare_ensemble_to_historical(
        valid["value"].to_numpy(), valid.index, ens, valid.index
    )
    n_total = len(summary) - 2  # minus the two summary counter keys
    print(f"Properties within the 90% synthetic envelope: "
          f"{summary['_n_properties_within_envelope']}/{n_total}")
    for k, v in summary.items():
        if k.startswith("_"):
            continue
        flag = "OK" if v["within_90pct_envelope"] else "MISS"
        print(f"  [{flag}] {k:22s} hist={v['historical']:.3f}  "
              f"ensemble=[{v['ensemble_p5']:.3f}, {v['ensemble_p95']:.3f}]  "
              f"median={v['ensemble_median']:.3f}")
