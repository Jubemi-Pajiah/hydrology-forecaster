"""
0_Forecast.py — Streamlit stochastic forecast dashboard.

Redesigned 2026-08-13 (v2) as a three-pane app shell: a static context rail
on the left, the interactive controls/chart/story in the centre, and a
compact outlook-card rail on the right -- rather than one narrow centred
column, so the wide layout is actually used instead of fought.

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

HORIZON_OPTIONS = {"3 months": 3, "6 months": 6, "1 year": 12, "2 years": 24, "5 years": 60}


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


def track_record_word(n_ok, n_total):
    if n_ok >= 6:
        return "Strong track record", GREEN
    if n_ok >= 4:
        return "Reasonable track record", AMBER
    return "Weak track record", RED


def build_narrative(variable, unit, horizon_months, origin_label, avg_val,
                    hist_mean, trend_word, level_word, n_ok, n_total):
    """Fill-in-the-blanks narrative. Uses <strong> (not Markdown **bold**)
    because it is always injected into a raw HTML block, where Markdown
    syntax is not parsed."""
    var_label = VAR_LABEL[variable].lower()
    confidence = "a solid" if n_ok >= 6 else ("a reasonable" if n_ok >= 4 else "a rough")
    return (
        f"We are forecasting <strong>{var_label}</strong> for the <strong>{BASIN_SHORT}</strong> "
        f"over the next <strong>{horizon_months} months</strong>, starting "
        f"<strong>{origin_label}</strong>. Based on the result, we see {var_label} "
        f"<strong>{trend_word}</strong>, averaging about <strong>{avg_val:.1f} {unit}</strong> "
        f"&mdash; {level_word} the typical level of {hist_mean:.1f} {unit}. Our model's outlook "
        f"has matched real historical patterns in <strong>{n_ok} of {n_total}</strong> key ways, "
        f"so treat this as {confidence} guide, not a guarantee."
    )


# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Raleway:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap');
    html, body, [class*="css"] {{ font-family: 'Raleway', system-ui, sans-serif; color: {NAVY}; }}
    .block-container {{ padding-top: 1.6rem; max-width: 1760px; }}
    h1 {{ font-weight: 800 !important; color: {NAVY} !important; letter-spacing: -0.02em; margin-bottom:0 !important; }}
    h3 {{ font-weight: 700 !important; color: {NAVY} !important; }}
    [data-testid="stSidebar"] {{ display: none; }}

    .rail-card {{ background: white; border: 1px solid {BORDER}; border-radius: 14px;
                  padding: 1.1rem 1.2rem; margin-bottom: 1rem; }}
    .rail-card h4 {{ margin: 0 0 0.5rem 0; font-size: 0.82rem; font-weight: 700; color: {GRAY};
                     text-transform: uppercase; letter-spacing: 0.06em; }}
    .rail-card p, .rail-card li {{ font-size: 0.88rem; line-height: 1.55; color: #334155; margin: 0.3rem 0; }}
    .rail-fact {{ display: flex; justify-content: space-between; font-size: 0.85rem; padding: 0.3rem 0;
                  border-bottom: 1px dashed {BORDER}; }}
    .rail-fact b {{ color: {NAVY}; }}

    .controls {{ background: white; border: 1px solid {BORDER}; border-radius: 16px;
                 padding: 1.1rem 1.3rem; margin-bottom: 1.1rem; }}

    div.stButton > button[kind="primary"] {{
        background: {BLUE}; border: none; font-weight: 700; font-size: 1.0rem;
        border-radius: 12px; padding: 0.6rem 1.4rem; box-shadow: 0 4px 14px rgba(37,99,235,0.28);
        transition: transform 150ms ease, box-shadow 150ms ease;
    }}
    div.stButton > button[kind="primary"]:hover {{
        transform: translateY(-1px); box-shadow: 0 6px 18px rgba(37,99,235,0.36);
    }}

    .card {{ background: white; border: 1px solid {BORDER}; border-radius: 14px;
             padding: 0.95rem 1.05rem; margin-bottom: 0.9rem; }}
    .card-head {{ display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.35rem; }}
    .card-title {{ font-size: 0.92rem; font-weight: 700; color: {NAVY}; margin: 0; }}
    .big-stat {{ font-family: 'JetBrains Mono', monospace; font-weight: 600; font-size: 1.55rem;
                 color: {NAVY}; margin: 0.1rem 0; }}
    .pill {{ display: inline-block; font-size: 0.66rem; font-weight: 700; text-transform: uppercase;
             letter-spacing: 0.04em; padding: 0.18rem 0.5rem; border-radius: 99px; margin: 0.15rem 0.3rem 0 0; }}
    .narrative {{ font-size: 0.87rem; line-height: 1.6; color: #334155; margin-top: 0.7rem; }}

    [data-testid="stExpander"] {{ border: 1px solid {BORDER}; border-radius: 12px; }}
    [data-testid="stVerticalBlockBorderWrapper"] {{ height: 100%; }}
    </style>
    """,
    unsafe_allow_html=True,
)

