"""
model.py — Self-contained statistical time-series toolkit for univariate
streamflow forecasting (Box & Jenkins, 1976).

The model forecasts discharge from its OWN past values only. No rainfall,
temperature, evapotranspiration, or unit-hydrograph routing is used.

Everything here is implemented on top of NumPy and SciPy so the project has no
heavy modelling dependency:

  * acf / pacf            - autocorrelation and partial autocorrelation
  * adf_test              - Augmented Dickey-Fuller stationarity test
  * kpss_test             - KPSS stationarity test
  * ljung_box             - Ljung-Box white-noise test for residuals
  * ARIMA                 - ARIMA(p, d, q) estimated by conditional sum of
                            squares (CSS); AR(p) handled exactly by OLS

The ARIMA class is fitted on the natural-log of discharge (variance-stabilised)
and exposes a rolling multi-step forecast used for 1-, 2- and 3-day lead-time
evaluation.
"""

import numpy as np
from scipy import stats
from scipy.optimize import minimize


# ----------------------------------------------------------------------------
# Correlation diagnostics
# ----------------------------------------------------------------------------
def acf(y: np.ndarray, nlags: int = 40) -> np.ndarray:
    """Sample autocorrelation function for lags 0..nlags."""
    y = np.asarray(y, dtype=float)
    y = y - y.mean()
    n = len(y)
    denom = np.dot(y, y)
    out = np.empty(nlags + 1)
    out[0] = 1.0
    for k in range(1, nlags + 1):
        out[k] = np.dot(y[:-k], y[k:]) / denom
    return out


def pacf(y: np.ndarray, nlags: int = 40) -> np.ndarray:
    """Partial autocorrelation function via the Levinson-Durbin recursion."""
    r = acf(y, nlags)
    phi = np.zeros((nlags + 1, nlags + 1))
    out = np.empty(nlags + 1)
    out[0] = 1.0
    phi[1, 1] = r[1]
    out[1] = r[1]
    for k in range(2, nlags + 1):
        num = r[k] - np.sum(phi[k - 1, 1:k] * r[1:k][::-1])
        den = 1.0 - np.sum(phi[k - 1, 1:k] * r[1:k])
        phi[k, k] = num / den if den != 0 else 0.0
        for j in range(1, k):
            phi[k, j] = phi[k - 1, j] - phi[k, k] * phi[k - 1, k - j]
        out[k] = phi[k, k]
    return out


def conf_interval(n: int, alpha: float = 0.05) -> float:
    """Approximate +/- white-noise confidence bound for ACF/PACF."""
    return stats.norm.ppf(1 - alpha / 2) / np.sqrt(n)


# ----------------------------------------------------------------------------
# Stationarity tests
# ----------------------------------------------------------------------------
def _ols(X: np.ndarray, y: np.ndarray):
    """Ordinary least squares: returns (beta, residuals, XtX_inv)."""
    XtX = X.T @ X
    XtX_inv = np.linalg.pinv(XtX)
    beta = XtX_inv @ (X.T @ y)
    resid = y - X @ beta
    return beta, resid, XtX_inv


def adf_test(y: np.ndarray, maxlag: int = None) -> dict:
    """
    Augmented Dickey-Fuller test (constant, no trend).

    Regression:  dy_t = a + g * y_{t-1} + sum_i d_i * dy_{t-i} + e_t
    Test statistic = g_hat / SE(g_hat); H0: g = 0 (a unit root, non-stationary).

    Critical values from the MacKinnon (1996) response surface for the
    constant-only case.
    """
    y = np.asarray(y, dtype=float)
    n = len(y)
    if maxlag is None:
        maxlag = int(np.ceil(12 * (n / 100.0) ** 0.25))
    dy = np.diff(y)
    # Build the lagged-difference design
    nobs = len(dy) - maxlag
    Y = dy[maxlag:]
    X = [np.ones(nobs), y[maxlag:-1]]
    for i in range(1, maxlag + 1):
        X.append(dy[maxlag - i: -i] if i != 0 else dy[maxlag:])
    X = np.column_stack(X)
    beta, resid, XtX_inv = _ols(X, Y)
    sigma2 = np.dot(resid, resid) / (nobs - X.shape[1])
    se_gamma = np.sqrt(sigma2 * XtX_inv[1, 1])
    stat = beta[1] / se_gamma

    T = nobs
    cv = {
        "1%": -3.43035 - 6.5393 / T - 16.786 / T ** 2,
        "5%": -2.86154 - 2.8903 / T - 4.234 / T ** 2,
        "10%": -2.56677 - 1.5384 / T - 2.809 / T ** 2,
    }
    stationary = stat < cv["5%"]
    return {
        "stat": float(stat),
        "crit": {k: float(v) for k, v in cv.items()},
        "usedlag": maxlag,
        "nobs": int(nobs),
        "stationary_5pct": bool(stationary),
    }


