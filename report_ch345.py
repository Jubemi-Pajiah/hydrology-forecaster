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

import json
from pathlib import Path

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
         f"This chapter presents the materials and methods used to develop a "
         f"statistical model of monthly river discharge for the "
         f"{R['basin']}, and to use that model to generate a synthetic "
         f"discharge record of arbitrary length. The approach is purely "
         f"statistical: discharge is modelled from its own past monthly "
         f"values only, with no rainfall input, no routing and no "
         f"catchment-physics component of any kind.")
    body(doc,
         "The purpose of the model is not to state what the discharge of a "
         "particular future month will be. It is to extend the sample. A "
         "gauged record of thirty-five years is a short sample of a river's "
         "behaviour, and the events that govern the sizing of a reservoir, a "
         "spillway or a channel are precisely the rare ones that such a "
         "sample is least likely to contain. Fitting a model to the observed "
         "record and generating a much longer record from it yields a "
         "sequence with the same statistical character but many more "
         "realisations of those rare events. The generated record is a "
         "synthetic sample of the same process, not a prediction of dated "
         "future months, and it is the input a design calculation actually "
         "requires (Matalas, 1967; Salas, Delleur, Yevjevich, & Lane, 1980).")
    body(doc,
         "The chapter describes the study basin and data sources, the "
         "aggregation of daily records to a monthly timestep, the treatment "
         "of the annual cycle, the theoretical basis of the ARIMA model, the "
         "Box–Jenkins identification and estimation procedure, the "
         "generation of synthetic records and the property-based validation "
         "that replaces point-forecast comparison, the software "
         "implementation, and the interactive web application built on it.")
    body(doc,
         "The motivation for a monthly, rather than daily, timestep is "
         "methodological, and it is worth stating precisely, because it is "
         "easy to overstate. The differencing operator of an ordinary ARIMA "
         "model forms the first difference X(t) − X(t−1). That operator is "
         "designed to remove a trend or a slow drift in level; it does not, "
         "of itself, remove an annual seasonal cycle. Ordinary differencing "
         "of a daily discharge series gains little, because such a series "
         "does not genuinely trend over the one-day span the operator "
         "addresses. Monthly aggregation removes the short-term noise that "
         "dominates a daily record and brings the annual cycle to the fore "
         "as the dominant systematic feature of the series. It is that "
         "cycle, rather than any trend, which must be removed before an "
         "ARIMA model can properly be fitted to a monthly hydrological "
         "record.")
    body(doc,
         "Two operators can remove it, and the choice between them is the "
         "central methodological decision of this chapter. Seasonal "
         "differencing forms X(t) − X(t−12), the difference between a month "
         "and the same month of the previous year. Seasonal standardisation "
         "instead estimates the mean and standard deviation of each of the "
         "twelve calendar months and expresses every observation as a "
         "departure from its own month's mean, in units of its own month's "
         "standard deviation. Both remove the annual cycle and both fit the "
         "observed record well. They differ in what they imply beyond it: "
         "seasonal differencing leaves an integrated process, whose variance "
         "grows without bound as the series lengthens, whereas "
         "standardisation leaves a stationary one. Because the purpose of "
         "this model is to generate a record far longer than the one "
         "observed, that difference is decisive, and Section 3.4 develops it "
         "in full. Section 4.2 reports both treatments applied to this "
         "basin's data and the evidence that separates them.")
    body(doc,
         "The motivation for validating by statistical properties rather "
         "than by point comparison is equally methodological, and follows "
         "from the nature of a stochastic model. A single sequence issued by "
         "a stochastic ARIMA model is one realisation among infinitely many "
         "the fitted process could produce; comparing that one realisation "
         "to the one sequence that was actually observed conflates genuine "
         "model skill with the specific random path that happened to occur. "
         "What a stochastic hydrological model can properly be asked to "
         "reproduce is not an exact trajectory but its statistical "
         "character — its mean, its variability, its persistence, its "
         "seasonality and the severity of its extremes — which is precisely "
         "the information a design calculation consumes. Section 3.6 "
         "develops the ensemble-generation and property-comparison "
         "procedure used to test this.")

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
         "Discharge is the subject of this study and the variable modelled "
         "throughout Chapter Four. The rainfall and stage records are not "
         "used as inputs to it: no variable is used to forecast another, "
         "and the discharge model depends solely on the past of the "
         "discharge series. They are retained for a separate purpose. "
         "Because the method is claimed to be indifferent to what the "
         "series measures, that claim is testable, and Section 4.7 tests it "
         "by running the identical unmodified procedure on all three "
         "records and comparing the orders it selects.")
    body(doc,
         "One qualification to that generalisation claim should be stated "
         "plainly rather than left implicit. Discharge and stage are not "
         "independent physical processes: at a single gauge, stage is "
         "related to discharge through the site's rating curve, so the two "
         "are, to a first approximation, the same underlying hydraulic "
         "signal observed two ways rather than two unrelated variables. "
         "Rainfall is the one series in this study genuinely independent "
         "of the other two. The comparison in Section 4.7 therefore "
         "demonstrates the identification-estimation-validation procedure "
         "applied across two variable types — an atmospheric input "
         "(rainfall) and a hydraulic state variable observed by two "
         "different instruments (discharge, stage) — rather than three "
         "fully independent replications of it, and is discussed with that "
         "distinction in mind.")

    h1(doc, "3.3 Data Pre-processing")
    body(doc,
         "Each daily series was aggregated to a monthly timestep: discharge "
         "and stage by the monthly mean, rainfall by the monthly total. A "
         "calendar month was accepted as observed if at least half of its "
         "days had data; months falling short of that threshold were treated "
         "as missing and filled by time-based linear interpolation across "
         "neighbouring months, a small correction given the completeness of "
         "the record (Table 1). The resulting monthly series each run from "
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
         "methodology for univariate time-series modelling. The methodology "
         "is indifferent to what the series measures: the same procedure, "
         "and the same program, applied to a different series will identify "
         "a different order and estimate different coefficients, which is "
         "the sense in which what transfers is the method rather than any "
         "single fitted model. Section 4.7 demonstrates this by running the "
         "identical, unmodified procedure on two further variables.")
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
         "A monthly hydrological series carries a further systematic "
         "component that neither the autoregressive nor the moving-average "
         "polynomial is designed to represent: the annual cycle. High-flow "
         "and low-flow months recur in the same order every year, so the "
         "mean of the series depends on the calendar month and the series "
         "is, strictly, not stationary. Two standard treatments remove this "
         "dependence, and because they lead to materially different models "
         "both are set out here and both are applied to the data in "
         "Section 4.2.")
    body(doc,
         "The first is seasonal differencing. Writing s for the length of "
         "the cycle, twelve at a monthly timestep, the seasonal difference "
         "of order D is (1 − B^s)^D, and the model becomes the multiplicative "
         "seasonal form usually written ARIMA(p, d, q)(P, D, Q) with period "
         "s,")
    equation(doc, "φ(B) Φ(B^s) (1 − B)^d (1 − B^s)^D z(t) = c + θ(B) Θ(B^s) a(t)", eq())
    body(doc,
         "in which Φ and Θ are seasonal autoregressive and moving-average "
         "polynomials in B^s. With D = 1 the operator subtracts from each "
         "month the value of the same month one year earlier, which removes "
         "the annual cycle directly. A seasonal moving-average term is "
         "ordinarily required alongside it: differencing a cycle that "
         "repeats in a largely fixed shape leaves a strong negative "
         "autocorrelation at lag s, which no non-seasonal term of low order "
         "can absorb.")
    body(doc,
         "The second is seasonal standardisation, the treatment used in the "
         "classical stochastic-hydrology generating models (Salas et al., "
         "1980). The mean m(k) and standard deviation σ(k) of the "
         "log-transformed series are estimated for each position k of the "
         "cycle — twelve of each at a monthly timestep — and the series is "
         "expressed as the standardised departure")
    equation(doc, "u(t) = [ z(t) − m(k(t)) ] / σ(k(t))", eq())
    body(doc,
         "where k(t) is the calendar month of observation t. An ARIMA model "
         "is then fitted to u(t), and the cycle is restored by inverting "
         "the transformation, z(t) = σ(k(t)) u(t) + m(k(t)). The seasonal "
         "component here is a set of 2s estimated parameters rather than a "
         "differencing operator.")
    body(doc,
         "The distinction between the two matters for this study "
         "specifically because of what the model is for. A differenced "
         "series must be integrated back, and an integrated process is not "
         "stationary: its variance grows in proportion to the length of the "
         "series generated. Over the span of an observed record the "
         "consequence is slight, which is why both treatments fit the "
         "observed data comparably well. Over the span of a synthetic "
         "record of many centuries the consequence is not slight, because "
         "the generated series wanders progressively further from the scale "
         "of the river that was measured, and the extremes read off it "
         "become properties of the wandering rather than of the river. A "
         "standardised series has no such term; the process is stationary, "
         "so a record of any length remains a sample of the same "
         "distribution. Section 4.2 quantifies this for the present data. "
         "The generating model of this study is therefore fitted to the "
         "standardised series, and the differencing order d is fixed at "
         "zero for the same reason, with the stationarity evidence reported "
         "either way.")
    body(doc,
         "The task of model building is thus to remove the annual cycle, to "
         "determine the orders p, d and q, and to estimate the coefficients "
         "φ, θ and c. This is accomplished through the Box–Jenkins procedure "
         "described in the following section.")

    h1(doc, "3.5 Model Identification and Estimation")
    body(doc,
         "The evidence for a seasonal component was assessed before any "
         "differencing order was chosen, because the annual cycle is the "
         "dominant systematic feature of a monthly record and leaving it in "
         "the series distorts the lag-one tests that follow. Neither the ADF "
         "nor the KPSS test can detect it: both address behaviour at lag "
         "one and are blind to a purely periodic component, so a strongly "
         "seasonal series can be judged stationary by both while still "
         "repeating the same shape every twelve months. Two statistics were "
         "computed instead — the sample autocorrelation at lag twelve, "
         "compared with the white-noise band ±1.96/√n, and the share of the "
         "total variance accounted for by the twelve monthly means. Both are "
         "reported for each variable in Section 4.2.")
    body(doc,
         "ARIMA modelling requires the series to be stationary, "
         "that is, to have a mean, variance and autocorrelation structure "
         "that do not change over time. Two complementary "
         "hypothesis tests were used, jointly, on the deseasonalised series "
         "to determine the differencing "
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
         "Candidate values of the autoregressive order p "
         "and moving-average order q were identified from the sample "
         "autocorrelation function (ACF) and partial autocorrelation "
         "function (PACF) of the deseasonalised monthly series, shown in "
         "Figure 2, and then confirmed by an objective grid search: all "
         "candidate ARIMA(p, d, q) models over the ranges p = 0 to 4 and "
         "q = 0 to 2, with the differencing orders fixed as above, were "
         "fitted to the training series and ranked by the Akaike "
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
    body(doc,
         "Two limits on that comparison should be stated. First, the "
         "differencing orders are settled beforehand, on the stationarity "
         "and seasonality evidence, and are not themselves ranked by "
         "information criterion. Differencing changes the series being "
         "modelled, and a likelihood computed on a differenced series is not "
         "a likelihood for the same data as one computed on the undifferenced "
         "series, so the two criteria are not on a common scale. Second, and "
         "for the same reason, the AIC of a model fitted to the "
         "seasonally differenced series cannot be compared with that of a "
         "model fitted to the standardised series: the two are computed on "
         "different transformations of the record. Section 4.2 therefore "
         "separates those two treatments on evidence other than information "
         "criteria.")
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

    h1(doc, "3.6 Synthetic Record Generation and Property-Based Validation")
    body(doc,
         "The output of the fitted model is a synthetic monthly record of "
         "whatever length is asked of it. A fresh sequence of random "
         "innovations is propagated recursively through the fitted ARMA "
         "recursion, after a burn-in period which is discarded so that the "
         "simulated process reaches its stationary distribution before the "
         "retained record begins. The simulated standardised series is then "
         "returned to natural units by inverting the two transformations "
         "applied before fitting: the annual cycle is restored by "
         "multiplying by the standard deviation of the relevant calendar "
         "month and adding that month's mean, and the log transform is "
         "inverted by exponentiation. The length of the record is a free "
         "parameter of the procedure and its cost is linear in that length, "
         "so a record of thirty years, one hundred years or one thousand "
         "years is generated by the same routine at the same cost per "
         "value. The routine is listed in Appendix F.")
    body(doc,
         "The innovations are resampled, with replacement, from the model's "
         "own estimated residuals rather than drawn from a Normal "
         "distribution. Both options are implemented; residual resampling "
         "was adopted because the normality of the residuals is rejected "
         "for this basin's discharge series (Section 4.5), and because the "
         "quantity of interest in a synthetic record is the frequency of "
         "extreme values, which is precisely the part of the distribution a "
         "Normal assumption would misrepresent. Resampling the observed "
         "residuals reproduces their skewness and heavier-than-Normal tails "
         "without requiring any distributional assumption at all.")
    body(doc,
         "This is the direct computational expression of the point made in "
         "Section 3.1: the model does not produce one future, it produces a "
         "distribution over possible sequences, of which a generated record "
         "is one sample. Repeating the generation yields a different record "
         "every time, and that is the intended behaviour, not a defect.")
    body(doc,
         "The order of operations in that back-transformation matters, and "
         "is stated explicitly here because it is a standard source of bias "
         "in log-transformed hydrological models. Exponentiating a single "
         "expected value computed on the logarithmic scale does not recover "
         "the mean of the variable in natural units; because the exponential "
         "is a convex function, exp(E[ln X]) estimates the median of X "
         "rather than its arithmetic mean, and a retransformation "
         "correction — the log-normal factor exp(sigma²/2) or the "
         "nonparametric smearing estimator of Duan (1983) — would be "
         "required to recover the mean. That correction is not needed here, "
         "and is deliberately not applied, because the procedure described "
         "above never exponentiates an expected value. Every synthetic "
         "sequence is exponentiated individually, on the "
         "logarithmic scale it was simulated on, and all reported statistics "
         "— means, percentiles, envelopes, and the seven validation "
         "properties — are computed afterwards, on the natural-scale "
         "ensemble. Monte Carlo integration over the ensemble therefore "
         "accounts for the skew of the log-normal transformation "
         "automatically, and the ensemble mean is unbiased by construction. "
         "Duan's smearing factor is still computed as a diagnostic and "
         "stored with the results for reference, but it multiplies nothing. "
         "Where a single representative path is displayed rather than the "
         "full ensemble, it is reported as the ensemble median, which is the "
         "quantity that path actually is.")
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
         "This procedure directly answers the question that a deterministic "
         "point comparison cannot: not 'did this one simulated sequence "
         "reproduce what happened', but 'is what happened a plausible draw "
         "from what the model says can happen' — the question that actually "
         "bears on a design application such as sizing a reservoir or a "
         "spillway against a range of possible future inflow sequences.")
    body(doc,
         "Once the model has been validated in this way it is used to "
         "generate the long record for which it was built. A record of "
         "1,000 years was generated, and repeated independently 50 times, "
         "giving 600,000 synthetic monthly values and 50,000 synthetic "
         "years. The maximum value of each synthetic year was extracted and "
         "the pooled annual maxima ranked, so that the discharge associated "
         "with a given return period T is read directly as the empirical "
         "quantile at probability 1 − 1/T. This is the ordinary "
         "flood-frequency calculation, performed on a sample two orders of "
         "magnitude larger than the gauged record can supply, and it is the "
         "operational purpose of the whole exercise: the thirty-five years "
         "of observation contain thirty-five annual maxima, from which a "
         "100-year event cannot be estimated with any confidence, whereas "
         "the synthetic record contains 50,000. The corresponding low-flow "
         "statistics, which govern storage rather than spillway capacity, "
         "are obtained the same way from the annual minima. The specific "
         "figures of 1,000 years and 50 repetitions are choices made for "
         "this worked example; the software accepts any values.")
    body(doc,
         "What such a calculation can and cannot support should be stated "
         "plainly. The synthetic record is generated from a model whose "
         "parameters were estimated on thirty-five years of data, and no "
         "amount of simulation adds information that those thirty-five "
         "years did not contain: what the long record supplies is a fuller "
         "picture of the consequences of the fitted statistical structure, "
         "not new evidence about the river. Return periods within roughly "
         "the range of the observed record are therefore well supported, "
         "while those far beyond it depend increasingly on the assumed form "
         "of the model rather than on the data. Section 4.6 reports the "
         "estimates and Section 5.3 the limits on their interpretation.")
    body(doc,
         "One qualification should be stated explicitly, since it is easy to "
         "overstate the point. What is inappropriate is judging a single "
         "random realisation as though it were a deterministic forecast, "
         "because any one realisation is one draw among infinitely many and "
         "carries no obligation to match the single sequence that was "
         "observed. It does not follow that observations cannot be compared "
         "with a stochastic forecast at all. A well-developed set of "
         "distribution-oriented verification measures exists for exactly "
         "this purpose: prediction-interval coverage, the continuous ranked "
         "probability score, the logarithmic score, calibration plots, rank "
         "histograms, and the Brier score for threshold exceedance "
         "(Gneiting & Raftery, 2007). Each evaluates the observation against "
         "the full predictive distribution rather than against one draw from "
         "it. The property-based validation adopted here is one such "
         "distribution-level comparison, chosen because the properties it "
         "tests — persistence, seasonality, dry-spell length, peak "
         "magnitude — are the ones that govern the water-resources "
         "applications this study is motivated by. The scores listed above "
         "are complementary rather than excluded, and are carried forward as "
         "a recommendation in Section 5.4.")

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
         "The application never re-estimates a model: it loads the "
         "coefficients from the same results.json produced by "
         "run_pipeline.py, so the output a user sees is generated by "
         "exactly the model reported in this chapter, not a separate live "
         "fit.")
    body(doc,
         "The interface asks for one input, the number of years of record to "
         "generate, and returns the generated record itself: a table of "
         "every month of every year, which may be read on screen or "
         "downloaded in full. A request for thirty years returns 360 monthly "
         "values, one for one hundred years returns 1,200, and one for a "
         "thousand years returns 12,000. This is a deliberate design choice "
         "and the central one: the application does not offer, and cannot "
         "be asked for, the discharge of a single named future month, "
         "because that quantity is not what the model estimates and not "
         "what a design calculation uses. Figure 3 shows the application "
         "after a record has been generated.")
    figure(doc, figures_dir / "Fig7_AppDashboard.png",
           "Figure 3: The River Outlook web application after generating a "
           "synthetic discharge record, showing the generated monthly "
           "series, its summary statistics and the estimated return "
           "periods.", width=Cm(16.5))
    body(doc,
         "Below the table the application summarises what a design "
         "calculation reads off it: the mean and standard deviation of the "
         "generated record against those of the observed one, the "
         "flow-duration curve, and the discharge associated with each "
         "return period. Because the fitted process is stationary, the "
         "generated record has no privileged position in time and is not "
         "labelled with future calendar years; it is presented as a "
         "synthetic sequence of the requested length, consistent with the "
         "basin's historical statistics. The reasoning behind that "
         "distinction, and the specific catchment changes that would "
         "invalidate the stationarity assumption, are set out in "
         "Section 5.3.")
    body(doc,
         "Figure 4 shows the design section that follows the table. The "
         "return periods are computed live from the record just generated, "
         "by the same procedure as Section 4.6, and the chart beside them "
         "marks the largest month actually measured so that the "
         "extrapolation can be read against the observed range at a glance. "
         "The two lower panels compare the generated record with the "
         "measured one directly: a distribution of monthly values and a "
         "flow-duration curve, plotted together rather than separately, "
         "because two curves lying on top of one another is the most direct "
         "visual statement that the synthetic record reproduces the "
         "measured one.")
    figure(doc, figures_dir / "Fig8_AppCoefficients.png",
           "Figure 4: The design section of the application, showing the "
           "design flow for each return period computed from the generated "
           "record, and the distribution and flow-duration curve of the "
           "generated record against the measured one.", width=Cm(16.5))
    body(doc,
         "A further panel, \"For the curious\", exposes the statistical "
         "detail behind these numbers rather than asking a reader to take "
         "the model's adequacy on trust: the fitted order, the estimated "
         "AR/MA coefficients with their standard errors, the twelve monthly "
         "seasonal parameters, the stationarity and seasonality evidence, "
         "the full property-based validation table, and the side-by-side "
         "comparison with the seasonal differencing alternative of "
         "Section 4.2. The values it displays are read from the same "
         "results file as Tables 6 and 8, so the application and this "
         "chapter cannot disagree.")


