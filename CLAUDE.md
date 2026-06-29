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
│   ├── Chapter3_4_5_Hydrological_Forecasting.docx   (thesis; figures embedded)
│   ├── Project_Overview.pdf                          (overview)
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
├── write_document.py          ← builds the thesis .docx into documents/
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
python write_document.py      # rebuild documents/Chapter3_4_5_Hydrological_Forecasting.docx
python make_overview_pdf.py   # rebuild documents/Project_Overview.pdf
streamlit run app.py          # launch the web app
```
Regeneration order matters: `run_pipeline.py` first (it refreshes `results.json` and the
figures), then the two document generators, which read `results.json`.

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

## Deployment note
The Streamlit app needs `data/conecuh_discharge.csv` (the cached discharge) at runtime;
it is force-tracked in git (see `.gitignore`) so the Render deployment works without the
3.4 GB raw zip. The live site updates only when you commit and push.
```bash
streamlit run app.py
```