def kpss_test(y: np.ndarray, nlags: int = None) -> dict:
    """
    KPSS test for level stationarity (regression on a constant).
    H0: the series IS stationary (opposite of ADF).
    """
    y = np.asarray(y, dtype=float)
    n = len(y)
    resid = y - y.mean()
    S = np.cumsum(resid)
    eta = np.sum(S ** 2) / n ** 2
    if nlags is None:
        nlags = int(np.floor(4 * (n / 100.0) ** 0.25))
    # Newey-West long-run variance
    s2 = np.dot(resid, resid) / n
    for lag in range(1, nlags + 1):
        w = 1.0 - lag / (nlags + 1.0)
        cov = np.dot(resid[lag:], resid[:-lag]) / n
        s2 += 2.0 * w * cov
    stat = eta / s2
    cv = {"10%": 0.347, "5%": 0.463, "2.5%": 0.574, "1%": 0.739}
    stationary = stat < cv["5%"]
    return {
        "stat": float(stat),
        "crit": cv,
        "usedlag": nlags,
        "stationary_5pct": bool(stationary),
    }


def ljung_box(resid: np.ndarray, lags: int = 20, model_df: int = 0) -> dict:
    """
    Ljung-Box Q test for residual autocorrelation (white-noise check).
    H0: residuals are independently distributed (no remaining structure).
    """
    resid = np.asarray(resid, dtype=float)
    n = len(resid)
    r = acf(resid, lags)[1:]
    q = n * (n + 2) * np.sum((r ** 2) / (n - np.arange(1, lags + 1)))
    dof = max(lags - model_df, 1)
    pvalue = 1.0 - stats.chi2.cdf(q, dof)
    return {"stat": float(q), "pvalue": float(pvalue), "lags": lags, "dof": dof}


def jarque_bera(resid: np.ndarray) -> dict:
    """Jarque-Bera normality test. H0: residuals are normally distributed."""
    r = np.asarray(resid, dtype=float)
    n = len(r)
    r = r - r.mean()
    s = np.mean(r ** 3) / (np.mean(r ** 2) ** 1.5)          # skewness
    k = np.mean(r ** 4) / (np.mean(r ** 2) ** 2)            # kurtosis
    jb = n / 6.0 * (s ** 2 + (k - 3.0) ** 2 / 4.0)
    pvalue = 1.0 - stats.chi2.cdf(jb, 2)
    return {"stat": float(jb), "pvalue": float(pvalue),
            "skew": float(s), "kurtosis": float(k)}


def arch_test(resid: np.ndarray, lags: int = 20) -> dict:
    """Engle-style ARCH check: Ljung-Box on squared residuals.
    A low p-value indicates volatility clustering (conditional heteroscedasticity)."""
    r = np.asarray(resid, dtype=float)
    sq = (r - r.mean()) ** 2
    return ljung_box(sq, lags=lags, model_df=0)


# ----------------------------------------------------------------------------
# Differencing helpers
# ----------------------------------------------------------------------------
def difference(y: np.ndarray, d: int) -> np.ndarray:
    return np.diff(np.asarray(y, dtype=float), n=d) if d > 0 else np.asarray(y, dtype=float)


def integrate_forecasts(y_hist: np.ndarray, w_fcst: np.ndarray, d: int) -> np.ndarray:
    """
    Reconstruct level-scale forecasts from differenced-scale forecasts using
    the tail of the original history y_hist.
    """
    cur = np.asarray(w_fcst, dtype=float)
    y_hist = np.asarray(y_hist, dtype=float)
    for level in range(d, 0, -1):
        base = np.diff(y_hist, n=level - 1)
        cur = base[-1] + np.cumsum(cur)
    return cur


