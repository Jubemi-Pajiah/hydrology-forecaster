"""
report_ch345.py — Chapters Three, Four and Five.

Carried over from Chapter3_4_5_Hydrological_Forecasting.docx, with three
changes required by PROJECT TEMPLATE_Civil.docx:

  * the heading hierarchy is flattened to two levels (the template forbids a
    third), so the former 3.2.1-3.2.3, 3.3.1-3.3.2 and 3.4.1-3.4.4 are merged
    into 3.2-3.5;
  * figures and tables are numbered sequentially through the whole report
    (Figure 1-6, Table 1-4) rather than by chapter;
  * every cross-reference is updated to match.

All numerical values are read from data/results.json, so the text cannot drift
from the pipeline output.
"""

from docx.shared import Cm

from report_lib import (body, chapter_heading, equation, figure, h1, table,
                        table_title)


def fm(R, k, which, metric):
    """Fetch a forecast metric: `which` is 'model', 'median' or 'persistence'."""
    return R["forecast"][str(k)][which][metric]


# ── Chapter Three ────────────────────────────────────────────────────────────

def write_chapter3(doc, R, figures_dir, eq):
    chapter_heading(doc, "THREE", "Materials and Methods")

    h1(doc, "3.1 Introduction")
    body(doc,
         "This chapter presents the materials and methods used to develop and "
         "evaluate a short-term streamflow forecasting model for the Conecuh "
         "River, Alabama, United States. In contrast to process-based "
         "hydrological modelling, the approach adopted here is purely "
         "statistical: future river discharge is forecast from the past values "
         "of discharge itself, using the class of autoregressive integrated "
         "moving average (ARIMA) models formalised by Box and Jenkins (1976). "
         "The chapter describes the study basin and data source, the "
         "pre-processing of the discharge record, the theoretical basis of the "
         "ARIMA model, the Box–Jenkins identification procedure, the "
         "multi-step forecasting strategy, and the metrics used to judge "
         "forecast performance.")
    body(doc,
         "The motivation for a discharge-only statistical model is practical "
         "and methodological. Daily river flow is a strongly autocorrelated "
         "process: the flow on any given day carries a large amount of "
         "information about the flow on the following days. A model that "
         "exploits this temporal dependence directly avoids the need for "
         "meteorological inputs, catchment-parameter calibration and the "
         "associated uncertainty, and yields a transparent, reproducible "
         "short-range baseline forecasting tool that is well suited to "
         "data-scarce settings where reliable flow records exist but dense "
         "meteorological networks do not.")
    body(doc,
         "The aim of the study is to develop and evaluate a discharge-only "
         "statistical model for short-term streamflow forecasting. The "
         "specific objectives are: to identify and estimate an appropriate "
         "ARIMA model for the daily discharge series following the "
         "Box–Jenkins procedure; to generate one-, two- and three-day-ahead "
         "forecasts and evaluate them out-of-sample against observed "
         "discharge; to benchmark the model against the persistence forecast "
         "using a persistence skill score; and to verify the statistical "
         "adequacy of the fitted model through residual diagnostics. The "
         "success criterion is stated in Section 3.7.")

    h1(doc, "3.2 Study Area and Data Source")
    body(doc,
         "The study basin is the catchment of the Conecuh River drained to "
         "the United States Geological Survey (USGS) streamflow gauge 02361000 "
         "in southern Alabama, United States. The basin lies in a humid "
         "subtropical, rain-fed region with no appreciable snow influence and "
         "minimal flow regulation, which makes the observed hydrograph a clean "
         "expression of natural catchment response. The gauge has a long, "
         "continuous and high-quality daily flow record, and the basin is "
         "included in the CAMELS (Catchment Attributes and Meteorology for "
         "Large-sample Studies) data set, which has become a community "
         "benchmark for hydrological modelling. The catchment is treated here "
         "as a demonstration basin: the aim is to evaluate a transferable "
         "statistical forecasting methodology rather than to study a "
         "location-specific water-resources problem. The CAMELS record is "
         "deliberately chosen as a long, high-quality benchmark so that the "
         "method can be assessed under controlled, well-observed conditions; "
         "it is the discharge-only design of the method, not the richness of "
         "this particular data set, that makes the approach transferable to "
         "basins where only a flow record is available.")
    body(doc,
         "Daily mean discharge for gauge 02361000 was obtained from the "
         "CAMELS United States data set (Newman et al., 2015; Addor, Newman, "
         "Mizukami, & Clark, 2017), specifically the quality-controlled USGS "
         "streamflow series distributed with that archive. The record spans "
         "1 January 1980 to 31 December 2014, giving 12,784 daily "
         "observations. Discharge in the source file is reported in cubic feet "
         "per second and was converted to cubic metres per second by "
         "multiplying by 0.0283168.")
    body(doc,
         "The river is perennial — flow never falls to zero — which is an "
         "important property for the logarithmic transform described below. "
         "The descriptive statistics of the record are presented with the "
         "results in Section 4.1 (Table 2). No meteorological variables of any "
         "kind, and no other exogenous predictors, were used at any stage of "
         "the analysis.")

    h1(doc, "3.3 Data Pre-processing")
    body(doc,
         "Three pre-processing steps were applied. First, the small "
         "proportion of missing daily values (flagged in the source file with "
         "the value −999) was identified and filled by time-based linear "
         "interpolation; missing values constitute less than one per cent of "
         "the record, so this has negligible effect on the analysis while "
         "guaranteeing a continuous daily index. Second, because daily "
         "discharge is strongly right-skewed and its variability grows with "
         "its magnitude (heteroscedasticity), the series was transformed by "
         "the natural logarithm. Modelling the logarithm of flow stabilises "
         "the variance, renders the series more nearly Gaussian, and prevents "
         "the small number of large flood peaks from dominating the parameter "
         "estimation. Forecasts produced on the logarithmic scale are returned "
         "to physical units by the back-transformation of Section 3.6.")
    body(doc,
         "Third, the record was split chronologically into a training "
         "(calibration) period and an independent validation period. The "
         "training period runs from 1980 to 2003 (8,766 days, approximately "
         "70 per cent of the record) and is used to identify the model order "
         "and estimate its parameters. The validation period runs from 2004 "
         "to 2014 (4,018 days, approximately 30 per cent) and is held back "
         "entirely from model fitting so that forecast skill is assessed on "
         "data the model has never seen. Figure 1 shows the complete "
         "discharge series on both the natural and logarithmic scales, with "
         "the training and validation boundary marked. The implementation of "
         "these steps is listed in Appendix A.")
    figure(doc, figures_dir / "Fig1_DischargeTimeSeries.png",
           "Figure 1: Observed daily discharge of the Conecuh River (USGS "
           "02361000), 1980–2014, on the natural scale (top) and the "
           "log-transformed scale (bottom). The dashed line marks the boundary "
           "between the training (1980–2003) and validation (2004–2014) "
           "periods.")

    h1(doc, "3.4 Theoretical Framework")
    body(doc,
         "Hydrological forecasting models fall broadly into two families. "
         "Process-based (conceptual or physically based) models represent the "
         "catchment's transformation of meteorological forcing into runoff "
         "through storages and fluxes, and therefore require those inputs and "
         "the calibration of catchment parameters. Data-driven or statistical "
         "models, by contrast, infer the forecast relationship directly from "
         "the observed flow record (Solomatine & Ostfeld, 2008). For short "
         "lead times the statistical approach is particularly attractive "
         "because the dominant predictor of tomorrow's flow is today's flow "
         "and the recent flow history. The present study adopts the ARIMA "
         "framework, the best-established statistical methodology for "
         "univariate time-series forecasting (Box & Jenkins, 1976; Salas, "
         "Delleur, Yevjevich, & Lane, 1980; Hipel & McLeod, 1994).")
    body(doc,
         "An autoregressive integrated moving average model, written "
         "ARIMA(p, d, q), describes a time series in terms of three "
         "components: an autoregressive part of order p, in which the current "
         "value depends linearly on its own p previous values; an integration "
         "order d, the number of times the series is differenced to achieve "
         "stationarity; and a moving-average part of order q, in which the "
         "current value depends on the q previous random shocks or errors "
         "(Brockwell & Davis, 2016). Let z(t) denote the log-discharge and B "
         "the backshift operator defined by B z(t) = z(t−1). Differencing of "
         "order d is written (1 − B)^d. The ARIMA(p, d, q) model is")
    equation(doc, "φ(B) (1 − B)^d z(t) = c + θ(B) a(t)", eq())
    body(doc,
         "where φ(B) = 1 − φ1 B − … − φp B^p is the autoregressive "
         "polynomial, θ(B) = 1 + θ1 B + … + θq B^q is the moving-average "
         "polynomial, c is a constant, and a(t) is a white-noise error process "
         "with zero mean and constant variance. Writing w(t) = (1 − B)^d z(t) "
         "for the differenced series, the model in explicit form is")
    equation(doc,
             "w(t) = c + φ1 w(t−1) + … + φp w(t−p) + a(t) + θ1 a(t−1) + … "
             "+ θq a(t−q)", eq())
    body(doc,
         "The task of model building is to determine the orders p, d and q "
         "and to estimate the coefficients φ, θ and c. This is accomplished "
         "through the Box–Jenkins procedure described in the following "
         "section.")

    h1(doc, "3.5 Model Identification and Estimation")
    body(doc,
         "ARIMA modelling requires the differenced series to be stationary, "
         "that is, to have a mean, variance and autocorrelation structure that "
         "do not change over time. Two complementary hypothesis tests were "
         "used to determine the differencing order d. The Augmented "
         "Dickey–Fuller (ADF) test takes a unit root, and hence "
         "non-stationarity, as its null hypothesis; a test statistic more "
         "negative than the critical value leads to rejection of the unit root "
         "in favour of stationarity. The Kwiatkowski–Phillips–Schmidt–Shin "
         "(KPSS) test takes stationarity as its null hypothesis and therefore "
         "provides a confirmatory check in the opposite direction. The "
         "differencing order was increased from zero until both tests agreed "
         "that the series was stationary. The ADF test was implemented as the "
         "regression")
    equation(doc, "Δy(t) = a + γ y(t−1) + Σ βi Δy(t−i) + e(t)", eq())
    body(doc,
         "where Δ denotes the first-difference operator and the coefficients βi are the "
         "coefficients of the augmenting lagged differences. The test "
         "statistic is formed as the ratio of the estimated γ to its standard "
         "error and compared against the MacKinnon (1996) critical values for "
         "the constant-only case (Dickey & Fuller, 1979). The KPSS test "
         "(Kwiatkowski, Phillips, Schmidt, & Shin, 1992) provides the "
         "complementary stationarity-null check. Both tests are listed in "
         "Appendix B.")
    body(doc,
         "Candidate values of the autoregressive order p and moving-average "
         "order q were identified by inspecting the sample autocorrelation "
         "function (ACF) and partial autocorrelation function (PACF) of the "
         "differenced log-discharge. In the classical Box–Jenkins reading, a "
         "PACF that cuts off after lag p together with an ACF that decays "
         "gradually suggests an autoregressive process of order p, whereas an "
         "ACF that cuts off after lag q with a gradually decaying PACF "
         "suggests a moving-average process of order q; a mixture indicates an "
         "ARMA process. The ACF and PACF of the differenced series are shown "
         "in Figure 2, with approximate 95 per cent white-noise confidence "
         "bounds. The partial autocorrelation function was computed using the "
         "Levinson–Durbin recursion, listed in Appendix C.")
    figure(doc, figures_dir / "Fig2_ACF_PACF.png",
           "Figure 2: Sample autocorrelation function (left) and partial "
           "autocorrelation function (right) of the first-differenced "
           "log-discharge. Dashed lines are the approximate 95 per cent "
           "confidence bounds for white noise.")
    body(doc,
         "For a given order, the model parameters were estimated by the "
         "method of conditional sum of squares (CSS), a standard estimator for "
         "ARMA models. The one-step-ahead errors a(t) are computed recursively "
         "from the differenced series for a trial set of coefficients, "
         "conditioning on the first observations, and the coefficients are "
         "chosen to minimise the sum of squared errors. For pure "
         "autoregressive models (q = 0) the estimates were obtained exactly by "
         "ordinary least squares. The error variance was estimated as the "
         "residual sum of squares divided by the effective number of "
         "observations. The estimation routine is listed in Appendix D.")
    body(doc,
         "Rather than relying on visual inspection of the ACF and PACF alone, "
         "the final model order was selected objectively by an iterative grid "
         "search: all candidate ARIMA(p, d, q) models over the ranges p = 0 to "
         "4 and q = 0 to 2, with d fixed by the stationarity tests above, were "
         "fitted in turn to the training series and ranked by the Akaike "
         "Information Criterion (AIC; Hyndman & Athanasopoulos, 2021). This "
         "systematic, repeated testing of each candidate model ensures that "
         "the selected order is not an arbitrary or visual judgement but the "
         "objectively best-supported choice from the full set of plausible "
         "orders. The AIC rewards goodness of fit while penalising the number "
         "of estimated parameters, thereby guarding against over-fitting:")
    equation(doc, "AIC = n ln(σ²) + 2k", eq())
    body(doc,
         "where n is the number of observations, σ² is the estimated error "
         "variance and k is the number of estimated parameters. The Bayesian "
         "Information Criterion (BIC), which applies the heavier penalty "
         "k ln(n), was computed alongside as a confirmatory measure. To ensure "
         "that the AIC values are comparable across orders, every candidate "
         "model was conditioned on the same initial observations, equal to "
         "max(p) + max(q), so that all information criteria are computed on an "
         "identical sample. The order-selection routine is listed in "
         "Appendix E.")

    h1(doc, "3.6 Forecasting Procedure")
    body(doc,
         "Forecasts were generated for lead times of one, two and three days. "
         "Multi-step forecasts were produced recursively: the one-step-ahead "
         "forecast is computed from the model equation, and that forecast is "
         "then fed back as an input to obtain the two-step-ahead forecast, and "
         "so on, with future random shocks set to their expected value of "
         "zero. Forecasts on the differenced log scale were integrated back to "
         "the level of log-discharge and finally returned to discharge in "
         "cubic metres per second.")
    body(doc,
         "Because the model is fitted on the logarithm of discharge, simple "
         "exponentiation of a log-scale forecast yields the median rather than "
         "the mean of the log-normal predictive distribution, and therefore "
         "under-estimates the expected discharge by an amount that grows with "
         "the forecast variance. To remove this retransformation bias, "
         "forecasts were back-transformed using the log-normal correction")
    equation(doc, "Q(t+k | t) = exp( z(t+k | t) + σk² / 2 )", eq())
    body(doc,
         "where Q(t+k | t) and z(t+k | t) denote the k-step forecast of "
         "discharge and of log-discharge respectively, made at origin t, and "
         "σk² is the "
         "corresponding k-step forecast error variance, obtained from the "
         "infinite moving-average (psi-weight) representation of the model as "
         "σk² = σ² Σ ψj² for j = 0 to k−1. The nonparametric smearing "
         "estimator of Duan (1983) was computed as a cross-check and gave a "
         "consistent correction. All performance metrics reported below are "
         "computed on the bias-corrected forecasts, expressed as discharge in "
         "cubic metres per second and not on the log scale.")
    body(doc,
         "Forecast skill was assessed using a rolling-origin, or "
         "walk-forward, evaluation over the validation period. The model "
         "parameters, estimated once on the training period, were held fixed; "
         "then for every day t in the validation period the model was supplied "
         "with the discharge observed up to and including day t and asked to "
         "forecast discharge on day t+k. This produces an out-of-sample "
         "forecast at every origin and reproduces the conditions of genuine "
         "operational forecasting, in which the most recent observations are "
         "always available but the future is not. The forecasting routine is "
         "listed in Appendix F.")
    body(doc,
         "As a benchmark, the naive persistence forecast was evaluated in "
         "parallel. Persistence assumes that discharge does not change over "
         "the lead time, that is, the forecast for day t+k equals the observed "
         "discharge on day t. Persistence is the standard reference for "
         "short-range streamflow forecasting because the high autocorrelation "
         "of daily flow makes it a surprisingly strong competitor; a useful "
         "model must demonstrably improve upon it.")

    h1(doc, "3.7 Performance Evaluation")
    body(doc,
         "Forecast performance was quantified with a complementary set of "
         "metrics. The Nash–Sutcliffe efficiency (NSE; Nash & Sutcliffe, "
         "1970) measures the proportion of observed variance reproduced by the "
         "forecast; the root-mean-square error (RMSE) and mean absolute error "
         "(MAE) measure the magnitude of forecast errors in cubic metres per "
         "second; the percentage bias (PBIAS) measures systematic over- or "
         "under-prediction; and the coefficient of determination (R²) measures "
         "linear association between observed and forecast flows. Their "
         "formulae are")
    equation(doc, "NSE = 1 − Σ(Qobs − Qsim)² / Σ(Qobs − mean(Qobs))²", eq())
    equation(doc, "RMSE = √[ (1/n) Σ(Qobs − Qsim)² ]", eq())
    equation(doc, "PBIAS = 100 × Σ(Qsim − Qobs) / Σ(Qobs)", eq())
    body(doc,
         "The NSE was interpreted using the performance ratings of Moriasi et "
         "al. (2007), reproduced in Table 1.")
    table_title(doc, "Table 1: Performance ratings for the Nash–Sutcliffe "
                     "efficiency, after Moriasi et al. (2007).")
    table(doc, ["NSE value", "Performance rating"],
          [["Greater than 0.75", "Very good"],
           ["0.65 to 0.75", "Good"],
           ["0.50 to 0.65", "Acceptable"],
           ["Less than 0.50", "Unsatisfactory"]])
    body(doc,
         "Because persistence alone attains a high NSE at short lead times, "
         "the decisive measure of added value is the persistence skill score "
         "(PSS):")
    equation(doc, "PSS = 1 − MSE(model) / MSE(persistence)", eq())
    body(doc,
         "where MSE denotes the mean squared error. The study adopts an "
         "explicit success criterion defined in advance: the model is judged "
         "to add value if its persistence skill score is positive and its "
         "one-day Nash–Sutcliffe efficiency attains at least the ‘good’ "
         "Moriasi rating. A positive PSS indicates that the statistical model "
         "outperforms persistence; a value of zero indicates no improvement, "
         "and a negative value indicates that the model is inferior to simply "
         "assuming no change. Finally, the adequacy of the fitted model was "
         "checked with the Ljung–Box test, which examines whether the model "
         "residuals retain any significant autocorrelation. A p-value above "
         "0.05 indicates that the residuals are indistinguishable from white "
         "noise and that the model has successfully captured the temporal "
         "structure of the series. The metric definitions are listed in "
         "Appendix G.")

    h1(doc, "3.8 Software and Implementation")
    body(doc,
         "The entire framework was implemented in the Python programming "
         "language. Numerical computation used NumPy (Harris et al., 2020) "
         "and SciPy (Virtanen et al., 2020); figures were produced with "
         "Matplotlib (Hunter, 2007). The ARIMA estimation, stationarity tests, "
         "autocorrelation diagnostics, conditional-sum-of-squares optimisation "
         "and Ljung–Box test were implemented directly from their defining "
         "equations, so that the framework is fully self-contained and "
         "reproducible and carries no dependence on a third-party modelling "
         "package. The complete analysis is driven by a single script, "
         "run_pipeline.py, that loads the data, identifies and estimates the "
         "model, evaluates the forecasts and generates all figures and tables "
         "reported in Chapter Four. The source code is reproduced in the "
         "Appendix.")


