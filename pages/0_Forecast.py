"""
0_Forecast.py — Streamlit stochastic forecast tool.

Rewritten 2026-08-12 for the monthly, three-variable (discharge, rainfall,
stage), stochastic-validation pipeline. Each variable has its own
independently fitted ARIMA model. A forecast here is an ENSEMBLE of
synthetic monthly sequences, not a single point prediction -- re-running
the same forecast gives a different ensemble each time, which is the point:
per the supervisor's own framing, a stochastic model's individual forecasts
are not meant to be compared value-for-value against what actually
happened, only its statistical properties are.
"""
import sys
import json
from pathlib import Path
from datetime import timedelta

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.preprocess import build_monthly_dataset, split_monthly, inv_log_transform
from src.model import ARIMA
from src.simulate import simulate_ensemble

RESULTS_PATH = ROOT / "data" / "results.json"

# ── Palette ─────────────────────────────────────────────────────────────────
COLOR_PRIMARY = "#2563EB"
COLOR_ACCENT = "#F97316"
COLOR_BG = "#F8FAFC"
COLOR_TEXT = "#1E293B"
COLOR_SURFACE = "#EFF6FF"
COLOR_BORDER = "#CBD5E1"
COLOR_CHART = "#0080FF"
COLOR_BAND = "#93C5FD"

UNIT = {"discharge": "m3/s", "rainfall": "mm/month", "stage": "m"}
VARIABLE_LABEL = {"discharge": "Discharge", "rainfall": "Rainfall", "stage": "Stage"}


@st.cache_resource
def load_results() -> dict:
    with open(RESULTS_PATH) as f:
        return json.load(f)


@st.cache_resource
def load_monthly(variable: str):
    return build_monthly_dataset(variable)


@st.cache_resource
def fit_model(variable: str):
    """
    Load the model reported in the thesis rather than re-estimating it (see
    the identical rationale in the daily version of this app: re-fitting on
    every cold start is slow, and would silently fit on the full record
    instead of the training-only coefficients the thesis reports).
    """
    results = load_results()
    r = results["variables"][variable]
    df = load_monthly(variable)
    order = tuple(r["order"])
    return ARIMA.from_params(order, r["constant"], r["phi"], r["theta"],
                             df["log_value"].to_numpy())


# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600;700&family=Fira+Sans:wght@300;400;500;600&display=swap');
    html, body, [class*="css"] {{ font-family: 'Fira Sans', system-ui, sans-serif; color: {COLOR_TEXT}; }}
    [data-testid="stSidebar"] {{ background-color: {COLOR_SURFACE}; border-right: 1px solid {COLOR_BORDER}; }}
    h1 {{ font-family: 'Fira Code', monospace; color: {COLOR_PRIMARY} !important; font-size: 1.8rem !important;
         font-weight: 700 !important; border-bottom: 2px solid {COLOR_PRIMARY}; padding-bottom: 0.4rem; }}
    h2 {{ font-size: 1.1rem !important; font-weight: 600 !important; text-transform: uppercase;
         letter-spacing: 0.06em; margin-top: 1.4rem !important; }}
    [data-testid="metric-container"] {{ background:white; border:1px solid {COLOR_BORDER};
         border-top:3px solid {COLOR_PRIMARY}; border-radius:6px; padding:0.75rem 1rem; }}
    [data-testid="metric-container"] [data-testid="stMetricValue"] {{ font-family:'Fira Code',monospace;
         font-size:1.25rem !important; color:{COLOR_PRIMARY} !important; }}
    .stButton > button[kind="primary"] {{ background-color:{COLOR_PRIMARY}; border:none; font-weight:600;
         border-radius:6px; padding:0.5rem 1.25rem; }}
    .app-intro {{ background: linear-gradient(135deg, {COLOR_SURFACE} 0%, #DBEAFE 100%);
         border-left:4px solid {COLOR_PRIMARY}; border-radius:0 6px 6px 0; padding:0.9rem 1.1rem;
         margin-bottom:1rem; font-size:0.9rem; line-height:1.65; }}
    .app-intro strong {{ color:{COLOR_PRIMARY}; }}
    .section-label {{ display:inline-block; background:{COLOR_SURFACE}; border:1px solid {COLOR_PRIMARY};
         color:{COLOR_PRIMARY}; font-size:0.7rem; font-weight:600; text-transform:uppercase;
         letter-spacing:0.1em; padding:0.15rem 0.55rem; border-radius:99px; margin-bottom:0.4rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)

results = load_results()

st.title("Conecuh River Stochastic Forecaster")
st.markdown(
    f"""<div class="app-intro">
    Three <strong>independent statistical ARIMA models</strong> -- one each for <strong>discharge,
    rainfall, and stage</strong> -- forecast the <strong>Conecuh River at Brantley, Alabama
    (USGS 02371500)</strong> from each variable's own past <strong>monthly</strong> values.<br>
    A forecast here is an <strong>ensemble of synthetic sequences</strong>, not one number: this is
    a stochastic model, so re-running the same forecast gives a different set of sequences each
    time. What should stay stable across runs is not the exact path but its <strong>statistical
    properties</strong> &mdash; mean, variability, seasonality, drought duration &mdash; which is
    what the validation section below checks, not point-for-point accuracy.<br>
    The record runs <strong>1980&ndash;2014</strong>, so forecast dates are historical, not today's.
    </div>""",
    unsafe_allow_html=True,
)

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Forecast Configuration")
    variable = st.selectbox("Variable", ["discharge", "rainfall", "stage"],
                            format_func=lambda v: f"{VARIABLE_LABEL[v]} ({UNIT[v]})")

    df = load_monthly(variable)
    model = fit_model(variable)
    r = results["variables"][variable]
    first_month, last_month = df.index[0], df.index[-1]

    month_options = list(df.index)
    default_idx = len(month_options) - 13  # a year before the record ends, so there's room to forecast against real data
    origin_idx = st.selectbox(
        "Forecast origin (month)",
        options=range(len(month_options)),
        index=max(default_idx, 0),
        format_func=lambda i: month_options[i].strftime("%Y-%m"),
        help="The model sees this variable's history up to and including this month, "
             "and nothing after it.",
    )
    origin_ts = month_options[origin_idx]
    horizon = int(st.number_input("Horizon (months)", min_value=1, max_value=36,
                                  value=12, step=1))
    n_reps = int(st.slider("Synthetic replicates", 50, 1000, 300, 50,
                           help="More replicates = smoother percentile bands, slower to compute."))
    hist_window = int(st.slider("History to display (months)", 12, 240, 60, 6))
    st.markdown("---")
    st.markdown("#### Model")
    st.caption(
        f"ARIMA{tuple(r['order'])}  \n"
        f"Differencing d = {r['differencing_d']}  \n"
        f"AIC = {r['aic']:.1f}  \n"
        f"Coefficients estimated on the training period ({r['train_period'][0]} to "
        f"{r['train_period'][1]})"
    )
    run_btn = st.button("Run Forecast", type="primary", use_container_width=True)

# ── Run ─────────────────────────────────────────────────────────────────────
if run_btn:
    hist_to_origin = df.loc[:origin_ts]
    ens = simulate_ensemble(model, hist_to_origin["log_value"].to_numpy(), horizon,
                            n_reps=n_reps, method="gaussian", seed=None)
    fcst_dates = [origin_ts + pd.DateOffset(months=i + 1) for i in range(horizon)]
    origin_value = float(hist_to_origin["value"].iloc[-1])
    q_median = np.median(ens, axis=0)
    q_lo, q_hi = np.percentile(ens, [5, 95], axis=0)

    # Where the origin is early enough, the record already contains what
    # actually happened -- shown for context, NOT as a target the ensemble
    # is expected to hit exactly.
    actual = df["value"].reindex(fcst_dates)
    n_actual = int(actual.notna().sum())

    st.markdown('<span class="section-label">Forecast Summary</span>', unsafe_allow_html=True)
    kpi_cols = st.columns(min(horizon, 6))
    for i, col in enumerate(kpi_cols):
        with col:
            st.metric(
                label=f"Month {i+1}  {fcst_dates[i].strftime('%Y-%m')}",
                value=f"{q_median[i]:.2f} {UNIT[variable]}",
                delta=f"[{q_lo[i]:.1f}, {q_hi[i]:.1f}] 90% band",
                delta_color="off",
            )
    if horizon > 6:
        st.caption(f"Showing the first 6 of {horizon} months; see the chart and table below for all of them.")

    if n_actual:
        st.info(
            f"**For context, not for scoring:** the actual observed values for "
            f"{n_actual} of these months are shown below and in the chart. A stochastic "
            f"model is not expected to reproduce that exact path -- what matters is "
            f"whether the observed value typically falls **inside the 90% band**, "
            f"not whether it matches the median. (Re-run the forecast and watch the "
            f"band redraw with a fresh random ensemble -- the exact paths change, "
            f"the band shouldn't move much.)"
        )
        n_inside = int(np.sum((actual.iloc[:n_actual].to_numpy() >= q_lo[:n_actual]) &
                              (actual.iloc[:n_actual].to_numpy() <= q_hi[:n_actual])))
        st.metric("Observed months inside the 90% band", f"{n_inside} / {n_actual}")
    else:
        st.warning(
            f"**No observed values to compare against.** {origin_ts:%Y-%m} is at or "
            f"near the end of the record, so these months lie beyond the data. Move "
            f"the forecast origin back in the sidebar to forecast a period that "
            f"already happened."
        )

    # Forecast table
    st.markdown("## Forecast Table")
    rows = []
    for i in range(horizon):
        row = {"Month": i + 1, "Date": fcst_dates[i].strftime("%Y-%m"),
               f"Median ({UNIT[variable]})": round(float(q_median[i]), 3),
               "5th pct": round(float(q_lo[i]), 3), "95th pct": round(float(q_hi[i]), 3)}
        if i < n_actual:
            row["Observed"] = round(float(actual.iloc[i]), 3)
            row["Inside 90% band"] = "yes" if q_lo[i] <= actual.iloc[i] <= q_hi[i] else "no"
        else:
            row["Observed"] = "—"
            row["Inside 90% band"] = "—"
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Chart
    st.markdown("## Stochastic Forecast")
    hist = hist_to_origin["value"].iloc[-hist_window:]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    fig.patch.set_facecolor(COLOR_BG); ax.set_facecolor("white")
    ax.plot(hist.index, hist.values, color=COLOR_CHART, lw=1.6, label="Observed history")
    ax.fill_between(fcst_dates, q_lo, q_hi, color=COLOR_BAND, alpha=0.4, label="Synthetic 5th-95th pct")
    ax.plot([origin_ts] + fcst_dates, [origin_value] + list(q_median),
            "o--", color=COLOR_ACCENT, lw=2.0, markersize=5,
            markerfacecolor="white", markeredgecolor=COLOR_ACCENT, label="Synthetic median")
    if n_actual:
        ax.plot(fcst_dates[:n_actual], actual.iloc[:n_actual].to_numpy(),
                "o-", color=COLOR_CHART, lw=1.8, markersize=5, alpha=0.85, label="Observed (context only)")
    ax.axvline(origin_ts, color=COLOR_TEXT, ls=":", lw=1.2, alpha=0.7)
    ax.set_xlabel("Date"); ax.set_ylabel(f"{VARIABLE_LABEL[variable]} ({UNIT[variable]})")
    ax.set_title(f"{VARIABLE_LABEL[variable]} — stochastic forecast issued {origin_ts:%Y-%m}",
                 fontsize=12, fontweight="bold", color=COLOR_TEXT)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", ls="--", color="#E2E8F0", lw=0.8)
    ax.legend(fontsize=9, loc="upper left")
    fig.autofmt_xdate()
    fig.tight_layout()
    st.pyplot(fig); plt.close(fig)

    # Property-based validation, from results.json (computed once, at
    # pipeline time, over the full validation period -- not re-run per click)
    st.markdown("## Property-Based Validation (2004-2014)")
    st.caption(
        "How well the model's synthetic ensemble reproduces the historical "
        "record's statistical properties, evaluated once over the full "
        "validation period (not this single forecast)."
    )
    val = r["validation"]
    n_ok, n_tot = r["validation_n_within"], r["validation_n_total"]
    st.metric("Properties within the synthetic ensemble's 90% envelope", f"{n_ok} / {n_tot}")
    val_rows = []
    for key, v in val.items():
        val_rows.append({
            "Property": key.replace("_", " "),
            "Historical": v["historical"],
            "Ensemble 5th pct": v["ensemble_p5"],
            "Ensemble median": v["ensemble_median"],
            "Ensemble 95th pct": v["ensemble_p95"],
            "Within envelope": "yes" if v["within_90pct_envelope"] else "no",
        })
    st.dataframe(pd.DataFrame(val_rows), use_container_width=True, hide_index=True)
    st.caption(
        f"Residual Ljung-Box p = {r['diagnostics']['ljung_box']['pvalue']:.4f} "
        f"({'white noise' if r['diagnostics']['ljung_box']['pvalue'] > 0.05 else 'some structure remains'}). "
        f"Basin: {results['basin']} | Data: CAMELS + USGS NWIS, 1980-2014, monthly."
    )
else:
    st.info(
        f"Choose a **variable**, a **forecast origin**, and a **horizon** in the "
        f"sidebar, then press **Run Forecast**.\n\n"
        f"The record runs {first_month:%Y-%m} to {last_month:%Y-%m}. Leaving the "
        f"origin near the end of the record forecasts past it, into months with no "
        f"observations to compare against. Moving it earlier forecasts a stretch "
        f"that already happened, so the observed values can be shown for context."
    )

# ── Model Selection (always visible) ─────────────────────────────────────────
with st.expander("How each model was selected (Box-Jenkins order selection)", expanded=False):
    st.markdown(
        "Each variable goes through its own **Box-Jenkins identification** process, "
        "independently, to find the best ARIMA(p, d, q) configuration:\n\n"
        "1. **Stationarity tests** (ADF + KPSS) on the training data determine the "
        "differencing order d.\n"
        "2. **All combinations** over a grid of p and q values are fitted to the "
        "training data (1980-2003). Each candidate model is scored by the **Akaike "
        "Information Criterion (AIC)**, which rewards accuracy while penalising "
        "unnecessary complexity. The model with the **lowest AIC wins**.\n"
        "3. The winning model's **AR/MA coefficients are estimated** by conditional "
        "sum of squares (exact ordinary least squares for pure autoregressive models), "
        "each with a **standard error** -- not just picked."
    )
    for v in ["discharge", "rainfall", "stage"]:
        rv = results["variables"][v]
        st.markdown(f"**{VARIABLE_LABEL[v]}: ARIMA{tuple(rv['order'])}** "
                    f"(AIC {rv['aic']:.1f}, d={rv['differencing_d']})")
        ranking = rv.get("aic_ranking", [])
        rank_rows = [{"Rank": i + 1, "Model": f"ARIMA{tuple(rr['order'])}",
                      "AIC": round(rr["aic"], 1), "BIC": round(rr["bic"], 1),
                      "Selected": "check" if i == 0 else ""}
                     for i, rr in enumerate(ranking[:5])]
        st.dataframe(pd.DataFrame(rank_rows), use_container_width=True, hide_index=True)
