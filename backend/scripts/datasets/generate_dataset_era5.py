"""
Genera dataset de entrenamiento usando datos REALES de ERA5-Land (2010-2026).

Por cada archivo .nc extrae promedios mensuales de temperatura, lluvia,
humedad y humedad de suelo para cada municipio. Combina eso con los
rangos óptimos de cada cultivo para calcular yield_pct.

Variables ERA5 base (era5_land_*.nc):
    t2m   → temperatura media (K → °C)
    tp    → precipitación total (m → mm)
    d2m   → temperatura punto de rocío → humedad relativa %
    swvl1 → humedad volumétrica suelo capa 1 (0-7 cm)

Variables ERA5 extra (era5_extra_soil_*.nc):
    swvl2 → humedad suelo capa 2 (7-28 cm, zona de raíces)
    swvl3 → humedad suelo capa 3 (28-100 cm, reserva profunda)
    stl1  → temperatura del suelo capa 1 (K → °C)

Variables estimadas (no disponibles en ERA5):
    soil_ph       → rango típico de suelos guatemaltecos (5.0–7.5)
    light_lux     → estimado desde mes y latitud (temporada seca/húmeda)
    greenness_idx → correlacionado con soil_moisture + ruido

Salida: data/processed/dataset_preliminar.csv
"""

import os
import sys
_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_SCRIPTS, "datasets"))
sys.path.insert(0, os.path.join(_SCRIPTS, "processing"))
import zipfile
import tempfile

import numpy as np
import pandas as pd
import xarray as xr

from crop_reference import build_dataframe as build_crop_ref
from process_era5 import _estimate_rh, MUNICIPIOS, KELVIN_OFFSET

# ── Config ────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR  = os.path.join(BASE_DIR, "data", "raw")
OUT_PATH = os.path.join(BASE_DIR, "data", "datasets", "dataset_preliminar.csv")

RNG = np.random.default_rng(42)

# Cuántas muestras de cultivo generar por cada registro municipio/mes/año
SAMPLES_PER_RECORD = 3

# Rango de pH típico por municipio (suelos guatemaltecos)
PH_RANGES = {
    "Chimaltenango": (5.2, 7.0),
    "Sacatepequez":  (5.5, 7.2),
    "Guatemala":     (5.8, 7.5),
}

# Lux base por mes: más alto en temporada seca (nov-abr), menos en lluviosa
LUX_BY_MONTH = {
    1: 38000, 2: 42000, 3: 44000, 4: 40000,
    5: 28000, 6: 22000, 7: 26000, 8: 24000,
    9: 22000, 10: 24000, 11: 32000, 12: 36000,
}


# ── Funciones de extracción ────────────────────────────────────────────────────

def _open_nc(nc_path: str) -> xr.Dataset:
    """Abre un .nc, extrayéndolo de ZIP si hace falta. Fusiona todos los archivos internos."""
    if zipfile.is_zipfile(nc_path):
        with zipfile.ZipFile(nc_path) as z:
            tmp = tempfile.mkdtemp()
            inner_paths = [z.extract(name, tmp) for name in z.namelist()]
        if len(inner_paths) == 1:
            return xr.open_dataset(inner_paths[0], engine="netcdf4")
        # Fusionar múltiples archivos internos (ej. data_0.nc y data_1.nc)
        return xr.open_mfdataset(inner_paths, combine="by_coords", engine="netcdf4")
    return xr.open_dataset(nc_path, engine="netcdf4")


def extract_monthly_climate(nc_path: str) -> pd.DataFrame:
    """
    Extrae variables base de ERA5-Land (t2m, tp, d2m, swvl1).
    Devuelve DataFrame: municipio, year, month, temperature, rainfall, humidity, soil_moisture
    """
    ds = _open_nc(nc_path)
    records = []

    for municipio, coords in MUNICIPIOS.items():
        point = ds.sel(
            latitude=coords["lat"],
            longitude=coords["lon"],
            method="nearest",
        )

        vt = point["valid_time"]
        years  = np.unique(vt.dt.year.values)

        for year in years:
            for month in range(1, 13):
                mask = (vt.dt.year == year) & (vt.dt.month == month)
                if not mask.any():
                    continue

                sel = point.sel(valid_time=mask)

                temp_c   = round(float(sel["t2m"].mean().values) - KELVIN_OFFSET, 1)
                rainfall = round(float(sel["tp"].sum().values) * 1000, 1)
                dew_c    = float(sel["d2m"].mean().values) - KELVIN_OFFSET
                humidity = round(_estimate_rh(temp_c, dew_c), 1)
                soil_moist = round(float(sel["swvl1"].mean().values), 3)

                records.append({
                    "municipio":    municipio,
                    "year":         int(year),
                    "month":        int(month),
                    "temperature":  temp_c,
                    "rainfall":     max(0.0, rainfall),
                    "humidity":     humidity,
                    "soil_moisture": soil_moist,
                })

    ds.close()
    return pd.DataFrame(records)