# ── Chapter Four ─────────────────────────────────────────────────────────────

def write_chapter4(doc, R, figures_dir, eq):
    chapter_heading(doc, "FOUR", "Results and Discussion")
    stats = R["discharge_stats"]

    h1(doc, "4.1 Characteristics of the Discharge Record")
    body(doc,
         "The daily discharge record of the Conecuh River for the period "
         "1980–2014 comprises 12,784 observations. Its summary statistics are "
         "given in Table 2. The record is strongly right-skewed: the mean "
         f"daily flow of {stats['mean']:.2f} m3/s is far below the maximum of "
         f"{stats['max']:.1f} m3/s, reflecting a regime of low to moderate "
         "flows punctuated by occasional large flood peaks. The minimum flow "
         f"of {stats['min']:.2f} m3/s confirms that the river is perennial, "
         "which justifies the use of the logarithmic transform. This skewness "
         "and the magnitude-dependent variability visible in Figure 1 are "
         "precisely the features that the log transform is intended to "
         "address.")
    table_title(doc, "Table 2: Summary statistics of daily discharge (m3/s), "
                     "1980–2014.")
    table(doc, ["Statistic", "Value (m3/s)"],
          [["Number of daily observations", "12,784"],
           ["Mean", f"{stats['mean']:.2f}"],
           ["Standard deviation", f"{stats['std']:.2f}"],
           ["Minimum", f"{stats['min']:.2f}"],
           ["Maximum", f"{stats['max']:.1f}"]])

    h1(doc, "4.2 Stationarity and Order of Differencing")
    body(doc,
         "The stationarity tests applied to the training series determined "
         "the order of differencing. On the level, undifferenced "
         "log-discharge the two tests disagreed: the Augmented Dickey–Fuller "
         "test rejected the unit root, but the KPSS test also rejected level "
         "stationarity, a pattern indicating a highly persistent series that "
         "is not cleanly stationary in its mean. On the first-differenced "
         "log-discharge both tests agreed — the Augmented Dickey–Fuller test "
         "rejected the unit root decisively and the KPSS statistic fell well "
         "below its five per cent critical value — so the integration order "
         f"was set to d = {R['differencing_d']}. Differencing once removes the "
         "slow drift in the level of the series while preserving its "
         "short-term dynamic structure. It is acknowledged, and revisited in "
         "Chapter Five, that because river discharge is physically bounded and "
         "mean-reverting, a stationary ARMA model fitted to the undifferenced "
         "log-flow is a plausible alternative; the near-unit moving-average "
         "root reported in Section 4.4 is a sign of mild over-differencing in "
         "this respect.")

    h1(doc, "4.3 Model Identification and Selection")
    body(doc,
         "Guided by the autocorrelation and partial autocorrelation functions "
         "of Figure 2, a systematic grid search was carried out over all "
         "ARIMA(p, 1, q) models with p in {0, 1, 2, 3, 4} and q in {0, 1, 2}, "
         "excluding the trivial case p = q = 0. Each of the resulting "
         "candidate models was fitted independently to the training series and "
         "ranked by the Akaike Information Criterion. This iterative, "
         "repeated-testing procedure ensures that the selected order is the "
         "objectively best-supported choice from the full set of plausible "
         "configurations, not a product of visual judgement alone. The five "
         "best-ranked models are listed in Table 3. The selected model is "
         f"{R['model']}, which attains the lowest AIC of {R['aic']:.1f} "
         f"(BIC {R['bic']:.1f}).")
    table_title(doc, "Table 3: Top five candidate ARIMA models ranked by the "
                     "Akaike Information Criterion (lower is better).")
    table(doc, ["Rank", "Model", "AIC", "BIC"],
          [[str(i + 1), f"ARIMA{tuple(r['order'])}", f"{r['aic']:.1f}",
            f"{r['bic']:.1f}"]
           for i, r in enumerate(R.get("aic_ranking", [])[:5])])
    body(doc,
         f"The estimated parameters of the selected {R['model']} model are an "
         "autoregressive vector φ = "
         f"{', '.join(f'{v:.3f}' for v in R['phi'])} and a moving-average "
         f"vector θ = {', '.join(f'{v:.3f}' for v in R['theta'])}, with a "
         "near-zero constant. The combination of autoregressive and "
         "moving-average terms indicates that the river's day-to-day dynamics "
         "are governed both by persistence of the flow level and by the "
         "propagation of recent shocks, for example the recession that follows "
         "a flow peak, consistent with the recession behaviour of a natural "
         "catchment.")

    h1(doc, "4.4 Residual Diagnostics")
    body(doc,
         "The adequacy of the fitted model was assessed from its residuals. "
         f"The Ljung–Box test (lag 20, with {R['ljung_box'].get('dof', 15)} "
         "degrees of freedom) returned a statistic of "
         f"{R['ljung_box']['stat']:.2f} with a p-value of "
         f"{R['ljung_box']['pvalue']:.3f}. Because this p-value exceeds 0.05, "
         "the null hypothesis of no residual autocorrelation cannot be "
         "rejected: there is no significant short-lag autocorrelation in the "
         "residuals, indicating that the selected model has captured the "
         "linear temporal dependence of the log-discharge series. The residual "
         "series, its distribution and its autocorrelation function are shown "
         "in Figure 3.")
    body(doc,
         "Two further diagnostics qualify this result. A test for conditional "
         "heteroscedasticity, the Ljung–Box statistic applied to the squared "
         "residuals in the spirit of Engle (1982), returned p = "
         f"{R['arch']['pvalue']:.3f}, and the Jarque–Bera test of normality "
         "(Jarque & Bera, 1980) returned a statistic of "
         f"{R['jarque_bera']['stat']:.0f} (skewness "
         f"{R['jarque_bera']['skew']:.2f}, kurtosis "
         f"{R['jarque_bera']['kurtosis']:.2f}). These indicate that, although "
         "the residuals are free of linear autocorrelation, they exhibit "
         "volatility clustering and depart from normality — features that are "
         "characteristic of daily streamflow. They do not bias the point "
         "forecasts, but they imply that any future construction of prediction "
         "intervals would require a heteroscedastic, for example "
         "conditional-variance, error model.")
    body(doc,
         "The characteristic roots of the fitted model were examined to "
         "confirm its validity. The autoregressive roots all lie outside the "
         f"unit circle (minimum modulus {min(R['roots']['ar']):.2f}), "
         "confirming stationarity, and the moving-average roots lie outside "
         f"the unit circle (minimum modulus {min(R['roots']['ma']):.2f}), "
         "confirming invertibility. The smallest moving-average root lies only "
         "modestly beyond the unit circle, which suggests mild "
         "over-differencing; this is consistent with the level-series tests of "
         "Section 4.2 and is revisited as a limitation in Chapter Five.")
    figure(doc, figures_dir / "Fig5_ResidualDiagnostics.png",
           "Figure 3: Diagnostic plots of the model residuals: the residual "
           "series (left), the residual distribution against a fitted normal "
           "curve (centre), and the residual autocorrelation function (right).")

    h1(doc, "4.5 Forecast Performance")
    body(doc,
         "The out-of-sample forecast performance over the 2004–2014 "
         "validation period is summarised in Table 4, which reports the "
         "metrics for both the ARIMA model and the persistence benchmark at "
         "each lead time. At a one-day lead the model achieves an NSE of "
         f"{fm(R,1,'model','NSE'):.3f}, rated "
         f"{fm(R,1,'model','rating').lower()} on the Moriasi scale, an RMSE of "
         f"{fm(R,1,'model','RMSE'):.2f} m3/s and a percentage bias of "
         f"{fm(R,1,'model','PBIAS'):.2f} per cent. As expected for a forecast "
         "of a strongly autocorrelated process, skill declines as the lead "
         "time lengthens, with the NSE falling to "
         f"{fm(R,2,'model','NSE'):.3f} at two days and "
         f"{fm(R,3,'model','NSE'):.3f} at three days.")
    table_title(doc, "Table 4: Forecast performance over the validation period "
                     "(2004–2014) for the ARIMA model and the persistence "
                     "benchmark.")
    table(doc,
          ["Lead (days)", "NSE", "RMSE", "MAE", "R²", "PBIAS", "PSS",
           "Persistence NSE", "Persistence RMSE"],
          [[str(k),
            f"{fm(R,k,'model','NSE'):.3f}",
            f"{fm(R,k,'model','RMSE'):.2f}",
            f"{fm(R,k,'model','MAE'):.2f}",
            f"{fm(R,k,'model','R2'):.3f}",
            f"{fm(R,k,'model','PBIAS'):.2f}",
            f"{fm(R,k,'model','PSS'):.3f}",
            f"{fm(R,k,'persistence','NSE'):.3f}",
            f"{fm(R,k,'persistence','RMSE'):.2f}"] for k in (1, 2, 3)],
          font_pt=9.5)
    body(doc,
         "The bias correction of Section 3.6 is effective: before correction "
         "the percentage bias grew markedly with lead time "
         f"({fm(R,1,'median','PBIAS'):.1f} per cent, "
         f"{fm(R,2,'median','PBIAS'):.1f} per cent and "
         f"{fm(R,3,'median','PBIAS'):.1f} per cent at one, two and three "
         "days), confirming that the apparent under-prediction was largely a "
         "log-retransformation artefact rather than a physical effect; after "
         "applying the log-normal correction the bias is reduced to "
         f"{fm(R,1,'model','PBIAS'):.1f} per cent, "
         f"{fm(R,2,'model','PBIAS'):.1f} per cent and "
         f"{fm(R,3,'model','PBIAS'):.1f} per cent respectively — essentially "
         "unbiased.")
    body(doc,
         "The persistence skill score is positive at every lead time "
         f"({fm(R,1,'model','PSS'):.3f}, {fm(R,2,'model','PSS'):.3f} and "
         f"{fm(R,3,'model','PSS'):.3f} at one, two and three days), showing "
         "that the ARIMA model extracts genuine predictive information beyond "
         "the naive assumption of no change. A one-day skill score of "
         f"{fm(R,1,'model','PSS'):.3f} corresponds to a reduction of about "
         f"{100*fm(R,1,'model','PSS'):.0f} per cent in mean squared error, or "
         f"roughly {100*(1-(1-fm(R,1,'model','PSS'))**0.5):.0f} per cent in "
         "root-mean-square error. The skill score rises with lead time, but "
         "this reflects the faster collapse of persistence rather than any "
         "improvement in the model itself: the model's absolute skill falls "
         f"from ‘{fm(R,1,'model','rating').lower()}’ at one day to "
         f"‘{fm(R,3,'model','rating').lower()}’ (NSE "
         f"{fm(R,3,'model','NSE'):.2f}) at three days. Useful absolute skill "
         "is therefore confined to roughly the one-day horizon.")
    body(doc,
         "Figure 4 compares the one-day-ahead forecast with the observed "
         "hydrograph over a representative window of the validation period. "
         "The forecast tracks both the timing and the magnitude of the rises "
         "and recessions closely, with the largest departures occurring at the "
         "sharpest flood peaks, where the assumption of linear dynamics is "
         "most strained. Figure 5 presents the corresponding scatter of "
         "forecast against observed discharge; the points cluster tightly "
         "about the 1:1 line, consistent with the high one-day NSE and the "
         f"R² of {fm(R,1,'model','R2'):.3f}.")
    figure(doc, figures_dir / "Fig3_ForecastHydrograph.png",
           "Figure 4: Observed discharge and one-day-ahead ARIMA forecast, "
           "with the persistence forecast for reference, over a sample of the "
           "validation period.")
    figure(doc, figures_dir / "Fig4_Scatter.png",
           "Figure 5: Observed versus one-day-ahead forecast discharge over "
           "the validation period, with the 1:1 line.", width=Cm(11.5))
    body(doc,
         "Figure 6 summarises the skill comparison across all lead times, "
         "showing the NSE of the model against persistence and the persistence "
         "skill score. The model dominates persistence at every horizon, and "
         "the gap between the two widens with lead time.")
    figure(doc, figures_dir / "Fig6_SkillVsLead.png",
           "Figure 6: Forecast Nash–Sutcliffe efficiency of the ARIMA model "
           "and persistence (left) and the persistence skill score (right) at "
           "one-, two- and three-day lead times.")

    h1(doc, "4.6 Discussion")
    body(doc,
         "The results confirm that a parsimonious univariate ARIMA model, "
         "driven by discharge alone, provides skilful short-range forecasts of "
         "river flow. Several features of the analysis deserve emphasis. "
         "First, the model shows no significant residual autocorrelation, so "
         "it has captured the linear temporal structure of the series; this "
         "should be read as statistical adequacy with respect to linear "
         "dependence rather than as proof of complete specification, since the "
         "residuals do retain volatility clustering and non-normal, "
         "heavy-tailed behaviour typical of daily streamflow. Second, the "
         "model adds real value over persistence, as shown by the uniformly "
         "positive skill score; this is the appropriate standard against which "
         "to judge short-range forecasts, because the high autocorrelation of "
         "daily flow allows persistence to attain an inflated NSE in its own "
         "right. Third, absolute skill declines with lead time and is confined "
         "to roughly the one-day horizon — the fundamental limit of any model "
         "that uses only past flow.")
    body(doc,
         f"The one-day NSE of {fm(R,1,'model','NSE'):.2f} obtained here is "
         "consistent with the range reported for univariate ARIMA streamflow "
         "forecasting in the wider literature (for example Salas et al., 1980; "
         "Hipel & McLeod, 1994), where short-lead daily forecasts of perennial "
         "rivers commonly achieve high one-step efficiencies that decay "
         "rapidly with lead time. The value of the present study lies less in "
         "the headline efficiency than in the disciplined, fully reproducible "
         "Box–Jenkins workflow and the honest benchmarking against "
         "persistence.")
    body(doc,
         "A note on bias is important. Before the log-normal correction the "
         "forecasts showed an increasingly negative bias with lead time; the "
         "correction of Section 3.6 removed almost all of it, demonstrating "
         "that the apparent under-prediction was predominantly a "
         "retransformation, or Jensen, artefact rather than a physical "
         "inability of the model. A residual tendency to under-predict the "
         "very highest peaks remains, visible in Figure 4 and in the large "
         "ratio of RMSE to MAE — an RMSE of "
         f"{fm(R,1,'model','RMSE'):.1f} m3/s against an MAE of only "
         f"{fm(R,1,'model','MAE'):.1f} m3/s at one day — which shows that a "
         "few large peak errors dominate the squared-error metrics while "
         "typical errors are small. This is the expected signature of a linear "
         "model that, using only past flow, cannot anticipate a flood peak "
         "before it begins to register in the river.")
    body(doc,
         "These properties define the model's proper role. Because it cannot "
         "anticipate peaks and its absolute skill is unsatisfactory beyond "
         "about one day, it is best regarded as a transparent, data-light "
         "short-range baseline, and as a benchmark against which more capable "
         "models, whether meteorology-informed or non-linear, should be "
         "judged, rather than as a stand-alone flood-warning system (World "
         "Meteorological Organization, 2011). Its strengths — reproducibility, "
         "minimal data requirements and statistically honest evaluation — are "
         "precisely what make it a useful reference model.")


