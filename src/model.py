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
SEASONAL_PERIOD = 12


def difference(y: np.ndarray, d: int) -> np.ndarray:
    return np.diff(np.asarray(y, dtype=float), n=d) if d > 0 else np.asarray(y, dtype=float)


def integrate_forecasts(y_hist: np.ndarray, w_fcst: np.ndarray, d: int) -> np.ndarray:
    """
    Reconstruct level-scale forecasts from differenced-scale forecasts using
    the tail of the original history y_hist.

    Accepts w_fcst of shape (n,) or (n_reps, n); the cumulative sum runs along
    the last axis, so a whole ensemble integrates in one call.
    """
    cur = np.asarray(w_fcst, dtype=float)
    y_hist = np.asarray(y_hist, dtype=float)
    for level in range(d, 0, -1):
        base = np.diff(y_hist, n=level - 1)
        cur = base[-1] + np.cumsum(cur, axis=-1)
    return cur


def seasonal_difference(y: np.ndarray, D: int, s: int = SEASONAL_PERIOD) -> np.ndarray:
    """
    Apply the seasonal differencing operator (1 - B^s)^D, i.e. D successive
    passes of X(t) - X(t-s).

    At a monthly timestep with s = 12 this is the operator that removes an
    annual cycle. Ordinary differencing, X(t) - X(t-1), does not: it removes
    trend and slow drift, leaving a twelve-month periodicity essentially
    untouched. The two are different filters and the distinction matters here,
    because the monthly records this project models are strongly seasonal but
    show no unit root at lag 1.
    """
    out = np.asarray(y, dtype=float)
    for _ in range(int(D)):
        if len(out) <= s:
            raise ValueError(
                f"Series of length {len(out)} is too short for a lag-{s} difference."
            )
        out = out[s:] - out[:-s]
    return out


def integrate_seasonal(y_hist: np.ndarray, w_fcst: np.ndarray, D: int,
                       s: int = SEASONAL_PERIOD) -> np.ndarray:
    """
    Invert (1 - B^s)^D: reconstruct the level scale from a seasonally
    differenced series, anchored on the last s values of y_hist.

    With D = 1 the relation X(t) = X(t-s) + w(t) splits the series into s
    independent chains, one per phase of the cycle (all Januaries, all
    Februaries, ...). Each chain is a plain cumulative sum started from the
    corresponding month of the final year of history, so the inversion is s
    interleaved cumulative sums rather than the single one that inverts
    ordinary differencing.

    Accepts w_fcst of shape (n,) or (n_reps, n).
    """
    cur = np.array(w_fcst, dtype=float)
    y_hist = np.asarray(y_hist, dtype=float)
    for level in range(int(D), 0, -1):
        base = seasonal_difference(y_hist, level - 1, s)
        if len(base) < s:
            raise ValueError(
                f"History of length {len(y_hist)} is too short to anchor a "
                f"lag-{s} integration of order {D}."
            )
        anchor = base[len(base) - s:]
        for j in range(s):
            cur[..., j::s] = anchor[j] + np.cumsum(cur[..., j::s], axis=-1)
    return cur


def apply_differencing(y: np.ndarray, d: int, D: int = 0,
                       s: int = SEASONAL_PERIOD) -> np.ndarray:
    """Apply the full differencing operator (1 - B)^d (1 - B^s)^D to y."""
    return difference(seasonal_difference(y, D, s), d)


def invert_differencing(y_hist: np.ndarray, w: np.ndarray, d: int, D: int = 0,
                        s: int = SEASONAL_PERIOD) -> np.ndarray:
    """
    Invert (1 - B)^d (1 - B^s)^D, the reverse of :func:`apply_differencing`.

    The two operators are inverted in the opposite order to that in which they
    were applied: the ordinary integration is anchored on the *seasonally
    differenced* history, and the seasonal integration is then anchored on the
    original history.
    """
    cur = np.asarray(w, dtype=float)
    if d > 0:
        cur = integrate_forecasts(seasonal_difference(y_hist, D, s), cur, d)
    if D > 0:
        cur = integrate_seasonal(y_hist, cur, D, s)
    return cur


