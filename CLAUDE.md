# CLAUDE.md — Computer Hydrological Forecasting

Guidance for Claude Code (and humans) working in this repository.

## What this project is
B.Sc. final-year project: **short-term (1–3 day) river-discharge forecasting** for the
**Conecuh River, Alabama (USGS gauge 02361000, CAMELS dataset)** using a **purely
statistical, discharge-only ARIMA (Box–Jenkins) model**. It forecasts discharge from its
own past values — **no rainfall, temperature, evapotranspiration, or unit-hydrograph
routing**. Author: Ugbodaga Benedict Osikpemi. Supervisor: Prof. K. O. Aiyesimoju.

> History: an earlier rainfall-runoff (two-bucket) version targeting the Ogun-Osun basin
> in Nigeria was **replaced** on supervisor instruction. Do not reintroduce rainfall,
> the unit hydrograph, the Ogun-Osun basin, or NASA POWER data. The superseded files live
> in `archive/`.

## Folder structure
```
finals_project/
├── CLAUDE.md                  ← this file
├── PROJECT_OVERVIEW.md        ← plain-English repo overview (source for the PDF)
├── documents/                 ← FINISHED DELIVERABLES to send to the supervisor
│   ├── Computer_Hydrological_Forecasting_Full_Report.docx  ← THE deliverable
│   │      (front matter + Ch 1-5 + References + code Appendix, on the Civil template)
│   ├── Chapter3_4_5_Hydrological_Forecasting.docx   (superseded: Ch 3-5 only)
│   ├── Project_Overview.pdf                          (overview)
│   ├── PROJECT TEMPLATE_Civil.docx                   (departmental template)
│   ├── 190402003_ benedict ugbodaga (2).docx         (author's Ch 1-3 draft)
│   └── README.md                                     (what to send + WPS export steps)
├── archive/                   ← superseded rainfall-runoff material (not used)
│   ├── PROJECT_CONTEXT.md, POWER_…csv, logs/, README.md
├── src/                       ← the engine
│   ├── preprocess.py   load discharge from CAMELS zip, log-transform, train/valid split
│   ├── model.py        ARIMA(p,d,q) by CSS + ADF/KPSS/ACF/PACF/Ljung-Box/ARCH/Jarque-Bera
│   ├── calibrate.py    stationarity tests + common-sample AIC order selection
│   ├── forecast.py     rolling multi-step forecast, persistence benchmark, bias correction
│   ├── metrics.py      NSE, RMSE, PBIAS, MAE, R², persistence skill score
│   └── plots.py        the six figures
├── run_pipeline.py            ← runs everything end-to-end (writes data/results.json + figures/)
├── write_full_report.py       ← builds the FULL Ch 1-5 report (+ references, + code appendix)
│   ├── report_lib.py             template styling, figures/tables, code-block rendering
│   ├── report_front_ch12.py      front matter, Chapter One, Chapter Two
│   └── report_ch345.py           Chapters Three, Four, Five
├── write_document.py          ← builds the older Ch 3-5-only .docx into documents/
├── make_overview_pdf.py       ← builds the overview PDF into documents/
├── app.py + pages/            ← Streamlit web app (Forecast Tool + Documentation)
├── render.yaml                ← Render.com deploy config (needs app.py at repo root)
├── requirements.txt
├── data/
│   ├── results.json           ← model + validation metrics (consumed by docs and app)
│   └── conecuh_discharge.csv  ← cached discharge (lets the pipeline/app run without the 3.4 GB zip)
├── figures/                   ← Fig1–Fig6 PNGs (embedded into the thesis)
└── basin_timeseries_v1p2_metForcing_obsFlow.zip  ← raw CAMELS archive (3.4 GB, source data)
```

## How to run
```bash
python run_pipeline.py        # model + forecasts + figures + data/results.json (~80 s)
python write_full_report.py   # rebuild documents/Computer_Hydrological_Forecasting_Full_Report.docx
python write_document.py      # rebuild the older Ch 3-5-only .docx
python make_overview_pdf.py   # rebuild documents/Project_Overview.pdf
streamlit run app.py          # launch the web app
```
Regeneration order matters: `run_pipeline.py` first (it refreshes `results.json` and the
figures), then the document generators, which read `results.json`.

