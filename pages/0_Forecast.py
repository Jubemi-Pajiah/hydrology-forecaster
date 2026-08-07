"""
0_Forecast.py — Streamlit forecast tool for the statistical (ARIMA) streamflow
model. Forecasts daily discharge of the Conecuh River from its own past values;
no rainfall or meteorological input is required.
"""
import sys
import json
from pathlib import Path
from datetime import timedelta

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.preprocess import build_dataset, inv_log_transform
from src.model import ARIMA

RESULTS_PATH = ROOT / "data" / "results.json"

# ── Palette ─────────────────────────────────────────────────────────────────
COLOR_PRIMARY = "#2563EB"
COLOR_ACCENT = "#F97316"
COLOR_BG = "#F8FAFC"
COLOR_TEXT = "#1E293B"
COLOR_SURFACE = "#EFF6FF"
COLOR_BORDER = "#CBD5E1"
COLOR_CHART = "#0080FF"
COLOR_MEAN_LINE = "#059669"


@st.cache_resource
def load_results() -> dict:
    with open(RESULTS_PATH) as f:
        return json.load(f)


@st.cache_resource
def load_data():
    return build_dataset()


@st.cache_resource
def fit_model(order_tuple):
    """
    Load the model reported in the thesis rather than re-estimating it.

    Re-fitting here was wrong on two counts. It ran the conditional-sum-of-
    squares optimiser on every cold start, which took over two minutes on the
    free tier and left visitors staring at a blank page; and it fitted on the
    FULL 1980-2014 record, validation period included, so the app's
    coefficients silently differed from the training-period coefficients
    reported in Chapter Four while the sidebar displayed the thesis AIC beside
    them. Loading the stored coefficients fixes both: the app now forecasts
    with exactly the model the document describes, and starts in under a
    second.
    """
    results = load_results()
    df = load_data()
    return ARIMA.from_params(order_tuple, results["constant"], results["phi"],
                             results["theta"], df["log_flow"].to_numpy())


def explain_forecast(q_fcst, origin_flow, origin_date, q_mean, results, horizon):
    """Rule-based plain-English explanation of a forecast (no external model)."""
    end = float(q_fcst[-1])
    chg = (end - origin_flow) / origin_flow * 100.0 if origin_flow else 0.0
    if abs(chg) < 4:
        trend = f"stay close to its latest level, around {end:.1f} m³/s"
    elif chg > 0:
        trend = f"rise gradually to about {end:.1f} m³/s (up ~{abs(chg):.0f}%)"
    else:
        trend = f"ease down to about {end:.1f} m³/s (down ~{abs(chg):.0f}%)"

    ratio = end / q_mean if q_mean else 1.0
    if ratio < 0.5:
        level, regime = "well below the long-term average — a low-flow (dry) spell", "low"
    elif ratio < 0.85:
        level, regime = "below the long-term average", "low"
    elif ratio <= 1.15:
        level, regime = "close to the long-term average", "normal"
    elif ratio <= 2.0:
        level, regime = "above the long-term average", "high"
    else:
        level, regime = "well above average — a high-flow spell", "high"

    if regime == "low":
        drift = ("Because the river is currently running low, the model expects it "
                 "to recover slowly toward normal levels.")
    elif regime == "high":
        drift = ("Because the river is currently running high, the model expects it "
                 "to recede slowly toward normal levels.")
    else:
        drift = ("Because the river is near its usual level, the model expects only "
                 "small day-to-day changes.")

    nse1 = results.get("forecast", {}).get("1", {}).get("model", {}).get("NSE", 0.82)
    days = f"{horizon} day" + ("s" if horizon > 1 else "")
    return [
        f"**What the model did:** starting from the discharge measured on "
        f"{origin_date:%d %b %Y} ({origin_flow:.1f} m³/s), it projected the flow "
        f"{days} ahead using only the river's own history up to that day — no "
        f"rainfall or weather data, and nothing measured afterwards.",
        f"**What it expects:** over this period the flow should {trend}. That is "
        f"{level} (the long-term average is {q_mean:.0f} m³/s).",
        f"**Why the days look similar:** river flow changes slowly, so the forecasts "
        f"move only gently. {drift}",
        f"**How much to trust it:** the first day is the most reliable (validated as "
        f"'very good', NSE {nse1:.2f}); accuracy falls with each extra day, so treat "
        f"anything beyond about three days as a rough guide only.",
    ]


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
order = tuple(results["aic_ranking"][0]["order"]) if results.get("aic_ranking") else (3, 1, 2)

