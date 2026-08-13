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
  slow drift and make it stationary. (At a **daily** timestep, differencing gains almost
  nothing for a river that never truly trends; at a **monthly** timestep it can remove
  genuine seasonal drift where present -- part of why this project moved from a daily to a
  monthly timestep.)
- **MA (moving average), order q** — the current value depends on the *q* previous random
  shocks.

Related, simpler members of the same family exist -- a pure **AR(p)** model (no MA term),
a pure **MA(q)** model (no AR term), an **ARMA(p, q)** model (no differencing, i.e. d = 0),
and **ARIMAX**, which adds exogenous input variables. This project uses plain ARIMA, not
ARIMAX, deliberately: each variable is forecast from its own past only, by design, so
there is no exogenous driver to add.
"""
)
st.markdown("### Working on log-transformed values")
st.markdown(
    """
Streamflow, rainfall, and stage are all strictly positive and right-skewed, with
variability that grows with magnitude, so each model is fitted to the **natural
logarithm** of its variable. This stabilises variance and stops a few extreme months
from dominating the fit. Forecasts are converted back to natural units by exponentiation.
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
Forecast Tool) is part of what should be judged, not just whether the historical value
happens to fall inside it.
"""
)

# 6 ---------------------------------------------------------------------------
st.markdown("## 6. How to Use the App")
st.markdown(
    """
1. Go to the **River Outlook** page.
2. Choose **where to start from** (the end of the record, or an earlier month if you
   want to also see what actually happened next) and **how far ahead to look**.
3. Press **Get the Outlook** -- one click forecasts all three variables together.

Because the model is stochastic, each click generates a fresh random ensemble -- the
exact synthetic paths will differ between runs, and that is expected, not a bug. What
you'll see:
- **Three cards**, one per variable, each with a plain-English summary sentence, a
  headline number, and two small tags: a trend (rising / falling / steady) and how the
  level compares to what's typical.
- **A chart per variable** showing recent history, the range of plausible futures, the
  expected path through the middle of that range, and (where available) what actually
  happened, for context.
- **A "track record" tag** on each card, showing how many of seven statistical
  properties the model's ensemble reproduces from the real 2004-2014 record -- the
  honest measure of how much to trust it.
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
| **Non-seasonal ARIMA** | No explicit seasonal (P, D, Q, 12) terms; some residual autocorrelation at seasonal lags remains for discharge and stage (visible in the Ljung-Box result), an acknowledged limitation rather than a hidden one. |
| **Linear model** | Catchment response during extreme events is partly non-linear and not fully captured. |
| **Gaussian innovations** | The synthetic ensembles draw innovations from a Normal distribution fitted to the residuals; residual diagnostics show heavier tails than Normal for some variables, so extreme-tail synthetic values may be somewhat under-dispersed. |
| **Single basin** | Demonstrated on one basin; transfer to a different climate regime is untested. |
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