## The full report (documents/…Full_Report.docx)
- Formatted to `documents/PROJECT TEMPLATE_Civil.docx`: A4, 2 cm margins, Times New
  Roman 12 pt double-spaced, **two heading levels only** (the template forbids a third,
  so Chapter 3's old 3.2.1/3.4.2-style headings are flattened into 3.2–3.5), table titles
  above tables, figure captions below figures, sequential Figure 1–6 / Table 1–4, APA 6
  references with hanging indents, equations numbered (1)–(12) flush right.
- **Chapters 1–2 were rewritten.** The author's Ch 1–3 draft still described the
  superseded lumped rainfall–runoff model; leaving it would have contradicted Ch 4–5.
  The structure, argument and voice are preserved but the model family is now the ARIMA
  one actually built. Do not reintroduce the rainfall–runoff text.
- The Table of Contents, List of Figures and List of Tables are **Word fields**, and the
  figure/table lists key off the custom `FigureCaption` / `TableCaption` styles. They are
  empty until refreshed — Ctrl+A then F9 in WPS Writer before exporting to PDF.
- The Appendix (A–G) is extracted from `src/*.py` **at build time via `ast`**, so the
  listings cannot drift from the code that produced the results. Renaming a function
  listed in `write_full_report.appendix_listings()` will fail the build loudly, which is
  intended.

## Working rules (important)
- **No new installs.** Do not `pip install` packages or system software without explicit
  approval. The time-series toolkit (ARIMA, ADF, KPSS, ACF/PACF, Ljung–Box, ARCH,
  Jarque–Bera) is implemented from scratch on NumPy/SciPy on purpose — **do not add
  `statsmodels`**.
- **docx → PDF is manual.** This machine has no Word/LibreOffice; the user exports the
  `.docx` to PDF in **WPS Writer** (Ctrl+A, F9 to refresh fields, then export). Do not
  install converters or attempt headless conversion.
- **Forecasts are bias-corrected.** Modelling is on log-discharge; forecasts are
  back-transformed with the log-normal correction `exp(μ + σ²ₖ/2)` (Duan smearing as a
  cross-check). Keep this — removing it reintroduces a lead-time-growing negative bias.
- Headline metric is the **persistence skill score** (daily flow is highly autocorrelated,
  so persistence is the benchmark to beat). Useful absolute skill is ~1-day.

## Current results (validation 2004–2014, bias-corrected)
ARIMA(3,1,2): 1-day NSE 0.824 / PSS +0.224 / PBIAS +1.0%; 2-day 0.541 / +0.244;
3-day 0.347 / +0.267. Residuals: no short-lag autocorrelation (Ljung–Box p≈0.23) but
volatility clustering + heavy tails (expected for streamflow). MA root ≈1.09 (mild
over-differencing, acknowledged in the thesis).

## The Streamlit app (app.py + pages/)
- The app **must not re-estimate the model**. `fit_model()` loads the coefficients from
  `data/results.json` via `ARIMA.from_params(...)`. Calling `.fit()` here was wrong twice
  over: it took ~133 s (a two-minute blank page on Render's free tier), and it fitted on
  the FULL 1980-2014 record, so the app's coefficients silently differed from the
  training-period ones reported in Chapter 4 while the sidebar showed the thesis AIC.
- The forecast **origin is user-selectable** (`ARIMA.forecast_from(y_hist, k)`), not pinned
  to the end of the record. With a fixed origin the app returned identical values forever
  and looked broken. Choosing an earlier origin scores the forecast against the discharge
  that actually followed — the single-origin form of the thesis's rolling-origin evaluation.
- The record ends 2014-12-31, so forecast dates are historical. Say so prominently in the
  UI; a grey caption at the bottom of the page is not enough — testers missed it.

## Deployment note
The Streamlit app needs `data/conecuh_discharge.csv` (the cached discharge) at runtime;
it is force-tracked in git (see `.gitignore`) so the Render deployment works without the
3.4 GB raw zip. The live site updates only when you commit and push.
```bash
streamlit run app.py
```
