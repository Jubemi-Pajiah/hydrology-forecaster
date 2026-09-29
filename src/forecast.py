"""
forecast.py — Residual diagnostics for a fitted ARIMA model.

The module once also held the evaluation machinery of the daily point-forecast
pipeline: rolling-origin k-step forecasts scored against a persistence
benchmark by Nash-Sutcliffe efficiency and a skill score, with a lognormal
retransformation correction applied to each point forecast. That pipeline was
superseded when validation moved from point-forecast comparison to
property-based comparison of a stochastic ensemble (see run_pipeline.py and
validation.py), and the code was removed rather than left to suggest that a
skill score is the reported result. It is not.

The ARIMA class itself retains its forecasting methods (``forecast``,
``rolling_kstep``, ``kstep_logvar`` in model.py) because producing a k-step
forecast is a genuine capability of the model; what this project deliberately
does not do is report one as its output.
"""

from .model import ARIMA, ljung_box, jarque_bera, arch_test


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