# ----------------------------------------------------------------------------
# ARIMA(p, d, q) by conditional sum of squares
# ----------------------------------------------------------------------------
class ARIMA:
    """
    ARIMA(p, d, q)(0, D, 0)[s] with a constant, estimated by conditional sum
    of squares.

    The series is differenced by (1 - B)^d (1 - B^s)^D; an ARMA(p, q) model
    with intercept c is then fitted to the differenced series w:

        w_t = c + sum_i phi_i w_{t-i} + e_t + sum_j theta_j e_{t-j}

    AR(p) models (q = 0) are solved exactly by OLS; mixed models use SciPy's
    optimiser on the conditional sum of squared errors.

    The seasonal part follows the standard multiplicative form

        phi(B) PHI(B^s) (1-B)^d (1-B^s)^D w_t = c + theta(B) THETA(B^s) e_t

    At a monthly timestep with s = 12, seasonal differencing removes the
    annual cycle, which ordinary differencing does not do at any order of d.
    A seasonal moving-average term is usually needed alongside it: seasonal
    differencing of a largely deterministic cycle induces a strong negative
    autocorrelation at lag s, which the non-seasonal terms cannot absorb.
    """

    def __init__(self, order=(1, 0, 0), seasonal_order=(0, 0, 0),
                 s=SEASONAL_PERIOD):
        self.p, self.d, self.q = order
        self.order = tuple(order)
        self.P, self.D, self.Q = seasonal_order
        self.seasonal_order = tuple(seasonal_order)
        self.s = int(s)
        self.c = 0.0
        self.phi = np.zeros(self.p)
        self.theta = np.zeros(self.q)
        self.Phi = np.zeros(self.P)
        self.Theta = np.zeros(self.Q)
        self.sigma2 = None
        self.aic = None
        self.bic = None
        self.nobs = None
        self.resid_ = None
        self._y_train = None
        self._XtX_inv = None

    # -- internal: multiplicative seasonal form -> plain coefficient vectors --
    def _expand(self, phi, theta, Phi, Theta):
        """
        Expand the multiplicative seasonal form into plain AR and MA
        coefficient vectors.

        Convolving phi(B) with PHI(B^s), and theta(B) with THETA(B^s), yields
        an equivalent ARMA whose coefficient vectors are long but mostly zero:
        an ARIMA(1,0,0)(0,1,1)[12] expands to one AR coefficient and thirteen
        MA coefficients, of which only the 1st and 12th (and their product at
        lag 13) are non-zero. The conditional-sum-of-squares recursion then
        runs unchanged, so there is one estimation path for the whole family
        rather than a separate seasonal one.
        """
        s = self.s
        phi = np.asarray(phi, dtype=float)
        theta = np.asarray(theta, dtype=float)
        Phi = np.asarray(Phi, dtype=float)
        Theta = np.asarray(Theta, dtype=float)

        ar_poly = np.concatenate([[1.0], -phi]) if len(phi) else np.array([1.0])
        if len(Phi):
            sar = np.zeros(len(Phi) * s + 1)
            sar[0] = 1.0
            for k, val in enumerate(Phi, start=1):
                sar[k * s] = -val
            ar_poly = np.convolve(ar_poly, sar)

        ma_poly = np.concatenate([[1.0], theta]) if len(theta) else np.array([1.0])
        if len(Theta):
            sma = np.zeros(len(Theta) * s + 1)
            sma[0] = 1.0
            for k, val in enumerate(Theta, start=1):
                sma[k * s] = val
            ma_poly = np.convolve(ma_poly, sma)

        return -ar_poly[1:], ma_poly[1:]

    def _full(self):
        """Expanded AR/MA coefficient vectors for the current parameters."""
        return self._expand(self.phi, self.theta, self.Phi, self.Theta)

    def _cond(self):
        """Observations consumed before the CSS recursion can start."""
        phi_full, theta_full = self._full()
        return max(len(phi_full), len(theta_full))

    # -- internal: conditional residuals for a differenced series w ----------
    def _css_resid(self, w, c, phi, theta):
        """Conditional residuals given *expanded* AR/MA coefficient vectors."""
        phi = np.asarray(phi, dtype=float)
        theta = np.asarray(theta, dtype=float)
        p, q = len(phi), len(theta)
        m = max(p, q)
        n = len(w)
        e = np.zeros(n)
        for t in range(m, n):
            ar = np.dot(phi, w[t - p:t][::-1]) if p else 0.0
            ma = np.dot(theta, e[t - q:t][::-1]) if q else 0.0
            e[t] = w[t] - c - ar - ma
        return e

    def _pack(self):
        return np.concatenate([[self.c], self.phi, self.theta, self.Phi, self.Theta])

    def _unpack(self, x):
        p, q, P, Q = self.p, self.q, self.P, self.Q
        c = x[0]
        phi = x[1:1 + p]
        theta = x[1 + p:1 + p + q]
        Phi = x[1 + p + q:1 + p + q + P]
        Theta = x[1 + p + q + P:1 + p + q + P + Q]
        return c, phi, theta, Phi, Theta

    def label(self) -> str:
        """Model order as it is reported in the thesis and the web app."""
        base = f"ARIMA({self.p}, {self.d}, {self.q})"
        if self.P or self.D or self.Q:
            base += f"({self.P}, {self.D}, {self.Q})[{self.s}]"
        return base

    @classmethod
    def from_params(cls, order, c, phi, theta, y, seasonal_order=(0, 0, 0),
                    s=SEASONAL_PERIOD, Phi=None, Theta=None):
        """
        Build a model from coefficients that were estimated earlier, instead of
        re-estimating them.

        The expensive part of :meth:`fit` is the optimiser, which evaluates the
        conditional sum of squares many times over. Given the coefficients
        already reported in data/results.json, a single pass is enough to
        recover the residuals and the error variance, which is all the
        forecasting and bias-correction methods need. Used by the web app so it
        starts in seconds rather than re-fitting on every cold start, and it
        forecasts from exactly the coefficients reported in the thesis.
        """
        self = cls(tuple(order), tuple(seasonal_order), s)
        self.c = float(c)
        self.phi = np.asarray(phi, dtype=float)
        self.theta = np.asarray(theta, dtype=float)
        self.Phi = np.asarray(Phi if Phi is not None else [], dtype=float)
        self.Theta = np.asarray(Theta if Theta is not None else [], dtype=float)

        y = np.asarray(y, dtype=float)
        self._y_train = y
        w = apply_differencing(y, self.d, self.D, self.s)
        self._w_train = w
        phi_full, theta_full = self._full()
        m = max(len(phi_full), len(theta_full))
        resid = self._css_resid(w, self.c, phi_full, theta_full)[m:]
        self.resid_ = resid
        self.nobs = len(w) - m
        self.sigma2 = float(np.dot(resid, resid)) / self.nobs
        return self

    def fit(self, y, cond=None):
        """Fit the model to series y (here: log-discharge of the training set).

        cond : if given, the number of initial observations on which to condition
               the comparable information criteria (aic_c/bic_c), so that all
               candidate orders are ranked on an identical sample.
        """
        y = np.asarray(y, dtype=float)
        self._y_train = y
        w = apply_differencing(y, self.d, self.D, self.s)
        p, q, P, Q = self.p, self.q, self.P, self.Q
        m = self._cond()
        n_eff = len(w) - m
        k = p + q + P + Q + 1 + 1  # AR + MA + seasonal + constant + variance
        self._w_train = w

        self._XtX_inv = None
        if q == 0 and P == 0 and Q == 0:
            # Exact OLS for pure AR(p) (with constant). The multiplicative
            # seasonal form is nonlinear in its parameters, so this shortcut
            # only applies when there are no seasonal AR/MA terms.
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
                beta, resid, XtX_inv = _ols(X, target)
                self.c = float(beta[0])
                self.phi = beta[1:]
                self._XtX_inv = XtX_inv
        else:
            # CSS optimisation for ARMA(p, q)(P, Q)[s]
            x0 = np.zeros(1 + p + q + P + Q)
            x0[0] = w.mean() * (1.0 - 0.5)
            if p:
                x0[1] = 0.3
            if Q:
                # Seasonal differencing leaves a strong negative spike at lag
                # s; start the seasonal MA near the value that absorbs it.
                x0[1 + p + q + P] = -0.5

            def obj(x):
                c, phi, theta, Phi_, Theta_ = self._unpack(x)
                phi_f, theta_f = self._expand(phi, theta, Phi_, Theta_)
                with np.errstate(over="ignore", invalid="ignore"):
                    e = self._css_resid(w, c, phi_f, theta_f)[m:]
                    ssr = np.dot(e, e)
                if not np.isfinite(ssr) or ssr <= 0:
                    return 1e12
                return 0.5 * n_eff * np.log(ssr / n_eff + 1e-12)

            bounds = [(None, None)] + [(-0.999, 0.999)] * (p + q + P + Q)
            res = minimize(obj, x0, method="L-BFGS-B", bounds=bounds)
            self.c, self.phi, self.theta, self.Phi, self.Theta = self._unpack(res.x)
            phi_full, theta_full = self._full()
            resid = self._css_resid(w, self.c, phi_full, theta_full)[m:]

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

    # -- parameter uncertainty ------------------------------------------------
    def standard_errors(self) -> dict:
        """
        Asymptotic standard errors of the estimated coefficients (c, phi,
        theta) -- the piece of the estimation this project's supervisor
        singled out as missing ("how do you estimate the parameters? that's
        where the work is").

        For pure AR(p) (q = 0) these are the exact OLS standard errors from
        the fit's normal equations. For mixed ARMA(p, q) (q > 0), estimated
        by conditional sum of squares, they come from the numerical Hessian
        of the (Gaussian) conditional log-likelihood at the optimum:
        Cov(theta_hat) ~= [Hessian(-logL)]^-1 -- the standard asymptotic
        result for CSS/ML ARMA estimation (Box, Jenkins & Reinsel, 2008,
        ch. 7). NaN entries mean the Hessian was not (numerically) positive
        definite at the optimum, typically a coefficient pinned near its
        stationarity/invertibility bound.

        Returns {"c": se, "phi": [...], "theta": [...], "Phi": [...],
        "Theta": [...]}.
        """
        p, q, P, Q = self.p, self.q, self.P, self.Q
        if q == 0 and P == 0 and Q == 0:
            if p == 0 or self._XtX_inv is None:
                se_c = float(np.sqrt(self.sigma2 / self.nobs)) if self.nobs else float("nan")
                return {"c": se_c, "phi": [], "theta": [], "Phi": [], "Theta": []}
            se = np.sqrt(np.diag(self._XtX_inv) * self.sigma2)
            return {"c": float(se[0]), "phi": se[1:].tolist(), "theta": [],
                    "Phi": [], "Theta": []}

        # Mixed ARMA: numerical Hessian of the CSS negative log-likelihood
        # (up to the parameter-independent constants of the Gaussian
        # log-likelihood, which don't affect the Hessian).
        w = self._w_train
        m = self._cond()
        n_eff = len(w) - m
        k = 1 + p + q + P + Q

        def negloglik(x):
            c, phi, theta, Phi_, Theta_ = self._unpack(x)
            phi_f, theta_f = self._expand(phi, theta, Phi_, Theta_)
            with np.errstate(over="ignore", invalid="ignore"):
                e = self._css_resid(w, c, phi_f, theta_f)[m:]
                ssr = np.dot(e, e)
            if not np.isfinite(ssr) or ssr <= 0:
                return 1e12
            return 0.5 * n_eff * np.log(ssr / n_eff + 1e-12)

        x0 = self._pack()
        h = 1e-4 * np.maximum(np.abs(x0), 1e-2)
        H = np.zeros((k, k))
        for i in range(k):
            for j in range(i, k):
                xpp, xpm = x0.copy(), x0.copy()
                xmp, xmm = x0.copy(), x0.copy()
                xpp[i] += h[i]; xpp[j] += h[j]
                xpm[i] += h[i]; xpm[j] -= h[j]
                xmp[i] -= h[i]; xmp[j] += h[j]
                xmm[i] -= h[i]; xmm[j] -= h[j]
                H[i, j] = H[j, i] = (
                    negloglik(xpp) - negloglik(xpm) - negloglik(xmp) + negloglik(xmm)
                ) / (4 * h[i] * h[j])

        try:
            cov = np.linalg.inv(H)
            diag = np.diag(cov)
            se_all = np.where(diag >= 0, np.sqrt(np.maximum(diag, 0)), np.nan)
        except np.linalg.LinAlgError:
            se_all = np.full(k, np.nan)

        return {
            "c": float(se_all[0]),
            "phi": se_all[1:1 + p].tolist(),
            "theta": se_all[1 + p:1 + p + q].tolist(),
            "Phi": se_all[1 + p + q:1 + p + q + P].tolist(),
            "Theta": se_all[1 + p + q + P:1 + p + q + P + Q].tolist(),
        }

    # -- diagnostics ---------------------------------------------------------
    def _psi_weights(self, nmax):
        """MA(infinity) weights of the integrated model
        phi(B)PHI(B^s)(1-B)^d (1-B^s)^D / theta(B)THETA(B^s)."""
        phi_full, theta_full = self._full()
        phi_poly = (np.concatenate([[1.0], -phi_full]) if len(phi_full)
                    else np.array([1.0]))
        diff_poly = np.array([1.0])
        for _ in range(self.d):
            diff_poly = np.convolve(diff_poly, [1.0, -1.0])
        seasonal_op = np.zeros(self.s + 1)
        seasonal_op[0], seasonal_op[self.s] = 1.0, -1.0
        for _ in range(self.D):
            diff_poly = np.convolve(diff_poly, seasonal_op)
        ar_poly = np.convolve(phi_poly, diff_poly)    # 1 - a1 B - a2 B^2 - ...
        a = -ar_poly[1:]
        n_ar = len(a)
        n_ma = len(theta_full)
        psi = np.zeros(nmax)
        psi[0] = 1.0
        for j in range(1, nmax):
            s = 0.0
            for i in range(1, min(j, n_ar) + 1):
                s += a[i - 1] * psi[j - i]
            if 1 <= j <= n_ma:
                s += theta_full[j - 1]
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
        # Roots of the expanded polynomials, so the seasonal factors are
        # included: a multiplicative model is invertible only if both its
        # non-seasonal and seasonal MA factors are.
        phi_full, theta_full = self._full()
        ma_poly = (np.concatenate([[1.0], theta_full]) if len(theta_full)
                   else np.array([1.0]))
        ma_mod = (sorted(np.abs(np.roots(ma_poly[::-1])).tolist())
                  if len(theta_full) else [])
        return {"ar": _moduli(phi_full), "ma": ma_mod}

    # -- forecasting ---------------------------------------------------------
    def _forecast_diff(self, w_hist, e_hist, k):
        """Recursive k-step forecast on the differenced scale."""
        phi_full, theta_full = self._full()
        p, q = len(phi_full), len(theta_full)
        y_ext = list(w_hist)
        e_ext = list(e_hist)
        preds = []
        for _ in range(k):
            idx = len(y_ext)
            ar = sum(phi_full[j] * y_ext[idx - 1 - j] for j in range(p)) if p else 0.0
            ma = sum(theta_full[j] * e_ext[idx - 1 - j] for j in range(q)) if q else 0.0
            val = self.c + ar + ma
            preds.append(val)
            y_ext.append(val)
            e_ext.append(0.0)
        return np.array(preds)

    def forecast(self, k):
        """k-step forecast (level scale) from the end of the training series."""
        return self.forecast_from(self._y_train, k)

    def forecast_from(self, y_hist, k):
        """
        k-step forecast (level scale) from the end of an arbitrary history.

        Same recursion as :meth:`forecast`, but the origin is wherever y_hist
        ends rather than the end of the training series, so a forecast can be
        issued from any point in the record using only the data up to that
        point. This is the single-origin form of :meth:`rolling_kstep`.
        """
        y_hist = np.asarray(y_hist, dtype=float)
        w = apply_differencing(y_hist, self.d, self.D, self.s)
        phi_full, theta_full = self._full()
        e = self._css_resid(w, self.c, phi_full, theta_full)
        w_fcst = self._forecast_diff(w, e, k)
        return invert_differencing(y_hist, w_fcst, self.d, self.D, self.s)

    def rolling_kstep(self, y_full, k, start_idx):
        """
        Rolling-origin k-step forecasts with fixed (already estimated)
        parameters. For every origin t with start_idx <= t+k <= len-1 the model
        forecasts y_full[t+k] using only information up to and including t.

        Returns (targets_index, y_pred) arrays aligned on the forecast target.
        """
        y_full = np.asarray(y_full, dtype=float)
        w_full = apply_differencing(y_full, self.d, self.D, self.s)
        phi_full, theta_full = self._full()
        e_full = self._css_resid(w_full, self.c, phi_full, theta_full)
        n = len(y_full)
        origins = []
        preds = []
        # Differencing shortens the series by d + s*D, so the differenced index
        # corresponding to level-scale origin t is offset by that much.
        offset = self.d + self.s * self.D
        for t in range(start_idx - 1, n - k):
            nd = t - offset  # last available differenced index
            if nd < self._cond():
                continue
            w_hist = w_full[: nd + 1]
            e_hist = e_full[: nd + 1]
            w_fcst = self._forecast_diff(w_hist, e_hist, k)
            y_fcst = invert_differencing(y_full[: t + 1], w_fcst, self.d,
                                         self.D, self.s)
            origins.append(t + k)
            preds.append(y_fcst[-1])
        return np.array(origins), np.array(preds)
