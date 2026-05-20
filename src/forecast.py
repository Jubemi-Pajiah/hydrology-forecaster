"""
forecast.py — Multi-step ahead discharge forecasting.

For lead times 1, 2, 3 days, the model state at each day t is used to generate
a forecast by running the model forward with observed forcing (perfect-forcing
scenario — the standard benchmark for short-range hydrological forecasting).

The forecast NSE is computed over the validation period, comparing the
t+k forecast to observed discharge at t+k.
"""

import numpy as np
import pandas as pd

from .model import run_model
from .metrics import nse


def forecast_horizon(
    prcp: np.ndarray,
    pet: np.ndarray,
    q_obs: np.ndarray,
    params: dict,
    lead_times: list = (1, 2, 3),
    state_S0: float = None,
    state_G0: float = None,
) -> dict:
    """
    Generate multi-step-ahead discharge forecasts and evaluate NSE per lead time.

    Strategy: Run the model through the full period to collect daily states.
    Then for each day t, re-initialise from state(t) and run forward `k` steps
    to obtain Q_forecast(t+k). Compare to Q_obs(t+k).

    Parameters
    ----------
    prcp, pet   : forcing arrays (mm/day), length N
    q_obs       : observed discharge (m³/s), length N
    params      : calibrated parameter dict
    lead_times  : list of integer lead times (days)
    state_S0, state_G0 : initial states (warm-up already applied)

    Returns
    -------
    dict with keys like 1, 2, 3 mapping to {"nse": float, "q_forecast": array}
    """
    Smax = params["Smax"]
    kq   = params["kq"]
    kp   = params["kp"]
    kg   = params["kg"]
    cet  = params["cet"]

    N = len(prcp)
    S0 = state_S0 if state_S0 is not None else Smax / 2.0
    G0 = state_G0 if state_G0 is not None else 10.0

    # Pass 1: run model and record daily states (S, G) at END of each day
    S_arr = np.zeros(N + 1)
    G_arr = np.zeros(N + 1)
    S_arr[0] = S0
    G_arr[0] = G0

    S, G = S0, G0
    for t in range(N):
        ET     = cet * pet[t] * min(S / Smax, 1.0)
        ET     = max(0.0, min(ET, S))
        Qquick = kq * max(0.0, S - Smax)
        Rperc  = kp * S
        S      = max(0.0, S + prcp[t] - ET - Qquick - Rperc)
        Qbase  = kg * G
        G      = max(0.0, G + Rperc - Qbase)
        S_arr[t + 1] = S
        G_arr[t + 1] = G

    results = {}
    for k in lead_times:
        # For each t from 0 to N-k-1, forecast at t+k
        n_fcst = N - k
        q_fcst = np.empty(n_fcst)

        for t in range(n_fcst):
            # Re-initialise from state at END of day t (i.e. start of t+1)
            S_i = S_arr[t + 1]
            G_i = G_arr[t + 1]
            # Run k steps forward using observed forcing
            prcp_k = prcp[t + 1 : t + 1 + k]
            pet_k  = pet[t + 1 : t + 1 + k]
            q_seg  = run_model(prcp_k, pet_k, params, S0=S_i, G0=G_i)
            q_fcst[t] = q_seg[-1]   # discharge on day t+k

        q_obs_k = q_obs[k:]   # observed at t+k, aligned with q_fcst
        nse_k   = nse(q_obs_k, q_fcst)
        results[k] = {"nse": nse_k, "q_forecast": q_fcst}
        print(f"  Lead {k} day: NSE = {nse_k:.4f}")

    return results