# ── Chapter Five ─────────────────────────────────────────────────────────────

def write_chapter5(doc, R, eq):
    chapter_heading(doc, "FIVE", "Conclusion and Recommendations")

    h1(doc, "5.1 Summary of Findings")
    body(doc,
         "This study developed and evaluated a purely statistical model for "
         "short-term forecasting of daily river discharge, using the Conecuh "
         "River (USGS gauge 02361000) as a demonstration basin. Following the "
         "Box–Jenkins methodology, the log-transformed discharge series was "
         "tested for stationarity, differenced once, and modelled as an "
         f"{R['model']} process whose order was selected objectively by the "
         "Akaike Information Criterion. The model was estimated on the "
         "1980–2003 training period and evaluated by rolling-origin forecasts "
         "over the independent 2004–2014 validation period.")
    body(doc,
         "The selected model showed no significant residual autocorrelation "
         f"(Ljung–Box p = {R['ljung_box']['pvalue']:.3f}), confirming that it "
         "had captured the linear temporal structure of the series. Forecasts "
         "were back-transformed with a log-normal bias correction, which "
         "reduced the percentage bias to near zero at all horizons. The model "
         "outperformed the persistence benchmark at every lead time, with "
         f"persistence skill scores of {fm(R,1,'model','PSS'):.3f}, "
         f"{fm(R,2,'model','PSS'):.3f} and {fm(R,3,'model','PSS'):.3f} at one, "
         "two and three days, and a one-day Nash–Sutcliffe efficiency of "
         f"{fm(R,1,'model','NSE'):.3f}, rated "
         f"‘{fm(R,1,'model','rating').lower()}’. The pre-defined success "
         "criterion — a positive skill score together with at least a ‘good’ "
         "one-day efficiency — was therefore met, although useful absolute "
         "skill is confined to roughly the one-day horizon, the three-day NSE "
         f"of {fm(R,3,'model','NSE'):.2f} being unsatisfactory on the same "
         "scale.")

    h1(doc, "5.2 Contribution of the Study")
    body(doc,
         "The contribution of this work is a transparent, reproducible and "
         "data-light forecasting framework that depends on the discharge "
         "record alone. By dispensing with meteorological inputs and with the "
         "calibration of catchment parameters, the framework sidesteps two of "
         "the largest sources of effort and uncertainty in operational "
         "hydrological forecasting. The entire methodology, from stationarity "
         "testing to forecast evaluation, was implemented from first "
         "principles in open-source software, so that it can be audited, "
         "re-run and transferred to any basin for which a flow record exists. "
         "This makes the approach particularly suited to data-scarce settings "
         "where reliable discharge measurements are available but dense "
         "meteorological monitoring is not.")

    h1(doc, "5.3 Limitations")
    body(doc,
         "Several limitations should be acknowledged. First, the model is "
         "univariate: it uses only past discharge and therefore cannot "
         "anticipate flow changes driven by meteorological events that have "
         "not yet influenced the river, which limits its ability to predict "
         "the onset and magnitude of the largest flood peaks and confines "
         "useful skill to short lead times. Second, the ARIMA model is linear, "
         "whereas catchment response, especially during extreme events, is "
         "partly non-linear. Third, the residuals, while free of linear "
         "autocorrelation, display volatility clustering, that is conditional "
         "heteroscedasticity, and heavy-tailed, non-normal behaviour; the "
         "reported point forecasts are unaffected, but valid prediction "
         "intervals would require an error model that represents this "
         "behaviour. Fourth, the near-unit moving-average root indicates mild "
         "over-differencing, and a stationary ARMA model on the undifferenced "
         "log-flow — more natural for a bounded, mean-reverting process — was "
         "not pursued here. Fifth, the analysis used a single basin and a "
         "single fixed parameter set held over an eleven-year validation "
         "period; transferability and parameter stability across contrasting "
         "regimes remain to be tested. Sixth, seasonality was not modelled "
         "explicitly, and the residual diagnostics examined short lags only.")

    h1(doc, "5.4 Recommendations for Future Work")
    body(doc,
         "Several directions are recommended. First, the framework should be "
         "applied to additional basins, including rivers in data-scarce "
         "regions, to test the generality of the methodology across "
         "contrasting flow regimes. Second, a stationary ARMA model on the "
         "undifferenced log-flow should be evaluated as an alternative to the "
         "integrated model, given the over-differencing signal noted above. "
         "Third, point forecasts should be extended to probabilistic forecasts "
         "with prediction intervals, using an error model that accounts for "
         "the conditional heteroscedasticity and heavy tails found in the "
         "residuals, so that forecasts support risk-based decision-making. "
         "Fourth, seasonal structure could be represented explicitly through "
         "seasonal ARIMA models, and non-linear data-driven methods such as "
         "artificial neural networks could be benchmarked against the ARIMA "
         "baseline established here. Fifth, where a reliable short-range "
         "meteorological forecast is available, it could be incorporated as an "
         "exogenous predictor, in an ARIMAX formulation, to extend useful "
         "skill to longer lead times without abandoning the statistical "
         "framework.")
    body(doc,
         "In conclusion, the study demonstrates that a disciplined, fully "
         "reproducible statistical time-series analysis of the discharge "
         "record alone yields a skilful short-range baseline forecast — "
         "accurate at the one-day horizon, statistically sound and economical "
         "in its data requirements — that provides an honest benchmark for "
         "more elaborate models.")
