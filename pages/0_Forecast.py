"""
app.py — Streamlit web application for two-bucket hydrological forecasting.

Uses calibrated parameters from data/results.json. Runs the lumped conceptual
model forward from user-supplied initial conditions and weather inputs.
"""
import sys
import json
from pathlib import Path
from datetime import date, timedelta

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.preprocess import hargreaves_pet

# Use Numba-compiled model if available; fall back to pure-NumPy for deployment
try:
    from src.model import run_model, warm_up
    _NUMBA_AVAILABLE = True
except Exception:
    _NUMBA_AVAILABLE = False

    def run_model(prcp, pet, params, S0=None, G0=None):
        Smax, kq, kp, kg, cet = (
            params["Smax"], params["kq"], params["kp"], params["kg"], params["cet"]
        )
        S = float(S0) if S0 is not None else Smax / 2.0
        G = float(G0) if G0 is not None else 10.0
        Qsim = np.empty(len(prcp))
        for t in range(len(prcp)):
            ET = min(max(cet * pet[t] * (S / Smax), 0.0), S)
            Qquick = kq * max(0.0, S - Smax)
            Rperc = kp * S
            S = max(0.0, S + prcp[t] - ET - Qquick - Rperc)
            Qbase = kg * G
            G = max(0.0, G + Rperc - Qbase)
            Qsim[t] = Qquick + Qbase
        return Qsim

    def warm_up():
        pass

# ── Constants ─────────────────────────────────────────────────────────────────
RESULTS_PATH = ROOT / "data" / "results.json"
BASIN_LAT    = 31.56
BASIN_AREA   = 1779.30
MMDAY_TO_M3S = BASIN_AREA * 1e6 / 86400.0 / 1000.0

# Design system palette (Data-Dense Dashboard)
COLOR_PRIMARY   = "#2563EB"
COLOR_SECONDARY = "#3B82F6"
COLOR_ACCENT    = "#F97316"
COLOR_BG        = "#F8FAFC"
COLOR_TEXT      = "#1E293B"
COLOR_SURFACE   = "#EFF6FF"
COLOR_BORDER    = "#CBD5E1"
COLOR_SUCCESS   = "#059669"
COLOR_ERROR     = "#DC2626"
COLOR_CHART     = "#0080FF"
COLOR_MEAN_LINE = "#059669"


# ── Cached resources ──────────────────────────────────────────────────────────
@st.cache_resource
def load_results() -> dict:
    with open(RESULTS_PATH) as f:
        return json.load(f)


@st.cache_resource
def _compile_numba():
    warm_up()


# ── PET helper ────────────────────────────────────────────────────────────────
def compute_pet(tmax_arr: np.ndarray, tmin_arr: np.ndarray,
                start: date) -> np.ndarray:
    tmean = (tmax_arr + tmin_arr) / 2.0
    doy   = np.array(
        [(start + timedelta(days=i)).timetuple().tm_yday for i in range(len(tmax_arr))],
        dtype=float,
    )
    return hargreaves_pet(tmax_arr, tmin_arr, tmean, doy, BASIN_LAT)



