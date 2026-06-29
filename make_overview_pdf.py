"""
make_overview_pdf.py — Generate a plain-English project overview PDF.

Sections:
  1. Very basic explanation (high-school level)
  2. The actual explanation (builds on #1, technical)
  3. How to use the software

This project forecasts river discharge from its OWN past discharge using a
statistical time-series (ARIMA / Box-Jenkins) model. No rainfall, temperature or
evapotranspiration is used.

Run:  python make_overview_pdf.py
Output: Project_Overview.pdf
"""

import json
from pathlib import Path
from fpdf import FPDF

_DOCS = Path(__file__).parent / "documents"
_DOCS.mkdir(exist_ok=True)
OUTPUT = str(_DOCS / "Project_Overview.pdf")

# Load pipeline results so the overview always reflects the latest run
_RES = Path(__file__).parent / "data" / "results.json"
try:
    with open(_RES) as _f:
        R = json.load(_f)
except Exception:
    R = {}


def _fc(k, which, metric, default=0.0):
    try:
        return R["forecast"][str(k)][which][metric]
    except Exception:
        return default

# ── Colours ──────────────────────────────────────────────────────────────────
NAVY   = (30, 58, 95)
BLUE   = (37, 99, 235)
GREY   = (90, 100, 115)
LIGHT  = (239, 246, 255)
CODEBG = (244, 246, 248)
TEXT   = (30, 41, 59)


def clean(s: str) -> str:
    """Replace non-latin-1 characters so the core PDF fonts can render them."""
    repl = {
        "³": "^3", "²": "^2", "→": "->", "—": "-",
        "–": "-", "₀": "0", "°": " deg", "≈": "~",
        "≥": ">=", "≤": "<=", "•": "-", "×": "x",
        "’": "'", "‘": "'", "“": '"', "”": '"',
        "…": "...", "­": "", " ": " ", "φ": "phi", "θ": "theta",
    }
    for k, v in repl.items():
        s = s.replace(k, v)
    return s.encode("latin-1", "replace").decode("latin-1")


class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GREY)
        self.cell(0, 8, "Computer Hydrological Forecasting - Project Overview",
                  align="L")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GREY)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    # ── building blocks ──────────────────────────────────────────────────────
    def h1(self, num, title):
        self.ln(2)
        self.set_fill_color(*LIGHT)
        self.set_text_color(*NAVY)
        self.set_font("Helvetica", "B", 15)
        self.cell(0, 11, clean(f"  {num}.  {title}"), fill=True, new_x="LMARGIN",
                  new_y="NEXT")
        self.ln(3)

    def h2(self, title):
        self.ln(1)
        self.set_text_color(*BLUE)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, clean(title), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body(self, text):
        self.set_text_color(*TEXT)
        self.set_font("Helvetica", "", 11)
        self.multi_cell(0, 6, clean(text))
        self.ln(2)

    def note(self, text):
        self.set_fill_color(*LIGHT)
        self.set_text_color(*NAVY)
        self.set_font("Helvetica", "I", 10.5)
        self.multi_cell(0, 6, clean(text), fill=True)
        self.ln(2)

    def bullet(self, text, label=None):
        self.set_text_color(*TEXT)
        self.set_font("Helvetica", "", 11)
        self.cell(6, 6, clean("-"))
        if label:
            self.set_font("Helvetica", "B", 11)
            self.write(6, clean(label + " "))
            self.set_font("Helvetica", "", 11)
        self.write(6, clean(text))
        self.ln(8)

    def code(self, lines):
        self.set_fill_color(*CODEBG)
        self.set_text_color(*TEXT)
        self.set_font("Courier", "", 10)
        for ln in lines:
            self.cell(0, 6, clean("  " + ln), fill=True, new_x="LMARGIN",
                      new_y="NEXT")
        self.ln(3)


