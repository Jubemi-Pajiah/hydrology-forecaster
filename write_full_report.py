"""
write_full_report.py — Build the complete Chapter 1-5 project report.

Merges the author's Chapter 1-3 draft with the ARIMA Chapters 3-5, applies the
Department of Civil and Environmental Engineering project template, and appends
the source code of the forecasting framework as an appendix.

    python write_full_report.py

Output: documents/Computer_Hydrological_Forecasting_Full_Report.docx

Regeneration order matters: run run_pipeline.py first, since every numerical
value in Chapters Four and Five is read from data/results.json, and the code
listings in the Appendix are extracted from the live src/*.py modules.

The .docx is converted to PDF by hand in WPS Writer (Ctrl+A, then F9 to build
the table of contents, the list of figures and the list of tables, then export).
"""

import json
from pathlib import Path

from docx import Document

import report_ch345 as ch345
import report_front_ch12 as front
from report_lib import (appendix_heading, body, clear_footer, code_block,
                        extract, extract_methods, front_heading, imports_of,
                        new_section, reference, setup_page, setup_styles)

PROJECT_ROOT = Path(__file__).parent
SRC = PROJECT_ROOT / "src"
FIGURES_DIR = PROJECT_ROOT / "figures"
RESULTS_FILE = PROJECT_ROOT / "data" / "results.json"
DOCUMENTS_DIR = PROJECT_ROOT / "documents"
OUTPUT_FILE = DOCUMENTS_DIR / "Computer_Hydrological_Forecasting_Full_Report.docx"


class EquationCounter:
    """Numbers equations consecutively through the whole report, as the
    template requires."""

    def __init__(self):
        self.n = 0

    def __call__(self):
        self.n += 1
        return self.n


# ── References ───────────────────────────────────────────────────────────────
# Merged from the author's draft and the ARIMA chapters, deduplicated, and
# pruned to the works actually cited in this report. Entries specific to the
# superseded rainfall-runoff study (crop evapotranspiration, SCE-UA, dynamically
# dimensioned search, statsmodels) are omitted because nothing now cites them.

