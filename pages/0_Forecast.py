"""
0_Forecast.py — Streamlit stochastic forecast dashboard.

Redesigned 2026-08-13 (v2) as a three-pane app shell: a static context rail
on the left, the interactive controls/chart/story in the centre, and a
compact outlook-card rail on the right -- rather than one narrow centred
column, so the wide layout is actually used instead of fought.

Redesigned again 2026-08-13 (v3): controls are framed as a future date
RANGE ("predict from X to Y"), not an "origin + horizon" -- the last real
data point (Dec 2014) is purely an internal simulation anchor, never a
concept the user has to think about.

A forecast here is an ENSEMBLE of synthetic monthly sequences, not a single
point prediction -- re-running gives a different ensemble each time, which
is the point: a stochastic model's individual forecasts aren't meant to be
compared value-for-value against what actually happened, only its
statistical properties are (see the Documentation page).
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


def svg_icon(name, color, size=22):
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


def year_stepper(key, min_year, max_year, columns):
    """A year dropdown (searchable, jump-to-any-year) flanked by -/+ buttons
    (nudge by one). Buttons are rendered in their own columns before the
    dropdown so their session_state writes happen before the dropdown widget
    with the same key is instantiated -- Streamlit forbids writing to a
    key after its widget exists in the same run."""
    dec_col, mid_col, inc_col = columns
    with dec_col:
        dec_clicked = st.button("−", key=f"{key}_dec", use_container_width=True)
    with inc_col:
        inc_clicked = st.button("+", key=f"{key}_inc", use_container_width=True)
    if dec_clicked:
        st.session_state[key] = max(min_year, st.session_state[key] - 1)
    if inc_clicked:
        st.session_state[key] = min(max_year, st.session_state[key] + 1)
    with mid_col:
        st.selectbox("Year", list(range(min_year, max_year + 1)), key=key,
                    label_visibility="collapsed")
    return st.session_state[key]


def track_record_word(n_ok, n_total):
    if n_ok >= 6:
        return "Strong track record", GREEN
    if n_ok >= 4:
        return "Reasonable track record", AMBER
    return "Weak track record", RED


def build_narrative(variable, unit, from_label, to_label, avg_val,
                    hist_mean, trend_word, level_word, n_ok, n_total):
    """Fill-in-the-blanks narrative. Uses <strong> (not Markdown **bold**)
    because it is always injected into a raw HTML block, where Markdown
    syntax is not parsed."""
    var_label = VAR_LABEL[variable].lower()
    confidence = "a solid" if n_ok >= 6 else ("a reasonable" if n_ok >= 4 else "a rough")
    return (
        f"We are forecasting <strong>{var_label}</strong> for the <strong>{BASIN_SHORT}</strong> "
        f"from <strong>{from_label}</strong> to <strong>{to_label}</strong>. Based on the "
        f"result, we see {var_label} <strong>{trend_word}</strong>, averaging about "
        f"<strong>{avg_val:.1f} {unit}</strong> &mdash; {level_word} the typical level of "
        f"{hist_mean:.1f} {unit}. Our model's outlook has matched real historical patterns "
        f"in <strong>{n_ok} of {n_total}</strong> key ways, so treat this as {confidence} "
        f"guide, not a guarantee."
    )


# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Raleway:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap');
    html, body, [class*="css"] {{ font-family: 'Raleway', system-ui, sans-serif; color: {NAVY}; }}
    .stApp {{ background: radial-gradient(1200px 600px at 15% -10%, #DBEAFE55 0%, transparent 60%),
                          radial-gradient(1000px 500px at 100% 0%, #E9D5FF44 0%, transparent 55%),
                          {BG}; }}
    .block-container {{ padding-top: 1.6rem; max-width: 1760px; }}
    h1 {{ font-weight: 800 !important; letter-spacing: -0.02em; margin-bottom:0 !important;
         background: linear-gradient(100deg, {NAVY} 30%, {BLUE} 100%);
         -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }}
    h3 {{ font-weight: 700 !important; color: {NAVY} !important; }}
    [data-testid="stSidebar"] {{ display: none; }}

    .rail-card {{ background: linear-gradient(165deg, #FFFFFF 0%, #F8FAFF 100%);
                  border: 1px solid {BORDER}; border-top: 3px solid {BLUE};
                  border-radius: 14px; padding: 1.1rem 1.2rem; margin-bottom: 1rem;
                  box-shadow: 0 4px 18px rgba(37,99,235,0.07); }}
    .rail-card h4 {{ margin: 0 0 0.5rem 0; font-size: 0.82rem; font-weight: 700; color: {BLUE};
                     text-transform: uppercase; letter-spacing: 0.06em; }}
    .rail-card p, .rail-card li {{ font-size: 0.88rem; line-height: 1.55; color: #334155; margin: 0.3rem 0; }}
    .rail-fact {{ display: flex; justify-content: space-between; font-size: 0.85rem; padding: 0.3rem 0;
                  border-bottom: 1px dashed {BORDER}; }}
    .rail-fact b {{ color: {NAVY}; }}

    .controls {{ background: white; border: 1px solid {BORDER}; border-radius: 16px;
                 padding: 1.1rem 1.3rem; margin-bottom: 1.1rem; }}
    [data-testid="stVerticalBlockBorderWrapper"] > div:first-child {{
        background: linear-gradient(180deg, #FFFFFF 0%, #FAFBFF 100%);
    }}

    div.stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {BLUE} 0%, #0EA5E9 100%);
        border: none; color: white; font-weight: 700; font-size: 1.0rem;
        border-radius: 12px; padding: 0.6rem 1.5rem;
        box-shadow: 0 6px 18px rgba(37,99,235,0.38), 0 1px 2px rgba(37,99,235,0.25);
        transition: transform 150ms ease, box-shadow 150ms ease;
    }}
    div.stButton > button[kind="primary"]:hover {{
        transform: translateY(-2px); box-shadow: 0 10px 26px rgba(37,99,235,0.46);
    }}
    div.stButton > button[kind="secondary"] {{
        background: linear-gradient(180deg, #FFFFFF 0%, #F0F5FE 100%);
        border: 1.5px solid #DBEAFE; color: {NAVY}; font-weight: 600;
        border-radius: 10px; transition: all 150ms ease;
    }}
    div.stButton > button[kind="secondary"]:hover {{
        border-color: {BLUE}; color: {BLUE};
        background: linear-gradient(180deg, #EFF6FF 0%, #DBEAFE 100%);
        box-shadow: 0 4px 14px rgba(37,99,235,0.2); transform: translateY(-1px);
    }}

    .card {{ background: white; border: 1px solid {BORDER}; border-radius: 14px;
             padding: 0.95rem 1.05rem; margin-bottom: 0.9rem;
             transition: transform 150ms ease, box-shadow 150ms ease; }}
    .card:hover {{ transform: translateY(-1px); }}
    .card-head {{ display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.35rem; }}
    .card-title {{ font-size: 0.92rem; font-weight: 700; color: {NAVY}; margin: 0; }}
    .big-stat {{ font-family: 'JetBrains Mono', monospace; font-weight: 600; font-size: 1.55rem;
                 color: {NAVY}; margin: 0.1rem 0; }}
    .pill {{ display: inline-block; font-size: 0.66rem; font-weight: 700; text-transform: uppercase;
             letter-spacing: 0.04em; padding: 0.18rem 0.5rem; border-radius: 99px; margin: 0.15rem 0.3rem 0 0; }}
    .narrative {{ font-size: 0.87rem; line-height: 1.6; color: #334155; margin-top: 0.7rem; }}

    [data-testid="stExpander"] {{ border: 1px solid {BORDER}; border-left: 3px solid {BLUE};
                                  border-radius: 12px; background: #FFFFFF; }}
    [data-baseweb="tab-highlight"] {{ background-color: {BLUE} !important; height: 3px !important; }}
    [data-baseweb="tab"][aria-selected="true"] {{ color: {BLUE} !important; font-weight: 700; }}
    [data-testid="stSliderThumbValue"], .stSlider [role="slider"] {{ background-color: {BLUE} !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)

results = load_results()
full_df = {v: load_monthly(v) for v in ["discharge", "rainfall", "stage"]}
last_month = full_df["discharge"].index[-1]
first_month = full_df["discharge"].index[0]

# ── Header (full width) ──────────────────────────────────────────────────────
st.title("River Outlook")
st.caption(f"{BASIN_SHORT} at Brantley, Alabama &nbsp;&middot;&nbsp; USGS 02371500 &nbsp;&middot;&nbsp; "
          f"record: {first_month:%b %Y}–{last_month:%b %Y}", unsafe_allow_html=True)
st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

left, center, right = st.columns([1, 2.35, 1.15], gap="medium")

# ── LEFT rail: static context, doesn't change on interaction ────────────────
with left:
    st.markdown(
        f"""<div class="rail-card"><h4>What this is</h4>
        <p>Three separate statistical models &mdash; one each for river flow, rainfall and
        river level &mdash; each learn only from that variable's own 35-year history, then
        generate a thousand possible versions of what could happen next.</p>
        <p>Nothing here is a single guaranteed number. It's a <strong>range of plausible
        outcomes</strong>, which is the honest way to describe a river's future.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""<div class="rail-card"><h4>Good to know</h4>
        <div class="rail-fact"><span>Data ends</span><b>{last_month:%b %Y}</b></div>
        <div class="rail-fact"><span>Years of history</span><b>35</b></div>
        <div class="rail-fact"><span>Variables modelled</span><b>3, independently</b></div>
        <div class="rail-fact"><span>Method</span><b>ARIMA (Box&ndash;Jenkins)</b></div>
        <p style="margin-top:0.6rem;">Pick any future window you actually want &mdash;
        2030 to 2035, 2050 to 2060, whatever. The model builds forward internally from
        the last real measurement to get there; that's just plumbing, not something you
        need to think about. The further out the window, the wider the plausible range
        gets &mdash; that's the model being honest about how much less certain a
        50-year-out guess is than a 1-year one, not a flaw.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    st.page_link("pages/1_Documentation.py", label="How the method works, in full")

