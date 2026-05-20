"""
metrics.py — Performance metrics for hydrological model evaluation.

Formulas per PROJECT_CONTEXT.md:
  NSE   = 1 - sum((Qobs-Qsim)²) / sum((Qobs-mean(Qobs))²)
  RMSE  = sqrt[(1/n) * sum((Qobs-Qsim)²)]
  PBIAS = 100 * sum(Qsim-Qobs) / sum(Qobs)   [%]
"""

import numpy as np


def nse(q_obs: np.ndarray, q_sim: np.ndarray) -> float:
    """Nash-Sutcliffe Efficiency."""
    num = np.sum((q_obs - q_sim) ** 2)
    den = np.sum((q_obs - np.mean(q_obs)) ** 2)
    if den == 0:
        return np.nan
    return float(1.0 - num / den)


def rmse(q_obs: np.ndarray, q_sim: np.ndarray) -> float:
    """Root Mean Square Error (m³/s)."""
    return float(np.sqrt(np.mean((q_obs - q_sim) ** 2)))


def pbias(q_obs: np.ndarray, q_sim: np.ndarray) -> float:
    """Percent Bias [%]."""
    if np.sum(q_obs) == 0:
        return np.nan
    return float(100.0 * np.sum(q_sim - q_obs) / np.sum(q_obs))


def evaluate(q_obs: np.ndarray, q_sim: np.ndarray, label: str = "") -> dict:
    """Compute all metrics and print a summary."""
    metrics = {
        "NSE":   nse(q_obs, q_sim),
        "RMSE":  rmse(q_obs, q_sim),
        "PBIAS": pbias(q_obs, q_sim),
    }
    if label:
        print(f"\n--- {label} Performance ---")
        print(f"  NSE   = {metrics['NSE']:.4f}")
        print(f"  RMSE  = {metrics['RMSE']:.4f} m³/s")
        print(f"  PBIAS = {metrics['PBIAS']:.2f} %")
    return metrics