REFERENCES = [
    "Addor, N., Newman, A. J., Mizukami, N., & Clark, M. P. (2017). The CAMELS "
    "data set: Catchment attributes and meteorology for large-sample studies. "
    "Hydrology and Earth System Sciences, 21(10), 5293–5313. "
    "https://doi.org/10.5194/hess-21-5293-2017",

    "Arnold, J. G., Srinivasan, R., Muttiah, R. S., & Williams, J. R. (1998). "
    "Large area hydrologic modeling and assessment part I: Model development. "
    "Journal of the American Water Resources Association, 34(1), 73–89. "
    "https://doi.org/10.1111/j.1752-1688.1998.tb05961.x",

    "ASCE Task Committee on Application of Artificial Neural Networks in "
    "Hydrology. (2000a). Artificial neural networks in hydrology. I: "
    "Preliminary concepts. Journal of Hydrologic Engineering, 5(2), 115–123. "
    "https://doi.org/10.1061/(ASCE)1084-0699(2000)5:2(115)",

    "ASCE Task Committee on Application of Artificial Neural Networks in "
    "Hydrology. (2000b). Artificial neural networks in hydrology. II: "
    "Hydrologic applications. Journal of Hydrologic Engineering, 5(2), "
    "124–137. https://doi.org/10.1061/(ASCE)1084-0699(2000)5:2(124)",

    "Beven, K. (2012). Rainfall-runoff modelling: The primer (2nd ed.). "
    "Wiley-Blackwell.",

    "Beven, K., & Freer, J. (2001). Equifinality, data assimilation, and "
    "uncertainty estimation in mechanistic modelling of complex environmental "
    "systems using the GLUE methodology. Journal of Hydrology, 249(1–4), "
    "11–29. https://doi.org/10.1016/S0022-1694(01)00421-8",

    "Box, G. E. P., & Jenkins, G. M. (1976). Time series analysis: Forecasting "
    "and control (Rev. ed.). Holden-Day.",

    "Box, G. E. P., Jenkins, G. M., & Reinsel, G. C. (2008). Time series "
    "analysis: Forecasting and control (4th ed.). Wiley.",

    "Brockwell, P. J., & Davis, R. A. (2016). Introduction to time series and "
    "forecasting (3rd ed.). Springer.",

    "Chow, V. T., Maidment, D. R., & Mays, L. W. (2008). Applied hydrology. "
    "McGraw-Hill.",

    "Dickey, D. A., & Fuller, W. A. (1979). Distribution of the estimators for "
    "autoregressive time series with a unit root. Journal of the American "
    "Statistical Association, 74(366), 427–431.",

    "Duan, N. (1983). Smearing estimate: A nonparametric retransformation "
    "method. Journal of the American Statistical Association, 78(383), "
    "605–610. https://doi.org/10.1080/01621459.1983.10478017",

    "Engle, R. F. (1982). Autoregressive conditional heteroscedasticity with "
    "estimates of the variance of United Kingdom inflation. Econometrica, "
    "50(4), 987–1007. https://doi.org/10.2307/1912773",

    "Gneiting, T., & Raftery, A. E. (2007). Strictly proper scoring rules, "
    "prediction, and estimation. Journal of the American Statistical "
    "Association, 102(477), 359–378. "
    "https://doi.org/10.1198/016214506000001437",

    "Gupta, H. V., Kling, H., Yilmaz, K. K., & Martinez, G. F. (2009). "
    "Decomposition of the mean squared error and NSE performance criteria: "
    "Implications for improving hydrological modelling. Journal of Hydrology, "
    "377(1–2), 80–91. https://doi.org/10.1016/j.jhydrol.2009.08.003",

    "Harris, C. R., Millman, K. J., van der Walt, S. J., Gommers, R., "
    "Virtanen, P., Cournapeau, D., … Oliphant, T. E. (2020). Array programming "
    "with NumPy. Nature, 585(7825), 357–362. "
    "https://doi.org/10.1038/s41586-020-2649-2",

    "Hipel, K. W., & McLeod, A. I. (1994). Time series modelling of water "
    "resources and environmental systems. Elsevier.",

    "Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. Computing in "
    "Science & Engineering, 9(3), 90–95. https://doi.org/10.1109/MCSE.2007.55",

    "Hyndman, R. J., & Athanasopoulos, G. (2021). Forecasting: Principles and "
    "practice (3rd ed.). OTexts.",

    "Jarque, C. M., & Bera, A. K. (1980). Efficient tests for normality, "
    "homoscedasticity and serial independence of regression residuals. "
    "Economics Letters, 6(3), 255–259.",

    "Knoben, W. J. M., Freer, J. E., & Woods, R. A. (2019). Technical note: "
    "Inherent benchmark or not? Comparing Nash–Sutcliffe and Kling–Gupta "
    "efficiency scores. Hydrology and Earth System Sciences, 23(10), "
    "4323–4331. https://doi.org/10.5194/hess-23-4323-2019",

    "Klemeš, V. (1974). The Hurst phenomenon: A puzzle? Water Resources "
    "Research, 10(4), 675–688. https://doi.org/10.1029/WR010i004p00675",

    "Kwiatkowski, D., Phillips, P. C. B., Schmidt, P., & Shin, Y. (1992). "
    "Testing the null hypothesis of stationarity against the alternative of a "
    "unit root. Journal of Econometrics, 54(1–3), 159–178.",

    "Lindström, G., Johansson, B., Persson, M., Gardelin, M., & Bergström, S. "
    "(1997). Development and test of the distributed HBV-96 hydrological "
    "model. Journal of Hydrology, 201(1–4), 272–288. "
    "https://doi.org/10.1016/S0022-1694(97)00041-3",

    "Ljung, G. M., & Box, G. E. P. (1978). On a measure of lack of fit in time "
    "series models. Biometrika, 65(2), 297–303.",

    "MacKinnon, J. G. (1996). Numerical distribution functions for unit root "
    "and cointegration tests. Journal of Applied Econometrics, 11(6), 601–618.",

    "Matalas, N. C. (1967). Mathematical assessment of synthetic hydrology. "
    "Water Resources Research, 3(4), 937–945. "
    "https://doi.org/10.1029/WR003i004p00937",

    "McKinney, W. (2010). Data structures for statistical computing in "
    "Python. Proceedings of the 9th Python in Science Conference, 56–61. "
    "https://doi.org/10.25080/Majora-92bf1922-00a",

    "Moriasi, D. N., Arnold, J. G., Van Liew, M. W., Bingner, R. L., Harmel, "
    "R. D., & Veith, T. L. (2007). Model evaluation guidelines for systematic "
    "quantification of accuracy in watershed simulations. Transactions of the "
    "ASABE, 50(3), 885–900. https://doi.org/10.13031/2013.23153",

    "Nash, J. E., & Sutcliffe, J. V. (1970). River flow forecasting through "
    "conceptual models part I — A discussion of principles. Journal of "
    "Hydrology, 10(3), 282–290. "
    "https://doi.org/10.1016/0022-1694(70)90255-6",

    "Newman, A. J., Clark, M. P., Sampson, K., Wood, A., Hay, L. E., Bock, A., "
    "… Duan, Q. (2015). Development of a large-sample watershed-scale "
    "hydrometeorological data set for the contiguous USA. Hydrology and Earth "
    "System Sciences, 19(1), 209–223. https://doi.org/10.5194/hess-19-209-2015",

    "Perrin, C., Michel, C., & Andréassian, V. (2003). Improvement of a "
    "parsimonious model for streamflow simulation. Journal of Hydrology, "
    "279(1–4), 275–289. https://doi.org/10.1016/S0022-1694(03)00225-7",

    "Salas, J. D., Delleur, J. W., Yevjevich, V., & Lane, W. L. (1980). "
    "Applied modeling of hydrologic time series. Water Resources "
    "Publications.",

    "Singh, V. P. (Ed.). (2002). Computer models of watershed hydrology. Water "
    "Resources Publications.",

    "Solomatine, D. P., & Ostfeld, A. (2008). Data-driven modelling: Some past "
    "experiences and new approaches. Journal of Hydroinformatics, 10(1), 3–22. "
    "https://doi.org/10.2166/hydro.2008.015",

    "Virtanen, P., Gommers, R., Oliphant, T. E., Haberland, M., Reddy, T., "
    "Cournapeau, D., … SciPy 1.0 Contributors. (2020). SciPy 1.0: Fundamental "
    "algorithms for scientific computing in Python. Nature Methods, 17(3), "
    "261–272. https://doi.org/10.1038/s41592-019-0686-2",

    "World Meteorological Organization. (2011). Manual on flood forecasting "
    "and warning (WMO-No. 1072). WMO.",
]


