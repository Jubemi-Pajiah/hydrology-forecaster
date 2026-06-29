"""
forecast.py — Multi-step-ahead streamflow forecasting and evaluation.

For each lead time k (1, 2, 3 days) the fitted ARIMA model produces a
rolling-origin forecast over the validation period: at every day t it forecasts
discharge at t+k using only discharge observed up to t. Forecasts are produced
on the log scale and back-transformed to m3/s.

Two reference forecasts are evaluated for context:
  * persistence : Q(t+k) = Q(t)   (the naive benchmark)
  * the ARIMA model

The persistence skill score quantifies how much the model improves on
persistence.
"""

import numpy as np

from .metrics import evaluate
from .model import ARIMA, ljung_box, jarque_bera, arch_test
from .preprocess import inv_log_transform


def forecast_evaluation(model: ARIMA, log_full: np.ndarray, flow_full: np.ndarray,
                        valid_start_idx: int, lead_times=(1, 2, 3)) -> dict:
    """
    Evaluate the model and persistence over the validation period.

    Parameters
    ----------
    model            : ARIMA already fitted on the training (log) series
    log_full         : full log-discharge series (train + validation)
    flow_full        : full discharge series in m3/s (train + validation)
    valid_start_idx  : index in the full series where validation begins
    lead_times       : forecast lead times in days

    Returns
    -------
    dict keyed by lead time, each with model metrics, persistence metrics and
    the aligned observed/forecast arrays (m3/s) for plotting.
    """
    flow_full = np.asarray(flow_full, dtype=float)
    # k-step log-scale forecast variance, for the lognormal retransformation
    # bias correction: E[Q] = exp(mu + sigma_k^2 / 2), not exp(mu) (the median).
    logvar = model.kstep_logvar(max(lead_times))
    results = {}
    for k in lead_times:
        targets, preds_log = model.rolling_kstep(log_full, k, valid_start_idx)
        var_k = logvar[k - 1]
        q_pred = inv_log_transform(preds_log + 0.5 * var_k)   # bias-corrected mean
        q_median = inv_log_transform(preds_log)               # uncorrected (median)
        q_obs = flow_full[targets]
        q_persist = flow_full[targets - k]

        m_model = evaluate(q_obs, q_pred, q_persist=q_persist)
        m_median = evaluate(q_obs, q_median, q_persist=q_persist)
        m_persist = evaluate(q_obs, q_persist)

        results[k] = {
            "targets": targets,
            "q_obs": q_obs,
            "q_pred": q_pred,
            "q_median": q_median,
            "q_persist": q_persist,
            "logvar": float(var_k),
            "bias_factor": float(np.exp(0.5 * var_k)),
            "model": m_model,
            "median": m_median,
            "persistence": m_persist,
        }
    return results


def residual_diagnostics(model: ARIMA, lags: int = 20) -> dict:
    """Full residual diagnostic suite on the in-sample one-step residuals:
    Ljung-Box (autocorrelation), ARCH (volatility clustering), Jarque-Bera
    (normality), and the AR/MA characteristic roots."""
    df = model.p + model.q
    return {
        "ljung_box": ljung_box(model.resid_, lags=lags, model_df=df),
        "arch": arch_test(model.resid_, lags=lags),
        "jarque_bera": jarque_bera(model.resid_),
        "roots": model.roots(),
        "smearing_factor": model.smearing_factor(),
    }
