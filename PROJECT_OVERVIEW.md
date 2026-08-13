# Project Overview — Computer Hydrological Forecasting

A plain-English rundown of what this project is and how it fits together, as of
2026-08-13 — after the pivot to a monthly, three-variable, stochastically-validated
framework, and the app/overview rewrite that followed it.

---

## 🌊 What this project is

This is a **B.Sc. Civil & Environmental Engineering final-year project** — *"Computer
Hydrological Forecasting"*.

- **Author:** Ugbodaga Benedict Osikpemi (Matric 190402003)
- **Institution:** University of Lagos
- **Supervisor:** Prof. K. O. Aiyesimoju
- **Submission:** February 2026

In simple terms: it's **three computer programs, each learning one river variable's own
habits** — discharge, rainfall, and stage — from decades of monthly history, and using
that to generate plausible future sequences. No variable is used to predict another,
and no weather forecast is consumed. The approach is purely **statistical**, and it is
deliberately **stochastic**: it does not claim to predict the one true future, only the
*range* of futures the river could plausibly produce, which is what actually matters for
sizing a reservoir or a spillway.

---

## 🔁 What changed on 2026-08-12 (read this first)

Two pivots happened in the same day, on supervisor instruction, and they're worth
understanding before anything else below:

1. **A real data error was found and fixed.** Every earlier version of this project
   (and its committed history) referred to USGS gauge `02361000` as "the Conecuh
   River." It isn't — NWIS confirms that gauge is the **Choctawhatchee River near
   Newton, AL**, a different river. A search for the actual Conecuh gauge turned up
   **USGS 02371500, "Conecuh River at Brantley, AL"** — a real CAMELS basin with a
   *longer, cleaner* record than the one mistakenly used before (discharge back to
   1937, not 1980; stage back to 1973; still actively updating). All data was re-pulled
   under the correct gauge, and every reference to the old gauge number in the live
   code was corrected.
2. **The whole modelling approach pivoted**, per the supervisor's direct feedback
   (a defence-style meeting): **monthly** instead of daily timestep (differencing only
   does real work — removing seasonality — at a monthly step, not a daily one); **three
   independent variables** (discharge, rainfall, stage) instead of discharge alone, to
   demonstrate the same ARIMA machinery generalises across variable types; and
   **stochastic, property-based validation** instead of comparing one forecast to the
   one thing that actually happened, since a stochastic model's individual runs aren't
   meant to match a specific observed sequence — only its statistical *properties*
   (mean, variability, seasonality, drought duration, peak size) should.

Everything below describes the project **after** both of these changes.

---

## 🔍 What was added on 2026-08-13 (two rounds of critical review)

After the pivot above, the thesis text was put through **two independent rounds of
critical review** (three simulated professor-reviewer agents each round, asked to
challenge "why", "how", and "where did this come from" across the whole document, not
just skim it). Real, checkable problems came out of both rounds, and each was either
fixed directly or deliberately deferred and disclosed — not silently dropped:

**Fixed directly** — a Table 8 arithmetic error (text said 13/21 property checks passed;
the data said 20/21); a missing "Table 1" caused by an earlier deletion, which had
silently shifted every later table number by one; an ARCH-test paragraph that had
rainfall and stage's borderline p-values backwards; a Jarque–Bera paragraph that claimed
normality was rejected for "every variable" when the data show only rainfall's residuals
actually fail that test.

**Resolved with new work, not just edited text** — three specific methodological gaps
were raised twice, independently, by different reviewer angles, and each got a real
supplementary analysis rather than a rewording:

- *"Reservoir/spillway sizing is the motivating application but never once demonstrated
  with an actual calculation."* → A worked design-discharge example now exists: 500
  synthetic 30-year discharge traces, pooled annual maxima, empirical return-period
  discharges read off the pooled distribution (the plotting-position method, Chow,
  Maidment & Mays 2008) — e.g. a 100-year design discharge of ~376 m³/s, versus a 35-year
  observed peak of ~110 m³/s. → *Report §4.6, Table 8; `design_discharge_example.py`.*
