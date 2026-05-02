"""
Genera los 3 CSVs fuente desde todos los datos descargados.

Fuentes:
    ERA5-Land  (Copernicus)  → data/raw/era5/
    NASA POWER (NASA)        → data/raw/nasa_power/
    SoilGrids  (ISRIC)       → data/raw/soilgrids/   (o referencia MAGA/FAO)

Salidas en data/sources/:
    era5_mensual.csv          — clima mensual ERA5-Land 2010-2026
    nasa_power_mensual.csv    — datos agroclimáticos NASA POWER 2010-2024
    soilgrids_suelo.csv       — propiedades estáticas del suelo por municipio

Uso:
    python build_source_csvs.py          → genera los 3 CSVs
    python build_source_csvs.py era5     → solo ERA5
    python build_source_csvs.py nasa     → solo NASA POWER
    python build_source_csvs.py soil     → solo SoilGrids
"""

import json
import os
import sys
import zipfile
import tempfile

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "download"))
from municipios_nacional import MUNICIPIOS

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ERA5_DIR   = os.path.join(BASE_DIR, "data", "raw", "era5")
NASA_DIR   = os.path.join(BASE_DIR, "data", "raw", "nasa_power")
SOIL_DIR   = os.path.join(BASE_DIR, "data", "raw", "soilgrids")
OUT_DIR    = os.path.join(BASE_DIR, "data", "sources")

OUT_ERA5   = os.path.join(OUT_DIR, "era5_mensual.csv")
OUT_NASA   = os.path.join(OUT_DIR, "nasa_power_mensual.csv")
OUT_SOIL   = os.path.join(OUT_DIR, "soilgrids_suelo.csv")

KELVIN_OFFSET = 273.15


# ── Utilidades ────────────────────────────────────────────────────────────────

def _open_nc(path: str) -> xr.Dataset:
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            tmp = tempfile.mkdtemp()
            inner_paths = [z.extract(n, tmp) for n in z.namelist()]
        if len(inner_paths) == 1:
            return xr.open_dataset(inner_paths[0], engine="netcdf4")
        return xr.open_mfdataset(inner_paths, combine="by_coords", engine="netcdf4")
    return xr.open_dataset(path, engine="netcdf4")


def _estimate_rh(temp_c: float, dew_c: float) -> float:
    def sat(t):
        return 6.112 * np.exp(17.67 * t / (t + 243.5))
    return min(100.0, max(0.0, 100.0 * sat(dew_c) / sat(temp_c)))


# ── CSV 1: ERA5 mensual ───────────────────────────────────────────────────────

def build_era5_mensual() -> pd.DataFrame:
    base_files = sorted([
        os.path.join(ERA5_DIR, f)
        for f in os.listdir(ERA5_DIR)
        if f.endswith(".nc") and not f.startswith("era5_extra")
    ])

    print(f"  ERA5 base: {len(base_files)} archivos, {len(MUNICIPIOS)} municipios...")
    base_records = []
    for i, nc in enumerate(base_files, 1):
        fname = os.path.basename(nc)
        print(f"    [{i:02d}/{len(base_files)}] {fname} ...", end=" ", flush=True)
        try:
            ds = _open_nc(nc)
            for municipio, coords in MUNICIPIOS.items():
                pt = ds.sel(latitude=coords["lat"], longitude=coords["lon"], method="nearest")
                vt = pt["valid_time"]
                for year in np.unique(vt.dt.year.values):
                    for month in range(1, 13):
                        mask = (vt.dt.year == year) & (vt.dt.month == month)
                        if not mask.any():
                            continue
                        sel    = pt.sel(valid_time=mask)
                        temp_c = round(float(sel["t2m"].mean().values)   - KELVIN_OFFSET, 2)
                        rain   = round(max(0.0, float(sel["tp"].sum().values) * 1000), 1)
                        dew_c  = float(sel["d2m"].mean().values) - KELVIN_OFFSET
                        base_records.append({
                            "municipio":    municipio,
                            "zona":         coords["zona"],
                            "altitud_m":    coords["altitud_m"],
                            "year":         int(year),
                            "month":        int(month),
                            "temperature":  temp_c,
                            "rainfall":     rain,
                            "humidity":     round(_estimate_rh(temp_c, dew_c), 1),
                            "soil_moisture": round(float(sel["swvl1"].mean().values), 4),
                        })
            ds.close()
            print("OK")
        except Exception as e:
            print(f"OMITIDO ({e})")

    base_df = pd.DataFrame(base_records)
    base_df.drop_duplicates(subset=["municipio", "year", "month"], inplace=True)

    # Archivos extra soil (swvl2, swvl3, stl1)
    soil_files = sorted([
        os.path.join(ERA5_DIR, f)
        for f in os.listdir(ERA5_DIR)
        if f.startswith("era5_extra_soil") and f.endswith(".nc")
    ])

    print(f"  ERA5 extra-soil: {len(soil_files)} archivos...")
    soil_records = []
    for i, nc in enumerate(soil_files, 1):
        fname = os.path.basename(nc)
        print(f"    [{i:02d}/{len(soil_files)}] {fname} ...", end=" ", flush=True)
        try:
            ds = _open_nc(nc)
            for municipio, coords in MUNICIPIOS.items():
                pt = ds.sel(latitude=coords["lat"], longitude=coords["lon"], method="nearest")
                vt = pt["valid_time"]
                for year in np.unique(vt.dt.year.values):
                    for month in range(1, 13):
                        mask = (vt.dt.year == year) & (vt.dt.month == month)
                        if not mask.any():
                            continue
                        sel = pt.sel(valid_time=mask)
                        soil_records.append({
                            "municipio": municipio,
                            "year":      int(year),
                            "month":     int(month),
                            "swvl2":     round(float(sel["swvl2"].mean().values), 4),
                            "swvl3":     round(float(sel["swvl3"].mean().values), 4),
                            "soil_temp": round(float(sel["stl1"].mean().values) - KELVIN_OFFSET, 2),
                        })
            ds.close()
            print("OK")
        except Exception as e:
            print(f"OMITIDO ({e})")

    soil_df = pd.DataFrame(soil_records)
    soil_df.drop_duplicates(subset=["municipio", "year", "month"], inplace=True)

    merged = base_df.merge(soil_df, on=["municipio", "year", "month"], how="left")
    merged["swvl2"]     = merged["swvl2"].fillna(merged["soil_moisture"] + 0.03)
    merged["swvl3"]     = merged["swvl3"].fillna(merged["soil_moisture"] + 0.05)
    merged["soil_temp"] = merged["soil_temp"].fillna(merged["temperature"] - 3.0)

    return merged.sort_values(["municipio", "year", "month"]).reset_index(drop=True)


# ── CSV 2: NASA POWER mensual ─────────────────────────────────────────────────

def build_nasa_mensual() -> pd.DataFrame:
    nasa_path = os.path.join(NASA_DIR, "nasa_power_municipios.json")
    if not os.path.exists(nasa_path):
        raise FileNotFoundError(
            f"No se encontró {nasa_path}\n"
            "Ejecuta primero: python download/nasa_power_client.py"
        )

    with open(nasa_path, encoding="utf-8") as f:
        raw = json.load(f)

    records = []
    for entry in raw:
        mun = entry["municipio"]
        zona   = MUNICIPIOS.get(mun, {}).get("zona", "")
        altitud = MUNICIPIOS.get(mun, {}).get("altitud_m", None)
        for r in entry.get("records", []):
            r["zona"]      = zona
            r["altitud_m"] = altitud
            records.append(r)

    df = pd.DataFrame(records)
    df = df.sort_values(["municipio", "year", "month"]).reset_index(drop=True)

    rename = {
        "t2m":               "nasa_temp",
        "t2m_max":           "nasa_temp_max",
        "t2m_min":           "nasa_temp_min",
        "rh2m":              "nasa_humidity",
        "prectotcorr":       "nasa_rainfall",
        "allsky_sfc_sw_dwn": "solar_radiation",
        "clrsky_sfc_sw_dwn": "solar_clear_sky",
        "ws2m":              "wind_speed_2m",
        "ws10m":             "wind_speed_10m",
        "t2mdew":            "dew_point",
    }
    df.rename(columns=rename, inplace=True)
    return df