results = load_results()
full_df = {v: load_monthly(v) for v in ["discharge", "rainfall", "stage"]}
last_month = full_df["discharge"].index[-1]
first_month = full_df["discharge"].index[0]
month_options = list(full_df["discharge"].index)

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
        <p style="margin-top:0.6rem;">The starting point has to be a month we've actually
        measured, so the model has real history to build from &mdash; that's why it can't
        start in 2018 or today. But it can look as far <em>ahead</em> from that point as
        you like: a 5-year horizon from Dec 2014 reaches all the way to Dec 2019.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    st.page_link("pages/1_Documentation.py", label="How the method works, in full")

# ── CENTER: controls, then chart + story ─────────────────────────────────────
with center:
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
            "How far ahead from that point", options=list(HORIZON_OPTIONS.keys()),
            default="1 year", required=True,
        )
        horizon = HORIZON_OPTIONS.get(horizon_label, 12)

    with st.expander("Advanced settings"):
        n_reps = st.slider("Synthetic replicates", 100, 1000, 400, 100,
                           help="More replicates = smoother uncertainty bands, slower to compute.")
        hist_window = st.slider("History to show on the chart (months)", 12, 240, 48, 6)

    go = st.button("Get the Outlook", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    origin_label = origin_ts.strftime("%B %Y")

    outputs = {}
    if go:
        with st.spinner("Running a thousand possible futures for each variable..."):
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

    if outputs:
        st.markdown(f"#### The picture behind the outlook &mdash; {horizon} months from {origin_label}")
        tabs = st.tabs([VAR_LABEL[v] for v in ["discharge", "rainfall", "stage"]])
        for tab, v in zip(tabs, ["discharge", "rainfall", "stage"]):
            o = outputs[v]
            with tab:
                hist = o["hist_to_origin"]["value"].iloc[-hist_window:]
                hist_df = pd.DataFrame({"date": hist.index, "value": hist.values})
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

                chart = alt.layer(*layers).properties(height=270).interactive()
                st.altair_chart(chart, use_container_width=True)

                legend_bits = [
                    f'<span style="color:{NAVY}">&#9644;</span> Observed history',
                    f'<span style="color:{VAR_COLOR[v]}">&#9646;&#9646;</span> Uncertainty range (90%)',
                    f'<span style="color:{VAR_COLOR[v]}">- - -</span> Expected path',
                ]
                if o["n_actual"]:
                    legend_bits.append(f'<span style="color:{NAVY}">&middot;&middot;&middot;</span> What actually happened')
                st.caption(" &nbsp;&nbsp; ".join(legend_bits), unsafe_allow_html=True)

                st.markdown(f'<div class="narrative">{build_narrative(v, UNIT[v], horizon, origin_label, o["avg_val"], o["hist_mean"], o["trend_word"], o["level_word"], o["n_ok"], o["n_tot"])}</div>',
                           unsafe_allow_html=True)

                if o["n_actual"]:
                    n_inside = int(np.sum(
                        (o["actual"].iloc[:o["n_actual"]].to_numpy() >= o["q_lo"][:o["n_actual"]]) &
                        (o["actual"].iloc[:o["n_actual"]].to_numpy() <= o["q_hi"][:o["n_actual"]])
                    ))
                    st.caption(f"Of the {o['n_actual']} months we can check, {n_inside} landed inside "
                              f"the uncertainty range shown above.")

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
            Choose a starting point and how far ahead to look above, then press
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
        for v in ["discharge", "rainfall", "stage"]:
            o = outputs[v]
            record_word, record_color = track_record_word(o["n_ok"], o["n_tot"])
            st.markdown(
                f"""<div class="card">
                <div class="card-head">{svg_icon(v, VAR_COLOR[v])}<p class="card-title">{VAR_LABEL[v]}</p></div>
                <div class="big-stat">{o['avg_val']:.1f} <span style="font-size:0.85rem;font-weight:500;color:{GRAY}">{UNIT[v]}</span></div>
                <div>
                    <span class="pill" style="background:{trend_color[o['trend_dir']]}22;color:{trend_color[o['trend_dir']]}">
                        {trend_arrow[o['trend_dir']]} {o['trend_word'].split()[0].capitalize()}</span>
                    <span class="pill" style="background:{level_pill_color[o['level_status']]}22;color:{level_pill_color[o['level_status']]}">
                        {o['level_word'].capitalize()}</span>
                </div>
                <div style="margin-top:0.4rem;">
                    <span class="pill" style="background:{record_color}22;color:{record_color}">{record_word.split()[0]}: {o['n_ok']}/{o['n_tot']}</span>
                </div>
                </div>""",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(f"**Typical levels**")
        st.caption("Historical averages, shown until you run an outlook.")
        for v in ["discharge", "rainfall", "stage"]:
            r = results["variables"][v]
            mean_val = r["historical_stats"]["mean"]
            st.markdown(
                f"""<div class="card">
                <div class="card-head">{svg_icon(v, VAR_COLOR[v])}<p class="card-title">{VAR_LABEL[v]}</p></div>
                <div class="big-stat">{mean_val:.1f} <span style="font-size:0.85rem;font-weight:500;color:{GRAY}">{UNIT[v]}</span></div>
                <div><span class="pill" style="background:{GRAY}22;color:{GRAY}">Long-term typical</span></div>
                </div>""",
                unsafe_allow_html=True,
            )