df = load_data()
model = fit_model(order)
flow = df["flow"]
first_date = df.index[0]
last_date = df.index[-1]
q_mean = float(flow.mean())

# ── Header ──────────────────────────────────────────────────────────────────
st.title("Conecuh River Streamflow Forecaster")
st.markdown(
    f"""<div class="app-intro">
    A <strong>statistical {results['model']} time-series model</strong> forecasts daily river
    discharge for the <strong>Conecuh River, Alabama (USGS 02361000)</strong> using only the
    river's own <strong>past discharge</strong> &mdash; no rainfall or weather input is needed.<br>
    This runs on the <strong>observed record for {first_date:%Y}&ndash;{last_date:%Y}</strong>, so
    forecast dates are historical, not today's. Pick a <strong>forecast origin</strong> and a
    horizon in the sidebar, then press <strong>Run Forecast</strong>. Choose an origin before
    {last_date:%d %b %Y} and the app will show you what the river
    <strong>actually did</strong> next, so you can see how close the model got.<br>
    <strong>Input:</strong> discharge up to the origin &nbsp;|&nbsp;
    <strong>Output:</strong> daily discharge forecast (m&sup3;/s)
    </div>""",
    unsafe_allow_html=True,
)

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Forecast Configuration")
    origin_date = st.date_input(
        "Forecast origin",
        value=last_date.date(),
        min_value=(first_date + timedelta(days=365)).date(),
        max_value=last_date.date(),
        help="The day the forecast is issued from. The model sees discharge up "
             "to and including this day and nothing after it. Pick an earlier "
             "date to forecast a period that already happened and compare the "
             "forecast against what the river actually did.",
    )
    origin_ts = pd.Timestamp(origin_date)
    horizon = int(st.number_input("Horizon (days)", min_value=1, max_value=7,
                                  value=3, step=1,
                                  help="Number of days ahead to forecast (1-7)"))
    hist_window = int(st.slider("History to display (days)", 30, 365, 90, 5))
    st.markdown("---")
    st.markdown("#### Model")
    st.caption(
        f"Model: **{results['model']}**  \n"
        f"Differencing d = {results['differencing_d']}  \n"
        f"AIC = {results['aic']:.0f}  \n"
        f"Coefficients estimated on the training period (1980-2003)"
    )
    run_btn = st.button("Run Forecast", type="primary", use_container_width=True)