def write_references(doc):
    front_heading(doc, "REFERENCES", page_break=True)
    for ref in REFERENCES:
        reference(doc, ref)


# ── Appendix ─────────────────────────────────────────────────────────────────
# Listings are extracted from the live modules in src/, so the appendix can
# never drift from the code that produced the results in Chapter Four.

def appendix_listings():
    model = SRC / "model.py"
    return [
        ("APPENDIX-A",
         "Loading and monthly aggregation of the series, the logarithmic "
         "transform, the seasonal profile and the standardisation that "
         "removes the annual cycle, and the training and validation split "
         "(src/preprocess.py).",
         imports_of(SRC / "preprocess.py") + "\n\n\n"
         + extract(SRC / "preprocess.py", "log_transform", "inv_log_transform",
                   "seasonal_profile", "deseasonalise", "reseasonalise",
                   "cycle_months", "monthly_aggregate", "build_monthly_dataset",
                   "split_monthly")),

        ("APPENDIX-B",
         "Stationarity testing: the Augmented Dickey–Fuller and "
         "Kwiatkowski–Phillips–Schmidt–Shin tests, implemented from their "
         "defining regressions (src/model.py).",
         extract(model, "_ols", "adf_test", "kpss_test")),

        ("APPENDIX-C",
         "Correlation and residual diagnostics: the autocorrelation and "
         "partial autocorrelation functions, and the Ljung–Box, Jarque–Bera "
         "and ARCH tests (src/model.py).",
         extract(model, "acf", "pacf", "conf_interval", "ljung_box",
                 "jarque_bera", "arch_test")),

        ("APPENDIX-D",
         "The differencing operators, ordinary and seasonal, with their "
         "inverses; and estimation of the ARIMA coefficients by conditional "
         "sum of squares, with pure autoregressive models solved exactly by "
         "ordinary least squares, and the standard error of every estimated "
         "coefficient (src/model.py).",
         extract(model, "difference", "integrate_forecasts",
                 "seasonal_difference", "integrate_seasonal",
                 "apply_differencing", "invert_differencing") + "\n\n\n"
         + extract_methods(model, "ARIMA",
                           ["_expand", "_css_resid", "_unpack", "fit",
                            "standard_errors"])),

        ("APPENDIX-E",
         "Model identification: measuring the strength of the annual cycle, "
         "choosing the orders of differencing from the seasonality and "
         "stationarity evidence, and selecting the model order by a grid "
         "search over the Akaike Information Criterion (src/calibrate.py).",
         extract(SRC / "calibrate.py", "seasonal_strength",
                 "choose_seasonal_differencing", "choose_differencing",
                 "select_order")),

        ("APPENDIX-F",
         "Synthetic record generation: simulating monthly sequences of "
         "arbitrary length from a fitted model's own estimated parameters "
         "and residuals, and restoring the annual cycle and natural units "
         "(src/simulate.py).",
         imports_of(SRC / "simulate.py") + "\n\n\n"
         + extract(SRC / "simulate.py", "_simulate_w", "simulate_ensemble",
                   "generate_synthetic_record")),

        ("APPENDIX-G",
         "Property-based validation: summarising a monthly series by seven "
         "hydrologically meaningful statistics and comparing a synthetic "
         "ensemble's distribution of each to the historical record "
         "(src/validation.py).",
         imports_of(SRC / "validation.py") + "\n\n\n"
         + extract(SRC / "validation.py", "series_properties",
                   "compare_ensemble_to_historical")),
    ]


