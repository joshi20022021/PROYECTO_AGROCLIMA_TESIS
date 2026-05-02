"""
Genera el dataset de entrenamiento cargando los 3 CSVs fuente.

Requiere (ejecutar build_source_csvs.py primero):
    data/sources/era5_mensual.csv          → clima mensual ERA5 2010-2026
    data/sources/nasa_power_mensual.csv    → NASA POWER 2010-2024
    data/sources/soilgrids_suelo.csv       → propiedades suelo por municipio

Mejoras sobre generate_dataset_era5.py:
    ✓ solar_radiation (NASA POWER) reemplaza light_lux sintético
    ✓ phh2o de SoilGrids reemplaza pH aleatorio (cuando está disponible)
    ✓ nasa_temp_max / nasa_temp_min → features de estrés térmico
    ✓ wind_speed_2m → feature de evapotranspiración
    ✓ 585 × 37 cultivos × 3 muestras = 64 935 filas (igual base, mejor calidad)

Uso:
    python generate_dataset_v2.py          → genera y entrena automáticamente
    python generate_dataset_v2.py nofit    → solo genera el CSV, no entrena

Salida: data/datasets/dataset_v2.csv
"""

import os
import sys
import pathlib
_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_SCRIPTS, "datasets"))
sys.path.insert(0, os.path.dirname(_SCRIPTS))
import sys

import numpy as np
import pandas as pd

from crop_reference import build_dataframe as build_crop_ref
from database.connection import db_available
from database.repository import replace_dataset_rows, upsert_dataset_registered

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCES_DIR  = os.path.join(BASE_DIR, "data", "sources")
DATASETS_DIR = os.path.join(BASE_DIR, "data", "datasets")

IN_ERA5      = os.path.join(SOURCES_DIR,  "era5_mensual.csv")
IN_NASA      = os.path.join(SOURCES_DIR,  "nasa_power_mensual.csv")
IN_SOIL      = os.path.join(SOURCES_DIR,  "soilgrids_suelo.csv")
OUT_DATASET  = os.path.join(DATASETS_DIR, "dataset_v2.csv")

RNG = np.random.default_rng(42)
SAMPLES_PER_RECORD = 3

# NASA POWER solar_radiation está en MJ/m²/día (rango Guatemala: 15-23 MJ/m²/día)
# Conversión: MJ/m²/día → lux representativo de luz diurna
#   1 MJ/m²/día ÷ (12 h × 3600 s) = 23.1 W/m² promedio diurno
#   23.1 W/m² × 120 lux/(W/m²) ≈ 2775 lux por MJ/m²/día
#   Resultado: 15 MJ → ~42 000 lux | 23 MJ → ~64 000 lux
SOLAR_TO_LUX = 2_800

# Lux fallback si NASA POWER no cubre ese año/mes
LUX_BY_MONTH = {
    1: 38000, 2: 42000, 3: 44000, 4: 40000,
    5: 28000, 6: 22000, 7: 26000, 8: 24000,
    9: 22000, 10: 24000, 11: 32000, 12: 36000,
}


# ── Carga y fusión de CSVs ────────────────────────────────────────────────────

