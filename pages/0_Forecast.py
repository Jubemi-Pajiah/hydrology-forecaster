"""
0_Forecast.py — Streamlit synthetic-record generator.

Rebuilt 2026-08-19 (v4). The app previously asked for a future date range
("predict from X to Y") and displayed a band through it. That framing was
wrong twice over. It implied the model predicts named future months, which
it does not, and the date window was in any case statistically meaningless:
the fitted process is stationary, so every window of a given length is
identically distributed and slicing one out of the middle of a simulation
returns the same thing as taking it from the start.

What the model actually does is generate a synthetic monthly record of
whatever length is asked for, statistically consistent with the observed
record but far longer, so that the rare events a design must survive appear
often enough to be counted. The interface therefore asks for one number --
how many years -- and returns the record itself, month by month, with the
statistics a design calculation reads off it.

Re-running gives a different record every time. That is the point: a
stochastic model's individual realisations are not meant to be compared
value-for-value with what actually happened, only its statistical
properties are (see the Documentation page).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import altair as alt
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import json

from src.preprocess import build_monthly_dataset, deseasonalise
from src.model import ARIMA
from src.simulate import generate_synthetic_record

RESULTS_PATH = ROOT / "data" / "results.json"

st.set_page_config(page_title="River Outlook", page_icon=None, layout="wide")

# ── Palette ───────────────────────────────────────────────────────────────────
NAVY = "#1E293B"
BLUE = "#2563EB"
AMBER = "#F59E0B"
GREEN = "#16A34A"
RED = "#DC2626"
BG = "#F8FAFC"
BORDER = "#E2E8F0"
GRAY = "#64748B"

VARIABLE = "discharge"
UNIT = "m³/s"
VAR_LABEL = "River flow"
BASIN_SHORT = "Conecuh River"

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
RETURN_PERIODS = [2, 5, 10, 25, 50, 100, 500]


# ── Data and model ────────────────────────────────────────────────────────────
@st.cache_data
def load_results() -> dict:
    with open(RESULTS_PATH) as f:
        return json.load(f)


@st.cache_data
def load_monthly(variable: str):
    return build_monthly_dataset(variable)


@st.cache_resource
def fit_model(variable: str = VARIABLE):
    """Rebuild the model from the coefficients reported in the thesis.

    The app never re-estimates anything: it loads the coefficients from the
    same data/results.json that run_pipeline.py wrote, so what a user
    generates here comes from exactly the model the report describes.
    """
    r = load_results()["variables"][variable]
    fr = r["full_record"]
    df = load_monthly(variable)
    profile = fr["seasonal_profile"]
    z = deseasonalise(df["log_value"].to_numpy(), df.index.month.to_numpy(), profile)
    model = ARIMA.from_params(tuple(fr["order"]), fr["constant"],
                              fr["phi"], fr["theta"], z)
    return model, profile, fr


def return_period_table(record: np.ndarray, period: int = 12) -> pd.DataFrame:
    """Design value for each return period, from the pooled annual maxima."""
    n_years = record.shape[-1] // period
    annual_max = record[:, :n_years * period].reshape(
        record.shape[0], n_years, period).max(axis=2).ravel()
    rows = []
    for T in RETURN_PERIODS:
        if annual_max.size < T:           # not enough years to speak to this T
            continue
        rows.append({
            # Short headers on purpose: these three columns have to stay
            # readable side by side in a narrow pane, and the design flow is
            # the column that must never be the one that gets clipped.
            "Return period": f"{T} yr",
            "Chance/yr": f"{100.0 / T:.1f}%",
            f"Design flow ({UNIT})": float(
                np.percentile(annual_max, 100.0 * (1.0 - 1.0 / T))),
        })
    return pd.DataFrame(rows), annual_max


def track_record_word(n_ok, n_total):
    if n_ok >= 6:
        return "Strong track record", GREEN
    if n_ok >= 4:
        return "Reasonable track record", AMBER
    return "Weak track record", RED


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
    .amber-card {{ border-top-color: {AMBER}; }}
    .amber-card h4 {{ color: {AMBER}; }}

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
             padding: 0.95rem 1.05rem; margin-bottom: 0.9rem; }}
    .card-title {{ font-size: 0.92rem; font-weight: 700; color: {NAVY}; margin: 0 0 0.35rem 0; }}
    .big-stat {{ font-family: 'JetBrains Mono', monospace; font-weight: 600; font-size: 1.55rem;
                 color: {NAVY}; margin: 0.1rem 0; }}
    .stat-row {{ display: flex; justify-content: space-between; font-size: 0.86rem;
                 padding: 0.32rem 0; border-bottom: 1px dashed {BORDER}; }}
    .stat-row b {{ font-family: 'JetBrains Mono', monospace; color: {NAVY}; }}
    .pill {{ display: inline-block; font-size: 0.66rem; font-weight: 700; text-transform: uppercase;
             letter-spacing: 0.04em; padding: 0.18rem 0.5rem; border-radius: 99px; margin: 0.15rem 0.3rem 0 0; }}
    .narrative {{ font-size: 0.87rem; line-height: 1.6; color: #334155; margin-top: 0.7rem; }}

    [data-testid="stExpander"] {{ border: 1px solid {BORDER}; border-left: 3px solid {BLUE};
                                  border-radius: 12px; background: #FFFFFF; }}
    [data-baseweb="tab-highlight"] {{ background-color: {BLUE} !important; height: 3px !important; }}
    [data-baseweb="tab"][aria-selected="true"] {{ color: {BLUE} !important; font-weight: 700; }}
    </style>
    """,
    unsafe_allow_html=True,
)