- *"The framework 'transfers to any basin... demonstrated here directly' — but only one
  basin was ever tested."* → The identical identification-and-estimation procedure was
  run, unmodified, on two more CAMELS basins from different climate regimes (Great Basin,
  arid; New England, humid continental/snow-influenced). The honest result: the
  *procedure* runs cleanly everywhere, but the *specific findings* don't transfer —
  discharge shows AR(1) persistence at all three basins but fails its residual test at
  all three, and rainfall's persistence genuinely differs by basin (near-zero at Conecuh,
  strong at New England). Two of the four new fits also showed real numerical warning
  signs (boundary-pinned coefficients, near-zero standard errors) — evidence the
  pipeline's own diagnostics work, not evidence to be swept under the rug. → *Report
  §4.8, Table 9, Figure 9; `cross_basin_check.py`, `cross_basin_figure.py`.*
- *"Discharge and stage are hydraulically linked (stage is discharge through a rating
  curve) — that weakens the 'three independent variable types' claim."* → The report now
  states this caveat directly next to the independence claim instead of leaving it
  implicit. → *Report §3.2.*

**Deliberately declined, not fixed** — the same review rounds asked, point-blank,
whether to (1) make the persistence skill score the headline metric, (2) reintroduce an
explicit Duan/log-normal bias-correction step, and (3) claim the method "transfers to any
basin... demonstrated here directly" without qualification. All three were **declined**:
the first two would have reintroduced exactly the point-forecast machinery the
2026-08-12 pivot deliberately moved away from (the stochastic ensemble already handles
log-normal bias by Monte Carlo integration, and property-based validation is the correct
standard for a stochastic model, not a repackaged point-forecast score); the third would
have been an overclaim the one-basin study didn't support — which is exactly what the
new §4.8 supplementary check above replaces it with, honestly.

**App and screenshots refreshed to match.** The Streamlit app's forecast controls were
rebuilt around explicit "predict from [month/year] to [month/year]" fields with range
presets, replacing an earlier "horizon from today" framing that couldn't express an
arbitrary future window; a rendering bug that left the controls panel an empty bordered
box was fixed; and a colour/shadow pass was applied for a more finished look. The two
app screenshots in Chapter 3 (Figures 3 and 4) were retaken from the current app to match.

---

## ❓ Questions to expect, and where the answer lives

Every question below is one the supervisor has actually asked, in the defence session
that drove this rewrite. Full detail (with page/section numbers) is in the PDF; this is
the fast-reference version.

**On the choice of model**

- **"Why ARIMA, not AR alone, MA alone, ARMA, or ARIMAX?"** AR alone assumes only past
  values matter; MA alone assumes only past shocks matter; ARMA combines both but needs
  stationary data; ARIMA adds differencing for non-stationary data; ARIMAX adds an
  outside variable. Order selection tests AR-only, MA-only, and mixed forms for every
  variable and keeps whichever fits best by AIC — the data picks, not us. ARIMAX was
  ruled out on purpose: each variable is forecast from its own past only, so there's no
  outside variable to add. → *Report Ch.2 §2.4; app "For the curious" shows each
  variable's actual (p,d,q).*
- **"Shouldn't the model work on rainfall too, not just discharge?"** It does — same
  code, unmodified, independently fits discharge, rainfall, and stage. → *App: switch
  tabs between the three variables. Report Ch.2 §2.4, Ch.3 §3.2.*

**On daily vs. monthly**

- **"Why daily data with ARIMA?"** We're not using daily anymore. Differencing only
  does real work — removing seasonal drift — at a monthly timestep. → *App left rail;
  Report Ch.1 §1.5, Ch.3 §3.1.*

**On parameter estimation (asked the most, and the most pointed)**

- **"How do you estimate the parameters? p,d,q aren't the parameters."** Correct — p,d,q
  are the *order* (structure), chosen by AIC. The actual parameters are the phi (AR) and
  theta (MA) coefficients, estimated by conditional sum of squares, each with a standard
  error. → *App "For the curious" → coefficient table per variable. Report Ch.3 §3.5,
  Ch.4 §4.4 (Table 6, Fig.6).*