# ── CSS: typography, spacing, component polish ────────────────────────────────
st.markdown(
    f"""
    <style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Fira Sans', system-ui, sans-serif;
        color: {COLOR_TEXT};
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {COLOR_SURFACE};
        border-right: 1px solid {COLOR_BORDER};
    }}
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {{
        color: {COLOR_PRIMARY};
        font-family: 'Fira Sans', sans-serif;
        font-weight: 600;
    }}

    /* Page headings */
    h1 {{
        font-family: 'Fira Code', monospace;
        color: {COLOR_PRIMARY} !important;
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.3px;
        border-bottom: 2px solid {COLOR_PRIMARY};
        padding-bottom: 0.4rem;
        margin-bottom: 0.5rem !important;
    }}
    h2 {{
        font-family: 'Fira Sans', sans-serif;
        color: {COLOR_TEXT} !important;
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 1.5rem !important;
    }}
    h3 {{
        font-family: 'Fira Sans', sans-serif;
        color: {COLOR_TEXT} !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
    }}

    /* Main container padding */
    .block-container {{
        padding-top: 1.25rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }}

    /* Data table styling */
    [data-testid="stDataFrame"] table {{
        font-size: 0.875rem;
        border-collapse: collapse;
    }}
    [data-testid="stDataFrame"] th {{
        background-color: {COLOR_PRIMARY} !important;
        color: white !important;
        font-family: 'Fira Sans', sans-serif;
        font-weight: 600;
        padding: 0.5rem 0.75rem;
    }}
    [data-testid="stDataFrame"] tr:nth-child(even) {{
        background-color: #F1F5F9;
    }}
    [data-testid="stDataFrame"] tr:hover {{
        background-color: #DBEAFE;
    }}

    /* Metric cards */
    [data-testid="metric-container"] {{
        background-color: white;
        border: 1px solid {COLOR_BORDER};
        border-top: 3px solid {COLOR_PRIMARY};
        border-radius: 6px;
        padding: 0.75rem 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }}
    [data-testid="metric-container"] label {{
        font-size: 0.7rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748B !important;
    }}
    [data-testid="metric-container"] [data-testid="stMetricValue"] {{
        font-family: 'Fira Code', monospace;
        font-size: 1.3rem !important;
        color: {COLOR_PRIMARY} !important;
        font-weight: 600;
    }}

    /* Primary button */
    .stButton > button[kind="primary"] {{
        background-color: {COLOR_PRIMARY};
        border: none;
        font-family: 'Fira Sans', sans-serif;
        font-weight: 600;
        letter-spacing: 0.04em;
        border-radius: 6px;
        padding: 0.5rem 1.25rem;
        transition: background-color 150ms ease-out, transform 100ms ease-out;
        box-shadow: 0 2px 4px rgba(37,99,235,0.25);
    }}
    .stButton > button[kind="primary"]:hover {{
        background-color: #1D4ED8;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(37,99,235,0.3);
    }}
    .stButton > button[kind="primary"]:active {{
        transform: translateY(0);
        box-shadow: 0 1px 2px rgba(37,99,235,0.2);
    }}

    /* Expander styling */
    [data-testid="stExpander"] {{
        border: 1px solid {COLOR_BORDER};
        border-radius: 6px;
        margin-bottom: 0.35rem;
        background: white;
    }}
    [data-testid="stExpander"][aria-expanded="true"] {{
        border-color: {COLOR_SECONDARY};
        box-shadow: 0 0 0 2px rgba(37,99,235,0.1);
    }}

    /* Divider */
    hr {{
        border-color: {COLOR_BORDER};
        margin: 0.75rem 0;
    }}

    /* Caption / small text */
    .stCaption, [data-testid="stCaptionContainer"] {{
        color: #64748B;
        font-size: 0.78rem;
        line-height: 1.6;
    }}

    /* Error box */
    [data-testid="stAlert"][kind="error"] {{
        background-color: #FEF2F2;
        border-left: 4px solid {COLOR_ERROR};
        color: {COLOR_ERROR};
        font-weight: 500;
    }}

    /* Warning box */
    [data-testid="stAlert"][kind="warning"] {{
        background-color: #FFFBEB;
        border-left: 4px solid {COLOR_ACCENT};
        color: #92400E;
    }}

    /* Info intro box */
    .app-intro {{
        background: linear-gradient(135deg, {COLOR_SURFACE} 0%, #DBEAFE 100%);
        border-left: 4px solid {COLOR_PRIMARY};
        border-radius: 0 6px 6px 0;
        padding: 0.9rem 1.1rem;
        margin-bottom: 1rem;
        font-size: 0.9rem;
        line-height: 1.65;
        color: {COLOR_TEXT};
    }}
    .app-intro strong {{ color: {COLOR_PRIMARY}; }}

    /* Section label chips */
    .section-label {{
        display: inline-block;
        background-color: {COLOR_SURFACE};
        border: 1px solid {COLOR_SECONDARY};
        color: {COLOR_PRIMARY};
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        padding: 0.15rem 0.55rem;
        border-radius: 99px;
        margin-bottom: 0.4rem;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Load resources ─────────────────────────────────────────────────────────────
results = load_results()
params  = results["params"]
Smax    = params["Smax"]
q_mean  = results["data_stats"]["q_obs"]["mean"]

with st.spinner("Compiling model (first run only — a few seconds)…"):
    _compile_numba()

# ── Page header ────────────────────────────────────────────────────────────────
st.title("Conecuh River Streamflow Forecaster")
st.markdown(
    f"""<div class="app-intro">
    A calibrated <strong>two-bucket lumped hydrological model</strong> (CAMELS basin 02361000,
    Conecuh River, Alabama) generates short-term streamflow forecasts from weather inputs.
    Enter the <strong>forecast horizon</strong> and expected daily conditions in the sidebar,
    then press <strong>Run Forecast</strong>.<br>
    <strong>Required per day:</strong> Rainfall (mm), max/min air temperature (°C) &nbsp;|&nbsp;
    <strong>Output:</strong> Daily discharge (m³/s)
    </div>""",
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Forecast Configuration")

    horizon = int(
        st.number_input(
            "Horizon (days)", min_value=1, max_value=7, value=3, step=1,
            help="Number of days ahead to forecast (1–7)",
        )
    )

    st.markdown("---")
    st.markdown("#### Daily Weather Inputs")
    st.caption("Enter expected conditions for each forecast day.")

    today    = date.today()
    prcp_arr = np.zeros(horizon)
    tmax_arr = np.zeros(horizon)
    tmin_arr = np.zeros(horizon)

    for i in range(horizon):
        day_label = (today + timedelta(days=i)).strftime("%a %d %b")
        with st.expander(f"Day {i + 1}  —  {day_label}", expanded=(i < 3)):
            c1, c2, c3 = st.columns(3)
            with c1:
                prcp_arr[i] = st.number_input(
                    "Rain (mm)", min_value=0.0, max_value=200.0,
                    value=5.0, step=0.5, key=f"prcp_{i}",
                )
            with c2:
                tmax_arr[i] = st.number_input(
                    "Tmax (°C)", min_value=-10.0, max_value=50.0,
                    value=25.0, step=0.5, key=f"tmax_{i}",
                )
            with c3:
                tmin_arr[i] = st.number_input(
                    "Tmin (°C)", min_value=-20.0, max_value=50.0,
                    value=15.0, step=0.5, key=f"tmin_{i}",
                )

    st.markdown("---")
    st.markdown("#### Initial Conditions")
    S0 = st.slider(
        "Soil moisture S₀ (mm)",
        min_value=0.0, max_value=float(round(Smax)),
        value=float(round(Smax / 2.0)), step=1.0,
        help=f"Current soil water storage — 0 to Smax = {Smax:.0f} mm",
    )
    G0 = st.slider(
        "Groundwater G₀ (mm)",
        min_value=0.0, max_value=100.0, value=10.0, step=0.5,
        help="Current groundwater store depth (mm)",
    )

    st.markdown("---")
    run_btn = st.button("Run Forecast", type="primary", use_container_width=True)

# ── Validation ────────────────────────────────────────────────────────────────
bad_days = [i + 1 for i in range(horizon) if tmin_arr[i] > tmax_arr[i]]
if bad_days:
    days_str = ", ".join(f"Day {d}" for d in bad_days)
    st.error(
        f"Temperature input error on {days_str}: "
        "Tmin must not exceed Tmax. Correct the sidebar inputs to run the forecast."
    )

# ── Results ───────────────────────────────────────────────────────────────────
if run_btn:
    if bad_days:
        st.warning("Forecast blocked — fix temperature inputs first.")
        st.stop()

    pet_arr     = compute_pet(tmax_arr, tmin_arr, today)
    q_sim_mmday = run_model(prcp_arr, pet_arr, params, S0=S0, G0=G0)
    q_sim_m3s   = q_sim_mmday * MMDAY_TO_M3S

    # ── KPI cards row ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<span class="section-label">Forecast Summary</span>', unsafe_allow_html=True)

    kpi_cols = st.columns(min(horizon, 7))
    for i, col in enumerate(kpi_cols):
        with col:
            q_val    = q_sim_m3s[i]
            day_date = (today + timedelta(days=i)).strftime("%d %b")
            delta_pct = (q_val - q_mean) / q_mean * 100.0
            delta_str = f"{delta_pct:+.0f}% vs mean"
            st.metric(
                label=f"Day {i+1}  {day_date}",
                value=f"{q_val:.2f} m³/s",
                delta=delta_str,
                delta_color="normal",
            )

    # ── Forecast table ─────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## Forecast Table")

    table_rows = []
    for i in range(horizon):
        q_val    = q_sim_m3s[i]
        relation = "above" if q_val > q_mean else "below"
        pct_diff = abs(q_val - q_mean) / q_mean * 100.0
        table_rows.append(
            {
                "Day":                 i + 1,
                "Date":                (today + timedelta(days=i)).strftime("%Y-%m-%d"),
                "Rainfall (mm/day)":   round(float(prcp_arr[i]), 1),
                "PET (mm/day)":        round(float(pet_arr[i]), 2),
                "Q forecast (m³/s)":   round(float(q_val), 3),
                "vs Basin Mean":       f"{pct_diff:.0f}% {relation}",
            }
        )
    df_out = pd.DataFrame(table_rows)
    st.dataframe(df_out, use_container_width=True, hide_index=True)

    # ── Discharge chart ────────────────────────────────────────────────────
    st.markdown("## Discharge Forecast")

    days_x = list(range(1, horizon + 1))

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor("white")

    # Fill area under forecast curve
    ax.fill_between(days_x, q_sim_m3s, alpha=0.12, color=COLOR_CHART, zorder=1)

    # Forecast line + points
    ax.plot(
        days_x, q_sim_m3s, "o-",
        color=COLOR_CHART, linewidth=2.5, markersize=9,
        markerfacecolor="white", markeredgecolor=COLOR_CHART, markeredgewidth=2.5,
        label="Forecast discharge", zorder=3,
    )

    # Basin mean reference (dashed green)
    ax.axhline(
        q_mean, color=COLOR_MEAN_LINE, linestyle="--", linewidth=1.5,
        label=f"Basin mean  {q_mean:.1f} m³/s", zorder=2,
    )

    # Value labels above each point
    for xi, yi in zip(days_x, q_sim_m3s):
        ax.annotate(
            f"{yi:.2f}",
            xy=(xi, yi),
            xytext=(0, 11),
            textcoords="offset points",
            ha="center", va="bottom",
            fontsize=9.5,
            fontfamily="monospace",
            color=COLOR_TEXT,
            fontweight="600",
        )

    # Axes formatting
    ax.set_xlabel("Forecast Day", fontsize=11, color=COLOR_TEXT, labelpad=8)
    ax.set_ylabel("Discharge (m³/s)", fontsize=11, color=COLOR_TEXT, labelpad=8)
    ax.set_title(
        "Predicted Streamflow  —  Conecuh River (CAMELS 02361000)",
        fontsize=12, fontweight="bold", color=COLOR_TEXT, pad=12,
    )
    ax.set_xticks(days_x)
    ax.tick_params(colors=COLOR_TEXT, labelsize=10)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(COLOR_BORDER)
    ax.spines["bottom"].set_color(COLOR_BORDER)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
    ax.grid(axis="y", linestyle="--", color="#E2E8F0", linewidth=0.8, zorder=0)

    legend = ax.legend(
        fontsize=10, frameon=True, loc="upper right",
        framealpha=0.95, edgecolor=COLOR_BORDER,
    )
    legend.get_frame().set_linewidth(0.8)

    fig.tight_layout(pad=1.5)
    st.pyplot(fig)
    plt.close(fig)

    # ── Model parameters ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## Calibrated Parameters")

    param_meta = {
        "Smax": ("Max soil storage",      "mm"),
        "kq":   ("Quick-flow coeff.",     "—"),
        "kp":   ("Percolation rate",      "day⁻¹"),
        "kg":   ("Groundwater recession", "day⁻¹"),
        "cet":  ("ET scaling factor",     "—"),
    }
    cols = st.columns(5)
    for col, (k, (label, unit)) in zip(cols, param_meta.items()):
        with col:
            st.metric(
                label=f"{k}  ({unit})",
                value=f"{params[k]:.4f}",
                help=label,
            )

    st.caption(
        f"Calibration NSE: **{results['cal_nse']:.4f}** (Acceptable, 0.50–0.65)  |  "
        f"Validation NSE: **{results['val_nse']:.4f}**  |  "
        f"Calibration period: 1980–2003  |  "
        f"Basin: Conecuh River, Alabama  |  "
        f"Source: CAMELS US (Newman et al., 2015)"
    )
