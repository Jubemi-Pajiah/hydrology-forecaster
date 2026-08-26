"""
preprocess.py — Load observed daily discharge for the Conecuh River, Alabama.

Data source: CAMELS US dataset (Newman et al., 2015; Addor et al., 2017),
USGS gauge 02371500 (Conecuh River at Brantley, AL), contained in
    basin_timeseries_v1p2_metForcing_obsFlow.zip
    -> basin_dataset_public_v1p2/usgs_streamflow/03/02371500_streamflow_qc.txt

This project forecasts streamflow from its OWN past values (a univariate
statistical time-series approach). No rainfall, temperature, or potential
evapotranspiration is used. Discharge is the only variable.

Pipeline:
  1. Read the raw streamflow file from the CAMELS archive.
  2. Convert discharge from ft3/s to m3/s (x 0.0283168).
  3. Flag the USGS missing-data sentinel (-999) as NaN and fill the few short
     gaps by time interpolation (< 1 % of the record).
  4. Provide a natural-log transform helper (streamflow is strongly
     right-skewed and heteroscedastic; modelling log-flow stabilises variance).
  5. Split into a training period (1980-2003) and a validation period
     (2004-2014).
"""

import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# CAMELS archive and the path of the Conecuh streamflow file inside it
CAMELS_ZIP = PROJECT_ROOT / "basin_timeseries_v1p2_metForcing_obsFlow.zip"
STREAMFLOW_MEMBER = (
    "basin_dataset_public_v1p2/usgs_streamflow/03/02371500_streamflow_qc.txt"
)
# A cached extracted copy so the pipeline runs without the 3.4 GB archive
CACHED_CSV = DATA_DIR / "conecuh_discharge.csv"

# Basin / gauge metadata (Conecuh River at Brantley, AL, gauge 02371500).
# Verified directly against USGS NWIS (station_nm "CONECUH RIVER AT BRANTLEY
# AL") and the CAMELS basin list (camels_name.txt, HUC region 03) on
# 2026-08-12, after discovering that the gauge previously used here,
# 02361000, is actually the Choctawhatchee River, not the Conecuh.
GAUGE_ID = "02371500"
BASIN_NAME = "Conecuh River at Brantley, Alabama, USA"
BASIN_LATITUDE_DEG = 31.80        # gauge latitude (CAMELS forcing file header)
BASIN_AREA_KM2 = 1294.4           # drainage area (CAMELS forcing file header)

# Unit conversion: cubic feet per second -> cubic metres per second
CFS_TO_M3S = 0.0283168

# Calendar split between training (calibration) and validation periods
TRAIN_END = "2003-12-31"
VALID_START = "2004-01-01"

# Small constant guarding the log transform (all observed flows are > 0,
# but interpolation could in principle produce a non-positive value)
LOG_EPS = 1e-3


def load_discharge(zip_path: Path = CAMELS_ZIP) -> pd.DataFrame:
    """
    Load the Conecuh daily discharge series.

    Returns a DataFrame indexed by date with columns:
        flow_cfs : raw discharge (ft3/s), missing flagged as NaN
        flow     : discharge converted to m3/s, short gaps interpolated
        qc       : USGS quality flag (A approved, A:e estimated, M missing)

    The function reads the cached CSV if present; otherwise it extracts the
    streamflow file from the CAMELS archive and writes the cache.
    """
    if CACHED_CSV.exists():
        df = pd.read_csv(CACHED_CSV, parse_dates=["date"]).set_index("date")
        return df

    if not zip_path.exists():
        raise FileNotFoundError(
            f"CAMELS archive not found at {zip_path} and no cached CSV at "
            f"{CACHED_CSV}. Provide one of them to load the discharge series."
        )

    with zipfile.ZipFile(zip_path) as z:
        raw = z.read(STREAMFLOW_MEMBER).decode("utf-8", "replace")

    df = pd.read_csv(
        io.StringIO(raw),
        sep=r"\s+",
        header=None,
        names=["id", "year", "month", "day", "flow_cfs", "qc"],
    )
    df["date"] = pd.to_datetime(df[["year", "month", "day"]])
    df = df.set_index("date").sort_index()

    # USGS missing sentinel -> NaN
    df["flow_cfs"] = df["flow_cfs"].replace(-999.0, np.nan)

    # Convert to m3/s and fill the short gaps by time interpolation
    flow = df["flow_cfs"] * CFS_TO_M3S
    flow = flow.interpolate(method="time", limit_direction="both")
    df["flow"] = flow

    out = df[["flow_cfs", "flow", "qc"]].copy()
    out.to_csv(CACHED_CSV, index=True, index_label="date")
    return out


