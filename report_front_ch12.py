"""
report_front_ch12.py — Front matter, Chapter One and Chapter Two.

The Chapter 1-3 draft supplied by the author described a lumped conceptual
rainfall-runoff model. That approach was superseded, on the supervisor's
instruction, by the discharge-only ARIMA model reported in Chapters Three to
Five. Chapters One and Two are therefore rewritten here onto the statistical
framing so that the report is internally consistent: the structure, argument and
voice of the draft are preserved, but the model family described is the one
actually built and evaluated.
"""

from docx.enum.text import WD_ALIGN_PARAGRAPH

from report_lib import (abbreviation, blank, body, bullet, centered,
                        chapter_heading, definition, equation, front_heading,
                        h1, list_of_figures, list_of_tables,
                        table_of_contents)

TITLE = "COMPUTER HYDROLOGICAL FORECASTING"
AUTHOR = "UGBODAGA BENEDICT OSIKPEMI"
MATRIC = "190402003"
SUPERVISOR = "Prof. K. O. Aiyesimoju"
HOD = "Dr. K. O. Olonade"
SUBMISSION_DATE = "FEBRUARY, 2026"


# ── front matter ─────────────────────────────────────────────────────────────

def write_title_page(doc):
    blank(doc, 2)
    centered(doc, TITLE, size=14, bold=True, caps=True, after=6)
    blank(doc, 3)
    centered(doc, "BY", bold=True, after=6)
    blank(doc, 2)
    centered(doc, AUTHOR, bold=True, caps=True, after=0)
    par = centered(doc, MATRIC, bold=True, after=6)
    par.runs[0].italic = True
    blank(doc, 3)
    centered(doc, "A PROJECT REPORT", bold=True, after=6)
    centered(doc, "SUBMITTED TO THE DEPARTMENT OF CIVIL AND ENVIRONMENTAL "
                  "ENGINEERING", bold=True, after=6)
    centered(doc, "IN PARTIAL FULFILMENT OF THE REQUIREMENTS FOR THE AWARD OF "
                  "BACHELOR OF SCIENCE (B.Sc.) DEGREE IN CIVIL AND "
                  "ENVIRONMENTAL ENGINEERING, UNIVERSITY OF LAGOS",
             bold=True, after=6)
    blank(doc, 3)
    centered(doc, "SUPERVISED BY", bold=True, after=6)
    centered(doc, SUPERVISOR, after=6)
    blank(doc, 3)
    centered(doc, SUBMISSION_DATE, bold=True, after=0)


def write_abstract(doc, R):
    dis = R["variables"]["discharge"]
    rain = R["variables"]["rainfall"]
    stage = R["variables"]["stage"]
    front_heading(doc, "ABSTRACT", page_break=False)
    sr = dis["synthetic_record"]
    alt = dis["seasonal_difference_alternative"]
    body(doc,
         "The sizing of reservoirs, spillways and channels depends on the "
         "frequency of rare flows, yet the gauged records available to "
         "estimate that frequency are typically only a few decades long "
         "and therefore contain few examples of the events that govern "
         "design. Stochastic hydrology addresses this by fitting a model "
         "to the observed record and generating from it a synthetic record "
         "of far greater length, statistically consistent with the "
         "observed one but containing many more realisations of its rare "
         "events. This study develops such a framework, implemented from "
         "first principles in Python and depending on the discharge record "
         "alone: no meteorological forcing, spatial catchment data, "
         "routing information or proprietary software is required at any "
         "stage. The methodology is demonstrated on thirty-five years of "
         f"monthly data (1980-2014, {dis['n_months']} months) for the "
         "Conecuh River at United States Geological Survey gauge 02371500, "
         "drawn from the CAMELS data set and the USGS National Water "
         "Information System.")
    body(doc,
         "The annual cycle, which accounts for approximately half the "
         "variance of the monthly record, is removed before fitting. Two "
         "standard treatments were applied and compared: seasonal "
         "differencing at lag twelve, and seasonal standardisation by the "
         "twelve monthly means and standard deviations. Both fit the "
         "observed record acceptably and neither is distinguishable from "
         "the other on residual diagnostics, but they differ decisively in "
         "what they imply beyond it. Seasonal differencing leaves an "
         "integrated process whose variance grows without bound, and a "
         f"{alt['record_years']}-year record generated from it drifts to a "
         f"mean of {alt['record_mean']:.2g} m³/s against an observed mean "
         f"of {dis['full_record']['historical_properties']['mean']:.1f}; "
         "standardisation leaves a stationary process, from which a record "
         "of any length remains a sample of the same distribution. The "
         "study adopts standardisation on that ground, and reports the "
         "comparison as a methodological result: the standard diagnostic "
         "apparatus of the Box–Jenkins procedure does not by itself "
         "distinguish a model suitable for generating long records from "
         "one that is not.")
    body(doc,
         "The deseasonalised series was tested jointly by the Augmented "
         "Dickey-Fuller and Kwiatkowski-Phillips-Schmidt-Shin tests and "
         "its order selected by a grid search minimising the Akaike "
         f"Information Criterion, giving {'ARIMA' + str(tuple(dis['order']))} "
         "for discharge, with every coefficient reported alongside its "
         "standard error and residuals that the Ljung–Box test does not "
         f"distinguish from white noise "
         f"(p = {dis['diagnostics']['ljung_box']['pvalue']:.3f}). "
         "Validation over the independent 2004-2014 period compares the "
         "statistical properties of a 1,000-member synthetic ensemble — "
         "mean, variability, skewness, month-to-month persistence, "
         "seasonal amplitude, dry-spell duration and peak value — with the "
         "observed record, rather than comparing a single simulated value "
         "with a single observed one, since the individual realisations of "
         "a stochastic model are not meant to match a specific observed "
         f"sequence. Discharge reproduced {dis['validation_n_within']} of "
         f"{dis['validation_n_total']} properties within the ensemble's 90 "
         "per cent envelope; the exception, seasonal amplitude, is traced "
         "to a measurable weakening of the annual cycle across the record "
         "itself rather than to a defect of the model.")
    body(doc,
         f"The validated model was used to generate {sr['n_months'] // 12:,} "
         f"years of synthetic monthly discharge, repeated "
         f"{sr['n_realisations']} times, yielding {sr['n_annual_maxima']:,} "
         "synthetic annual maxima from which design discharges were read "
         "by return period. The resulting estimates are internally "
         f"consistent and externally checkable: the 10-year value, "
         f"{sr['return_period_discharge']['10']:.0f} m³/s, is close to the "
         "largest monthly discharge observed in thirty-five years of "
         f"record, {dis['full_record']['historical_properties']['peak']:.0f} "
         "m³/s, which is approximately where a 10-year event should fall "
         "in a sample of that length. Applying the identical unmodified "
         "procedure to monthly rainfall and stage returned different "
         "orders and a different verdict on seasonality for each, "
         "confirming that what transfers between series is the method "
         "rather than any fitted model. The study demonstrates that a "
         "parsimonious, open-source and fully reproducible statistical "
         "framework can extend a short gauged record into one long enough "
         "to support a design calculation, without recourse to costly "
         "modelling platforms or dense meteorological monitoring.")


