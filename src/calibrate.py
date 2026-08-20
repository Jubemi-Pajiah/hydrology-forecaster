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

from .model import (ARIMA, SEASONAL_PERIOD, acf, adf_test, conf_interval,
                    difference, kpss_test, seasonal_difference)


def seasonal_strength(y, s: int = SEASONAL_PERIOD) -> dict:
    """
    Evidence for a periodic component of period s, used to decide whether the
    seasonal differencing operator (1 - B^s) is required.

    ADF and KPSS cannot answer this question: both test for a unit root or
    level stationarity at lag 1 and are blind to a purely periodic component,
    which is why a monthly series can be judged stationary by both while still
    repeating the same shape every twelve months. Two statistics are reported
    instead:

    acf_s
        The sample autocorrelation at lag s, compared with the white-noise
        band +/- 1.96/sqrt(n). A series with an annual cycle shows a clear
        positive spike at lag 12.
    strength
        The share of total variance explained by the mean cycle, obtained by
        folding the series into s phases: Var(phase means) / Var(series).
        Zero for white noise, approaching one for a near-deterministic cycle.
        Folding is done on position modulo s, so the series must start at the
        beginning of a cycle (January, for the monthly records used here).
    """
    y = np.asarray(y, dtype=float)
    n = len(y)
    r = acf(y, nlags=s)
    acf_s = float(r[s])
    bound = float(conf_interval(n))

    phase_means = np.array([y[j::s].mean() for j in range(s)])
    total_var = float(np.var(y, ddof=1))
    strength = float(np.var(phase_means, ddof=0) / total_var) if total_var > 0 else 0.0

    return {
        "period": s,
        "acf_at_period": acf_s,
        "white_noise_bound": bound,
        "acf_significant": bool(acf_s > bound),
        "strength": strength,
        "n": n,
    }


def choose_seasonal_differencing(y, s: int = SEASONAL_PERIOD,
                                 max_D: int = 1,
                                 strength_threshold: float = 0.05) -> dict:
    """
    Decide the seasonal differencing order D at period s.

    D is set to 1 when the autocorrelation at lag s is significantly positive
    and the mean cycle accounts for a non-trivial share of the variance; the
    two conditions together guard against differencing away a cycle that is
    not really there. Repeated seasonal differencing is rarely justified, so
    max_D defaults to 1.
    """
    report = []
    series = np.asarray(y, dtype=float)
    chosen = 0
    for D in range(0, max_D + 1):
        stats_D = seasonal_strength(seasonal_difference(series, D, s), s)
        stats_D["D"] = D
        report.append(stats_D)
        needs_more = (stats_D["acf_significant"]
                      and stats_D["strength"] > strength_threshold)
        if not needs_more:
            chosen = D
            break
        chosen = min(D + 1, max_D)
    return {"D": chosen, "period": s, "report": report,
            "strength_threshold": strength_threshold}


def choose_differencing(y, max_d: int = 2, s: int = SEASONAL_PERIOD,
                        max_D: int = 1) -> dict:
    """
    Decide the full differencing operator (1 - B)^d (1 - B^s)^D.

    The seasonal order is settled first, because the annual cycle is the
    dominant non-stationary feature of a monthly hydrological record and
    leaving it in the series distorts the lag-1 tests. The ordinary order d is
    then chosen on the seasonally differenced series by ADF and KPSS jointly:
    d increases until ADF rejects a unit root AND KPSS fails to reject
    stationarity (or max_d is reached).
    """
    series = np.asarray(y, dtype=float)

    seasonal_info = choose_seasonal_differencing(series, s=s, max_D=max_D)
    D = seasonal_info["D"]
    base = seasonal_difference(series, D, s)

    report = []
    d = 0
    chosen = 0
    while d <= max_d:
        w = difference(base, d)
        adf = adf_test(w)
        kpss = kpss_test(w)
        report.append({"d": d, "adf": adf, "kpss": kpss})
        if adf["stationary_5pct"] and kpss["stationary_5pct"]:
            chosen = d
            break
        chosen = d
        d += 1
    return {"d": chosen, "D": D, "s": s, "report": report,
            "seasonal_report": seasonal_info}


def select_order(y, p_range=range(0, 5), d_values=(None,), q_range=range(0, 3),
                 max_d: int = 2, D=None, s: int = SEASONAL_PERIOD,
                 max_D: int = 1, Q_range=None):
    """
    Grid-search ARIMA orders by AIC.

    If d_values is (None,), the differencing operator is chosen automatically
    by :func:`choose_differencing`; otherwise the supplied d values are
    searched. D may likewise be pinned by the caller or left to the data.

    Only (p, q) are searched: the differencing orders are settled beforehand
    on the stationarity and seasonality evidence, not by information criteria,
    because differencing changes the series being modelled and AIC values
    computed on differently differenced data are not comparable.

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
        diff_info = choose_differencing(y, max_d=max_d, s=s, max_D=max_D)
        d_values = (diff_info["d"],)
        if D is None:
            D = diff_info["D"]
    if D is None:
        D = 0
    D = int(D)

    # A seasonal difference of a largely deterministic cycle induces a strong
    # negative autocorrelation at lag s, which no non-seasonal term of low
    # order can absorb; a seasonal MA term is the standard remedy. Search it
    # only when seasonal differencing was actually applied.
    if Q_range is None:
        Q_range = range(0, 2) if D > 0 else range(0, 1)

    # Condition every candidate on a common number of initial observations so
    # the information criteria are computed on an identical sample (otherwise
    # CSS drops a different number of points per candidate and models are
    # ranked on different n). A seasonal MA term of order Q expands to lag
    # Q*s, so it consumes far more of the head of the series than any
    # non-seasonal term and sets the common conditioning length.
    cond = max(max(p, q + Q * s)
               for p in p_range for q in q_range for Q in Q_range)

    table = []
    best = None
    for d in d_values:
        for p in p_range:
            for q in q_range:
                for Q in Q_range:
                    if p == 0 and q == 0 and Q == 0:
                        continue
                    seasonal_order = (0, D, Q)
                    try:
                        model = ARIMA((p, d, q), seasonal_order, s).fit(y, cond=cond)
                        if not np.isfinite(model.aic_c):
                            continue
                        table.append({"order": (p, d, q),
                                      "seasonal_order": seasonal_order,
                                      "label": model.label(),
                                      "aic": model.aic_c, "bic": model.bic_c})
                        if best is None or model.aic_c < best[1]:
                            best = ((p, d, q), model.aic_c, model)
                    except Exception:
                        continue

    table.sort(key=lambda r: r["aic"])
    best_order, _, best_model = best
    return best_order, best_model, table, diff_info
