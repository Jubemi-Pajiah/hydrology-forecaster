"""
make_overview_pdf.py — Generate a plain-English project overview PDF.

Sections:
  0. What changed on 2026-08-12 (gauge correction + monthly/3-variable/
     stochastic pivot)
  1. Very basic explanation (high-school level)
  2. The actual explanation (builds on #1, technical)
  3. How to use the software

This project forecasts discharge, rainfall and stage -- three independent
monthly ARIMA models, each from that variable's own past only -- and
validates each by the statistical properties a stochastic ensemble
reproduces relative to the historical record.

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

VARS = ["discharge", "rainfall", "stage"]
VAR_UNIT = {"discharge": "m3/s", "rainfall": "mm/month", "stage": "m"}


def _v(variable, *keys, default=0):
    try:
        node = R["variables"][variable]
        for k in keys:
            node = node[k]
        return node
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
    pdf.multi_cell(0, 8, clean("Three independent monthly ARIMA models -- discharge, "
                               "rainfall, stage -- validated by stochastic properties, "
                               "not point comparison"), align="C")
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
        "the software. It starts with what changed most recently, since that's "
        "what makes everything after it correct."), align="C", fill=True)

    # ── What changed (revision note) ───────────────────────────────────────────
    pdf.add_page()
    pdf.h1(0, "What Changed Most Recently (and Why)")
    pdf.body(
        "Two things changed on 2026-08-12, on the supervisor's direct instruction, "
        "and both matter for reading everything that follows correctly.")
    pdf.h2("A data error was found and corrected")
    pdf.body(
        "Every earlier version of this project used USGS gauge 02361000, believing "
        "it was the Conecuh River. It is not: NWIS confirms that gauge is the "
        "Choctawhatchee River near Newton, AL, a different river entirely. A search "
        "turned up the real Conecuh gauge -- USGS 02371500, Conecuh River at "
        "Brantley, AL -- which is also a genuine CAMELS basin, and has a longer, "
        "cleaner record than the one mistakenly used before (discharge back to "
        "1937 rather than 1980, still actively updating). All data was re-pulled "
        "under the correct gauge, and every reference to the old gauge number in "
        "the live code and this report was corrected.")
    pdf.h2("The modelling approach pivoted")
    pdf.bullet("Differencing only does useful work -- removing seasonality -- at a "
               "monthly timestep, not a daily one, on a river that never really "
               "trends day to day.", label="Monthly, not daily:")
    pdf.bullet("Discharge, rainfall and stage are each modelled independently, to "
               "show the same ARIMA method generalises across variable types, not "
               "just discharge.", label="Three variables, not one:")
    pdf.bullet("A stochastic model's individual forecasts are not meant to match "
               "the one thing that actually happened; only its statistical "
               "properties -- mean, variability, seasonality, drought duration, "
               "peak size -- should match history.", label="Stochastic validation:")
    pdf.note(
        "An even earlier version of this project (before either of the above) used "
        "a rainfall-runoff model on a Nigerian basin; that was replaced by the "
        "ARIMA approach on the same supervisor's instruction, and is not revisited "
        "here -- see CLAUDE.md and archive/ for that history if needed.")

    # ── 1. Very basic explanation ──────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(1, "The Simple Version (for anyone)")

    pdf.body(
        "A river does not change from one month to the next by pure chance. A wet "
        "month tends to follow other wet months in the same season; a dry spell "
        "tends to persist for a while once it starts. This project builds three "
        "small computer models -- one for how much water flows in the river, one "
        "for how much rain falls on its catchment, and one for how high the river "
        "runs -- and each one learns its own variable's habits from decades of "
        "monthly history. None of them needs a weather forecast; each works from "
        "its own past alone.")
    pdf.body(
        "Because rivers, rainfall and river levels are naturally unpredictable "
        "(that's what \"stochastic\" means here), the model doesn't try to name the "
        "one exact number that will happen next month. Instead it generates a "
        "thousand plausible versions of what could happen, and the honest question "
        "asked of it is: do the ordinary and extreme features of those thousand "
        "versions -- how wet, how dry, how variable, how seasonal -- look like the "
        "real history? That is a much fairer test of a model that admits the "
        "future is uncertain than asking it to guess one specific number correctly.")

    pdf.h2("How do we know it works?")
    pdf.body(
        "For each of the three variables, we held back eleven years of real data "
        "(2004-2014) that the model never saw while being built, generated a "
        "thousand synthetic versions of what those eleven years could have looked "
        "like, and checked seven different properties of the real data -- its "
        "average, its variability, how extreme its wettest and driest spells were, "
        "and so on -- against the range the thousand synthetic versions produced. "
        "Discharge and rainfall passed on all seven; river stage passed on six of "
        "seven, and the one it missed (its average level) is reported honestly "
        "rather than hidden.")

    # ── 2. The actual explanation ──────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(2, "The Actual Version (technical)")

    pdf.body(
        "The project is a modular, open-source Python framework for monthly "
        "hydrological forecasting. It fits three independent ARIMA (autoregressive "
        "integrated moving average) models, one each for discharge, rainfall and "
        "stage, using the Box-Jenkins methodology, and validates each by the "
        "statistical properties its stochastic output reproduces relative to the "
        "historical record. No variable is used to forecast another, and no "
        "exogenous (meteorological forecast) input is used.")

    pdf.h2("2.1  The data")
    pdf.body(
        f"Monthly discharge (m3/s), rainfall (mm/month) and stage (m) for the "
        f"Conecuh River at Brantley, Alabama (USGS gauge 02371500 -- verified "
        f"directly against USGS NWIS, see page 2), 1980-2014 "
        f"({_v('discharge','n_months')} months). Discharge and stage come from "
        f"USGS NWIS; rainfall is the Daymet basin-mean product from the CAMELS "
        f"archive, chosen because it is the only one of three available rainfall "
        f"products with zero missing days across the full record. All three "
        f"series are strictly positive throughout, so each is modelled on the "
        f"natural-log scale. The record is split into a training period "
        f"(1980-2003) and an independent validation period (2004-2014).")

    pdf.h2("2.2  The model: three independent ARIMA(p, d, q)")
    pdf.body(
        "An ARIMA model describes a series using three ingredients: an "
        "autoregressive part (the value depends on its own p past values), an "
        "integration order d (the series is differenced d times to make it "
        "stationary), and a moving-average part (the value depends on the q past "
        "random shocks). On the differenced log-series w(t), for each variable "
        "independently:")
    pdf.code([
        "w(t) = c + phi_1 w(t-1) + ... + phi_p w(t-p)",
        "          + a(t) + theta_1 a(t-1) + ... + theta_q a(t-q)",
    ])
    pdf.body(
        "where phi are the autoregressive coefficients, theta the moving-average "
        "coefficients, c a constant, and a(t) a white-noise error term. ARIMAX "
        "(which adds an exogenous predictor) was deliberately not used: each "
        "variable is forecast from its own past only, by design, so there is no "
        "exogenous driver to add.")

    pdf.h2("2.3  How each model was identified (Box-Jenkins)")
    pdf.bullet("Augmented Dickey-Fuller and KPSS tests determined the differencing "
               "order for each variable independently. For this basin, at the "
               "monthly timestep, all three came back d = 0.", label="Stationarity:")
    pdf.bullet("The autocorrelation (ACF) and partial autocorrelation (PACF) "
               "functions suggested candidate AR and MA orders.", label="Identification:")
    pdf.bullet("Coefficients were estimated by conditional sum of squares (pure AR "
               "models by exact least squares), each with a standard error -- "
               "answering not just what order was picked, but how precisely each "
               "coefficient is known.", label="Estimation:")
    pdf.bullet("All candidate orders were ranked by the Akaike Information "
               "Criterion (AIC).", label="Selection:")
    pdf.code([
        f"  Discharge : ARIMA{tuple(_v('discharge','order', default=[0,0,0]))}"
        f"   AIC={_v('discharge','aic'):.1f}",
        f"  Rainfall  : ARIMA{tuple(_v('rainfall','order', default=[0,0,0]))}"
        f"   AIC={_v('rainfall','aic'):.1f}",
        f"  Stage     : ARIMA{tuple(_v('stage','order', default=[0,0,0]))}"
        f"   AIC={_v('stage','aic'):.1f}",
    ])

    pdf.h2("2.4  Stochastic ensembles and property-based validation")
    pdf.body(
        "Rather than one deterministic forecast, each fitted model generates an "
        "ensemble of 1,000 synthetic monthly sequences over the validation period. "
        "Each sequence, and the actual historical record, is characterised by "
        "seven statistics: mean, standard deviation, skewness, month-to-month "
        "persistence, seasonal amplitude, longest dry spell, and peak value. A "
        "statistic is judged reproduced if the historical value falls within the "
        "ensemble's 5th-to-95th-percentile range.")
    pdf.code([
        "Variable     Properties within 90% envelope",
        f" Discharge    {_v('discharge','validation_n_within')} / {_v('discharge','validation_n_total')}",
        f" Rainfall     {_v('rainfall','validation_n_within')} / {_v('rainfall','validation_n_total')}",
        f" Stage        {_v('stage','validation_n_within')} / {_v('stage','validation_n_total')}",
    ])
    pdf.body(
        "Stage's one miss (its mean) is traced to residual seasonal structure the "
        "non-seasonal ARIMA specification does not fully capture -- visible "
        "independently as a failed Ljung-Box residual test for discharge and "
        "stage (p < 0.05, some autocorrelation remains) but not for rainfall "
        f"(p = {_v('rainfall','diagnostics','ljung_box','pvalue', default=0):.3f}). "
        "This is reported as an acknowledged limitation, not concealed: a "
        "validation procedure that always passes would not be doing useful work.")

    pdf.h2("2.5  Code structure")
    pdf.code([
        "src/preprocess.py  - monthly loaders: discharge, rainfall, stage",
        "src/model.py       - ARIMA + ADF/KPSS/ACF/PACF/Ljung-Box + std. errors",
        "src/calibrate.py   - stationarity tests + AIC order selection",
        "src/simulate.py    - stochastic synthetic-ensemble generation",
        "src/validation.py  - property-based validation vs. historical record",
        "src/plots.py       - the six figures (3-variable, monthly, stochastic)",
        "run_pipeline.py    - runs everything end to end, all 3 variables",
        "write_full_report.py + report_*.py - builds the full Ch1-5 report",
        "app.py + pages/    - the Streamlit web app",
    ])
    pdf.body(
        "The entire time-series toolkit -- ARIMA, stationarity tests, ACF/PACF, "
        "Ljung-Box, standard errors, stochastic simulation, property-based "
        "validation -- is implemented directly from first principles on NumPy and "
        "SciPy, so the framework is fully self-contained and reproducible (no "
        "external time-series library is required).")

    # ── 3. How to use the software ──────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(3, "How to Use the Software")

    pdf.h2("3.0  The easy version")
    pdf.body(
        "Open the app, pick a variable (discharge, rainfall or stage), pick a "
        "starting month and how many months ahead to look, and press Run "
        "Forecast. You'll see a band of plausible futures, not one line -- and "
        "that band will look slightly different every time you press the button, "
        "because the model is honestly stochastic. Here is all you do:")
    pdf.bullet("Open the app - a page opens in your web browser.", label="1.")
    pdf.bullet("On the left, pick the variable and the forecast origin month.",
               label="2.")
    pdf.bullet("Choose the horizon (months ahead) and how many synthetic "
               "replicates to generate.", label="3.")
    pdf.bullet("Press the \"Run Forecast\" button.", label="4.")
    pdf.bullet("Read the answer: a band of plausible outcomes as cards, a table, "
               "a chart, and the property-based validation results.", label="5.")

    pdf.h2("3.1  The web app, step by step (the main way to use it)")
    pdf.body(
        "Open the app and you get a browser page with two pages in the left "
        "sidebar: \"Forecast Tool\" and \"Documentation\". On the Forecast Tool "
        "page:")
    pdf.bullet("Choose the Variable (discharge, rainfall or stage).", label="1.")
    pdf.bullet("Choose the Forecast origin (month) and Horizon (months ahead).",
               label="2.")
    pdf.bullet("Click \"Run Forecast\".", label="3.")
    pdf.bullet("Read the results: per-month summary cards showing the median and "
               "90% band, a forecast table, a chart of recent history plus the "
               "synthetic band, and the property-based validation table showing "
               "how many statistics the model reproduces.", label="4.")

    pdf.h2("3.2  The full run (get every chart and number at once)")
    pdf.body(
        "Run the whole study in one command. It loads all three monthly series, "
        "runs the stationarity tests, identifies and estimates all three ARIMA "
        "models with standard errors, generates the stochastic ensembles, runs "
        "property-based validation, and saves all six figures plus a results "
        "file (data/results.json).")
    pdf.code([
        "python run_pipeline.py       # all 3 models + ensembles + figures",
        "python write_full_report.py  # rebuild the full Ch1-5 report .docx",
        "python make_overview_pdf.py  # rebuild this overview PDF",
        "streamlit run app.py         # launch the interactive web app",
    ])

    pdf.output(OUTPUT)
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    build()