def write_certification(doc):
    front_heading(doc, "CERTIFICATION")
    body(doc,
         f"This is to certify that this project report titled “{TITLE}” "
         f"was carried out by {AUTHOR.title()} (Matriculation number "
         f"{MATRIC}) of the Department of Civil and Environmental "
         "Engineering, University of Lagos, under my supervision. The work "
         "embodies the candidate’s own research efforts and has not been "
         "previously submitted for the award of any degree or certificate. "
         "The results presented were obtained in accordance with the rules "
         "and regulations of this university and are hereby approved for "
         "submission.")
    blank(doc, 3)
    _signature(doc, SUPERVISOR, "Project Supervisor")
    blank(doc, 3)
    _signature(doc, HOD, "Head of Department")


def _signature(doc, name, role):
    body(doc, "…" * 20 + "\t\t" + "…" * 12,
         align=WD_ALIGN_PARAGRAPH.LEFT)
    body(doc, f"{name}\t\t\t\tDate", align=WD_ALIGN_PARAGRAPH.LEFT, bold=True)
    body(doc, role, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True)


def write_acknowledgement(doc):
    front_heading(doc, "ACKNOWLEDGEMENT")
    body(doc,
         "I wish to express my profound gratitude to the Almighty God for the "
         "gift of life and for granting me the strength, wisdom and "
         "perseverance required to complete this research. My sincere "
         f"appreciation goes to my supervisor, {SUPERVISOR}, for his "
         "invaluable guidance, constructive criticisms and support throughout "
         "the course of this work. His dedication to mentoring and his "
         "attention to detail have greatly shaped the quality of this project, "
         "not least in directing the study towards a disciplined statistical "
         "treatment of the discharge record.")
    body(doc,
         "I am also grateful to the academic and non-teaching staff of the "
         "Department of Civil and Environmental Engineering, University of "
         "Lagos, for providing a conducive learning environment.")
    body(doc,
         "I acknowledge my parents and family members for their prayers, "
         "encouragement and moral and financial support. To my friends and "
         "colleagues, especially those in the hydrology research group, I "
         "appreciate your motivation, discussions and companionship, which "
         "made this journey enjoyable. Finally, I thank all who contributed "
         "directly or indirectly to this project. May God bless you all.")


def write_dedication(doc):
    front_heading(doc, "DEDICATION")
    body(doc,
         "This project is dedicated to Almighty God, the giver of knowledge "
         "and wisdom, and to my beloved parents, whose love, prayers and "
         "sacrifices have been a constant source of inspiration.",
         align=WD_ALIGN_PARAGRAPH.CENTER)


ABBREVIATIONS = [
    ("ACF", "Autocorrelation Function"),
    ("ADF", "Augmented Dickey–Fuller (test)"),
    ("AIC", "Akaike Information Criterion"),
    ("AR", "Autoregressive"),
    ("ARIMA", "Autoregressive Integrated Moving Average"),
    ("ARIMAX", "Autoregressive Integrated Moving Average with Exogenous inputs"),
    ("ARMA", "Autoregressive Moving Average"),
    ("BIC", "Bayesian Information Criterion"),
    ("B.Sc.", "Bachelor of Science"),
    ("CAMELS", "Catchment Attributes and Meteorology for Large-sample Studies"),
    ("CSS", "Conditional Sum of Squares"),
    ("KPSS", "Kwiatkowski–Phillips–Schmidt–Shin (test)"),
    ("MA", "Moving Average"),
    ("MAE", "Mean Absolute Error"),
    ("MSE", "Mean Squared Error"),
    ("NSE", "Nash–Sutcliffe Efficiency"),
    ("PACF", "Partial Autocorrelation Function"),
    ("PBIAS", "Percent Bias"),
    ("PSS", "Persistence Skill Score"),
    ("R²", "Coefficient of Determination"),
    ("RMSE", "Root Mean Square Error"),
    ("USGS", "United States Geological Survey"),
    ("WMO", "World Meteorological Organization"),
]

TERMS = [
    ("Hydrological forecasting",
     "the prediction of future hydrological variables such as streamflow, "
     "water level or reservoir inflow from available observations."),
    ("Discharge",
     "the volume of water passing a river cross-section per unit time, "
     "reported here in cubic metres per second."),
    ("Time series",
     "a sequence of observations of a variable recorded at successive, "
     "equally spaced instants; here, monthly discharge, rainfall or stage."),
    ("Autocorrelation",
     "the correlation of a time series with a lagged copy of itself, which "
     "measures how strongly present values depend on past values."),
    ("Stationarity",
     "the property of a time series whose mean, variance and autocorrelation "
     "structure do not change over time."),
    ("Differencing",
     "the operation of replacing each observation by its change from the "
     "previous observation, used to remove drift and induce stationarity."),
    ("White noise",
     "a sequence of uncorrelated random values with zero mean and constant "
     "variance; the residuals of an adequate model should resemble it."),
    ("ARIMA model",
     "a univariate statistical model that expresses the present value of a "
     "differenced series as a linear combination of its own past values and "
     "of past random shocks."),
    ("Forecast lead time",
     "the interval between the moment a forecast is issued and the moment "
     "being predicted."),
    ("Persistence forecast",
     "the naive benchmark forecast that assumes no change, so that the "
     "predicted flow equals the most recently observed flow; a reference "
     "point in the wider literature (Section 2.7), not the validation "
     "method adopted in this study."),
    ("Stochastic ensemble",
     "a set of independently generated synthetic sequences from a fitted "
     "model, used here in place of a single deterministic forecast."),
    ("Property-based validation",
     "assessing a stochastic model by whether the statistical properties "
     "(mean, variance, persistence, seasonality, extremes) of its synthetic "
     "ensemble reproduce those of the historical record, rather than by "
     "comparing individual forecast and observed values."),
    ("Validation",
     "independent testing of a fitted model on a period withheld from model "
     "fitting, in order to assess genuine predictive reliability."),
    ("Nash–Sutcliffe efficiency",
     "a statistical measure of the proportion of the observed variance that "
     "is reproduced by a deterministic forecast; discussed in Section 2.7 as "
     "part of the wider verification literature."),
    ("Standard error",
     "a measure of the statistical uncertainty of an estimated coefficient, "
     "distinct from the coefficient's point estimate; reported for every "
     "AR/MA coefficient in this study (Section 3.5)."),
]


