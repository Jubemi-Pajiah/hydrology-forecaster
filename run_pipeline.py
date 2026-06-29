"""
run_pipeline.py — End-to-end statistical streamflow-forecasting pipeline.

Basin : Conecuh River, Alabama, USA (USGS 02361000, CAMELS dataset)
Model : ARIMA(p, d, q) for log-discharge, identified by Box-Jenkins analysis
Input : observed daily discharge ONLY (no rainfall, no temperature, no PET)
Leads : 1-, 2- and 3-day ahead forecasts, benchmarked against persistence

Run:
    python run_pipeline.py
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from src.preprocess import build_dataset, split_dataset, TRAIN_END
from src.calibrate import select_order
from src.forecast import forecast_evaluation, residual_diagnostics
from src.model import difference, adf_test, kpss_test
from src.metrics import moriasi_rating

RESULTS_FILE = Path(__file__).parent / "data" / "results.json"


def main():
    print("=" * 68)
    print("  STATISTICAL STREAMFLOW FORECASTING PIPELINE")
    print("  Basin : Conecuh River, Alabama (USGS 02361000)")
    print("  Model : ARIMA(p,d,q) on log-discharge | input: discharge only")
    print("=" * 68)

    # ------------------------------------------------------------------
    # 1. Load observed discharge
    # ------------------------------------------------------------------
    print("\n[1/5] Loading observed discharge from CAMELS archive...")
    df = build_dataset()
    train, valid = split_dataset(df)
    print(f"  Full record : {df.index[0].date()} to {df.index[-1].date()}  ({len(df)} days)")
    print(f"  Training    : {train.index[0].date()} to {train.index[-1].date()}  ({len(train)} days)")
    print(f"  Validation  : {valid.index[0].date()} to {valid.index[-1].date()}  ({len(valid)} days)")
    print(f"  Discharge (m3/s): mean={df['flow'].mean():.2f}  min={df['flow'].min():.2f}  "
          f"max={df['flow'].max():.1f}  std={df['flow'].std():.2f}")

    y_train = train["log_flow"].to_numpy()

    # ------------------------------------------------------------------
    # 2. Stationarity testing
    # ------------------------------------------------------------------
    print("\n[2/5] Stationarity testing on training log-discharge...")
    adf0, kpss0 = adf_test(y_train), kpss_test(y_train)
    adf1 = adf_test(difference(y_train, 1))
    kpss1 = kpss_test(difference(y_train, 1))
    print(f"  Level    : ADF={adf0['stat']:.3f} (5% crit {adf0['crit']['5%']:.3f}) "
          f"-> {'stationary' if adf0['stationary_5pct'] else 'non-stationary'}; "
          f"KPSS={kpss0['stat']:.3f} (5% crit {kpss0['crit']['5%']})")
    print(f"  1st diff : ADF={adf1['stat']:.3f} (5% crit {adf1['crit']['5%']:.3f}) "
          f"-> {'stationary' if adf1['stationary_5pct'] else 'non-stationary'}; "
          f"KPSS={kpss1['stat']:.3f}")

    # ------------------------------------------------------------------
    # 3. Order selection (Box-Jenkins, AIC grid search)
    # ------------------------------------------------------------------
    print("\n[3/5] Identifying ARIMA order by AIC grid search...")
    order, model, table, diff_info = select_order(
        y_train, p_range=range(0, 5), q_range=range(0, 3))
    d = diff_info["d"]
    print(f"  Differencing order d = {d} (from ADF + KPSS)")
    print(f"  Selected model: ARIMA{order}")
    print(f"  AIC = {model.aic_c:.1f}   BIC = {model.bic_c:.1f}   sigma^2 = {model.sigma2:.5f}")
    print("  Candidate ranking (top 5 by AIC):")
    for r in table[:5]:
        print(f"    ARIMA{r['order']}: AIC={r['aic']:.1f}, BIC={r['bic']:.1f}")
    print(f"  AR coefficients : {np.round(model.phi, 4).tolist()}")
    print(f"  MA coefficients : {np.round(model.theta, 4).tolist()}")
    print(f"  Constant        : {model.c:.6f}")

    # ------------------------------------------------------------------
    # 4. Forecast evaluation (rolling origin, 1/2/3-day leads)
    # ------------------------------------------------------------------
    print("\n[4/5] Rolling-origin forecast evaluation over validation period...")
    log_full = df["log_flow"].to_numpy()
    flow_full = df["flow"].to_numpy()
    results = forecast_evaluation(model, log_full, flow_full, len(train),
                                  lead_times=(1, 2, 3))
    diag = residual_diagnostics(model)
    lb = diag["ljung_box"]

    print("\n  +-------+-----------------------------------+------------------+")
    print("  | Lead  |            ARIMA model            |   Persistence    |")
    print("  | (day) |  NSE    RMSE   PBIAS   PSS  rating|  NSE     RMSE     |")
    print("  +-------+-----------------------------------+------------------+")
    for k in (1, 2, 3):
        m = results[k]["model"]; p = results[k]["persistence"]
        print(f"  |   {k}   | {m['NSE']:.3f}  {m['RMSE']:5.2f}  {m['PBIAS']:6.2f}  "
              f"{m['PSS']:.3f} {m['rating'][:4]:>4} | {p['NSE']:.3f}  {p['RMSE']:6.2f}   |")
    print("  +-------+-----------------------------------+------------------+")

    print("\n  Lognormal retransformation bias correction "
          "(corrected = exp(mu + sigma_k^2/2)):")
    print("    Lead | bias factor | PBIAS uncorrected -> corrected")
    for k in (1, 2, 3):
        bf = results[k]["bias_factor"]
        print(f"      {k}  |    {bf:5.3f}    |  {results[k]['median']['PBIAS']:7.2f}% -> "
              f"{results[k]['model']['PBIAS']:7.2f}%")

    roots = diag["roots"]
    ar_min = min(roots["ar"]) if roots["ar"] else float('nan')
    ma_min = min(roots["ma"]) if roots["ma"] else float('nan')
    print(f"\n  Characteristic roots (|root| > 1 => stationary/invertible):")
    print(f"    AR min |root| = {ar_min:.3f} ; MA min |root| = {ma_min:.3f}"
          f"{'  (MA root near unit circle: mild over-differencing)' if ma_min < 1.2 else ''}")

    print(f"\n  Residual diagnostics:")
    print(f"    Ljung-Box(20)        : Q={lb['stat']:.2f}, p={lb['pvalue']:.4f} "
          f"-> {'no significant autocorrelation' if lb['pvalue'] > 0.05 else 'autocorrelation remains'}")
    print(f"    ARCH (LB on sq resid): Q={diag['arch']['stat']:.2f}, p={diag['arch']['pvalue']:.4f} "
          f"-> {'no volatility clustering' if diag['arch']['pvalue'] > 0.05 else 'volatility clustering present'}")
    print(f"    Jarque-Bera normality: JB={diag['jarque_bera']['stat']:.1f}, p={diag['jarque_bera']['pvalue']:.4f} "
          f"(skew={diag['jarque_bera']['skew']:.2f}, kurt={diag['jarque_bera']['kurtosis']:.2f})")

    # ------------------------------------------------------------------
    # 5. Figures
    # ------------------------------------------------------------------
    print("\n[5/5] Generating figures...")
    from src.plots import (
        fig1_discharge_series, fig2_acf_pacf, fig3_forecast_hydrograph,
        fig4_scatter, fig5_residual_diagnostics, fig6_skill_vs_lead,
    )
    train_end = train.index[-1]
    diff_train = difference(y_train, d)
    # one-year validation window for the hydrograph (readability)
    r1 = results[1]
    win = slice(0, min(365, len(r1["targets"])))
    dates_win = df.index[r1["targets"]][win]

    figs = [
        fig1_discharge_series(df, train_end),
        fig2_acf_pacf(diff_train),
        fig3_forecast_hydrograph(dates_win, r1["q_obs"][win], r1["q_pred"][win],
                                 r1["q_persist"][win]),
        fig4_scatter(r1["q_obs"], r1["q_pred"], lead=1),
        fig5_residual_diagnostics(model.resid_),
        fig6_skill_vs_lead(results),
    ]
    for f in figs:
        print(f"  saved {Path(f).name}")

    # ------------------------------------------------------------------
    # Save results JSON
    # ------------------------------------------------------------------
    out = {
        "basin": "Conecuh River, Alabama (USGS 02361000)",
        "model": f"ARIMA{order}",
        "differencing_d": d,
        "aic": round(model.aic_c, 2),
        "bic": round(model.bic_c, 2),
        "phi": np.round(model.phi, 6).tolist(),
        "theta": np.round(model.theta, 6).tolist(),
        "constant": round(float(model.c), 6),
        "aic_ranking": [
            {"order": list(r["order"]), "aic": round(r["aic"], 2), "bic": round(r["bic"], 2)}
            for r in table[:5]
        ],
        "ljung_box": {"stat": round(lb["stat"], 3), "pvalue": round(lb["pvalue"], 4)},
        "arch": {"stat": round(diag["arch"]["stat"], 3), "pvalue": round(diag["arch"]["pvalue"], 4)},
        "jarque_bera": {k2: round(v2, 4) for k2, v2 in diag["jarque_bera"].items()},
        "roots": {"ar": [round(x, 3) for x in diag["roots"]["ar"]],
                  "ma": [round(x, 3) for x in diag["roots"]["ma"]]},
        "smearing_factor": round(diag["smearing_factor"], 4),
        "discharge_stats": {
            "mean": round(float(df["flow"].mean()), 3),
            "min": round(float(df["flow"].min()), 3),
            "max": round(float(df["flow"].max()), 3),
            "std": round(float(df["flow"].std()), 3),
        },
        "forecast": {
            str(k): {
                "bias_factor": round(results[k]["bias_factor"], 4),
                "model": {kk: (round(vv, 4) if isinstance(vv, float) else vv)
                          for kk, vv in results[k]["model"].items()},
                "median": {kk: (round(vv, 4) if isinstance(vv, float) else vv)
                           for kk, vv in results[k]["median"].items()},
                "persistence": {kk: (round(vv, 4) if isinstance(vv, float) else vv)
                                for kk, vv in results[k]["persistence"].items()},
            }
            for k in (1, 2, 3)
        },
    }
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nResults saved to {RESULTS_FILE}")

    print("\n" + "=" * 68)
    print("  SUMMARY — CONECUH RIVER STATISTICAL FORECAST")
    print("=" * 68)
    print(f"  Model                 : ARIMA{order}")
    print(f"  1-day NSE / PSS       : {results[1]['model']['NSE']:.3f} / {results[1]['model']['PSS']:.3f}")
    print(f"  2-day NSE / PSS       : {results[2]['model']['NSE']:.3f} / {results[2]['model']['PSS']:.3f}")
    print(f"  3-day NSE / PSS       : {results[3]['model']['NSE']:.3f} / {results[3]['model']['PSS']:.3f}")
    print(f"  Residuals white noise : {'yes' if lb['pvalue'] > 0.05 else 'no'} (Ljung-Box p={lb['pvalue']:.3f})")
    print("=" * 68)
    return out


if __name__ == "__main__":
    main()
