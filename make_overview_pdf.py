"""
make_overview_pdf.py — Generate a plain-English project overview PDF.

Sections:
  0. What changed on 2026-08-12 (gauge correction + monthly/3-variable/
     stochastic pivot)
  1. Q&A: every question the supervisor has actually asked, with a plain
     answer and a pointer to where it's addressed in the app/report
  2. Very basic explanation (high-school level)
  3. The actual explanation (builds on #2, technical)
  4. How to use the software

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

    def qa(self, question, answer, pointer):
        self.set_x(self.l_margin)
        self.set_fill_color(*LIGHT)
        self.set_text_color(*NAVY)
        self.set_font("Helvetica", "B", 11.5)
        self.multi_cell(0, 6.5, clean("Q: " + question), fill=True)
        self.set_x(self.l_margin)
        self.set_text_color(*TEXT)
        self.set_font("Helvetica", "", 11)
        self.multi_cell(0, 6, clean(answer))
        self.set_x(self.l_margin)
        self.set_text_color(*BLUE)
        self.set_font("Helvetica", "I", 10)
        self.multi_cell(0, 6, clean("-> Where to look: " + pointer))
        self.ln(4)

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
        "The modelling approach pivoted on 2026-08-12, on the supervisor's direct "
        "instruction, and it matters for reading everything that follows correctly.")
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

    pdf.h2("The report was then put through two rounds of critical review")
    pdf.body(
        "After the pivot above, the thesis text was independently reviewed twice "
        "(each round: three reviewer personas instructed to challenge why, how, and "
        "where every claim came from, not just skim the document). Real, checkable "
        "problems came out of both rounds. A table-numbering gap, a data-vs-text "
        "arithmetic mismatch, and two backwards test-result claims (ARCH and "
        "Jarque-Bera) were fixed directly. Three deeper methodological gaps -- no "
        "worked reservoir/spillway design example, an unsupported cross-basin "
        "transfer claim, and an unstated discharge/stage independence caveat -- were "
        "resolved with real supplementary analysis rather than softened wording (see "
        "'On generalisation and design use' in Section 2). Three other requests -- "
        "make the persistence skill score the headline metric, reintroduce an "
        "explicit Duan bias-correction step, and drop the qualification on the "
        "cross-basin claim -- were considered and declined, because each would have "
        "reintroduced exactly the point-forecast framing the 2026-08-12 pivot moved "
        "away from.")

    # ── 1. Questions and answers from last review ───────────────────────────────
    pdf.add_page()
    pdf.h1(1, "Questions and Answers From Last Review")
    pdf.body(
        "This is the actual defence-style review session that drove the 2026-08-12 "
        "pivot above, extracted question by question from the recording, with what "
        "the project does about each one today. Some overlap with the curated "
        "questions list in the next section; this is the direct, literal record.")
    pdf.qa(
        "Why are you using ARIMA? AR alone? MA alone? ARMA? ARIMA? ARIMAX? There are "
        "many variants -- why introduce all of them?",
        "Because they each answer a different question about a series' memory (past "
        "values only, past shocks only, both, both plus differencing, both plus an "
        "outside variable), and the project doesn't just assert ARIMA -- it runs an "
        "explicit family comparison in the literature review and lets an "
        "AIC-based grid search choose the specific structure per variable from the "
        "data itself, not from preference.",
        "Report Chapter 2, Section 2.4.")
    pdf.qa(
        "Why are you using daily data with ARIMA? You won't gain anything from the "
        "differencing... but if you difference monthly flows, you actually gain "
        "something, because it removes the seasonality.",
        "Fixed, exactly along those lines -- the whole pipeline now runs at a "
        "monthly timestep. Daily discharge doesn't have a seasonal cycle for "
        "differencing to usefully remove; monthly does.",
        "Report Chapter 1, Section 1.5; Chapter 3, Section 3.1.")
    pdf.qa(
        "How do you estimate the parameters? The p, d, q you mentioned are not the "
        "parameters -- that's just the order. How do you estimate the "
        "autoregressive component? The moving average parameters? How did you get "
        "it?",
        "p, d, q are the order (structure), chosen by AIC. The actual parameters -- "
        "the AR (phi) and MA (theta) coefficients -- are estimated by conditional "
        "sum of squares, and every one is reported with a standard error, not just "
        "a value.",
        "Report Chapter 3, Section 3.5; Chapter 4, Table 5; app 'For the curious' panel.")
    pdf.qa(
        "Can you even forecast? 'I can only forecast 7 days' -- that's terrible. "
        "Why?",
        "That was a real bug (a leftover default), now removed. The app forecasts "
        "any user-chosen future range via explicit 'predict from/to' month-and-year "
        "controls.",
        "App: Predict from / to controls.")
    pdf.qa(
        "Your data is up to 2014 -- how do you now know 2015 is correct? How do you "
        "check that? How do we know it's not garbage that you have forecasted?",
        "You can't check one stochastic run against one real sequence -- every run "
        "differs by design. What's actually checkable, and is checked, is whether "
        "the historical record's statistical properties (mean, variability, "
        "seasonality, drought length, peak size) fall within the range a "
        "1,000-member synthetic ensemble produces.",
        "Report Section 3.6, Section 4.6.")
    pdf.qa(
        "The data is bulky -- 35 years, 365 days a year -- is that bulky for a "
        "computer?",
        "Not for a computer, no, and that was never really the constraint. The "
        "reason the project moved to monthly wasn't data volume -- it was that "
        "differencing only does useful work (removing seasonal drift) at a monthly "
        "step, which is the point made in the previous answer.",
        "See the daily-vs-ARIMA answer above.")
    pdf.qa(
        "Which year to which year did you use -- 1980 to 2014?",
        "Yes -- 420 months, split 1980-2003 (288 months) to identify order and "
        "estimate parameters, and 2004-2014 (132 months) held back entirely for "
        "validation.",
        "Report Chapter 3, Section 3.4.")
    pdf.qa(
        "When you're forecasting stochastic data, you can't compare to real data -- "
        "each forecast is different, so how can you compare it to 2015? It's "
        "meaningless. You can only compare the parameters -- the properties -- of "
        "what you forecast to the properties of the original data.",
        "Agreed, and that's exactly the current validation design: the project "
        "never compares one synthetic run to the one thing that actually happened. "
        "It compares the ensemble's statistical properties to history's. This is "
        "the core idea of the whole 2026-08-12 rebuild.",
        "Report Section 4.6, Table 7.")
    pdf.qa(
        "Why are you using whatever river in the US? Have you checked for monthly "
        "data in Nigeria that you didn't find?",
        "Yes -- NIHSA was checked directly, not skipped, and couldn't give a firm "
        "price or delivery date inside the project deadline. Conecuh was already "
        "downloaded, verified, and clean, so it became the working basin while the "
        "Nigerian request stayed open -- a disclosed trade-off.",
        "Report Chapter 1, Section 1.5; 'Why Conecuh, specifically' below.")
    pdf.qa(
        "This business of 'not enough data' isn't really relevant -- it's precisely "
        "because you don't have enough data that you're forecasting. If you had "
        "huge data, why would you be forecasting at all?",
        "Agreed -- this is the actual justification given for stochastic hydrology "
        "in the literature review, not '35 years is too little' or 'too much'.",
        "Report Chapter 2 (Matalas, 1967).")
    pdf.qa(
        "Forecast rainfall from rainfall, runoff from runoff -- there's no "
        "difference. Your model doesn't change, it's the same model. You should be "
        "able to estimate the parameters for whatever data you put in.",
        "That is exactly how it's built: one ARIMA implementation, applied "
        "unmodified to discharge, rainfall, and stage -- only the fitted "
        "coefficients differ between them, not the code.",
        "Report Section 2.4, Section 3.2; app: switch tabs between the three variables.")
    pdf.qa(
        "You have to show that the ARIMA model fits the data -- ARIMA can't be "
        "used for just anything, you must show the data itself fits it, not "
        "assume it.",
        "Every variable runs through ADF and KPSS stationarity tests before a "
        "model is chosen, and the evidence -- not just the conclusion -- is "
        "reported and shown live in the app.",
        "Report Section 3.5, Section 4.2; app 'For the curious' -> stationarity evidence line.")

    # ── 2. Questions to expect, and where the answer lives ──────────────────────
    pdf.add_page()
    pdf.h1(2, "Questions To Expect, And Where The Answer Lives")
    pdf.body(
        "Every question below is one the supervisor has actually asked, in the exact "
        "defence session that drove this rewrite. Each answer is short on purpose -- "
        "say the sentence, then point at the app or the report page and let it do the "
        "rest of the talking.")

    pdf.h2("On the choice of model")
    pdf.qa(
        "Why ARIMA, and not AR alone, MA alone, ARMA, or ARIMAX?",
        "AR alone assumes only past values matter; MA alone assumes only past random "
        "shocks matter; ARMA combines both but needs the series already stationary; "
        "ARIMA adds differencing on top of ARMA for series that are not; ARIMAX adds "
        "an outside variable. We don't pick by preference -- the order-selection step "
        "tests AR-only, MA-only and mixed forms for every one of the three variables "
        "and keeps whichever the Akaike Information Criterion scores best. ARIMAX was "
        "ruled out deliberately: each variable is forecast from its own past only, so "
        "there is no outside variable to add.",
        "Report Chapter 2, Section 2.4 (family comparison, explicit ARIMAX "
        "paragraph). App: each model's actual (p,d,q) is shown under 'For the "
        "curious'.")
    pdf.qa(
        "Shouldn't the same model work on rainfall too, not just discharge?",
        "It does. The same code, unchanged, independently fits discharge, rainfall "
        "and river stage -- three different variables, three different fitted "
        "models, one shared method.",
        "App: switch the River flow / Rainfall / River level tabs -- identical "
        "layout each time, different numbers. Report Chapter 2, Section 2.4; "
        "Chapter 3, Section 3.2.")

    pdf.h2("On daily versus monthly")
    pdf.qa(
        "Why were you using daily data with ARIMA?",
        "We aren't, any more. Differencing -- the 'I' in ARIMA -- only does real "
        "work when there is seasonal drift to remove, and that shows up at a "
        "monthly timestep, not day to day. The whole pipeline was rebuilt on "
        "monthly data for exactly this reason.",
        "App: left-hand 'Good to know' panel. Report Chapter 1, Section 1.5; "
        "Chapter 3, Section 3.1.")

    pdf.h2("On parameter estimation (asked the most, and the most pointed)")
    pdf.qa(
        "How do you estimate the parameters? p, d, q are not the parameters.",
        "Correct, and now answered properly. p, d, q are the order -- the shape of "
        "the model, chosen by AIC. The actual parameters are the phi (AR) and theta "
        "(MA) coefficients, estimated by conditional sum of squares (exact least "
        "squares when there's no MA term). Every coefficient now carries a standard "
        "error too, so it's clear how precisely each one is known, not just its "
        "value.",
        "App: 'For the curious' -> a coefficient table per variable, value and "
        "standard error side by side. Report Chapter 3, Section 3.5; Chapter 4, "
        "Section 4.4 (Table 5 and Figure 5).")
    pdf.qa(
        "You must show the data actually fits ARIMA -- not assume it.",
        "Each variable is run through the Augmented Dickey-Fuller and KPSS "
        "stationarity tests before any model is chosen, and the result -- not just "
        "the conclusion -- is shown.",
        "App: 'For the curious' -> stationarity evidence line per variable "
        "(ADF/KPSS statistics). Report Chapter 3, Section 3.5; Chapter 4, "
        "Section 4.2.")

    pdf.h2("On whether it can even forecast")
    pdf.qa(
        "Can it forecast? Why is it limited to 7 days?",
        "That cap is gone -- it was a leftover default, not a real limit of the "
        "method. The app now takes an explicit 'predict from [month/year] to "
        "[month/year]' range, not a horizon length off a fixed anchor, so it can "
        "target any future window -- 2030-2035, 2050-2060, whatever is asked for.",
        "App: the 'Predict from / to' controls.")

    pdf.h2("On checking whether a forecast is correct")
    pdf.qa(
        "Your data stops at 2014 -- how do you know a forecast into 2015 is "
        "correct? How do you check it?",
        "You cannot check a single stochastic forecast against a single real "
        "sequence and call it right or wrong -- each run of the model produces a "
        "different plausible sequence, so there is no one number to be 'correct'. "
        "What's checkable is whether the real historical record's properties -- "
        "average, variability, seasonal pattern, drought length, peak size -- fall "
        "inside the range that a thousand simulated versions produce.",
        "App: the shaded band on every chart, plus the 'track record' score on "
        "each card (e.g. 7/7). Report Chapter 3, Section 3.6; Chapter 4, Section "
        "4.6.")
    pdf.qa(
        "When forecasting stochastic data, can't you only compare properties, not "
        "the forecast itself, to the original data?",
        "Yes -- that is exactly what changed. This is no longer a point-forecast "
        "model scored against one observed sequence; it is a stochastic generator "
        "scored by whether its output's statistical properties match history.",
        "Same as above -- this is the core of the whole 2026-08-12 rebuild.")
    pdf.qa(
        "Isn't 35 years of data 'not enough', or daily data 'too much' -- which is "
        "it?",
        "Neither framing is the point. Forecasting exists precisely because the "
        "future is never in hand, however much history you have; 35 years is "
        "enough to estimate a model, and stochastic simulation is what you do with "
        "a finite past, not a reason to wait for more of it.",
        "Report Chapter 2 (stochastic hydrology literature, Matalas 1967).")

    pdf.h2("On the study basin")
    pdf.qa(
        "Why a US river? Why not a Nigerian one -- that's a standard question the "
        "panel will ask.",
        "The Nigerian custodian (NIHSA) was checked directly, not skipped -- see "
        "the next section for the specific numbers. Short version: it could not "
        "give a firm price or delivery date inside the project timeline, so the "
        "pipeline was built and validated on the Conecuh record, which was "
        "already in hand, verified, and clean. The Nigerian request stayed open as "
        "a possible future swap. This is a disclosed trade-off, not a hidden one -- "
        "the thing actually being demonstrated is that the method generalises "
        "across variables at this basin; a supplementary check (Section 4.8 of the "
        "report) has since tested whether the procedure also generalises across "
        "basins, with an honest, qualified answer -- see 'On generalisation and "
        "design use' below.",
        "Report Chapter 1, Section 1.5. See 'Why Conecuh, specifically' below for "
        "the full reasoning.")

    pdf.h2("Why Conecuh, specifically: the Nigerian data attempt")
    pdf.body(
        "NIHSA (Nigeria Hydrological Services Agency) has a real online request "
        "form (nihsa.gov.ng/data-request) stating 5-7 working days turnaround for "
        "straightforward requests, but the request is not free -- cost is "
        "assessed per request and only communicated after NIHSA reviews it, so "
        "neither a firm price nor a true delivery date could be known in advance, "
        "inside a project deadline. CAMELS, by contrast, already provides free, "
        "ready-to-use monthly data for hundreds of US basins -- which is exactly "
        "what made it possible to test transferability on two more basins (the "
        "cross-basin check, Section 4.8) at zero cost and no wait. The method "
        "itself doesn't care which country supplied the numbers: it's the same "
        "ARIMA procedure applied to whatever series is in front of it, so if the "
        "Nigerian data comes through, it would run on a Nigerian basin exactly as "
        "it already runs on Conecuh and the two supplementary US basins. See "
        "DATA_OPTIONS.md for the full investigation.")

    pdf.h2("On generalisation and design use (added after the 2026-08-13 review rounds)")
    pdf.qa(
        "Does this actually transfer to other basins, or is it just this one?",
        "The identical identification-and-estimation procedure was run, unmodified, "
        "on two more CAMELS basins in climate regimes distinct from Conecuh's humid "
        "subtropical setting -- the Great Basin (arid interior West) and New England "
        "(humid continental, snow-influenced). It ran cleanly on both, for both "
        "discharge and rainfall, without a single code change. What did not transfer "
        "was the specific pattern found at Conecuh: discharge shows strong AR(1) "
        "persistence at all three basins but fails its residual test at all three, "
        "and rainfall persistence genuinely differs by basin -- near zero at "
        "Conecuh, strong at the other two. Two of the four new fits also showed real "
        "numerical warning signs (coefficients pinned at the optimiser's boundary, "
        "standard errors essentially zero) -- evidence the pipeline's own diagnostics "
        "catch bad fits rather than reporting them as good, which is the honest "
        "reading of this result.",
        "Report Chapter 4, Section 4.8 (Table 9, Figure 9); cross_basin_check.py, "
        "cross_basin_figure.py.")
    pdf.qa(
        "You keep invoking reservoir and spillway design as the motivation -- can "
        "you actually show a design number?",
        "Yes, now. Five hundred synthetic 30-year discharge traces are generated "
        "from the already-fitted discharge model; annual maximum monthly discharge "
        "is pooled across all of them (15,000 values), and return-period design "
        "discharges are read directly off that pooled distribution using the "
        "standard plotting-position method (Chow, Maidment and Mays, 2008). The "
        "100-year design discharge comes out to about 376 cubic metres per second, "
        "against a 35-year observed peak of about 110. This is explicitly "
        "illustrative -- a real design study would use a formally chosen "
        "exceedance-probability standard and cross-check several methods -- but it "
        "is a real, reproducible calculation, not just an invoked application.",
        "Report Chapter 4, Section 4.6 (Table 8); design_discharge_example.py.")

    # ── 2. Very basic explanation ──────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(3, "The Simple Version (for anyone)")

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

    # ── 3. The actual explanation ──────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(4, "The Actual Version (technical)")

    pdf.body(
        "The project is a modular, open-source Python framework for monthly "
        "hydrological forecasting. It fits three independent ARIMA (autoregressive "
        "integrated moving average) models, one each for discharge, rainfall and "
        "stage, using the Box-Jenkins methodology, and validates each by the "
        "statistical properties its stochastic output reproduces relative to the "
        "historical record. No variable is used to forecast another, and no "
        "exogenous (meteorological forecast) input is used.")

    pdf.h2("4.1  The data")
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

    pdf.h2("4.2  The model: three independent ARIMA(p, d, q)")
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

    pdf.h2("4.3  How each model was identified (Box-Jenkins)")
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

    pdf.h2("4.4  Stochastic ensembles and property-based validation")
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

    pdf.h2("4.5  Code structure")
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
    pdf.h1(5, "How to Use the Software")

    pdf.h2("5.0  The easy version")
    pdf.body(
        "Open the app -- it's called \"River Outlook\" in the top navigation. Pick "
        "a future month-and-year range to predict, and press \"Get the "
        "Outlook\". One click forecasts all three variables together -- you don't "
        "pick one first. You'll see bands of plausible futures, not single lines "
        "-- and they'll look slightly different every time you press the button, "
        "because the model is honestly stochastic. Here is all you do:")
    pdf.bullet("Open the app - a page opens in your web browser.", label="1.")
    pdf.bullet("In the centre panel, pick a range preset or set \"Predict from\" "
               "and \"to\" month and year directly.", label="2.")
    pdf.bullet("Press the \"Get the Outlook\" button.", label="3.")
    pdf.bullet("Read the answer: a compact outlook card for each of the three "
               "variables on the right, and a chart with the plain-language story "
               "behind each one in the centre.", label="4.")

    pdf.h2("5.1  The web app, step by step (the main way to use it)")
    pdf.body(
        "Open the app and you get a browser page with two tabs along the top: "
        "\"River Outlook\" and \"How This Works\". The River Outlook page is laid "
        "out in three panels -- a left panel with context and quick facts, a "
        "centre panel with the controls, charts and plain-language story, and a "
        "right panel with a compact outlook card per variable. On the River "
        "Outlook page:")
    pdf.bullet("Pick a jump-to-range preset (e.g. \"2030 - 2035\"), or set "
               "\"Predict from\" and \"to\" directly with the month dropdown and "
               "year field (year has -/+ stepper buttons, from 2015 up to 2200).",
               label="1.")
    pdf.bullet("Click \"Get the Outlook\" -- this runs all three variables "
               "(discharge, rainfall, stage) at once, not one at a time.",
               label="2.")
    pdf.bullet("Read the results: a compact card per variable on the right (trend, "
               "level, track record), and in the centre a tab per variable with a "
               "chart (recent observed history up to Dec 2014, the synthetic "
               "uncertainty band, and the expected path) plus a fill-in-the-blanks "
               "explanation sentence underneath it.", label="3.")
    pdf.bullet("Open \"For the curious\" at the bottom of the centre panel for the "
               "actual numbers behind each model: the AR/MA coefficients with "
               "their standard errors, the stationarity test evidence, and the "
               "full property-based validation table.", label="4.")

    pdf.h2("5.2  The full run (get every chart and number at once)")
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