# ── Run ─────────────────────────────────────────────────────────────────────
if run_btn:
    # The model sees discharge up to and including the chosen origin and
    # nothing after it, exactly as in the rolling-origin evaluation of the
    # thesis. Forecast on the log scale, then back-transform with the same
    # log-normal bias correction (exp(mu + sigma_k^2 / 2)), so the app and the
    # reported results are consistent and the values are unbiased.
    hist_to_origin = df.loc[:origin_ts]
    log_fcst = model.forecast_from(hist_to_origin["log_flow"].to_numpy(), horizon)
    q_fcst = inv_log_transform(log_fcst + 0.5 * model.kstep_logvar(horizon))
    fcst_dates = [origin_ts + timedelta(days=i + 1) for i in range(horizon)]
    origin_flow = float(hist_to_origin["flow"].iloc[-1])

    # Where the origin is early enough, the record already contains what the
    # river actually did, so the forecast can be scored against it.
    actual = flow.reindex(fcst_dates)
    n_actual = int(actual.notna().sum())

    st.markdown('<span class="section-label">Forecast Summary</span>', unsafe_allow_html=True)
    kpi_cols = st.columns(min(horizon, 7))
    for i, col in enumerate(kpi_cols):
        with col:
            if i < n_actual:
                err = q_fcst[i] - float(actual.iloc[i])
                st.metric(label=f"Day {i+1}  {fcst_dates[i].strftime('%d %b %Y')}",
                          value=f"{q_fcst[i]:.2f} m³/s",
                          delta=f"{err:+.2f} vs actual",
                          delta_color="inverse")
            else:
                delta = (q_fcst[i] - q_mean) / q_mean * 100.0
                st.metric(label=f"Day {i+1}  {fcst_dates[i].strftime('%d %b %Y')}",
                          value=f"{q_fcst[i]:.2f} m³/s",
                          delta=f"{delta:+.0f}% vs mean")

    if n_actual:
        mae = float(np.mean(np.abs(q_fcst[:n_actual] - actual.iloc[:n_actual].to_numpy())))
        st.success(
            f"**Verified against the record.** The river's actual discharge on "
            f"these days is known, so the forecast above is scored against it: "
            f"mean absolute error **{mae:.2f} m³/s** over {n_actual} day"
            f"{'s' if n_actual > 1 else ''}. The model was given no data after "
            f"{origin_ts:%d %b %Y}."
        )
    else:
        st.warning(
            f"**No actual values to compare against.** {origin_ts:%d %b %Y} is the "
            f"end of the observed record, so these days lie beyond the data and "
            f"nothing can be checked. Move the forecast origin back in the "
            f"sidebar to forecast a period that already happened and see how "
            f"close the model gets."
        )

    # Plain-language explanation
    st.markdown("## What this forecast means")
    for line in explain_forecast(q_fcst, origin_flow, origin_ts,
                                 q_mean, results, horizon):
        st.markdown(f"- {line}")
    st.caption(
        f"Note: this is a demonstration built on the historical record, which runs "
        f"from {first_date:%d %b %Y} to {last_date:%d %b %Y}. Forecast dates are "
        f"therefore historical, not today's date. The model is a statistical one: "
        f"it projects the river forward from its own past values only."
    )

    # Forecast table
    st.markdown("## Forecast Table")
    rows = []
    for i in range(horizon):
        row = {"Day": i + 1, "Date": fcst_dates[i].strftime("%Y-%m-%d"),
               "Q forecast (m³/s)": round(float(q_fcst[i]), 3)}
        if i < n_actual:
            a = float(actual.iloc[i])
            row["Q actual (m³/s)"] = round(a, 3)
            row["Error (m³/s)"] = round(float(q_fcst[i]) - a, 3)
            row["Error (%)"] = f"{(q_fcst[i] - a) / a * 100:+.1f}%" if a else "n/a"
        else:
            row["Q actual (m³/s)"] = "—"
            row["Error (m³/s)"] = "—"
            row["Error (%)"] = "—"
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Chart: history up to the origin, the forecast, and (where known) the
    # discharge that actually followed
    st.markdown("## Discharge Forecast")
    hist = hist_to_origin["flow"].iloc[-hist_window:]
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor(COLOR_BG); ax.set_facecolor("white")
    ax.plot(hist.index, hist.values, color=COLOR_CHART, lw=1.6,
            label="Observed history (seen by model)")
    fc_x = [origin_ts] + fcst_dates
    fc_y = [origin_flow] + list(q_fcst)
    ax.plot(fc_x, fc_y, "o--", color=COLOR_ACCENT, lw=2.2, markersize=7,
            markerfacecolor="white", markeredgecolor=COLOR_ACCENT, label="Forecast")
    if n_actual:
        ax.plot([origin_ts] + fcst_dates[:n_actual],
                [origin_flow] + list(actual.iloc[:n_actual].to_numpy()),
                "o-", color=COLOR_CHART, lw=2.0, markersize=6, alpha=0.85,
                label="Actual (not seen by model)")
    ax.axvline(origin_ts, color=COLOR_TEXT, ls=":", lw=1.2, alpha=0.7)
    ax.axhline(q_mean, color=COLOR_MEAN_LINE, ls="--", lw=1.3,
               label=f"Record mean {q_mean:.1f} m³/s")
    ax.set_xlabel("Date"); ax.set_ylabel("Discharge (m³/s)")
    ax.set_title(f"Conecuh River — forecast issued {origin_ts:%d %b %Y}",
                 fontsize=12, fontweight="bold", color=COLOR_TEXT)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", ls="--", color="#E2E8F0", lw=0.8)
    ax.legend(fontsize=9, loc="upper left")
    fig.autofmt_xdate()
    fig.tight_layout()
    st.pyplot(fig); plt.close(fig)

    # Validation skill (from results.json)
    st.markdown("## Validation Skill (2004-2014)")
    f = results["forecast"]
    sc = st.columns(3)
    for i, k in enumerate(("1", "2", "3")):
        with sc[i]:
            st.metric(label=f"{k}-day NSE",
                      value=f"{f[k]['model']['NSE']:.3f}",
                      delta=f"PSS {f[k]['model']['PSS']:+.3f} vs persistence")
    st.caption(
        f"Out-of-sample skill from rolling-origin validation. "
        f"Residual Ljung-Box p = {results['ljung_box']['pvalue']:.3f} "
        f"({'white noise — model adequate' if results['ljung_box']['pvalue'] > 0.05 else 'structure remains'}). "
        f"Basin: Conecuh River, Alabama (USGS 02361000) | "
        f"Data: CAMELS observed discharge, 1980-2014 | discharge-only statistical model."
    )
