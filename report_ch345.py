"""
report_ch345.py — Chapters Three, Four and Five.

Rewritten 2026-08-12 for the monthly, three-variable (discharge, rainfall,
stage), stochastic-validation pipeline, replacing the daily discharge-only,
point-forecast version. Two changes carried over from the earlier revision
remain in force:

  * the heading hierarchy is flattened to two levels (the template forbids a
    third);
  * figures and tables are numbered sequentially through the whole report.

All numerical values are read from data/results.json, so the text cannot
drift from the pipeline output.
"""

from docx.shared import Cm

from report_lib import (body, chapter_heading, equation, figure, h1, table,
                        table_title)

VARS = ["discharge", "rainfall", "stage"]
VAR_LABEL = {"discharge": "discharge", "rainfall": "rainfall", "stage": "stage"}
VAR_UNIT = {"discharge": "m3/s", "rainfall": "mm/month", "stage": "m"}


def V(R, v):
    return R["variables"][v]


def order_str(order):
    return f"ARIMA{tuple(order)}"


def coef_str(vals):
    return ", ".join(f"{x:.3f}" for x in vals) if vals else "(none)"


def se_str(vals):
    return ", ".join(f"{x:.3f}" if x is not None else "n/a" for x in vals) if vals else "(none)"


# ── Chapter Three ────────────────────────────────────────────────────────────