results = load_results()
R = results["variables"][VARIABLE]
df_hist = load_monthly(VARIABLE)
hist_values = df_hist["value"].to_numpy()
n_hist_years = len(df_hist) // 12

st.title("River Outlook")
st.caption(f"Synthetic monthly discharge records for the {BASIN_SHORT} at Brantley, "
           f"Alabama (USGS 02371500) — generated from an ARIMA model fitted to "
           f"{df_hist.index[0]:%Y}–{df_hist.index[-1]:%Y}.")

left, center, right = st.columns([1, 2.35, 1.15], gap="medium")

# ── Left rail ─────────────────────────────────────────────────────────────────
with left:
    st.markdown(
        f"""
        <div class="rail-card">
          <h4>What this is</h4>
          <p>The river has been measured for <b>{n_hist_years} years</b>. That is a short
          sample, and the floods and droughts a dam or channel has to survive are
          rarer than it is long.</p>
          <p>This tool fits a statistical model to those {n_hist_years} years and uses
          it to write out a <b>much longer record</b> — as many years as you ask for —
          that behaves like the same river, but contains far more of the rare
          events.</p>
        </div>
        """, unsafe_allow_html=True)

    lb = R["diagnostics"]["ljung_box"]["pvalue"]
    st.markdown(
        f"""
        <div class="rail-card">
          <h4>Good to know</h4>
          <div class="rail-fact"><span>Measured record</span>
            <b>{df_hist.index[0]:%b %Y} – {df_hist.index[-1]:%b %Y}</b></div>
          <div class="rail-fact"><span>Years of history</span><b>{n_hist_years}</b></div>
          <div class="rail-fact"><span>Model</span><b>{R['label']}</b></div>
          <div class="rail-fact"><span>Seasonal cycle</span><b>12 monthly parameters</b></div>
          <div class="rail-fact"><span>Residual check</span><b>Ljung–Box p = {lb:.3f}</b></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="rail-card amber-card">
          <h4>How to read the output</h4>
          <p>The generated record is <b>not a forecast of particular months</b>. It is
          not dated, and no row of it says what will happen in a given future year.</p>
          <p>It is a <b>sample of the same river</b>, drawn out to whatever length you
          need, so that the size of a 1-in-100-year flow can be counted rather than
          guessed. Generate it twice and you get two different records — both equally
          valid samples.</p>
          <p>Estimates near the range of the measured record are the solid ones.
          The further past it you read, the more the answer depends on the shape of
          the model rather than on the river.</p>
        </div>
        """, unsafe_allow_html=True)
    st.page_link("pages/1_Documentation.py", label="How this works →")

