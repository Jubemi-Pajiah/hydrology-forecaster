# Project Overview — Computer Hydrological Forecasting

A plain-English rundown of what this project is and how it fits together.

---

## 🌊 What this project is

This is a **B.Sc. Civil & Environmental Engineering final-year project** — *"Computer
Hydrological Forecasting"*.

- **Author:** Ugbodaga Benedict Osikpemi (Matric 190402003)
- **Institution:** University of Lagos
- **Supervisor:** Prof. K. O. Aiyesimoju
- **Submission:** February 2026

In simple terms: it's a **computer program that predicts how much water will flow in a
river** over the next 1–3 days, using **only the river's own past discharge** — no
rainfall or weather data. The approach is purely **statistical**.

---

## 🧠 How it works (the science, simply)

It uses a **statistical time-series model** from the **ARIMA (Box–Jenkins) family**.
The idea: daily river flow is highly *autocorrelated* — today's flow is the best single
predictor of tomorrow's. The model learns this temporal pattern from the historical
discharge record and projects it forward.

The model is built the proper Box–Jenkins way:
1. **Stationarity tests** (ADF + KPSS) decide how much to *difference* the series → `d`.
2. **ACF / PACF** plots suggest the autoregressive (`p`) and moving-average (`q`) orders.
3. The order is picked objectively by **AIC**; the winner here is **ARIMA(3,1,2)**.
4. A **Ljung–Box test** confirms the residuals are white noise (model is adequate).

The model is fitted to the **natural log** of discharge to stabilise the variance.

---

## 🎯 The basin and the benchmark

- **Conecuh River, Alabama (USA)** — CAMELS gauge `02361000`. ~35 years of clean daily
  discharge (1980–2014). Trained on 1980–2003, validated on 2004–2014.
- **Persistence benchmark** — "tomorrow equals today." Because daily flow is so
  autocorrelated, persistence is a strong baseline, so the key result is the
  **persistence skill score** (how much the model beats it). It's **positive at every
  lead time**, proving the model adds real skill.

---

## 🗂️ What's in the folder

| Piece | What it does |
|-------|--------------|
| `src/` | The engine — `preprocess.py` (load discharge, log-transform, split), `model.py` (self-contained ARIMA + ADF/KPSS/ACF/PACF/Ljung–Box), `calibrate.py` (stationarity + AIC order selection), `forecast.py` (rolling multi-step forecast + persistence), `metrics.py` (NSE, RMSE, PBIAS, MAE, R², skill score), `plots.py` (figures) |
| `run_pipeline.py` | The **"run everything" button** — loads data, identifies/fits the model, evaluates forecasts, makes all 6 figures |
| `app.py` + `pages/` | A **Streamlit web app** with a "Forecast Tool" page and a "Documentation" page |
| `figures/` | The 6 charts for the thesis (discharge series, ACF/PACF, forecast hydrograph, scatter, residual diagnostics, skill-vs-lead) |
| `Chapter3_4_5_Hydrological_Forecasting.docx` | The **written thesis** chapters (Methods, Results, Conclusion) |
| `write_document.py` | Generates the thesis docx from `data/results.json` + figures |

---

## 🛠️ Tech used

Plain **Python** — `pandas`, `numpy`, `scipy` (the math), `matplotlib` (charts),
`streamlit` (the web app). The whole time-series toolkit (ARIMA, stationarity tests,
ACF/PACF, Ljung–Box) is implemented from first principles — no extra modelling library.

---

## ✅ Where it stands

Runs end-to-end. Latest validation results (2004–2014), model vs persistence
(forecasts back-transformed with a log-normal bias correction, so PBIAS is near zero):

- **1-day:** NSE 0.824 (Very Good), skill score +0.22, PBIAS ≈ +1.0%
- **2-day:** NSE 0.541, skill score +0.24, PBIAS ≈ +0.4%
- **3-day:** NSE 0.347, skill score +0.27, PBIAS ≈ +0.1%
- Residuals show no significant short-lag autocorrelation (Ljung–Box p ≈ 0.23);
  as expected for streamflow they do show volatility clustering and heavy tails
  (so prediction intervals would need a heteroscedastic error model)
- Useful absolute skill is concentrated at the ~1-day horizon

---

## ▶️ How to run it

```bash
# Run the full forecasting pipeline (model + forecasts + figures + results.json)
python run_pipeline.py

# Regenerate the thesis document
python write_document.py

# Launch the interactive web app
streamlit run app.py
```