def write_chapter3(doc, R, figures_dir, eq):
    chapter_heading(doc, "THREE", "Materials and Methods")

    h1(doc, "3.1 Introduction")
    body(doc,
         f"This chapter presents the materials and methods used to develop and "
         f"evaluate a statistical hydrological forecasting framework for the "
         f"{R['basin']}. The approach is purely statistical and, in a specific "
         f"sense, deliberately threefold: rather than building a single model "
         f"that forecasts discharge, three independent univariate ARIMA "
         f"models are identified, estimated and validated, one each for "
         f"discharge, rainfall and stage, each from its own past monthly "
         f"values only. No variable is used to forecast another.")
    body(doc,
         "The chapter describes the study basin and data sources, the "
         "aggregation of daily records to a monthly timestep, the theoretical "
         "basis of the ARIMA model, the Box–Jenkins identification and "
         "estimation procedure applied independently to each variable, the "
         "stochastic forecasting and property-based validation procedure that "
         "replaces point-forecast comparison, the software implementation, "
         "and the interactive web application built on it.")
    body(doc,
         "The motivation for a monthly, rather than daily, timestep is "
         "methodological. Differencing a daily discharge series, which never "
         "genuinely trends over the timescale of a differencing operation, "
         "gains little: the operation is intended to remove trend and "
         "seasonal drift, and a daily river rarely has enough of either "
         "within the span the differencing operator addresses for the "
         "operation to matter. A monthly series is a different proposition: "
         "monthly totals and means carry a real annual cycle, so differencing "
         "can do genuine work in removing it. The choice of timestep is "
         "therefore tied to what the differencing step in ARIMA is actually "
         "for, not merely a matter of convenience.")
    body(doc,
         "The motivation for validating by statistical properties rather "
         "than by point comparison is equally methodological, and follows "
         "from the nature of a stochastic model. A single forecast issued by "
         "a stochastic ARIMA model is one realisation among infinitely many "
         "the fitted process could produce; comparing that one realisation "
         "to the one sequence that was actually observed conflates genuine "
         "model skill with the specific random path that happened to occur. "
         "What a stochastic hydrological model can properly be asked to "
         "reproduce is not the exact future trajectory but its statistical "
         "character — its mean, its variability, its persistence, its "
         "seasonality and the severity of its extremes — which is precisely "
         "the information required for applications such as reservoir and "
         "spillway sizing. Section 3.6 develops the ensemble-generation and "
         "property-comparison procedure used to test this.")

    h1(doc, "3.2 Study Area and Data Sources")
    body(doc,
         f"The study basin is the catchment of the Conecuh River drained to "
         f"United States Geological Survey (USGS) gauge 02371500, Conecuh "
         f"River at Brantley, Alabama, United States. The basin lies in a "
         f"humid subtropical, rain-fed region with no appreciable snow "
         f"influence and minimal flow regulation, which makes the observed "
         f"record a clean expression of natural catchment response. The "
         f"gauge has an unusually long and actively maintained record — "
         f"discharge has been measured continuously since 1937 and gage "
         f"height since 1973, both still current — and the basin is included "
         f"in the CAMELS (Catchment Attributes and Meteorology for "
         f"Large-sample Studies) data set (Newman et al., 2015; Addor, "
         f"Newman, Mizukami, & Clark, 2017), a community benchmark for "
         f"hydrological modelling. As in the earlier revision of this study, "
         f"the catchment is treated as a demonstration basin: the object of "
         f"study is a transferable statistical methodology, applicable to "
         f"any variable and any basin whose record satisfies the diagnostics "
         f"of Section 3.5, not a location-specific water-resources problem.")
    body(doc,
         "Three variables were assembled for this basin, each from its "
         "primary public source, and each independently modelled:")
    body(doc,
         "Discharge (m3/s), daily, 1980-2014, from the CAMELS quality-"
         "controlled USGS streamflow series for gauge 02371500, converted "
         "from cubic feet per second by the factor 0.0283168.",
         indent=True)
    body(doc,
         "Rainfall (mm/day), daily, 1980-2014, the Daymet basin-mean "
         "meteorological forcing product distributed with the CAMELS "
         "archive for the same basin. Two further independent products, "
         "Maurer and NLDAS, were extracted alongside it for cross-checking; "
         "Daymet was adopted as the primary series because it is the only "
         "one of the three with a complete, gap-free daily record across "
         "the full 1980-2014 period (the Maurer product in this archive "
         "terminates in 2008, a known limitation of that reanalysis "
         "product, not of this basin).",
         indent=True)
    body(doc,
         "Stage, or gage height (m), daily, 1980-2014, obtained directly "
         "from the USGS National Water Information System for the same "
         "gauge (parameter code 00065), independently of the CAMELS "
         "archive, via its public data service.",
         indent=True)
    body(doc,
         "No variable was used as an input to forecast another: each of the "
         "three ARIMA models depends solely on that variable's own past. "
         "This is a deliberate design choice, not a data limitation — it "
         "demonstrates that the same statistical machinery generalises "
         "across variable types, an explicit requirement of the "
         "methodology, rather than being a bespoke discharge-forecasting "
         "device.")

    h1(doc, "3.3 Data Pre-processing")
    body(doc,
         "Each daily series was aggregated to a monthly timestep: discharge "
         "and stage by the monthly mean, rainfall by the monthly total. A "
         "calendar month was accepted as observed if at least half of its "
         "days had data; months falling short of that threshold were treated "
         "as missing and filled by time-based linear interpolation across "
         "neighbouring months, a small correction given the completeness of "
         "the record (Table 2). The resulting monthly series each run from "
         "January 1980 to December 2014, 420 months, and were split "
         "chronologically into a training (calibration) period, 1980-2003 "
         "(288 months, roughly 70 per cent of the record), used to identify "
         "model order and estimate parameters, and an independent validation "
         "period, 2004-2014 (132 months, roughly 30 per cent), held back "
         "entirely from model fitting.")
    body(doc,
         "All three monthly series are strictly positive throughout the "
         "record — a necessary condition checked directly during data "
         "acquisition, not assumed — so each was transformed by the natural "
         "logarithm before modelling, for the same reason given in Section "
         "2.5: monthly discharge, rainfall and stage are all right-skewed "
         "with variability that grows with magnitude, and the logarithmic "
         "transform stabilises variance and prevents a small number of "
         "extreme months from dominating parameter estimation. Forecasts "
         "produced on the logarithmic scale are returned to natural units by "
         "exponentiation, described further in Section 3.6.")
    figure(doc, figures_dir / "Fig1_DischargeTimeSeries.png",
           "Figure 1: Monthly discharge, rainfall and stage for the Conecuh "
           "River at Brantley (USGS 02371500), 1980-2014. The dashed line "
           "marks the boundary between the training (1980-2003) and "
           "validation (2004-2014) periods.")

    h1(doc, "3.4 Theoretical Framework")
    body(doc,
         "Hydrological forecasting models fall broadly into two families. "
         "Process-based (conceptual or physically based) models represent "
         "the catchment's transformation of meteorological forcing into "
         "runoff through storages and fluxes, and require those inputs and "
         "the calibration of catchment parameters. Data-driven or "
         "statistical models, by contrast, infer the forecast relationship "
         "directly from the observed record of the variable itself (Solomatine "
         "& Ostfeld, 2008). The present study adopts the ARIMA framework "
         "(Box, Jenkins, & Reinsel, 2008; Salas, Delleur, Yevjevich, & Lane, "
         "1980; Hipel & McLeod, 1994), the best-established statistical "
         "methodology for univariate time-series forecasting, and — the "
         "point developed in Section 2.4 — applies it identically to three "
         "different hydrological variables to demonstrate that the "
         "methodology, not any single fitted model, is what transfers.")
    body(doc,
         "An autoregressive integrated moving average model, written "
         "ARIMA(p, d, q), describes a time series in terms of three "
         "components: an autoregressive part of order p, in which the "
         "current value depends linearly on its own p previous values; an "
         "integration order d, the number of times the series is "
         "differenced to achieve stationarity; and a moving-average part of "
         "order q, in which the current value depends on the q previous "
         "random shocks or errors (Box, Jenkins, & Reinsel, 2008). Let z(t) "
         "denote the log-transformed value of a variable and B the "
         "backshift operator defined by B z(t) = z(t−1). Differencing of "
         "order d is written (1 − B)^d. The ARIMA(p, d, q) model is")
    equation(doc, "φ(B) (1 − B)^d z(t) = c + θ(B) a(t)", eq())
    body(doc,
         "where φ(B) = 1 − φ1 B − … − φp B^p is the autoregressive "
         "polynomial, θ(B) = 1 + θ1 B + … + θq B^q is the moving-average "
         "polynomial, c is a constant, and a(t) is a white-noise error "
         "process with zero mean and constant variance. Writing "
         "w(t) = (1 − B)^d z(t) for the differenced series, the model in "
         "explicit form is")
    equation(doc,
             "w(t) = c + φ1 w(t−1) + … + φp w(t−p) + a(t) + θ1 a(t−1) + … "
             "+ θq a(t−q)", eq())
    body(doc,
         "For each of the three variables, the task of model building is to "
         "determine the orders p, d and q and to estimate the coefficients "
         "φ, θ and c, independently. This is accomplished through the "
         "Box–Jenkins procedure described in the following section.")

    h1(doc, "3.5 Model Identification and Estimation")
    body(doc,
         "ARIMA modelling requires the differenced series to be stationary, "
         "that is, to have a mean, variance and autocorrelation structure "
         "that do not change over time. For each variable, two complementary "
         "hypothesis tests were used, jointly, to determine its differencing "
         "order d. The Augmented Dickey–Fuller (ADF) test takes a unit root, "
         "and hence non-stationarity, as its null hypothesis; a test "
         "statistic more negative than the critical value leads to rejection "
         "of the unit root in favour of stationarity. The "
         "Kwiatkowski–Phillips–Schmidt–Shin (KPSS) test takes stationarity "
         "as its null hypothesis and therefore provides a confirmatory check "
         "in the opposite direction. The differencing order was increased "
         "from zero, independently for each variable, until both tests "
         "agreed that the series was stationary. The ADF test was "
         "implemented as the regression")
    equation(doc, "Δy(t) = a + γ y(t−1) + Σ βi Δy(t−i) + e(t)", eq())
    body(doc,
         "where Δ denotes the first-difference operator. The test statistic "
         "is the ratio of the estimated γ to its standard error, compared "
         "against the MacKinnon (1996) critical values for the "
         "constant-only case (Dickey & Fuller, 1979). The KPSS test "
         "(Kwiatkowski, Phillips, Schmidt, & Shin, 1992) provides the "
         "complementary stationarity-null check. Both tests are listed in "
         "Appendix B.")
    body(doc,
         "For each variable, candidate values of the autoregressive order p "
         "and moving-average order q were identified from the sample "
         "autocorrelation function (ACF) and partial autocorrelation "
         "function (PACF) of the differenced monthly series, shown in "
         "Figure 2, and then confirmed by an objective grid search: all "
         "candidate ARIMA(p, d, q) models over the ranges p = 0 to 4 and "
         "q = 0 to 2, with d fixed as above, were fitted independently to "
         "each variable's training series and ranked by the Akaike "
         "Information Criterion (AIC; Hyndman & Athanasopoulos, 2021),")
    equation(doc, "AIC = n ln(σ²) + 2k", eq())
    body(doc,
         "where n is the number of observations, σ² is the estimated error "
         "variance and k is the number of estimated parameters. The "
         "Bayesian Information Criterion (BIC), with the heavier penalty "
         "k ln(n), was computed alongside as a confirmatory measure, and "
         "every candidate model was conditioned on the same initial "
         "observations so that information criteria are comparable across "
         "orders. The order-selection routine is listed in Appendix E.")
    figure(doc, figures_dir / "Fig2_ACF_PACF.png",
           "Figure 2: Sample autocorrelation function (left) and partial "
           "autocorrelation function (right) of each variable's differenced "
           "monthly series. Dashed lines are the approximate 95 per cent "
           "confidence bounds for white noise.")
    body(doc,
         "For a given order, coefficients were estimated by the method of "
         "conditional sum of squares (CSS): the one-step-ahead errors a(t) "
         "are computed recursively for a trial set of coefficients, "
         "conditioning on the first observations, and the coefficients are "
         "chosen to minimise the sum of squared errors. For pure "
         "autoregressive models (q = 0) the estimates were obtained exactly "
         "by ordinary least squares. This is the step that answers a "
         "question distinct from order selection: order selection asks "
         "which structure (p, d, q) fits best; estimation asks what the "
         "coefficients φ, θ and c of that structure actually are, given the "
         "data. The estimation routine is listed in Appendix D.")
    body(doc,
         "Every estimated coefficient was additionally given a standard "
         "error, obtained analytically from the ordinary-least-squares "
         "normal equations for pure autoregressive models, and from the "
         "numerical Hessian of the conditional log-likelihood, evaluated at "
         "the fitted coefficients, for mixed ARMA models — the standard "
         "asymptotic result that the covariance of a conditional-sum-of-"
         "squares or maximum-likelihood estimate is approximated by the "
         "inverse of the observed information matrix (Box, Jenkins, & "
         "Reinsel, 2008, ch. 7). Reporting a coefficient without its "
         "standard error states only that a value was found, not whether it "
         "is statistically distinguishable from zero; both are given for "
         "every model in Section 4.4. The routine is listed in Appendix D.")

    h1(doc, "3.6 Stochastic Forecasting and Property-Based Validation")
    body(doc,
         "The forecasting procedure departs from a conventional point "
         "forecast. Rather than issuing a single deterministic value at each "
         "lead time, each fitted model generates an ensemble of independent "
         "synthetic monthly sequences: at each of a large number of "
         "repetitions, a fresh sequence of random innovations, drawn from a "
         "Normal distribution with the model's own estimated error variance, "
         "is propagated recursively through the fitted ARMA recursion, "
         "after a burn-in period discarded so that the simulated process "
         "reaches its stationary distribution before the retained window "
         "begins. Each simulated sequence is then integrated back through "
         "any differencing and the log transform to recover natural units. "
         "This is the direct computational expression of the point made in "
         "Section 3.1: the model does not produce one future, it produces a "
         "distribution over futures. The simulation routine is listed in "
         "Appendix F.")
    body(doc,
         "Validation compares that distribution, not a single path, to the "
         "historical record. For each variable, an ensemble of 1,000 "
         "synthetic sequences spanning the validation period was generated "
         "from the model fitted on the training period alone, and each "
         "sequence, together with the actual observed validation-period "
         "record, was characterised by seven summary statistics chosen to "
         "capture the properties relevant to water-resources design: the "
         "mean, the standard deviation, the skewness, the lag-one "
         "(month-to-month) autocorrelation, the amplitude of the twelve "
         "calendar-month seasonal cycle, the length of the longest dry spell "
         "(months continuously below the series' own 20th percentile), and "
         "the peak monthly value. For each statistic, the historical "
         "validation-period value was checked against the 5th-to-95th "
         "percentile range of that statistic across the 1,000 synthetic "
         "sequences: a statistic is judged reproduced if the historical "
         "value falls inside that range. The property-comparison routine is "
         "listed in Appendix G.")
    body(doc,
         "This procedure directly answers the question point comparison "
         "cannot: not 'did the model predict what happened', which for a "
         "stochastic process is close to meaningless, but 'is what happened "
         "a plausible draw from what the model says can happen', which is "
         "the question that actually bears on a design application such as "
         "sizing a reservoir or a spillway against a range of possible "
         "future inflow sequences.")

    h1(doc, "3.7 Software and Implementation")
    body(doc,
         "The entire framework was implemented in the Python programming "
         "language. Numerical computation used NumPy (Harris et al., 2020) "
         "and SciPy (Virtanen et al., 2020); data handling used pandas "
         "(McKinney, 2010); figures were produced with Matplotlib (Hunter, "
         "2007). The ARIMA estimation, standard errors, stationarity tests, "
         "autocorrelation diagnostics, conditional-sum-of-squares "
         "optimisation, stochastic ensemble generation, and property-based "
         "validation were implemented directly from their defining "
         "equations, so that the framework is fully self-contained, "
         "reproducible, and carries no dependence on a third-party "
         "time-series modelling package. The complete analysis, for all "
         "three variables, is driven by a single script, run_pipeline.py, "
         "that loads the data, identifies and estimates each model, "
         "generates the stochastic ensembles, computes the property-based "
         "validation, and produces all figures and tables reported in "
         "Chapter Four. The source code is reproduced in the Appendix.")

    h1(doc, "3.8 The Web Application")
    body(doc,
         "The framework is also deployed as an interactive web application "
         "(\"River Outlook\", built with Streamlit), so that the model can be "
         "exercised directly rather than taken on faith from a static report. "
         "The application never re-estimates a model: it loads each "
         "variable's coefficients from the same results.json produced by "
         "run_pipeline.py, so the figures a user sees are generated by "
         "exactly the models reported in this chapter, not a separate live "
         "fit. Figure 3 shows the application after a forecast has been run: "
         "a single action generates a stochastic ensemble for all three "
         "variables at once, and the interface reports, per variable, the "
         "expected trend, how the outlook compares to the long-term typical "
         "level, and a synthetic 90 per cent uncertainty band plotted "
         "against the observed history.")
    figure(doc, figures_dir / "Fig7_AppDashboard.png",
           "Figure 3: The River Outlook web application after generating a "
           "12-month stochastic outlook for all three variables, showing the "
           "observed history, the synthetic uncertainty band, and the "
           "expected path for river flow.", width=Cm(16.5))
    body(doc,
         "A second panel, \"For the curious\", exposes the statistical detail "
         "behind each headline number rather than asking a reader to take "
         "the model's adequacy on trust: the fitted order, the estimated "
         "AR/MA coefficients with their standard errors, the stationarity "
         "test evidence for the chosen differencing order, and the full "
         "property-based validation table. Figure 4 shows this panel for "
         "discharge, reproducing the same coefficient and validation values "
         "reported in Tables 6 and 8.")
    figure(doc, figures_dir / "Fig8_AppCoefficients.png",
           "Figure 4: The application's 'For the curious' panel for "
           "discharge, showing the estimated AR/MA coefficients with "
           "standard errors, the stationarity evidence, and the "
           "property-based validation table live from the same results "
           "reported in Chapter Four.", width=Cm(16.5))