def load_sources() -> pd.DataFrame:
    """
    Carga los 3 CSVs y los fusiona en un único DataFrame mensual por municipio.
    """
    # ── ERA5 (obligatorio)
    if not os.path.exists(IN_ERA5):
        raise FileNotFoundError(
            f"No se encontró {IN_ERA5}\n"
            "Ejecuta primero: python build_source_csvs.py era5"
        )
    era5 = pd.read_csv(IN_ERA5)
    print(f"  ERA5 cargado       : {len(era5)} registros")

    # ── NASA POWER (opcional — si no existe se omite sin error)
    if os.path.exists(IN_NASA):
        nasa = pd.read_csv(IN_NASA)
        print(f"  NASA POWER cargado : {len(nasa)} registros")
        era5 = era5.merge(
            nasa[["municipio","year","month",
                  "solar_radiation","solar_clear_sky",
                  "nasa_temp_max","nasa_temp_min",
                  "wind_speed_2m","nasa_humidity","nasa_rainfall"]],
            on=["municipio","year","month"],
            how="left",
        )
        n_solar = era5["solar_radiation"].notna().sum()
        print(f"  Solar radiation unida: {n_solar}/{len(era5)} registros")
    else:
        print("  NASA POWER no disponible — usando light_lux estimado")
        era5["solar_radiation"] = None
        era5["nasa_temp_max"]   = None
        era5["nasa_temp_min"]   = None
        era5["wind_speed_2m"]   = None

    # ── SoilGrids (opcional — si no existe se usan rangos de referencia del CSV)
    if os.path.exists(IN_SOIL):
        soil = pd.read_csv(IN_SOIL)[["municipio","phh2o_0-5cm","soc_0-5cm",
                                      "clay_0-5cm","sand_0-5cm","nitrogen_0-5cm"]]
        soil = soil.rename(columns={
            "phh2o_0-5cm":    "real_ph",
            "soc_0-5cm":      "org_carbon",
            "clay_0-5cm":     "clay",
            "sand_0-5cm":     "sand",
            "nitrogen_0-5cm": "nitrogen",
        })
        era5 = era5.merge(soil, on="municipio", how="left")
        n_ph = era5["real_ph"].notna().sum()
        src  = soil.get("source", pd.Series(["?"]))[0] if "source" in soil.columns else "csv"
        print(f"  SoilGrids cargado  : pH real disponible para {n_ph}/{len(era5)} registros ({src})")
    else:
        print("  SoilGrids no disponible — usando pH estimado por municipio")
        era5["real_ph"] = None

    return era5


# ── Función de rendimiento ────────────────────────────────────────────────────

def _score(value: float, opt_min: float, opt_max: float, slope: float = 0.04) -> float:
    if opt_min <= value <= opt_max:
        return 1.0
    dist = min(abs(value - opt_min), abs(value - opt_max))
    return max(0.0, 1.0 - slope * dist)


def compute_yield(row: dict, p: dict) -> float:
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
    return float(np.clip(base + RNG.normal(0, 6), 5, 100))


# ── Pipeline ─────────────────────────────────────────────────────────────────

# Rangos de pH por zona como fallback si SoilGrids no tiene el municipio
_PH_RANGES_ZONA = {
    "altiplano_central":   (5.5, 6.8),
    "altiplano_occidente": (5.2, 6.4),
    "boca_costa":          (5.2, 6.3),
    "costa_sur":           (5.8, 7.0),
    "oriente_seco":        (6.2, 7.5),
    "verapaces":           (5.2, 6.5),
    "peten_izabal":        (5.4, 6.8),
    "noroccidente":        (5.0, 6.2),
}