def write_abbreviations(doc):
    front_heading(doc, "ABBREVIATIONS")
    for short, long in ABBREVIATIONS:
        abbreviation(doc, short, long)


def write_definitions(doc):
    front_heading(doc, "DEFINITION OF TERMS")
    for term, meaning in TERMS:
        definition(doc, term, meaning)


def write_lists(doc):
    front_heading(doc, "LIST OF FIGURES")
    list_of_figures(doc)
    front_heading(doc, "LIST OF TABLES")
    list_of_tables(doc)
    front_heading(doc, "TABLE OF CONTENTS")
    table_of_contents(doc)


# ── Chapter One ──────────────────────────────────────────────────────────────

def write_chapter1(doc, eq):
    chapter_heading(doc, "ONE", "Introduction", page_break=False)

    h1(doc, "1.1 Background to the Study")
    body(doc,
         "Water resources systems — rivers, reservoirs, floodplains and "
         "aquifers — support domestic supply, irrigation, navigation, "
         "ecosystem health and industrial activity. The performance and safety "
         "of these systems are strongly influenced by the temporal variability "
         "of river flow. In engineering practice, the ability to characterise "
         "how a river's discharge, rainfall and water level are likely to "
         "vary over the coming months to years is fundamental to reservoir "
         "operation, the design of hydraulic structures such as spillways, "
         "and long-term water-resources planning.")
    body(doc,
         "Hydrological forecasting is the process of predicting future "
         "hydrological states, such as discharge, stage or reservoir inflow, "
         "from available observations. The forecast horizon may be short-term "
         "(from nowcasting to a few days), medium-term (weeks to months) or "
         "seasonal to multi-year. This study is concerned with the last of "
         "these: monthly-timestep forecasting over horizons of months to "
         "decades, the timescale relevant to reservoir sizing, spillway "
         "design and long-term water-resources planning (World "
         "Meteorological Organization, 2011), as distinct from the "
         "hours-to-days timescale of operational flood early warning, which "
         "is outside this study's scope.")
    body(doc,
         "Over the last few decades, advances in computing, numerical methods "
         "and software engineering have moved hydrological forecasting from "
         "manual, rule-based practice to computer-based modelling frameworks. "
         "A modern forecasting system typically comprises data acquisition and "
         "cleaning, model identification and estimation, forecast generation, "
         "and performance evaluation and visualisation. These components can "
         "be implemented entirely with open-source programming tools, which "
         "brings reproducibility, automation and transparency within reach of "
         "any engineer with a standard computer.")
    body(doc,
         "Two broad families of model are available for this purpose. "
         "Process-based models represent the physical transformation of "
         "rainfall into runoff through catchment storages and fluxes; they "
         "require meteorological forcing, and often spatial data on soils, "
         "land cover and topography, together with the calibration of "
         "parameters that cannot be measured directly. Statistical, or "
         "data-driven, models instead infer the forecast relationship directly "
         "from the observed record (Solomatine & Ostfeld, 2008). The second "
         "family is particularly attractive at short lead times, for a reason "
         "that is physical rather than merely convenient: daily river flow is "
         "a strongly autocorrelated process, so that the flow observed today "
         "already carries a great deal of information about the flow that will "
         "occur tomorrow. A model that exploits this temporal dependence "
         "directly can forecast the river from its own history alone.")
    body(doc,
         "Despite the advances noted above, the adoption of operational "
         "forecasting frameworks remains constrained in many developing "
         "contexts by three persistent factors. The first is data "
         "availability: rainfall and streamflow networks may be sparse, "
         "discontinuous or difficult to access, and gauged rainfall in "
         "particular is frequently the scarcer of the two. The second is the "
         "technical barrier: physically based and distributed models require "
         "high-resolution spatial data sets and considerable specialist "
         "expertise, while conceptual models require the calibration of "
         "parameters whose values are not uniquely identifiable. The third is "
         "cost and accessibility: proprietary modelling platforms can be "
         "expensive or simply unavailable for routine academic and operational "
         "use.")
    body(doc,
         "These constraints motivate a deliberately parsimonious response. If "
         "a useful short-range forecast can be produced from the discharge "
         "record alone, then the meteorological inputs, the spatial data and "
         "the parameter calibration all fall away, and with them the largest "
         "sources of both effort and uncertainty. This project pursues exactly "
         "that possibility, developing a computer-based forecasting framework "
         "built on the autoregressive integrated moving average (ARIMA) family "
         "of models (Box & Jenkins, 1976) and demonstrating it on a long, "
         "high-quality daily flow record.")

    h1(doc, "1.2 Statement of the Problem")
    body(doc,
         "Short-term streamflow forecasting is essential to flood "
         "preparedness and to water resources decision-making. In many "
         "practical settings, however, the available forecasting tools are "
         "limited by inadequate access to continuous meteorological data, by "
         "the computational and data demands of complex models, by dependence "
         "on costly proprietary software, and by the absence of transparent, "
         "easily implemented workflows suitable for academic and operational "
         "environments.")
    body(doc,
         "A specific difficulty compounds these limitations. Process-based "
         "forecasting requires forecast meteorological inputs, so the "
         "uncertainty of the weather forecast is inherited by, and compounded "
         "within, the hydrological forecast. Where rainfall observations are "
         "themselves sparse, the model is calibrated against inputs that are "
         "poorly known, and its apparent skill may not survive operational "
         "use.")
    body(doc,
         "Consequently, stakeholders often fall back on simplified heuristics, "
         "manual judgement or purely retrospective analysis rather than "
         "automated forecasting. This reduces the effectiveness of early "
         "warning systems and limits the adoption of data-driven operational "
         "strategies. There is therefore a need for a computer-based "
         "hydrological forecasting framework that is accessible, in that it "
         "can be implemented with open-source tools on a standard computer; "
         "data-efficient, in that it operates on the single time series that "
         "is most commonly available; technically clear, in that it can be "
         "understood, modified and extended by engineering students and "
         "practitioners; and evaluable, in that it embeds identification, "
         "validation and honest benchmarking so that its forecasts can be "
         "defended.")

    h1(doc, "1.3 Aim and Objectives of the Study")
    body(doc,
         "The aim of this study is to design and develop a computer-based "
         "statistical forecasting framework that predicts monthly river "
         "discharge, rainfall and stage, each from that variable's own past "
         "values alone, and to evaluate the resulting forecasts honestly by "
         "the statistical properties they reproduce, appropriate to their "
         "stochastic nature.")
    body(doc, "The specific objectives are:", bold=True)
    for text in (
        "to design and implement, in the Python programming environment, a "
        "modular computational framework for univariate statistical "
        "hydrological forecasting, comprising monthly data aggregation, "
        "model identification, estimation, stochastic ensemble generation "
        "and property-based validation;",
        "to identify and estimate, independently, an appropriate ARIMA "
        "model for each of three monthly hydrological series — discharge, "
        "rainfall and stage — by following the Box–Jenkins procedure, using "
        "formal stationarity tests to fix each series' order of "
        "differencing and an information criterion to select each model "
        "order objectively;",
        "to estimate a standard error for every coefficient of every "
        "selected model, distinguishing the choice of model order from the "
        "estimation of the model's actual parameters;",
        "to generate, from each fitted model, an ensemble of synthetic "
        "monthly sequences over an independent validation period, and to "
        "evaluate that ensemble by the statistical properties it reproduces "
        "— mean, variability, persistence, seasonality and extremes — "
        "rather than by point-for-point comparison against the sequence "
        "that was actually observed; and",
        "to verify the statistical adequacy of each fitted model through "
        "residual diagnostics.",
    ):
        bullet(doc, text)

    h1(doc, "1.4 Significance of the Study")
    body(doc,
         "This study is significant in four respects. For engineering "
         "practice, it provides a structured and defensible workflow for "
         "monthly hydrological forecasting that can support water-resources "
         "planning, including reservoir and spillway sizing, in catchments "
         "where only a variable's own record exists. For capacity "
         "development, it offers a compact educational framework through "
         "which students of civil and environmental engineering can learn "
         "computational hydrology, time-series identification and the "
         "discipline of out-of-sample, stochastic evaluation. For "
         "accessibility and reproducibility, it promotes open and "
         "transparent modelling in Python, so that every step from "
         "stationarity testing to stochastic validation can be audited, "
         "re-run and extended without licensing barriers. For adaptability, "
         "the identification-estimation-validation procedure requires no "
         "input beyond a variable's own monthly record, and runs "
         "unmodified on any such record: demonstrated directly within the "
         "primary basin by applying it to three variables, and, as a "
         "supplementary check (Section 4.8), by applying it without "
         "modification to two further basins in climate regimes distinct "
         "from the primary one. That check found the procedure itself "
         "transfers — order selection, estimation and diagnostics complete "
         "successfully on unfamiliar data — while the specific qualitative "
         "pattern found at the primary basin does not universally repeat, "
         "which is the expected and honest outcome for different basins "
         "with different hydrology, not a failure of the method.")
    body(doc,
         "A further contribution is methodological. Because a stochastic "
         "model's individual forecasts are not meant to reproduce a single "
         "observed trajectory, comparing one forecast to the one sequence "
         "that happened to follow it conflates genuine model skill with the "
         "specific random path realised. By validating instead against the "
         "statistical properties an ensemble of synthetic sequences "
         "reproduces relative to the historical record, this study "
         "establishes an evaluation standard suited to the stochastic "
         "nature of the model itself, and directly relevant to the "
         "design applications, such as sizing a reservoir against a range "
         "of plausible inflow sequences, that motivate stochastic "
         "hydrological modelling in the first place.")

    h1(doc, "1.5 Scope of the Study")
    body(doc,
         "This study concerns monthly forecasting of river discharge, "
         "rainfall and stage using univariate statistical time-series "
         "modelling implemented in Python. The framework operates on a "
         "monthly time step and produces stochastic ensembles of synthetic "
         "monthly sequences rather than single deterministic values. Its "
         "scope covers monthly data aggregation, stationarity testing, "
         "model identification and order selection, parameter estimation "
         "with standard errors, stochastic ensemble generation, and "
         "property-based validation against the historical record.")
    body(doc,
         "The methodology is demonstrated on thirty-five years of monthly "
         "discharge, rainfall and stage for the Conecuh River at Brantley, "
         "United States Geological Survey gauge 02371500, in southern "
         "Alabama, United States, obtained from the CAMELS data set and the "
         "USGS National Water Information System. That catchment is treated "
         "purely as a demonstration basin: the object of study is a "
         "transferable forecasting methodology, applicable across variable "
         "types, not a location-specific water resources problem. A long, "
         "continuous and quality-controlled record was chosen so that the "
         "method could be assessed under well-observed conditions.")
    body(doc,
         "The study deliberately excludes rainfall–runoff transformation "
         "and unit-hydrograph routing — no variable is forecast from "
         "another, each of the three models depends on that variable's own "
         "past alone. It also excludes fully distributed modelling, "
         "sediment transport, water quality forecasting, socio-economic "
         "flood impact assessment, and explicit seasonal (SARIMA) "
         "extensions, the last of which is identified as a direction for "
         "future work in Chapter Five.")


