"""
pages/1_Documentation.py — Documentation and user guide for the statistical
(ARIMA) streamflow forecasting app.
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
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600&display=swap');
    html, body, [class*="css"] {{ font-family: 'Fira Sans', system-ui, sans-serif; color: {COLOR_TEXT}; }}
    h1 {{ font-family: 'Fira Code', monospace; color: {COLOR_PRIMARY} !important; font-size: 1.85rem !important;
         font-weight: 700 !important; border-bottom: 2px solid {COLOR_PRIMARY}; padding-bottom: 0.4rem; }}
    h2 {{ color: {COLOR_TEXT} !important; font-size: 1.1rem !important; font-weight: 700 !important;
         text-transform: uppercase; letter-spacing: 0.06em; margin-top: 2rem !important;
         border-left: 3px solid {COLOR_PRIMARY}; padding-left: 0.6rem; }}
    h3 {{ color: {COLOR_PRIMARY} !important; font-size: 1rem !important; font-weight: 600 !important;
         margin-top: 1.25rem !important; }}
    p, li {{ font-size: 0.95rem; line-height: 1.7; }}
    code {{ font-family: 'Fira Code', monospace; background: {COLOR_SURFACE}; padding: 0.15em 0.45em;
         border-radius: 4px; font-size: 0.88em; color: {COLOR_PRIMARY}; }}
    .block-container {{ max-width: 900px; padding-top: 1.25rem; padding-bottom: 3rem; }}
    .callout {{ background: {COLOR_SURFACE}; border-left: 4px solid {COLOR_PRIMARY}; border-radius: 0 6px 6px 0;
         padding: 0.85rem 1.1rem; margin: 1rem 0; font-size: 0.92rem; line-height: 1.65; }}
    .callout strong {{ color: {COLOR_PRIMARY}; }}
    .eq-box {{ background: #F1F5F9; border: 1px solid {COLOR_BORDER}; border-radius: 6px; padding: 0.75rem 1.25rem;
         margin: 0.6rem 0; font-family: 'Fira Code', monospace; font-size: 0.9rem; color: {COLOR_TEXT}; line-height: 1.9; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; margin: 0.75rem 0; }}
    th {{ background: {COLOR_PRIMARY}; color: white; padding: 0.5rem 0.75rem; text-align: left; font-weight: 600; }}
    td {{ padding: 0.45rem 0.75rem; border-bottom: 1px solid {COLOR_BORDER}; }}
    tr:nth-child(even) td {{ background: #F8FAFC; }}
    </style>
    """,
    unsafe_allow_html=True,
)

model_name = R.get("model", "ARIMA(3, 1, 2)")
d = R.get("differencing_d", 1)
nse1 = R.get("forecast", {}).get("1", {}).get("model", {}).get("NSE", 0.827)
pss1 = R.get("forecast", {}).get("1", {}).get("model", {}).get("PSS", 0.236)
lb_p = R.get("ljung_box", {}).get("pvalue", 0.228)

st.title("Documentation")
st.caption(
    "Conecuh River Streamflow Forecaster  ·  "
    "Civil & Environmental Engineering, University of Lagos  ·  "
    "Ugbodaga Benedict Osikpemi  ·  2026"
)

st.markdown(
    """<div class="callout">
    This page explains <strong>what the app does</strong>, the <strong>statistical method behind it</strong>,
    and <strong>how to read the output</strong>. The model forecasts river discharge from its own
    past values only &mdash; there is no rainfall or weather input.
    </div>""",
    unsafe_allow_html=True,
)

# 1 ---------------------------------------------------------------------------
st.markdown("## 1. What This App Does")
st.markdown(
    f"""
This application forecasts **short-term river discharge** (streamflow) for the
**Conecuh River, Alabama, USA** (USGS gauge 02361000) for the next 1&ndash;7 days.

Unlike a rainfall-runoff model, it requires **no weather input at all**. It is a
**statistical time-series model** that learns the temporal behaviour of the river
directly from its **historical discharge record** and projects that behaviour forward.
The model used is **{model_name}**, an autoregressive integrated moving average
(ARIMA) model identified through the Box&ndash;Jenkins methodology.
"""
)
st.markdown(
    """<div class="callout">
    <strong>Why discharge-only?</strong> Daily river flow is highly autocorrelated &mdash;
    today's flow is the single best predictor of tomorrow's. A statistical model exploits this
    directly, avoiding the data demands and calibration uncertainty of process-based models.
    This makes it well suited to settings where reliable flow records exist but dense weather
    networks do not.
    </div>""",
    unsafe_allow_html=True,
)

