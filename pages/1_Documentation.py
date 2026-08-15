"""
pages/1_Documentation.py — Documentation and user guide for the statistical
(ARIMA) hydrological forecasting app.

Rewritten 2026-08-12 for the monthly, three-variable, stochastic-validation
pipeline.
"""
import json
from pathlib import Path
import streamlit as st

COLOR_PRIMARY = "#2563EB"
COLOR_TEXT = "#1E293B"
COLOR_SURFACE = "#EFF6FF"
COLOR_BORDER = "#CBD5E1"

ROOT = Path(__file__).resolve().parent.parent
try:
    with open(ROOT / "data" / "results.json") as f:
        R = json.load(f)
except Exception:
    R = {}

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Raleway:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap');
    html, body, [class*="css"] {{ font-family: 'Raleway', system-ui, sans-serif; color: {COLOR_TEXT}; }}
    h1 {{ font-weight: 800 !important; color: {COLOR_TEXT} !important; font-size: 1.9rem !important;
         letter-spacing: -0.02em; }}
    h2 {{ color: {COLOR_TEXT} !important; font-size: 1.05rem !important; font-weight: 700 !important;
         text-transform: uppercase; letter-spacing: 0.06em; margin-top: 2rem !important;
         border-left: 3px solid {COLOR_PRIMARY}; padding-left: 0.6rem; }}
    h3 {{ color: {COLOR_PRIMARY} !important; font-size: 1rem !important; font-weight: 700 !important;
         margin-top: 1.25rem !important; }}
    p, li {{ font-size: 0.97rem; line-height: 1.7; }}
    code {{ font-family: 'JetBrains Mono', monospace; background: {COLOR_SURFACE}; padding: 0.15em 0.45em;
         border-radius: 4px; font-size: 0.85em; color: {COLOR_PRIMARY}; }}
    .block-container {{ max-width: 900px; padding-top: 1.25rem; padding-bottom: 3rem; }}
    .callout {{ background: {COLOR_SURFACE}; border-left: 4px solid {COLOR_PRIMARY}; border-radius: 0 10px 10px 0;
         padding: 0.9rem 1.15rem; margin: 1rem 0; font-size: 0.94rem; line-height: 1.65; }}
    .callout strong {{ color: {COLOR_PRIMARY}; }}
    .eq-box {{ background: #F1F5F9; border: 1px solid {COLOR_BORDER}; border-radius: 10px; padding: 0.75rem 1.25rem;
         margin: 0.6rem 0; font-family: 'JetBrains Mono', monospace; font-size: 0.88rem; color: {COLOR_TEXT}; line-height: 1.9; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; margin: 0.75rem 0; }}
    th {{ background: {COLOR_PRIMARY}; color: white; padding: 0.5rem 0.75rem; text-align: left; font-weight: 600; }}
    td {{ padding: 0.45rem 0.75rem; border-bottom: 1px solid {COLOR_BORDER}; }}
    tr:nth-child(even) td {{ background: #F8FAFC; }}
    </style>
    """,
    unsafe_allow_html=True,
)

variables = R.get("variables", {})
basin = R.get("basin", "Conecuh River at Brantley, Alabama (USGS 02371500)")

st.title("How This Works")
st.caption(
    "River Outlook  ·  Conecuh River at Brantley, Alabama  ·  "
    "Ugbodaga Benedict Osikpemi  ·  2026"
)

st.markdown(
    """<div class="callout">
    <strong>In one sentence:</strong> we don't try to guess one exact number for next month's
    river flow, rainfall, or water level &mdash; instead, we generate a thousand plausible
    versions of the future and show you the range they land in, checked against 35 years of
    real history. The rest of this page explains that in as much or as little detail as you
    want: what the app does, the method behind it, and how to read what it shows you.
    </div>""",
    unsafe_allow_html=True,
)

# 1 ---------------------------------------------------------------------------
st.markdown("## 1. What This App Does")
st.markdown(
    f"""
This application forecasts **monthly discharge, rainfall, and stage** for the
**{basin}** using three separate statistical time-series models, one per variable.

Each is a **statistical ARIMA model** (Box&ndash;Jenkins methodology) that learns a
variable's temporal behaviour directly from its own historical record and projects
that behaviour forward -- no rainfall-runoff routing, no cross-variable input, and
(critically) **no single "correct" forecast**: because the model is stochastic, it
produces an **ensemble of plausible future sequences**, not one number.
"""
)
st.markdown(
    """<div class="callout">
    <strong>Why three separate models instead of one?</strong> The same ARIMA machinery applies
    to any series that fits its assumptions -- streamflow, rainfall, water level, even stock
    prices. Rather than building one model to predict discharge and hoping it generalises,
    this app estimates three independent models, one per variable, and shows that the same
    identification/estimation/validation procedure works for all three.
    </div>""",
    unsafe_allow_html=True,
)

# 2 ---------------------------------------------------------------------------
st.markdown("## 2. The Method — How the Model Works")
st.markdown(
    """
Each model belongs to the **ARIMA(p, d, q)** family (Box & Jenkins, 1976), which describes
a time series using three ingredients:

- **AR (autoregressive), order p** — the current value depends on its own *p* previous
  monthly values.
- **I (integrated), order d** — the series is *differenced* *d* times to remove trend or
  slow drift and make it stationary.
- **MA (moving average), order q** — the current value depends on the *q* previous random
  shocks.

Related, simpler members of the same family exist -- a pure **AR(p)** model (no MA term),
a pure **MA(q)** model (no AR term), an **ARMA(p, q)** model (no differencing, i.e. d = 0),
and **ARIMAX**, which adds exogenous input variables. This project uses plain ARIMA, not
ARIMAX, deliberately: each variable is forecast from its own past only, by design, so
there is no exogenous driver to add.
"""
)
st.markdown("### What differencing does, and does not, do")
st.markdown(
    """
This is worth stating precisely, because it is easy to overstate. Ordinary ARIMA
differencing forms

$$X_t - X_{t-1}$$

which removes a **trend or slow drift in level**. It does *not*, by itself, remove an
annual seasonal cycle. Removing an annual cycle from monthly data requires **seasonal
differencing**,

$$X_t - X_{t-12}$$

or the seasonal terms of a **SARIMA** model.

So the reason this project moved from a daily to a monthly timestep is narrower than
"differencing removes the seasonality". Ordinary differencing of a daily river series
gains little, because such a series does not genuinely trend over a single day. Monthly
aggregation strips the short-term noise and **exposes** the annual cycle and any slow
drift clearly enough that the differencing order *d* becomes a meaningful thing to test
for. It does not turn ordinary differencing into a seasonal filter.

What the stationarity tests actually selected for this basin was **d = 0** for all three
variables, so these models do not difference the series at all. The seasonal structure
that consequently remains in the discharge and stage residuals (Section 5) is an
acknowledged reason to investigate SARIMA in future work.
"""
)
st.markdown("### Working on log-transformed values")
st.markdown(
    """
Streamflow, rainfall, and stage are all strictly positive and right-skewed, with
variability that grows with magnitude, so each model is fitted to the **natural
logarithm** of its variable. This stabilises variance and stops a few extreme months
from dominating the fit. Values are converted back to natural units by exponentiation.

**The order of that back-transformation matters,** and is a standard source of bias
worth being explicit about. Exponentiating a single *expected value* computed on the log
scale does not give you the mean in natural units — because the exponential is convex,
`exp(E[ln X])` estimates the **median** of X, not its arithmetic mean, and recovering
the mean would require a retransformation correction (the log-normal factor
`exp(σ²/2)`, or Duan's 1983 smearing estimator).

No such correction is applied here, and none is needed, because this pipeline never
exponentiates an expected value. Each of the 1,000 simulated sequences is exponentiated
**individually**, and every reported statistic — means, percentiles, the 90% envelope,
the seven validation properties — is computed afterwards on the natural-scale ensemble.
Monte Carlo integration over the ensemble handles the log-normal skew automatically, so
the ensemble mean is unbiased by construction. (Duan's smearing factor is still computed
as a diagnostic and stored with the results, but it multiplies nothing.)

Where the River Outlook page draws a single line through the band, that line is labelled
as the ensemble **median**, because that is the quantity it is.
"""
)
st.markdown("### The model equation")
st.markdown(
    """<div class="eq-box">
    Let z(t) = ln[X(t)] for variable X, and w(t) = (1 &minus; B)<sup>d</sup> z(t) be the
    differenced series.<br><br>
    w(t) = c + &phi;<sub>1</sub> w(t&minus;1) + &hellip; + &phi;<sub>p</sub> w(t&minus;p)
    + a(t) + &theta;<sub>1</sub> a(t&minus;1) + &hellip; + &theta;<sub>q</sub> a(t&minus;q)<br><br>
    where &phi; are the autoregressive coefficients, &theta; the moving-average coefficients,
    c a constant, and a(t) a white-noise error term.
    </div>""",
    unsafe_allow_html=True,
)

# 3 ---------------------------------------------------------------------------
st.markdown("## 3. How Each Model Was Built (Box-Jenkins)")
st.markdown(
    """
1. **Stationarity testing.** The Augmented Dickey&ndash;Fuller (ADF) and KPSS tests are
   applied, jointly, to decide each variable's differencing order d.
2. **Order identification.** The autocorrelation (ACF) and partial autocorrelation (PACF)
   functions of the (differenced) training series suggest candidate AR and MA orders.
3. **Estimation.** Coefficients are estimated by **conditional sum of squares** (pure AR
   models solved exactly by ordinary least squares), together with a **standard error on
   every coefficient** -- from the OLS normal equations for pure-AR models, or from the
   numerical Hessian of the conditional log-likelihood for mixed ARMA models. This is the
   step that answers "how do you estimate the parameters", not just "what order did you
   pick" -- the two are different questions.
4. **Order selection.** All candidate orders are ranked by the **Akaike Information
   Criterion (AIC)**, which balances fit against parsimony.
5. **Diagnostic check.** The **Ljung&ndash;Box**, **ARCH**, and **Jarque&ndash;Bera** tests
   check, respectively, whether residual autocorrelation remains, whether volatility
   clustering is present, and whether residuals are normally distributed.
"""
)
if variables:
    rows = "".join(
        f"<tr><td>{v.capitalize()}</td><td>ARIMA{tuple(r['order'])}</td>"
        f"<td>{r['differencing_d']}</td><td>{r['aic']:.1f}</td>"
        f"<td>{r['diagnostics']['ljung_box']['pvalue']:.4f}</td></tr>"
        for v, r in variables.items()
    )
    st.markdown(
        f"""
<table>
<tr><th>Variable</th><th>Selected model</th><th>d</th><th>AIC</th><th>Ljung-Box p</th></tr>
{rows}
</table>
""",
        unsafe_allow_html=True,
    )

# 4 ---------------------------------------------------------------------------
st.markdown("## 4. Data")
st.markdown(
    f"""
| Item | Detail |
|------|--------|
| **Basin** | {basin} |
| **Variables** | Discharge (m&sup3;/s), rainfall (mm/month), stage (m) -- three independent series |
| **Timestep** | Monthly (aggregated from daily USGS/CAMELS records) |
| **Record** | Jan 1980 &ndash; Dec 2014 (420 months) |
| **Training** | 1980&ndash;2003 (model identification & estimation) |
| **Validation** | 2004&ndash;2014 (out-of-sample property-based assessment) |
| **Source** | USGS NWIS (discharge, stage); CAMELS/Daymet basin-mean forcing (rainfall) |

Discharge and stage come directly from USGS gauge 02371500; rainfall is the Daymet
basin-mean product from the CAMELS archive for the same basin (the only one of the three
rainfall products in that archive with zero missing days across the full record).
"""
)

# 5 ---------------------------------------------------------------------------
st.markdown("## 5. Stochastic, Property-Based Validation")
st.markdown(
    """
Earlier versions of this project validated forecasts by comparing a single predicted
value against the single observed value that followed -- the standard approach for a
*deterministic* forecast. That approach does not fit a *stochastic* model: each run of a
stochastic model produces a different random realisation, so comparing one realisation to
the one sequence that actually happened conflates model skill with random chance. What
should be reproducible is not the exact path but the **statistical properties** of the
process -- its mean, variability, persistence, seasonality, and extremes -- which is what
matters for applications like sizing a reservoir or a spillway.

Validation here works as follows: each model, fitted on the training period, generates an
**ensemble of independent synthetic sequences** spanning the validation period. Each
sequence is characterised by seven summary statistics (mean, standard deviation, skewness,
month-to-month persistence, seasonal amplitude, longest dry spell, and peak value), and the
**actual historical validation-period record is checked against the ensemble's spread**:
if the historical value for a property falls within the ensemble's 5th-95th percentile
range, that property is judged reproduced.
"""
)
if variables:
    rows = "".join(
        f"<tr><td>{v.capitalize()}</td>"
        f"<td>{r['validation_n_within']} / {r['validation_n_total']}</td></tr>"
        for v, r in variables.items()
    )
    st.markdown(
        f"""
<table>
<tr><th>Variable</th><th>Properties within 90% synthetic envelope</th></tr>
{rows}
</table>
""",
        unsafe_allow_html=True,
    )
st.markdown(
    """
This is a stricter, more honest test than it might look: a wide synthetic envelope that
contains everything is not informative, so the envelope width itself (visible in the
River Outlook charts) is part of what should be judged, not just whether the historical
value happens to fall inside it.

**What this score is not.** A result such as 7/7 means that seven selected historical
properties fell within the simulated 90% envelopes. It is evidence of *property
reproduction*. It is **not** point-forecast accuracy, **not** a percentage correct,
**not** a prediction error, and **not** a statement about the reliability of any
individual future value.

**A stochastic forecast can still be compared with observations.** It would be too
absolute to say that comparing simulations with real data is meaningless. What is
inappropriate is judging a *single* random realisation as though it were a deterministic
forecast — any one run carries no obligation to match the one sequence that happened.
But the observation can legitimately be evaluated against the *full predictive
distribution*, using prediction-interval coverage, the continuous ranked probability
score (CRPS), the logarithmic score, calibration plots, rank histograms, or the Brier
score for threshold exceedance. The property-based validation used here is one such
distribution-level comparison, chosen because the properties it tests are the ones that
govern water-resources design. The scores just listed are complementary to it, not ruled
out by it, and are noted as future work in the report.
"""
)

# 6 ---------------------------------------------------------------------------
st.markdown("## 6. How to Use the App")
st.markdown(
    """
1. Go to the **River Outlook** page.
2. Set the range you want with **Predict from [month] [year] to [month] [year]**, or hit
   one of the jump-to-range presets. The record ends December 2014, so every predictable
   month is after that.
3. Press **Get the Outlook** -- one click forecasts all three variables together.

Because the model is stochastic, each click generates a fresh random ensemble -- the
exact synthetic paths will differ between runs, and that is expected, not a bug. What
you'll see:
- **Three cards**, one per variable, each with a plain-English summary sentence, a
  headline number, and two small tags: a trend (rising / falling / steady) and how the
  level compares to what's typical.
- **A chart per variable** showing recent history, the range of plausible futures, and
  the ensemble **median** path through the middle of that range (a median, not a
  prediction -- see "Working on log-transformed values" above).
- **A "track record" tag** on each card, showing how many of seven statistical
  properties of the real 2004-2014 record fell inside the simulated 90% envelope. This
  is evidence of property reproduction, not a forecast-accuracy percentage.
- **A "for the curious" section** at the bottom with the full statistical detail
  (model orders, coefficients, diagnostics) for anyone who wants it.
"""
)

# 7 ---------------------------------------------------------------------------
st.markdown("## 7. Limitations")
st.markdown(
    """
| Limitation | Implication |
|-----------|-------------|
| **Univariate per variable** | Each model uses only its own past; discharge cannot anticipate a rainfall event that has not yet reached the river. |
| **Non-seasonal ARIMA** | No explicit seasonal (P, D, Q, 12) terms. Residuals should resemble white noise for a satisfactory fit; the Ljung-Box test **rejects** that for discharge and for stage (see Section 3 for the p-values) and does **not** reject it for rainfall. Rainfall therefore has the cleanest statistical fit of the three; discharge and stage retain unexplained temporal structure, most plausibly seasonal. Acknowledged, not hidden -- and the direct reason SARIMA is the leading item of future work. |
| **Linear model** | Catchment response during extreme events is partly non-linear and not fully captured. |
| **Gaussian innovations** | The synthetic ensembles draw innovations from a Normal distribution fitted to the residuals; residual diagnostics show heavier tails than Normal for some variables, so extreme-tail synthetic values may be somewhat under-dispersed. |
| **Primary basin** | The full stochastic property-based validation covers this basin only. A supplementary check reran the identification and estimation procedure, unmodified, on two further CAMELS basins (one arid, one humid continental with snow) for discharge and rainfall: it ran cleanly on both, but its qualitative findings did not universally repeat, and two of the four extra fits showed numerical warning signs. So the *procedure* transfers; the *specific results* are not claimed to. Full replication -- stage included, with the complete 1,000-member validation -- at other basins remains to be done. |
| **Long horizons are conditional** | The model is mathematically defined at any lead time, so the app will answer for any year you ask for. That is not the same as being reliable that far out: every run assumes the process estimated from 1980-2003 continues unchanged, which climate change, land-use change, reservoir construction, river engineering, urbanisation, or a change to the gauge would each break. Read long-range output as a **synthetic scenario** consistent with this river's historical statistics -- what a design calculation needs -- not as a prediction of the river in a given future year. |
"""
)

# 8 ---------------------------------------------------------------------------
st.markdown("## 8. Technical Details")
st.markdown(
    """
**Software stack:** Python, NumPy, SciPy, Pandas, Matplotlib, Streamlit. The ARIMA
estimation, stationarity tests, ACF/PACF, conditional-sum-of-squares optimisation,
parameter standard errors, and the Ljung&ndash;Box/ARCH/Jarque&ndash;Bera tests are
implemented directly from their defining equations (self-contained, no external
time-series library).

```
finals_project/
├── app.py                 ← navigation entrypoint
├── pages/
│   ├── 0_Forecast.py      ← forecast tool (stochastic, per-variable)
│   └── 1_Documentation.py ← this page
├── src/
│   ├── preprocess.py      ← monthly loaders (discharge, rainfall, stage)
│   ├── model.py           ← ARIMA + ADF/KPSS/ACF/PACF/Ljung-Box + standard errors
│   ├── calibrate.py       ← stationarity + AIC order selection
│   ├── simulate.py        ← stochastic synthetic-ensemble generation
│   ├── validation.py      ← property-based validation
│   └── metrics.py         ← summary statistics
├── data/results.json      ← per-variable model + validation results
└── run_pipeline.py        ← full pipeline runner
```

**Run locally:**
```
pip install -r requirements.txt
streamlit run app.py
```
"""
)

# 9 ---------------------------------------------------------------------------
st.markdown("## 9. Key References")
st.markdown(
    """
- Addor, N., Newman, A. J., Mizukami, N., & Clark, M. P. (2017). The CAMELS data set.
  *HESS*, 21(10), 5293&ndash;5313.
- Box, G. E. P., Jenkins, G. M., & Reinsel, G. C. (2008). *Time series analysis:
  Forecasting and control* (4th ed.). Wiley.
- Hipel, K. W., & McLeod, A. I. (1994). *Time series modelling of water resources and
  environmental systems*. Elsevier.
- Moriasi, D. N., et al. (2007). Model evaluation guidelines. *Transactions of the ASABE*, 50(3), 885&ndash;900.
- Nash, J. E., & Sutcliffe, J. V. (1970). River flow forecasting through conceptual models: Part I.
  *Journal of Hydrology*, 10(3), 282&ndash;290.
- Newman, A. J., et al. (2015). Development of a large-sample hydrometeorological data set for the
  contiguous USA. *HESS*, 19(1), 209&ndash;223.
- Salas, J. D., Delleur, J. W., Yevjevich, V., & Lane, W. L. (1980). *Applied modeling of hydrologic
  time series*. Water Resources Publications.
"""
)

st.markdown("---")
st.caption(
    "Conecuh River Stochastic Forecaster  ·  "
    "Computer Hydrological Forecasting — Final Year Project  ·  "
    "Ugbodaga Benedict Osikpemi  ·  "
    "Supervisor: Prof. K. O. Aiyesimoju  ·  2026"
)