# ── Centre: controls and results ──────────────────────────────────────────────
with center:
    with st.container(border=True):
        st.markdown("#### Generate a synthetic discharge record")

        st.session_state.setdefault("n_years", 100)
        p1, p2, p3, p4 = st.columns(4)
        for col, yrs in zip((p1, p2, p3, p4), (30, 100, 500, 1000)):
            with col:
                if st.button(f"{yrs:,} yr", use_container_width=True, key=f"preset{yrs}"):
                    st.session_state["n_years"] = yrs

        c1, c2 = st.columns([2, 1])
        with c1:
            n_years = st.number_input(
                "Number of years to generate",
                min_value=1, max_value=10000, step=10, key="n_years",
                help="Any value from 1 to 10,000. The presets above are shortcuts.")
        with c2:
            n_reps = st.number_input(
                "Independent records", min_value=1, max_value=100, value=20, step=1,
                help="How many separate records to generate. The table shows the "
                     "first; the statistics and return periods pool all of them.")

        st.caption(f"{n_years:,} years = {n_years * 12:,} monthly values per record, "
                   f"{n_years * n_reps:,} synthetic years in total.")
        go = st.button("Generate synthetic record", type="primary")

    if go:
        model, profile, fr = fit_model()
        with st.spinner(f"Generating {n_years:,} years…"):
            record, months = generate_synthetic_record(
                model, int(n_years), profile, n_reps=int(n_reps),
                method=fr.get("innovations", "bootstrap"), seed=None, start_month=1)
        st.session_state["record"] = record
        st.session_state["months"] = months
        st.session_state["gen_years"] = int(n_years)
        st.session_state["gen_reps"] = int(n_reps)

    record = st.session_state.get("record")

    if record is None:
        st.markdown(
            f"""
            <div class="card" style="text-align:center; padding:2.4rem 1rem;">
              <p class="card-title" style="font-size:1.05rem;">No record generated yet</p>
              <p style="color:{GRAY}; font-size:0.9rem;">Choose a number of years and press
              <strong style="color:{BLUE}">Generate synthetic record</strong>. The table of
              monthly values appears here.</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        gen_years = st.session_state["gen_years"]
        gen_reps = st.session_state["gen_reps"]
        months = st.session_state["months"]
        first = record[0]

        # ── The record itself. This is the deliverable. ───────────────────────
        st.markdown(f"#### The generated record — {gen_years:,} years, "
                    f"{len(first):,} monthly values")
        table = pd.DataFrame({
            "Year": np.repeat(np.arange(1, gen_years + 1), 12)[:len(first)],
            "Month": [MONTH_ABBR[m - 1] for m in months],
            f"Discharge ({UNIT})": np.round(first, 2),
        })
        st.dataframe(table, use_container_width=True, height=380, hide_index=True)
        st.download_button(
            f"Download this record as CSV ({len(first):,} rows)",
            data=table.to_csv(index=False).encode("utf-8"),
            file_name=f"synthetic_discharge_{gen_years}yr.csv",
            mime="text/csv")
        st.caption(
            "Years are numbered 1 to "
            f"{gen_years:,} rather than dated. The model is stationary, so the record "
            "has no particular position in time — it is a sample of the river's "
            "behaviour, not a calendar of future events.")

        st.markdown("---")

        # ── Design numbers ───────────────────────────────────────────────────
        rp_df, annual_max = return_period_table(record)
        st.markdown("#### What a design calculation reads off it")
        st.caption(
            f"The largest flow in each of the {annual_max.size:,} synthetic years was "
            "taken, and those annual maxima ranked. The flow for a 100-year return "
            "period is the value exceeded in 1 per cent of them.")

        rc1, rc2 = st.columns([1.1, 1])
        with rc1:
            st.dataframe(
                rp_df.style.format({f"Design flow ({UNIT})": "{:.1f}"}),
                use_container_width=True, hide_index=True,
                column_config={
                    f"Design flow ({UNIT})": st.column_config.NumberColumn(
                        f"Design flow ({UNIT})", format="%.1f", width="medium"),
                })
        with rc2:
            chart_df = rp_df.copy()
            chart_df["T"] = [int(str(x).split()[0]) for x in chart_df["Return period"]]
            rp_chart = alt.Chart(chart_df).mark_line(
                point=alt.OverlayMarkDef(size=60, filled=True), color=BLUE
            ).encode(
                x=alt.X("T:Q", scale=alt.Scale(type="log"),
                        title="Return period (years, log scale)"),
                y=alt.Y(f"Design flow ({UNIT}):Q", title=f"Design flow ({UNIT})"),
                tooltip=[alt.Tooltip("T:Q", title="Return period (yr)"),
                         alt.Tooltip(f"Design flow ({UNIT}):Q", format=".1f")],
            ).properties(height=250)
            obs_rule = alt.Chart(pd.DataFrame({"y": [hist_values.max()]})).mark_rule(
                color=AMBER, strokeDash=[5, 4]).encode(y="y:Q")
            st.altair_chart(rp_chart + obs_rule, use_container_width=True)
            st.caption(
                f"Dashed line: the largest month actually measured "
                f"({hist_values.max():.0f} {UNIT}) in {n_hist_years} years of record.")

        # ── Distribution ─────────────────────────────────────────────────────
        st.markdown("#### How the generated record compares with the measured one")
        sample = record.ravel()
        if sample.size > 60000:                     # keep the chart responsive
            sample = np.random.default_rng(0).choice(sample, 60000, replace=False)

        d1, d2 = st.columns(2)
        with d1:
            comp = pd.concat([
                pd.DataFrame({"value": hist_values, "Record": "Measured"}),
                pd.DataFrame({"value": sample, "Record": "Synthetic"}),
            ])
            hist_chart = alt.Chart(comp).transform_filter(
                alt.datum.value < float(np.percentile(sample, 99.5))
            ).mark_area(opacity=0.45, interpolate="step").encode(
                x=alt.X("value:Q", bin=alt.Bin(maxbins=45),
                        title=f"Monthly discharge ({UNIT})"),
                y=alt.Y("count()", stack=None, title="Frequency"),
                color=alt.Color("Record:N",
                                scale=alt.Scale(domain=["Measured", "Synthetic"],
                                                range=[NAVY, BLUE])),
            ).properties(height=250)
            st.altair_chart(hist_chart, use_container_width=True)
            st.caption("Distribution of monthly values, upper 0.5% trimmed so the "
                       "bulk of both records is legible.")
        with d2:
            probs = np.linspace(0.1, 99.9, 220)
            fdc = pd.concat([
                pd.DataFrame({"Exceeded (%)": 100 - probs,
                              "value": np.percentile(hist_values, probs),
                              "Record": "Measured"}),
                pd.DataFrame({"Exceeded (%)": 100 - probs,
                              "value": np.percentile(sample, probs),
                              "Record": "Synthetic"}),
            ])
            fdc_chart = alt.Chart(fdc).mark_line(strokeWidth=2).encode(
                x=alt.X("Exceeded (%):Q", title="Percentage of months exceeding"),
                y=alt.Y("value:Q", scale=alt.Scale(type="log"),
                        title=f"Monthly discharge ({UNIT}, log scale)"),
                color=alt.Color("Record:N",
                                scale=alt.Scale(domain=["Measured", "Synthetic"],
                                                range=[NAVY, BLUE])),
                tooltip=["Record:N", "Exceeded (%):Q", "value:Q"],
            ).properties(height=250)
            st.altair_chart(fdc_chart, use_container_width=True)
            st.caption("Flow-duration curve. The two lines lying together means the "
                       "synthetic record reproduces the measured one across its range.")

        # ── Narrative ────────────────────────────────────────────────────────
        n_ok, n_tot = R["validation_n_within"], R["validation_n_total"]
        word, colour = track_record_word(n_ok, n_tot)
        rp100 = rp_df.loc[rp_df["Return period"] == "100 yr", f"Design flow ({UNIT})"]
        rp100_txt = (f"a 100-year flow of about <strong>{rp100.iloc[0]:.0f} {UNIT}</strong>"
                     if not rp100.empty else
                     "too few synthetic years to estimate a 100-year flow")
        st.markdown(
            f"""
            <div class="narrative">
            This record covers <strong>{gen_years:,} years</strong> of monthly flow
            ({gen_reps} independent records, {annual_max.size:,} synthetic years in
            total). It averages <strong>{record.mean():.1f} {UNIT}</strong> against
            <strong>{hist_values.mean():.1f} {UNIT}</strong> in the measured record,
            and gives {rp100_txt}. Tested against {n_hist_years - 24} years of data
            held back from fitting, this model reproduced <strong>{n_ok} of {n_tot}</strong>
            statistical properties of the real record.
            </div>
            """, unsafe_allow_html=True)

        # ── For the curious ──────────────────────────────────────────────────
        with st.expander("For the curious: the statistics behind this record"):
            model, profile, fr = fit_model()
            st.markdown(
                f"**Model.** `{R['label']}` fitted to the deseasonalised "
                f"log-transformed series, AIC {R['aic']:.1f}. Estimated on "
                f"{R['train_period'][0][:4]}–{R['train_period'][1][:4]} and validated "
                f"on {R['valid_period'][0][:4]}–{R['valid_period'][1][:4]}; the "
                "record generator above uses coefficients refitted on the full record.")

            se = R["standard_errors"]
            rows = [{"Coefficient": "constant", "Estimate": R["constant"],
                     "Standard error": se["c"]}]
            for i, ph in enumerate(R["phi"]):
                rows.append({"Coefficient": f"AR (phi) {i+1}", "Estimate": ph,
                             "Standard error": se["phi"][i]})
            for i, th in enumerate(R["theta"]):
                rows.append({"Coefficient": f"MA (theta) {i+1}", "Estimate": th,
                             "Standard error": se["theta"][i]})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            st.markdown("**The seasonal component — twelve monthly parameters.**")
            st.caption(
                "The annual cycle is removed before fitting by expressing each month "
                "as a departure from its own calendar month's average, and restored "
                "when the record is generated. This is what makes the model "
                "stationary, and therefore what makes a record of any length "
                "meaningful.")
            st.dataframe(pd.DataFrame({
                "Month": MONTH_ABBR,
                "Mean (log scale)": np.round(profile["means"], 3),
                "Std. dev. (log scale)": np.round(profile["sds"], 3),
                f"Typical flow ({UNIT})": np.round(np.exp(profile["means"]), 1),
            }), use_container_width=True, hide_index=True)

            alt_info = R.get("seasonal_difference_alternative", {})
            if alt_info.get("applicable"):
                st.markdown("**Why the cycle is not removed by differencing at lag 12.**")
                st.caption(
                    f"Differencing at lag 12 was tested and fits the measured record "
                    f"well (Ljung–Box p = {alt_info['ljung_box_pvalue']:.3f}). It "
                    "cannot be used to generate a long record, because it leaves an "
                    "integrated process whose spread grows without limit. Asked for "
                    f"{alt_info['record_years']:,} years it returns a series averaging "
                    f"{alt_info['record_mean']:.2g} {UNIT} — against a measured "
                    f"average of {hist_values.mean():.1f} — drifting by a factor of "
                    f"{alt_info['drift_ratio']:.2g} from its first decade to its last. "
                    "Removing the cycle by seasonal standardisation instead keeps the "
                    "process stationary. This is discussed in Section 4.2 of the report.")

            rep = R["stationarity_report"][-1]
            st.caption(
                f"Stationarity of the deseasonalised series — ADF statistic "
                f"{rep['adf_stat']:.3f} "
                f"({'rejects' if rep['adf_stationary'] else 'does not reject'} a unit "
                f"root); KPSS statistic {rep['kpss_stat']:.3f} "
                f"({'does not reject' if rep['kpss_stationary'] else 'rejects'} "
                f"stationarity). Both point to d = 0, so no differencing is applied.")

            st.markdown("**Property-based validation** (2004–2014, held out of fitting)")
            st.dataframe(pd.DataFrame([{
                "Property": k.replace("_", " "),
                "Historical": round(v["historical"], 3),
                "Model's range (90%)": f"[{v['ensemble_p5']:.2f}, {v['ensemble_p95']:.2f}]",
                "Reproduced?": "yes" if v["within_90pct_envelope"] else "no",
            } for k, v in R["validation"].items()]),
                use_container_width=True, hide_index=True)
            st.caption(
                "The property not reproduced is the seasonal amplitude: the annual "
                "cycle at this gauge weakened over the record (amplitude 35.2 m³/s in "
                "1980–89 and 43.5 in 1990–99, against 25.8 in 2004–14), so a model "
                "whose seasonal parameters come from the earlier period cannot match "
                "the later one. That is a finding about the river, not a fault in the "
                "fit — see Section 4.6 of the report.")

# ── Right rail: the extremes ──────────────────────────────────────────────────
with right:
    record = st.session_state.get("record")
    if record is None:
        st.markdown(
            f"""
            <div class="card">
              <p class="card-title">The measured record</p>
              <div class="big-stat">{hist_values.mean():.1f} {UNIT}</div>
              <span class="pill" style="background:#F1F5F9; color:{GRAY};">Long-term average</span>
              <div class="stat-row"><span>Highest month</span><b>{hist_values.max():.1f}</b></div>
              <div class="stat-row"><span>Lowest month</span><b>{hist_values.min():.2f}</b></div>
              <div class="stat-row"><span>Years of record</span><b>{n_hist_years}</b></div>
            </div>
            """, unsafe_allow_html=True)
        st.caption("Generate a record to see the same statistics for it.")
    else:
        gen_years = st.session_state["gen_years"]
        gen_reps = st.session_state["gen_reps"]
        n_ok, n_tot = R["validation_n_within"], R["validation_n_total"]
        word, colour = track_record_word(n_ok, n_tot)
        st.markdown(
            f"""
            <div class="card">
              <p class="card-title">Generated record — extremes</p>
              <span class="pill" style="background:{colour}1A; color:{colour};">
                {n_ok}/{n_tot} {word.split()[0]}</span>
              <div class="big-stat">{record.mean():.1f} {UNIT}</div>
              <span class="pill" style="background:#F1F5F9; color:{GRAY};">Average month</span>
              <div class="stat-row"><span>Highest month</span><b>{record.max():.1f}</b></div>
              <div class="stat-row"><span>99th percentile</span><b>{np.percentile(record, 99):.1f}</b></div>
              <div class="stat-row"><span>95th percentile</span><b>{np.percentile(record, 95):.1f}</b></div>
              <div class="stat-row"><span>Lowest month</span><b>{record.min():.2f}</b></div>
              <div class="stat-row"><span>Std. deviation</span><b>{record.std(ddof=1):.1f}</b></div>
              <div class="stat-row"><span>Synthetic years</span><b>{gen_years * gen_reps:,}</b></div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="card">
              <p class="card-title">The measured record</p>
              <div class="stat-row"><span>Average month</span><b>{hist_values.mean():.1f}</b></div>
              <div class="stat-row"><span>Highest month</span><b>{hist_values.max():.1f}</b></div>
              <div class="stat-row"><span>Lowest month</span><b>{hist_values.min():.2f}</b></div>
              <div class="stat-row"><span>Std. deviation</span><b>{hist_values.std(ddof=1):.1f}</b></div>
              <div class="stat-row"><span>Years</span><b>{n_hist_years}</b></div>
            </div>
            """, unsafe_allow_html=True)
        st.caption(
            "The single highest month of a long synthetic record should not be used "
            "as a design figure: it is the most extreme of "
            f"{gen_years * gen_reps:,} simulated years, and the model has no upper "
            "bound. Use the return periods instead.")
