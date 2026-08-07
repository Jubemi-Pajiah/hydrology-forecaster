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
    f1 = R["forecast"]["1"]["model"]
    front_heading(doc, "ABSTRACT", page_break=False)
    body(doc,
         "Hydrological forecasting underpins flood preparedness, reservoir "
         "operation and sustainable water resources planning. Many operational "
         "forecasting systems nevertheless remain out of reach in data-limited "
         "settings, because they demand meteorological forcing, spatial "
         "catchment data, extensive parameter calibration and, frequently, "
         "proprietary software. This study develops and evaluates a purely "
         "statistical, computer-based framework for short-term river-discharge "
         "forecasting that depends on the discharge record alone. Future flow "
         "is predicted from the past values of flow itself using the class of "
         "autoregressive integrated moving average (ARIMA) models formalised "
         "by Box and Jenkins, so that no rainfall, temperature, "
         "evapotranspiration or routing information is required at any stage. "
         "The framework is implemented from first principles in Python, "
         "comprising modules for data pre-processing, stationarity testing, "
         "model identification, parameter estimation, forecast generation and "
         "performance evaluation. The methodology is demonstrated on "
         "thirty-five years of daily discharge (1980-2014) for the Conecuh "
         "River at United States Geological Survey gauge 02361000, drawn from "
         "the CAMELS data set. The log-transformed series was differenced once "
         "on the joint evidence of the Augmented Dickey-Fuller and "
         "Kwiatkowski-Phillips-Schmidt-Shin tests, and the model order was "
         "selected objectively by an iterative grid search minimising the "
         "Akaike Information Criterion, which identified "
         f"{R['model']}. The model was estimated on the 1980-2003 training "
         "period and evaluated by rolling-origin forecasts over the "
         "independent 2004-2014 validation period, with forecasts "
         "back-transformed using a log-normal bias correction. At a one-day "
         f"lead time the model attained a Nash-Sutcliffe efficiency of "
         f"{f1['NSE']:.3f}, a root-mean-square error of {f1['RMSE']:.2f} m3/s "
         f"and a percentage bias of {f1['PBIAS']:.2f} per cent, and it "
         "outperformed the naive persistence benchmark at every lead time, "
         f"with persistence skill scores of {f1['PSS']:.3f}, "
         f"{R['forecast']['2']['model']['PSS']:.3f} and "
         f"{R['forecast']['3']['model']['PSS']:.3f} at one, two and three "
         "days. Residual diagnostics confirmed the absence of significant "
         f"short-lag autocorrelation (Ljung-Box p = "
         f"{R['ljung_box']['pvalue']:.3f}). The study demonstrates that a "
         "parsimonious, open-source and fully reproducible statistical "
         "approach yields skilful short-range discharge forecasts without "
         "recourse to costly modelling platforms or dense meteorological "
         "monitoring, and provides an honest benchmark against which more "
         "elaborate models should be judged.")


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
     "equally spaced instants; here, daily mean discharge."),
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
     "predicted flow equals the most recently observed flow."),
    ("Rolling-origin evaluation",
     "a walk-forward assessment in which a forecast is issued from every day "
     "of the validation period using only the data available up to that day."),
    ("Validation",
     "independent testing of a fitted model on a period withheld from model "
     "fitting, in order to assess genuine predictive reliability."),
    ("Nash–Sutcliffe efficiency",
     "a statistical measure of the proportion of the observed variance that "
     "is reproduced by a model."),
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
         "of river flow. In engineering practice, the ability to anticipate "
         "near-future streamflow, over hours to days, is fundamental to flood "
         "early warning, reservoir operation, the safety assessment of "
         "hydraulic structures and emergency response planning.")
    body(doc,
         "Hydrological forecasting is the process of predicting future "
         "hydrological states, such as discharge, stage or reservoir inflow, "
         "from available observations. The forecast horizon may be short-term "
         "(from nowcasting to a few days), medium-term (weeks to months) or "
         "seasonal. In many real-world applications, and especially in flood "
         "response and day-to-day operational decisions, short-term "
         "forecasting over one to three days is the most actionable horizon, "
         "because it matches the time window available for issuing warnings, "
         "adjusting reservoir releases, mobilising field teams and protecting "
         "critical assets (World Meteorological Organization, 2011).")
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
         "hydrological forecasting system that predicts short-term river "
         "discharge from the past values of discharge alone, and to evaluate "
         "its forecast skill honestly against an established benchmark.")
    body(doc, "The specific objectives are:", bold=True)
    for text in (
        "to design and implement, in the Python programming environment, a "
        "modular computational framework for univariate statistical "
        "streamflow forecasting, comprising data pre-processing, model "
        "identification, estimation, forecasting and evaluation;",
        "to identify and estimate an appropriate ARIMA model for the daily "
        "discharge series by following the Box–Jenkins procedure, using "
        "formal stationarity tests to fix the order of differencing and an "
        "information criterion to select the model order objectively;",
        "to generate one-, two- and three-day-ahead forecasts and to evaluate "
        "them out-of-sample against observed discharge over an independent "
        "validation period;",
        "to benchmark the model against the naive persistence forecast by "
        "means of a persistence skill score, and to interpret its performance "
        "using standard hydrological efficiency ratings; and",
        "to verify the statistical adequacy of the fitted model through "
        "residual diagnostics.",
    ):
        bullet(doc, text)

    h1(doc, "1.4 Significance of the Study")
    body(doc,
         "This study is significant in four respects. For engineering "
         "practice, it provides a structured and defensible workflow for "
         "short-range flow forecasting that can support flood preparedness and "
         "routine operational decisions in catchments where only a flow record "
         "exists. For capacity development, it offers a compact educational "
         "framework through which students of civil and environmental "
         "engineering can learn computational hydrology, time-series "
         "identification and the discipline of out-of-sample evaluation. For "
         "accessibility and reproducibility, it promotes open and transparent "
         "modelling in Python, so that every step from stationarity testing to "
         "forecast verification can be audited, re-run and extended without "
         "licensing barriers. For adaptability, the framework transfers to any "
         "basin for which a daily discharge record is available, since it "
         "requires no other input.")
    body(doc,
         "A further contribution is methodological. Because daily flow is "
         "highly autocorrelated, a naive forecast that simply assumes no "
         "change already scores well on conventional efficiency measures. Any "
         "claim of forecasting skill that is not tested against that benchmark "
         "is therefore weakly supported. By adopting the persistence skill "
         "score as its headline measure, this study establishes a reference "
         "model and an evaluation standard against which more elaborate "
         "forecasting schemes may fairly be judged.")

    h1(doc, "1.5 Scope of the Study")
    body(doc,
         "This study concerns short-term forecasting of daily river discharge "
         "using univariate statistical time-series modelling implemented in "
         "Python. The framework operates on a daily time step and produces "
         "forecasts at lead times of one to three days. Its scope covers data "
         "pre-processing, stationarity testing, model identification and order "
         "selection, parameter estimation, rolling-origin forecast generation, "
         "back-transformation with bias correction, and performance "
         "evaluation against a persistence benchmark.")
    body(doc,
         "The methodology is demonstrated on thirty-five years of daily "
         "discharge for the Conecuh River at United States Geological Survey "
         "gauge 02361000 in southern Alabama, United States, obtained from the "
         "CAMELS data set. That catchment is treated purely as a demonstration "
         "basin: the object of study is a transferable forecasting "
         "methodology, not a location-specific water resources problem. A "
         "long, continuous and quality-controlled record was chosen so that "
         "the method could be assessed under well-observed conditions.")
    body(doc,
         "The study deliberately excludes rainfall–runoff transformation, "
         "unit-hydrograph routing and any use of rainfall, temperature or "
         "evapotranspiration data, since the central premise under "
         "investigation is that the discharge record alone is sufficient for "
         "short-range forecasting. It also excludes fully distributed "
         "modelling, sediment transport, water quality forecasting, "
         "socio-economic flood impact assessment, and the construction of "
         "probabilistic prediction intervals, the last of which is identified "
         "as a direction for future work in Chapter Five.")


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
         "documented. Because daily flow is strongly autocorrelated, a small "
         "number of parameters can capture most of the predictable structure, "
         "and the resulting model is both computationally trivial and "
         "statistically transparent. Its limitation is equally clear: a "
         "univariate model cannot anticipate an event that has not yet begun "
         "to register in the river, so forecast skill decays as the lead time "
         "extends beyond the memory of the catchment.")

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
         "The transformation carries a consequence that is frequently "
         "overlooked. Because the exponential function is convex, "
         "exponentiating a forecast made on the logarithmic scale recovers the "
         "median rather than the mean of the predictive distribution, and "
         "therefore systematically under-estimates the expected discharge by "
         "an amount that grows with the forecast variance. Duan (1983) "
         "proposed a nonparametric smearing estimator to correct this "
         "retransformation bias; under a log-normal assumption the "
         "corresponding correction is an analytical factor involving the "
         "forecast error variance. Chapter Three adopts the latter and uses "
         "the former as a cross-check.")
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
         "acutely. Because flow is highly autocorrelated, the naive "
         "persistence forecast, which simply carries today's flow forward, "
         "attains a high efficiency in its own right, and a model may post an "
         "impressive efficiency while adding no information whatever. The "
         "appropriate response is to score the model against persistence "
         "directly by means of a skill score, defined as one minus the ratio "
         "of the model's mean squared error to that of persistence. A positive "
         "value demonstrates genuine added value; zero indicates none. This "
         "study accordingly adopts the persistence skill score as its headline "
         "measure and reports the efficiency alongside it.")
    body(doc,
         "A second requirement of honest verification concerns the "
         "evaluation protocol. Forecast skill must be assessed on a period "
         "withheld entirely from model fitting, and by rolling-origin "
         "evaluation, in which a forecast is issued from every day of that "
         "period using only the information available up to that day. This "
         "reproduces the conditions of genuine operational forecasting, in "
         "which recent observations are always available but the future never "
         "is.")

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
         "Four gaps emerge from this review. First, a great many published "
         "studies apply a specific model to a specific river without producing "
         "a reusable framework, so that the computational effort is not "
         "transferable. Second, there is limited emphasis on open-source, "
         "modular architectures in which pre-processing, identification, "
         "estimation, forecasting and evaluation are integrated within a "
         "single reproducible pipeline. Third, and most consequentially, "
         "short-range streamflow forecasts are frequently reported against "
         "the Nash–Sutcliffe efficiency alone, without benchmarking "
         "against persistence, so that the claimed skill cannot be "
         "distinguished from the autocorrelation of the flow itself. Fourth, "
         "the retransformation bias introduced by logarithmic modelling is "
         "often left uncorrected, producing forecasts that under-estimate "
         "discharge increasingly with lead time.")
    body(doc,
         "There is therefore a need for a generalised, modular forecasting "
         "architecture, implemented entirely in open-source software, "
         "operating on the discharge record alone, and evaluated by "
         "rolling-origin forecasting against an explicit persistence benchmark "
         "with the retransformation bias properly corrected. This study "
         "addresses that need.")
