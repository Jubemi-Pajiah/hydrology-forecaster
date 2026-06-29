"""
metrics.py — Performance metrics for streamflow-forecast evaluation.

  NSE   = 1 - sum((Qobs-Qsim)^2) / sum((Qobs-mean(Qobs))^2)
  RMSE  = sqrt[(1/n) * sum((Qobs-Qsim)^2)]
  PBIAS = 100 * sum(Qsim-Qobs) / sum(Qobs)            [%]
  MAE   = (1/n) * sum|Qobs-Qsim|
  R2    = squared Pearson correlation of (Qobs, Qsim)
  PSS   = persistence skill score = 1 - MSE_model / MSE_persistence

The persistence skill score is the decisive metric for short-range streamflow
forecasting: daily flow is strongly autocorrelated, so a naive "tomorrow equals
today" forecast already scores a high NSE. PSS > 0 means the statistical model
adds genuine skill beyond persistence.
"""

import numpy as np


def nse(q_obs, q_sim):
    q_obs, q_sim = np.asarray(q_obs, float), np.asarray(q_sim, float)
    den = np.sum((q_obs - q_obs.mean()) ** 2)
    if den == 0:
        return np.nan
    return float(1.0 - np.sum((q_obs - q_sim) ** 2) / den)


def rmse(q_obs, q_sim):
    q_obs, q_sim = np.asarray(q_obs, float), np.asarray(q_sim, float)
    return float(np.sqrt(np.mean((q_obs - q_sim) ** 2)))


def pbias(q_obs, q_sim):
    q_obs, q_sim = np.asarray(q_obs, float), np.asarray(q_sim, float)
    if np.sum(q_obs) == 0:
        return np.nan
    return float(100.0 * np.sum(q_sim - q_obs) / np.sum(q_obs))


def mae(q_obs, q_sim):
    q_obs, q_sim = np.asarray(q_obs, float), np.asarray(q_sim, float)
    return float(np.mean(np.abs(q_obs - q_sim)))


def r2(q_obs, q_sim):
    q_obs, q_sim = np.asarray(q_obs, float), np.asarray(q_sim, float)
    if q_obs.std() == 0 or q_sim.std() == 0:
        return np.nan
    return float(np.corrcoef(q_obs, q_sim)[0, 1] ** 2)


def persistence_skill_score(q_obs, q_sim, q_persist):
    """1 - MSE(model) / MSE(persistence). > 0 means skill beyond persistence."""
    q_obs = np.asarray(q_obs, float)
    mse_model = np.mean((q_obs - np.asarray(q_sim, float)) ** 2)
    mse_persist = np.mean((q_obs - np.asarray(q_persist, float)) ** 2)
    if mse_persist == 0:
        return np.nan
    return float(1.0 - mse_model / mse_persist)


def moriasi_rating(nse_value: float) -> str:
    """Performance rating after Moriasi et al. (2007)."""
    if np.isnan(nse_value):
        return "N/A"
    if nse_value > 0.75:
        return "Very Good"
    if nse_value > 0.65:
        return "Good"
    if nse_value > 0.50:
        return "Acceptable"
    return "Unsatisfactory"


def evaluate(q_obs, q_sim, q_persist=None, label=""):
    """Compute the full metric set and optionally print a summary."""
    m = {
        "NSE": nse(q_obs, q_sim),
        "RMSE": rmse(q_obs, q_sim),
        "PBIAS": pbias(q_obs, q_sim),
        "MAE": mae(q_obs, q_sim),
        "R2": r2(q_obs, q_sim),
    }
    if q_persist is not None:
        m["PSS"] = persistence_skill_score(q_obs, q_sim, q_persist)
    m["rating"] = moriasi_rating(m["NSE"])
    if label:
        print(f"\n--- {label} ---")
        print(f"  NSE   = {m['NSE']:.4f}  ({m['rating']})")
        print(f"  RMSE  = {m['RMSE']:.3f} m3/s")
        print(f"  PBIAS = {m['PBIAS']:.2f} %")
        print(f"  MAE   = {m['MAE']:.3f} m3/s")
        print(f"  R2    = {m['R2']:.4f}")
        if "PSS" in m:
            print(f"  PSS   = {m['PSS']:.4f}  (skill vs persistence)")
    return m
