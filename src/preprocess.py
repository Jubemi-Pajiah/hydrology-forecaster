"""
preprocess.py — Load and preprocess CAMELS US basin 02361000 forcing and streamflow data.
Extracts from the zip archive into data/, merges into a single daily DataFrame.
"""

import zipfile
from pathlib import Path
import numpy as np
import pandas as pd

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ZIP_PATH = PROJECT_ROOT / "basin_timeseries_v1p2_metForcing_obsFlow.zip"
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

BASIN_ID = "02361000"
FORCING_PATH_IN_ZIP = f"basin_dataset_public_v1p2/basin_mean_forcing/daymet/03/{BASIN_ID}_lump_cida_forcing_leap.txt"
STREAMFLOW_PATH_IN_ZIP = f"basin_dataset_public_v1p2/usgs_streamflow/03/{BASIN_ID}_streamflow_qc.txt"

# Basin latitude for Hargreaves PET (from forcing file header)
BASIN_LATITUDE_DEG = 31.56
BASIN_AREA_KM2 = 1779.30   # drainage area from CAMELS metadata

# Unit conversion: Q [m³/s] → Q [mm/day]
# Q [mm/day] = Q [m³/s] × 86400 s/day / (Area [m²]) × 1000 mm/m
# = Q [m³/s] × 86400 / (Area_km2 × 1e6) × 1000
M3S_TO_MMDAY = 86400.0 / (BASIN_AREA_KM2 * 1e6) * 1000.0   # ≈ 0.04856
MMDAY_TO_M3S = 1.0 / M3S_TO_MMDAY


def load_forcing(zip_path: Path) -> pd.DataFrame:
    """Load Daymet basin-mean forcing from CAMELS zip."""
    with zipfile.ZipFile(zip_path) as z:
        with z.open(FORCING_PATH_IN_ZIP) as f:
            lines = f.read().decode("utf-8").splitlines()

    # First 3 lines are metadata (lat, elev, area), then header, then data
    header_line = 3  # index of header row
    # Parse
    rows = []
    for line in lines[header_line + 1 :]:
        parts = line.split()
        if len(parts) < 10:
            continue
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        prcp = float(parts[5])   # mm/day
        tmax = float(parts[8])   # °C
        tmin = float(parts[9])   # °C
        rows.append((year, month, day, prcp, tmax, tmin))

    df = pd.DataFrame(rows, columns=["year", "month", "day", "prcp", "tmax", "tmin"])
    df["date"] = pd.to_datetime(df[["year", "month", "day"]])
    df = df.set_index("date").drop(columns=["year", "month", "day"])
    return df


def load_streamflow(zip_path: Path) -> pd.Series:
    """Load USGS streamflow (ft³/s → m³/s) from CAMELS zip."""
    with zipfile.ZipFile(zip_path) as z:
        with z.open(STREAMFLOW_PATH_IN_ZIP) as f:
            lines = f.read().decode("utf-8").splitlines()

    rows = []
    for line in lines:
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            year, month, day = int(parts[1]), int(parts[2]), int(parts[3])
            q_cfs = float(parts[4])
            rows.append((year, month, day, q_cfs))
        except (ValueError, IndexError):
            continue

    df = pd.DataFrame(rows, columns=["year", "month", "day", "q_cfs"])
    df["date"] = pd.to_datetime(df[["year", "month", "day"]])
    df = df.set_index("date")
    # Convert ft³/s to m³/s
    df["q_obs"] = df["q_cfs"] * 0.0283168
    return df["q_obs"]