# ── CENTER: controls, then chart + story ─────────────────────────────────────
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"]
PRESETS = {
    "2025 – 2030": (2025, "January", 2030, "January"),
    "2030 – 2035": (2030, "January", 2035, "January"),
    "2035 – 2045": (2035, "January", 2045, "January"),
    "2045 – 2065": (2045, "January", 2065, "January"),
}
MIN_YEAR = last_month.year + 1  # the record ends 2014-12; every predictable month is after that

st.session_state.setdefault("from_year", 2030)
st.session_state.setdefault("from_month", "January")
st.session_state.setdefault("to_year", 2035)
st.session_state.setdefault("to_month", "January")

with center:
    with st.container(border=True):
        st.markdown("**Jump to a range**")
        preset_cols = st.columns(len(PRESETS))
        for col, (label, (fy, fm, ty, tm)) in zip(preset_cols, PRESETS.items()):
            with col:
                if st.button(label, use_container_width=True):
                    st.session_state["from_year"] = fy
                    st.session_state["from_month"] = fm
                    st.session_state["to_year"] = ty
                    st.session_state["to_month"] = tm

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Predict from**")
            fc1, fc2, fc3, fc4 = st.columns([1.3, 0.5, 1, 0.5])
            with fc1:
                from_month = st.selectbox("Month", MONTH_NAMES, key="from_month",
                                          label_visibility="collapsed")
            from_year = year_stepper("from_year", MIN_YEAR, 2200, (fc2, fc3, fc4))
        with c2:
            st.markdown("**to**")
            tc1, tc2, tc3, tc4 = st.columns([1.3, 0.5, 1, 0.5])
            with tc1:
                to_month = st.selectbox("Month", MONTH_NAMES, key="to_month",
                                        label_visibility="collapsed")
            to_year = year_stepper("to_year", MIN_YEAR, 2200, (tc2, tc3, tc4))

        display_from = pd.Timestamp(year=st.session_state["from_year"],
                                    month=MONTH_NAMES.index(st.session_state["from_month"]) + 1, day=1)
        display_to = pd.Timestamp(year=st.session_state["to_year"],
                                  month=MONTH_NAMES.index(st.session_state["to_month"]) + 1, day=1)
        if display_to < display_from:
            display_from, display_to = display_to, display_from
        from_label = display_from.strftime("%B %Y")
        to_label = display_to.strftime("%B %Y")

        with st.expander("Advanced settings"):
            n_reps = st.slider("Synthetic replicates", 100, 1000, 400, 100,
                               help="More replicates = smoother uncertainty bands, slower to compute.")
            show_recent_history = st.checkbox(
                "Show recent observed history alongside the forecast", value=True,
                help="Only shown when the forecast window starts reasonably soon after "
                     "the data ends -- otherwise the chart would be mostly empty space.")

        go = st.button("Get the Outlook", type="primary")

    outputs = {}
    if go:
        full_horizon = (display_to.year - last_month.year) * 12 + (display_to.month - last_month.month)
        window_start = (display_from.year - last_month.year) * 12 + (display_from.month - last_month.month)
        with st.spinner(f"Running a thousand possible futures out to {to_label} for each variable..."):
            for v in ["discharge", "rainfall", "stage"]:
                df = full_df[v]
                model = fit_model(v)
                r = results["variables"][v]
                ens_full = simulate_ensemble(model, df["log_value"].to_numpy(),
                                             full_horizon, n_reps=n_reps, method="gaussian", seed=None)
                ens = ens_full[:, window_start:]  # only the requested [from, to] window
                fcst_dates = [display_from + pd.DateOffset(months=i) for i in range(ens.shape[1])]
                q_median = np.median(ens, axis=0)
                q_lo, q_hi = np.percentile(ens, [5, 95], axis=0)

                avg_val = float(np.mean(q_median))
                hist_mean = r["historical_stats"]["mean"]
                trend_word, trend_dir = classify_trend(q_median, float(q_median[0]))
                level_word, level_status = classify_level(avg_val, hist_mean)
                n_ok, n_tot = r["validation_n_within"], r["validation_n_total"]

                outputs[v] = dict(
                    df=df, fcst_dates=fcst_dates,
                    q_median=q_median, q_lo=q_lo, q_hi=q_hi,
                    avg_val=avg_val, hist_mean=hist_mean, trend_word=trend_word,
                    trend_dir=trend_dir, level_word=level_word, level_status=level_status,
                    n_ok=n_ok, n_tot=n_tot, r=r,
                )

    if outputs:
        st.markdown(f"#### The picture behind the outlook &mdash; {from_label} to {to_label}")
        gap_months = (display_from.year - last_month.year) * 12 + (display_from.month - last_month.month)
        show_hist = show_recent_history and gap_months <= 60
        tabs = st.tabs([VAR_LABEL[v] for v in ["discharge", "rainfall", "stage"]])
        for tab, v in zip(tabs, ["discharge", "rainfall", "stage"]):
            o = outputs[v]
            with tab:
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
                layers = [band, median_line]
                if show_hist:
                    hist = o["df"]["value"].loc[:last_month].iloc[-48:]
                    hist_df = pd.DataFrame({"date": hist.index, "value": hist.values})
                    hist_line = alt.Chart(hist_df).mark_line(color=NAVY, strokeWidth=1.8).encode(
                        x="date:T", y="value:Q",
                        tooltip=[alt.Tooltip("date:T", title="Month", format="%b %Y"),
                                alt.Tooltip("value:Q", title=f"Observed ({UNIT[v]})", format=".1f")],
                    )
                    layers.insert(0, hist_line)

                chart = alt.layer(*layers).properties(height=270).interactive()
                st.altair_chart(chart, use_container_width=True)

                legend_bits = []
                if show_hist:
                    legend_bits.append(f'<span style="color:{NAVY}">&#9644;</span> Observed history (up to Dec 2014)')
                legend_bits.append(f'<span style="color:{VAR_COLOR[v]}">&#9646;&#9646;</span> Uncertainty range (90%)')
                legend_bits.append(f'<span style="color:{VAR_COLOR[v]}">- - -</span> Expected path')
                st.caption(" &nbsp;&nbsp; ".join(legend_bits), unsafe_allow_html=True)

                st.markdown(f'<div class="narrative">{build_narrative(v, UNIT[v], from_label, to_label, o["avg_val"], o["hist_mean"], o["trend_word"], o["level_word"], o["n_ok"], o["n_tot"])}</div>',
                           unsafe_allow_html=True)

        with st.expander("For the curious: the statistics behind this outlook", expanded=False):
            st.markdown(
                "This is the part a supervisor or examiner actually wants to see: not just "
                "*which* model was picked, but *how its numbers were estimated*, *how precisely* "
                "they're known, and *what evidence* says this data fits an ARIMA model at all."
            )
            for v in ["discharge", "rainfall", "stage"]:
                o = outputs[v]
                r = o["r"]
                st.markdown(f"**{VAR_LABEL[v]}**")
                st.markdown(
                    f"Model: `ARIMA{tuple(r['order'])}`, AIC {r['aic']:.1f}, differencing d={r['differencing_d']}. "
                    f"Coefficients estimated on 1980-2003 (conditional sum of squares; exact ordinary "
                    f"least squares when there's no moving-average term), validated on 2004-2014."
                )

                se = r["standard_errors"]
                coef_rows = [{"Coefficient": "constant", "Estimate": round(r["constant"], 4),
                              "Standard error": round(se["c"], 4) if se["c"] is not None else "n/a"}]
                for i, ph in enumerate(r["phi"]):
                    s = se["phi"][i]
                    coef_rows.append({"Coefficient": f"AR (phi) {i+1}", "Estimate": round(ph, 4),
                                      "Standard error": round(s, 4) if s is not None else "n/a"})
                for i, th in enumerate(r["theta"]):
                    s = se["theta"][i]
                    coef_rows.append({"Coefficient": f"MA (theta) {i+1}", "Estimate": round(th, 4),
                                      "Standard error": round(s, 4) if s is not None else "n/a"})
                st.caption("Estimated coefficients — not just which order was picked, but the actual "
                          "numbers and how precisely each is known:")
                st.dataframe(pd.DataFrame(coef_rows), use_container_width=True, hide_index=True)

                stat = r["stationarity_report"][-1]
                st.caption(
                    f"Stationarity evidence for d={r['differencing_d']}: ADF stat {stat['adf_stat']:.3f} "
                    f"({'rejects a unit root' if stat['adf_stationary'] else 'does not reject a unit root'}), "
                    f"KPSS stat {stat['kpss_stat']:.3f} "
                    f"({'does not reject stationarity' if stat['kpss_stationary'] else 'rejects stationarity'}) "
                    f"— the joint evidence used to decide this series fits an ARIMA model at this "
                    f"differencing order, not an assumption."
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
            f"""<div class="controls" style="text-align:center;padding:3rem 1.5rem;">
            <p style="font-size:1.0rem;color:{GRAY};margin:0;">
            Pick a future range above, then press
            <strong style="color:{BLUE}">Get the Outlook</strong>.</p>
            </div>""",
            unsafe_allow_html=True,
        )

