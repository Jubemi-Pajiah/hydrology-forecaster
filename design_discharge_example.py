"""
design_discharge_example.py — Illustrative reservoir/spillway design-discharge
worked example.

Added 2026-08-13 in direct response to review feedback (raised independently
in two rounds): "reservoir and spillway sizing" was invoked repeatedly as the
motivating design application for property-based validation, but never once
demonstrated with an actual calculation. This script provides one, using
tools already built for this project (src/simulate.py) rather than new
machinery: a large ensemble of synthetic 30-year discharge traces is
generated from the already-fitted, already-reported discharge model, annual
maximum monthly discharge is extracted from each trace, and empirical
return-period design discharges are read directly off the pooled
distribution -- the plotting-position approach to flood-frequency analysis
(Chow, Maidment & Mays, 2008), applied here to synthetic rather than
observed annual maxima, which is exactly the kind of design use a synthetic
ensemble is for.

This is explicitly illustrative, not a substitute for a real design study:
a real spillway design would use observed annual maxima (or a fitted
distribution such as Log-Pearson III) with a formal exceedance-probability
standard set by the responsible authority, cross-checked against several
methods. What this demonstrates is the mechanical step from "we have a
stochastic ensemble" to "here is a design number an engineer could start
from", which the thesis's own repeated invocation of reservoir/spillway
sizing had not, until now, actually shown.

Run:
    python design_discharge_example.py
Output: data/design_discharge_example.json
"""

import json
from pathlib import Path

import numpy as np

from src.preprocess import build_monthly_dataset
from src.model import ARIMA
from src.simulate import simulate_ensemble

PROJECT_ROOT = Path(__file__).parent
RESULTS_PATH = PROJECT_ROOT / "data" / "results.json"
OUT_PATH = PROJECT_ROOT / "data" / "design_discharge_example.json"

N_REPS = 500
TRACE_YEARS = 30
RETURN_PERIODS = [2, 5, 10, 25, 50, 100]


def main():
    R = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    r = R["variables"]["discharge"]
    df = build_monthly_dataset("discharge")

    model = ARIMA.from_params(tuple(r["order"]), r["constant"], r["phi"], r["theta"],
                              df["log_value"].to_numpy())

    horizon = TRACE_YEARS * 12
    ens = simulate_ensemble(model, df["log_value"].to_numpy(), horizon,
                            n_reps=N_REPS, method="gaussian", seed=None)
    # ens: (N_REPS, horizon) monthly discharge, m3/s

    # Annual maximum monthly discharge per synthetic year, pooled across all replicates
    annual_max = ens.reshape(N_REPS, TRACE_YEARS, 12).max(axis=2).flatten()
    print(f"Pooled synthetic annual maxima: n={len(annual_max)} "
          f"(from {N_REPS} traces x {TRACE_YEARS} years)")

    design_values = {}
    for T in RETURN_PERIODS:
        pct = 100 * (1 - 1 / T)
        design_values[str(T)] = round(float(np.percentile(annual_max, pct)), 2)
        print(f"  T={T:>3} yr  (P={100/T:.1f}% annual exceedance)  "
              f"design monthly-max discharge = {design_values[str(T)]:.1f} m3/s")

    hist_annual_max = df["value"].groupby(df.index.year).max()
    out = {
        "n_reps": N_REPS, "trace_years": TRACE_YEARS,
        "n_pooled_annual_maxima": len(annual_max),
        "design_discharge_m3s_by_return_period": design_values,
        "historical_annual_max_observed_mean": round(float(hist_annual_max.mean()), 2),
        "historical_annual_max_observed_max": round(float(hist_annual_max.max()), 2),
        "historical_annual_max_n_years": int(len(hist_annual_max)),
    }
    OUT_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nSaved {OUT_PATH}")
    print(f"For comparison, the observed record's {len(hist_annual_max)} annual "
          f"maxima average {out['historical_annual_max_observed_mean']:.1f} m3/s "
          f"and peak at {out['historical_annual_max_observed_max']:.1f} m3/s.")


if __name__ == "__main__":
    main()
