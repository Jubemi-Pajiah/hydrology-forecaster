"""
0_Forecast.py — Streamlit stochastic forecast dashboard.

Redesigned 2026-08-13 around a single "Get the Outlook" action that forecasts
all three variables (discharge, rainfall, stage) at once and presents them as
a plain-language dashboard, with the statistical detail tucked into
expandable "for the curious" sections rather than up front. Each forecast is
an ENSEMBLE of synthetic monthly sequences, not a single point prediction --
re-running gives a different ensemble each time, which is the point: a
stochastic model's individual forecasts aren't meant to be compared
value-for-value against what actually happened, only its statistical
properties are (see the Documentation page).
"""
import sys
import json
from pathlib import Path

import numpy as np
import pandas as pd
import altair as alt
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.preprocess import build_monthly_dataset
from src.model import ARIMA
from src.simulate import simulate_ensemble

RESULTS_PATH = ROOT / "data" / "results.json"

st.set_page_config(page_title="River Outlook", page_icon=None, layout="wide")

# ── Palette ───────────────────────────────────────────────────────────────────
NAVY = "#1E293B"
BLUE = "#2563EB"
BLUE_LIGHT = "#93C5FD"
AMBER = "#F59E0B"
GREEN = "#16A34A"
RED = "#DC2626"
BG = "#F8FAFC"
SURFACE = "#EFF6FF"
BORDER = "#E2E8F0"
GRAY = "#64748B"

UNIT = {"discharge": "m3/s", "rainfall": "mm/month", "stage": "m"}
VAR_LABEL = {"discharge": "River flow", "rainfall": "Rainfall", "stage": "River level"}
VAR_COLOR = {"discharge": BLUE, "rainfall": "#0EA5E9", "stage": "#7C3AED"}
BASIN_SHORT = "Conecuh River"

ICONS = {
    "discharge": '<path d="M3 15c2-2 4-2 6 0s4 2 6 0 4-2 6 0" stroke-linecap="round" stroke-linejoin="round"/>'
                 '<path d="M3 10c2-2 4-2 6 0s4 2 6 0 4-2 6 0" stroke-linecap="round" stroke-linejoin="round"/>',
    "rainfall": '<path d="M7 15a4 4 0 0 1 .5-7.97A5.5 5.5 0 0 1 18 9.5 3.5 3.5 0 0 1 17.5 16H7z"/>'
                '<path d="M8 18l-1 2M12 18l-1 2M16 18l-1 2" stroke-linecap="round"/>',
    "stage": '<path d="M6 3v18M6 3h3M6 8h3M6 13h3M6 18h3" stroke-linecap="round" stroke-linejoin="round"/>'
             '<path d="M14 20l3-13 3 13" stroke-linecap="round" stroke-linejoin="round"/>',
}


def svg_icon(name, color, size=26):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="1.8">{ICONS[name]}</svg>')


# ── Data / model loading ────────────────────────────────────────────────────
@st.cache_resource
def load_results() -> dict:
    with open(RESULTS_PATH) as f:
        return json.load(f)


@st.cache_resource
def load_monthly(variable: str):
    return build_monthly_dataset(variable)


@st.cache_resource
def fit_model(variable: str):
    """Load the coefficients reported in the thesis rather than re-estimating
    them (fitting on every cold start would be slow, and would silently fit
    on the full record instead of the training-only coefficients reported)."""
    results = load_results()
    r = results["variables"][variable]
    df = load_monthly(variable)
    order = tuple(r["order"])
    return ARIMA.from_params(order, r["constant"], r["phi"], r["theta"],
                             df["log_value"].to_numpy())


# ── Narrative + classification helpers ──────────────────────────────────────
def classify_trend(median_forecast, origin_value):
    start = origin_value if origin_value else float(median_forecast[0])
    tail = median_forecast[-3:] if len(median_forecast) >= 3 else median_forecast
    end = float(np.mean(tail))
    delta = (end - start) / start if start else 0.0
    if abs(delta) < 0.08:
        return "holding fairly steady", "steady"
    return ("rising", "up") if delta > 0 else ("falling", "down")