- **"You must show the data fits ARIMA, not assume it."** Each variable runs through
  ADF and KPSS stationarity tests before a model is picked, and the result is shown, not
  just the conclusion. → *App "For the curious" → stationarity evidence line. Report
  Ch.3 §3.5, Ch.4 §4.2.*

**On whether it can even forecast**

- **"Can it forecast? Why only 7 days?"** That cap is gone — leftover default, not a
  real limit. Horizon now goes up to 5 years. → *App "How far ahead" control.*

**On checking correctness**

- **"Your data stops at 2014 — how do you know 2015 is correct? How do you check?"**
  You can't check one stochastic forecast against one real sequence — each run differs.
  What's checkable is whether history's *properties* (mean, variability, seasonality,
  drought length, peak size) fall inside the range 1,000 simulated versions produce.
  → *App: the shaded band + "track record" score on every card. Report Ch.3 §3.6, Ch.4
  §4.6.*
- **"Stochastic forecasts — you can only compare properties, not the forecast itself."**
  Yes, exactly — that's the whole 2026-08-12 rebuild in one sentence.
- **"Is 34 years 'not enough', or daily data 'too much'?"** Neither is the point —
  forecasting exists because the future is never in hand, regardless of how much history
  you have. → *Report Ch.2 (Matalas 1967, stochastic hydrology).*

**On the study basin**

- **"Why a US river? That's a standard panel question."** We looked into Nigeria
  seriously — see below for the specific numbers. Short version: neither Nigerian
  custodian could give a firm price or delivery date inside the project timeline, so the
  pipeline was built on the Conecuh record, already in hand and verified. The Nigerian
  request stayed open as a possible future swap — this is a disclosed trade-off, not a
  hidden one. → *Report Ch.1 §1.5.*

### Why Conecuh, specifically — the Nigerian data attempt

Two real custodians hold Nigerian river data, and both were checked, not skipped:

- **NIHSA (Nigeria Hydrological Services Agency)** — the federal agency under the
  Ministry of Water Resources, running 273 gauging stations nationwide, holding stage,
  discharge, sediment and water-quality records. Has a real online request form
  (`nihsa.gov.ng/data-request`) stating **5–7 working days** turnaround for
  straightforward requests. But **it publishes no fee schedule** — cost is assessed per
  request and only communicated *after* NIHSA reviews it, so there was no way to know in
  advance whether a request would be free, discounted, or a real cost, or the true
  delivery date once that review step is added on.
- **OORBDA (Ogun-Osun River Basin Development Authority)** — the authority that actually
  operates the gauging stations on the Ogun and Yewa rivers, the right rivers for a
  Lagos-relevant study. Access is by formal letter on departmental letterhead, with no
  published turnaround at all.

Given the project deadline, the methodology couldn't be built around data with an
unknown price *and* an unknown delivery date. The Conecuh record was already downloaded,
verified against USGS NWIS, and clean across all three variables, so it became the
working basin while the Nigerian request stayed open. A Beninese fallback (AMMA-CATCH —
free, no request needed) was also scoped; see `DATA_OPTIONS.md` for the full breakdown.

**On generalisation and design use (added after the 2026-08-13 review rounds)**

- **"Does this actually transfer to other basins, or just this one?"** The identical
  procedure was run, unmodified, on two more CAMELS basins in different climate regimes.
  It runs cleanly everywhere; the *specific* findings (which order fits, whether
  residuals pass) don't automatically carry over — reported honestly, not oversold. →
  *Report §4.8, Table 9, Figure 9.*
- **"You keep saying this is for reservoir/spillway design — show me a number."** A
  worked example now exists: pooled synthetic annual maxima across 500 thirty-year
  traces give return-period design discharges by the standard plotting-position method
  (100-year ≈ 376 m³/s). → *Report §4.6, Table 8.*
- **"Discharge and stage aren't really independent, are they?"** Correct, and now stated
  directly — they're linked by the site's rating curve, which is a real limitation on
  the "three independent variable types" framing, not something to gloss over. → *Report
  §3.2.*

