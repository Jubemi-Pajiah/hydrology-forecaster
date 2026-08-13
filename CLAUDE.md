# CLAUDE.md — Computer Hydrological Forecasting

Guidance for Claude Code (and humans) working in this repository.

## What this project is
B.Sc. final-year project: statistical hydrological forecasting for the **Conecuh River
at Brantley, Alabama (USGS gauge 02371500, CAMELS dataset)**. Three **independent**
univariate ARIMA (Box–Jenkins) models — discharge, rainfall, stage — each forecast from
that variable's own past **monthly** values only (no cross-variable input), validated by
whether a 1,000-sequence stochastic ensemble reproduces the *statistical properties* of
the historical record, not by point-forecast comparison. Author: Ugbodaga Benedict
Osikpemi. Supervisor: Prof. K. O. Aiyesimoju.

> **History — read before touching basin/gauge or timestep/variable code.**
> This project has been through three pivots, each on direct supervisor instruction:
> 1. An early rainfall-runoff (two-bucket) version targeting the Ogun-Osun basin in
>    Nigeria was **replaced** by a discharge-only statistical ARIMA model. Do not
>    reintroduce rainfall-runoff, the unit hydrograph, the Ogun-Osun basin, or NASA
>    POWER data as inputs — the superseded files live in `archive/`.
> 2. On 2026-08-12 a data error was found: USGS gauge **02361000**, used throughout the
>    project until then, is the **Choctawhatchee River near Newton, AL**, not the
>    Conecuh — confirmed against NWIS. The real Conecuh gauge is **02371500** (Conecuh
>    River at Brantley, AL), also a CAMELS basin, with a longer and cleaner record
>    (discharge 1937–present, stage 1973–present). Do not reintroduce 02361000.
> 3. Also on 2026-08-12, per supervisor instruction: **monthly** timestep instead of
>    daily (differencing only does useful work — removing seasonality — at a monthly
>    step); **three independent variables** (discharge, rainfall, stage) instead of
>    discharge alone, to demonstrate the ARIMA methodology generalises across variable
>    types; and **stochastic, property-based validation** instead of point-forecast
>    comparison, since a stochastic model's individual runs aren't meant to reproduce
>    one specific observed sequence. **This pivot is complete** — pipeline, app, and
>    report all reflect it. On 2026-08-13 the Streamlit app was further redesigned
>    ("River Outlook": a one-click, all-3-variables-at-once dashboard) and the project
>    overview gained a defence-prep Q&A section.