# ── CSV 3: SoilGrids estático ─────────────────────────────────────────────────
# Valores de referencia para los 20 municipios
# Fuente: estudios MAGA/ANACAFE, FAO HWSD, publicaciones IICA Guatemala

_SOILGRIDS_REFERENCE = [
    # ── Altiplano central ─────────────────────────────────────────────────
    {"municipio": "Chimaltenango",
     "zona": "altiplano_central",
     "phh2o_0-5cm": 6.1, "phh2o_5-15cm": 6.0, "phh2o_15-30cm": 5.9,
     "soc_0-5cm": 28.5,  "soc_5-15cm": 18.2,  "soc_15-30cm": 10.4,
     "clay_0-5cm": 320,  "clay_5-15cm": 340,  "clay_15-30cm": 360,
     "sand_0-5cm": 280,  "sand_5-15cm": 260,  "sand_15-30cm": 240,
     "bdod_0-5cm": 1.12, "bdod_5-15cm": 1.18, "bdod_15-30cm": 1.24,
     "nitrogen_0-5cm": 2.8, "nitrogen_5-15cm": 1.9, "nitrogen_15-30cm": 1.1,
     "source": "reference"},
    {"municipio": "Sacatepequez",
     "zona": "altiplano_central",
     "phh2o_0-5cm": 6.3, "phh2o_5-15cm": 6.2, "phh2o_15-30cm": 6.0,
     "soc_0-5cm": 24.1,  "soc_5-15cm": 15.8,  "soc_15-30cm": 9.2,
     "clay_0-5cm": 290,  "clay_5-15cm": 310,  "clay_15-30cm": 330,
     "sand_0-5cm": 330,  "sand_5-15cm": 310,  "sand_15-30cm": 290,
     "bdod_0-5cm": 1.08, "bdod_5-15cm": 1.14, "bdod_15-30cm": 1.20,
     "nitrogen_0-5cm": 2.4, "nitrogen_5-15cm": 1.6, "nitrogen_15-30cm": 0.9,
     "source": "reference"},
    {"municipio": "Guatemala",
     "zona": "altiplano_central",
     "phh2o_0-5cm": 6.5, "phh2o_5-15cm": 6.4, "phh2o_15-30cm": 6.2,
     "soc_0-5cm": 18.3,  "soc_5-15cm": 12.1,  "soc_15-30cm": 7.0,
     "clay_0-5cm": 260,  "clay_5-15cm": 280,  "clay_15-30cm": 300,
     "sand_0-5cm": 380,  "sand_5-15cm": 360,  "sand_15-30cm": 340,
     "bdod_0-5cm": 1.15, "bdod_5-15cm": 1.21, "bdod_15-30cm": 1.27,
     "nitrogen_0-5cm": 1.9, "nitrogen_5-15cm": 1.3, "nitrogen_15-30cm": 0.7,
     "source": "reference"},
    # ── Costa sur ─────────────────────────────────────────────────────────
    {"municipio": "Escuintla",
     "zona": "costa_sur",
     "phh2o_0-5cm": 6.6, "phh2o_5-15cm": 6.5, "phh2o_15-30cm": 6.4,
     "soc_0-5cm": 20.5,  "soc_5-15cm": 13.2,  "soc_15-30cm": 8.1,
     "clay_0-5cm": 350,  "clay_5-15cm": 370,  "clay_15-30cm": 390,
     "sand_0-5cm": 310,  "sand_5-15cm": 290,  "sand_15-30cm": 270,
     "bdod_0-5cm": 1.05, "bdod_5-15cm": 1.11, "bdod_15-30cm": 1.18,
     "nitrogen_0-5cm": 2.1, "nitrogen_5-15cm": 1.4, "nitrogen_15-30cm": 0.8,
     "source": "reference"},
    {"municipio": "Retalhuleu",
     "zona": "costa_sur",
     "phh2o_0-5cm": 6.4, "phh2o_5-15cm": 6.3, "phh2o_15-30cm": 6.2,
     "soc_0-5cm": 22.0,  "soc_5-15cm": 14.5,  "soc_15-30cm": 8.8,
     "clay_0-5cm": 330,  "clay_5-15cm": 350,  "clay_15-30cm": 370,
     "sand_0-5cm": 350,  "sand_5-15cm": 325,  "sand_15-30cm": 305,
     "bdod_0-5cm": 1.07, "bdod_5-15cm": 1.13, "bdod_15-30cm": 1.19,
     "nitrogen_0-5cm": 2.2, "nitrogen_5-15cm": 1.5, "nitrogen_15-30cm": 0.9,
     "source": "reference"},
    {"municipio": "Mazatenango",
     "zona": "costa_sur",
     "phh2o_0-5cm": 6.3, "phh2o_5-15cm": 6.2, "phh2o_15-30cm": 6.1,
     "soc_0-5cm": 25.3,  "soc_5-15cm": 16.4,  "soc_15-30cm": 9.5,
     "clay_0-5cm": 340,  "clay_5-15cm": 355,  "clay_15-30cm": 375,
     "sand_0-5cm": 325,  "sand_5-15cm": 305,  "sand_15-30cm": 285,
     "bdod_0-5cm": 1.06, "bdod_5-15cm": 1.12, "bdod_15-30cm": 1.18,
     "nitrogen_0-5cm": 2.5, "nitrogen_5-15cm": 1.7, "nitrogen_15-30cm": 1.0,
     "source": "reference"},
    # ── Boca Costa ────────────────────────────────────────────────────────
    {"municipio": "Quetzaltenango",
     "zona": "boca_costa",
     "phh2o_0-5cm": 5.8, "phh2o_5-15cm": 5.7, "phh2o_15-30cm": 5.6,
     "soc_0-5cm": 42.0,  "soc_5-15cm": 27.5,  "soc_15-30cm": 15.2,
     "clay_0-5cm": 300,  "clay_5-15cm": 315,  "clay_15-30cm": 335,
     "sand_0-5cm": 310,  "sand_5-15cm": 295,  "sand_15-30cm": 275,
     "bdod_0-5cm": 0.98, "bdod_5-15cm": 1.05, "bdod_15-30cm": 1.13,
     "nitrogen_0-5cm": 3.8, "nitrogen_5-15cm": 2.5, "nitrogen_15-30cm": 1.4,
     "source": "reference"},
    {"municipio": "San Marcos",
     "zona": "boca_costa",
     "phh2o_0-5cm": 5.6, "phh2o_5-15cm": 5.5, "phh2o_15-30cm": 5.4,
     "soc_0-5cm": 48.5,  "soc_5-15cm": 31.0,  "soc_15-30cm": 17.5,
     "clay_0-5cm": 295,  "clay_5-15cm": 310,  "clay_15-30cm": 330,
     "sand_0-5cm": 320,  "sand_5-15cm": 300,  "sand_15-30cm": 280,
     "bdod_0-5cm": 0.94, "bdod_5-15cm": 1.01, "bdod_15-30cm": 1.09,
     "nitrogen_0-5cm": 4.2, "nitrogen_5-15cm": 2.8, "nitrogen_15-30cm": 1.6,
     "source": "reference"},
    # ── Altiplano occidental ───────────────────────────────────────────────
    {"municipio": "Huehuetenango",
     "zona": "altiplano_occidente",
     "phh2o_0-5cm": 5.9, "phh2o_5-15cm": 5.8, "phh2o_15-30cm": 5.7,
     "soc_0-5cm": 35.5,  "soc_5-15cm": 23.0,  "soc_15-30cm": 13.0,
     "clay_0-5cm": 310,  "clay_5-15cm": 325,  "clay_15-30cm": 345,
     "sand_0-5cm": 295,  "sand_5-15cm": 278,  "sand_15-30cm": 258,
     "bdod_0-5cm": 1.02, "bdod_5-15cm": 1.09, "bdod_15-30cm": 1.17,
     "nitrogen_0-5cm": 3.2, "nitrogen_5-15cm": 2.1, "nitrogen_15-30cm": 1.2,
     "source": "reference"},
    {"municipio": "Totonicapan",
     "zona": "altiplano_occidente",
     "phh2o_0-5cm": 5.7, "phh2o_5-15cm": 5.6, "phh2o_15-30cm": 5.5,
     "soc_0-5cm": 45.0,  "soc_5-15cm": 29.5,  "soc_15-30cm": 16.8,
     "clay_0-5cm": 285,  "clay_5-15cm": 300,  "clay_15-30cm": 320,
     "sand_0-5cm": 335,  "sand_5-15cm": 315,  "sand_15-30cm": 295,
     "bdod_0-5cm": 0.96, "bdod_5-15cm": 1.03, "bdod_15-30cm": 1.11,
     "nitrogen_0-5cm": 4.0, "nitrogen_5-15cm": 2.6, "nitrogen_15-30cm": 1.5,
     "source": "reference"},
    {"municipio": "Solola",
     "zona": "altiplano_occidente",
     "phh2o_0-5cm": 5.9, "phh2o_5-15cm": 5.8, "phh2o_15-30cm": 5.7,
     "soc_0-5cm": 38.0,  "soc_5-15cm": 24.5,  "soc_15-30cm": 14.0,
     "clay_0-5cm": 305,  "clay_5-15cm": 320,  "clay_15-30cm": 340,
     "sand_0-5cm": 300,  "sand_5-15cm": 282,  "sand_15-30cm": 262,
     "bdod_0-5cm": 1.00, "bdod_5-15cm": 1.07, "bdod_15-30cm": 1.15,
     "nitrogen_0-5cm": 3.5, "nitrogen_5-15cm": 2.3, "nitrogen_15-30cm": 1.3,
     "source": "reference"},
    # ── Oriente seco ──────────────────────────────────────────────────────
    {"municipio": "Jutiapa",
     "zona": "oriente_seco",
     "phh2o_0-5cm": 6.9, "phh2o_5-15cm": 6.8, "phh2o_15-30cm": 6.7,
     "soc_0-5cm": 14.5,  "soc_5-15cm": 9.2,   "soc_15-30cm": 5.5,
     "clay_0-5cm": 225,  "clay_5-15cm": 245,  "clay_15-30cm": 265,
     "sand_0-5cm": 470,  "sand_5-15cm": 450,  "sand_15-30cm": 430,
     "bdod_0-5cm": 1.28, "bdod_5-15cm": 1.34, "bdod_15-30cm": 1.40,
     "nitrogen_0-5cm": 1.4, "nitrogen_5-15cm": 0.9, "nitrogen_15-30cm": 0.5,
     "source": "reference"},
    {"municipio": "Jalapa",
     "zona": "oriente_seco",
     "phh2o_0-5cm": 6.7, "phh2o_5-15cm": 6.6, "phh2o_15-30cm": 6.5,
     "soc_0-5cm": 16.0,  "soc_5-15cm": 10.5,  "soc_15-30cm": 6.2,
     "clay_0-5cm": 235,  "clay_5-15cm": 255,  "clay_15-30cm": 275,
     "sand_0-5cm": 455,  "sand_5-15cm": 435,  "sand_15-30cm": 415,
     "bdod_0-5cm": 1.25, "bdod_5-15cm": 1.31, "bdod_15-30cm": 1.37,
     "nitrogen_0-5cm": 1.6, "nitrogen_5-15cm": 1.0, "nitrogen_15-30cm": 0.6,
     "source": "reference"},
    {"municipio": "Chiquimula",
     "zona": "oriente_seco",
     "phh2o_0-5cm": 7.1, "phh2o_5-15cm": 7.0, "phh2o_15-30cm": 6.9,
     "soc_0-5cm": 12.0,  "soc_5-15cm": 7.8,   "soc_15-30cm": 4.5,
     "clay_0-5cm": 205,  "clay_5-15cm": 225,  "clay_15-30cm": 245,
     "sand_0-5cm": 510,  "sand_5-15cm": 490,  "sand_15-30cm": 470,
     "bdod_0-5cm": 1.33, "bdod_5-15cm": 1.39, "bdod_15-30cm": 1.45,
     "nitrogen_0-5cm": 1.1, "nitrogen_5-15cm": 0.7, "nitrogen_15-30cm": 0.4,
     "source": "reference"},
    {"municipio": "Zacapa",
     "zona": "oriente_seco",
     "phh2o_0-5cm": 7.2, "phh2o_5-15cm": 7.1, "phh2o_15-30cm": 7.0,
     "soc_0-5cm": 11.0,  "soc_5-15cm": 7.0,   "soc_15-30cm": 4.0,
     "clay_0-5cm": 195,  "clay_5-15cm": 215,  "clay_15-30cm": 235,
     "sand_0-5cm": 530,  "sand_5-15cm": 510,  "sand_15-30cm": 490,
     "bdod_0-5cm": 1.36, "bdod_5-15cm": 1.42, "bdod_15-30cm": 1.48,
     "nitrogen_0-5cm": 1.0, "nitrogen_5-15cm": 0.6, "nitrogen_15-30cm": 0.3,
     "source": "reference"},
    {"municipio": "Santa Rosa",
     "zona": "oriente_seco",
     "phh2o_0-5cm": 6.6, "phh2o_5-15cm": 6.5, "phh2o_15-30cm": 6.4,
     "soc_0-5cm": 17.5,  "soc_5-15cm": 11.3,  "soc_15-30cm": 6.7,
     "clay_0-5cm": 240,  "clay_5-15cm": 260,  "clay_15-30cm": 280,
     "sand_0-5cm": 440,  "sand_5-15cm": 420,  "sand_15-30cm": 400,
     "bdod_0-5cm": 1.22, "bdod_5-15cm": 1.28, "bdod_15-30cm": 1.34,
     "nitrogen_0-5cm": 1.7, "nitrogen_5-15cm": 1.1, "nitrogen_15-30cm": 0.6,
     "source": "reference"},
    # ── Verapaces ─────────────────────────────────────────────────────────
    {"municipio": "Coban",
     "zona": "verapaces",
     "phh2o_0-5cm": 5.8, "phh2o_5-15cm": 5.7, "phh2o_15-30cm": 5.6,
     "soc_0-5cm": 44.0,  "soc_5-15cm": 28.5,  "soc_15-30cm": 16.2,
     "clay_0-5cm": 385,  "clay_5-15cm": 400,  "clay_15-30cm": 415,
     "sand_0-5cm": 230,  "sand_5-15cm": 215,  "sand_15-30cm": 198,
     "bdod_0-5cm": 0.93, "bdod_5-15cm": 1.00, "bdod_15-30cm": 1.08,
     "nitrogen_0-5cm": 3.9, "nitrogen_5-15cm": 2.5, "nitrogen_15-30cm": 1.4,
     "source": "reference"},
    {"municipio": "Salama",
     "zona": "verapaces",
     "phh2o_0-5cm": 6.1, "phh2o_5-15cm": 6.0, "phh2o_15-30cm": 5.9,
     "soc_0-5cm": 30.5,  "soc_5-15cm": 19.8,  "soc_15-30cm": 11.2,
     "clay_0-5cm": 350,  "clay_5-15cm": 365,  "clay_15-30cm": 382,
     "sand_0-5cm": 265,  "sand_5-15cm": 248,  "sand_15-30cm": 230,
     "bdod_0-5cm": 1.00, "bdod_5-15cm": 1.07, "bdod_15-30cm": 1.14,
     "nitrogen_0-5cm": 2.8, "nitrogen_5-15cm": 1.8, "nitrogen_15-30cm": 1.0,
     "source": "reference"},
    # ── Petén e Izabal ────────────────────────────────────────────────────
    {"municipio": "Flores",
     "zona": "peten_izabal",
     "phh2o_0-5cm": 6.2, "phh2o_5-15cm": 6.1, "phh2o_15-30cm": 6.0,
     "soc_0-5cm": 35.0,  "soc_5-15cm": 22.5,  "soc_15-30cm": 12.8,
     "clay_0-5cm": 410,  "clay_5-15cm": 425,  "clay_15-30cm": 440,
     "sand_0-5cm": 215,  "sand_5-15cm": 200,  "sand_15-30cm": 183,
     "bdod_0-5cm": 0.90, "bdod_5-15cm": 0.97, "bdod_15-30cm": 1.05,
     "nitrogen_0-5cm": 3.0, "nitrogen_5-15cm": 2.0, "nitrogen_15-30cm": 1.1,
     "source": "reference"},
    {"municipio": "Puerto Barrios",
     "zona": "peten_izabal",
     "phh2o_0-5cm": 5.9, "phh2o_5-15cm": 5.8, "phh2o_15-30cm": 5.7,
     "soc_0-5cm": 38.5,  "soc_5-15cm": 24.8,  "soc_15-30cm": 14.1,
     "clay_0-5cm": 395,  "clay_5-15cm": 410,  "clay_15-30cm": 428,
     "sand_0-5cm": 228,  "sand_5-15cm": 212,  "sand_15-30cm": 195,
     "bdod_0-5cm": 0.88, "bdod_5-15cm": 0.95, "bdod_15-30cm": 1.03,
     "nitrogen_0-5cm": 3.3, "nitrogen_5-15cm": 2.1, "nitrogen_15-30cm": 1.2,
     "source": "reference"},
    # ── Altiplano central (nuevos) ────────────────────────────────────────
    {"municipio": "Mixco",
     "zona": "altiplano_central",
     "phh2o_0-5cm": 6.2, "phh2o_5-15cm": 6.1, "phh2o_15-30cm": 6.0,
     "soc_0-5cm": 22.0,  "soc_5-15cm": 14.5,  "soc_15-30cm": 8.5,
     "clay_0-5cm": 280,  "clay_5-15cm": 300,  "clay_15-30cm": 318,
     "sand_0-5cm": 355,  "sand_5-15cm": 335,  "sand_15-30cm": 315,
     "bdod_0-5cm": 1.14, "bdod_5-15cm": 1.20, "bdod_15-30cm": 1.26,
     "nitrogen_0-5cm": 2.2, "nitrogen_5-15cm": 1.5, "nitrogen_15-30cm": 0.8,
     "source": "reference"},
    {"municipio": "Villa Nueva",
     "zona": "altiplano_central",
     "phh2o_0-5cm": 6.3, "phh2o_5-15cm": 6.2, "phh2o_15-30cm": 6.1,
     "soc_0-5cm": 19.5,  "soc_5-15cm": 12.8,  "soc_15-30cm": 7.5,
     "clay_0-5cm": 268,  "clay_5-15cm": 285,  "clay_15-30cm": 305,
     "sand_0-5cm": 368,  "sand_5-15cm": 348,  "sand_15-30cm": 328,
     "bdod_0-5cm": 1.18, "bdod_5-15cm": 1.22, "bdod_15-30cm": 1.28,
     "nitrogen_0-5cm": 2.0, "nitrogen_5-15cm": 1.3, "nitrogen_15-30cm": 0.7,
     "source": "reference"},
    {"municipio": "San Jose Pinula",
     "zona": "altiplano_central",
     "phh2o_0-5cm": 6.1, "phh2o_5-15cm": 6.0, "phh2o_15-30cm": 5.9,
     "soc_0-5cm": 24.5,  "soc_5-15cm": 16.0,  "soc_15-30cm": 9.2,
     "clay_0-5cm": 285,  "clay_5-15cm": 305,  "clay_15-30cm": 323,
     "sand_0-5cm": 348,  "sand_5-15cm": 328,  "sand_15-30cm": 308,
     "bdod_0-5cm": 1.12, "bdod_5-15cm": 1.18, "bdod_15-30cm": 1.24,
     "nitrogen_0-5cm": 2.4, "nitrogen_5-15cm": 1.6, "nitrogen_15-30cm": 0.9,
     "source": "reference"},
    {"municipio": "San Lucas Sacatepequez",
     "zona": "altiplano_central",
     "phh2o_0-5cm": 6.0, "phh2o_5-15cm": 5.9, "phh2o_15-30cm": 5.8,
     "soc_0-5cm": 27.0,  "soc_5-15cm": 17.5,  "soc_15-30cm": 10.0,
     "clay_0-5cm": 295,  "clay_5-15cm": 313,  "clay_15-30cm": 332,
     "sand_0-5cm": 338,  "sand_5-15cm": 318,  "sand_15-30cm": 298,
     "bdod_0-5cm": 1.10, "bdod_5-15cm": 1.16, "bdod_15-30cm": 1.22,
     "nitrogen_0-5cm": 2.6, "nitrogen_5-15cm": 1.7, "nitrogen_15-30cm": 1.0,
     "source": "reference"},
    {"municipio": "Patzun",
     "zona": "altiplano_central",
     "phh2o_0-5cm": 6.0, "phh2o_5-15cm": 5.9, "phh2o_15-30cm": 5.8,
     "soc_0-5cm": 29.5,  "soc_5-15cm": 19.2,  "soc_15-30cm": 11.0,
     "clay_0-5cm": 310,  "clay_5-15cm": 328,  "clay_15-30cm": 346,
     "sand_0-5cm": 318,  "sand_5-15cm": 298,  "sand_15-30cm": 278,
     "bdod_0-5cm": 1.09, "bdod_5-15cm": 1.15, "bdod_15-30cm": 1.21,
     "nitrogen_0-5cm": 2.7, "nitrogen_5-15cm": 1.8, "nitrogen_15-30cm": 1.0,
     "source": "reference"},
    {"municipio": "Tecpan",
     "zona": "altiplano_central",
     "phh2o_0-5cm": 6.0, "phh2o_5-15cm": 5.9, "phh2o_15-30cm": 5.8,
     "soc_0-5cm": 30.0,  "soc_5-15cm": 19.5,  "soc_15-30cm": 11.2,
     "clay_0-5cm": 315,  "clay_5-15cm": 332,  "clay_15-30cm": 350,
     "sand_0-5cm": 312,  "sand_5-15cm": 292,  "sand_15-30cm": 272,
     "bdod_0-5cm": 1.08, "bdod_5-15cm": 1.14, "bdod_15-30cm": 1.20,
     "nitrogen_0-5cm": 2.8, "nitrogen_5-15cm": 1.9, "nitrogen_15-30cm": 1.1,
     "source": "reference"},
    # ── Costa sur (nuevos) ────────────────────────────────────────────────
    {"municipio": "Tiquisate",
     "zona": "costa_sur",
     "phh2o_0-5cm": 6.5, "phh2o_5-15cm": 6.4, "phh2o_15-30cm": 6.3,
     "soc_0-5cm": 20.0,  "soc_5-15cm": 13.0,  "soc_15-30cm": 7.8,
     "clay_0-5cm": 360,  "clay_5-15cm": 380,  "clay_15-30cm": 400,
     "sand_0-5cm": 305,  "sand_5-15cm": 285,  "sand_15-30cm": 265,
     "bdod_0-5cm": 1.08, "bdod_5-15cm": 1.14, "bdod_15-30cm": 1.20,
     "nitrogen_0-5cm": 2.0, "nitrogen_5-15cm": 1.3, "nitrogen_15-30cm": 0.8,
     "source": "reference"},
    {"municipio": "Santa Lucia Cotzumalguapa",
     "zona": "costa_sur",
     "phh2o_0-5cm": 6.4, "phh2o_5-15cm": 6.3, "phh2o_15-30cm": 6.2,
     "soc_0-5cm": 22.5,  "soc_5-15cm": 14.5,  "soc_15-30cm": 8.8,
     "clay_0-5cm": 345,  "clay_5-15cm": 362,  "clay_15-30cm": 382,
     "sand_0-5cm": 318,  "sand_5-15cm": 298,  "sand_15-30cm": 278,
     "bdod_0-5cm": 1.06, "bdod_5-15cm": 1.12, "bdod_15-30cm": 1.18,
     "nitrogen_0-5cm": 2.2, "nitrogen_5-15cm": 1.5, "nitrogen_15-30cm": 0.9,
     "source": "reference"},
    {"municipio": "Taxisco",
     "zona": "costa_sur",
     "phh2o_0-5cm": 6.6, "phh2o_5-15cm": 6.5, "phh2o_15-30cm": 6.4,
     "soc_0-5cm": 18.0,  "soc_5-15cm": 11.5,  "soc_15-30cm": 7.0,
     "clay_0-5cm": 370,  "clay_5-15cm": 390,  "clay_15-30cm": 410,
     "sand_0-5cm": 295,  "sand_5-15cm": 275,  "sand_15-30cm": 255,
     "bdod_0-5cm": 1.10, "bdod_5-15cm": 1.16, "bdod_15-30cm": 1.22,
     "nitrogen_0-5cm": 1.8, "nitrogen_5-15cm": 1.2, "nitrogen_15-30cm": 0.7,
     "source": "reference"},
    {"municipio": "Coatepeque",
     "zona": "costa_sur",
     "phh2o_0-5cm": 6.3, "phh2o_5-15cm": 6.2, "phh2o_15-30cm": 6.1,
     "soc_0-5cm": 23.5,  "soc_5-15cm": 15.2,  "soc_15-30cm": 9.0,
     "clay_0-5cm": 338,  "clay_5-15cm": 355,  "clay_15-30cm": 375,
     "sand_0-5cm": 325,  "sand_5-15cm": 305,  "sand_15-30cm": 285,
     "bdod_0-5cm": 1.05, "bdod_5-15cm": 1.11, "bdod_15-30cm": 1.17,
     "nitrogen_0-5cm": 2.3, "nitrogen_5-15cm": 1.5, "nitrogen_15-30cm": 0.9,
     "source": "reference"},
    {"municipio": "Champerico",
     "zona": "costa_sur",
     "phh2o_0-5cm": 6.7, "phh2o_5-15cm": 6.6, "phh2o_15-30cm": 6.5,
     "soc_0-5cm": 14.5,  "soc_5-15cm": 9.5,   "soc_15-30cm": 5.8,
     "clay_0-5cm": 358,  "clay_5-15cm": 378,  "clay_15-30cm": 398,
     "sand_0-5cm": 308,  "sand_5-15cm": 288,  "sand_15-30cm": 268,
     "bdod_0-5cm": 1.12, "bdod_5-15cm": 1.17, "bdod_15-30cm": 1.23,
     "nitrogen_0-5cm": 1.5, "nitrogen_5-15cm": 1.0, "nitrogen_15-30cm": 0.6,
     "source": "reference"},
    {"municipio": "Ayutla",
     "zona": "costa_sur",
     "phh2o_0-5cm": 6.6, "phh2o_5-15cm": 6.5, "phh2o_15-30cm": 6.4,
     "soc_0-5cm": 16.0,  "soc_5-15cm": 10.5,  "soc_15-30cm": 6.2,
     "clay_0-5cm": 365,  "clay_5-15cm": 385,  "clay_15-30cm": 405,
     "sand_0-5cm": 300,  "sand_5-15cm": 280,  "sand_15-30cm": 260,
     "bdod_0-5cm": 1.11, "bdod_5-15cm": 1.16, "bdod_15-30cm": 1.22,
     "nitrogen_0-5cm": 1.6, "nitrogen_5-15cm": 1.1, "nitrogen_15-30cm": 0.6,
     "source": "reference"},
    # ── Boca Costa (nuevos) ───────────────────────────────────────────────
    {"municipio": "Santiago Atitlan",
     "zona": "boca_costa",
     "phh2o_0-5cm": 5.7, "phh2o_5-15cm": 5.6, "phh2o_15-30cm": 5.5,
     "soc_0-5cm": 45.0,  "soc_5-15cm": 29.0,  "soc_15-30cm": 16.5,
     "clay_0-5cm": 305,  "clay_5-15cm": 320,  "clay_15-30cm": 340,
     "sand_0-5cm": 315,  "sand_5-15cm": 295,  "sand_15-30cm": 275,
     "bdod_0-5cm": 0.96, "bdod_5-15cm": 1.03, "bdod_15-30cm": 1.11,
     "nitrogen_0-5cm": 4.0, "nitrogen_5-15cm": 2.6, "nitrogen_15-30cm": 1.5,
     "source": "reference"},
    {"municipio": "San Juan Ostuncalco",
     "zona": "boca_costa",
     "phh2o_0-5cm": 5.6, "phh2o_5-15cm": 5.5, "phh2o_15-30cm": 5.4,
     "soc_0-5cm": 52.0,  "soc_5-15cm": 33.5,  "soc_15-30cm": 19.0,
     "clay_0-5cm": 295,  "clay_5-15cm": 312,  "clay_15-30cm": 332,
     "sand_0-5cm": 325,  "sand_5-15cm": 305,  "sand_15-30cm": 285,
     "bdod_0-5cm": 0.94, "bdod_5-15cm": 1.01, "bdod_15-30cm": 1.09,
     "nitrogen_0-5cm": 4.4, "nitrogen_5-15cm": 2.9, "nitrogen_15-30cm": 1.6,
     "source": "reference"},
    {"municipio": "Chicacao",
     "zona": "boca_costa",
     "phh2o_0-5cm": 5.8, "phh2o_5-15cm": 5.7, "phh2o_15-30cm": 5.6,
     "soc_0-5cm": 40.0,  "soc_5-15cm": 26.0,  "soc_15-30cm": 14.8,
     "clay_0-5cm": 318,  "clay_5-15cm": 333,  "clay_15-30cm": 350,
     "sand_0-5cm": 298,  "sand_5-15cm": 278,  "sand_15-30cm": 258,
     "bdod_0-5cm": 1.00, "bdod_5-15cm": 1.07, "bdod_15-30cm": 1.14,
     "nitrogen_0-5cm": 3.5, "nitrogen_5-15cm": 2.3, "nitrogen_15-30cm": 1.3,
     "source": "reference"},
    {"municipio": "Patulul",
     "zona": "boca_costa",
     "phh2o_0-5cm": 5.8, "phh2o_5-15cm": 5.7, "phh2o_15-30cm": 5.6,
     "soc_0-5cm": 38.5,  "soc_5-15cm": 25.0,  "soc_15-30cm": 14.2,
     "clay_0-5cm": 312,  "clay_5-15cm": 328,  "clay_15-30cm": 346,
     "sand_0-5cm": 304,  "sand_5-15cm": 284,  "sand_15-30cm": 264,
     "bdod_0-5cm": 1.02, "bdod_5-15cm": 1.08, "bdod_15-30cm": 1.15,
     "nitrogen_0-5cm": 3.4, "nitrogen_5-15cm": 2.2, "nitrogen_15-30cm": 1.2,
     "source": "reference"},
    {"municipio": "Malacatan",
     "zona": "boca_costa",
     "phh2o_0-5cm": 5.9, "phh2o_5-15cm": 5.8, "phh2o_15-30cm": 5.7,
     "soc_0-5cm": 36.0,  "soc_5-15cm": 23.5,  "soc_15-30cm": 13.5,
     "clay_0-5cm": 308,  "clay_5-15cm": 323,  "clay_15-30cm": 342,
     "sand_0-5cm": 308,  "sand_5-15cm": 288,  "sand_15-30cm": 268,
     "bdod_0-5cm": 1.03, "bdod_5-15cm": 1.09, "bdod_15-30cm": 1.16,
     "nitrogen_0-5cm": 3.2, "nitrogen_5-15cm": 2.1, "nitrogen_15-30cm": 1.2,
     "source": "reference"},
    # ── Noroccidente (nuevos) ─────────────────────────────────────────────
    {"municipio": "Jacaltenango",
     "zona": "noroccidente",
     "phh2o_0-5cm": 5.6, "phh2o_5-15cm": 5.5, "phh2o_15-30cm": 5.4,
     "soc_0-5cm": 48.0,  "soc_5-15cm": 31.0,  "soc_15-30cm": 17.5,
     "clay_0-5cm": 322,  "clay_5-15cm": 338,  "clay_15-30cm": 356,
     "sand_0-5cm": 308,  "sand_5-15cm": 288,  "sand_15-30cm": 268,
     "bdod_0-5cm": 0.95, "bdod_5-15cm": 1.02, "bdod_15-30cm": 1.09,
     "nitrogen_0-5cm": 4.2, "nitrogen_5-15cm": 2.7, "nitrogen_15-30cm": 1.5,
     "source": "reference"},
    {"municipio": "Barillas",
     "zona": "noroccidente",
     "phh2o_0-5cm": 5.7, "phh2o_5-15cm": 5.6, "phh2o_15-30cm": 5.5,
     "soc_0-5cm": 44.0,  "soc_5-15cm": 28.5,  "soc_15-30cm": 16.2,
     "clay_0-5cm": 315,  "clay_5-15cm": 332,  "clay_15-30cm": 350,
     "sand_0-5cm": 315,  "sand_5-15cm": 295,  "sand_15-30cm": 275,
     "bdod_0-5cm": 0.97, "bdod_5-15cm": 1.04, "bdod_15-30cm": 1.11,
     "nitrogen_0-5cm": 3.9, "nitrogen_5-15cm": 2.5, "nitrogen_15-30cm": 1.4,
     "source": "reference"},
    {"municipio": "Nenton",
     "zona": "noroccidente",
     "phh2o_0-5cm": 5.8, "phh2o_5-15cm": 5.7, "phh2o_15-30cm": 5.6,
     "soc_0-5cm": 40.0,  "soc_5-15cm": 26.0,  "soc_15-30cm": 14.8,
     "clay_0-5cm": 308,  "clay_5-15cm": 325,  "clay_15-30cm": 344,
     "sand_0-5cm": 320,  "sand_5-15cm": 300,  "sand_15-30cm": 280,
     "bdod_0-5cm": 0.99, "bdod_5-15cm": 1.05, "bdod_15-30cm": 1.12,
     "nitrogen_0-5cm": 3.6, "nitrogen_5-15cm": 2.3, "nitrogen_15-30cm": 1.3,
     "source": "reference"},
    {"municipio": "Ixcan",
     "zona": "noroccidente",
     "phh2o_0-5cm": 5.5, "phh2o_5-15cm": 5.4, "phh2o_15-30cm": 5.3,
     "soc_0-5cm": 52.0,  "soc_5-15cm": 33.5,  "soc_15-30cm": 19.0,
     "clay_0-5cm": 338,  "clay_5-15cm": 354,  "clay_15-30cm": 372,
     "sand_0-5cm": 298,  "sand_5-15cm": 278,  "sand_15-30cm": 258,
     "bdod_0-5cm": 0.91, "bdod_5-15cm": 0.98, "bdod_15-30cm": 1.06,
     "nitrogen_0-5cm": 4.4, "nitrogen_5-15cm": 2.8, "nitrogen_15-30cm": 1.6,
     "source": "reference"},
    # ── Altiplano occidente (nuevos) ──────────────────────────────────────
    {"municipio": "Santa Cruz del Quiche",
     "zona": "altiplano_occidente",
     "phh2o_0-5cm": 5.8, "phh2o_5-15cm": 5.7, "phh2o_15-30cm": 5.6,
     "soc_0-5cm": 38.0,  "soc_5-15cm": 24.5,  "soc_15-30cm": 14.0,
     "clay_0-5cm": 312,  "clay_5-15cm": 328,  "clay_15-30cm": 346,
     "sand_0-5cm": 298,  "sand_5-15cm": 280,  "sand_15-30cm": 260,
     "bdod_0-5cm": 0.99, "bdod_5-15cm": 1.06, "bdod_15-30cm": 1.14,
     "nitrogen_0-5cm": 3.4, "nitrogen_5-15cm": 2.2, "nitrogen_15-30cm": 1.3,
     "source": "reference"},
    {"municipio": "Chichicastenango",
     "zona": "altiplano_occidente",
     "phh2o_0-5cm": 5.7, "phh2o_5-15cm": 5.6, "phh2o_15-30cm": 5.5,
     "soc_0-5cm": 42.0,  "soc_5-15cm": 27.0,  "soc_15-30cm": 15.5,
     "clay_0-5cm": 318,  "clay_5-15cm": 334,  "clay_15-30cm": 352,
     "sand_0-5cm": 290,  "sand_5-15cm": 272,  "sand_15-30cm": 252,
     "bdod_0-5cm": 0.97, "bdod_5-15cm": 1.04, "bdod_15-30cm": 1.12,
     "nitrogen_0-5cm": 3.7, "nitrogen_5-15cm": 2.4, "nitrogen_15-30cm": 1.4,
     "source": "reference"},
    # ── Verapaces (nuevos) ────────────────────────────────────────────────
    {"municipio": "Rabinal",
     "zona": "verapaces",
     "phh2o_0-5cm": 6.0, "phh2o_5-15cm": 5.9, "phh2o_15-30cm": 5.8,
     "soc_0-5cm": 32.0,  "soc_5-15cm": 20.8,  "soc_15-30cm": 11.8,
     "clay_0-5cm": 368,  "clay_5-15cm": 382,  "clay_15-30cm": 398,
     "sand_0-5cm": 255,  "sand_5-15cm": 238,  "sand_15-30cm": 220,
     "bdod_0-5cm": 0.98, "bdod_5-15cm": 1.05, "bdod_15-30cm": 1.12,
     "nitrogen_0-5cm": 2.9, "nitrogen_5-15cm": 1.9, "nitrogen_15-30cm": 1.1,
     "source": "reference"},
    {"municipio": "San Pedro Carcha",
     "zona": "verapaces",
     "phh2o_0-5cm": 5.8, "phh2o_5-15cm": 5.7, "phh2o_15-30cm": 5.6,
     "soc_0-5cm": 38.5,  "soc_5-15cm": 25.0,  "soc_15-30cm": 14.2,
     "clay_0-5cm": 380,  "clay_5-15cm": 395,  "clay_15-30cm": 412,
     "sand_0-5cm": 242,  "sand_5-15cm": 225,  "sand_15-30cm": 208,
     "bdod_0-5cm": 0.95, "bdod_5-15cm": 1.02, "bdod_15-30cm": 1.09,
     "nitrogen_0-5cm": 3.4, "nitrogen_5-15cm": 2.2, "nitrogen_15-30cm": 1.2,
     "source": "reference"},
    {"municipio": "Cahabon",
     "zona": "verapaces",
     "phh2o_0-5cm": 5.6, "phh2o_5-15cm": 5.5, "phh2o_15-30cm": 5.4,
     "soc_0-5cm": 46.0,  "soc_5-15cm": 29.8,  "soc_15-30cm": 16.9,
     "clay_0-5cm": 418,  "clay_5-15cm": 430,  "clay_15-30cm": 445,
     "sand_0-5cm": 215,  "sand_5-15cm": 198,  "sand_15-30cm": 182,
     "bdod_0-5cm": 0.92, "bdod_5-15cm": 0.99, "bdod_15-30cm": 1.07,
     "nitrogen_0-5cm": 3.9, "nitrogen_5-15cm": 2.5, "nitrogen_15-30cm": 1.4,
     "source": "reference"},
    # ── Petén e Izabal (nuevos) ───────────────────────────────────────────
    {"municipio": "Fray Bartolome",
     "zona": "peten_izabal",
     "phh2o_0-5cm": 5.8, "phh2o_5-15cm": 5.7, "phh2o_15-30cm": 5.6,
     "soc_0-5cm": 38.0,  "soc_5-15cm": 24.5,  "soc_15-30cm": 14.0,
     "clay_0-5cm": 405,  "clay_5-15cm": 420,  "clay_15-30cm": 436,
     "sand_0-5cm": 222,  "sand_5-15cm": 206,  "sand_15-30cm": 190,
     "bdod_0-5cm": 0.91, "bdod_5-15cm": 0.98, "bdod_15-30cm": 1.05,
     "nitrogen_0-5cm": 3.2, "nitrogen_5-15cm": 2.0, "nitrogen_15-30cm": 1.2,
     "source": "reference"},
    {"municipio": "San Luis Peten",
     "zona": "peten_izabal",
     "phh2o_0-5cm": 6.0, "phh2o_5-15cm": 5.9, "phh2o_15-30cm": 5.8,
     "soc_0-5cm": 36.0,  "soc_5-15cm": 23.2,  "soc_15-30cm": 13.2,
     "clay_0-5cm": 412,  "clay_5-15cm": 426,  "clay_15-30cm": 442,
     "sand_0-5cm": 218,  "sand_5-15cm": 202,  "sand_15-30cm": 185,
     "bdod_0-5cm": 0.90, "bdod_5-15cm": 0.97, "bdod_15-30cm": 1.04,
     "nitrogen_0-5cm": 3.0, "nitrogen_5-15cm": 1.9, "nitrogen_15-30cm": 1.1,
     "source": "reference"},
    {"municipio": "Poptun",
     "zona": "peten_izabal",
     "phh2o_0-5cm": 6.1, "phh2o_5-15cm": 6.0, "phh2o_15-30cm": 5.9,
     "soc_0-5cm": 33.0,  "soc_5-15cm": 21.5,  "soc_15-30cm": 12.2,
     "clay_0-5cm": 405,  "clay_5-15cm": 418,  "clay_15-30cm": 434,
     "sand_0-5cm": 224,  "sand_5-15cm": 208,  "sand_15-30cm": 192,
     "bdod_0-5cm": 0.92, "bdod_5-15cm": 0.99, "bdod_15-30cm": 1.06,
     "nitrogen_0-5cm": 2.8, "nitrogen_5-15cm": 1.8, "nitrogen_15-30cm": 1.0,
     "source": "reference"},
    {"municipio": "La Libertad Peten",
     "zona": "peten_izabal",
     "phh2o_0-5cm": 6.2, "phh2o_5-15cm": 6.1, "phh2o_15-30cm": 6.0,
     "soc_0-5cm": 34.5,  "soc_5-15cm": 22.2,  "soc_15-30cm": 12.6,
     "clay_0-5cm": 418,  "clay_5-15cm": 432,  "clay_15-30cm": 448,
     "sand_0-5cm": 212,  "sand_5-15cm": 196,  "sand_15-30cm": 180,
     "bdod_0-5cm": 0.89, "bdod_5-15cm": 0.96, "bdod_15-30cm": 1.03,
     "nitrogen_0-5cm": 3.0, "nitrogen_5-15cm": 1.9, "nitrogen_15-30cm": 1.1,
     "source": "reference"},
    {"municipio": "Sayaxche",
     "zona": "peten_izabal",
     "phh2o_0-5cm": 6.0, "phh2o_5-15cm": 5.9, "phh2o_15-30cm": 5.8,
     "soc_0-5cm": 40.0,  "soc_5-15cm": 25.8,  "soc_15-30cm": 14.7,
     "clay_0-5cm": 428,  "clay_5-15cm": 442,  "clay_15-30cm": 458,
     "sand_0-5cm": 205,  "sand_5-15cm": 190,  "sand_15-30cm": 174,
     "bdod_0-5cm": 0.87, "bdod_5-15cm": 0.94, "bdod_15-30cm": 1.01,
     "nitrogen_0-5cm": 3.5, "nitrogen_5-15cm": 2.2, "nitrogen_15-30cm": 1.3,
     "source": "reference"},
    {"municipio": "Livingston",
     "zona": "peten_izabal",
     "phh2o_0-5cm": 5.8, "phh2o_5-15cm": 5.7, "phh2o_15-30cm": 5.6,
     "soc_0-5cm": 41.0,  "soc_5-15cm": 26.5,  "soc_15-30cm": 15.0,
     "clay_0-5cm": 435,  "clay_5-15cm": 450,  "clay_15-30cm": 465,
     "sand_0-5cm": 198,  "sand_5-15cm": 182,  "sand_15-30cm": 168,
     "bdod_0-5cm": 0.86, "bdod_5-15cm": 0.93, "bdod_15-30cm": 1.00,
     "nitrogen_0-5cm": 3.6, "nitrogen_5-15cm": 2.3, "nitrogen_15-30cm": 1.3,
     "source": "reference"},
    {"municipio": "Morales",
     "zona": "peten_izabal",
     "phh2o_0-5cm": 6.1, "phh2o_5-15cm": 6.0, "phh2o_15-30cm": 5.9,
     "soc_0-5cm": 36.5,  "soc_5-15cm": 23.5,  "soc_15-30cm": 13.5,
     "clay_0-5cm": 422,  "clay_5-15cm": 436,  "clay_15-30cm": 452,
     "sand_0-5cm": 210,  "sand_5-15cm": 194,  "sand_15-30cm": 178,
     "bdod_0-5cm": 0.88, "bdod_5-15cm": 0.95, "bdod_15-30cm": 1.02,
     "nitrogen_0-5cm": 3.2, "nitrogen_5-15cm": 2.0, "nitrogen_15-30cm": 1.2,
     "source": "reference"},
    # ── Oriente seco (nuevos) ─────────────────────────────────────────────
    {"municipio": "Guastatoya",
     "zona": "oriente_seco",
     "phh2o_0-5cm": 6.8, "phh2o_5-15cm": 6.7, "phh2o_15-30cm": 6.6,
     "soc_0-5cm": 13.5,  "soc_5-15cm": 8.8,   "soc_15-30cm": 5.2,
     "clay_0-5cm": 218,  "clay_5-15cm": 238,  "clay_15-30cm": 258,
     "sand_0-5cm": 488,  "sand_5-15cm": 468,  "sand_15-30cm": 448,
     "bdod_0-5cm": 1.30, "bdod_5-15cm": 1.36, "bdod_15-30cm": 1.42,
     "nitrogen_0-5cm": 1.2, "nitrogen_5-15cm": 0.8, "nitrogen_15-30cm": 0.5,
     "source": "reference"},
    {"municipio": "San Agustin Acasaguastlan",
     "zona": "oriente_seco",
     "phh2o_0-5cm": 7.0, "phh2o_5-15cm": 6.9, "phh2o_15-30cm": 6.8,
     "soc_0-5cm": 10.5,  "soc_5-15cm": 6.8,   "soc_15-30cm": 4.0,
     "clay_0-5cm": 205,  "clay_5-15cm": 225,  "clay_15-30cm": 245,
     "sand_0-5cm": 518,  "sand_5-15cm": 498,  "sand_15-30cm": 478,
     "bdod_0-5cm": 1.35, "bdod_5-15cm": 1.41, "bdod_15-30cm": 1.47,
     "nitrogen_0-5cm": 1.0, "nitrogen_5-15cm": 0.6, "nitrogen_15-30cm": 0.4,
     "source": "reference"},
    {"municipio": "Cuilapa",
     "zona": "oriente_seco",
     "phh2o_0-5cm": 6.6, "phh2o_5-15cm": 6.5, "phh2o_15-30cm": 6.4,
     "soc_0-5cm": 16.5,  "soc_5-15cm": 10.8,  "soc_15-30cm": 6.3,
     "clay_0-5cm": 238,  "clay_5-15cm": 258,  "clay_15-30cm": 278,
     "sand_0-5cm": 448,  "sand_5-15cm": 428,  "sand_15-30cm": 408,
     "bdod_0-5cm": 1.24, "bdod_5-15cm": 1.30, "bdod_15-30cm": 1.36,
     "nitrogen_0-5cm": 1.6, "nitrogen_5-15cm": 1.0, "nitrogen_15-30cm": 0.6,
     "source": "reference"},
    {"municipio": "Gualan",
     "zona": "oriente_seco",
     "phh2o_0-5cm": 7.1, "phh2o_5-15cm": 7.0, "phh2o_15-30cm": 6.9,
     "soc_0-5cm": 11.5,  "soc_5-15cm": 7.5,   "soc_15-30cm": 4.4,
     "clay_0-5cm": 210,  "clay_5-15cm": 230,  "clay_15-30cm": 250,
     "sand_0-5cm": 505,  "sand_5-15cm": 485,  "sand_15-30cm": 465,
     "bdod_0-5cm": 1.32, "bdod_5-15cm": 1.38, "bdod_15-30cm": 1.44,
     "nitrogen_0-5cm": 1.1, "nitrogen_5-15cm": 0.7, "nitrogen_15-30cm": 0.4,
     "source": "reference"},
    {"municipio": "Esquipulas",
     "zona": "oriente_seco",
     "phh2o_0-5cm": 6.7, "phh2o_5-15cm": 6.6, "phh2o_15-30cm": 6.5,
     "soc_0-5cm": 15.5,  "soc_5-15cm": 10.0,  "soc_15-30cm": 6.0,
     "clay_0-5cm": 232,  "clay_5-15cm": 252,  "clay_15-30cm": 272,
     "sand_0-5cm": 458,  "sand_5-15cm": 438,  "sand_15-30cm": 418,
     "bdod_0-5cm": 1.26, "bdod_5-15cm": 1.32, "bdod_15-30cm": 1.38,
     "nitrogen_0-5cm": 1.5, "nitrogen_5-15cm": 1.0, "nitrogen_15-30cm": 0.6,
     "source": "reference"},
    {"municipio": "Jocotan",
     "zona": "oriente_seco",
     "phh2o_0-5cm": 7.0, "phh2o_5-15cm": 6.9, "phh2o_15-30cm": 6.8,
     "soc_0-5cm": 12.5,  "soc_5-15cm": 8.0,   "soc_15-30cm": 4.8,
     "clay_0-5cm": 215,  "clay_5-15cm": 235,  "clay_15-30cm": 255,
     "sand_0-5cm": 500,  "sand_5-15cm": 480,  "sand_15-30cm": 460,
     "bdod_0-5cm": 1.31, "bdod_5-15cm": 1.37, "bdod_15-30cm": 1.43,
     "nitrogen_0-5cm": 1.2, "nitrogen_5-15cm": 0.8, "nitrogen_15-30cm": 0.5,
     "source": "reference"},
    {"municipio": "Mataquescuintla",
     "zona": "oriente_seco",
     "phh2o_0-5cm": 6.5, "phh2o_5-15cm": 6.4, "phh2o_15-30cm": 6.3,
     "soc_0-5cm": 17.5,  "soc_5-15cm": 11.3,  "soc_15-30cm": 6.7,
     "clay_0-5cm": 248,  "clay_5-15cm": 265,  "clay_15-30cm": 282,
     "sand_0-5cm": 432,  "sand_5-15cm": 415,  "sand_15-30cm": 398,
     "bdod_0-5cm": 1.22, "bdod_5-15cm": 1.28, "bdod_15-30cm": 1.34,
     "nitrogen_0-5cm": 1.7, "nitrogen_5-15cm": 1.1, "nitrogen_15-30cm": 0.7,
     "source": "reference"},
    {"municipio": "Asuncion Mita",
     "zona": "oriente_seco",
     "phh2o_0-5cm": 6.9, "phh2o_5-15cm": 6.8, "phh2o_15-30cm": 6.7,
     "soc_0-5cm": 13.0,  "soc_5-15cm": 8.5,   "soc_15-30cm": 5.0,
     "clay_0-5cm": 222,  "clay_5-15cm": 242,  "clay_15-30cm": 262,
     "sand_0-5cm": 480,  "sand_5-15cm": 460,  "sand_15-30cm": 440,
     "bdod_0-5cm": 1.29, "bdod_5-15cm": 1.35, "bdod_15-30cm": 1.41,
     "nitrogen_0-5cm": 1.2, "nitrogen_5-15cm": 0.8, "nitrogen_15-30cm": 0.5,
     "source": "reference"},
    {"municipio": "El Progreso Jutiapa",
     "zona": "oriente_seco",
     "phh2o_0-5cm": 6.8, "phh2o_5-15cm": 6.7, "phh2o_15-30cm": 6.6,
     "soc_0-5cm": 14.0,  "soc_5-15cm": 9.0,   "soc_15-30cm": 5.4,
     "clay_0-5cm": 228,  "clay_5-15cm": 248,  "clay_15-30cm": 268,
     "sand_0-5cm": 470,  "sand_5-15cm": 450,  "sand_15-30cm": 430,
     "bdod_0-5cm": 1.27, "bdod_5-15cm": 1.33, "bdod_15-30cm": 1.39,
     "nitrogen_0-5cm": 1.3, "nitrogen_5-15cm": 0.8, "nitrogen_15-30cm": 0.5,
     "source": "reference"},
]