---

## 🧠 How it works (the science, simply)

Each of the three variables — discharge, rainfall, stage — gets its own **independent
ARIMA (Box–Jenkins) model**, fitted the same way:

1. **Stationarity tests** (ADF + KPSS) decide how much to *difference* the series → `d`.
   For this basin, at the monthly timestep, all three variables came back `d = 0` — the
   data itself said no differencing was needed, which the pipeline reports honestly
   rather than forcing.
2. **ACF / PACF** plots suggest the autoregressive (`p`) and moving-average (`q`) orders.
3. **All combinations** over a grid of p and q values are fitted and ranked by **AIC**
   (Akaike Information Criterion) — the score that rewards accuracy while penalising
   complexity.
4. **Every coefficient gets a standard error** — not just a value. This directly answers
   the question "how do you estimate the parameters?", distinct from "what order did you
   pick?" — the two are different questions, and only the second was answered before.
5. Each fitted model then generates an **ensemble of 1,000 synthetic monthly
   sequences**, and validation checks whether the *historical* record's statistical
   properties fall inside the *range* that ensemble produces — not whether any one
   synthetic sequence matches history exactly.

Each model is fitted to the **natural log** of its variable to stabilise variance —
checked to be valid (all three series are strictly positive at every one of 420 months),
not assumed.

---

## 🎯 The basin and the models

**Conecuh River at Brantley, Alabama (USA)** — USGS/CAMELS gauge `02371500` (the
*correct* gauge, see above). 35 years of monthly data (1980–2014, 420 months), trained
on 1980–2003, validated on 2004–2014.

| Variable | Selected model | Validation: properties within envelope |
|---|---|---|
| Discharge (m³/s) | ARIMA(4,0,1) | **7 / 7** |
| Rainfall (mm/month) | ARIMA(1,0,0) | **7 / 7** |
| Stage (m) | ARIMA(4,0,0) | **6 / 7** (mean falls short — see below) |

The one honest miss — stage's mean — is traced to residual seasonal structure the
non-seasonal ARIMA specification doesn't fully absorb (visible as a failed Ljung-Box
test for discharge and stage, though not for rainfall). This is reported, not hidden:
that's the whole point of validating by properties instead of picking a metric that
would look clean.

---

## 🗂️ What's in the folder

| Piece | What it does |
|-------|--------------|
| `src/preprocess.py` | Loads and monthly-aggregates all three series (discharge, rainfall, stage), log transform, train/valid split |
| `src/model.py` | Self-contained ARIMA + ADF/KPSS/ACF/PACF/Ljung–Box/ARCH/Jarque–Bera **+ parameter standard errors** |
| `src/calibrate.py` | Stationarity testing + AIC order selection |
| `src/simulate.py` | **New** — generates stochastic synthetic-sequence ensembles from a fitted model |
| `src/validation.py` | **New** — property-based validation: compares an ensemble's statistical properties to the historical record |
| `src/plots.py` | The 6 figures, rewritten for 3 variables x monthly x stochastic |
| `run_pipeline.py` | The **"run everything" button** — loads all 3 variables, fits all 3 models, runs stochastic validation, saves `data/results.json` + all figures |
| `app.py` + `pages/` | "River Outlook" — a 3-pane Streamlit dashboard (context left, controls/charts/story centre, compact per-variable cards right). One button forecasts all 3 variables at once; "For the curious" surfaces the AR/MA coefficients, standard errors, and stationarity evidence live |
| `figures/` | 9 charts: monthly series, ACF/PACF, ensemble vs. observed, property validation, residual diagnostics, parameter estimates with confidence intervals (all 3-variable panels), plus the two app screenshots and the cross-basin check figure |
| `documents/Computer_Hydrological_Forecasting_Full_Report.docx` | The full Chapter 1–5 thesis, rewritten for the new methodology |
| `write_full_report.py` (+ `report_front_ch12.py`, `report_ch345.py`, `report_lib.py`) | Generates the full report from `data/results.json`; the code appendix is extracted live from `src/*.py` so it can't drift from the code that produced the results |
| `cross_basin_check.py` | Supplementary: reruns the identification/estimation procedure, unmodified, on two more CAMELS basins → `data/cross_basin_check.json` |
| `cross_basin_figure.py` | Turns the cross-basin check into Figure 9 (AR(1) coefficients with 95% CI, coloured by Ljung-Box pass/fail) |
| `design_discharge_example.py` | Worked reservoir/spillway design-discharge example from pooled synthetic annual maxima → `data/design_discharge_example.json` |