## Folder structure
```
finals_project/
├── CLAUDE.md                  ← this file
├── PROJECT_OVERVIEW.md        ← plain-English repo overview (source for the PDF)
├── DATA_OPTIONS.md            ← working doc: Nigerian/Beninese data options investigated
│                                  (NIHSA, OORBDA, AMMA-CATCH) and why Conecuh was kept
├── documents/                 ← FINISHED DELIVERABLES to send to the supervisor
│   ├── Computer_Hydrological_Forecasting_Full_Report.docx  ← THE deliverable
│   │      (front matter + Ch 1-5 + References + code Appendix, on the Civil template)
│   ├── Chapter3_4_5_Hydrological_Forecasting.docx   (superseded: Ch 3-5 only)
│   ├── Project_Overview.pdf                          (overview + defence-prep Q&A)
│   ├── Project_Overview.docx                         (same content as PROJECT_OVERVIEW.md, .docx form)
│   ├── PROJECT TEMPLATE_Civil.docx                   (departmental template)
│   ├── 190402003_ benedict ugbodaga (2).docx         (author's Ch 1-3 draft, superseded)
│   └── README.md                                     (what to send + WPS export steps)
├── archive/                   ← superseded rainfall-runoff material (not used)
│   ├── PROJECT_CONTEXT.md, POWER_…csv, logs/, README.md
├── src/                       ← the engine
│   ├── preprocess.py   monthly loaders for discharge/rainfall/stage, log-transform, train/valid split
│   ├── model.py         ARIMA(p,d,q) by CSS + ADF/KPSS/ACF/PACF/Ljung-Box/ARCH/Jarque-Bera + standard errors
│   ├── calibrate.py    stationarity tests + common-sample AIC order selection
│   ├── simulate.py     stochastic synthetic-ensemble generation from a fitted model
│   ├── validation.py   property-based validation (ensemble vs. historical statistics)
│   ├── forecast.py     residual_diagnostics (used); forecast_evaluation is legacy point-forecast code, not called by run_pipeline.py
│   ├── metrics.py      NSE, RMSE, PBIAS, MAE, R², persistence skill score (legacy; not the headline metric any more, see below)
│   └── plots.py        the six figures (monthly, 3-variable, stochastic)
├── run_pipeline.py            ← runs everything end-to-end for all 3 variables (~2 min; writes data/results.json + figures/)
├── write_full_report.py       ← builds the FULL Ch 1-5 report (+ references, + code appendix)
│   ├── report_lib.py             template styling, figures/tables, code-block rendering
│   ├── report_front_ch12.py      front matter, Chapter One, Chapter Two
│   └── report_ch345.py           Chapters Three, Four, Five
├── write_document.py          ← builds the older Ch 3-5-only .docx into documents/ (superseded, still runnable)
├── make_overview_pdf.py       ← builds the overview + Q&A PDF into documents/ (own hand-authored content,
│                                  not derived from PROJECT_OVERVIEW.md -- keep both in sync by hand)
├── make_overview_docx.py      ← mechanically converts PROJECT_OVERVIEW.md itself into documents/
│                                  Project_Overview.docx, so this one *can't* drift from the .md
├── cross_basin_check.py       ← supplementary: reruns identification+estimation, unmodified, on 2 more CAMELS
│                                  basins → data/cross_basin_check.json (Report §4.8, Table 9)
├── cross_basin_figure.py      ← turns cross_basin_check.json into Fig9_CrossBasinCheck.png (Report Figure 9)
├── design_discharge_example.py ← worked reservoir/spillway design-discharge example from pooled synthetic
│                                  annual maxima → data/design_discharge_example.json (Report §4.6, Table 8)
├── app.py + pages/            ← Streamlit web app: "River Outlook" (0_Forecast.py) + "How This Works" (1_Documentation.py)
├── render.yaml                ← Render.com deploy config (needs app.py at repo root)
├── requirements.txt
├── data/
│   ├── results.json                    ← per-variable model + validation results (consumed by docs and app)
│   ├── conecuh_discharge.csv           ← cached discharge, force-tracked in git
│   ├── conecuh_rainfall.csv            ← cached rainfall (daymet/maurer/nldas cols), force-tracked in git
│   ├── conecuh_gage_height_raw.csv     ← cached stage, force-tracked in git
│   ├── cross_basin_check.json          ← output of cross_basin_check.py
│   └── design_discharge_example.json   ← output of design_discharge_example.py
├── figures/                   ← Fig1–Fig9 PNGs (embedded into the thesis); Fig7/Fig8 are app screenshots
│                                  (retaken from the live app, not model output), Fig9 is the cross-basin figure
└── basin_timeseries_v1p2_metForcing_obsFlow.zip  ← raw CAMELS archive (3.4 GB, source data)
```

## How to run
```bash
python run_pipeline.py        # all 3 models + ensembles + figures + data/results.json (~2 min)
python write_full_report.py   # rebuild documents/Computer_Hydrological_Forecasting_Full_Report.docx
python write_document.py      # rebuild the older Ch 3-5-only .docx (superseded, kept working)
python make_overview_pdf.py   # rebuild documents/Project_Overview.pdf
python make_overview_docx.py  # rebuild documents/Project_Overview.docx (from PROJECT_OVERVIEW.md)
streamlit run app.py          # launch the web app ("River Outlook")
```
Regeneration order matters: `run_pipeline.py` first (it refreshes `results.json` and the
figures), then the document generators, which read `results.json`.