def log_transform(flow: np.ndarray, offset: float = 0.0) -> np.ndarray:
    """
    Natural log of discharge (variance-stabilising transform).

    ``offset`` is a small constant added before taking the log. It is zero for
    perennial rivers, whose monthly flows never approach zero, and non-zero for
    the seasonally intermittent Sahelian regime of the Hadejia, where dry-season
    monthly means fall to hundredths of a cubic metre per second and, in the
    drought years, to exactly zero. Without an offset a single such month maps
    to a log value several standard deviations below every other observation
    and dominates the monthly variance it belongs to. The constant used and the
    sensitivity of the results to it are reported in the methodology.
    """
    x = np.asarray(flow, dtype=float) + float(offset)
    return np.log(np.maximum(x, LOG_EPS))


def inv_log_transform(log_flow: np.ndarray, offset: float = 0.0) -> np.ndarray:
    """Inverse of :func:`log_transform` (back to m3/s), offset removed and the
    result floored at zero so back-transformation cannot return a negative
    discharge."""
    x = np.exp(np.asarray(log_flow, dtype=float)) - float(offset)
    return np.maximum(x, 0.0) if offset else x


def seasonal_profile(values: np.ndarray, months: np.ndarray, period: int = 12) -> dict:
    """
    Mean and standard deviation of the series for each position in the annual
    cycle -- twelve of each, at a monthly timestep.

    This is the seasonal component of the classical stochastic-hydrology
    generating model (Salas et al., 1980): the twelve monthly means describe
    the shape of the average year and the twelve standard deviations describe
    how variable each month is, both estimated on the log scale from the
    training period only.
    """
    values = np.asarray(values, dtype=float)
    months = np.asarray(months, dtype=int)
    means = np.zeros(period)
    sds = np.zeros(period)
    for k in range(period):
        block = values[months == k + 1]
        if len(block) == 0:
            raise ValueError(f"No observations for position {k + 1} of the cycle.")
        means[k] = block.mean()
        sds[k] = block.std(ddof=1) if len(block) > 1 else 1.0
    sds[sds <= 0] = 1.0
    return {"means": means.tolist(), "sds": sds.tolist(), "period": int(period)}


def deseasonalise(values: np.ndarray, months: np.ndarray, profile: dict) -> np.ndarray:
    """
    Remove the annual cycle: z = (x - mean_month) / sd_month.

    Standardising by month is what makes the residual series stationary, and
    therefore what makes a synthetic record of arbitrary length well defined.
    Seasonal differencing, x(t) - x(t-12), also removes the cycle but leaves an
    integrated process whose variance grows without bound, so it cannot be used
    to generate one (see Section 4.2).
    """
    means = np.asarray(profile["means"], dtype=float)
    sds = np.asarray(profile["sds"], dtype=float)
    idx = np.asarray(months, dtype=int) - 1
    return (np.asarray(values, dtype=float) - means[idx]) / sds[idx]


def reseasonalise(z: np.ndarray, months: np.ndarray, profile: dict) -> np.ndarray:
    """Inverse of :func:`deseasonalise`: x = z * sd_month + mean_month.

    Accepts z of shape (n,) or (n_reps, n); months is indexed along the last
    axis.
    """
    means = np.asarray(profile["means"], dtype=float)
    sds = np.asarray(profile["sds"], dtype=float)
    idx = np.asarray(months, dtype=int) - 1
    return np.asarray(z, dtype=float) * sds[idx] + means[idx]


def cycle_months(n: int, start_month: int = 1, period: int = 12) -> np.ndarray:
    """Month-of-year labels (1..period) for n consecutive steps."""
    return (np.arange(n) + (start_month - 1)) % period + 1


def build_dataset(zip_path: Path = CAMELS_ZIP) -> pd.DataFrame:
    """
    Return the analysis-ready daily series 1980-2014 with columns:
        flow     : observed discharge (m3/s)
        log_flow : natural-log discharge
    Index: continuous DatetimeIndex (gaps interpolated).
    """
    df = load_discharge(zip_path)
    df = df.loc["1980-01-01":"2014-12-31"].copy()
    # Guarantee a continuous daily index
    full_idx = pd.date_range(df.index[0], df.index[-1], freq="D")
    df = df.reindex(full_idx)
    df["flow"] = df["flow"].interpolate(method="time", limit_direction="both")
    df.index.name = "date"
    df["log_flow"] = log_transform(df["flow"].to_numpy())
    return df[["flow", "log_flow"]]