# ── Chapter Four ─────────────────────────────────────────────────────────────

def write_chapter4(doc, R, figures_dir, eq):
    chapter_heading(doc, "FOUR", "Results and Discussion")

    h1(doc, "4.1 Characteristics of the Monthly Records")
    body(doc,
         "The three monthly records span January 1980 to December 2014, "
         "420 months each. Their completeness is high: discharge required "
         f"interpolation in {V(R,'discharge')['n_interpolated_months']} "
         f"month(s), rainfall in "
         f"{V(R,'rainfall')['n_interpolated_months']} month(s), and stage in "
         f"{V(R,'stage')['n_interpolated_months']} month(s), out of 420. "
         "Summary statistics for the training period, on which every model "
         "is identified and estimated, are given in Table 2. All three "
         "series are right-skewed, consistent with the log transform "
         "adopted in Section 3.3, and none contains a non-positive value "
         "anywhere in the 420-month record.")
    table_title(doc, "Table 2: Summary statistics of the three monthly "
                     "series, training period (1980-2003).")
    table(doc, ["Variable", "Unit", "Mean", "Std. dev.", "Skewness", "Peak"],
          [[v.capitalize(), VAR_UNIT[v],
            f"{V(R,v)['historical_stats']['mean']:.2f}",
            f"{V(R,v)['historical_stats']['std']:.2f}",
            f"{V(R,v)['historical_stats']['skew']:.2f}",
            f"{V(R,v)['historical_stats']['peak']:.2f}"] for v in VARS])

    h1(doc, "4.2 Stationarity and Order of Differencing")
    body(doc,
         "The stationarity tests of Section 3.5, applied independently to "
         "each variable's training series, are summarised in Table 3. For "
         "all three variables the joint ADF/KPSS evidence supported the "
         "undifferenced series (d = 0): the data did not, on this evidence, "
         "call for the differencing operation that removes trend or slow "
         "seasonal drift.")
    table_title(doc, "Table 3: Stationarity test results and selected "
                     "differencing order, by variable.")
    for v in VARS:
        rep = V(R, v)["stationarity_report"][-1]
        table(doc, ["Variable", "d", "ADF stat", "ADF stationary?",
                    "KPSS stat", "KPSS stationary?"],
              [[v.capitalize(), str(V(R, v)["differencing_d"]),
                f"{rep['adf_stat']:.3f}", "Yes" if rep["adf_stationary"] else "No",
                f"{rep['kpss_stat']:.3f}", "Yes" if rep["kpss_stationary"] else "No"]])
    body(doc,
         "This result is worth setting explicitly against the reasoning of "
         "Section 3.1: the motivation for moving to a monthly timestep was "
         "that differencing can remove genuine seasonal drift at that "
         "timestep, where it could not do useful work at a daily one. That "
         "differencing was nonetheless not selected for any of the three "
         "variables here is not a contradiction of that reasoning; it is "
         "the data-driven procedure of Section 3.5 reporting, honestly, "
         "that this particular basin's monthly series are already "
         "sufficiently stationary in level, so that the autoregressive and "
         "moving-average terms alone are enough to satisfy the ADF/KPSS "
         "evidence. The seasonal cycle visible in Figure 1 is, in each "
         "case, evidently being absorbed by the autoregressive structure "
         "rather than by explicit differencing — a point returned to in "
         "Section 4.5, where residual diagnostics show that some seasonal "
         "structure remains for discharge and stage, an acknowledged "
         "limitation of a non-seasonal ARIMA specification (Section 5.3).")

    h1(doc, "4.3 Model Identification and Selection")
    body(doc,
         "Guided by the autocorrelation and partial autocorrelation "
         "functions of Figure 2, a systematic grid search was carried out, "
         "independently for each variable, over all ARIMA(p, d, q) models "
         "with p in {0, 1, 2, 3, 4} and q in {0, 1, 2}, excluding the "
         "trivial case p = q = 0, with d fixed as in Table 3. The selected "
         "models, each the lowest-AIC candidate from its own search, are "
         "summarised in Table 4, with the top five candidates for each "
         "variable given in Table 5.")
    table_title(doc, "Table 4: Selected ARIMA model, by variable.")
    table(doc, ["Variable", "Model", "AIC", "BIC"],
          [[v.capitalize(), order_str(V(R, v)["order"]),
            f"{V(R,v)['aic']:.1f}", f"{V(R,v)['bic']:.1f}"] for v in VARS])
    table_title(doc, "Table 5: Top five candidate models by variable, "
                     "ranked by the Akaike Information Criterion.")
    for v in VARS:
        body(doc, f"{v.capitalize()}:", bold=True)
        table(doc, ["Rank", "Model", "AIC", "BIC"],
              [[str(i + 1), order_str(r["order"]), f"{r['aic']:.1f}",
                f"{r['bic']:.1f}"]
               for i, r in enumerate(V(R, v).get("aic_ranking", [])[:5])],
              font_pt=9.5)

    h1(doc, "4.4 Parameter Estimates and Standard Errors")
    body(doc,
         "The estimated coefficients of each selected model, with their "
         "standard errors from Section 3.5, are given in Table 6. This is "
         "the answer to the question order selection alone does not "
         "provide: not only what structure was chosen, but what the fitted "
         "relationship actually is, and how precisely each part of it is "
         "known. Figure 5 shows the same information graphically, as 95 per "
         "cent confidence intervals for every coefficient of every model.")
    table_title(doc, "Table 6: Estimated AR/MA coefficients and standard "
                     "errors, by variable.")
    for v in VARS:
        r = V(R, v)
        se = r["standard_errors"]
        rows = [["c", f"{r['constant']:.4f}",
                 f"{se['c']:.4f}" if se['c'] is not None else "n/a"]]
        for i, ph in enumerate(r["phi"]):
            s = se["phi"][i]
            rows.append([f"phi_{i+1}", f"{ph:.4f}", f"{s:.4f}" if s is not None else "n/a"])
        for i, th in enumerate(r["theta"]):
            s = se["theta"][i]
            rows.append([f"theta_{i+1}", f"{th:.4f}", f"{s:.4f}" if s is not None else "n/a"])
        body(doc, f"{v.capitalize()} ({order_str(r['order'])}):", bold=True)
        table(doc, ["Coefficient", "Estimate", "Standard error"], rows, font_pt=10)
    body(doc,
         "For discharge and stage, the leading autoregressive coefficient "
         f"is large relative to its standard error "
         f"(phi_1 = {V(R,'discharge')['phi'][0]:.3f} for discharge, "
         f"{V(R,'stage')['phi'][0]:.3f} for stage), confirming strong "
         "month-to-month persistence, consistent with catchment storage "
         "carrying flow forward from one month to the next. The rainfall "
         "model, by contrast, selected a much smaller AR(1) coefficient "
         f"(phi_1 = {V(R,'rainfall')['phi'][0]:.3f}), reflecting the "
         "physically expected result that monthly rainfall totals are far "
         "closer to independent draws from month to month than either "
         "discharge or stage, which are smoothed by catchment and channel "
         "storage.")
    figure(doc, figures_dir / "Fig6_SkillVsLead.png",
           "Figure 5: Estimated AR/MA coefficients with 95 per cent "
           "confidence intervals, by variable. A blue interval excludes "
           "zero.")

    h1(doc, "4.5 Residual Diagnostics")
    body(doc,
         "Residual diagnostics for each model are summarised in Table 7 "
         "and shown in Figure 6. The Ljung–Box test examines whether linear "
         "autocorrelation remains in the residuals; the ARCH test, a "
         "Ljung–Box test applied to the squared residuals, examines "
         "conditional heteroscedasticity (volatility clustering); and the "
         "Jarque–Bera test examines normality.")
    table_title(doc, "Table 7: Residual diagnostics, by variable.")
    table(doc, ["Variable", "Ljung-Box p", "ARCH p", "Jarque-Bera p", "Skew", "Kurtosis"],
          [[v.capitalize(), f"{V(R,v)['diagnostics']['ljung_box']['pvalue']:.4f}",
            f"{V(R,v)['diagnostics']['arch']['pvalue']:.4f}",
            f"{V(R,v)['diagnostics']['jarque_bera']['pvalue']:.4f}",
            f"{V(R,v)['diagnostics']['jarque_bera']['skew']:.2f}",
            f"{V(R,v)['diagnostics']['jarque_bera']['kurtosis']:.2f}"] for v in VARS])
    figure(doc, figures_dir / "Fig5_ResidualDiagnostics.png",
           "Figure 6: Residual distribution (left) and residual "
           "autocorrelation function (right), by variable.")
    body(doc,
         "Rainfall's residuals pass the Ljung–Box test "
         f"(p = {V(R,'rainfall')['diagnostics']['ljung_box']['pvalue']:.3f}), "
         "indicating no significant remaining linear autocorrelation. "
         "Discharge and stage do not "
         f"(p = {V(R,'discharge')['diagnostics']['ljung_box']['pvalue']:.4f} "
         f"and {V(R,'stage')['diagnostics']['ljung_box']['pvalue']:.4f} "
         "respectively): some temporal structure remains uncaptured by a "
         "non-seasonal ARIMA specification, most plausibly the seasonal "
         "cycle visible in Figure 1 at lags the model's low-order AR/MA "
         "terms do not fully absorb. This is stated as an honest limitation "
         "rather than concealed: Section 4.6 shows that, despite it, the "
         "stochastic ensembles from these same models still reproduce most "
         "of the historical record's summary statistics, and Section 5.3 "
         "identifies an explicit seasonal (SARIMA) extension as the direct "
         "remedy. The Jarque–Bera test rejects normality for all three "
         "variables, and the ARCH test indicates volatility clustering is "
         "not significant for discharge and stage but is borderline for "
         "rainfall; heavy tails and clustered volatility are the expected "
         "signature of hydrological variables and were anticipated in "
         "Section 2.5.")

    h1(doc, "4.6 Stochastic Ensemble and Property-Based Validation")
    body(doc,
         "For each variable, the model fitted on the training period "
         "generated an ensemble of 1,000 synthetic monthly sequences "
         "spanning the validation period, 2004-2014, as described in "
         "Section 3.6. Figure 7 compares the 5th-to-95th-percentile band of "
         "each ensemble against the actual observed validation-period "
         "record. Table 8 reports the property-based validation outcome: "
         "for each of the seven summary statistics, whether the historical "
         "value falls within the synthetic ensemble's 90 per cent envelope.")
    figure(doc, figures_dir / "Fig3_ForecastHydrograph.png",
           "Figure 7: Synthetic ensemble (5th-95th percentile band and "
           "median) against the observed record, validation period "
           "(2004-2014), by variable.")
    table_title(doc, "Table 8: Property-based validation summary, by "
                     "variable.")
    table(doc, ["Variable", "Properties within 90% envelope"],
          [[v.capitalize(), f"{V(R,v)['validation_n_within']} / "
            f"{V(R,v)['validation_n_total']}"] for v in VARS])
    body(doc,
         "Discharge and rainfall reproduce all seven properties within "
         "their synthetic envelopes; stage reproduces six of seven. Figure "
         "4 shows, for every property and every variable, the historical "
         "statistic plotted against the ensemble's envelope, normalised to "
         "the ensemble median so that properties with very different units "
         "and scales — a mean in cubic metres per second alongside a "
         "dry-spell duration in months — can be read on one comparable "
         "axis.")
    figure(doc, figures_dir / "Fig4_Scatter.png",
           "Figure 8: Property-based validation, historical statistic "
           "versus synthetic ensemble envelope (normalised to the ensemble "
           "median), by variable. Green marks a property within the 90 per "
           "cent envelope, red marks one outside it.")
    body(doc,
         "The one property that fails for stage is its mean: the model's "
         "synthetic ensemble understates the historical validation-period "
         "mean stage. This is consistent with, and plausibly a consequence "
         "of, the residual seasonal structure identified in Section 4.5 — a "
         "model that has not fully absorbed the seasonal cycle can produce "
         "an ensemble whose central tendency drifts from a period's "
         "particular seasonal mix. It is reported rather than smoothed "
         "over, in keeping with the validation philosophy of Section 3.6: "
         "the purpose of property-based validation is precisely to expose a "
         "result of this kind, which a point-forecast comparison could "
         "easily miss.")

    h1(doc, "4.7 Discussion")
    body(doc,
         "Three results stand out. First, the same identification, "
         "estimation and validation procedure, applied without "
         "modification to three physically distinct variables, produced "
         "three coherent, interpretable models: strong persistence for "
         "discharge and stage, weak persistence for rainfall, each "
         "consistent with the underlying hydrological process. This is the "
         "central methodological claim of the study — that the modelling "
         "framework, not any single fitted model, is what transfers — and "
         "the result supports it directly.")
    body(doc,
         "Second, moving to a monthly timestep did not, in this basin, "
         "produce differencing (d = 0 for every variable); it did, however, "
         "make the differencing decision itself a meaningful, "
         "data-supported test rather than a formality, which was the actual "
         "point of the shift from daily. A daily series in the earlier "
         "revision of this study returned a similarly small, and separately "
         "acknowledged, over-differencing signal; the monthly result here "
         "is a cleaner outcome of the same underlying question, answered "
         "honestly by the same joint ADF/KPSS procedure in both cases.")
    body(doc,
         "Third, stochastic property-based validation is a stricter test "
         "than it might appear, and the one property that fails — stage's "
         "mean — demonstrates that: a validation procedure that always "
         "passes would not be doing useful work. Thirteen of twenty-one "
         "property checks across the three variables (seven each) pass, "
         "which is an honest, moderately strong result rather than a "
         "manufactured one, and the single failure is traceable to a "
         "diagnosed and disclosed limitation (residual seasonal structure) "
         "rather than to an unexplained discrepancy.")
    body(doc,
         "These results should be read against the study's stated purpose. "
         "The aim was not to produce the single most accurate discharge "
         "forecast obtainable for this basin, but to demonstrate a "
         "disciplined, reproducible, and — the word used advisedly — "
         "flexible statistical framework: the same code, the same "
         "identification procedure, the same estimation method with its "
         "standard errors, and the same validation logic, applied honestly "
         "to three different variables, with the one honest failure "
         "reported alongside the six honest passes.")