## The full report (documents/…Full_Report.docx)
- Formatted to `documents/PROJECT TEMPLATE_Civil.docx`: A4, 2 cm margins, Times New
  Roman 12 pt double-spaced, **two heading levels only** (the template forbids a third),
  table titles above tables, figure captions below figures, sequential Figure 1–9 /
  Table 1–9, APA 6 references with hanging indents, equations numbered flush right.
  Figures 3/4 are screenshots of the live app (Fig7_AppDashboard.png /
  Fig8_AppCoefficients.png on disk — filenames don't match caption numbers, re-take
  these from the app whenever its UI changes materially). Figure 9 and Table 9
  (Section 4.8) are the supplementary cross-basin check; Table 8 (Section 4.6) is the
  design-discharge worked example — added 2026-08-13 in response to two rounds of
  independent critical review, see PROJECT_OVERVIEW.md's "What was added on
  2026-08-13" section for the full list of what was fixed vs. deliberately deferred.
- **Chapters 1–2 have been rewritten twice.** First to replace the superseded
  rainfall-runoff framing with the ARIMA one. Then again on 2026-08-12/13 for the
  monthly/3-variable/stochastic pivot — Chapter 2 now includes an explicit
  AR/MA/ARMA/ARIMA/ARIMAX comparison (the supervisor asked for this directly) and a
  stochastic-hydrology/property-based-validation literature section. Do not reintroduce
  the rainfall–runoff text, and do not silently drop the ARIMAX comparison.
- The Table of Contents, List of Figures and List of Tables are **Word fields**, and the
  figure/table lists key off the custom `FigureCaption` / `TableCaption` styles. They are
  empty until refreshed — Ctrl+A then F9 in WPS Writer before exporting to PDF.
- The Appendix (A–G) is extracted from `src/*.py` **at build time via `ast`**, so the
  listings cannot drift from the code that produced the results. Renaming a function
  listed in `write_full_report.appendix_listings()` will fail the build loudly, which is
  intended. Appendix F/G now cover `simulate.py`/`validation.py`, not the old
  forecast/metrics point-forecast code.

## Working rules (important)
- **No new installs.** Do not `pip install` packages or system software without explicit
  approval. The time-series toolkit (ARIMA, ADF, KPSS, ACF/PACF, Ljung–Box, ARCH,
  Jarque–Bera, standard errors, stochastic simulation, property-based validation) is
  implemented from scratch on NumPy/SciPy/pandas on purpose — **do not add
  `statsmodels`**. `altair` (already installed) is used for the app's charts; `requests`
  for the one-off USGS NWIS pull that produced the cached stage CSV.
- **docx → PDF is manual.** This machine has no Word/LibreOffice; the user exports the
  `.docx` to PDF in **WPS Writer** (Ctrl+A, F9 to refresh fields, then export). Do not
  install converters or attempt headless conversion.
- **No explicit bias-correction step any more.** The old daily/discharge-only pipeline
  needed a log-normal (`exp(μ+σ²ₖ/2)`) or Duan-smearing correction because it produced a
  single point forecast on the log scale. The current pipeline generates a stochastic
  ensemble and exponentiates every member individually (`src/simulate.py`), so the
  ensemble mean is unbiased by construction (Monte Carlo integration handles the
  log-normal skew automatically) — do not re-add an explicit correction step. The
  `smearing_factor` diagnostic is still computed and stored in `results.json` for
  reference, but it is not applied to anything.
- **Headline metric is property-based validation**, not the persistence skill score.
  Each variable reports "N of 7 properties within the synthetic ensemble's 90%
  envelope" (currently discharge 7/7, rainfall 7/7, stage 6/7). `metrics.py`'s NSE/PSS
  functions and `forecast.py`'s `forecast_evaluation` are legacy from the daily
  point-forecast pipeline and are not called by `run_pipeline.py` — don't reintroduce
  them as the reported result without discussing it first, since that would contradict
  the whole rationale for the 2026-08-12 pivot (see History above).
- All three variables currently select **d = 0** (no differencing) at the monthly
  timestep for this basin — a real, data-driven result (ADF/KPSS), not a bug. Chapter 4
  discusses this explicitly against the "monthly lets differencing do real work"
  rationale from the pivot. Don't force d ≥ 1.

