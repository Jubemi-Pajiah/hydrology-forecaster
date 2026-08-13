"""
cross_basin_check.py — Supplementary cross-basin transferability check.

Added 2026-08-13 in direct response to independent review feedback (raised
twice, by name, across two rounds of critical review): the thesis claimed the
framework "transfers to any basin... demonstrated here directly" while having
tested exactly one basin. That claim was not earned. This script runs the
same identification + estimation procedure (Section 3.5) on two additional
CAMELS basins, chosen from climate regimes distinct from the primary
Conecuh basin (humid subtropical, Alabama):

  - USGS 10023000, Great Basin (arid interior West, Nevada/Utah region)
  - USGS 01013500, New England (humid continental, snow-influenced)

Scope, stated honestly: this is a supplementary check, not a full
replication. It runs discharge and rainfall (not stage, which would require
a live NWIS pull per basin) through stationarity testing and order
selection, and reports whether the qualitative pattern found at Conecuh
(strong AR persistence for discharge, weak/insignificant persistence for
rainfall) holds. It does not repeat the full stochastic-ensemble
property-based validation for these two basins -- that remains future work
(see Chapter 5).

Run:
    python cross_basin_check.py
Output: data/cross_basin_check.json
"""

import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from src.calibrate import select_order
from src.forecast import residual_diagnostics
from src.preprocess import log_transform

PROJECT_ROOT = Path(__file__).parent
ZIP_PATH = PROJECT_ROOT / "basin_timeseries_v1p2_metForcing_obsFlow.zip"
OUT_PATH = PROJECT_ROOT / "data" / "cross_basin_check.json"

BASINS = [
    {"id": "10023000", "region": "16", "label": "Great Basin (arid interior West)",
     "start": "1986-10-01", "end": "2014-12-31"},
    {"id": "01013500", "region": "01", "label": "New England (humid continental, snow-influenced)",
     "start": "1980-01-01", "end": "2014-12-31"},
]


def load_discharge_monthly(z, basin, region, start, end):
    path = f"basin_dataset_public_v1p2/usgs_streamflow/{region}/{basin}_streamflow_qc.txt"
    raw = z.read(path).decode("utf-8", "replace")
    df = pd.read_csv(io.StringIO(raw), sep=r"\s+", header=None,
                     names=["id", "year", "month", "day", "flow_cfs", "qc"])
    df["date"] = pd.to_datetime(df[["year", "month", "day"]])
    df = df.set_index("date").sort_index()
    df["flow_cfs"] = df["flow_cfs"].replace(-999.0, np.nan)
    flow = (df["flow_cfs"] * 0.0283168).interpolate(method="time", limit_direction="both")
    full_idx = pd.date_range(start, end, freq="D")
    flow = flow.reindex(full_idx)
    monthly = flow.resample("MS").mean()
    monthly = monthly.interpolate(method="time", limit_direction="both")
    return monthly


def load_rainfall_monthly(z, basin, region, start, end):
    path = f"basin_dataset_public_v1p2/basin_mean_forcing/daymet/{region}/{basin}_lump_cida_forcing_leap.txt"
    raw = z.read(path).decode("utf-8", "replace")
    lines = raw.splitlines()
    body = "\n".join(lines[3:])
    fdf = pd.read_csv(io.StringIO(body), sep=r"\s+")
    fdf.columns = [c.lower() for c in fdf.columns]
    fdf["date"] = pd.to_datetime(dict(year=fdf["year"], month=fdf["mnth"], day=fdf["day"]))
    fdf = fdf.set_index("date").sort_index()
    prcp_col = [c for c in fdf.columns if "prcp" in c][0]
    prcp = fdf[prcp_col]
    full_idx = pd.date_range(start, end, freq="D")
    prcp = prcp.reindex(full_idx)
    monthly = prcp.resample("MS").sum()
    return monthly


def fit_and_summarize(monthly_series, label):
    y = log_transform(monthly_series.to_numpy())
    n = len(y)
    train = y[: int(n * 0.7)]

    order, model, table, diff_info = select_order(train, p_range=range(0, 5), q_range=range(0, 3))
    d = diff_info["d"]
    se = model.standard_errors()
    diag = residual_diagnostics(model)

    return {
        "label": label,
        "n_train_months": len(train),
        "order": list(order),
        "d": d,
        "phi": np.round(model.phi, 4).tolist(),
        "phi_se": [round(x, 4) if x is not None and np.isfinite(x) else None for x in se["phi"]],
        "theta": np.round(model.theta, 4).tolist(),
        "aic": round(model.aic_c, 2),
        "ljung_box_pvalue": round(diag["ljung_box"]["pvalue"], 4),
        "phi1_significant": bool(se["phi"] and se["phi"][0] and np.isfinite(se["phi"][0])
                                 and abs(model.phi[0]) > 1.96 * se["phi"][0]) if model.phi.size else None,
    }


def main():
    z = zipfile.ZipFile(ZIP_PATH)
    results = {}
    for b in BASINS:
        print(f"\n{'='*60}\n  {b['id']} — {b['label']}\n{'='*60}")
        discharge_m = load_discharge_monthly(z, b["id"], b["region"], b["start"], b["end"])
        rainfall_m = load_rainfall_monthly(z, b["id"], b["region"], b["start"], b["end"])

        r_dis = fit_and_summarize(discharge_m, "discharge")
        r_rain = fit_and_summarize(rainfall_m, "rainfall")
        print(f"  discharge: ARIMA{tuple(r_dis['order'])}  phi1={r_dis['phi'][0] if r_dis['phi'] else None}  "
              f"significant={r_dis['phi1_significant']}  LB p={r_dis['ljung_box_pvalue']}")
        print(f"  rainfall : ARIMA{tuple(r_rain['order'])}  phi1={r_rain['phi'][0] if r_rain['phi'] else None}  "
              f"significant={r_rain['phi1_significant']}  LB p={r_rain['ljung_box_pvalue']}")

        results[b["id"]] = {
            "label": b["label"], "region_folder": b["region"],
            "record": [b["start"], b["end"]],
            "discharge": r_dis, "rainfall": r_rain,
        }

    OUT_PATH.parent.mkdir(exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved {OUT_PATH}")


if __name__ == "__main__":
    main()