def hargreaves_pet(tmax: np.ndarray, tmin: np.ndarray, tmean: np.ndarray,
                   doy: np.ndarray, lat_deg: float) -> np.ndarray:
    """
    Hargreaves & Samani (1985) potential evapotranspiration (mm/day).
    PET = 0.0023 * Ra * (Tmax - Tmin)^0.5 * (Tmean + 17.8)
    Ra estimated from latitude and day of year (Allen et al., 1998 formula).
    """
    lat_rad = np.deg2rad(lat_deg)
    # Solar declination
    delta = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)
    # Sunset hour angle
    omega_s = np.arccos(-np.tan(lat_rad) * np.tan(delta))
    # Inverse relative Earth-Sun distance
    dr = 1 + 0.033 * np.cos(2 * np.pi * doy / 365)
    # Extraterrestrial radiation (MJ/m²/day)
    Gsc = 0.0820  # solar constant MJ/m²/min
    Ra_MJ = (24 * 60 / np.pi) * Gsc * dr * (
        omega_s * np.sin(lat_rad) * np.sin(delta)
        + np.cos(lat_rad) * np.cos(delta) * np.sin(omega_s)
    )
    # Convert Ra from MJ/m²/day to mm/day equivalent
    # λ = 2.45 MJ/kg (latent heat), 1 mm water = 1 kg/m²  → Ra_mm = Ra_MJ / 2.45
    Ra = Ra_MJ / 2.45
    # Hargreaves & Samani (1985): PET [mm/day] = 0.0023 × Ra [mm/day] × √(Tmax-Tmin) × (Tmean+17.8)
    pet = 0.0023 * Ra * np.sqrt(np.maximum(tmax - tmin, 0.0)) * (tmean + 17.8)
    return np.maximum(pet, 0.0)


def build_dataset(zip_path: Path = ZIP_PATH) -> pd.DataFrame:
    """
    Return a single merged DataFrame with columns:
    prcp (mm/day), tmax (°C), tmin (°C), tmean (°C), pet (mm/day), q_obs (m³/s)
    Index: daily DatetimeIndex 1980-01-01 to 2014-12-31.
    """
    forcing = load_forcing(zip_path)
    q_obs = load_streamflow(zip_path)

    df = forcing.copy()
    df["tmean"] = (df["tmax"] + df["tmin"]) / 2.0
    df["q_obs"]      = q_obs                             # m³/s (for output)
    df["q_obs_mm"]   = q_obs * M3S_TO_MMDAY             # mm/day (for model calibration)

    # Compute PET
    doy = df.index.dayofyear.to_numpy().astype(float)
    df["pet"] = hargreaves_pet(
        df["tmax"].to_numpy(),
        df["tmin"].to_numpy(),
        df["tmean"].to_numpy(),
        doy,
        BASIN_LATITUDE_DEG,
    )

    # Keep 1980-2014
    df = df.loc["1980-01-01":"2014-12-31"]

    # Drop rows where q_obs is missing or negative
    df = df.dropna(subset=["q_obs"])
    df = df[df["q_obs"] >= 0]
    # Recompute q_obs_mm after filtering
    df["q_obs_mm"] = df["q_obs"] * M3S_TO_MMDAY

    # Fill any remaining NaN in forcing with forward-fill then 0
    df["prcp"] = df["prcp"].fillna(0.0)
    df["pet"] = df["pet"].ffill().fillna(0.0)

    return df


def split_dataset(df: pd.DataFrame):
    """Split into calibration (1980-2003) and validation (2004-2014)."""
    cal = df.loc[:"2003-12-31"].copy()
    val = df.loc["2004-01-01":].copy()
    return cal, val


if __name__ == "__main__":
    df = build_dataset()
    cal, val = split_dataset(df)
    print(f"Full dataset:  {df.index[0].date()} to {df.index[-1].date()}  ({len(df)} days)")
    print(f"Calibration:   {cal.index[0].date()} to {cal.index[-1].date()}  ({len(cal)} days)")
    print(f"Validation:    {val.index[0].date()} to {val.index[-1].date()}  ({len(val)} days)")
    print("\nData statistics:")
    print(df[["prcp", "tmax", "tmin", "pet", "q_obs"]].describe().round(3))

    out = DATA_DIR / "processed_dataset.csv"
    df.to_csv(out)
    print(f"\nSaved to {out}")