def build_dataset() -> pd.DataFrame:
    print("Cargando fuentes de datos...")
    climate = load_sources()

    print(f"\nCargando referencia de cultivos...")
    ref_df      = build_crop_ref()
    crop_params = {row["crop"]: row.to_dict() for _, row in ref_df.iterrows()}
    crops       = list(crop_params.keys())
    print(f"  {len(crops)} cultivos cargados")

    has_solar    = "solar_radiation" in climate.columns and climate["solar_radiation"].notna().any()
    has_real_ph  = "real_ph"         in climate.columns and climate["real_ph"].notna().any()
    has_temp_max = "nasa_temp_max"   in climate.columns and climate["nasa_temp_max"].notna().any()
    has_wind     = "wind_speed_2m"   in climate.columns and climate["wind_speed_2m"].notna().any()

    print(f"\nFeatures activas:")
    print(f"  solar_radiation (NASA POWER) : {'SI — reemplaza light_lux sintético' if has_solar else 'NO — usando estimacion mensual'}")
    print(f"  pH real (SoilGrids)          : {'SI' if has_real_ph else 'NO — usando rango aleatorio por municipio'}")
    print(f"  nasa_temp_max/min            : {'SI' if has_temp_max else 'NO'}")
    print(f"  wind_speed_2m                : {'SI' if has_wind else 'NO'}")

    print(f"\nGenerando dataset ({len(climate)} climas × {len(crops)} cultivos × {SAMPLES_PER_RECORD} muestras)...")
    rows = []

    for _, clim in climate.iterrows():
        municipio = clim["municipio"]
        month     = int(clim["month"])
        zona      = clim.get("zona", "altiplano_central") or "altiplano_central"
        ph_range  = _PH_RANGES_ZONA.get(zona, (5.5, 7.0))

        # pH: real de SoilGrids si está disponible, si no fallback por zona
        if has_real_ph and not pd.isna(clim.get("real_ph")):
            ph_center = float(clim["real_ph"])
            ph_lo = max(4.0, ph_center - 0.4)
            ph_hi = min(8.5, ph_center + 0.4)
        else:
            ph_lo, ph_hi = ph_range

        # Luz solar: de NASA POWER o estimada por mes
        if has_solar and not pd.isna(clim.get("solar_radiation")):
            lux_base = float(clim["solar_radiation"]) * SOLAR_TO_LUX
        else:
            lux_base = LUX_BY_MONTH[month]

        for crop in crops:
            for _ in range(SAMPLES_PER_RECORD):
                soil_ph = round(float(RNG.uniform(ph_lo, ph_hi)), 2)

                lux_noise  = RNG.uniform(0.75, 1.25)
                light_lux  = round(float(np.clip(lux_base * lux_noise, 500, 120_000)), 0)

                sm_norm   = np.clip((clim["soil_moisture"] - 0.10) / 0.40, 0, 1)
                greenness = round(float(np.clip(35 + sm_norm * 40 + RNG.normal(0, 7), 10, 95)), 1)

                row = {
                    "municipio":     municipio,
                    "crop":          crop,
                    "month":         month,
                    "year":          int(clim["year"]),
                    # ERA5 base
                    "temperature":   clim["temperature"],
                    "rainfall":      clim["rainfall"],
                    "humidity":      clim["humidity"],
                    "soil_moisture": clim["soil_moisture"],
                    # ERA5 extra soil
                    "swvl2":         float(clim["swvl2"]),
                    "swvl3":         float(clim["swvl3"]),
                    "soil_temp":     float(clim["soil_temp"]),
                    # Estimadas / SoilGrids
                    "soil_ph":       soil_ph,
                    "light_lux":     light_lux,
                    "greenness_idx": greenness,
                }

                # Features extra de NASA POWER si están disponibles
                if has_temp_max and not pd.isna(clim.get("nasa_temp_max")):
                    row["temp_max"] = float(clim["nasa_temp_max"])
                    row["temp_min"] = float(clim["nasa_temp_min"])
                if has_wind and not pd.isna(clim.get("wind_speed_2m")):
                    row["wind_speed"] = float(clim["wind_speed_2m"])

                row["yield_pct"] = round(compute_yield(row, crop_params[crop]), 1)
                rows.append(row)

    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    return df


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(DATASETS_DIR, exist_ok=True)

    df = build_dataset()
    df.to_csv(OUT_DATASET, index=False)

    if db_available():
        replace_dataset_rows("dataset_v2.csv", df)
        upsert_dataset_registered(
            filename="dataset_v2.csv",
            tipo="entrenamiento",
            origen="backend/data/datasets",
            periodo=f"{int(df['year'].min())}-{int(df['year'].max())}" if "year" in df.columns else None,
            total_filas=len(df),
            total_columnas=len(df.columns),
            columnas=list(df.columns),
            metadata={"path": str(pathlib.Path(OUT_DATASET).relative_to(BASE_DIR))},
            activo=True,
        )
        print("Dataset sincronizado en PostgreSQL.")

    print(f"\nDataset guardado : {OUT_DATASET}")
    print(f"Total filas      : {len(df):,}")
    print(f"Columnas ({len(df.columns)}): {list(df.columns)}")
    print(f"Cultivos únicos  : {df['crop'].nunique()}")
    print()
    print("Rendimiento promedio por cultivo (top 10):")
    print(df.groupby("crop")["yield_pct"].mean().sort_values(ascending=False).head(10).round(1).to_string())
    print()
    print("Promedios por municipio:")
    cols = ["temperature","rainfall","humidity","soil_moisture","soil_temp","light_lux"]
    print(df.groupby("municipio")[cols].mean().round(2).to_string())

    # Entrenar automáticamente salvo que se pase "nofit"
    if "nofit" not in [a.lower() for a in sys.argv[1:]]:
        print("\n" + "="*55)
        print("Entrenando modelo XGBoost con dataset_v2...")
        print("="*55)
        import importlib.util

        model_path = pathlib.Path(__file__).parent.parent / "training" / "model_xgboost.py"
        spec = importlib.util.spec_from_file_location("model_xgboost", model_path)
        mx   = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mx)

        # Ajustar rutas del módulo para apuntar al nuevo dataset
        mx.DATASET_PATH = OUT_DATASET
        mx.cmd_train()
