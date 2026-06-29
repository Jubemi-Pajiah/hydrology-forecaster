"""
calibrate.py — Model identification and order selection (Box-Jenkins).

Replaces parameter calibration of a rainfall-runoff model with the statistical
identification of an ARIMA(p, d, q) process for log-discharge:

  1. Stationarity testing (ADF + KPSS) on the training series to choose the
     differencing order d.
  2. A grid search over (p, d, q) minimising the Akaike Information Criterion
     (AIC), with the Bayesian Information Criterion (BIC) reported alongside.

This is the "calibration" step of the statistical framework: the data, not a
hydrologist, choose the model order.
"""

import numpy as np

from .model import ARIMA, adf_test, kpss_test, difference


def choose_differencing(y, max_d: int = 2) -> dict:
    """
    Decide the differencing order d using ADF and KPSS jointly.
    d increases until ADF rejects a unit root AND KPSS fails to reject
    stationarity (or max_d is reached).
    """
    report = []
    d = 0
    series = np.asarray(y, dtype=float)
    chosen = 0
    while d <= max_d:
        s = difference(series, d)
        adf = adf_test(s)
        kpss = kpss_test(s)
        report.append({"d": d, "adf": adf, "kpss": kpss})
        if adf["stationary_5pct"] and kpss["stationary_5pct"]:
            chosen = d
            break
        chosen = d
        d += 1
    return {"d": chosen, "report": report}


def select_order(y, p_range=range(0, 5), d_values=(None,), q_range=range(0, 3),
                 max_d: int = 2):
    """
    Grid-search ARIMA orders by AIC.

    If d_values is (None,), the differencing order is chosen automatically by
    :func:`choose_differencing`; otherwise the supplied d values are searched.

    Returns
    -------
    best_order : tuple (p, d, q)
    best_model : fitted ARIMA
    table      : list of dicts {order, aic, bic} sorted by AIC
    diff_info  : output of choose_differencing (or None)
    """
    y = np.asarray(y, dtype=float)
    diff_info = None
    if d_values == (None,):
        diff_info = choose_differencing(y, max_d=max_d)
        d_values = (diff_info["d"],)

    # Condition every candidate on a common number of initial observations so
    # the information criteria are computed on an identical sample (otherwise
    # CSS drops max(p, q) points and models are ranked on different n).
    cond = max(max(p, q) for p in p_range for q in q_range)

    table = []
    best = None
    for d in d_values:
        for p in p_range:
            for q in q_range:
                if p == 0 and q == 0:
                    continue
                try:
                    model = ARIMA((p, d, q)).fit(y, cond=cond)
                    if not np.isfinite(model.aic_c):
                        continue
                    table.append({"order": (p, d, q), "aic": model.aic_c,
                                  "bic": model.bic_c})
                    if best is None or model.aic_c < best[1]:
                        best = ((p, d, q), model.aic_c, model)
                except Exception:
                    continue

    table.sort(key=lambda r: r["aic"])
    best_order, _, best_model = best
    return best_order, best_model, table, diff_info
