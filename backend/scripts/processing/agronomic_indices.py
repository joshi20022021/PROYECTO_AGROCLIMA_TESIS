"""
Calcula indicadores agronomicos de alto valor cientifico para tesis:
1) Indice de estres hidrico mensual con ETo (FAO Penman-Monteith simplificado)
2) Calendario optimo de siembra por municipio y cultivo

Uso:
    python scripts/processing/agronomic_indices.py
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCES_DIR = os.path.join(BASE_DIR, "data", "sources")
DATASETS_DIR = os.path.join(BASE_DIR, "data", "datasets")
OUT_DIR = os.path.join(BASE_DIR, "data", "processed")

ERA5_PATH = os.path.join(SOURCES_DIR, "era5_mensual.csv")
NASA_PATH = os.path.join(SOURCES_DIR, "nasa_power_mensual.csv")
DATASET_PATH = os.path.join(DATASETS_DIR, "dataset_v2.csv")

OUT_WATER_STRESS = os.path.join(OUT_DIR, "water_stress_index.csv")
OUT_SOWING_CAL = os.path.join(OUT_DIR, "sowing_calendar.csv")


def _sat_vapor_pressure(temp_c: np.ndarray) -> np.ndarray:
    return 0.6108 * np.exp((17.27 * temp_c) / (temp_c + 237.3))


def _delta_svp(temp_c: np.ndarray) -> np.ndarray:
    es = _sat_vapor_pressure(temp_c)
    return 4098 * es / np.power(temp_c + 237.3, 2)


def _atm_pressure_kpa(alt_m: np.ndarray) -> np.ndarray:
    return 101.3 * np.power((293.0 - 0.0065 * alt_m) / 293.0, 5.26)


def _eto_fao56_simplified(df: pd.DataFrame) -> pd.Series:
    """
    FAO56 Penman-Monteith simplificado a escala mensual.
    Entradas requeridas por fila: nasa_temp, nasa_temp_max, nasa_temp_min,
    nasa_humidity, wind_speed_2m, solar_radiation, altitud_m.
    """
    t_mean = df["nasa_temp"].to_numpy(dtype=float)
    t_max = df["nasa_temp_max"].to_numpy(dtype=float)
    t_min = df["nasa_temp_min"].to_numpy(dtype=float)
    rh = np.clip(df["nasa_humidity"].to_numpy(dtype=float), 1.0, 100.0)
    u2 = np.clip(df["wind_speed_2m"].to_numpy(dtype=float), 0.1, None)
    rs = np.clip(df["solar_radiation"].to_numpy(dtype=float), 0.1, None)
    alt = np.nan_to_num(df["altitud_m"].to_numpy(dtype=float), nan=500.0)

    delta = _delta_svp(t_mean)
    pressure = _atm_pressure_kpa(alt)
    gamma = 0.000665 * pressure

    es = (_sat_vapor_pressure(t_max) + _sat_vapor_pressure(t_min)) / 2.0
    ea = es * (rh / 100.0)

    # Aproximacion de radiacion neta diaria en MJ/m2/dia.
    rn = 0.75 * rs
    g = np.zeros_like(rn)

    num = 0.408 * delta * (rn - g) + gamma * (900.0 / (t_mean + 273.0)) * u2 * (es - ea)
    den = delta + gamma * (1.0 + 0.34 * u2)
    eto = np.divide(num, den, out=np.zeros_like(num), where=den != 0)
    return pd.Series(np.clip(eto, 0.0, None))


def build_water_stress_index() -> pd.DataFrame:
    if not os.path.exists(ERA5_PATH):
        raise FileNotFoundError(f"No existe {ERA5_PATH}")
    if not os.path.exists(NASA_PATH):
        raise FileNotFoundError(f"No existe {NASA_PATH}")

    era = pd.read_csv(ERA5_PATH)
    nasa = pd.read_csv(NASA_PATH)

    required_era = ["municipio", "year", "month", "rainfall", "zona", "altitud_m"]
    required_nasa = [
        "municipio", "year", "month", "solar_radiation", "nasa_humidity",
        "nasa_temp", "nasa_temp_max", "nasa_temp_min", "wind_speed_2m",
    ]

    for col in required_era:
        if col not in era.columns:
            raise ValueError(f"Falta columna en ERA5: {col}")
    for col in required_nasa:
        if col not in nasa.columns:
            raise ValueError(f"Falta columna en NASA: {col}")

    merged = era[required_era].merge(
        nasa[required_nasa],
        on=["municipio", "year", "month"],
        how="inner",
    )

    merged["eto_mm_day"] = _eto_fao56_simplified(merged)
    merged["rain_mm_day"] = np.clip(merged["rainfall"] / 30.0, 0.0, None)

    # Stress >1 implica demanda evaporativa mayor que agua recibida.
    merged["water_stress_index"] = merged["eto_mm_day"] / np.clip(merged["rain_mm_day"] + 0.1, 0.1, None)

    def stress_level(x: float) -> str:
        if x >= 1.5:
            return "alto"
        if x >= 1.0:
            return "medio"
        return "bajo"

    merged["stress_level"] = merged["water_stress_index"].apply(stress_level)

    out = merged[[
        "municipio", "zona", "altitud_m", "year", "month",
        "rainfall", "eto_mm_day", "rain_mm_day", "water_stress_index", "stress_level",
    ]].copy()

    out["eto_mm_day"] = out["eto_mm_day"].round(3)
    out["rain_mm_day"] = out["rain_mm_day"].round(3)
    out["water_stress_index"] = out["water_stress_index"].round(3)
    out = out.sort_values(["municipio", "year", "month"]).reset_index(drop=True)
    return out


def build_sowing_calendar() -> pd.DataFrame:
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"No existe {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)
    needed = ["municipio", "crop", "month", "yield_pct"]
    for col in needed:
        if col not in df.columns:
            raise ValueError(f"Falta columna en dataset: {col}")

    df = df.dropna(subset=needed).copy()
    df["yield_pct"] = pd.to_numeric(df["yield_pct"], errors="coerce")
    df = df.dropna(subset=["yield_pct"])

    stats = (
        df.groupby(["municipio", "crop", "month"], as_index=False)
        .agg(
            mean_yield=("yield_pct", "mean"),
            std_yield=("yield_pct", "std"),
            n_samples=("yield_pct", "size"),
            high_yield_rate=("yield_pct", lambda s: (s >= 75).mean()),
        )
    )

    stats["std_yield"] = stats["std_yield"].fillna(0.0)
    stats["high_yield_rate"] = stats["high_yield_rate"].fillna(0.0)

    # Score compuesto: rendimiento esperado + estabilidad + probabilidad alta.
    stats["score"] = (
        0.65 * stats["mean_yield"]
        + 0.30 * (stats["high_yield_rate"] * 100.0)
        - 0.05 * stats["std_yield"]
    )

    stats = stats.sort_values(["municipio", "crop", "score"], ascending=[True, True, False])
    stats["rank"] = stats.groupby(["municipio", "crop"]).cumcount() + 1
    stats["is_top3"] = stats["rank"] <= 3

    out = stats[[
        "municipio", "crop", "month", "rank", "is_top3",
        "mean_yield", "std_yield", "high_yield_rate", "n_samples", "score",
    ]].copy()

    out["mean_yield"] = out["mean_yield"].round(2)
    out["std_yield"] = out["std_yield"].round(2)
    out["high_yield_rate"] = (out["high_yield_rate"] * 100.0).round(1)
    out["score"] = out["score"].round(2)

    # Etiqueta de recomendacion de siembra para lectura rapida.
    out["recommendation"] = np.where(out["is_top3"], "recomendado", "secundario")
    return out


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)

    stress_df = build_water_stress_index()
    stress_df.to_csv(OUT_WATER_STRESS, index=False)

    calendar_df = build_sowing_calendar()
    calendar_df.to_csv(OUT_SOWING_CAL, index=False)

    print(f"OK water stress: {OUT_WATER_STRESS} ({len(stress_df)} filas)")
    print(f"OK sowing calendar: {OUT_SOWING_CAL} ({len(calendar_df)} filas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