def split_dataset(df: pd.DataFrame):
    """Split into training (1980-2003) and validation (2004-2014) periods."""
    train = df.loc[:TRAIN_END].copy()
    valid = df.loc[VALID_START:].copy()
    return train, valid


# ----------------------------------------------------------------------------
# Monthly, multi-variable loading (discharge, rainfall, stage)
#
# Added 2026-08-12 per reviewer instruction: monthly timestep instead of
# daily, and three independent univariate series instead of discharge-only.
# All three are drawn from the same USGS 02371500 / CAMELS 02371500 basin.
# ----------------------------------------------------------------------------
RAINFALL_CSV = DATA_DIR / "conecuh_rainfall.csv"
STAGE_CSV = DATA_DIR / "conecuh_gage_height_raw.csv"

# Daymet is the primary rainfall product: it covers the full 1980-2014 record
# with zero missing days. Maurer and NLDAS are cached alongside it for
# cross-checking (Maurer truncates at 2008 -- a known CAMELS limitation --
# so it cannot serve as the primary series here).
RAINFALL_PRODUCT = "daymet"


def load_rainfall_daily() -> pd.Series:
    """Daily basin-mean rainfall (mm/day), Daymet product, 1980-2014."""
    df = pd.read_csv(RAINFALL_CSV, parse_dates=["date"]).set_index("date")
    return df[RAINFALL_PRODUCT].rename("value")


def load_stage_daily() -> pd.Series:
    """Daily gage height (m), USGS gauge 02371500, 1980-2014."""
    df = pd.read_csv(STAGE_CSV, parse_dates=["date"]).set_index("date")
    return df["gage_height_m"].rename("value")


def load_discharge_daily() -> pd.Series:
    """Daily discharge (m3/s), USGS gauge 02371500, 1980-2014."""
    return load_discharge()["flow"].rename("value")


# variable name -> (daily loader, monthly aggregation rule)
# discharge and stage are averaged over the month; rainfall is summed (a
# monthly total, not a monthly mean daily rate).
VARIABLE_LOADERS = {
    "discharge": (load_discharge_daily, "mean"),
    "rainfall": (load_rainfall_daily, "sum"),
    "stage": (load_stage_daily, "mean"),
}

MONTHLY_START = "1980-01-01"
MONTHLY_END = "2014-12-31"
TRAIN_END_MONTH = "2003-12-01"
VALID_START_MONTH = "2004-01-01"


def monthly_aggregate(daily: pd.Series, how: str = "mean", min_frac: float = 0.5) -> pd.Series:
    """
    Aggregate a daily series to monthly (month-start index).

    A month is set to NaN -- and later filled by time interpolation across
    the (small number of) neighbouring months -- if fewer than min_frac of
    its days actually have data, rather than silently averaging/summing over
    a mostly-missing month.
    """
    full_idx = pd.date_range(MONTHLY_START, MONTHLY_END, freq="D")
    s = daily.reindex(full_idx)
    counts = s.notna().resample("MS").sum()
    sizes = s.resample("MS").size()
    agg = s.resample("MS").sum() if how == "sum" else s.resample("MS").mean()
    frac = counts / sizes
    n_missing = int((frac < min_frac).sum())
    agg = agg.where(frac >= min_frac)
    agg = agg.interpolate(method="time", limit_direction="both")
    agg.attrs["n_fully_missing_months"] = n_missing
    return agg


def build_monthly_dataset(variable: str) -> pd.DataFrame:
    """
    Monthly analysis-ready series for one of 'discharge', 'rainfall', 'stage'.

    Returns a DataFrame indexed by month-start date with columns:
        value     : monthly mean (discharge m3/s, stage m) or monthly total
                    (rainfall mm)
        log_value : natural-log transform. All three series are strictly
                    positive at monthly resolution for this basin -- checked
                    during data acquisition (2026-08-12), not assumed.
    The count of months that needed interpolation is stashed in
    df.attrs["n_fully_missing_months"] for reporting in the methodology.
    """
    if variable not in VARIABLE_LOADERS:
        raise ValueError(f"Unknown variable {variable!r}; choose from {list(VARIABLE_LOADERS)}")
    loader, how = VARIABLE_LOADERS[variable]
    daily = loader()
    monthly = monthly_aggregate(daily, how=how)
    df = monthly.to_frame("value")
    df.index.name = "date"
    df["log_value"] = log_transform(df["value"].to_numpy())
    df.attrs["n_fully_missing_months"] = monthly.attrs.get("n_fully_missing_months", 0)
    df.attrs["variable"] = variable
    return df