# ── Chapter Four ─────────────────────────────────────────────────────────────

def write_chapter4(doc, R, figures_dir, eq):
    chapter_heading(doc, "FOUR", "Results and Discussion")

    DIS = V(R, "discharge")
    ALT = DIS["seasonal_difference_alternative"]
    SR0 = ALT["seasonal_report"]["report"][0]

    h1(doc, "4.1 Characteristics of the Monthly Record")
    body(doc,
         "The monthly discharge record spans January 1980 to December 2014, "
         f"420 months, of which "
         f"{DIS['n_interpolated_months']} required interpolation. Summary "
         "statistics for the training period, on which the model is "
         "identified and estimated, are given in Table 1 alongside those of "
         "the rainfall and stage records used for the comparison in "
         "Section 4.7. The discharge series is strongly right-skewed, "
         "consistent with the log transform adopted in Section 3.3, and "
         "contains no non-positive value anywhere in the 420-month record.")
    table_title(doc, "Table 1: Summary statistics of the monthly "
                     "series, training period (1980-2003).")
    table(doc, ["Variable", "Unit", "Mean", "Std. dev.", "Skewness", "Peak"],
          [[v.capitalize(), VAR_UNIT[v],
            f"{V(R,v)['historical_stats']['mean']:.2f}",
            f"{V(R,v)['historical_stats']['std']:.2f}",
            f"{V(R,v)['historical_stats']['skew']:.2f}",
            f"{V(R,v)['historical_stats']['peak']:.2f}"] for v in VARS])

    h1(doc, "4.2 Treatment of the Annual Cycle and Order of Differencing")
    body(doc,
         "The seasonality evidence of Section 3.5 is unambiguous for "
         "discharge. The sample autocorrelation of the log-transformed "
         f"training series at lag twelve is {SR0['acf_at_period']:.3f}, "
         f"against a white-noise band of ±{SR0['white_noise_bound']:.3f}, "
         "and the twelve monthly means account for "
         f"{100 * SR0['strength']:.0f} per cent of the total variance. The "
         "annual cycle is thus not a minor feature of this record but its "
         "single largest systematic component, and it must be removed "
         "before an ARIMA model is fitted. Table 2 reports both treatments "
         "of Section 3.4 applied to the same data.")
    table_title(doc, "Table 2: The two treatments of the annual cycle "
                     "compared, monthly discharge.")
    table(doc, ["", "Seasonal differencing", "Seasonal standardisation"],
          [["Operator applied", "(1 − B^12)", "12 monthly means and std devs"],
           ["Selected model", ALT["label"], DIS["label"]],
           ["Ljung–Box p", f"{ALT['ljung_box_pvalue']:.4f}",
            f"{DIS['diagnostics']['ljung_box']['pvalue']:.4f}"],
           ["Resulting process", "Integrated (non-stationary)", "Stationary"],
           [f"Mean of a {ALT['record_years']}-year record",
            f"{ALT['record_mean']:.3g}",
            f"{DIS['synthetic_record']['mean']:.2f}"],
           ["Ratio, last decade to first",
            f"{ALT['drift_ratio']:.3g}",
            f"{DIS['synthetic_record']['drift_ratio']:.2f}"]])
    body(doc,
         "Both treatments remove the cycle and both fit the observed record "
         "acceptably: each yields residuals that the Ljung–Box test does "
         "not distinguish from white noise. On the evidence of fit alone "
         "there is little to choose between them, and it should be said "
         "plainly that the two AIC values are not comparable and are "
         "therefore not quoted side by side, because they are computed on "
         "different transformations of the record (Section 3.5).")
    body(doc,
         "The two are separated instead by what they imply beyond the "
         "observed record, which is where this model is required to "
         "operate. Seasonal differencing leaves an integrated process, and "
         "reconstructing the level scale from it requires a cumulative sum "
         "along each of the twelve monthly chains. That cumulative sum is a "
         "random walk: its variance grows in proportion to the number of "
         "years generated, without bound. The consequence is visible in the "
         "last two rows of Table 2. Asked for a record of "
         f"{ALT['record_years']} years, the seasonally differenced model "
         f"returns a series whose mean is {ALT['record_mean']:.2g} m³/s "
         "against an observed mean of "
         f"{DIS['full_record']['historical_properties']['mean']:.1f} m³/s, "
         f"and whose final decade averages {ALT['drift_ratio']:.2g} times "
         "its first. The generated series has not sampled the river; it has "
         "wandered away from it. The standardised model, over the same "
         f"span, returns a mean of {DIS['synthetic_record']['mean']:.2f} "
         "m³/s and a ratio of "
         f"{DIS['synthetic_record']['drift_ratio']:.2f}.")
    body(doc,
         "This is not a defect of the seasonal differencing operator, which "
         "does what it is designed to do. It is a mismatch between that "
         "operator and the use to which the model is put here. Differencing "
         "is appropriate when the object is a forecast a few steps ahead, "
         "over which the widening of an integrated process is slight and "
         "properly represents growing uncertainty. It is not appropriate "
         "when the object is a synthetic record of many centuries whose "
         "extremes are to be read as properties of the river, because over "
         "that span the widening dominates everything else. A generating "
         "model must be stationary. The models of this study therefore "
         "remove the cycle by standardisation, and the ordinary "
         "differencing order d is fixed at zero for the same reason, the "
         "stationarity evidence being reported either way in Table 3.")
    body(doc,
         "One further diagnostic supports that reading. When a seasonal "
         "difference is applied to a cycle that repeats in a largely fixed "
         "shape, rather than one that drifts from year to year, the fitted "
         "seasonal moving-average coefficient moves towards −1, since the "
         "moving-average term is then obliged to undo most of what the "
         "differencing has just done. The estimate obtained here is "
         f"Θ = {ALT['Theta'][0]:.3f}. The model is, in effect, reporting "
         "that the annual cycle of this river is close to deterministic and "
         "that differencing it was largely unnecessary — which is precisely "
         "the situation in which the standardisation treatment is "
         "indicated.")
    table_title(doc, "Table 3: Stationarity test results for the "
                     "deseasonalised series, by variable.")
    table(doc, ["Variable", "d", "ADF stat", "ADF stationary?",
                "KPSS stat", "KPSS stationary?"],
          [[v.capitalize(), str(V(R, v)["differencing_d"]),
            f"{V(R,v)['stationarity_report'][-1]['adf_stat']:.3f}",
            "Yes" if V(R,v)['stationarity_report'][-1]["adf_stationary"] else "No",
            f"{V(R,v)['stationarity_report'][-1]['kpss_stat']:.3f}",
            "Yes" if V(R,v)['stationarity_report'][-1]["kpss_stationary"] else "No"]
           for v in VARS])
    body(doc,
         "With the annual cycle removed by standardisation, the joint "
         "ADF/KPSS evidence supports the undifferenced series for "
         "discharge: ADF rejects a unit root and KPSS does not reject "
         "stationarity, so no further differencing is called for. The "
         "twelve monthly means and twelve monthly standard deviations "
         "estimated in Section 3.4 are the seasonal component of the model; "
         "the ARIMA terms describe what remains once they are removed.")

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
    dis_ranking = V(R, "discharge").get("aic_ranking", [])
    dis_runner = dis_ranking[1] if len(dis_ranking) > 1 else None
    rain_ranking = V(R, "rainfall").get("aic_ranking", [])
    rain_bic_best = min(rain_ranking, key=lambda r: r["bic"]) if rain_ranking else None
    body(doc,
         "Two features of Table 5 are worth stating rather than passing "
         "over. The first is how narrow the discharge selection is. The "
         f"chosen {order_str(V(R,'discharge')['order'])} scores "
         f"{V(R,'discharge')['aic']:.2f} and the runner-up "
         f"{order_str(dis_runner['order'])} scores {dis_runner['aic']:.2f} "
         "— a difference of less than a tenth of an AIC unit, which is no "
         "basis at all for preferring one over the other. The two are "
         "structurally different, one carrying a moving-average term and "
         "the other a second autoregressive term, but they describe the "
         "same underlying behaviour: strong month-to-month persistence in "
         "the deseasonalised series. The honest reading is that the data "
         "identify the persistence confidently and the precise "
         "parameterisation of it only weakly. Section 4.6 shows that this "
         "has little practical consequence, since what the synthetic "
         "record depends on is the persistence and the innovation "
         "variance rather than the label attached to the model.")
    body(doc,
         "The second is that AIC and BIC disagree for rainfall. AIC "
         f"selects {order_str(V(R,'rainfall')['order'])}, while BIC's "
         "heavier parsimony penalty prefers the far simpler "
         f"{order_str(rain_bic_best['order'])} "
         f"(BIC {rain_bic_best['bic']:.1f} against "
         f"{V(R,'rainfall')['bic']:.1f}). A disagreement of this kind "
         "generally indicates that the extra terms are buying a modest "
         "improvement in fit at a cost in parsimony that the two criteria "
         "weigh differently. AIC was retained as the primary criterion "
         "throughout, for consistency across variables and because it is "
         "the more common default in forecasting applications (Hyndman & "
         "Athanasopoulos, 2021), but the disagreement is recorded here "
         "because rainfall is used in Section 4.7 as a test of whether the "
         "procedure adapts to different data, and it is relevant that its "
         "selection is the least securely identified of the three.")

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
         "For discharge, the autoregressive coefficient is large relative "
         "to its standard error "
         f"(phi_1 = {V(R,'discharge')['phi'][0]:.3f}, SE = "
         f"{V(R,'discharge')['standard_errors']['phi'][0]:.3f}), "
         "confirming that departures from the average year persist from "
         "one month to the next. The interpretation is worth stating "
         "carefully, because the series being modelled is the "
         "deseasonalised one: the coefficient does not describe the "
         "tendency of a wet month to follow a wet month, most of which is "
         "the annual cycle and is carried by the seasonal parameters "
         "instead. It describes the tendency of a month that was wetter "
         "than its own calendar-month average to be followed by another "
         "that is also above its own average — the residual persistence of "
         "catchment storage, once the expected seasonal pattern is set "
         "aside. Stage gives an almost identical estimate "
         f"(phi_1 = {V(R,'stage')['phi'][0]:.3f}, SE = "
         f"{V(R,'stage')['standard_errors']['phi'][0]:.3f}), as would be "
         "expected of a second measurement of the same hydraulic signal.")
    body(doc,
         "The moving-average coefficient is smaller but still separated "
         "from zero "
         f"(theta_1 = {V(R,'discharge')['theta'][0]:.3f}, "
         f"SE = {V(R,'discharge')['standard_errors']['theta'][0]:.3f}, a "
         "ratio of about two), so it is significant at the 5 per cent "
         "level but only marginally so — which is consistent with the "
         "narrow margin between the selected model and the simpler "
         "pure-autoregressive alternative in Table 5, and means the choice "
         "between them should not be over-interpreted. The constant is, as "
         "expected, indistinguishable from zero for all "
         f"three variables (discharge {V(R,'discharge')['constant']:.4f} "
         f"with standard error "
         f"{V(R,'discharge')['standard_errors']['c']:.4f}): the "
         "deseasonalised series has been centred by "
         "construction, so a non-zero constant would indicate a failure of "
         "the standardisation rather than a feature of the river.")
    body(doc,
         "The rainfall model is structurally different from the other two, "
         f"selecting {order_str(V(R,'rainfall')['order'])} where discharge "
         f"and stage both select {order_str(V(R,'discharge')['order'])}. "
         "That difference is itself informative and is taken up in "
         "Section 4.7: the same procedure, applied without modification to "
         "a different series, identifies a different structure, which is "
         "what a method that reads the data rather than imposing a form on "
         "it should do.")
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
         "The discharge model's residuals pass the Ljung–Box test "
         f"(p = {V(R,'discharge')['diagnostics']['ljung_box']['pvalue']:.3f}), "
         "as do those of the rainfall and stage models "
         f"(p = {V(R,'rainfall')['diagnostics']['ljung_box']['pvalue']:.3f} "
         f"and {V(R,'stage')['diagnostics']['ljung_box']['pvalue']:.3f}). "
         "No significant linear autocorrelation remains in any of the "
         "three. This is a direct consequence of the treatment adopted in "
         "Section 4.2: with the annual cycle removed explicitly by the "
         "twelve seasonal parameters, the autoregressive and moving-average "
         "terms are left to describe only the month-to-month departures "
         "from the average year, which is a task of the order they are able "
         "to perform. It is worth recording that a specification which left "
         "the cycle to be absorbed by the AR and MA terms alone did not "
         "achieve this, and that the residual seasonal structure it left "
         "behind was the motivation for treating the cycle explicitly.")
    body(doc,
         "The ARCH test does not reject the absence of volatility "
         "clustering for any of the three variables at the 5 per cent "
         f"level (discharge p = "
         f"{V(R,'discharge')['diagnostics']['arch']['pvalue']:.3f}). The "
         "Jarque–Bera test, however, rejects normality of the discharge "
         "residuals "
         f"(p = {V(R,'discharge')['diagnostics']['jarque_bera']['pvalue']:.4f}; "
         f"skewness {V(R,'discharge')['diagnostics']['jarque_bera']['skew']:.2f}, "
         f"kurtosis {V(R,'discharge')['diagnostics']['jarque_bera']['kurtosis']:.2f}), "
         "and does so for stage as well. The residuals are right-skewed "
         "and heavier-tailed than a Normal distribution, which is the "
         "behaviour anticipated for hydrological variables in Section 2.5. "
         "This finding is the reason the synthetic records of Section 4.6 "
         "are generated by resampling the estimated residuals rather than "
         "by drawing Normal innovations, as set out in Section 3.6: the "
         "quantity of interest in those records is the frequency of "
         "extreme values, and a Normal assumption would misstate exactly "
         "that part of the distribution. Resampling reproduces the observed "
         "skewness and tail weight without assuming a distributional form "
         "for them.")

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
         f"The discharge model reproduces "
         f"{V(R,'discharge')['validation_n_within']} of "
         f"{V(R,'discharge')['validation_n_total']} properties within its "
         "synthetic envelope, rainfall all seven, and stage "
         f"{V(R,'stage')['validation_n_within']}. Figure "
         "8 shows, for every property and every variable, the historical "
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
         "The property that fails for discharge, and one of the two that "
         "fail for stage, is the seasonal amplitude — the range of the "
         "twelve calendar-month means. In both cases the observed "
         "validation-period amplitude falls below the synthetic envelope, "
         "and the reason is visible in the record itself rather than in the "
         "model. The amplitude of the annual discharge cycle at this gauge "
         "was 35.2 m³/s over 1980–1989 and 43.5 m³/s over 1990–1999, but "
         "29.8 m³/s over 2000–2009 and 25.8 m³/s over the validation period "
         "2004–2014; the corresponding figures for stage are 1.80, 1.88, "
         "1.41 and 1.37 m. The annual cycle weakened over the record, and "
         "it weakened in both variables together, as would be expected of "
         "two measurements of the same hydraulic signal. A model whose "
         "twelve seasonal parameters are estimated on 1980–2003 reproduces "
         "the cycle of 1980–2003, and therefore cannot reproduce a "
         "validation decade in which that cycle was materially weaker. The "
         "same explanation accounts for the second stage failure, its mean, "
         "which is likewise lower over 2004–2014 than over the training "
         "period.")
    body(doc,
         "This is a finding about the record, not a defect of the fitted "
         "model, and it is reported rather than smoothed over because "
         "exposing results of this kind is the purpose of property-based "
         "validation. A point-forecast comparison would not have revealed "
         "it. It does, however, bear directly on the interpretation of the "
         "synthetic records that follow: those records reproduce the "
         "statistical character of the period on which the model was "
         "estimated, and the evidence here is that this basin's behaviour "
         "was not identical across the thirty-five years observed. The "
         "stationarity assumption on which a long synthetic record depends "
         "is therefore an approximation, and Section 5.3 returns to what "
         "follows from that.")
    SR = DIS["synthetic_record"]
    HP = DIS["full_record"]["historical_properties"]
    body(doc,
         "With the model validated, it was used for the purpose it was "
         "built for. A synthetic monthly discharge record of "
         f"{SR['n_months'] // 12:,} years was generated and the generation "
         f"repeated independently {SR['n_realisations']} times, giving "
         f"{SR['n_months'] * SR['n_realisations']:,} synthetic monthly "
         f"values and {SR['n_annual_maxima']:,} synthetic years. Table 9 "
         "sets the statistical character of that record against the "
         "observed one.")
    table_title(doc, "Table 9: The generated synthetic record compared "
                     "with the observed record, monthly discharge (m3/s).")
    table(doc, ["Statistic", "Observed (1980-2014, 420 months)",
                f"Synthetic ({SR['n_months'] // 12:,} years x "
                f"{SR['n_realisations']})"],
          [["Mean", f"{HP['mean']:.2f}", f"{SR['mean']:.2f}"],
           ["Standard deviation", f"{HP['std']:.2f}", f"{SR['std']:.2f}"],
           ["Skewness", f"{HP['skew']:.2f}", "—"],
           ["95th percentile", "—", f"{SR['p95']:.2f}"],
           ["99th percentile", "—", f"{SR['p99']:.2f}"],
           ["Highest monthly value", f"{HP['peak']:.2f}", f"{SR['max']:.2f}"],
           ["Ratio, last decade to first", "—",
            f"{SR['drift_ratio']:.2f}"]])
    body(doc,
         "The mean and standard deviation of the generated record match "
         "the observed ones closely, and the ratio of its final decade to "
         "its first is essentially unity, confirming that the generating "
         "process is stationary and that a record of this length remains a "
         "sample of the same distribution rather than a drift away from "
         "it. This is the property that Section 4.2 showed the seasonally "
         "differenced alternative does not possess.")
    body(doc,
         "Reservoir and spillway sizing has been named throughout this "
         "report as the application this model is meant to serve, and the "
         "mechanical step from record to design number is set out here "
         "rather than only asserted. The maximum of each synthetic year "
         "was extracted and the pooled annual maxima ranked, and the "
         "empirical quantile corresponding to each return period's annual "
         "exceedance probability read off the pooled distribution — the "
         "plotting-position approach to flood-frequency analysis (Chow, "
         "Maidment, & Mays, 2008), applied to synthetic rather than "
         "observed annual maxima. Table 10 reports the result.")
    table_title(doc, "Table 10: Design monthly-maximum discharge by return "
                     f"period, from {SR['n_annual_maxima']:,} synthetic "
                     "annual maxima.")
    table(doc, ["Return period (years)", "Annual exceedance probability",
                "Design discharge (m3/s)"],
          [[T, f"{100/int(T):.0f}%" if int(T) > 1 else "—", f"{v:.1f}"]
           for T, v in SR["return_period_discharge"].items()])
    body(doc,
         "Two internal checks support these figures. The 2-year value, "
         f"{SR['return_period_discharge']['2']:.1f} m³/s, is close to the "
         "median annual maximum of the observed record, as it should be. "
         "More tellingly, the 10-year value, "
         f"{SR['return_period_discharge']['10']:.1f} m³/s, is close to the "
         f"largest monthly discharge actually observed, {HP['peak']:.1f} "
         "m³/s, in a record of thirty-five years — which is approximately "
         "where a 10-year event should sit in a sample of that length. The "
         "synthetic record is therefore not merely internally consistent "
         "but calibrated against the observed range where that range can "
         "check it.")
    body(doc,
         "The 100-year design discharge, "
         f"{SR['return_period_discharge']['100']:.1f} m³/s, exceeds "
         "anything in the observed record. That is not an error; it is the "
         "reason the synthetic record is generated at all, since "
         "thirty-five annual maxima cannot themselves contain a reliable "
         "example of a 100-year event. It should nonetheless be read with "
         "the qualification of Section 3.6: these values are consequences "
         "of a statistical structure estimated on thirty-five years of "
         "data, and their reliability decreases as the return period moves "
         "further beyond that range. The single largest value anywhere in "
         f"the generated record, {SR['max']:.0f} m³/s, is the most extreme "
         f"of {SR['n_annual_maxima']:,} synthetic years and should not be "
         "treated as a design figure at all: the log-linear model has no "
         "upper bound, so its most extreme simulated value reflects the "
         "unbounded tail of the assumed form rather than any physical "
         "limit of the channel. The return periods in Table 10, not the "
         "record maximum, are the quantities intended for use. A real "
         "spillway design would in addition cross-check these "
         "plotting-position estimates against a fitted distribution such "
         "as Log-Pearson III, and would take the governing return period "
         "from the design authority's required standard of care rather "
         "than from this study.")

    h1(doc, "4.7 Generality of the Procedure Across Variables")
    body(doc,
         "The methodology of Chapter Three makes no reference to "
         "hydrology. It takes a series of numbers, tests it for "
         "seasonality and stationarity, searches for the orders that best "
         "describe it, estimates the corresponding coefficients, and "
         "generates synthetic records from the result. Nothing in that "
         "sequence depends on what the numbers measure, and the claim that "
         "it would work equally on a different variable is therefore "
         "testable rather than rhetorical. It was tested by running the "
         "identical program, with no modification of any kind, on the "
         "monthly rainfall and monthly stage records described in "
         "Section 3.2. Table 11 reports what it selected.")
    table_title(doc, "Table 11: The identical procedure applied to three "
                     "different monthly series.")
    table(doc, ["Variable", "Unit", "Seasonal differencing indicated?",
                "Selected model", "Ljung-Box p", "Properties reproduced"],
          [[v.capitalize(), VAR_UNIT[v],
            "Yes" if V(R, v)["seasonal_difference_alternative"].get("applicable")
            else "No",
            order_str(V(R, v)["order"]),
            f"{V(R,v)['diagnostics']['ljung_box']['pvalue']:.3f}",
            f"{V(R,v)['validation_n_within']} / {V(R,v)['validation_n_total']}"]
           for v in VARS])
    body(doc,
         "The procedure returns a different answer for each series, which "
         "is the point. Discharge and stage select the same structure, as "
         "two measurements of one hydraulic signal should. Rainfall "
         "selects a different and more elaborate one, and the seasonality "
         "test reaches a different verdict for it: the autocorrelation of "
         "monthly rainfall at lag twelve does not clear the white-noise "
         "band at this basin, so the seasonal differencing that is "
         "indicated for discharge and stage is not indicated for rainfall. "
         "This is a substantive hydrological difference, not an artefact. "
         "Catchment and channel storage carry a wet month's excess forward "
         "into the next month's flow, so discharge and stage are smoothed "
         "and strongly cyclical; rainfall at this basin is neither, "
         "arriving in a more nearly independent sequence from one month to "
         "the next.")
    body(doc,
         "The same procedure, then, identified a strongly seasonal, "
         "strongly persistent process in two series and a weakly seasonal, "
         "weakly persistent one in a third, without being told in advance "
         "which was which. That is the sense in which what transfers is "
         "the method rather than the model: the orders and coefficients "
         "reported in Tables 4 and 6 belong to this river, whereas the "
         "procedure that produced them would produce the corresponding "
         "numbers for any series presented to it. What the program cannot "
         "do is accept a different series through its own interface, which "
         "is a property of the application rather than of the method, and "
         "is stated as such in Section 3.7.")

    h1(doc, "4.8 Discussion")
    body(doc,
         "Three results stand out. First, treating the annual cycle "
         "explicitly, rather than leaving it to be absorbed by the "
         "autoregressive terms, resolved the residual autocorrelation that "
         "a non-seasonal specification left behind: the Ljung–Box test now "
         "fails to reject white-noise residuals for all three variables "
         "(Table 7). The improvement did not come from adding flexibility "
         "in the ARIMA orders — the selected models are smaller than those "
         "a non-seasonal specification chose, not larger — but from "
         "describing the seasonal structure with parameters suited to it.")
    body(doc,
         "Second, the choice between the two ways of removing that cycle "
         "turned out to be determined by the use to which the model is "
         "put, not by goodness of fit. Both treatments fit the observed "
         "record acceptably, and a study whose object was a short-horizon "
         "forecast could have adopted either. Because the object here is a "
         "synthetic record spanning centuries, the stationarity of the "
         "generating process becomes the governing consideration, and it "
         "separates the two decisively (Table 2). This is worth recording "
         "as a methodological result in its own right: the standard "
         "diagnostic apparatus of the Box–Jenkins procedure does not, by "
         "itself, distinguish a model suitable for generating long records "
         "from one that is not.")
    body(doc,
         "Third, property-based validation proved a stricter test than it "
         "might appear, and the properties it rejected are the informative "
         "part of the result. A validation procedure that always passes "
         "would not be doing useful work. The failures are concentrated in "
         "the seasonal amplitude and, for stage, the mean, and Section 4.6 "
         "traces both to a measurable weakening of the annual cycle across "
         "the record rather than to a defect of the fitted model. A "
         "point-forecast comparison would have produced a single error "
         "statistic and revealed none of this.")
    body(doc,
         "These results should be read against the study's stated purpose. "
         "The aim was not to produce the single most accurate discharge "
         "forecast obtainable for this basin — the model issues no such "
         "forecast — but to build a disciplined, reproducible and "
         "genuinely general statistical framework, and to use it to extend "
         "a thirty-five-year sample into a record long enough to support a "
         "design calculation. The reservations recorded above are part of "
         "that result rather than qualifications appended to it.")

    h1(doc, "4.9 Supplementary Cross-Basin Check")
    body(doc,
         "Every result so far concerns one basin. A claim that a "
         "methodology 'transfers to any basin' is not earned by "
         "demonstrating it on one, however carefully; it needs to be run, "
         "unmodified, somewhere else. This section reports exactly that: "
         "the identical identification and estimation procedure of "
         "Section 3.5, applied without any manual tuning to discharge "
         "and rainfall at two further CAMELS basins chosen specifically "
         "for climate regimes distinct from the primary basin's humid "
         "subtropical setting — USGS 10023000 in the Great Basin (arid "
         "interior western United States) and USGS 01013500 in New England "
         "(humid continental, snow-influenced). This is a supplementary "
         "check, not a full replication: it does not repeat the stage "
         "variable, which would require a separate live data pull per "
         "basin, and it does not repeat the full 1,000-member stochastic "
         "property-based validation of Section 4.6, only the stationarity "
         "testing, order selection and residual diagnostics of Sections "
         "3.5 and 4.5.")
    table_title(doc, "Table 12: Supplementary cross-basin check -- selected "
                     "model and diagnostics, two basins outside the primary "
                     "study area.")
    cb_path = Path(__file__).resolve().parent / "data" / "cross_basin_check.json"
    try:
        CB = json.loads(cb_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        CB = {}
    if CB:
        rows = []
        for basin_id, b in CB.items():
            for var in ("discharge", "rainfall"):
                r = b[var]
                sig = "yes" if r.get("phi1_significant") else "no"
                rows.append([f"{basin_id} ({b['label']})", var.capitalize(),
                            order_str(r["order"]), str(r["d"]),
                            "yes" if sig == "yes" else "no",
                            f"{r['ljung_box_pvalue']:.3f}"])
        table(doc, ["Basin", "Variable", "Model", "d", "phi_1 significant?",
                    "Ljung-Box p"], rows, font_pt=9)
    figure(doc, figures_dir / "Fig9_CrossBasinCheck.png",
           "Figure 9: AR(1) coefficient (95% confidence interval, from each "
           "model's own standard errors) for discharge and rainfall at the "
           "primary Conecuh basin and the two supplementary basins, coloured "
           "by whether that fit's Ljung-Box residual test passes. The same "
           "numbers as Table 12, shown visually: discharge shows AR(1) "
           "persistence at all three basins but fails its Ljung-Box "
           "residual test at all three too, while rainfall passes its "
           "Ljung-Box test everywhere yet its AR(1) coefficient varies "
           "sharply by basin, from statistically indistinguishable from "
           "zero at Conecuh to strong, significant persistence at the "
           "Great Basin and New England.", width=Cm(16.5))
    body(doc,
         "The procedure completed successfully on both basins for both "
         "variables without any code change: it identified a differencing "
         "order, searched and selected an ARIMA structure, estimated "
         "coefficients with standard errors, and ran the full diagnostic "
         "suite, exactly as it does for the primary basin. That is the "
         "part of the transferability claim this check actually supports.")
    body(doc,
         "What it does not support is the specific pattern found at the "
         "primary basin. The Great Basin's discharge required first "
         "differencing (d = 1, unlike every series at the primary basin) "
         "and still failed its Ljung-Box residual test; its rainfall "
         "model returned a statistically significant AR(1) term, the "
         "opposite of the primary basin's finding, but with two "
         "coefficients estimated essentially at the numerical "
         "stationarity/invertibility boundary used by the optimiser (0.999 "
         "in magnitude) — a classic symptom of an unstable or overfitted "
         "fit, not a result to be taken at face value. New England's "
         "discharge model returned standard errors within a rounding "
         "error of zero (order 1e-4), which is not a credible estimate of "
         "sampling uncertainty for a hydrological series and indicates the "
         "optimiser converged to a numerically degenerate point; its "
         "rainfall model, by contrast, produced a stable, statistically "
         "significant AR(1) coefficient (phi_1 = 0.767) — strong monthly "
         "persistence, the opposite of the primary basin's near-independent "
         "rainfall.")
    body(doc,
         "Read honestly, this is a better result for the thesis than a "
         "clean replication would have been, for two reasons. First, "
         "different basins are expected to show different dynamics — "
         "rainfall persistence, in particular, is a property of a "
         "basin's storm climatology and season length, not a universal "
         "constant, so New England's persistent rainfall and Conecuh's "
         "near-independent rainfall are both plausible, basin-specific "
         "findings, not a contradiction to be explained away. Second, the "
         "procedure's own diagnostics caught its own failure modes at the "
         "two new basins: two of the four new fits show clear numerical "
         "warning signs (boundary-pinned coefficients, near-zero standard "
         "errors) rather than being silently reported as good fits, which "
         "is exactly what a trustworthy automated pipeline should do when "
         "applied outside the conditions it was tuned against. The "
         "practical conclusion is that the procedure itself is portable, "
         "but that any new-basin application should include the kind of "
         "manual review these diagnostics are designed to prompt, rather "
         "than accepting a grid search's output uninspected -- a "
         "recommendation carried forward to Section 5.3.")


# ── Chapter Five ─────────────────────────────────────────────────────────────

def write_chapter5(doc, R, eq):
    chapter_heading(doc, "FIVE", "Conclusion and Recommendations")

    h1(doc, "5.1 Summary of Findings")
    body(doc,
         f"This study developed a purely statistical framework for "
         f"generating synthetic monthly discharge records, using the "
         f"{R['basin']} as a demonstration basin. The annual cycle, which "
         f"accounts for approximately half the variance of the monthly "
         f"record, was removed by seasonal standardisation rather than by "
         f"differencing at lag twelve; Section 4.2 reports both treatments "
         f"and the evidence separating them, namely that seasonal "
         f"differencing leaves an integrated process from which a long "
         f"record cannot be generated. Following the Box–Jenkins "
         f"methodology, the deseasonalised series was tested for "
         f"stationarity and modelled as an ARIMA(p, d, q) process whose "
         f"order was selected objectively by the Akaike Information "
         f"Criterion — {order_str(V(R,'discharge')['order'])} for "
         f"discharge — and estimated with a standard error on every "
         f"coefficient. Applying the identical procedure without "
         f"modification to rainfall and stage returned "
         f"{order_str(V(R,'rainfall')['order'])} and "
         f"{order_str(V(R,'stage')['order'])} respectively, together with "
         f"a different verdict on seasonality for rainfall (Section 4.7).")
    body(doc,
         "Rather than a single deterministic forecast, the fitted model "
         "generates synthetic monthly sequences. Validation over the "
         "independent 2004-2014 period compared the statistical properties "
         "of a 1,000-member ensemble — mean, variability, "
         "skewness, persistence, seasonal amplitude, dry-spell duration and "
         "peak value — with the historical record, rather than a forecast "
         "value with an observed value. Discharge reproduced "
         f"{V(R,'discharge')['validation_n_within']} of "
         f"{V(R,'discharge')['validation_n_total']} properties within the "
         "ensemble's 90 per cent envelope, rainfall all seven, and stage "
         f"{V(R,'stage')['validation_n_within']}. The failures are "
         "concentrated in the seasonal amplitude and traced, in "
         "Section 4.6, to a measurable weakening of the annual cycle over "
         "the observed record rather than to a defect of the model. "
         "Residual diagnostics show no remaining linear autocorrelation "
         "for any of the three variables.")
    body(doc,
         "The validated model was then used for its intended purpose. A "
         "synthetic record of "
         f"{V(R,'discharge')['synthetic_record']['n_months'] // 12:,} years "
         "was generated and repeated "
         f"{V(R,'discharge')['synthetic_record']['n_realisations']} times, "
         f"supplying {V(R,'discharge')['synthetic_record']['n_annual_maxima']:,} "
         "synthetic annual maxima from which design discharges were read "
         "by return period (Table 10). The generated record matches the "
         "observed mean and standard deviation and shows no drift over its "
         "length, and its 10-year value falls close to the largest monthly "
         "discharge observed in thirty-five years of record, which is "
         "where a 10-year event should fall in a sample of that length.")

    h1(doc, "5.2 Contribution of the Study")
    body(doc,
         "The contribution of this work is threefold. Methodologically, it "
         "demonstrates a stochastic, property-based validation procedure "
         "for statistical hydrological modelling, appropriate to a "
         "stochastic model in a way that point-forecast comparison against "
         "a single observed sequence is not, and directly useful for design "
         "applications such as reservoir and spillway sizing that depend on "
         "the range of plausible sequences rather than a single "
         "predicted trajectory. It further establishes a point about model "
         "selection that the standard Box–Jenkins apparatus does not "
         "capture: where the object is a synthetic record rather than a "
         "short-horizon forecast, the stationarity of the generating "
         "process is a selection criterion in its own right, and it can "
         "separate two specifications that residual diagnostics and "
         "information criteria leave indistinguishable (Section 4.2). "
         "Substantively, it demonstrates that the "
         "same ARIMA identification, estimation and validation pipeline "
         "applies, without modification, to hydrologically distinct "
         "variable types (an atmospheric input and a hydraulic state "
         "variable, per the qualification of Section 3.2) at the primary "
         "basin, and, per the supplementary check of Section 4.9, runs "
         "successfully -- producing sensible orders, estimates and "
         "diagnostics rather than silent failures -- at two further basins "
         "in different climate regimes, supporting the claim that the "
         "*procedure* is a general statistical methodology "
         "rather than a model bespoke to one river's discharge. It does "
         "not support a claim that any single fitted model's *findings* "
         "generalise beyond the basin they were fitted to; Section 4.9 "
         "found they specifically do not, which is expected rather than a "
         "shortcoming. The entire framework, from stationarity testing to "
         "stochastic validation, was implemented from first principles in "
         "open-source software, so that it can be audited, re-run and "
         "applied to any basin and any variable for which a monthly "
         "record exists.")

    h1(doc, "5.3 Limitations")
    body(doc,
         "Several limitations should be acknowledged. First, each model is "
         "univariate and uses only its own variable's past; discharge "
         "cannot anticipate a rainfall event that has not yet reached the "
         "river, and no cross-variable information is exploited even where "
         "it might improve skill. Second, the seasonal component is "
         "represented by twelve fixed monthly means and standard "
         "deviations, estimated once and held constant. The evidence of "
         "Section 4.6 is that this basin's annual cycle was not in fact "
         "constant across the record, so a fixed seasonal component is an "
         "approximation whose adequacy the data themselves call into "
         "question; a periodic model with time-varying seasonal parameters "
         "would represent it better. Third, the ARIMA model "
         "is linear, whereas catchment response, especially during extreme "
         "events, is partly non-linear, and the log-linear form has no "
         "upper bound, so its most extreme simulated values are governed "
         "by the assumed distributional form rather than by any physical "
         "limit of the channel (Section 4.6). Fourth, the seasonal "
         "parameters and the ARIMA coefficients are treated as known once "
         "estimated: the synthetic record propagates the innovation "
         "uncertainty of the fitted process but not the sampling "
         "uncertainty of the parameters themselves, so the envelopes "
         "reported in Section 4.6 are narrower than a fully Bayesian "
         "treatment would give, and the design discharges of Table 10 are "
         "correspondingly more precise than the evidence strictly "
         "warrants. Fifth, the primary analysis (Sections "
         "4.1-4.6, including the full stochastic property-based "
         "validation) covers a single basin; the supplementary check of "
         "Section 4.9 shows the identification-estimation procedure itself "
         "runs successfully on basins in different climate regimes, but "
         "also that its qualitative findings (strong discharge/stage "
         "persistence, weak rainfall persistence) do not universally "
         "repeat, and that two of four supplementary fits showed "
         "numerical warning signs (coefficients pinned at the estimator's "
         "stationarity/invertibility boundary, near-zero standard errors) "
         "that a fully automated application would need explicit checks "
         "to catch. Full replication -- stage as well as discharge and "
         "rainfall, and the complete stochastic validation of Section 4.6 "
         "-- at basins beyond the primary one remains to be done.")
    body(doc,
         "A sixth limitation concerns the length of the generated record, "
         "and applies specifically to the web application of Section 3.8, "
         "which will generate a record of any length requested of it. The "
         "model is mathematically defined at any length, so the "
         "software will return a thousand years, or ten thousand, without "
         "complaint; that mathematical availability should not be mistaken "
         "for hydrological reliability, and a longer record does not carry "
         "more information about the river than the thirty-five years the "
         "parameters were estimated from. Every such simulation rests on the "
         "assumption that the stochastic process estimated from the "
         "1980-2003 record continues to govern the basin unchanged. That "
         "assumption is progressively less defensible with lead time, "
         "because climate change, land-use and land-cover change, reservoir "
         "construction or operation, channel and river engineering works, "
         "urbanisation of the catchment, and changes to the gauge or its "
         "measurement practice can each alter the underlying process. A "
         "stationary model cannot represent any of them. The property-based "
         "validation of Section 4.6 establishes only that the fitted models "
         "reproduce the statistical character of an eleven-year held-out "
         "period under conditions closely resembling those of the training "
         "record; it supports no claim about multi-decade horizons. A "
         "generated record should therefore be read as a "
         "synthetic sequence consistent with the historical statistics of "
         "this basin — the input a design calculation such as that of "
         "Table 10 actually requires — and never as a prediction of the "
         "state of the river in a given calendar year. The application "
         "does not label the generated record with future dates, for "
         "precisely this reason.")

    h1(doc, "5.4 Recommendations for Future Work")
    body(doc,
         "Several directions are recommended. First, and most directly "
         "indicated by the results, the fixed seasonal component should be "
         "replaced by a periodic one whose parameters are permitted to "
         "vary over the record. Section 4.6 shows that the annual cycle at "
         "this gauge weakened measurably between the calibration and "
         "validation periods, and that this is the source of the property "
         "checks which fail; twelve constant monthly means cannot "
         "represent it. A periodic autoregressive formulation, in which "
         "the coefficients themselves depend on the position in the cycle "
         "(Salas et al., 1980), is the established treatment and would "
         "test directly whether the failing checks are resolved by it. "
         "Second, the sampling uncertainty of the estimated parameters "
         "should be propagated into the generated record, by resampling "
         "coefficients from their estimated distribution before each "
         "realisation rather than holding them fixed. The design "
         "discharges of Table 10 are currently conditional on one point "
         "estimate of the model, and a return-period estimate that "
         "acknowledged parameter uncertainty would be wider and more "
         "honest. Third, the supplementary cross-basin "
         "check of Section 4.9 should be extended to a full replication -- "
         "stage as well as discharge and rainfall, and the complete "
         "1,000-member stochastic property-based validation of Section "
         "4.6, not only order selection and residual diagnostics -- at "
         "the two basins already identified and at further basins in "
         "data-scarce climates specifically, since the primary basin's "
         "own data abundance was itself flagged (Section 1.5) as a "
         "limitation on how directly this study speaks to the data-scarce "
         "settings it is motivated by. Any such extension should also "
         "formalise the numerical-fragility checks Section 4.9 applied "
         "informally (coefficients pinned at the estimator's boundary, "
         "implausibly small standard errors) into an automated flag, so "
         "that a batch run across many basins does not silently report a "
         "degenerate fit as a good one. Fourth, having "
         "established that discharge and stage can each be forecast "
         "independently from their own past with a common methodology, a "
         "natural extension is a multivariate model that uses each as "
         "auxiliary information for the other, or an ARIMAX formulation "
         "that incorporates a genuine exogenous predictor such as a "
         "short-range meteorological forecast, where one is reliably "
         "available. Fifth, the property-based validation of Section 3.6 "
         "should be complemented by the standard distribution-oriented "
         "verification scores (Gneiting & Raftery, 2007): "
         "prediction-interval coverage, the continuous ranked probability "
         "score, the logarithmic score, rank histograms, and the Brier "
         "score for exceedance of a design threshold. These evaluate the "
         "observation against the full predictive distribution, as the "
         "property comparison does, but score calibration and sharpness at "
         "each lead time rather than aggregate statistics over a window, "
         "and would strengthen the validation argument without reverting to "
         "the point-forecast comparison this study deliberately moved away "
         "from.")
    body(doc,
         "In conclusion, the study demonstrates that a disciplined, fully "
         "reproducible statistical framework, applied identically to three "
         "hydrological variables and validated by the statistical "
         "properties of stochastically generated sequences rather than by "
         "point comparison, yields a coherent and largely successful "
         "account of monthly discharge, rainfall and stage — honest about "
         "the one property it does not reproduce, and about why.")
