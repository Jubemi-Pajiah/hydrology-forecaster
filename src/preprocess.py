"""
preprocess.py — Load observed daily discharge for the Conecuh River, Alabama.

Data source: CAMELS US dataset (Newman et al., 2015; Addor et al., 2017),
USGS gauge 02361000, contained in
    basin_timeseries_v1p2_metForcing_obsFlow.zip
    -> basin_dataset_public_v1p2/usgs_streamflow/03/02361000_streamflow_qc.txt

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
    "basin_dataset_public_v1p2/usgs_streamflow/03/02361000_streamflow_qc.txt"
)
# A cached extracted copy so the pipeline runs without the 3.4 GB archive
CACHED_CSV = DATA_DIR / "conecuh_discharge.csv"

# Basin / gauge metadata (Conecuh River near Brewton / at gauge 02361000)
GAUGE_ID = "02361000"
BASIN_NAME = "Conecuh River, Alabama, USA"
BASIN_LATITUDE_DEG = 31.10        # approx. gauge latitude
BASIN_AREA_KM2 = 3604.0           # approx. drainage area (km2)

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


def log_transform(flow: np.ndarray) -> np.ndarray:
    """Natural log of discharge (variance-stabilising transform)."""
    return np.log(np.maximum(np.asarray(flow, dtype=float), LOG_EPS))


def inv_log_transform(log_flow: np.ndarray) -> np.ndarray:
    """Inverse of :func:`log_transform` (back to m3/s)."""
    return np.exp(np.asarray(log_flow, dtype=float))


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
