# CLAUDE.md — Computer Hydrological Forecasting

Guidance for Claude Code (and humans) working in this repository.

## What this project is
B.Sc. final-year project: a statistical **synthetic-record generator** for monthly
discharge on the **Conecuh River at Brantley, Alabama (USGS gauge 02371500, CAMELS
dataset)**. A univariate ARIMA (Box–Jenkins) model is fitted to the deseasonalised
monthly record and used to **generate synthetic monthly records of arbitrary length**
(the worked example is 1,000 years × 50 traces), from which design discharges are read
by return period. Validated by whether a 1,000-member stochastic ensemble reproduces the
*statistical properties* of the historical record, not by point-forecast comparison.
Rainfall and stage are retained only as a generality demonstration (§4.7), not as
co-equal subjects. Author: Ugbodaga Benedict Osikpemi. Supervisor: Prof. K. O.
Aiyesimoju.

> **The single most important thing to understand about this project.** The model does
> **not** predict the discharge of a named future month, and the app deliberately cannot
> be asked for one. It produces a long synthetic record — a longer *sample* of the same
> river — because that is what sizing a reservoir, spillway or channel actually consumes.
> Any change that reintroduces a "forecast for date X" framing is a regression.

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
>    daily (the supervisor's shorthand was "differencing removes the seasonality at a
>    monthly step" — see correction 1 below for the precise version, which the docs now
>    use); **three independent variables** (discharge, rainfall, stage) instead of
>    discharge alone, to demonstrate the ARIMA methodology generalises across variable
>    types; and **stochastic, property-based validation** instead of point-forecast
>    comparison, since a stochastic model's individual runs aren't meant to reproduce
>    one specific observed sequence. **This pivot is complete** — pipeline, app, and
>    report all reflect it. On 2026-08-13 the Streamlit app was further redesigned
>    ("River Outlook": a one-click, all-3-variables-at-once dashboard) and the project
>    overview gained a defence-prep Q&A section.
> 4. On 2026-08-15 a review of the overview document and the *live app* (not the thesis
>    text) found seven claims that were imprecise, over-absolute, or inconsistent
>    between surfaces. All seven are now fixed in report + overview + app. **Do not
>    revert any of them**; each is a likely defence question:
>    1. **Ordinary differencing does not remove monthly seasonality.** `X(t)-X(t-1)`
>       removes trend/slow drift; an annual cycle needs `X(t)-X(t-12)` or SARIMA.
>       Monthly aggregation makes `d` *testable* and exposes the annual cycle — it does
>       not make ordinary differencing a seasonal filter. Still true, and pivot 5 acted on
>       it: the cycle is now removed explicitly (see the seasonality rule below).
>    2. ~~**Never say all three models fit well.**~~ **SUPERSEDED by pivot 5.** This was
>       true of the old non-seasonal models (Ljung–Box rejected for discharge p = 0.0035
>       and stage p = 0.0011). Treating the annual cycle explicitly fixed it: all three
>       now pass. See "Current results" below for the live figures.
>    3. **N/7 is not an accuracy grade** — it is property reproduction. The phrase "the
>       closest thing this model has to an accuracy grade" was removed from the app.
>    4. **"Comparing a stochastic forecast to observations is meaningless" is too
>       absolute.** Judging one *realisation* deterministically is what's wrong;
>       observations can be scored against the predictive distribution (coverage, CRPS,
>       log score, calibration, rank histograms, Brier). Property validation is one such
>       check; the others are cited as future work (§5.4, Gneiting & Raftery 2007).
>    5. **Cross-basin consistency.** The app's limitations table said transfer was
>       "untested" while the report described the §4.8 two-basin check. The app now
>       carries the report's qualified position.
>    6. ~~**Long horizons are conditional.**~~ **SUPERSEDED by pivot 5.** There is no
>       "horizon" any more — the app asks for a record length, not a target year, and the
>       output is never a prediction. The substance survives as an always-on statement
>       rather than a conditional warning.
>    7. **Log back-transformation verified against the code.** `src/simulate.py`
>       exponentiates each of the 1,000 paths individually and all statistics are taken
>       afterwards on the natural-scale ensemble, so no retransformation correction is
>       needed (see the bias-correction rule below). The app's single line through the
>       band is the ensemble **median** and is labelled as such, not "expected path".
> 5. **On 2026-08-19 the supervisor rejected the app and the differencing order** in a
>    phone review. Three demands: (a) *"monthly cannot be zero... if it's monthly data
>    it's ARIMA, not ARMA"* — with a follow-up message specifying **the differencing
>    factor should be 12**; (b) the program must work on any data, the front end being
>    wired to discharge is fine; (c) the output must be **a long table of every month for
>    a user-specified number of years** — *"it will just produce like a long table... it's
>    not supposed to just produce one particular month that you picked"* — because the
>    purpose is sizing a reservoir off the extremes. He also confirmed **discharge only**
>    for the headline. This pivot is complete; see the seasonality rule below for how (a)
>    was resolved, because it is the one place the implementation deliberately does not
>    follow his literal instruction, and the defence hinges on being able to explain why.

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
│   ├── preprocess.py   monthly loaders, log-transform, SEASONAL PROFILE
│   │                     (12 monthly means/SDs) + deseasonalise/reseasonalise, train/valid split
│   ├── model.py         ARIMA(p,d,q)(P,D,Q)[s] by CSS + ordinary AND seasonal differencing
│   │                     operators with inverses + ADF/KPSS/ACF/PACF/Ljung-Box/ARCH/JB + std errors
│   ├── calibrate.py    seasonality strength + stationarity tests + common-sample AIC order selection
│   ├── simulate.py     VECTORISED synthetic-record generation (generate_synthetic_record)
│   ├── validation.py   property-based validation (ensemble vs. historical statistics)
│   ├── forecast.py     residual_diagnostics (used); forecast_evaluation is legacy point-forecast code, not called by run_pipeline.py
│   ├── metrics.py      NSE, RMSE, PBIAS, MAE, R², persistence skill score (legacy; not the headline metric any more, see below)
│   └── plots.py        the six figures (monthly, 3-variable, stochastic)
├── run_pipeline.py            ← runs everything end-to-end for all 3 variables (~3 min; writes data/results.json + figures/)
│                                  incl. the 1000-yr synthetic record and the lag-12 differencing comparison
├── write_full_report.py       ← builds the FULL Ch 1-5 report (+ references, + code appendix)
│   ├── report_lib.py             template styling, figures/tables, code-block rendering
│   ├── report_front_ch12.py      front matter, Chapter One, Chapter Two
│   └── report_ch345.py           Chapters Three, Four, Five
├── write_document.py          ← builds the older Ch 3-5-only .docx into documents/ (superseded, still runnable)
├── overview_render.py         ← THE single content source for the overview + defence Q&A. Both output
│                                  scripts below call render(target, R) with a different backend, so the
│                                  PDF and the .docx cannot drift apart. Edit content HERE, once.
│                                  (Note: PROJECT_OVERVIEW.md is a separate, hand-maintained repo
│                                  overview — it does NOT feed these builds; keep it in sync by hand.)
├── make_overview_pdf.py       ← fpdf backend for overview_render → documents/Project_Overview.pdf
├── make_overview_docx.py      ← python-docx backend for overview_render → documents/Project_Overview.docx
├── cross_basin_check.py       ← supplementary: reruns identification+estimation, unmodified, on 2 more CAMELS
│                                  basins → data/cross_basin_check.json (Report §4.8, Table 9)
├── cross_basin_figure.py      ← turns cross_basin_check.json into Fig9_CrossBasinCheck.png (Report Figure 9)
├── design_discharge_example.py ← SUPERSEDED. Its worked example is now computed inside run_pipeline.py
│                                  (results.json → synthetic_record) and reported as Table 10. Script still
│                                  runs but nothing reads its JSON any more.
├── app.py + pages/            ← Streamlit web app: "River Outlook" (0_Forecast.py, synthetic-record
│                                  generator) + "How This Works" (1_Documentation.py)
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
python make_overview_docx.py  # rebuild documents/Project_Overview.docx (same content as the PDF)
streamlit run app.py          # launch the web app ("River Outlook")
```
Regeneration order matters: `run_pipeline.py` first (it refreshes `results.json` and the
figures), then the document generators, which read `results.json`.

## The full report (documents/…Full_Report.docx)
- Formatted to `documents/PROJECT TEMPLATE_Civil.docx`: A4, 2 cm margins, Times New
  Roman 12 pt double-spaced, **two heading levels only** (the template forbids a third),
  table titles above tables, figure captions below figures, sequential Figure 1–9 /
  Table 1–12, APA 6 references with hanging indents, equations numbered flush right.
  Figures 3/4 are screenshots of the live app (Fig7_AppDashboard.png /
  Fig8_AppCoefficients.png on disk — filenames don't match caption numbers, re-take
  these from the app whenever its UI changes materially — **they are stale as of the
  2026-08-19 rebuild and must be retaken**). Key tables: Table 2 (§4.2) is the
  lag-12-differencing-vs-standardisation comparison, Table 9 (§4.6) the generated record
  against the observed one, Table 10 (§4.6) the design discharges by return period,
  Table 11 (§4.7) the same procedure on three variables, and Figure 9 / Table 12 (§4.9)
  the supplementary cross-basin check.
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
- **Headline output is the synthetic record and its return periods.** The validation
  metric behind it is property-based ("N of 7 properties within the synthetic ensemble's
  90% envelope"), not a persistence skill score. `metrics.py`'s NSE/PSS
  functions and `forecast.py`'s `forecast_evaluation` are legacy from the daily
  point-forecast pipeline and are not called by `run_pipeline.py` — don't reintroduce
  them as the reported result without discussing it first, since that would contradict
  the whole rationale for the 2026-08-12 pivot (see History above).
- **Seasonality is removed by standardisation, NOT by differencing at lag 12 — and this
  is the one place the project deliberately departs from a direct supervisor
  instruction.** Read this before touching `choose_differencing`, `seasonal_profile` or
  anything in `simulate.py`.
  - He is right that the annual cycle must be removed and that ordinary differencing
    cannot do it. At this gauge the 12 monthly means carry ~50% of the variance.
  - But his two demands are **mathematically incompatible as literally stated**.
    Differencing at lag 12 leaves an *integrated* process: reconstructing the level scale
    is a running total, whose variance grows without bound. Asked for the 1,000-year
    record he also demanded, it drifts to a mean of ~10¹⁰ m³/s against an observed 16.4,
    a factor of ~10⁹ from first decade to last. **A generating model must be stationary.**
  - So the cycle is removed by seasonal standardisation (12 monthly means + 12 SDs,
    `src/preprocess.py`), which removes exactly what he wants removed, keeps the
    generator stationary, and is the classical stochastic-hydrology treatment (Salas et
    al. 1980). The number **12** is still literally in the model, as 12 parameters.
  - The lag-12 differencing path is **fully implemented and must stay that way**
    (`seasonal_difference` / `integrate_seasonal` / `apply_differencing` /
    `invert_differencing` in `src/model.py`, multiplicative seasonal AR/MA via
    `ARIMA._expand`). `run_pipeline.fit_seasonal_difference_alternative` fits it every
    run and stores the drift evidence in `results.json` under
    `seasonal_difference_alternative`. Report §4.2 Table 2 and the app's "For the
    curious" panel both present the comparison. **This is the evidence the student needs
    in front of the supervisor** — do not delete it as dead code.
  - Do not compare the two models' AICs: they are computed on different transformations
    of the series. §3.5 says so explicitly.
- With the cycle removed, ADF/KPSS select **d = 0** for the deseasonalised series. `d` is
  additionally **pinned to 0 for the generating model** (`d_values=(0,)` in
  `run_pipeline`), for the same stationarity reason; `d_indicated_by_tests` records what
  the tests said (stage's full record indicates d = 1). Don't "fix" this by letting d
  float — it would reintroduce the drift.
- **Innovations are bootstrapped from the residuals, not Gaussian.** Jarque–Bera rejects
  normality for discharge and stage, and the whole output is about extremes, so the tail
  shape matters. `INNOVATIONS = "bootstrap"` in `run_pipeline.py`.
- **`_simulate_w` is vectorised across realisations** (one Python step per time point,
  not per rep × time point). 1,000 years × 50 traces takes ~0.4 s; the old per-rep loop
  would take minutes. Don't refactor it back into a per-realisation loop.

## Current results (validation 2004–2014, stochastic property-based)
Seasonality removed by standardisation; ARIMA fitted to the deseasonalised series.

| Variable | Model | Ljung–Box p | Properties within 90% envelope |
|---|---|---|---|
| Discharge | ARIMA(1, 0, 1) | 0.344 | 6 / 7 |
| Rainfall | ARIMA(3, 0, 2) | 0.680 | 7 / 7 |
| Stage | ARIMA(1, 0, 1) | 0.286 | 5 / 7 |

**All three now pass Ljung–Box** — treating the cycle explicitly resolved the residual
autocorrelation the old non-seasonal models left behind (discharge was p = 0.0035).
The property misses are `seasonal_amplitude` (discharge, stage) and `mean` (stage), and
they are **not** a model defect: the annual cycle at this gauge weakened measurably over
the record (discharge amplitude 35.2 → 43.5 → 29.8 → 25.8 m³/s by decade; stage 1.80 →
1.88 → 1.41 → 1.37 m), so seasonal parameters fitted on 1980–2003 cannot reproduce
2004–2014. Report §4.6 says this; don't "fix" it.

**Design output (discharge, 1,000 yr × 50 traces, 50,000 synthetic years):**
mean 16.85 m³/s (observed 16.42), drift ratio 0.95.
Return periods — 2 yr 44, 10 yr 102, 100 yr 239, 500 yr 416 m³/s.
The 10-yr value sits at the observed 35-year maximum (110 m³/s), which is the
main external check that the extrapolation is calibrated.

**Never quote `synthetic_record.max` as a design figure** (1413 m³/s for discharge). It is the
most extreme of 50,000 simulated years from a log-linear model with no upper bound.
Return periods are the intended output; the report and app both say so explicitly.

Full coefficients, standard errors, seasonal profiles and diagnostics are in
`data/results.json` and Chapter 4 Tables 1–12.

## The Streamlit app (app.py + pages/) — "River Outlook"
- Two pages: `pages/0_Forecast.py` ("River Outlook", the default) and
  `pages/1_Documentation.py` ("How This Works"). Nav titles are set in `app.py`'s
  `st.Page(..., title=...)` calls — keep them in sync with the pages' own `st.title()`
  calls if either changes.
- **The app must not re-estimate any model.** `fit_model()` loads the coefficients and
  the seasonal profile from `data/results.json` (the `full_record` block) via
  `ARIMA.from_params(...)`, deseasonalising the history first so the residual pool the
  bootstrap draws from is correct. Calling `.fit()` in the app is wrong for the same
  reason it always was: slow on cold start, and it would silently refit.
- **The app asks for ONE input: how many years.** A free number field (1–10,000) plus
  30/100/500/1000 shortcuts, and a second field for how many independent records. There
  is no date, no target year, no horizon, and no way to request a single month. **Do not
  reintroduce any date-based control.** The supervisor rejected the previous version
  precisely for showing one value for one chosen year.
- **The long table is the primary output and must stay first**, above every chart: one
  row per month for every year requested, with a CSV download. Charts (return periods,
  histogram, flow-duration curve) come after it as reading aids. Years are numbered
  1…N, deliberately **not** dated — the process is stationary, so the record has no
  position in time.
- **Lead with return periods, never the record maximum.** The single largest value of a
  long record comes from an unbounded log-linear model; the app says so explicitly under
  the extremes card. Don't promote it to a headline number.
- **Layout is a 3-pane dashboard**: left = static context/facts/how-to-read, centre =
  control + table + design numbers + comparison charts + narrative + "For the curious",
  right = extremes card for the generated record and for the measured one. Do not revert
  to a form-and-chart layout without discussing it.
- Narrative and card text use `<strong>` HTML tags, **not** Markdown `**bold**` — they
  are injected into raw HTML blocks (`unsafe_allow_html=True`), where Markdown is not
  parsed. This was shipped broken once already; don't reintroduce `**` there.
- The app is **discharge-only**. `VARIABLE = "discharge"` at the top of
  `0_Forecast.py`; the old three-variable tabs, per-variable icons and trend pills are
  gone. A stationary process has no trend, so the old rising/falling arrow was sampling
  noise reported as a finding — don't bring it back.
- The "For the curious" panel carries the **lag-12 differencing comparison** (from
  `results.json → seasonal_difference_alternative`). That panel is the student's
  evidence for the supervisor; keep it.

## Deployment note
The Streamlit app needs `data/conecuh_discharge.csv`, `data/conecuh_rainfall.csv`, and
`data/conecuh_gage_height_raw.csv` (the three cached series) at runtime; all three are
force-tracked in git (see `.gitignore`) so the Render deployment works without the
3.4 GB raw zip or a live NWIS fetch. The live site updates only when you commit and push.
```bash
streamlit run app.py
```