def extract_extra_soil(nc_path: str) -> pd.DataFrame:
    """
    Extrae variables extra de ERA5-Land (swvl2, swvl3, stl1) desde era5_extra_soil_*.nc.
    Devuelve DataFrame: municipio, year, month, swvl2, swvl3, soil_temp
    """
    ds = _open_nc(nc_path)
    records = []

    for municipio, coords in MUNICIPIOS.items():
        point = ds.sel(
            latitude=coords["lat"],
            longitude=coords["lon"],
            method="nearest",
        )

        vt = point["valid_time"]
        years = np.unique(vt.dt.year.values)

        for year in years:
            for month in range(1, 13):
                mask = (vt.dt.year == year) & (vt.dt.month == month)
                if not mask.any():
                    continue

                sel = point.sel(valid_time=mask)

                swvl2     = round(float(sel["swvl2"].mean().values), 3)
                swvl3     = round(float(sel["swvl3"].mean().values), 3)
                soil_temp = round(float(sel["stl1"].mean().values) - KELVIN_OFFSET, 1)

                records.append({
                    "municipio": municipio,
                    "year":      int(year),
                    "month":     int(month),
                    "swvl2":     swvl2,
                    "swvl3":     swvl3,
                    "soil_temp": soil_temp,
                })

    ds.close()
    return pd.DataFrame(records)


# ── Función de rendimiento ────────────────────────────────────────────────────

def _score(value: float, opt_min: float, opt_max: float, slope: float = 0.04) -> float:
    if opt_min <= value <= opt_max:
        return 1.0
    dist = min(abs(value - opt_min), abs(value - opt_max))
    return max(0.0, 1.0 - slope * dist)


def compute_yield(row: dict, crop_params: dict) -> float:
    p = crop_params[row["crop"]]
    s_t     = _score(row["temperature"],   p["temp_min"],   p["temp_max"],   slope=0.07)
    s_r     = _score(row["rainfall"],      p["rain_min"],   p["rain_max"],   slope=0.02)
    s_h     = _score(row["humidity"],      p["humidity_min"], p["humidity_max"], slope=0.05)
    s_ph    = _score(row["soil_ph"],       p["ph_min"],     p["ph_max"],     slope=0.30)
    s_sm    = _score(row["soil_moisture"], p["sm_min"],     p["sm_max"],     slope=2.50)
    s_lux   = _score(row["light_lux"],     p["light_min"],  p["light_max"],  slope=0.00005)
    s_green = _score(row["greenness_idx"], p["green_min"],  p["green_max"],  slope=0.08)
    s_stl1  = _score(row["soil_temp"],     p["stl1_min"],   p["stl1_max"],   slope=0.07)
    s_swvl2 = _score(row["swvl2"],         p["swvl2_min"],  p["swvl2_max"],  slope=2.50)
    s_swvl3 = _score(row["swvl3"],         p["swvl3_min"],  p["swvl3_max"],  slope=2.00)

    base  = (s_t*0.18 + s_r*0.18 + s_h*0.12 + s_ph*0.15 +
             s_sm*0.10 + s_lux*0.08 + s_green*0.05 +
             s_stl1*0.07 + s_swvl2*0.05 + s_swvl3*0.02) * 100
    noise = RNG.normal(0, 6)
    return float(np.clip(base + noise, 5, 100))


# ── Pipeline principal ────────────────────────────────────────────────────────