# 2 ---------------------------------------------------------------------------
st.markdown("## 2. The Method — How the Model Works")
st.markdown(
    """
The model belongs to the **ARIMA(p, d, q)** family (Box & Jenkins, 1976), which describes
a time series using three ingredients:

- **AR (autoregressive), order p** — the current value depends on its own *p* previous values.
- **I (integrated), order d** — the series is *differenced* *d* times to remove trend and
  make it stationary (statistically stable over time).
- **MA (moving average), order q** — the current value depends on the *q* previous random shocks.
"""
)
st.markdown("### Working on log-discharge")
st.markdown(
    """
Because daily discharge is strongly right-skewed and its variability grows with its size,
the model is fitted to the **natural logarithm** of discharge. This stabilises the variance
and stops a few large flood peaks from dominating the fit. Forecasts are converted back to
m&sup3;/s by exponentiation.
"""
)
st.markdown("### The model equation")
st.markdown(
    """<div class="eq-box">
    Let z(t) = ln[Q(t)] and w(t) = (1 &minus; B)<sup>d</sup> z(t) be the differenced series.<br><br>
    w(t) = c + &phi;<sub>1</sub> w(t&minus;1) + &hellip; + &phi;<sub>p</sub> w(t&minus;p)
    + a(t) + &theta;<sub>1</sub> a(t&minus;1) + &hellip; + &theta;<sub>q</sub> a(t&minus;q)<br><br>
    where &phi; are the autoregressive coefficients, &theta; the moving-average coefficients,
    c a constant, and a(t) a white-noise error term.
    </div>""",
    unsafe_allow_html=True,
)

# 3 ---------------------------------------------------------------------------
st.markdown("## 3. How the Model Was Built (Box-Jenkins)")
st.markdown(
    f"""
1. **Stationarity testing.** The Augmented Dickey&ndash;Fuller (ADF) and KPSS tests were applied
   to decide the differencing order. Both agreed that **one difference (d = {d})** yields a
   stationary series.
2. **Order identification.** The autocorrelation (ACF) and partial autocorrelation (PACF)
   functions of the differenced series suggested candidate AR and MA orders.
3. **Estimation.** Model coefficients were estimated by **conditional sum of squares**;
   pure AR models were solved exactly by least squares.
4. **Order selection.** All candidate orders were ranked by the **Akaike Information
   Criterion (AIC)**, which balances fit against parsimony. The winner was **{model_name}**.
5. **Diagnostic check.** The **Ljung&ndash;Box test** confirmed the residuals are
   indistinguishable from white noise (p = {lb_p:.3f} &gt; 0.05), so the model is adequate.
"""
)

# 4 ---------------------------------------------------------------------------
st.markdown("## 4. Data")
st.markdown(
    """
| Item | Detail |
|------|--------|
| **Basin** | Conecuh River, Alabama, USA |
| **Gauge** | USGS 02361000 (CAMELS dataset) |
| **Variable** | Daily mean discharge only (converted ft&sup3;/s &rarr; m&sup3;/s) |
| **Record** | 1 Jan 1980 &ndash; 31 Dec 2014 (12,784 days) |
| **Training** | 1980&ndash;2003 (model identification & estimation) |
| **Validation** | 2004&ndash;2014 (out-of-sample skill assessment) |
| **Source** | Newman et al. (2015); Addor et al. (2017) |

No rainfall, temperature, evapotranspiration or any other variable is used.
"""
)

