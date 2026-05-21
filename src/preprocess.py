"""
preprocess.py — Load NASA POWER daily data for the Ogun-Osun River Basin, Nigeria.
Reads POWER_Point_Daily_19900101_20201231_007d50N_003d50E_LST.csv and builds
a daily DataFrame for model simulation (ungauged basin — no observed discharge).
"""

import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "POWER_Point_Daily_19900101_20201231_007d50N_003d50E_LST.csv"
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Basin parameters — Ogun-Osun River Basin, southwestern Nigeria
BASIN_LATITUDE_DEG = 7.5       # basin centroid latitude
BASIN_AREA_KM2 = 22800.0       # approximate drainage area (km²)

# Unit conversion: Q [mm/day] → Q [m³/s]
# Q [m³/s] = Q [mm/day] × Area [m²] / 86400 s/day / 1000 mm/m
MMDAY_TO_M3S = BASIN_AREA_KM2 * 1e6 / 86400.0 / 1000.0   # ≈ 263.89


def load_nasa_power_csv(csv_path: Path = CSV_PATH) -> pd.DataFrame:
    """
    Load NASA POWER daily CSV.
    File has an 11-line metadata header, then a data header row, then daily data.
    Columns in data: YEAR, DOY, T2M_MAX, T2M_MIN, PRECTOTCORR
    """
    # Skip the 11-line metadata block; line 12 (index 11) is the header
    df = pd.read_csv(csv_path, skiprows=11)
    # Rename to standard names
    df = df.rename(columns={
        "T2M_MAX": "tmax",
        "T2M_MIN": "tmin",
        "PRECTOTCORR": "prcp",
    })
    # Build DatetimeIndex from YEAR + DOY (day-of-year)
    df["date"] = pd.to_datetime(
        df["YEAR"].astype(str) + df["DOY"].astype(str).str.zfill(3),
        format="%Y%j",
    )
    df = df.set_index("date")
    df = df[["prcp", "tmax", "tmin"]]
    # Replace NASA POWER missing-data sentinel with NaN
    df = df.replace(-999, np.nan)
    return df


def hargreaves_pet(tmax: np.ndarray, tmin: np.ndarray, tmean: np.ndarray,
                   doy: np.ndarray, lat_deg: float) -> np.ndarray:
    """
    Hargreaves & Samani (1985) potential evapotranspiration (mm/day).
    PET = 0.0023 * Ra * (Tmax - Tmin)^0.5 * (Tmean + 17.8)
    Ra estimated from latitude and day of year (Allen et al., 1998 formula).
    """
    lat_rad = np.deg2rad(lat_deg)
    delta = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)
    omega_s = np.arccos(-np.tan(lat_rad) * np.tan(delta))
    dr = 1 + 0.033 * np.cos(2 * np.pi * doy / 365)
    Gsc = 0.0820  # solar constant MJ/m²/min
    Ra_MJ = (24 * 60 / np.pi) * Gsc * dr * (
        omega_s * np.sin(lat_rad) * np.sin(delta)
        + np.cos(lat_rad) * np.cos(delta) * np.sin(omega_s)
    )
    Ra = Ra_MJ / 2.45   # convert MJ/m²/day → mm/day equivalent
    pet = 0.0023 * Ra * np.sqrt(np.maximum(tmax - tmin, 0.0)) * (tmean + 17.8)
    return np.maximum(pet, 0.0)


def build_dataset(csv_path: Path = CSV_PATH) -> pd.DataFrame:
    """
    Return a daily DataFrame with columns:
    prcp (mm/day), tmax (°C), tmin (°C), tmean (°C), pet (mm/day)
    Index: DatetimeIndex 1990-01-01 to 2020-12-31.
    No observed discharge — ungauged basin.
    """
    df = load_nasa_power_csv(csv_path)
    df["tmean"] = (df["tmax"] + df["tmin"]) / 2.0

    # Compute PET using Hargreaves method
    doy = df.index.dayofyear.to_numpy().astype(float)
    df["pet"] = hargreaves_pet(
        df["tmax"].to_numpy(),
        df["tmin"].to_numpy(),
        df["tmean"].to_numpy(),
        doy,
        BASIN_LATITUDE_DEG,
    )

    # Keep 1990-2020
    df = df.loc["1990-01-01":"2020-12-31"]

    # Fill any missing values
    df["prcp"] = df["prcp"].fillna(0.0)
    df["pet"] = df["pet"].ffill().fillna(0.0)
    df["tmax"] = df["tmax"].ffill().fillna(float(df["tmax"].mean()))
    df["tmin"] = df["tmin"].ffill().fillna(float(df["tmin"].mean()))
    df["tmean"] = (df["tmax"] + df["tmin"]) / 2.0

    return df


def split_dataset(df: pd.DataFrame):
    """Split into historical (1990-2003) and recent (2004-2020) periods."""
    hist   = df.loc[:"2003-12-31"].copy()
    recent = df.loc["2004-01-01":].copy()
    return hist, recent


if __name__ == "__main__":
    df = build_dataset()
    hist, recent = split_dataset(df)
    print(f"Full dataset : {df.index[0].date()} to {df.index[-1].date()}  ({len(df)} days)")
    print(f"Historical   : {hist.index[0].date()} to {hist.index[-1].date()}  ({len(hist)} days)")
    print(f"Recent       : {recent.index[0].date()} to {recent.index[-1].date()}  ({len(recent)} days)")
    print("\nData statistics:")
    print(df[["prcp", "tmax", "tmin", "pet"]].describe().round(3))

    out = DATA_DIR / "processed_dataset.csv"
    df.to_csv(out)
    print(f"\nSaved to {out}")
