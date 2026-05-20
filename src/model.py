"""
model.py — Lumped two-bucket conceptual rainfall-runoff model.
JIT-compiled with Numba for fast calibration.

Model structure (per PROJECT_CONTEXT.md):
  Soil bucket  : S(t+1) = S(t) + P(t) - ET(t) - Qquick(t) - Rperc(t)
  ET           : ET(t)  = cet * PET(t) * (S(t) / Smax)
  Quick runoff : Qquick(t) = kq * max(0, S(t) - Smax)
  Percolation  : Rperc(t) = kp * S(t)
  GW bucket    : G(t+1) = G(t) + Rperc(t) - Qbase(t)
  Baseflow     : Qbase(t) = kg * G(t)
  Total Q      : Qsim(t) = Qquick(t) + Qbase(t)
"""

import numpy as np
from numba import njit

PARAM_NAMES = ["Smax", "kq", "kp", "kg", "cet"]
PARAM_BOUNDS = [
    (50.0, 800.0),   # Smax  [mm] — wider range
    (0.001, 0.99),   # kq
    (0.0001, 0.2),   # kp
    (0.001, 0.3),    # kg  — allow slower groundwater recession
    (0.3, 2.0),      # cet
]


@njit(cache=True)
def _run_model_core(prcp, pet, Smax, kq, kp, kg, cet, S0, G0):
    """Numba-compiled inner loop for maximum speed."""
    N = len(prcp)
    S = S0
    G = G0
    Qsim = np.empty(N)

    for t in range(N):
        # ET (bounded)
        ET = cet * pet[t] * (S / Smax)
        if ET < 0.0:
            ET = 0.0
        elif ET > S:
            ET = S

        # Quick runoff (saturation excess)
        excess = S - Smax
        Qquick = kq * excess if excess > 0.0 else 0.0

        # Percolation
        Rperc = kp * S

        # Update soil store
        S = S + prcp[t] - ET - Qquick - Rperc
        if S < 0.0:
            S = 0.0

        # Baseflow
        Qbase = kg * G

        # Update groundwater store
        G = G + Rperc - Qbase
        if G < 0.0:
            G = 0.0

        Qsim[t] = Qquick + Qbase

    return Qsim


def run_model(
    prcp: np.ndarray,
    pet: np.ndarray,
    params: dict,
    S0: float = None,
    G0: float = None,
) -> np.ndarray:
    """
    Run the two-bucket model for one period.

    Parameters
    ----------
    prcp : precipitation (mm/day), shape (N,)
    pet  : potential evapotranspiration (mm/day), shape (N,)
    params : dict with keys Smax, kq, kp, kg, cet
    S0, G0 : initial soil and groundwater states (mm).
              Defaults to Smax/2 and 10 mm if None.

    Returns
    -------
    Qsim : simulated discharge (mm/day), shape (N,)
    """
    Smax = params["Smax"]
    kq   = params["kq"]
    kp   = params["kp"]
    kg   = params["kg"]
    cet  = params["cet"]

    S0_val = float(S0) if S0 is not None else float(Smax / 2.0)
    G0_val = float(G0) if G0 is not None else 10.0

    return _run_model_core(
        np.asarray(prcp, dtype=np.float64),
        np.asarray(pet,  dtype=np.float64),
        float(Smax), float(kq), float(kp), float(kg), float(cet),
        S0_val, G0_val,
    )


def params_from_list(x) -> dict:
    """Convert optimiser parameter vector to named dict."""
    return dict(zip(PARAM_NAMES, x))


def warm_up():
    """Pre-compile Numba JIT function on a tiny dummy run."""
    dummy = np.ones(10, dtype=np.float64)
    _run_model_core(dummy, dummy, 100.0, 0.1, 0.01, 0.01, 1.0, 50.0, 10.0)