def build_dataset() -> pd.DataFrame:
    # 1. Cargar parámetros óptimos de cultivos
    ref_df      = build_crop_ref()
    crop_params = {row["crop"]: row.to_dict() for _, row in ref_df.iterrows()}
    crops       = list(crop_params.keys())

    # 2. Leer archivos ERA5 base (t2m, tp, d2m, swvl1)
    base_files = sorted([
        os.path.join(RAW_DIR, f)
        for f in os.listdir(RAW_DIR)
        if f.endswith(".nc") and not f.startswith("era5_extra")
    ])

    if not base_files:
        raise FileNotFoundError(f"No hay archivos .nc base en {RAW_DIR}")

    print(f"Leyendo {len(base_files)} archivos ERA5-Land base...")
    climate_frames = []
    for i, nc in enumerate(base_files, 1):
        fname = os.path.basename(nc)
        print(f"  [{i:02d}/{len(base_files)}] {fname} ...", end=" ", flush=True)
        try:
            df_c = extract_monthly_climate(nc)
            climate_frames.append(df_c)
            print(f"{len(df_c)} registros")
        except Exception as e:
            print(f"OMITIDO ({e})")

    climate_df = pd.concat(climate_frames, ignore_index=True)
    climate_df.drop_duplicates(subset=["municipio", "year", "month"], inplace=True)
    climate_df.reset_index(drop=True, inplace=True)
    print(f"\nRegistros clima base (municipio×mes×año): {len(climate_df)}")

    # 3. Leer archivos ERA5 extra soil (swvl2, swvl3, stl1)
    soil_extra_files = sorted([
        os.path.join(RAW_DIR, f)
        for f in os.listdir(RAW_DIR)
        if f.startswith("era5_extra_soil") and f.endswith(".nc")
    ])

    print(f"\nLeyendo {len(soil_extra_files)} archivos ERA5-extra-soil...")
    soil_frames = []
    for i, nc in enumerate(soil_extra_files, 1):
        fname = os.path.basename(nc)
        print(f"  [{i:02d}/{len(soil_extra_files)}] {fname} ...", end=" ", flush=True)
        try:
            df_s = extract_extra_soil(nc)
            soil_frames.append(df_s)
            print(f"{len(df_s)} registros")
        except Exception as e:
            print(f"OMITIDO ({e})")

    if soil_frames:
        soil_df = pd.concat(soil_frames, ignore_index=True)
        soil_df.drop_duplicates(subset=["municipio", "year", "month"], inplace=True)
        climate_df = climate_df.merge(
            soil_df, on=["municipio", "year", "month"], how="left"
        )
        n_matched = climate_df["swvl2"].notna().sum()
        print(f"Variables extra soil unidas: {n_matched}/{len(climate_df)} registros")
    else:
        # Si no hay archivos extra, usar valores derivados de swvl1
        climate_df["swvl2"]     = (climate_df["soil_moisture"] + 0.03).round(3)
        climate_df["swvl3"]     = (climate_df["soil_moisture"] + 0.05).round(3)
        climate_df["soil_temp"] = climate_df["temperature"] - 3.0
        print("Advertencia: sin archivos extra soil, usando estimaciones derivadas")

    # Rellenar NaN de soil_extra con estimaciones para filas sin cobertura
    climate_df["swvl2"] = climate_df["swvl2"].fillna(climate_df["soil_moisture"] + 0.03)
    climate_df["swvl3"] = climate_df["swvl3"].fillna(climate_df["soil_moisture"] + 0.05)
    if "soil_temp" not in climate_df.columns:
        climate_df["soil_temp"] = climate_df["temperature"] - 3.0
    climate_df["soil_temp"] = climate_df["soil_temp"].fillna(climate_df["temperature"] - 3.0)

    print(f"Rango años: {climate_df['year'].min()} – {climate_df['year'].max()}")

    # 4. Expandir: por cada fila de clima, generar N muestras × todos los cultivos
    print(f"\nGenerando dataset ({len(climate_df)} climas × {len(crops)} cultivos × {SAMPLES_PER_RECORD} muestras)...")
    rows = []

    for _, clim in climate_df.iterrows():
        municipio = clim["municipio"]
        month     = clim["month"]
        ph_range  = PH_RANGES[municipio]
        lux_base  = LUX_BY_MONTH[month]

        for crop in crops:
            for _ in range(SAMPLES_PER_RECORD):
                soil_ph   = round(float(RNG.uniform(*ph_range)), 2)

                lux_noise  = RNG.uniform(0.7, 1.3)
                light_lux  = round(float(np.clip(lux_base * lux_noise, 500, 90000)), 0)

                sm_norm   = np.clip((clim["soil_moisture"] - 0.10) / 0.40, 0, 1)
                green_base = 35 + sm_norm * 40
                greenness_idx = round(float(np.clip(green_base + RNG.normal(0, 7), 10, 95)), 1)

                row = {
                    "municipio":     municipio,
                    "crop":          crop,
                    "month":         month,
                    "temperature":   clim["temperature"],
                    "rainfall":      clim["rainfall"],
                    "humidity":      clim["humidity"],
                    "soil_ph":       soil_ph,
                    "soil_moisture": clim["soil_moisture"],
                    "light_lux":     light_lux,
                    "greenness_idx": greenness_idx,
                    "swvl2":         float(clim["swvl2"]),
                    "swvl3":         float(clim["swvl3"]),
                    "soil_temp":     float(clim["soil_temp"]),
                }
                row["yield_pct"] = round(compute_yield(row, crop_params), 1)
                rows.append(row)

    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    return df


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    df = build_dataset()
    df.to_csv(OUT_PATH, index=False)

    print(f"\nDataset guardado : {OUT_PATH}")
    print(f"Total filas      : {len(df):,}")
    print(f"Columnas         : {list(df.columns)}")
    print(f"Cultivos únicos  : {df['crop'].nunique()}")
    print()
    print("Rendimiento promedio por cultivo (top 10):")
    print(df.groupby("crop")["yield_pct"].mean().sort_values(ascending=False).head(10).round(1).to_string())
    print()
    print("Clima promedio por municipio:")
    print(df.groupby("municipio")[["temperature","rainfall","humidity","soil_moisture","swvl2","swvl3","soil_temp"]].mean().round(2).to_string())