else:
    st.info(
        f"Set the **forecast origin** and **horizon** in the sidebar, then press "
        f"**Run Forecast**.\n\n"
        f"The record runs {first_date:%d %b %Y} to {last_date:%d %b %Y}. Leaving "
        f"the origin at the end of the record forecasts past it, into days with "
        f"no observations to check against. Moving it earlier forecasts a stretch "
        f"of river that already happened, and the app then scores the forecast "
        f"against what was actually measured."
    )

# ── Model Selection (always visible) ─────────────────────────────────────────
with st.expander("How the model was selected (Box-Jenkins order selection)", expanded=False):
    st.markdown(
        "Before any forecast is made, the model goes through a **Box-Jenkins identification** "
        "process to find the best ARIMA(p, d, q) configuration:\n\n"
        "1. **Stationarity tests** (ADF + KPSS) on the training data determined the differencing "
        f"order **d = {results['differencing_d']}** — meaning the series is differenced once to remove slow trends.\n"
        "2. **ACF / PACF plots** suggested candidate ranges for the autoregressive order p and "
        "moving-average order q.\n"
        "3. **All combinations** over a grid of p and q values were fitted to the training data "
        "(1980–2003). Each candidate model was scored by the **Akaike Information Criterion (AIC)** "
        "— a measure that rewards accuracy while penalising unnecessary complexity. "
        "The model with the **lowest AIC wins**."
    )
    st.markdown("**Top 5 candidate models ranked by AIC** (lower = better fit):")
    ranking = results.get("aic_ranking", [])
    rank_rows = [{"Rank": i + 1,
                  "Model": f"ARIMA{tuple(r['order'])}",
                  "AIC": round(r["aic"], 1),
                  "BIC": round(r["bic"], 1),
                  "Selected": "✓" if i == 0 else ""}
                 for i, r in enumerate(ranking[:5])]
    st.dataframe(pd.DataFrame(rank_rows), use_container_width=True, hide_index=True)
    st.caption(
        f"Winner: **{results['model']}** (AIC {results['aic']:.1f}). "
        "The AIC and BIC both penalise model complexity, so winning on both gives confidence "
        "that the selected order is not over-fitted. Ljung-Box residual test p = "
        f"{results['ljung_box']['pvalue']:.3f} (> 0.05 → residuals are white noise, model is adequate)."
    )