---

## 🛠️ Tech used

Plain **Python** — `pandas`, `numpy`, `scipy` (the math), `matplotlib` (charts),
`streamlit` (the web app), `requests` (one-off USGS NWIS data pull). The whole
time-series toolkit — ARIMA, stationarity tests, ACF/PACF, Ljung–Box, standard errors,
stochastic simulation, property-based validation — is implemented from first principles.
No external time-series modelling library (no `statsmodels`).

---

## ✅ Where it stands

- **Data:** re-pulled and verified for the correct gauge (02371500). Discharge 0.56%
  missing at daily resolution, effectively complete monthly; rainfall complete
  (zero missing days, Daymet product); stage complete monthly (zero fully-missing
  months).
- **Models:** all three variables fitted, diagnosed, and validated. Full diagnostics
  (Ljung-Box, ARCH, Jarque-Bera, characteristic roots) computed and reported honestly,
  including where they don't pass.
- **App:** redesigned twice — first for per-variable stochastic forecasting, then
  rebuilt again as "River Outlook," a one-click dashboard that forecasts all 3
  variables together with a plain-language explanation per variable, a 3-pane layout
  (not a narrow centred column), and a "For the curious" panel exposing the actual
  AR/MA coefficients, their standard errors, and the stationarity test evidence — not
  just the model order. Tested end-to-end in a real browser, committed and pushed —
  the live Render deployment updates automatically from this.
- **Report:** Chapters 1–5 rewritten — corrected basin identity throughout, added an
  explicit AR/MA/ARMA/ARIMA/ARIMAX comparison to the literature review, rewrote the
  methodology chapter around monthly/multi-variable/stochastic validation, rewrote the
  results chapter around the new figures and tables, and the code appendix
  auto-updated to include the two new modules (`simulate.py`, `validation.py`).
- **Reviewed twice, independently.** Two rounds of critical review surfaced real
  problems (a table numbering gap, a data-vs-text mismatch, two backwards test-result
  claims) that are now fixed, plus three genuine methodological gaps (no reservoir/
  spillway worked example, an unsupported cross-basin transfer claim, an unstated
  discharge/stage independence caveat) that are now resolved with real supplementary
  analysis (§4.6, §4.8, §3.2) rather than just softened language. See "What was added on
  2026-08-13" above for the full list.
- **Still open, disclosed rather than hidden:** the cross-basin check covers discharge
  and rainfall only (not stage, which needs a live per-basin data pull) and stops at
  order selection + diagnostics — it does not repeat the full 1,000-member stochastic
  validation for the two extra basins; that full replication is future work (Report
  §5.4). The design-discharge worked example is explicitly illustrative, not a
  substitute for a real design study with a formally chosen exceedance-probability
  standard.
- **Not yet done:** the docx → PDF export is manual (WPS Writer, Ctrl+A then F9 to
  refresh the Table of Contents / List of Figures / List of Tables, then export) — this
  machine has no Word/LibreOffice, so that last step is on you.

---

## ▶️ How to run it

```bash
# Run the full pipeline (all 3 variables, all figures, data/results.json) — ~1-2 min
python run_pipeline.py

# Rebuild the full Chapter 1-5 report from the latest results.json
python write_full_report.py

# Rebuild this overview PDF
python make_overview_pdf.py

# Launch the interactive web app
streamlit run app.py
```

Regeneration order matters: run `run_pipeline.py` first — everything else reads
`data/results.json`, which it writes.