def write_appendix(doc):
    front_heading(doc, "APPENDIX", page_break=True)
    body(doc,
         "The forecasting framework described in Chapter Three was written "
         "from first principles in Python, without recourse to a third-party "
         "time-series package, so that every step of the analysis is open to "
         "inspection. The listings that follow reproduce the modules that "
         "produced the results reported in Chapter Four. They are presented in "
         "the order in which the pipeline executes them: data preparation, "
         "stationarity testing, correlation diagnostics, parameter "
         "estimation, order selection, stochastic ensemble generation and "
         "property-based validation.")

    for label, caption, code in appendix_listings():
        appendix_heading(doc, label, caption)
        code_block(doc, code)


# ── Assembly ─────────────────────────────────────────────────────────────────

def main():
    if not RESULTS_FILE.exists():
        raise FileNotFoundError(
            f"Results file not found: {RESULTS_FILE}\nRun run_pipeline.py first.")
    R = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
    DOCUMENTS_DIR.mkdir(exist_ok=True)

    doc = Document()
    setup_styles(doc)
    setup_page(doc.sections[0])

    # Section 1 — title page, unnumbered
    clear_footer(doc.sections[0])
    front.write_title_page(doc)

    # Section 2 — preliminary pages, lower-case Roman numerals
    new_section(doc, page_fmt="lowerRoman", start=1)
    front.write_abstract(doc, R)
    front.write_certification(doc)
    front.write_acknowledgement(doc)
    front.write_dedication(doc)
    front.write_abbreviations(doc)
    front.write_definitions(doc)
    front.write_lists(doc)

    # Section 3 — the body of the report, Arabic numerals from 1
    new_section(doc, page_fmt="decimal", start=1)
    eq = EquationCounter()
    front.write_chapter1(doc, eq)
    front.write_chapter2(doc, eq)
    ch345.write_chapter3(doc, R, FIGURES_DIR, eq)
    ch345.write_chapter4(doc, R, FIGURES_DIR, eq)
    ch345.write_chapter5(doc, R, eq)
    write_references(doc)
    write_appendix(doc)

    doc.save(OUTPUT_FILE)
    print(f"Saved: {OUTPUT_FILE}")
    print(f"Equations numbered: {eq.n}")
    return OUTPUT_FILE


if __name__ == "__main__":
    main()
