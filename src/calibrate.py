"""
calibrate.py — Calibrate the two-bucket model using differential evolution.

Objective: minimise negative NSE on the calibration period (1980-2003).
Uses scipy.optimize.differential_evolution with a warm-up period (first 365 days
excluded from NSE calculation) to allow model states to equilibrate.
"""

import numpy as np
from scipy.optimize import differential_evolution

from .model import run_model, PARAM_BOUNDS, params_from_list, warm_up
from .metrics import nse

WARMUP_DAYS = 365


def kge(q_obs: np.ndarray, q_sim: np.ndarray) -> float:
    """Kling-Gupta Efficiency (Gupta et al., 2009)."""
    if q_obs.std() == 0 or q_sim.std() == 0 or q_obs.mean() == 0:
        return -999.0
    r = np.corrcoef(q_obs, q_sim)[0, 1]
    alpha = q_sim.std() / q_obs.std()
    beta  = q_sim.mean() / q_obs.mean()
    return float(1.0 - np.sqrt((r - 1)**2 + (alpha - 1)**2 + (beta - 1)**2))


_EPS = 1e-6   # small constant for log transform


def log_nse(q_obs: np.ndarray, q_sim: np.ndarray) -> float:
    """NSE on log-transformed flows — more weight on low flows, more robust."""
    lo = np.log(q_obs + _EPS)
    ls = np.log(q_sim + _EPS)
    num = np.sum((lo - ls) ** 2)
    den = np.sum((lo - lo.mean()) ** 2)
    if den == 0:
        return np.nan
    return float(1.0 - num / den)


_EPS = 1e-6


def log_nse(q_obs: np.ndarray, q_sim: np.ndarray) -> float:
    """NSE on log-flows — more weight on low flows, more robust to extremes."""
    lo = np.log(np.maximum(q_obs, _EPS))
    ls = np.log(np.maximum(q_sim, _EPS))
    num = np.sum((lo - ls) ** 2)
    den = np.sum((lo - lo.mean()) ** 2)
    if den == 0:
        return np.nan
    return float(1.0 - num / den)


def objective(x: list, prcp: np.ndarray, pet: np.ndarray, q_obs: np.ndarray) -> float:
    """Combined objective: 0.7 × NSE + 0.3 × log-NSE.
    Balances peak-flow performance with volumetric robustness for better validation."""
    params = params_from_list(x)
    q_sim = run_model(prcp, pet, params)
    obs_w = q_obs[WARMUP_DAYS:]
    sim_w = q_sim[WARMUP_DAYS:]
    n1 = nse(obs_w, sim_w)
    n2 = log_nse(obs_w, sim_w)
    if np.isnan(n1) or np.isnan(n2):
        return 1.0
    return -(0.7 * n1 + 0.3 * n2)


def calibrate(prcp: np.ndarray, pet: np.ndarray, q_obs: np.ndarray,
              seed: int = 42, maxiter: int = 2000, popsize: int = 15,
              tol: float = 1e-7) -> tuple:
    """
    Run differential evolution calibration.

    Returns
    -------
    best_params : dict of calibrated parameters
    cal_nse     : calibration NSE (excluding warm-up)
    result      : full scipy OptimizeResult
    """
    print("Pre-compiling Numba JIT model...")
    warm_up()
    print("Starting calibration (differential_evolution)...")
    result = differential_evolution(
        objective,
        bounds=PARAM_BOUNDS,
        args=(prcp, pet, q_obs),
        seed=seed,
        maxiter=maxiter,
        popsize=popsize,
        tol=tol,
        mutation=(0.5, 1.5),
        recombination=0.7,
        polish=True,
        disp=True,
    )
    best_params = params_from_list(result.x)
    # Compute NSE (the reported metric) with best params
    q_sim_cal = run_model(prcp, pet, best_params)
    cal_nse = nse(q_obs[WARMUP_DAYS:], q_sim_cal[WARMUP_DAYS:])
    return best_params, cal_nse, result