def split_monthly(df: pd.DataFrame):
    """Split a monthly dataset into training (1980-2003) and validation
    (2004-2014) periods -- the same calendar split as the daily pipeline."""
    train = df.loc[:TRAIN_END_MONTH].copy()
    valid = df.loc[VALID_START_MONTH:].copy()
    return train, valid


if __name__ == "__main__":
    df = build_dataset()
    train, valid = split_dataset(df)
    print(f"Basin        : {BASIN_NAME} (USGS {GAUGE_ID})")
    print(f"Full record  : {df.index[0].date()} to {df.index[-1].date()}  ({len(df)} days)")
    print(f"Training     : {train.index[0].date()} to {train.index[-1].date()}  ({len(train)} days)")
    print(f"Validation   : {valid.index[0].date()} to {valid.index[-1].date()}  ({len(valid)} days)")
    print("\nDischarge statistics (m3/s):")
    print(df["flow"].describe().round(3))
    print(f"\nSaved cached discharge to {CACHED_CSV}")


# ============================================================================
# Nigerian case study — Hadejia River at Hadejia
#
# Added 2026-08-25. The reviewer's objection to the previous version was
# that the study was carried out on an American river and therefore said
# nothing about Nigerian hydrology. The case study is now a Nigerian gauge;
# the Conecuh is retained only as a contrasting climatic regime against which
# the deseasonalisation comparison of the results is judged.
#
# Provenance. The record originates from the Nigerian national gauging
# network, was archived by the Global Runoff Data Centre (GRDC station
# 1837401) and was quality-controlled and republished with a DOI as station
# NG_0000012 of the Global Streamflow Indices and Metadata Archive
# (Do et al., 2018; Gudmundsson et al., 2018), from which the monthly means
# used here are taken. Twenty-four Nigerian stations are held in that archive;
# this one has the longest usable record and by a wide margin the least
# missing data (3.7 per cent of months over 1963-2006, longest gap three
# months).
# ============================================================================
HADEJIA_CSV = DATA_DIR / "hadejia_discharge_monthly.csv"

HADEJIA_META = {
    "name": "Hadejia River at Hadejia, Jigawa State, Nigeria",
    "short_name": "Hadejia River at Hadejia",
    "country": "Nigeria",
    "river": "Hadejia",
    "station": "Hadejia",
    "basin": "Hadejia-Jama'are-Komadugu Yobe (Lake Chad basin)",
    "gsim_id": "NG_0000012",
    "grdc_id": "1837401",
    "latitude_deg": 12.4406,
    "longitude_deg": 10.0309,
    "altitude_m": 357.0,
    "area_km2": 30435.0,
    "climate": "Sahelian / semi-arid, single wet season (June-October)",
    "unit": "m3/s",
}

# Analysis window. Two independent reasons close the record at both ends:
#
#   Start 1980. Tiga Dam (1974) on the Kano River and, later, Challawa Gorge
#   Dam (1992) regulate flow upstream of this gauge. A generating model
#   assumes one consistent regime, so the window begins after the first and
#   largest of those interventions rather than straddling it. Independently,
#   the pre-1980 part of the record is where nearly all of the sparse months
#   sit: 36 of the 44 months with less than half their days gauged fall before
#   1980, against 8 in the 26 years after it.
#
#   End February 2006. The last two months of the archived record (March and
#   April 2006) rest on a single gauged day each and are discarded by the
#   same coverage rule applied throughout.
HADEJIA_START = "1980-01-01"
HADEJIA_END = "2006-02-01"
HADEJIA_TRAIN_END = "1999-12-01"
HADEJIA_VALID_START = "2000-01-01"

# Minimum share of a month's days that must be gauged for the archived monthly
# mean to be used; below it the month is treated as missing and filled by time
# interpolation across its neighbours. Same rule, and same 0.5 threshold, as
# the daily-to-monthly aggregation used for the Conecuh series.
HADEJIA_MIN_DAY_FRACTION = 0.5

# Offset added before the log transform, as a fraction of the mean flow of the
# analysis window. One per cent is a conventional small offset; the
# methodology reports the sensitivity of every design figure to this choice,
# which is negligible except in the far tail.
HADEJIA_OFFSET_FRACTION = 0.01