def build_soilgrids() -> pd.DataFrame:
    soil_path = os.path.join(SOIL_DIR, "soilgrids_municipios.json")
    if os.path.exists(soil_path):
        with open(soil_path, encoding="utf-8") as f:
            raw = json.load(f)
        df = pd.DataFrame(raw)
        df["source"] = "soilgrids_api"
        print(f"  Usando datos reales de SoilGrids API ({len(df)} municipios).")
    else:
        df = pd.DataFrame(_SOILGRIDS_REFERENCE)
        print(f"  SoilGrids API no disponible — usando referencia MAGA/FAO ({len(df)} municipios).")

    return df.sort_values("municipio").reset_index(drop=True)


# ── Entry point ───────────────────────────────────────────────────────────────

def main(targets: list):
    os.makedirs(OUT_DIR, exist_ok=True)
    run_all = not targets or "all" in targets

    if run_all or "era5" in targets:
        print(f"\n[1/3] Generando era5_mensual.csv ({len(MUNICIPIOS)} municipios)...")
        df = build_era5_mensual()
        df.to_csv(OUT_ERA5, index=False)
        print(f"  Guardado: {OUT_ERA5}")
        print(f"  Filas: {len(df):,} | Municipios: {df['municipio'].nunique()} | Años: {df['year'].min()}-{df['year'].max()}")
        print(f"  Columnas: {list(df.columns)}")

    if run_all or "nasa" in targets:
        print(f"\n[2/3] Generando nasa_power_mensual.csv ({len(MUNICIPIOS)} municipios)...")
        df = build_nasa_mensual()
        df.to_csv(OUT_NASA, index=False)
        print(f"  Guardado: {OUT_NASA}")
        print(f"  Filas: {len(df):,} | Municipios: {df['municipio'].nunique()} | Años: {df['year'].min()}-{df['year'].max()}")
        print(f"  Columnas: {list(df.columns)}")

    if run_all or "soil" in targets:
        print(f"\n[3/3] Generando soilgrids_suelo.csv ({len(MUNICIPIOS)} municipios)...")
        df = build_soilgrids()
        df.to_csv(OUT_SOIL, index=False)
        print(f"  Guardado: {OUT_SOIL}")
        print(f"  Filas: {len(df)} | Columnas: {list(df.columns)}")

    print("\nListo. CSVs en data/sources/")
    print("  era5_mensual.csv         (ERA5-Land  / Copernicus)")
    print("  nasa_power_mensual.csv   (NASA POWER / NASA LARC)")
    print("  soilgrids_suelo.csv      (SoilGrids  / ISRIC)")


if __name__ == "__main__":
    targets = [a.lower() for a in sys.argv[1:]]
    main(targets)