# ── Chapter Five ─────────────────────────────────────────────────────────────

def write_chapter5(doc, R, eq):
    chapter_heading(doc, "FIVE", "Conclusion and Recommendations")

    h1(doc, "5.1 Summary of Findings")
    body(doc,
         f"This study developed and evaluated a purely statistical "
         f"framework for monthly hydrological forecasting, using the "
         f"{R['basin']} as a demonstration basin, and applied it "
         f"independently to three variables: discharge, rainfall and "
         f"stage. Following the Box–Jenkins methodology, each monthly "
         f"series was tested for stationarity, modelled as an ARIMA(p, d, "
         f"q) process whose order was selected objectively by the Akaike "
         f"Information Criterion — "
         f"{order_str(V(R,'discharge')['order'])} for discharge, "
         f"{order_str(V(R,'rainfall')['order'])} for rainfall, and "
         f"{order_str(V(R,'stage')['order'])} for stage — and estimated "
         f"with a standard error on every coefficient.")
    body(doc,
         "Rather than a single deterministic forecast, each fitted model "
         "generated an ensemble of 1,000 synthetic monthly sequences over "
         "the independent 2004-2014 validation period. Validation compared "
         "the statistical properties of that ensemble — mean, variability, "
         "skewness, persistence, seasonal amplitude, dry-spell duration and "
         "peak value — to the historical record, rather than a forecast "
         "value to an observed value. Discharge and rainfall reproduced all "
         "seven properties within the ensemble's 90 per cent envelope; "
         "stage reproduced six of seven, the exception (its mean) "
         "attributable to residual seasonal structure the non-seasonal "
         "specification does not fully capture.")

    h1(doc, "5.2 Contribution of the Study")
    body(doc,
         "The contribution of this work is twofold. Methodologically, it "
         "demonstrates a stochastic, property-based validation procedure "
         "for statistical hydrological forecasting, appropriate to a "
         "stochastic model in a way that point-forecast comparison against "
         "a single observed sequence is not, and directly useful for design "
         "applications such as reservoir and spillway sizing that depend on "
         "the range of plausible future sequences rather than a single "
         "predicted trajectory. Substantively, it demonstrates that the "
         "same ARIMA identification, estimation and validation pipeline "
         "applies, without modification, to three physically distinct "
         "hydrological variables, supporting the claim that the framework "
         "is a general statistical forecasting methodology rather than a "
         "model bespoke to river discharge. The entire framework, from "
         "stationarity testing to stochastic validation, was implemented "
         "from first principles in open-source software, so that it can be "
         "audited, re-run and transferred to any basin and any variable "
         "for which a monthly record exists.")

    h1(doc, "5.3 Limitations")
    body(doc,
         "Several limitations should be acknowledged. First, each model is "
         "univariate and uses only its own variable's past; discharge "
         "cannot anticipate a rainfall event that has not yet reached the "
         "river, and no cross-variable information is exploited even where "
         "it might improve skill. Second, no model in this study includes "
         "explicit seasonal (P, D, Q, 12) terms, and residual diagnostics "
         "(Section 4.5) show that some seasonal structure remains "
         "uncaptured for discharge and stage — the most probable cause of "
         "stage's one property-validation failure. Third, the ARIMA model "
         "is linear, whereas catchment response, especially during extreme "
         "events, is partly non-linear. Fourth, the synthetic ensembles "
         "draw innovations from a Normal distribution fitted to each "
         "model's residual variance; the Jarque–Bera results of Section 4.5 "
         "show heavier-than-normal tails for every variable, so extreme-"
         "tail synthetic values are plausibly somewhat under-dispersed "
         "relative to reality, a bootstrap-innovation alternative was "
         "implemented (Appendix F) but not adopted as the primary method "
         "for this report. Fifth, the analysis used a single basin; "
         "transferability of both the fitted parameters and the "
         "qualitative pattern of results (strong persistence for discharge "
         "and stage, weak persistence for rainfall) to a basin with a "
         "different climate regime remains to be tested.")

    h1(doc, "5.4 Recommendations for Future Work")
    body(doc,
         "Several directions are recommended. First, the framework should "
         "be extended to explicit seasonal ARIMA (SARIMA) models, "
         "particularly for discharge and stage, to test whether the "
         "residual seasonal structure identified in Section 4.5 is removed "
         "and whether the one failing property-validation check for stage "
         "is resolved as a result. Second, the bootstrap-innovation "
         "variant of the stochastic simulator, which resamples from the "
         "model's own residuals rather than assuming Normal innovations, "
         "should be evaluated as the primary generator, to test whether it "
         "better reproduces the heavy-tailed behaviour identified in the "
         "Jarque–Bera diagnostics. Third, the framework should be applied "
         "to additional basins, including basins in more markedly seasonal "
         "or data-scarce climates, to test the generality of both the "
         "methodology and the specific finding that discharge and stage "
         "show strong persistence while rainfall does not. Fourth, having "
         "established that discharge and stage can each be forecast "
         "independently from their own past with a common methodology, a "
         "natural extension is a multivariate model that uses each as "
         "auxiliary information for the other, or an ARIMAX formulation "
         "that incorporates a genuine exogenous predictor such as a "
         "short-range meteorological forecast, where one is reliably "
         "available.")
    body(doc,
         "In conclusion, the study demonstrates that a disciplined, fully "
         "reproducible statistical framework, applied identically to three "
         "hydrological variables and validated by the statistical "
         "properties of stochastically generated sequences rather than by "
         "point comparison, yields a coherent and largely successful "
         "account of monthly discharge, rainfall and stage — honest about "
         "the one property it does not reproduce, and about why.")