# 5 ---------------------------------------------------------------------------
st.markdown("## 5. Forecast Skill and the Persistence Benchmark")
st.markdown(
    f"""
Skill was measured by rolling-origin (walk-forward) forecasting over the validation period:
for every day the model forecasts 1, 2 and 3 days ahead using only past observations.

Because daily flow is so autocorrelated, the naive **persistence** forecast
(&ldquo;tomorrow equals today&rdquo;) is already a strong competitor. The decisive metric is
therefore the **persistence skill score (PSS)**:
"""
)
st.markdown(
    """<div class="eq-box">PSS = 1 &minus; MSE(model) / MSE(persistence)</div>""",
    unsafe_allow_html=True,
)
if R.get("forecast"):
    rows = "".join(
        f"<tr><td>{k}-day</td>"
        f"<td>{R['forecast'][k]['model']['NSE']:.3f}</td>"
        f"<td>{R['forecast'][k]['model']['RMSE']:.2f}</td>"
        f"<td>{R['forecast'][k]['model']['PSS']:+.3f}</td>"
        f"<td>{R['forecast'][k]['persistence']['NSE']:.3f}</td></tr>"
        for k in ("1", "2", "3")
    )
    st.markdown(
        f"""
<table>
<tr><th>Lead time</th><th>Model NSE</th><th>Model RMSE (m&sup3;/s)</th><th>PSS</th><th>Persistence NSE</th></tr>
{rows}
</table>
""",
        unsafe_allow_html=True,
    )
st.markdown(
    f"""
A **positive PSS at every lead time** shows the model adds genuine skill beyond persistence.
At a one-day lead the model attains an NSE of **{nse1:.3f}** (&ldquo;very good&rdquo; on the
Moriasi et al. (2007) scale) with a skill score of **{pss1:+.3f}**. Skill declines at longer
leads, which is expected for any model that uses only past flow.
"""
)

# 6 ---------------------------------------------------------------------------
st.markdown("## 6. How to Use the App")
st.markdown(
    """
1. Go to the **Forecast Tool** page.
2. In the sidebar set the **Horizon (days)** (1&ndash;7) and the length of **history to display**.
3. Press **Run Forecast**.

The app forecasts forward from the **end of the observed record**. Results show:
- **Forecast Summary** &mdash; discharge for each day and its % difference from the record mean.
- **Forecast Table** &mdash; dated forecast values (downloadable as CSV).
- **Discharge Forecast Chart** &mdash; recent observed history with the forecast appended.
- **Validation Skill** &mdash; the out-of-sample NSE and persistence skill score by lead time.
"""
)

# 7 ---------------------------------------------------------------------------
st.markdown("## 7. Limitations")
st.markdown(
    """
| Limitation | Implication |
|-----------|-------------|
| **Univariate (discharge only)** | The model cannot anticipate a flood driven by rainfall that has not yet reached the river; it responds once the rise begins. |
| **Linear model** | Catchment response during extreme events is partly non-linear and not fully captured. |
| **Skill decays with lead time** | Most reliable at the 1-day horizon; weaker at 2&ndash;3 days. |
| **Point forecasts only** | A single deterministic value is returned; no prediction intervals (a recommended extension). |
| **Single basin, fixed parameters** | Demonstrated on one basin; transfer to very different regimes is untested. |
"""
)

# 8 ---------------------------------------------------------------------------
st.markdown("## 8. Technical Details")
st.markdown(
    """
**Software stack:** Python, NumPy, SciPy, Matplotlib, Streamlit. The ARIMA estimation,
stationarity tests, ACF/PACF, conditional-sum-of-squares optimisation and Ljung&ndash;Box
test are implemented directly from their defining equations (self-contained, no external
time-series library).

```
finals_project/
├── app.py                 ← navigation entrypoint
├── pages/
│   ├── 0_Forecast.py      ← forecast tool
│   └── 1_Documentation.py ← this page
├── src/
│   ├── preprocess.py      ← load discharge, log transform, train/valid split
│   ├── model.py           ← ARIMA + ADF/KPSS/ACF/PACF/Ljung-Box
│   ├── calibrate.py       ← stationarity + AIC order selection
│   ├── forecast.py        ← rolling multi-step forecast + persistence
│   └── metrics.py         ← NSE, RMSE, PBIAS, MAE, R2, skill score
├── data/results.json      ← model + validation metrics
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
- Box, G. E. P., & Jenkins, G. M. (1976). *Time series analysis: Forecasting and control*. Holden-Day.
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
    "Conecuh River Streamflow Forecaster  ·  "
    "Computer Hydrological Forecasting — Final Year Project  ·  "
    "Department of Civil and Environmental Engineering, University of Lagos  ·  "
    "Supervisor: Prof. K. O. Aiyesimoju  ·  February 2026"
)
