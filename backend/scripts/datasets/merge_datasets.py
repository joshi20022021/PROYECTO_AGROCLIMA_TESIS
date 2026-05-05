"""
merge_datasets.py — Combina dataset_openmeteo.csv + dataset_v2.csv.

Qué hace:
  1. dataset_openmeteo.csv → agrega wind_speed desde nasa_power_mensual.csv
  2. dataset_v2.csv        → agrega altitud_m desde era5_mensual.csv
  3. Concatena ambos       → dataset_combinado.csv (~2.1M filas)

El resultado tiene todas las features del modelo:
  altitud_m, temp_max, temp_min, wind_speed  (antes FEATURES_EXTRA)

Uso:
    python scripts/datasets/merge_datasets.py
"""

import os
import sys
import time

import numpy as np
import pandas as pd

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCES_DIR = os.path.join(BASE_DIR, "data", "sources")
DATASETS_DIR = os.path.join(BASE_DIR, "data", "datasets")

OM_PATH     = os.path.join(DATASETS_DIR, "dataset_openmeteo.csv")
V2_PATH     = os.path.join(DATASETS_DIR, "dataset_v2.csv")
NASA_PATH   = os.path.join(SOURCES_DIR,  "nasa_power_mensual.csv")
ERA5_PATH   = os.path.join(SOURCES_DIR,  "era5_mensual.csv")
OUT_PATH    = os.path.join(DATASETS_DIR, "dataset_combinado.csv")

# Columnas finales — mismo orden en ambos datasets
FINAL_COLS = [
    "municipio", "altitud_m", "crop", "month", "year",
    "temperature", "rainfall", "humidity", "soil_moisture",
    "swvl2", "swvl3", "soil_temp", "soil_ph",
    "light_lux", "greenness_idx",
    "temp_max", "temp_min", "wind_speed",
    "yield_pct",
]


def patch_openmeteo(df_om: pd.DataFrame) -> pd.DataFrame:
    """Agrega wind_speed a dataset_openmeteo desde NASA POWER."""
    print("  Cargando NASA POWER para wind_speed...")
    nasa = pd.read_csv(NASA_PATH, usecols=["municipio", "year", "month", "wind_speed_2m"])
    nasa = nasa.rename(columns={"wind_speed_2m": "wind_speed"})

    df = df_om.merge(nasa, on=["municipio", "year", "month"], how="left")
    n_missing = df["wind_speed"].isna().sum()
    if n_missing:
        df["wind_speed"] = df["wind_speed"].fillna(2.5)
        print(f"  wind_speed: {n_missing} filas sin cobertura NASA → rellenadas con 2.5 m/s")
    else:
        print("  wind_speed: cobertura NASA completa")
    return df


def patch_v2(df_v2: pd.DataFrame) -> pd.DataFrame:
    """Agrega altitud_m a dataset_v2 desde era5_mensual (valor único por municipio)."""
    print("  Cargando ERA5 para altitud_m...")
    era5 = pd.read_csv(ERA5_PATH, usecols=["municipio", "altitud_m"])
    alt_map = era5.groupby("municipio")["altitud_m"].first()

    df = df_v2.copy()
    df["altitud_m"] = df["municipio"].map(alt_map)
    n_missing = df["altitud_m"].isna().sum()
    if n_missing:
        df["altitud_m"] = df["altitud_m"].fillna(800.0)
        print(f"  altitud_m: {n_missing} filas sin cobertura ERA5 → rellenadas con 800 m")
    else:
        print(f"  altitud_m: cobertura ERA5 completa ({alt_map.shape[0]} municipios)")
    return df


def main():
    print("=== Merge de datasets de entrenamiento ===\n")
    t0 = time.time()

    # ── 1) dataset_openmeteo
    print(f"Cargando dataset_openmeteo.csv...")
    df_om = pd.read_csv(OM_PATH)
    print(f"  {len(df_om):,} filas | {df_om['municipio'].nunique()} municipios | cols: {list(df_om.columns)}")
    df_om = patch_openmeteo(df_om)

    # ── 2) dataset_v2
    print(f"\nCargando dataset_v2.csv...")
    df_v2 = pd.read_csv(V2_PATH)
    print(f"  {len(df_v2):,} filas | {df_v2['municipio'].nunique()} municipios | cols: {list(df_v2.columns)}")
    df_v2 = patch_v2(df_v2)

    # ── 3) Alinear columnas y concatenar
    print("\nAlineando columnas y concatenando...")

    # Verificar que todas las columnas finales existen en ambos
    for name, df in [("openmeteo", df_om), ("v2", df_v2)]:
        missing = [c for c in FINAL_COLS if c not in df.columns]
        if missing:
            raise ValueError(f"Columnas faltantes en {name}: {missing}")

    df_om_aligned = df_om[FINAL_COLS]
    df_v2_aligned = df_v2[FINAL_COLS]

    combined = pd.concat([df_om_aligned, df_v2_aligned], ignore_index=True)

    # Quitar filas con yield_pct nulo (debería ser 0 pero por si acaso)
    combined = combined.dropna(subset=["yield_pct", "temperature", "soil_moisture"])

    elapsed = round(time.time() - t0, 1)
    print(f"\n  dataset_openmeteo : {len(df_om_aligned):>9,} filas")
    print(f"  dataset_v2        : {len(df_v2_aligned):>9,} filas")
    print(f"  TOTAL combinado   : {len(combined):>9,} filas")
    print(f"  Municipios únicos : {combined['municipio'].nunique()}")
    print(f"  Cultivos únicos   : {combined['crop'].nunique()}")
    print(f"  Años cubiertos    : {combined['year'].min()} – {combined['year'].max()}")

    # ── 4) Guardar
    print(f"\nGuardando en {OUT_PATH}...")
    combined.to_csv(OUT_PATH, index=False)
    size_mb = os.path.getsize(OUT_PATH) / 1_048_576
    print(f"  Archivo guardado: {size_mb:.1f} MB  (en {elapsed}s)")

    print("\nListo. Para reentrenar:")
    print("  python scripts/training/model_xgboost.py train")


if __name__ == "__main__":
    main()