## Current results (validation 2004–2014, stochastic property-based)
| Variable | Model | Properties within 90% envelope |
|---|---|---|
| Discharge (m³/s) | ARIMA(4,0,1) | 7 / 7 |
| Rainfall (mm/month) | ARIMA(1,0,0) | 7 / 7 |
| Stage (m) | ARIMA(4,0,0) | 6 / 7 (mean falls short) |

Residuals: Ljung-Box rejects (some autocorrelation remains) for discharge and stage, not
for rainfall — attributed to residual seasonal structure a non-seasonal ARIMA doesn't
fully absorb, and reported as an honest limitation (Chapter 4/5), not hidden. This is
also the most likely cause of stage's one property-validation miss. Full per-variable
coefficients, standard errors, and diagnostics are in `data/results.json` and Chapter 4
Tables 4–8.

## The Streamlit app (app.py + pages/) — "River Outlook"
- Two pages: `pages/0_Forecast.py` ("River Outlook", the default) and
  `pages/1_Documentation.py` ("How This Works"). Nav titles are set in `app.py`'s
  `st.Page(..., title=...)` calls — keep them in sync with the pages' own `st.title()`
  calls if either changes.
- **The app must not re-estimate any model.** `fit_model(variable)` loads that
  variable's coefficients from `data/results.json` via `ARIMA.from_params(...)`.
  Calling `.fit()` in the app is wrong for the same reason it always was: slow on cold
  start, and it would silently fit on the full record instead of the training-only
  coefficients the report describes.
- **A forecast is a stochastic ensemble, not a point value.** The app calls
  `simulate_ensemble(model, y_hist_log, horizon, n_reps, method="gaussian")` — there is
  no `forecast_from`/point-forecast path in the current app. Re-running with the same
  inputs gives a different ensemble every time (no fixed seed) — this is deliberate, it
  demonstrates the stochastic nature of the model live.
- **Layout is a 3-pane dashboard**, not a sidebar-driven per-variable form: left =
  static context/facts, centre = controls + per-variable chart tabs + plain-language
  narrative + "For the curious" (coefficients/SEs/stationarity evidence/validation
  table), right = compact outlook card per variable. One "Get the Outlook" button runs
  all three variables at once. Do not revert to a single-variable-at-a-time flow without
  discussing it — this was a deliberate redesign, not the original design.
- Narrative text built by `build_narrative()` uses `<strong>` HTML tags, **not**
  Markdown `**bold**` — it is always injected into a raw HTML block
  (`unsafe_allow_html=True`), and Markdown syntax is not parsed inside HTML blocks.
  This was shipped broken once already; don't reintroduce `**` in that function.
- **No "horizon from origin" control any more.** The app asks for an explicit "Predict
  from [month] [year] to [month] [year]" range (plus four jump-to-range presets, e.g.
  "2030 – 2035"), not a horizon length off a fixed anchor — replaced deliberately after
  repeated feedback that an origin-plus-horizon framing didn't let a user just say "2050
  to 2060." Both year fields run from 2015 (the first predictable year after the record
  ends) up to 2200, with -/+ stepper buttons flanking each year dropdown. Internally the
  app still simulates forward from the record's last real month (2014-12) to the
  requested end date and slices the display window, but that's implementation plumbing,
  not something exposed as an "origin" concept in the UI. The record ends 2014-12-31, so
  any forecast is necessarily historical, not "today" — stated in the left rail and in
  the controls, not buried in a footer caption (an earlier version buried it and testers
  missed it).

## Deployment note
The Streamlit app needs `data/conecuh_discharge.csv`, `data/conecuh_rainfall.csv`, and
`data/conecuh_gage_height_raw.csv` (the three cached series) at runtime; all three are
force-tracked in git (see `.gitignore`) so the Render deployment works without the
3.4 GB raw zip or a live NWIS fetch. The live site updates only when you commit and push.
```bash
streamlit run app.py
```