def load_hadejia_monthly() -> pd.DataFrame:
    """
    Monthly mean discharge (m3/s) for the Hadejia River at Hadejia over the
    analysis window, with under-gauged months interpolated.

    Returns a DataFrame indexed by month-start date with a ``value`` column.
    The number of interpolated months is stashed in
    ``df.attrs["n_fully_missing_months"]`` for reporting, matching the
    convention of :func:`monthly_aggregate`.
    """
    raw = pd.read_csv(HADEJIA_CSV, parse_dates=["date"]).set_index("date")
    raw.index.name = "date"
    days_total = raw["n_days_observed"] + raw["n_days_missing"]
    covered = raw["n_days_observed"] / days_total
    value = raw["value"].where(covered >= HADEJIA_MIN_DAY_FRACTION)
    value = value.loc[HADEJIA_START:HADEJIA_END]
    n_missing = int(value.isna().sum())
    value = value.interpolate(method="time", limit_direction="both")
    out = value.to_frame("value")
    out.attrs["n_fully_missing_months"] = n_missing
    return out


def hadejia_log_offset(values: np.ndarray) -> float:
    """The additive constant used before the log transform (see above)."""
    v = np.asarray(values, dtype=float)
    positive = v[v > 0]
    return float(HADEJIA_OFFSET_FRACTION * positive.mean())


# ---------------------------------------------------------------------------
# Basin registry
#
# The model is basin-agnostic by construction: everything downstream of this
# point consumes a monthly series and its log transform and knows nothing
# about which river produced them. That is what allows the same unmodified
# code to run the Nigerian case study and the Conecuh contrast.
# ---------------------------------------------------------------------------
CONECUH_META = {
    "name": BASIN_NAME,
    "short_name": "Conecuh River at Brantley",
    "country": "United States",
    "river": "Conecuh",
    "station": "Brantley",
    "basin": "Conecuh-Escambia",
    "usgs_id": GAUGE_ID,
    "latitude_deg": BASIN_LATITUDE_DEG,
    "longitude_deg": -86.25,
    "altitude_m": None,
    "area_km2": BASIN_AREA_KM2,
    "climate": "Humid subtropical, rainfall in every month",
    "unit": "m3/s",
}

BASINS = {
    "hadejia": HADEJIA_META,
    "conecuh": CONECUH_META,
}

PRIMARY_BASIN = "hadejia"
CONTRAST_BASIN = "conecuh"


def build_basin_monthly(basin: str = PRIMARY_BASIN,
                        variable: str = "discharge") -> pd.DataFrame:
    """
    Monthly analysis-ready series for a basin and variable.

    Returns a DataFrame indexed by month-start date with columns ``value``
    (natural units) and ``log_value`` (natural log, after any offset). The
    offset actually applied is recorded in ``df.attrs["log_offset"]`` so the
    inverse transform can undo it.
    """
    if basin == "hadejia":
        if variable != "discharge":
            raise ValueError(
                "The Hadejia record holds discharge only; rainfall and stage "
                "are available for the Conecuh contrast basin."
            )
        df = load_hadejia_monthly()
        n_interp = df.attrs["n_fully_missing_months"]
        offset = hadejia_log_offset(df["value"].to_numpy())
    elif basin == "conecuh":
        source = build_monthly_dataset(variable)
        df = source[["value"]].copy()
        n_interp = source.attrs["n_fully_missing_months"]
        offset = 0.0
    else:
        raise ValueError(f"Unknown basin {basin!r}; choose from {list(BASINS)}")

    df["log_value"] = log_transform(df["value"].to_numpy(), offset=offset)
    df.attrs["n_fully_missing_months"] = int(n_interp)
    df.attrs["log_offset"] = float(offset)
    df.attrs["basin"] = basin
    df.attrs["variable"] = variable
    return df


def split_basin_monthly(df: pd.DataFrame, basin: str = PRIMARY_BASIN):
    """Chronological training/validation split for a basin's monthly series."""
    if basin == "hadejia":
        train = df.loc[:HADEJIA_TRAIN_END].copy()
        valid = df.loc[HADEJIA_VALID_START:].copy()
    else:
        train = df.loc[:TRAIN_END_MONTH].copy()
        valid = df.loc[VALID_START_MONTH:].copy()
    for part in (train, valid):
        part.attrs.update(df.attrs)
    return train, valid
