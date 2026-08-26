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
meta = R.get("case_study_basin", {})
contrast_meta = R.get("contrast_basin", {})
compare = R.get("method_comparison", {})
basin = meta.get("name", R.get("basin", ""))
disc = R.get("variables", {}).get("discharge", {})
n_years_record = disc.get("n_months", 314) // 12

st.title("How This Works")
st.caption(
    f"River Outlook  ·  {basin}  ·  "
    "  ·  2026"
)

st.markdown(
    f"""<div class="callout">
    <strong>In one sentence:</strong> we don't try to guess the river's flow in any particular
    future month &mdash; instead, we fit a model to {n_years_record} years of Nigerian gauge
    measurements and use it to write out a much longer record of the same river, so that the
    rare floods and droughts a dam or channel has to survive appear often enough to be
    counted. The rest of this page explains that in as much or as little detail as you want:
    what the app does, the method behind it, and how to read what it shows you.
    </div>""",
    unsafe_allow_html=True,
)

# 1 ---------------------------------------------------------------------------
st.markdown("## 1. What This App Does")
st.markdown(
    f"""
This application **generates synthetic monthly discharge records** for the
**{basin}** — sequences of monthly flow, of whatever length you ask for, that
behave statistically like the measured river but are far longer than it.

The reason to want one is practical. This gauge has been read for {n_years_record} years,
which gives {n_years_record} annual maximum flows. A spillway designed against a
1-in-100-year event cannot be sized from {n_years_record} numbers. Fitting a model to those
{n_years_record} years and generating 1,000 years from it gives 1,000 annual maxima drawn
from the same statistical behaviour, and the design flow can then be counted rather than
guessed.

The engine is a **statistical ARIMA model** (Box&ndash;Jenkins methodology) that
learns the river's temporal behaviour from its own historical record — no
rainfall-runoff routing, no cross-variable input, and (critically) **no single
"correct" answer**: because the model is stochastic, generating twice gives two
different records, both equally valid samples.
"""
)
st.markdown(
    """<div class="callout">
    <strong>What it does not do.</strong> It does not predict the discharge of a named
    future month. That quantity is not what the model estimates, and it is not what a
    design calculation uses. The generated record is deliberately not dated: the fitted
    process is stationary, so the record has no particular position in time. It is a
    longer sample of the same river, not a calendar of future events.
    </div>""",
    unsafe_allow_html=True,
)
st.markdown(
    """<div class="callout">
    <strong>Does this only work on rivers?</strong> No. The machinery reads a column of
    numbers, tests it for seasonality and stationarity, searches for the orders that best
    describe it, and generates from the result. Nothing in that sequence knows what the
    numbers measure — the same code applied to rainfall, to water level, or to any other
    series would select its own orders and estimate its own coefficients. Section 4.7 of the
    report tests exactly this, running the identical unmodified program on three different
    variables of a second basin and getting three different answers back. What is fixed here is the
    <em>data</em> the deployed app is wired to, not the method.
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
st.markdown("### How the annual cycle is removed, and why it matters")
st.markdown(
    """
Ordinary ARIMA differencing forms

$$X_t - X_{t-1}$$

which removes a **trend or slow drift in level**. It does *not*, by itself, remove an
annual seasonal cycle, at any order of *d*. That is the single most important thing to
be clear about here, because a monthly river record is dominated by its annual cycle —
at this gauge the twelve monthly averages account for about **half the total variance**
of the series.

There are two standard ways to remove it, and this project uses the second.

**Seasonal differencing** forms

$$X_t - X_{t-12}$$

subtracting from each month the same month a year earlier. This is the SARIMA approach,
and it removes the cycle cleanly. It was tested here, and it fits the measured record
well.

**Seasonal standardisation** instead estimates the average and the spread of each of the
**twelve calendar months**, and rewrites every observation as a departure from its own
month's average, in units of its own month's spread. The cycle is stored as 12 pairs of
numbers and restored when a record is generated.
"""
)
st.markdown(
    """<div class="callout">
    <strong>Why the difference matters here.</strong> Both remove the cycle, and for a
    forecast a few months ahead you could use either. They part company when the object is
    a record thousands of months long. Seasonal differencing leaves an <em>integrated</em>
    process: reconstructing the actual flow requires a running total, and a running total
    of random terms is a random walk, whose spread grows without limit. Over 1,000 years
    the generated series wanders away from the river entirely — in the test run here, to an
    average of around 10<sup>10</sup> m³/s against a measured average of 16.4. Seasonal
    standardisation leaves a <em>stationary</em> process, so a record of any length stays a
    sample of the same distribution. Since generating long records is the whole purpose,
    standardisation is what the model uses. Section 4.2 of the report gives the numbers.
    </div>""",
    unsafe_allow_html=True,
)
st.markdown(
    """
With the cycle removed this way, the stationarity tests select **d = 0** for the
remaining series: ADF rejects a unit root and KPSS does not reject stationarity, so no
further differencing is needed or applied. The **12** seasonal parameters carry the
annual structure; the AR and MA terms describe only the month-to-month departures from
the average year.
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
| **Station** | GRDC 1837401 / GSIM NG_0000012, 12.44&deg;N 10.03&deg;E |
| **Catchment area** | 30,435 km&sup2; |
| **Climate** | Sahelian / semi-arid, single wet season (June-October) |
| **Variable** | Monthly mean discharge (m&sup3;/s) |
| **Record** | 1980-01 &ndash; 2006-02 (314 months, 8 interpolated) |
| **Training** | 1980&ndash;1999 (model identification &amp; estimation) |
| **Validation** | 2000&ndash;2006 (out-of-sample, property-based) |
| **Source** | Nigerian national gauging network, via the Global Runoff Data Centre and the Global Streamflow Indices and Metadata Archive (Do et al., 2018; Gudmundsson et al., 2018) |

The record originates from Nigeria's own gauging network, was archived by the Global
Runoff Data Centre and was quality-controlled and republished with a DOI and an open
licence in the GSIM archive. It needed no institutional data request and can be
re-downloaded by anyone wanting to reproduce this work.

**Why this station, and why this window.** Twenty-four Nigerian stations are held in that
archive. This one has the longest usable record and much the least missing data &mdash;
3.7% of months over 1963&ndash;2006, longest gap three months. The window starts in 1980
because Tiga Dam (1974) changed the river's regime upstream of the gauge and a generating
model needs one consistent regime; independently, 36 of the 44 poorly-gauged months in the
archive fall before 1980 and only 8 after it.

**A second river, as a control.** The Conecuh River at Brantley in Alabama (humid subtropical, rainfall in every month)
is carried through the whole analysis alongside the Hadejia. It is not a second subject of
study. The comparison between the two ways of removing the annual cycle (Section 3 above,
and the "for the curious" panel on the main page) would be worth little if it had been run
on one river only: a single catchment cannot separate a property of the two methods from a
property of that catchment. The two chosen differ about as widely as gauged rivers can.
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
2. Type **how many years** of record you want, or press one of the shortcuts
   (30 / 100 / 500 / 1,000). Any value from 1 to 10,000 is accepted.
3. Optionally set **independent records** -- how many separate records to generate. The
   table shows the first; the statistics and return periods pool all of them, so more
   records means a steadier estimate of the rare events.
4. Press **Generate synthetic record**.

Because the model is stochastic, each press produces a fresh record -- the exact values
will differ every time, and that is expected, not a bug. What you'll see:

- **The record itself**, first and largest: one row per month for every year requested.
  1,000 years is 12,000 rows. It can be read on screen or downloaded as a CSV.
- **Return periods** -- the design flow for a 2-, 5-, 10-, 25-, 50-, 100- and 500-year
  event, taken from the largest flow of each synthetic year. This is what a spillway or
  channel calculation actually consumes.
- **Two comparison charts** -- the distribution of monthly values, and the flow-duration
  curve, each showing the generated record against the measured one. The two lines lying
  on top of each other is the visual check that the synthetic record behaves like the
  real river.
- **An extremes card** on the right: highest and lowest month, 95th and 99th percentiles.
- **A "track record" tag**, showing how many of seven statistical properties of the real
  held-out record fell inside the simulated 90% envelope. This is evidence of property
  reproduction, not a forecast-accuracy percentage.
- **A "for the curious" section** with the full statistical detail -- coefficients and
  standard errors, the twelve seasonal parameters, the stationarity evidence, and the
  validation table.

**Use the return periods, not the single highest month.** The largest value in a long
generated record is the most extreme of tens of thousands of simulated years, and the
model has no upper bound, so that number reflects the shape of the assumed distribution
rather than any physical limit of the channel.
"""
)

# 7 ---------------------------------------------------------------------------
st.markdown("## 7. Limitations")
st.markdown(
    """
| Limitation | Implication |
|-----------|-------------|
| **Univariate** | The model uses only discharge's own past; it cannot anticipate a rainfall event that has not yet reached the river. |
| **Fixed seasonal component** | The annual cycle is stored as twelve constant monthly means and twelve standard deviations, all treated as unchanging. A periodic model with time-varying seasonal parameters would represent a shifting regime better. |
| **Decadal non-stationarity** | This is the big one for this river. The record spans the Sahel drought and the rainfall recovery that followed: the estimation period averages 19.8 m³/s and the held-out period 38.7. A stationary model fitted to the first cannot reproduce the level of the second, and that is exactly the property check it fails. It reproduces the river's shape &mdash; variability, skewness, seasonal amplitude, low-flow duration, peak &mdash; and gets the level wrong. |
| **Regulated river** | Tiga Dam and Challawa Gorge Dam control much of the flow reaching this gauge, and Challawa was commissioned in 1992, inside the analysis window. The model describes a regulated river, and any design figure from it assumes the reservoirs keep being operated broadly as they were. |
| **Log offset is a convention** | Dry-season monthly means reach zero, so a constant of 1% of mean flow is added before taking logarithms. Its influence has been measured: negligible for the mean and the frequent floods, more than a factor of two on the 500-year value. |
| **Linear model, unbounded tail** | Catchment response during extreme events is partly non-linear and not fully captured. The log-linear form also has **no upper bound**, so the single largest value in a long generated record is governed by the assumed distribution rather than by any physical limit of the channel. Use the return periods, not the record maximum. |
| **Parameters treated as known** | The generated record propagates the randomness of the process but not the *sampling uncertainty of the fitted coefficients themselves*. The return-period estimates are therefore more precise-looking than 26 years of evidence strictly warrant. |
| **No new information** | Generating 1,000 years does not add knowledge the 26-year record did not contain; it works out the consequences of the fitted structure more fully. Estimates near the observed range are well supported, and become progressively more model-dependent beyond it. |
| **One basin's design figures** | The design discharges here are for this gauge alone. What has been shown to transfer is the *procedure*, and the finding about the two ways of removing the annual cycle, which was reproduced on the Conecuh River at Brantley in a completely different climate. The specific numbers are not claimed to transfer anywhere. |
| **Stationarity assumed** | Every generated record assumes the process estimated from the observed period continues to govern the basin unchanged — which climate change, land-use change, reservoir construction, river engineering, urbanisation, or a change to the gauge would each break. A stationary model cannot represent any of them. |
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
│   ├── 0_Forecast.py      ← synthetic record generator
│   └── 1_Documentation.py ← this page
├── src/
│   ├── preprocess.py      ← monthly loaders, log transform, deseasonalisation
│   ├── model.py           ← ARIMA + ADF/KPSS/ACF/PACF/Ljung-Box + standard errors
│   ├── calibrate.py       ← stationarity + AIC order selection
│   ├── simulate.py        ← stochastic synthetic-record generation
│   ├── validation.py      ← property-based validation
│   ├── forecast.py        ← residual diagnostics
│   └── plots.py           ← the figures, including the method comparison
├── data/
│   ├── hadejia_discharge_monthly.csv  ← the Nigerian case-study record
│   └── results.json                   ← model + validation + comparison results
└── run_pipeline.py        ← full pipeline runner (both basins, both methods)
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
- Do, H. X., Gudmundsson, L., Leonard, M., & Westra, S. (2018). The Global Streamflow Indices and
  Metadata Archive (GSIM) &ndash; Part 1. *Earth System Science Data*, 10(2), 765&ndash;785.
- Gudmundsson, L., Do, H. X., Leonard, M., & Westra, S. (2018). The Global Streamflow Indices and
  Metadata Archive (GSIM) &ndash; Part 2. *Earth System Science Data*, 10(2), 787&ndash;804.
"""
)

st.markdown("---")
st.caption(
    f"{meta.get('short_name', 'River')} Synthetic Record Generator  ·  "
    "Stochastic hydrology with ARIMA"
    "  ·  "
)