def classify_level(avg_val, hist_mean):
    ratio = avg_val / hist_mean if hist_mean else 1.0
    if ratio > 1.3:
        return "well above", "attention"
    if ratio > 1.1:
        return "a bit above", "attention"
    if ratio > 0.9:
        return "right around", "normal"
    if ratio > 0.7:
        return "a bit below", "attention"
    return "well below", "attention"


def track_record_word(n_ok, n_total):
    if n_ok >= 6:
        return "Strong track record", GREEN
    if n_ok >= 4:
        return "Reasonable track record", AMBER
    return "Weak track record", RED


def build_narrative(variable, unit, horizon_months, origin_label, avg_val,
                    hist_mean, trend_word, level_word, n_ok, n_total):
    var_label = VAR_LABEL[variable].lower()
    confidence = "a solid" if n_ok >= 6 else ("a reasonable" if n_ok >= 4 else "a rough")
    return (
        f"We are forecasting **{var_label}** for the **{BASIN_SHORT}** over the next "
        f"**{horizon_months} months**, starting **{origin_label}**. Based on the result, "
        f"we see {var_label} **{trend_word}**, averaging about **{avg_val:.1f} {unit}** "
        f"— {level_word} the typical level of {hist_mean:.1f} {unit}. Our model's outlook "
        f"has matched real historical patterns in **{n_ok} of {n_total}** key ways, so "
        f"treat this as {confidence} guide, not a guarantee."
    )


# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Raleway:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap');
    html, body, [class*="css"] {{ font-family: 'Raleway', system-ui, sans-serif; color: {NAVY}; }}
    .block-container {{ padding-top: 2rem; max-width: 1150px; }}
    h1 {{ font-weight: 800 !important; color: {NAVY} !important; letter-spacing: -0.02em; }}
    h2, h3 {{ font-weight: 700 !important; color: {NAVY} !important; }}
    [data-testid="stSidebar"] {{ display: none; }}

    .hero {{ background: linear-gradient(135deg, {SURFACE} 0%, #E0E7FF 100%);
             border-radius: 16px; padding: 1.4rem 1.6rem; margin-bottom: 1.2rem; }}
    .hero p {{ font-size: 1.02rem; line-height: 1.6; margin: 0.2rem 0 0 0; color: {NAVY}; }}

    .controls {{ background: white; border: 1px solid {BORDER}; border-radius: 16px;
                 padding: 1.2rem 1.4rem; margin-bottom: 1.4rem; }}

    div.stButton > button[kind="primary"] {{
        background: {BLUE}; border: none; font-weight: 700; font-size: 1.05rem;
        border-radius: 12px; padding: 0.7rem 1.6rem; box-shadow: 0 4px 14px rgba(37,99,235,0.28);
        transition: transform 150ms ease, box-shadow 150ms ease;
    }}
    div.stButton > button[kind="primary"]:hover {{
        transform: translateY(-1px); box-shadow: 0 6px 18px rgba(37,99,235,0.36);
    }}

    .card {{ background: white; border: 1px solid {BORDER}; border-radius: 16px;
             padding: 1.3rem 1.4rem; height: 100%; }}
    .card-head {{ display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.6rem; }}
    .card-title {{ font-size: 1.05rem; font-weight: 700; color: {NAVY}; margin: 0; }}
    .big-stat {{ font-family: 'JetBrains Mono', monospace; font-weight: 600; font-size: 1.9rem;
                 color: {NAVY}; margin: 0.15rem 0; }}
    .pill {{ display: inline-block; font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
             letter-spacing: 0.05em; padding: 0.22rem 0.6rem; border-radius: 99px; margin-right: 0.4rem; }}
    .narrative {{ font-size: 0.9rem; line-height: 1.6; color: #334155; margin-top: 0.7rem; }}

    [data-testid="stExpander"] {{ border: 1px solid {BORDER}; border-radius: 12px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

results = load_results()

# ── Hero ─────────────────────────────────────────────────────────────────────
st.title("River Outlook")
st.markdown(
    f"""<div class="hero"><p>
    A plain-language look ahead for the <strong>{BASIN_SHORT} at Brantley, Alabama</strong>
    &mdash; how much water is expected to flow, how much rain is expected to fall, and how
    high the river is expected to run. Three separate statistical models, each one learning
    only from that variable's own 35-year history, generate a thousand possible versions of
    what could happen next and summarise them below. Nothing here is a single guaranteed
    number &mdash; it's a range of plausible outcomes, which is the honest way to describe
    a river's future.
    </p></div>""",
    unsafe_allow_html=True,
)

# ── Controls ─────────────────────────────────────────────────────────────────
full_df = {v: load_monthly(v) for v in ["discharge", "rainfall", "stage"]}
last_month = full_df["discharge"].index[-1]
first_month = full_df["discharge"].index[0]
month_options = list(full_df["discharge"].index)

with st.container():
    st.markdown('<div class="controls">', unsafe_allow_html=True)
    c1, c2 = st.columns([1.3, 2])
    with c1:
        start_mode = st.segmented_control(
            "Start the outlook from",
            options=["End of record (2014-12)", "A date I pick"],
            default="End of record (2014-12)", required=True,
        )
        if start_mode == "A date I pick":
            origin_idx = st.selectbox(
                "Which month?", options=range(len(month_options)),
                index=len(month_options) - 25,
                format_func=lambda i: month_options[i].strftime("%B %Y"),
                help="Pick a month before the end of the record to also see what "
                     "actually happened next, for comparison.",
            )
            origin_ts = month_options[origin_idx]
        else:
            origin_ts = last_month
    with c2:
        horizon_label = st.segmented_control(
            "How far ahead", options=["3 months", "6 months", "1 year", "2 years"],
            default="1 year", required=True,
        )
        horizon = {"3 months": 3, "6 months": 6, "1 year": 12, "2 years": 24}.get(horizon_label, 12)

    with st.expander("Advanced settings"):
        n_reps = st.slider("Synthetic replicates", 100, 1000, 400, 100,
                           help="More replicates = smoother uncertainty bands, slower to compute.")
        hist_window = st.slider("History to show on the chart (months)", 12, 240, 48, 6)

    go = st.button("Get the Outlook", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

origin_label = origin_ts.strftime("%B %Y")

# ── Run: forecast all three variables at once ───────────────────────────────
if go:
    with st.spinner("Running a thousand possible futures for each variable..."):
        outputs = {}
        for v in ["discharge", "rainfall", "stage"]:
            df = full_df[v]
            model = fit_model(v)
            r = results["variables"][v]
            hist_to_origin = df.loc[:origin_ts]
            ens = simulate_ensemble(model, hist_to_origin["log_value"].to_numpy(),
                                    horizon, n_reps=n_reps, method="gaussian", seed=None)
            fcst_dates = [origin_ts + pd.DateOffset(months=i + 1) for i in range(horizon)]
            origin_value = float(hist_to_origin["value"].iloc[-1])
            q_median = np.median(ens, axis=0)
            q_lo, q_hi = np.percentile(ens, [5, 95], axis=0)
            actual = df["value"].reindex(fcst_dates)
            n_actual = int(actual.notna().sum())

            avg_val = float(np.mean(q_median))
            hist_mean = r["historical_stats"]["mean"]
            trend_word, trend_dir = classify_trend(q_median, origin_value)
            level_word, level_status = classify_level(avg_val, hist_mean)
            n_ok, n_tot = r["validation_n_within"], r["validation_n_total"]

            outputs[v] = dict(
                df=df, hist_to_origin=hist_to_origin, fcst_dates=fcst_dates,
                q_median=q_median, q_lo=q_lo, q_hi=q_hi, actual=actual, n_actual=n_actual,
                avg_val=avg_val, hist_mean=hist_mean, trend_word=trend_word,
                trend_dir=trend_dir, level_word=level_word, level_status=level_status,
                n_ok=n_ok, n_tot=n_tot, r=r,
            )

    # ── Dashboard: three KPI cards ──────────────────────────────────────────
    st.markdown(f"### Outlook for the {horizon}-month period starting {origin_label}")
    cols = st.columns(3)
    trend_arrow = {"up": "&#9650;", "down": "&#9660;", "steady": "&#8226;"}
    trend_color = {"up": BLUE, "down": AMBER, "steady": GRAY}
    level_pill_color = {"normal": GREEN, "attention": AMBER}

    for col, v in zip(cols, ["discharge", "rainfall", "stage"]):
        o = outputs[v]
        record_word, record_color = track_record_word(o["n_ok"], o["n_tot"])
        with col:
            st.markdown(
                f"""<div class="card">
                <div class="card-head">{svg_icon(v, VAR_COLOR[v])}
                    <p class="card-title">{VAR_LABEL[v]}</p></div>
                <div class="big-stat">{o['avg_val']:.1f} <span style="font-size:1rem;font-weight:500;color:{GRAY}">{UNIT[v]}</span></div>
                <div>
                    <span class="pill" style="background:{trend_color[o['trend_dir']]}22;color:{trend_color[o['trend_dir']]}">
                        {trend_arrow[o['trend_dir']]} {o['trend_word'].split()[0].capitalize()}</span>
                    <span class="pill" style="background:{level_pill_color[o['level_status']]}22;color:{level_pill_color[o['level_status']]}">
                        {o['level_word'].capitalize()} typical</span>
                </div>
                <div class="narrative">{build_narrative(v, UNIT[v], horizon, origin_label, o['avg_val'], o['hist_mean'], o['trend_word'], o['level_word'], o['n_ok'], o['n_tot'])}</div>
                <div style="margin-top:0.8rem;">
                    <span class="pill" style="background:{record_color}22;color:{record_color}">{record_word}: {o['n_ok']}/{o['n_tot']}</span>
                </div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("&nbsp;", unsafe_allow_html=True)

    # ── Charts: one per variable, tabbed ─────────────────────────────────────
    st.markdown("### The picture behind each number")
    tabs = st.tabs([VAR_LABEL[v] for v in ["discharge", "rainfall", "stage"]])
    for tab, v in zip(tabs, ["discharge", "rainfall", "stage"]):
        o = outputs[v]
        with tab:
            hist = o["hist_to_origin"]["value"].iloc[-hist_window:]
            hist_df = pd.DataFrame({"date": hist.index, "value": hist.values, "series": "Observed history"})
            fcst_df = pd.DataFrame({
                "date": o["fcst_dates"], "median": o["q_median"],
                "lo": o["q_lo"], "hi": o["q_hi"],
            })

            band = alt.Chart(fcst_df).mark_area(opacity=0.22, color=VAR_COLOR[v]).encode(
                x=alt.X("date:T", title=None),
                y=alt.Y("lo:Q", title=f"{VAR_LABEL[v]} ({UNIT[v]})"),
                y2="hi:Q",
            )
            median_line = alt.Chart(fcst_df).mark_line(
                strokeDash=[5, 3], color=VAR_COLOR[v], point=alt.OverlayMarkDef(color=VAR_COLOR[v]),
            ).encode(
                x="date:T", y="median:Q",
                tooltip=[alt.Tooltip("date:T", title="Month", format="%b %Y"),
                        alt.Tooltip("median:Q", title=f"Expected ({UNIT[v]})", format=".1f")],
            )
            hist_line = alt.Chart(hist_df).mark_line(color=NAVY, strokeWidth=1.8).encode(
                x="date:T", y="value:Q",
                tooltip=[alt.Tooltip("date:T", title="Month", format="%b %Y"),
                        alt.Tooltip("value:Q", title=f"Observed ({UNIT[v]})", format=".1f")],
            )
            layers = [band, hist_line, median_line]
            if o["n_actual"]:
                actual_df = pd.DataFrame({
                    "date": o["fcst_dates"][:o["n_actual"]],
                    "value": o["actual"].iloc[:o["n_actual"]].to_numpy(),
                })
                actual_line = alt.Chart(actual_df).mark_line(
                    color=NAVY, strokeDash=[2, 2], point=alt.OverlayMarkDef(color=NAVY, size=25),
                ).encode(
                    x="date:T", y="value:Q",
                    tooltip=[alt.Tooltip("date:T", title="Month", format="%b %Y"),
                            alt.Tooltip("value:Q", title=f"What actually happened ({UNIT[v]})", format=".1f")],
                )
                layers.append(actual_line)

            chart = alt.layer(*layers).properties(height=280).interactive()
            st.altair_chart(chart, use_container_width=True)

            legend_bits = [
                f'<span style="color:{NAVY}">&#9644;</span> Observed history',
                f'<span style="color:{VAR_COLOR[v]}">&#9646;&#9646;</span> Uncertainty range (90%)',
                f'<span style="color:{VAR_COLOR[v]}">- - -</span> Expected path',
            ]
            if o["n_actual"]:
                legend_bits.append(f'<span style="color:{NAVY}">&middot;&middot;&middot;</span> What actually happened')
            st.caption(" &nbsp;&nbsp; ".join(legend_bits), unsafe_allow_html=True)

            if o["n_actual"]:
                n_inside = int(np.sum(
                    (o["actual"].iloc[:o["n_actual"]].to_numpy() >= o["q_lo"][:o["n_actual"]]) &
                    (o["actual"].iloc[:o["n_actual"]].to_numpy() <= o["q_hi"][:o["n_actual"]])
                ))
                st.caption(f"Of the {o['n_actual']} months we can check, {n_inside} landed inside the "
                          f"uncertainty range shown above.")

    # ── For the curious: technical detail, tucked away ──────────────────────
    with st.expander("For the curious: the statistics behind this outlook"):
        for v in ["discharge", "rainfall", "stage"]:
            o = outputs[v]
            r = o["r"]
            st.markdown(f"#### {VAR_LABEL[v]}")
            st.markdown(
                f"Model: `ARIMA{tuple(r['order'])}`, AIC {r['aic']:.1f}, differencing d={r['differencing_d']}. "
                f"Coefficients estimated on 1980-2003, validated on 2004-2014."
            )
            val_rows = [{"Property": k.replace("_", " "), "Historical": v2["historical"],
                        "Model's range (90%)": f"[{v2['ensemble_p5']:.2f}, {v2['ensemble_p95']:.2f}]",
                        "Reproduced?": "yes" if v2["within_90pct_envelope"] else "no"}
                       for k, v2 in r["validation"].items()]
            st.dataframe(pd.DataFrame(val_rows), use_container_width=True, hide_index=True)
            lb_p = r["diagnostics"]["ljung_box"]["pvalue"]
            st.caption(f"Residual check (Ljung-Box p = {lb_p:.4f}): "
                      f"{'no leftover pattern detected' if lb_p > 0.05 else 'some leftover pattern remains, noted in the report'}.")
            st.markdown("---")

else:
    st.markdown(
        f"""<div class="controls" style="text-align:center;padding:2.5rem;">
        <p style="font-size:1.05rem;color:{GRAY};margin:0;">
        Choose a starting point and how far ahead to look above, then press
        <strong style="color:{BLUE}">Get the Outlook</strong>.</p>
        <p style="font-size:0.88rem;color:{GRAY};margin-top:0.6rem;">
        Data on record: {first_month:%B %Y} to {last_month:%B %Y}.</p>
        </div>""",
        unsafe_allow_html=True,
    )