# ── RIGHT rail: compact outlook cards, one per variable ──────────────────────
with right:
    trend_arrow = {"up": "&#9650;", "down": "&#9660;", "steady": "&#8226;"}
    trend_color = {"up": BLUE, "down": AMBER, "steady": GRAY}
    level_pill_color = {"normal": GREEN, "attention": AMBER}

    if outputs:
        st.markdown(f"**Outlook summary**")
        st.caption("The colored score on each card is how many of 7 real-world "
                  "checks that variable's model passed against 11 years of "
                  "held-out data &mdash; the closest thing this model has to "
                  "an accuracy grade.", unsafe_allow_html=True)
        for v in ["discharge", "rainfall", "stage"]:
            o = outputs[v]
            record_word, record_color = track_record_word(o["n_ok"], o["n_tot"])
            st.markdown(
                f"""<div class="card" style="border-left:4px solid {VAR_COLOR[v]};
                     box-shadow:0 4px 20px {VAR_COLOR[v]}26;">
                <div class="card-head">{svg_icon(v, VAR_COLOR[v])}<p class="card-title">{VAR_LABEL[v]}</p>
                    <span class="pill" style="background:{record_color};color:white;margin-left:auto;">
                        {o['n_ok']}/{o['n_tot']} &nbsp;{record_word.split()[0]}</span>
                </div>
                <div class="big-stat">{o['avg_val']:.1f} <span style="font-size:0.85rem;font-weight:500;color:{GRAY}">{UNIT[v]}</span></div>
                <div>
                    <span class="pill" style="background:{trend_color[o['trend_dir']]}22;color:{trend_color[o['trend_dir']]}">
                        {trend_arrow[o['trend_dir']]} {o['trend_word'].split()[0].capitalize()}</span>
                    <span class="pill" style="background:{level_pill_color[o['level_status']]}22;color:{level_pill_color[o['level_status']]}">
                        {o['level_word'].capitalize()}</span>
                </div>
                </div>""",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(f"**Typical levels**")
        st.caption("Historical averages. The colored score on each card is how "
                  "many of 7 real-world checks that variable's model passed "
                  "against 11 years of held-out data &mdash; the closest thing "
                  "this model has to an accuracy grade.", unsafe_allow_html=True)
        for v in ["discharge", "rainfall", "stage"]:
            r = results["variables"][v]
            mean_val = r["historical_stats"]["mean"]
            n_ok, n_tot = r["validation_n_within"], r["validation_n_total"]
            record_word, record_color = track_record_word(n_ok, n_tot)
            st.markdown(
                f"""<div class="card" style="border-left:4px solid {VAR_COLOR[v]};
                     box-shadow:0 4px 20px {VAR_COLOR[v]}26;">
                <div class="card-head">{svg_icon(v, VAR_COLOR[v])}<p class="card-title">{VAR_LABEL[v]}</p>
                    <span class="pill" style="background:{record_color};color:white;margin-left:auto;">
                        {n_ok}/{n_tot} &nbsp;{record_word.split()[0]}</span>
                </div>
                <div class="big-stat">{mean_val:.1f} <span style="font-size:0.85rem;font-weight:500;color:{GRAY}">{UNIT[v]}</span></div>
                <div><span class="pill" style="background:{GRAY}22;color:{GRAY}">Long-term typical</span></div>
                </div>""",
                unsafe_allow_html=True,
            )
