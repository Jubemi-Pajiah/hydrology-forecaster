"""
pages/1_Documentation.py — Full documentation and user guide.
"""
import streamlit as st


COLOR_PRIMARY   = "#2563EB"
COLOR_TEXT      = "#1E293B"
COLOR_SURFACE   = "#EFF6FF"
COLOR_BORDER    = "#CBD5E1"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600&display=swap');
    html, body, [class*="css"] {{
        font-family: 'Fira Sans', system-ui, sans-serif;
        color: {COLOR_TEXT};
    }}
    h1 {{
        font-family: 'Fira Code', monospace;
        color: {COLOR_PRIMARY} !important;
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        border-bottom: 2px solid {COLOR_PRIMARY};
        padding-bottom: 0.4rem;
    }}
    h2 {{
        font-family: 'Fira Sans', sans-serif;
        color: {COLOR_TEXT} !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 2rem !important;
        border-left: 3px solid {COLOR_PRIMARY};
        padding-left: 0.6rem;
    }}
    h3 {{
        font-family: 'Fira Sans', sans-serif;
        color: {COLOR_PRIMARY} !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        margin-top: 1.25rem !important;
    }}
    p, li {{
        font-size: 0.95rem;
        line-height: 1.7;
    }}
    code {{
        font-family: 'Fira Code', monospace;
        background: {COLOR_SURFACE};
        padding: 0.15em 0.45em;
        border-radius: 4px;
        font-size: 0.88em;
        color: {COLOR_PRIMARY};
    }}
    .block-container {{
        max-width: 900px;
        padding-top: 1.25rem;
        padding-bottom: 3rem;
    }}
    .callout {{
        background: {COLOR_SURFACE};
        border-left: 4px solid {COLOR_PRIMARY};
        border-radius: 0 6px 6px 0;
        padding: 0.85rem 1.1rem;
        margin: 1rem 0;
        font-size: 0.92rem;
        line-height: 1.65;
    }}
    .callout strong {{ color: {COLOR_PRIMARY}; }}
    .eq-box {{
        background: #F1F5F9;
        border: 1px solid {COLOR_BORDER};
        border-radius: 6px;
        padding: 0.75rem 1.25rem;
        margin: 0.6rem 0;
        font-family: 'Fira Code', monospace;
        font-size: 0.9rem;
        color: {COLOR_TEXT};
        line-height: 1.9;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
        margin: 0.75rem 0;
    }}
    th {{
        background: {COLOR_PRIMARY};
        color: white;
        padding: 0.5rem 0.75rem;
        text-align: left;
        font-weight: 600;
    }}
    td {{
        padding: 0.45rem 0.75rem;
        border-bottom: 1px solid {COLOR_BORDER};
    }}
    tr:nth-child(even) td {{ background: #F8FAFC; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Documentation")
st.caption(
    "Conecuh River Streamflow Forecaster  ·  "
    "Civil & Environmental Engineering, University of Lagos  ·  "
    "Ugbodaga Benedict Osikpemi  ·  2026"
)

st.markdown(
    """<div class="callout">
    This page explains <strong>what the app does</strong>, the <strong>science behind it</strong>,
    and <strong>how to use it correctly</strong>. Read this before running forecasts
    if you are unfamiliar with hydrological modelling concepts.
    </div>""",
    unsafe_allow_html=True,
)

# ── 1. What this app does ─────────────────────────────────────────────────────
st.markdown("## 1. What This App Does")

st.markdown(
    """
This application forecasts **short-term river discharge** (streamflow) for the
**Conecuh River, Alabama, USA** (CAMELS basin 02361000) using a lightweight
mathematical model of the rainfall-runoff process.

You supply the **expected weather** for the next 1–7 days — daily rainfall, maximum
temperature, and minimum temperature — and the app returns **predicted discharge in
cubic metres per second (m³/s)** for each day.

The model was *calibrated* on 24 years of historical data (1980–2003) so its internal
parameters match the behaviour of this specific river basin. The calibration
Nash-Sutcliffe Efficiency (NSE) is **0.59**, placing it in the *Acceptable* performance
band (0.50–0.65) under the Moriasi et al. (2007) guidelines.
"""
)

st.markdown(
    """<div class="callout">
    <strong>Important limitation:</strong> This is a <em>simulation tool</em>, not an operational
    flood-warning system. Forecasts depend entirely on how accurate your weather inputs are.
    If tomorrow's rainfall is unknown, use a range of scenarios (low / mid / high rainfall)
    to understand how sensitive the river response is.
    </div>""",
    unsafe_allow_html=True,
)

# ── 2. The Science ────────────────────────────────────────────────────────────
st.markdown("## 2. The Science — How the Model Works")

st.markdown(
    """
The app uses a **lumped conceptual two-bucket rainfall-runoff model**. 'Lumped' means
the entire catchment is treated as a single unit — spatial variation within the basin
is ignored. 'Conceptual' means the equations are simplified representations of physical
processes rather than exact physics. This class of model is widely used in operational
hydrology because it is computationally efficient and requires only basic weather data.
"""
)

st.markdown("### Two Storage Buckets")

col1, col2 = st.columns(2, gap="large")
with col1:
    st.markdown(
        """
**Soil Moisture Store (S)**

Represents water held in the unsaturated soil zone (the root zone). It fills when it
rains and empties through three pathways:
- **Evapotranspiration (ET)** — water used by plants and evaporation from the soil surface
- **Quick runoff (Qquick)** — excess water that runs off when the soil is saturated
- **Percolation (Rperc)** — slow drainage down into the groundwater store
"""
    )
with col2:
    st.markdown(
        """
**Groundwater Store (G)**

Represents water stored in the saturated zone below the soil. It fills via percolation
from the soil store and drains slowly as:
- **Baseflow (Qbase)** — the steady, slow contribution to river flow that sustains
  the river during dry periods between rain events
"""
    )

st.markdown("### Model Equations")

st.markdown(
    """<div class="eq-box">
    <strong>Soil bucket water balance (mm/day):</strong><br>
    S(t+1) = S(t) + P(t) − ET(t) − Q<sub>quick</sub>(t) − R<sub>perc</sub>(t)<br><br>

    <strong>Evapotranspiration:</strong><br>
    ET(t) = c<sub>et</sub> × PET(t) × [S(t) / S<sub>max</sub>]<br><br>

    <strong>Quick runoff (saturation excess):</strong><br>
    Q<sub>quick</sub>(t) = k<sub>q</sub> × max[0,  S(t) − S<sub>max</sub>]<br><br>

    <strong>Percolation to groundwater:</strong><br>
    R<sub>perc</sub>(t) = k<sub>p</sub> × S(t)<br><br>

    <strong>Groundwater bucket:</strong><br>
    G(t+1) = G(t) + R<sub>perc</sub>(t) − Q<sub>base</sub>(t)<br>
    Q<sub>base</sub>(t) = k<sub>g</sub> × G(t)<br><br>

    <strong>Total simulated discharge:</strong><br>
    Q<sub>sim</sub>(t) = Q<sub>quick</sub>(t) + Q<sub>base</sub>(t)  [mm/day → converted to m³/s]
    </div>""",
    unsafe_allow_html=True,
)

st.markdown("### Potential Evapotranspiration (PET)")
st.markdown(
    """
PET is estimated internally using the **Hargreaves & Samani (1985)** equation, which
requires only maximum and minimum daily temperature (no humidity or wind data):

```
PET = 0.0023 × Ra × √(Tmax − Tmin) × (Tmean + 17.8)
```

Where `Ra` is extraterrestrial radiation computed from the basin latitude (31.56° N)
and day of year. This makes the app suitable for data-scarce settings where only
temperature records are available.
"""
)

# ── 3. Calibrated Parameters ──────────────────────────────────────────────────
st.markdown("## 3. Calibrated Parameters")

st.markdown(
    """
The five model parameters were calibrated against 24 years of observed discharge
using **Differential Evolution** optimisation (Storn & Price, 1997), minimising a
composite objective: `−[0.7 × NSE + 0.3 × NSE_log]`. The log-NSE component gives
extra weight to low-flow periods, producing more balanced performance across the
full flow range.
"""
)

st.markdown(
    """
<table>
<tr><th>Parameter</th><th>Value</th><th>Units</th><th>Physical meaning</th></tr>
<tr><td><code>Smax</code></td><td>275.32</td><td>mm</td>
    <td>Maximum soil moisture capacity. When S exceeds this, the soil is saturated
    and quick runoff occurs.</td></tr>
<tr><td><code>kq</code></td><td>0.4966</td><td>—</td>
    <td>Quick-flow coefficient. High value (≈0.5) means nearly all saturation excess
    runs off rapidly — typical for this humid basin.</td></tr>
<tr><td><code>kp</code></td><td>0.0065</td><td>day⁻¹</td>
    <td>Percolation rate. Low value means soil water drains slowly to the
    groundwater store.</td></tr>
<tr><td><code>kg</code></td><td>0.3000</td><td>day⁻¹</td>
    <td>Groundwater recession constant. Moderate value gives a baseflow
    recession time-scale of ≈3 days (1/kg).</td></tr>
<tr><td><code>cet</code></td><td>1.6307</td><td>—</td>
    <td>ET scaling factor. Value > 1 indicates PET under-estimates actual ET for
    this basin, common in humid subtropical climates.</td></tr>
</table>
""",
    unsafe_allow_html=True,
)

# ── 4. Performance ────────────────────────────────────────────────────────────
st.markdown("## 4. Model Performance")

st.markdown(
    """
Performance is assessed using the **Nash-Sutcliffe Efficiency (NSE)** — the standard
metric in hydrology. NSE = 1.0 is a perfect model; NSE = 0.0 means the model is no
better than always predicting the long-term mean discharge.
"""
)

st.markdown(
    """
<table>
<tr><th>Period</th><th>NSE</th><th>RMSE (m³/s)</th><th>PBIAS (%)</th><th>Rating</th></tr>
<tr><td>Calibration (1980–2003)</td><td>0.5895</td><td>—</td><td>—</td>
    <td>Acceptable (0.50–0.65)</td></tr>
<tr><td>Validation (2004–2014)</td><td>0.3116</td><td>29.79</td><td>−1.61</td>
    <td>Below threshold</td></tr>
</table>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
The calibration NSE of **0.59** meets the Acceptable threshold. The validation NSE
of **0.31** falls below it, likely due to **inter-decadal climate non-stationarity** —
the precipitation-runoff relationship shifted between the 1980–2003 calibration period
and the 2004–2014 validation period. The PBIAS of **−1.61%** indicates the model
has negligible volume bias (Very Good by Moriasi et al., 2007), confirming the
parameter set is physically reasonable.

The NSE > 0.65 *Good* target set in the project specification was **not achieved**;
the result is in the *Acceptable* band.

**Performance thresholds** (Moriasi et al., 2007):
"""
)

st.markdown(
    """
<table>
<tr><th>NSE Range</th><th>Rating</th></tr>
<tr><td>> 0.75</td><td>Very Good</td></tr>
<tr><td>0.65 – 0.75</td><td>Good</td></tr>
<tr><td>0.50 – 0.65</td><td>Acceptable</td></tr>
<tr><td>< 0.50</td><td>Unsatisfactory</td></tr>
</table>
""",
    unsafe_allow_html=True,
)

# ── 5. How to Use ─────────────────────────────────────────────────────────────
st.markdown("## 5. How to Use the App — Step by Step")

st.markdown("### Step 1 — Choose Your Forecast Horizon")
st.markdown(
    """
In the **sidebar**, set *Horizon (days)* to a number between 1 and 7. This controls
how many days ahead you are forecasting. One input row will appear per day.

- Use **1 day** for the most reliable forecast (least weather uncertainty).
- Use **3 days** for short-range planning.
- Use up to **7 days** with the understanding that forecast uncertainty grows
  significantly beyond day 3 when using assumed/estimated rainfall.
"""
)

st.markdown("### Step 2 — Enter Daily Weather")
st.markdown(
    """
For each day, expand the day panel (e.g. *Day 1 — Wed 20 May*) and fill in:

| Field | What to enter | Typical range |
|-------|--------------|---------------|
| **Rain (mm)** | Expected total daily rainfall | 0–200 mm/day |
| **Tmax (°C)** | Expected maximum air temperature | 0–45 °C |
| **Tmin (°C)** | Expected minimum air temperature | −10–35 °C |

> **Tmin must be less than Tmax.** If you enter Tmin > Tmax, an error banner appears
> and the forecast is blocked until you correct it.

If you do not know the forecast rainfall, use observed rainfall from a similar
past event, or try several scenarios (0 mm, 10 mm, 50 mm) to see the range of
possible responses.
"""
)

st.markdown("### Step 3 — Set Initial Conditions")
st.markdown(
    """
The two sliders under *Initial Conditions* set the starting state of the model:

**Soil moisture S₀ (mm)**
: How full the soil store is at the start of the forecast. Range: 0 to Smax (275 mm).
  - Set near **0** after a prolonged dry spell.
  - Set near **Smax (275 mm)** after several days of heavy rain.
  - If uncertain, leave the default (**138 mm = Smax/2**), which represents
    a mid-range moisture state.

**Groundwater G₀ (mm)**
: The current groundwater storage depth.
  - Set **low (≈5 mm)** during or after a drought.
  - Set **higher (≈20–50 mm)** after a wet period.
  - The default of **10 mm** is a typical dry-season baseline.

Getting these right improves Day 1 accuracy significantly. For Day 3+ the model
state evolves from the inputs, so errors in initial conditions wash out.
"""
)

st.markdown("### Step 4 — Run Forecast")
st.markdown(
    """
Press **Run Forecast**. Results appear in three sections:

1. **Forecast Summary** — KPI cards showing the discharge for each day and how it
   compares (% above or below) to the long-term basin mean of **23.6 m³/s**.

2. **Forecast Table** — Full data table: date, rainfall input, computed PET,
   predicted discharge, and comparison to basin mean. The table can be downloaded
   as CSV using the icon in its top-right corner.

3. **Discharge Forecast Chart** — Line chart of predicted discharge over the forecast
   horizon. The dashed green line marks the basin calibration mean. Points above this
   line indicate above-average flow conditions.

4. **Calibrated Parameters** — The five model parameter values for reference.
"""
)

st.markdown("### Step 5 — Interpreting the Output")
st.markdown(
    """
**What the discharge numbers mean:**
- **< 10 m³/s** — Low flow / drought-like conditions. River is significantly below
  average.
- **10–23 m³/s** — Below-average flow. River is running but below typical levels.
- **23–50 m³/s** — Near to moderately above average. Normal wet-season or post-rain
  conditions.
- **50–150 m³/s** — High flow. Significant rainfall event. Monitor for flooding.
- **> 150 m³/s** — Very high flow. Potential flood conditions. The model's accuracy
  decreases at extreme flows.

**The decline pattern:** Even with steady daily rainfall, you will typically see
discharge *decrease* over the forecast horizon (Day 1 highest, Day 7 lower). This
is physically correct — the model is draining the initial soil and groundwater
stores over time. Discharge would only stay high or increase if rainfall inputs
are substantial (≥ 15–20 mm/day for this basin).
"""
)

# ── 6. Limitations ────────────────────────────────────────────────────────────
st.markdown("## 6. Limitations and Caveats")

st.markdown(
    """
| Limitation | Implication |
|-----------|-------------|
| **Lumped model** | Spatial variation in rainfall or land use within the basin is ignored. Localised heavy rainfall will be under- or over-represented. |
| **No snowmelt routine** | The Conecuh River basin rarely experiences snow, so this is acceptable here. Do not apply this model to basins where snow is important. |
| **Validation NSE = 0.31** | The model was calibrated on 1980–2003 data. Post-2003 behaviour is less accurately reproduced, likely due to climate non-stationarity. |
| **Perfect-forcing assumption** | The app takes your weather inputs as exact truth. If your rainfall forecast is wrong, the discharge forecast will also be wrong. |
| **Single basin** | The calibrated parameters apply only to CAMELS basin 02361000. They are not transferable to other rivers without recalibration. |
| **No uncertainty quantification** | The model returns a single deterministic forecast. No confidence intervals are provided. Real-world operational forecasts should use ensemble methods. |
"""
)

# ── 7. Technical stack ────────────────────────────────────────────────────────
st.markdown("## 7. Technical Details")

st.markdown(
    """
**Software stack:**
- **Python 3.x** — core language
- **NumPy / Pandas** — numerical computation and data handling
- **SciPy** (`differential_evolution`) — parameter calibration
- **Numba** (`@njit`) — JIT compilation of the model inner loop for fast calibration
- **Matplotlib** — charts
- **Streamlit** — web application framework

**Data source:**
The model was calibrated on the **CAMELS US dataset** (Newman et al., 2015;
Addor et al., 2017). Forcing data uses Daymet gridded meteorology; discharge
data is from the USGS stream gauge at basin 02361000.

**Code structure:**
```
finals_project/
├── app.py              ← This web application
├── pages/
│   └── 1_Documentation.py  ← This page
├── src/
│   ├── model.py        ← Two-bucket model equations
│   ├── preprocess.py   ← Data loading + Hargreaves PET
│   ├── calibrate.py    ← Differential Evolution calibration
│   ├── forecast.py     ← Multi-step forecast evaluation
│   └── metrics.py      ← NSE, RMSE, PBIAS
├── data/
│   └── results.json    ← Calibrated parameters + performance metrics
└── run_pipeline.py     ← Full pipeline runner
```

**Running the app locally:**
```bash
pip install -r requirements.txt
streamlit run app.py
```
"""
)

# ── 8. References ─────────────────────────────────────────────────────────────
st.markdown("## 8. Key References")

st.markdown(
    """
- Addor, N., Newman, A. J., Mizukami, N., & Clark, M. P. (2017). The CAMELS data set:
  Catchment attributes and meteorology for large-sample studies. *HESS*, 21, 5293–5313.
  https://doi.org/10.5194/hess-21-5293-2017

- Hargreaves, G. H., & Samani, Z. A. (1985). Reference crop evapotranspiration from
  temperature. *Applied Engineering in Agriculture*, 1(2), 96–99.

- Moriasi, D. N., Arnold, J. G., Van Liew, M. W., Bingner, R. L., Harmel, R. D., &
  Veith, T. L. (2007). Model evaluation guidelines for systematic quantification of
  accuracy in watershed simulations. *Transactions of the ASABE*, 50(3), 885–900.
  https://doi.org/10.13031/2013.23153

- Nash, J. E., & Sutcliffe, J. V. (1970). River flow forecasting through conceptual
  models: Part I — A discussion of principles. *Journal of Hydrology*, 10(3), 282–290.

- Newman, A. J., Clark, M. P., Sampson, K., Wood, A., Hay, L. E., Bock, A., …
  Duan, Q. (2015). Development of a large-sample watershed-scale hydrometeorological
  data set for the contiguous USA. *HESS*, 19(1), 209–223.
  https://doi.org/10.5194/hess-19-209-2015

- Storn, R., & Price, K. (1997). Differential evolution — A simple and efficient
  heuristic for global optimization over continuous spaces. *Journal of Global
  Optimization*, 11, 341–359. https://doi.org/10.1023/A:1008202821328
"""
)

st.markdown("---")
st.caption(
    "Conecuh River Streamflow Forecaster  ·  "
    "Computer Hydrological Forecasting — Final Year Project  ·  "
    "Department of Civil and Environmental Engineering, University of Lagos  ·  "
    "Supervisor: Prof. K. O. Aiyesimoju  ·  February 2026"
)