# ── Chapter Two ──────────────────────────────────────────────────────────────

def write_chapter2(doc, eq):
    chapter_heading(doc, "TWO", "Literature Review")

    h1(doc, "2.1 Introduction")
    body(doc,
         "Hydrological forecasting is an interdisciplinary field that draws "
         "on hydrologic science, applied mathematics, numerical modelling, "
         "statistics and computer programming in order to predict future "
         "water-related variables such as river discharge, reservoir inflow "
         "and flood level. Over the last five decades it has evolved from "
         "empirical, rule-based technique to computational frameworks capable "
         "of assimilating observations in real time.")
    body(doc,
         "This chapter reviews the theoretical foundations and computational "
         "developments relevant to short-term streamflow forecasting. It "
         "outlines the physical basis of catchment response, examines the "
         "principal modelling paradigms and the trade-offs between them, and "
         "then treats in detail the statistical time-series methodology "
         "adopted in this work: the ARIMA family, the stationarity and "
         "transformation questions it raises, the identification and order "
         "selection procedures it requires, and the verification standards "
         "against which its forecasts must be judged. The chapter closes by "
         "identifying the gaps in existing practice that justify the present "
         "study.")

    h1(doc, "2.2 The Hydrological Cycle and Catchment Response")
    body(doc,
         "The hydrological cycle governs the movement of water between the "
         "atmosphere, the land surface and the subsurface. At the catchment "
         "scale, the transformation of rainfall into runoff can be described "
         "by the conservation of mass (Chow, Maidment, & Mays, 2008):")
    equation(doc, "dS/dt = P − Q − ET − L", eq())
    body(doc,
         "where S is catchment water storage, P is precipitation, Q is "
         "streamflow discharge, ET is evapotranspiration and L represents "
         "deep percolation and other losses. Catchment response to a rainfall "
         "input depends on soil moisture dynamics, infiltration capacity, "
         "surface storage, groundwater recession and channel routing. The "
         "principal runoff generation mechanisms are infiltration-excess "
         "(Hortonian) overland flow, which occurs when rainfall intensity "
         "exceeds infiltration capacity; saturation-excess runoff, which "
         "occurs once the soil profile is saturated; interflow, the lateral "
         "movement of water through shallow soil layers; and baseflow, the "
         "slow groundwater discharge that sustains a perennial river through "
         "dry periods.")
    body(doc,
         "Two consequences of this physical picture are important to the "
         "present study. First, catchment response is nonlinear and depends "
         "strongly on antecedent moisture conditions, so that the same "
         "rainfall produces very different hydrographs at different times of "
         "year. Second, and more usefully for short-range forecasting, "
         "catchment storage imparts memory to the system. Because water "
         "released from soil and groundwater storage decays slowly, the "
         "recession limb of a hydrograph is smooth and highly predictable, and "
         "the discharge observed today constrains the discharge that can "
         "occur tomorrow. It is this memory, expressed statistically as "
         "autocorrelation, that a univariate time-series model exploits.")

    h1(doc, "2.3 Classification of Hydrological Forecasting Models")
    body(doc,
         "Hydrological models are conventionally grouped into three families "
         "according to how much physical process representation they contain.")
    body(doc,
         "Empirical, or black-box, models derive statistical relationships "
         "between inputs and outputs without explicit physical "
         "interpretation. They include linear regression, autoregressive "
         "moving average models, artificial neural networks (ASCE Task "
         "Committee on Application of Artificial Neural Networks in Hydrology, "
         "2000a, 2000b) and support vector machines. Their strengths are that "
         "they require minimal process knowledge and often perform very well "
         "in short-term forecasting; their weaknesses are poor extrapolation "
         "beyond the range of the training data, limited physical "
         "interpretability and sensitivity to non-stationarity.")
    body(doc,
         "Physically based, or white-box, models solve conservation equations "
         "explicitly, for example the Saint-Venant equations for flow routing "
         "and the Richards equation for unsaturated flow. Examples include "
         "MIKE SHE and the Soil and Water Assessment Tool (Arnold, "
         "Srinivasan, Muttiah, & Williams, 1998). They offer high process "
         "realism and are well suited to research-level studies, but they "
         "demand high-resolution spatial data, are computationally intensive "
         "and are difficult to calibrate.")
    body(doc,
         "Conceptual, or grey-box, models occupy the middle ground, "
         "representing dominant processes through simplified interconnected "
         "reservoirs. The HBV model (Lindström, Johansson, Persson, "
         "Gardelin, & Bergström, 1997), the GR4J model (Perrin, Michel, & "
         "Andréassian, 2003) and the Sacramento soil moisture accounting "
         "model are widely used examples. They have moderate data "
         "requirements and good computational efficiency, but they retain "
         "structural simplifications and suffer from equifinality, the "
         "condition in which many different parameter sets reproduce the "
         "observed record equally well, so that no single set can be "
         "identified as correct (Beven & Freer, 2001; Beven, 2012).")
    body(doc,
         "Both the conceptual and the physically based families share a "
         "requirement that is decisive for the present work: they are driven "
         "by meteorological forcing, and to forecast they must be supplied "
         "with forecast rainfall. Where rainfall observations are sparse, or "
         "where no reliable quantitative precipitation forecast is available, "
         "that requirement is not merely inconvenient but disqualifying. The "
         "empirical family, and within it the statistical time-series models "
         "reviewed below, avoids the requirement altogether.")

    h1(doc, "2.4 Statistical Time-Series Modelling of Streamflow")
    body(doc,
         "Statistical time-series analysis treats the observed sequence of "
         "discharge as a realisation of a stochastic process and seeks to "
         "characterise its temporal dependence directly. Its application to "
         "hydrology is long established: Salas, Delleur, Yevjevich and Lane "
         "(1980) and Hipel and McLeod (1994) provide comprehensive treatments "
         "of the modelling of hydrological and environmental time series, and "
         "the general statistical theory is set out by Box and Jenkins (1976) "
         "and, in modern form, by Brockwell and Davis (2016).")
    body(doc,
         "The building blocks are two elementary models. In an autoregressive "
         "model of order p, written AR(p), the present value of the series "
         "depends linearly on its own p previous values:")
    equation(doc,
             "z(t) = c + φ1 z(t−1) + … + φp z(t−p) + a(t)", eq())
    body(doc,
         "In a moving-average model of order q, written MA(q), the present "
         "value depends instead on the q previous random shocks:")
    equation(doc,
             "z(t) = μ + a(t) + θ1 a(t−1) + … + θq a(t−q)", eq())
    body(doc,
         "where a(t) is a white-noise process. Combining the two yields the "
         "ARMA(p, q) model, and admitting differencing to remove drift yields "
         "the ARIMA(p, d, q) model developed in Chapter Three. In hydrological "
         "terms, the autoregressive component expresses the persistence of "
         "the flow level that arises from catchment storage, while the "
         "moving-average component expresses the propagation of recent "
         "disturbances, such as the passage of a flood wave, through the "
         "system.")
    body(doc,
         "The strength of this approach at short lead times is well "
         "documented. Because streamflow is strongly autocorrelated, a small "
         "number of parameters can capture most of the predictable structure, "
         "and the resulting model is both computationally trivial and "
         "statistically transparent. Its limitation is equally clear: a "
         "univariate model cannot anticipate an event that has not yet begun "
         "to register in the observed series, so forecast skill decays as "
         "the lead time extends beyond the memory of the process.")
    body(doc,
         "The choice among these variants, and the further variant "
         "ARIMAX, is not a matter of preference but of what the data and "
         "the forecasting problem actually require, and is worth setting "
         "out explicitly. A pure AR(p) model is appropriate when a series' "
         "dependence on its own past is well summarised by a linear "
         "combination of a few previous values, with no distinct pattern in "
         "the shocks themselves; a pure MA(q) model is appropriate when the "
         "series is better described as a moving window over recent random "
         "disturbances than as persistence of level. The combined ARMA(p, "
         "q) model, and its differenced extension ARIMA(p, d, q), are the "
         "general cases that nest both as special cases (q = 0 or p = 0 "
         "respectively) and are preferred whenever the sample "
         "autocorrelation and partial autocorrelation functions do not "
         "cut off cleanly at a low lag, which is the common situation for "
         "hydrological series. ARIMAX extends ARIMA by adding one or more "
         "exogenous predictor series — for example forecast rainfall used "
         "to forecast discharge — and is the appropriate choice precisely "
         "when a genuine, independently available exogenous driver exists "
         "and is expected to improve on the variable's own past alone. This "
         "study does not adopt ARIMAX: each of its three models forecasts "
         "one variable from that same variable's own past only, by design "
         "(Section 1.5), so there is no exogenous driver to add, and "
         "introducing one would reintroduce exactly the meteorological-"
         "input dependency the univariate approach is meant to avoid "
         "(Section 1.1). Plain ARIMA, admitting the possibility that "
         "p = 0 or q = 0 emerges from the data, is therefore the correct "
         "member of the family for the problem as posed, and Section 3.5 "
         "lets the order-selection procedure, not an a priori assumption, "
         "decide which of AR, MA or the mixed ARMA form best fits each "
         "series.")
    body(doc,
         "One further member of the family requires separate treatment "
         "because the timestep of this study invites it. The multiplicative "
         "seasonal form, SARIMA(p, d, q)(P, D, Q) with period s, extends "
         "ARIMA with autoregressive, differencing and moving-average "
         "operators acting at the seasonal lag rather than at lag one, and "
         "is the standard recommendation for monthly data carrying an "
         "annual cycle. It is the natural candidate here, and it is "
         "examined directly rather than dismissed: Section 4.2 fits the "
         "seasonally differenced specification to this study's data and "
         "reports what it yields. The reason the study does not finally "
         "adopt it is specific to the purpose of the model rather than to "
         "any deficiency of the specification, and is set out in "
         "Section 2.5 in general terms and Section 4.2 in the particular "
         "case: the seasonal differencing operator leaves an integrated "
         "process, and this study requires a generating model that remains "
         "stationary over records far longer than the one observed. The "
         "annual cycle is therefore removed by seasonal standardisation "
         "instead, which is a difference in how the seasonal component is "
         "parameterised rather than a decision to ignore it.")

    h1(doc, "2.5 Stationarity, Transformation and Differencing")
    body(doc,
         "ARIMA modelling requires that the modelled series be stationary, "
         "that is, that its mean, variance and autocorrelation structure be "
         "invariant over time. Raw daily discharge satisfies neither "
         "condition well. It is strongly right-skewed, with long periods of "
         "low flow punctuated by short, very large peaks, and its variability "
         "grows with its magnitude, a form of heteroscedasticity. The "
         "standard remedy is a logarithmic transformation, which stabilises "
         "the variance, renders the distribution more nearly Gaussian and "
         "prevents a handful of flood peaks from dominating parameter "
         "estimation.")
    body(doc,
         "The transformation carries a consequence that matters for a "
         "deterministic, single-valued forecast and is frequently "
         "overlooked there. Because the exponential function is convex, "
         "exponentiating a single point forecast made on the logarithmic "
         "scale recovers the median rather than the mean of the predictive "
         "distribution, and therefore systematically under-estimates the "
         "expected value by an amount that grows with the forecast "
         "variance. Duan (1983) proposed a nonparametric smearing estimator "
         "to correct this retransformation bias, and an analytical "
         "log-normal correction is available as an alternative. Chapter "
         "Three does not use either: because this study forecasts by "
         "generating a stochastic ensemble rather than a single point value "
         "(Section 3.6), each ensemble member is exponentiated "
         "individually and the ensemble mean is then a Monte Carlo estimate "
         "of the true expected value, unbiased by construction without any "
         "explicit correction term. The retransformation-bias problem this "
         "section describes is real, but it is a problem for point "
         "forecasting specifically, and the ensemble approach adopted here "
         "sidesteps it rather than correcting for it after the fact.")
    body(doc,
         "The order of differencing is settled by formal hypothesis testing "
         "rather than by inspection. The Augmented Dickey–Fuller test "
         "(Dickey & Fuller, 1979), with critical values from the response "
         "surface of MacKinnon (1996), takes the presence of a unit root, and "
         "hence non-stationarity, as its null hypothesis. The "
         "Kwiatkowski–Phillips–Schmidt–Shin test (Kwiatkowski, "
         "Phillips, Schmidt, & Shin, 1992) reverses the null and takes "
         "stationarity as its hypothesis, and the two are therefore used "
         "together as complementary evidence. Over-differencing is a real "
         "risk, and manifests as a moving-average root close to the unit "
         "circle; it is a recognised difficulty when a physically bounded, "
         "mean-reverting variable such as river discharge is treated as an "
         "integrated process.")
    body(doc,
         "Seasonality is a distinct form of non-stationarity, and the "
         "literature is explicit that the two must not be conflated. "
         "Ordinary differencing, X(t) − X(t−1), removes a trend or slow "
         "drift in level; it leaves a twelve-month cycle essentially "
         "untouched, at any order of d. A monthly hydrological series is "
         "dominated by exactly such a cycle, so its treatment is a separate "
         "decision, and Box, Jenkins and Reinsel (2008) set out two "
         "approaches to it. The first is the seasonal differencing "
         "operator (1 − B^s), which subtracts from each observation the "
         "value one full cycle earlier and gives rise to the multiplicative "
         "seasonal ARIMA, or SARIMA, family. The second, associated "
         "particularly with the stochastic-hydrology tradition (Salas, "
         "Delleur, Yevjevich, & Lane, 1980), is seasonal standardisation, "
         "in which the mean and standard deviation of each position in the "
         "cycle are estimated and every observation expressed as a "
         "standardised departure from its own season's mean.")
    body(doc,
         "The two are often presented as interchangeable, and for "
         "short-horizon forecasting they largely are. They are not "
         "interchangeable when the object is to generate a long synthetic "
         "record, and the distinction turns on stationarity. A seasonally "
         "differenced series must be integrated back, and an integrated "
         "process is not stationary: the variance of a generated sequence "
         "grows in proportion to its length. Over the span of an observed "
         "record this is negligible; over the centuries of a synthetic "
         "record it is not, and the generated series ceases to be a sample "
         "of the process that was fitted. A standardised series carries no "
         "such term. This is why the classical synthetic-generation models "
         "of stochastic hydrology are built on standardised or periodic "
         "parameterisations rather than on seasonal differencing, a point "
         "that Section 3.4 develops and Section 4.2 tests directly on this "
         "study's data. A further diagnostic connects the two: when a "
         "seasonal difference is applied to a cycle that is close to "
         "deterministic, the fitted seasonal moving-average coefficient "
         "approaches −1, the seasonal counterpart of the over-differencing "
         "signature described above.")

    h1(doc, "2.6 Model Identification, Estimation and Order Selection")
    body(doc,
         "The classical Box–Jenkins procedure identifies candidate orders "
         "from the sample autocorrelation function and partial autocorrelation "
         "function of the stationary series. An autocorrelation function that "
         "decays gradually, together with a partial autocorrelation function "
         "that cuts off after lag p, indicates an autoregressive process of "
         "order p; the reverse pattern indicates a moving-average process; and "
         "a mixture of the two indicates an ARMA process. The partial "
         "autocorrelation function is conveniently computed by the "
         "Levinson–Durbin recursion.")
    body(doc,
         "Parameters are then estimated. Exact maximum likelihood is "
         "available, but the method of conditional sum of squares, in which "
         "the one-step-ahead errors are computed recursively and their squared "
         "sum minimised, is the standard and computationally economical "
         "alternative, and coincides with ordinary least squares for a pure "
         "autoregressive model.")
    body(doc,
         "Visual identification is, however, subjective, and different "
         "analysts may read the same correlogram differently. Modern practice "
         "therefore supplements it with an objective grid search over "
         "candidate orders, ranked by an information criterion that rewards "
         "goodness of fit while penalising the number of estimated parameters "
         "(Hyndman & Athanasopoulos, 2021). The Akaike Information Criterion "
         "is the usual choice for forecasting applications, with the Bayesian "
         "Information Criterion, whose penalty is heavier, reported alongside "
         "as a confirmatory measure. A necessary precaution, and one not "
         "always observed in the literature, is that all candidates must be "
         "fitted on an identical sample: conditional estimation discards a "
         "number of initial observations that depends on the model order, so "
         "criteria computed on different effective sample sizes are not "
         "comparable.")
    body(doc,
         "Finally, an identified model must be diagnosed. The Ljung–Box "
         "test (Ljung & Box, 1978) examines whether the residuals retain "
         "significant autocorrelation; a high p-value indicates that the "
         "linear temporal structure has been captured. Streamflow residuals "
         "commonly remain heteroscedastic and heavy-tailed even when they are "
         "serially uncorrelated, so the Jarque–Bera test of normality "
         "(Jarque & Bera, 1980) and a test for conditional heteroscedasticity "
         "in the spirit of Engle (1982) are appropriate companions. Such "
         "departures do not bias point forecasts, but they bear directly on "
         "the validity of any prediction interval built around them.")

    h1(doc, "2.7 Forecast Verification and the Choice of Benchmark")
    body(doc,
         "Forecast performance in hydrology is customarily reported through "
         "the Nash–Sutcliffe efficiency (Nash & Sutcliffe, 1970), which "
         "expresses the proportion of observed variance reproduced by the "
         "model, alongside the root-mean-square error, the mean absolute "
         "error and the percentage bias. Moriasi et al. (2007) provide widely "
         "adopted performance ratings for the efficiency, and Gupta, Kling, "
         "Yilmaz and Martinez (2009) decompose it into correlation, bias and "
         "variability components, exposing its tendency to reward variance "
         "under-estimation.")
    body(doc,
         "Knoben, Freer and Woods (2019) make the more fundamental point that "
         "an efficiency value is meaningful only relative to the benchmark "
         "implied by its denominator. For daily streamflow this matters "
         "acutely: because flow is highly autocorrelated, the naive "
         "persistence forecast, which simply carries today's flow forward, "
         "attains a high efficiency in its own right, and a model may post an "
         "impressive efficiency while adding no information whatever. The "
         "conventional response, for a model that issues a single "
         "deterministic forecast value at each lead time, is to score it "
         "against persistence directly by means of a skill score, defined "
         "as one minus the ratio of the model's mean squared error to that "
         "of persistence.")
    body(doc,
         "This entire verification tradition — efficiency, skill score, "
         "rolling-origin evaluation against a point-forecast benchmark — "
         "presupposes that the model produces one forecast value to be "
         "scored against one observed value. That precondition does not "
         "hold for the stochastic models developed in this study "
         "(Section 3.6): each model generates an ensemble of plausible "
         "future sequences, not a single value, so there is no single "
         "forecast to place in the numerator of an efficiency or skill-"
         "score calculation without arbitrarily collapsing the ensemble to "
         "one number and discarding the very information the stochastic "
         "approach exists to represent. Section 2.8 develops the "
         "alternative this study actually adopts: validation by the "
         "statistical properties an ensemble reproduces, rather than by "
         "scoring a single collapsed value against a single observed one. "
         "The efficiency and skill-score literature reviewed above remains "
         "the right standard for a deterministic point-forecasting model; "
         "it is reviewed here because it motivated the property-based "
         "alternative by showing what a benchmark-aware verification "
         "standard should demand, not because this study computes it.")

    h1(doc, "2.8 Forecast Uncertainty and Error Growth with Lead Time")
    body(doc,
         "Forecast error arises from four sources: model structural error, "
         "parameter uncertainty, measurement error in the observations, and, "
         "where meteorological inputs are used, error in the meteorological "
         "forecast itself. Uncertainty grows with lead time, because the "
         "errors made at each step propagate into subsequent steps of a "
         "recursive forecast. For a univariate model the growth has a "
         "particularly clear interpretation: the forecast error variance at "
         "lead time k is the accumulated contribution of the k random shocks "
         "that have not yet been observed, so that as k increases the forecast "
         "converges towards the unconditional mean of the process and its "
         "skill converges towards zero. This explains why three-day forecasts "
         "typically show markedly lower skill than one-day forecasts, and why "
         "the useful horizon of a discharge-only model is bounded by the "
         "memory of the catchment.")
    body(doc,
         "A separate and, for design applications, arguably more useful "
         "tradition treats this same growth of uncertainty not as a problem "
         "to be minimised but as the object of study. Stochastic hydrology "
         "generates synthetic sequences from a fitted time-series model "
         "specifically to characterise the range of futures a catchment "
         "could plausibly produce, an approach with a long history in water "
         "resources engineering (Matalas, 1967; Salas, Delleur, Yevjevich, "
         "& Lane, 1980) and applied to reservoir and spillway design, where "
         "the quantity of interest is the distribution of possible inflow "
         "sequences a structure must be sized against, not a single "
         "predicted trajectory. The natural evaluation standard for a "
         "synthetic generator is correspondingly different from the "
         "point-accuracy standard of Section 2.7: a generator is judged by "
         "whether the statistical properties of its synthetic output — "
         "mean, variance, skewness, autocorrelation, seasonal pattern, and "
         "extremes such as drought duration and peak value — reproduce "
         "those of the historical record, since any individual synthetic "
         "trajectory is only one draw from the fitted process and is not "
         "expected to match a specific observed sequence. This "
         "property-based standard, rather than the rolling-origin, "
         "point-comparison standard of Section 2.7, is the one adopted for "
         "the stochastic ensembles generated in this study (Section 3.6).")
    body(doc,
         "It is worth stating plainly what this tradition claims a "
         "synthetic record accomplishes, because the claim is easily "
         "overstated in either direction. A gauged record of a few decades "
         "provides a correspondingly small number of annual maxima, from "
         "which the flow associated with a long return period cannot be "
         "estimated with confidence; the design event is, by definition, "
         "rarer than the record is long. Generating a synthetic record of "
         "many centuries supplies as many annual maxima as are wanted, and "
         "the frequency curve can then be read from the synthetic sample "
         "directly. What this does not do is create information the gauged "
         "record did not contain. The synthetic record is a consequence of "
         "a statistical structure estimated from the observed data, and "
         "extrapolating it far beyond the observed range yields values "
         "that depend increasingly on the assumed form of the model rather "
         "than on evidence. Klemeš (1974) and the subsequent literature on "
         "long-term persistence caution specifically against reading such "
         "extrapolations as though they carried the authority of "
         "observation. The synthetic record is properly understood as a "
         "device for propagating the fitted structure into a fuller "
         "picture of its own consequences, and its reliability is bounded "
         "by the adequacy of that structure. Section 4.6 reports the "
         "design estimates obtained here together with the checks "
         "available against the observed range, and Section 5.3 the limits "
         "on their interpretation.")

    h1(doc, "2.9 Computational Hydrology and Open-Source Implementation")
    body(doc,
         "Hydrological modelling increasingly relies on general-purpose "
         "programming languages rather than standalone proprietary software. "
         "Python has become the dominant choice, because it is open-source, "
         "because it is supported by mature scientific libraries such as NumPy "
         "(Harris et al., 2020) and SciPy (Virtanen et al., 2020) for "
         "numerical work and Matplotlib (Hunter, 2007) for visualisation, and "
         "because a script is an unambiguous and executable record of a "
         "method. Singh (2002) surveys the longer history of computer models "
         "in watershed hydrology and the shift from monolithic packages "
         "towards modular, scriptable workflows.")
    body(doc,
         "Implementing a method from its defining equations, rather than "
         "invoking it from a library, carries a particular pedagogical and "
         "scientific value in a project of this kind. It obliges the analyst "
         "to understand each step, it removes any dependence on the "
         "correctness or continued availability of a third-party package, and "
         "it makes the entire computation auditable. The framework described "
         "in Chapter Three is written on that principle, and the source "
         "listings are reproduced in the Appendix.")

    h1(doc, "2.10 Research Gap")
    body(doc,
         "Five gaps emerge from this review. First, a great many published "
         "studies apply a specific model to a specific river without "
         "producing a reusable framework, so that the computational effort "
         "is not transferable. Second, there is limited emphasis on "
         "open-source, modular architectures in which pre-processing, "
         "identification, estimation, simulation and evaluation are "
         "integrated within a single reproducible pipeline. Third, "
         "univariate time-series studies in hydrology are overwhelmingly "
         "applied to discharge alone, with comparatively little published "
         "work demonstrating the same identification-estimation-validation "
         "procedure, unmodified, across physically distinct variables such "
         "as rainfall and stage, so the claim that the ARIMA methodology "
         "itself — rather than a fitted discharge model — is what "
         "generalises is asserted more often than it is shown. Fourth, and "
         "most consequentially for a model intended to be stochastic, many "
         "studies validate against a single observed sequence using "
         "point-accuracy measures such as the Nash–Sutcliffe efficiency, "
         "which is the correct standard for a deterministic forecast but "
         "conflates model skill with realised randomness when applied to a "
         "model whose whole premise is that each run produces a different "
         "plausible outcome (Section 2.8). Fifth, where model coefficients "
         "are reported at all, they are frequently given without standard "
         "errors, so a reader cannot judge which estimated parameters are "
         "well identified by the data and which are not.")
    body(doc,
         "There is therefore a need for a generalised, modular forecasting "
         "architecture, implemented entirely in open-source software, "
         "demonstrated identically across more than one hydrological "
         "variable, reporting a standard error alongside every estimated "
         "coefficient, and validated by the statistical properties its "
         "stochastic output reproduces relative to the historical record, "
         "rather than by point comparison against a single observed "
         "sequence. This study "
         "addresses that need.")
