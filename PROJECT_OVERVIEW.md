# Project Overview — Computer Hydrological Forecasting

A plain-English rundown of what this project is and how it fits together, as of the
2026-08-12 pivot to a monthly, three-variable, stochastically-validated framework.

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
| `app.py` + `pages/` | Streamlit web app — pick a variable, get a stochastic forecast ensemble, see property-based validation live |
| `figures/` | 6 charts: monthly series (3-panel), ACF/PACF (3x2), ensemble vs. observed (3-panel), property validation (3-panel), residual diagnostics (3x2), parameter estimates with confidence intervals (3-panel) |
| `documents/Computer_Hydrological_Forecasting_Full_Report.docx` | The full Chapter 1–5 thesis, rewritten for the new methodology |
| `write_full_report.py` (+ `report_front_ch12.py`, `report_ch345.py`, `report_lib.py`) | Generates the full report from `data/results.json`; the code appendix is extracted live from `src/*.py` so it can't drift from the code that produced the results |

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
- **App:** rewritten for per-variable stochastic forecasting, tested end-to-end in a
  real browser (variable selection, ensemble forecast, property validation table, all
  confirmed working), committed and pushed — the live Render deployment updates
  automatically from this.
- **Report:** Chapters 1–5 rewritten — corrected basin identity throughout, added an
  explicit AR/MA/ARMA/ARIMA/ARIMAX comparison to the literature review, rewrote the
  methodology chapter around monthly/multi-variable/stochastic validation, rewrote the
  results chapter around the new figures and tables, and the code appendix
  auto-updated to include the two new modules (`simulate.py`, `validation.py`).
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