# ----------------------------------------------------------------------------
# ARIMA(p, d, q) by conditional sum of squares
# ----------------------------------------------------------------------------
class ARIMA:
    """
    ARIMA(p, d, q) with a constant, estimated by conditional sum of squares.

    The series is differenced d times; an ARMA(p, q) model with intercept c is
    then fitted to the differenced series w:

        w_t = c + sum_i phi_i w_{t-i} + e_t + sum_j theta_j e_{t-j}

    AR(p) models (q = 0) are solved exactly by OLS; mixed models use SciPy's
    optimiser on the conditional sum of squared errors.
    """

    def __init__(self, order=(1, 0, 0)):
        self.p, self.d, self.q = order
        self.order = order
        self.c = 0.0
        self.phi = np.zeros(self.p)
        self.theta = np.zeros(self.q)
        self.sigma2 = None
        self.aic = None
        self.bic = None
        self.nobs = None
        self.resid_ = None
        self._y_train = None

    # -- internal: conditional residuals for a differenced series w ----------
    def _css_resid(self, w, c, phi, theta):
        p, q = self.p, self.q
        m = max(p, q)
        n = len(w)
        e = np.zeros(n)
        for t in range(m, n):
            ar = np.dot(phi, w[t - p:t][::-1]) if p else 0.0
            ma = np.dot(theta, e[t - q:t][::-1]) if q else 0.0
            e[t] = w[t] - c - ar - ma
        return e

    def _pack(self):
        return np.concatenate([[self.c], self.phi, self.theta])

    def _unpack(self, x):
        p, q = self.p, self.q
        c = x[0]
        phi = x[1:1 + p]
        theta = x[1 + p:1 + p + q]
        return c, phi, theta

    def fit(self, y, cond=None):
        """Fit the model to series y (here: log-discharge of the training set).

        cond : if given, the number of initial observations on which to condition
               the comparable information criteria (aic_c/bic_c), so that all
               candidate orders are ranked on an identical sample.
        """
        y = np.asarray(y, dtype=float)
        self._y_train = y
        w = difference(y, self.d)
        p, q = self.p, self.q
        m = max(p, q)
        n_eff = len(w) - m
        k = p + q + 1 + 1  # AR + MA + constant + variance
        self._w_train = w

        if q == 0:
            # Exact OLS for pure AR(p) (with constant)
            if p == 0:
                self.c = float(w.mean())
                self.phi = np.zeros(0)
                resid = w[m:] - self.c
            else:
                rows = len(w) - p
                X = np.column_stack(
                    [np.ones(rows)] + [w[p - i - 1: len(w) - i - 1] for i in range(p)]
                )
                target = w[p:]
                beta, resid, _ = _ols(X, target)
                self.c = float(beta[0])
                self.phi = beta[1:]
        else:
            # CSS optimisation for ARMA(p, q)
            x0 = np.zeros(1 + p + q)
            x0[0] = w.mean() * (1.0 - 0.5)
            if p:
                x0[1] = 0.3

            def obj(x):
                c, phi, theta = self._unpack(x)
                with np.errstate(over="ignore", invalid="ignore"):
                    e = self._css_resid(w, c, phi, theta)[m:]
                    ssr = np.dot(e, e)
                if not np.isfinite(ssr) or ssr <= 0:
                    return 1e12
                return 0.5 * n_eff * np.log(ssr / n_eff + 1e-12)

            bounds = [(None, None)] + [(-0.999, 0.999)] * (p + q)
            res = minimize(obj, x0, method="L-BFGS-B", bounds=bounds)
            self.c, self.phi, self.theta = self._unpack(res.x)
            resid = self._css_resid(w, self.c, self.phi, self.theta)[m:]

        self.resid_ = resid
        ssr = float(np.dot(resid, resid))
        self.sigma2 = ssr / n_eff
        self.nobs = n_eff
        self.aic = n_eff * np.log(self.sigma2) + 2 * k
        self.bic = n_eff * np.log(self.sigma2) + k * np.log(n_eff)

        # Comparable information criteria: condition every model on a common
        # number of initial observations (cond) so AIC/BIC are computed on an
        # identical sample regardless of (p, q). resid_ starts at index m.
        if cond is not None and cond >= m:
            resid_c = resid[cond - m:]
            n_c = len(resid_c)
            sigma2_c = float(np.dot(resid_c, resid_c)) / n_c
            self.aic_c = n_c * np.log(sigma2_c) + 2 * k
            self.bic_c = n_c * np.log(sigma2_c) + k * np.log(n_c)
            self.nobs_c = n_c
        else:
            self.aic_c, self.bic_c, self.nobs_c = self.aic, self.bic, n_eff
        return self

    # -- diagnostics ---------------------------------------------------------
    def _psi_weights(self, nmax):
        """MA(infinity) weights of the integrated model phi(B)(1-B)^d / theta(B)."""
        phi_poly = np.concatenate([[1.0], -self.phi]) if self.p else np.array([1.0])
        diff_poly = np.array([1.0])
        for _ in range(self.d):
            diff_poly = np.convolve(diff_poly, [1.0, -1.0])
        Phi = np.convolve(phi_poly, diff_poly)        # 1 - a1 B - a2 B^2 - ...
        a = -Phi[1:]
        P = len(a)
        psi = np.zeros(nmax)
        psi[0] = 1.0
        for j in range(1, nmax):
            s = 0.0
            for i in range(1, min(j, P) + 1):
                s += a[i - 1] * psi[j - i]
            if 1 <= j <= self.q:
                s += self.theta[j - 1]
            psi[j] = s
        return psi

    def kstep_logvar(self, K):
        """k-step-ahead forecast error variance on the log scale, k = 1..K."""
        psi = self._psi_weights(K)
        return np.array([self.sigma2 * np.sum(psi[:k] ** 2) for k in range(1, K + 1)])

    def smearing_factor(self):
        """Duan (1983) nonparametric smearing factor from 1-step residuals."""
        return float(np.mean(np.exp(self.resid_)))

    def roots(self):
        """Moduli of the AR and MA characteristic roots (stationary/invertible if > 1)."""
        def _moduli(coef):
            if len(coef) == 0:
                return []
            poly = np.concatenate([[1.0], -np.asarray(coef, dtype=float)])
            r = np.roots(poly[::-1])
            return sorted(np.abs(r).tolist())
        # MA convention here is +theta, so use +theta for the MA polynomial
        ma_poly = np.concatenate([[1.0], np.asarray(self.theta, dtype=float)]) if self.q else np.array([1.0])
        ma_mod = sorted(np.abs(np.roots(ma_poly[::-1])).tolist()) if self.q else []
        return {"ar": _moduli(self.phi), "ma": ma_mod}

    # -- forecasting ---------------------------------------------------------
    def _forecast_diff(self, w_hist, e_hist, k):
        """Recursive k-step forecast on the differenced scale."""
        p, q = self.p, self.q
        y_ext = list(w_hist)
        e_ext = list(e_hist)
        preds = []
        for _ in range(k):
            idx = len(y_ext)
            ar = sum(self.phi[j] * y_ext[idx - 1 - j] for j in range(p)) if p else 0.0
            ma = sum(self.theta[j] * e_ext[idx - 1 - j] for j in range(q)) if q else 0.0
            val = self.c + ar + ma
            preds.append(val)
            y_ext.append(val)
            e_ext.append(0.0)
        return np.array(preds)

    def forecast(self, k):
        """k-step forecast (level scale) from the end of the training series."""
        w = difference(self._y_train, self.d)
        e = self._css_resid(w, self.c, self.phi, self.theta)
        w_fcst = self._forecast_diff(w, e, k)
        return integrate_forecasts(self._y_train, w_fcst, self.d)

    def rolling_kstep(self, y_full, k, start_idx):
        """
        Rolling-origin k-step forecasts with fixed (already estimated)
        parameters. For every origin t with start_idx <= t+k <= len-1 the model
        forecasts y_full[t+k] using only information up to and including t.

        Returns (targets_index, y_pred) arrays aligned on the forecast target.
        """
        y_full = np.asarray(y_full, dtype=float)
        w_full = difference(y_full, self.d)
        e_full = self._css_resid(w_full, self.c, self.phi, self.theta)
        n = len(y_full)
        origins = []
        preds = []
        for t in range(start_idx - 1, n - k):
            nd = t - self.d  # last available differenced index
            if nd < max(self.p, self.q):
                continue
            w_hist = w_full[: nd + 1]
            e_hist = e_full[: nd + 1]
            w_fcst = self._forecast_diff(w_hist, e_hist, k)
            y_fcst = integrate_forecasts(y_full[: t + 1], w_fcst, self.d)
            origins.append(t + k)
            preds.append(y_fcst[-1])
        return np.array(origins), np.array(preds)