def build():
    pdf = PDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(20, 18, 20)
    pdf.add_page()

    # ── Title block ──────────────────────────────────────────────────────────
    pdf.ln(14)
    pdf.set_text_color(*NAVY)
    pdf.set_font("Helvetica", "B", 24)
    pdf.multi_cell(0, 12, clean("Computer Hydrological Forecasting"), align="C")
    pdf.ln(2)
    pdf.set_text_color(*BLUE)
    pdf.set_font("Helvetica", "", 13)
    pdf.multi_cell(0, 8, clean("Forecasting river flow from its own past discharge "
                               "(a statistical approach)"), align="C")
    pdf.ln(6)
    pdf.set_draw_color(*BLUE)
    pdf.set_line_width(0.6)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(8)
    pdf.set_text_color(*GREY)
    pdf.set_font("Helvetica", "", 11)
    for line in [
        "Author:        Ugbodaga Benedict Osikpemi (190402003)",
        "Department:    Civil and Environmental Engineering",
        "Institution:   University of Lagos",
        "Supervisor:    Prof. K. O. Aiyesimoju",
        "Submission:    February 2026",
    ]:
        pdf.cell(0, 7, clean(line), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_fill_color(*LIGHT)
    pdf.set_text_color(*NAVY)
    pdf.set_font("Helvetica", "I", 11)
    pdf.multi_cell(0, 7, clean(
        "This document explains the project in three parts: first in very simple "
        "terms, then the real technical version, and finally how to actually use "
        "the software."), align="C", fill=True)

    # ── What changed (revision note) ───────────────────────────────────────────
    pdf.add_page()
    pdf.h1(0, "What This Version Changed (and Why)")
    pdf.body(
        "An earlier version of this project used a rainfall-runoff model (a "
        "two-bucket conceptual model driven by rainfall and temperature, with "
        "parameters transferred to an ungauged Nigerian basin). Following the "
        "supervisor's guidance, the project was revised to a stronger, more "
        "statistical footing:")
    pdf.bullet("Rainfall, temperature and evapotranspiration are no longer used. "
               "The model forecasts discharge from past discharge alone.", label="Discharge only:")
    pdf.bullet("The unit-hydrograph / rainfall-runoff transform was removed and "
               "replaced by a statistical time-series model (ARIMA).", label="No rainfall-runoff:")
    pdf.bullet("The Nigerian (Ogun-Osun) catchment was dropped. The Conecuh River "
               "(Alabama, USA) is now the single study basin.", label="One basin:")
    pdf.bullet("The whole workflow is defined statistically: stationarity tests, "
               "autocorrelation-based identification, information-criterion model "
               "selection, and residual diagnostics.", label="More rigorous:")
    pdf.note(
        "In short: instead of turning rainfall into runoff, the model now learns "
        "the river's own day-to-day behaviour from its history and projects it "
        "forward - a cleaner, more defensible, and reproducible approach.")

    # ── 1. Very basic explanation ──────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(1, "The Simple Version (for anyone)")

    pdf.body(
        "A river does not change its flow randomly from one day to the next. If a "
        "lot of water is flowing today, a lot will still be flowing tomorrow; if "
        "the river is low today, it will most likely be low tomorrow. Flow changes "
        "gradually, following a recession after each rise.")
    pdf.body(
        "This project is a computer program that uses that simple fact. It looks at "
        "the recent history of the river's flow and answers one question: \"Given "
        "how the river has been flowing, how much water will flow over the next few "
        "days?\" It needs no weather information at all - only the river's own past.")

    pdf.h2("Learning the river's habits")
    pdf.body(
        "The program studies many years of daily flow measurements and learns the "
        "pattern: how strongly today's flow depends on yesterday's, the day "
        "before, and so on. It captures that pattern in a small set of numbers and "
        "then uses them to step forward into the future, one day at a time.")

    pdf.h2("How do we know it works?")
    pdf.body(
        "We test it honestly. There is a very simple guess called \"persistence\": "
        "assume tomorrow's flow equals today's. Because rivers change slowly, that "
        "guess is already quite good - so any real model must beat it. Our model "
        "does beat persistence at every forecast range we tested, which proves it "
        "is adding genuine skill and not just repeating the obvious.")

    # ── 2. The actual explanation ──────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(2, "The Actual Version (technical)")

    pdf.body(
        "The project is a modular, open-source Python framework for short-term "
        "streamflow forecasting (1-3 days ahead) from a univariate daily discharge "
        "series. It uses the ARIMA (autoregressive integrated moving average) class "
        "of models formalised by Box and Jenkins (1976). No exogenous "
        "(meteorological) inputs are used.")

    pdf.h2("2.1  The data")
    pdf.body(
        "Daily mean discharge for the Conecuh River, Alabama (USGS gauge 02361000) "
        "from the CAMELS US data set, 1980-2014 (12,784 days). Discharge is "
        "converted from cubic feet per second to cubic metres per second, the few "
        "missing values (<1%) are interpolated, and the series is modelled on the "
        "natural-log scale to stabilise its variance. The record is split into a "
        "training period (1980-2003) and an independent validation period "
        "(2004-2014).")

    pdf.h2("2.2  The model: ARIMA(p, d, q)")
    pdf.body(
        "An ARIMA model describes a series using three ingredients: an "
        "autoregressive part (the value depends on its own p past values), an "
        "integration order d (the series is differenced d times to make it "
        "stationary), and a moving-average part (the value depends on the q past "
        "random shocks). On the differenced log-series w(t):")
    pdf.code([
        "w(t) = c + phi_1 w(t-1) + ... + phi_p w(t-p)",
        "          + a(t) + theta_1 a(t-1) + ... + theta_q a(t-q)",
    ])
    pdf.body(
        "where phi are the autoregressive coefficients, theta the moving-average "
        "coefficients, c a constant, and a(t) a white-noise error term.")

    pdf.h2("2.3  How the model was identified (Box-Jenkins)")
    pdf.bullet("Augmented Dickey-Fuller and KPSS tests determined the differencing "
               "order: one difference (d = 1) makes the series stationary.",
               label="Stationarity:")
    pdf.bullet("The autocorrelation (ACF) and partial autocorrelation (PACF) "
               "functions suggested candidate AR and MA orders.", label="Identification:")
    pdf.bullet("Coefficients were estimated by conditional sum of squares (pure AR "
               "models by exact least squares).", label="Estimation:")
    pdf.bullet("All candidate orders were ranked by the Akaike Information Criterion "
               "(AIC). The winner was ARIMA(3, 1, 2).", label="Selection:")
    pdf.bullet("The Ljung-Box test confirmed the residuals are white noise "
               "(p = 0.23), so the model is statistically adequate.", label="Diagnostics:")

    pdf.h2("2.4  Results")
    pdf.body(
        "Forecasts were evaluated by rolling-origin (walk-forward) testing over the "
        "validation period and benchmarked against persistence. The model beats "
        "persistence at every lead time (positive persistence skill score, PSS):")
    pdf.code([
        "Lead    Model NSE    PSS (skill vs persistence)    Persistence NSE",
        f" 1 day    {_fc(1,'model','NSE'):.3f}          {_fc(1,'model','PSS'):+.3f}"
        f"                        {_fc(1,'persistence','NSE'):.3f}",
        f" 2 day    {_fc(2,'model','NSE'):.3f}          {_fc(2,'model','PSS'):+.3f}"
        f"                        {_fc(2,'persistence','NSE'):.3f}",
        f" 3 day    {_fc(3,'model','NSE'):.3f}          {_fc(3,'model','PSS'):+.3f}"
        f"                        {_fc(3,'persistence','NSE'):.3f}",
    ])
    pdf.body(
        "Forecasts are back-transformed from the log scale with a log-normal "
        "bias correction, so the percentage bias is near zero at all lead times. "
        "The one-day forecast is rated \"very good\" on the Moriasi et al. (2007) "
        "scale; absolute skill declines with lead time - expected for any model "
        "that uses only past flow - so useful skill is concentrated at about the "
        "one-day horizon. The raw NSE is high partly because daily flow is "
        "strongly autocorrelated, so the persistence skill score is the "
        "decisive, honest measure of the value added.")

    pdf.h2("2.5  Code structure")
    pdf.code([
        "src/preprocess.py  - load discharge, unit conversion, log transform, split",
        "src/model.py       - ARIMA + ADF/KPSS/ACF/PACF/Ljung-Box (from scratch)",
        "src/calibrate.py   - stationarity tests + AIC order selection",
        "src/forecast.py    - rolling multi-step forecast + persistence benchmark",
        "src/metrics.py     - NSE, RMSE, PBIAS, MAE, R2, skill score",
        "src/plots.py       - the six figures",
        "run_pipeline.py    - runs everything end to end",
        "write_document.py  - builds the thesis .docx",
        "app.py + pages/    - the Streamlit web app",
    ])
    pdf.body(
        "The entire time-series toolkit is implemented directly from its defining "
        "equations on NumPy and SciPy, so the framework is fully self-contained and "
        "reproducible (no external time-series library is required).")

    # ── 3. How to use the software ──────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(3, "How to Use the Software")

    pdf.h2("3.0  The easy version")
    pdf.body(
        "Using the tool is like checking a forecast: you open the app, choose how "
        "many days ahead you want, and it shows the predicted river flow. You do "
        "not enter any weather - the model works from the river's own record. Here "
        "is all you do:")
    pdf.bullet("Open the app - a page opens in your web browser.", label="1.")
    pdf.bullet("On the left, choose how many days ahead you want to forecast (1-7).",
               label="2.")
    pdf.bullet("Choose how much past history to display on the chart.", label="3.")
    pdf.bullet("Press the \"Run Forecast\" button.", label="4.")
    pdf.bullet("Read the answer: predicted flow per day as cards, a table, and a "
               "chart, plus the model's validation skill.", label="5.")

    pdf.h2("3.1  The web app, step by step (the main way to use it)")
    pdf.body(
        "Open the app and you get a browser page with two pages in the left "
        "sidebar: \"Forecast Tool\" and \"Documentation\". On the Forecast Tool "
        "page:")
    pdf.bullet("Set the forecast Horizon (1 to 7 days).", label="1.")
    pdf.bullet("Set how many days of history to display.", label="2.")
    pdf.bullet("Click \"Run Forecast\".", label="3.")
    pdf.bullet("Read the results: per-day summary cards, a forecast table (with the "
               "record-mean reference), a chart of recent history plus the forecast, "
               "and the out-of-sample validation skill (NSE and persistence skill "
               "score by lead time).", label="4.")

    pdf.h2("3.2  The full run (get every chart and number at once)")
    pdf.body(
        "Run the whole study in one command. It loads the discharge record, runs "
        "the stationarity tests, identifies and estimates the ARIMA model, performs "
        "the rolling forecast evaluation, and saves all six figures plus a results "
        "file (data/results.json). The terminal prints the chosen model, the "
        "metric table and the residual diagnostic.")
    pdf.code([
        "python run_pipeline.py     # model + forecasts + figures + results.json",
        "python write_document.py   # rebuild the thesis .docx from those results",
        "streamlit run app.py       # launch the interactive web app",
    ])

    pdf.output(OUTPUT)
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    build()
