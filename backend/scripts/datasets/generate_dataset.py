"""
Genera dataset sintético para entrenamiento del modelo XGBoost.
Incluye métricas de los sensores físicos del proyecto:
    - DS18B20              → temperature (°C)
    - TSL2561              → light_lux (lux)
    - TCS3200              → greenness_idx (%)
    - Higrómetro capacitivo → soil_moisture (0.0-1.0)

Salida: data/processed/dataset_preliminar.csv
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from crop_reference import build_dataframe as build_crop_ref

RNG = np.random.default_rng(42)

MUNICIPIO_CLIMATE = {
    "Chimaltenango": dict(t=(14, 24), r=(20, 160), h=(60, 88), sm=(0.20, 0.42), lux=(8000,  45000)),
    "Sacatepequez":  dict(t=(14, 23), r=(15, 150), h=(62, 86), sm=(0.18, 0.40), lux=(8000,  42000)),
    "Guatemala":     dict(t=(17, 28), r=(10, 120), h=(50, 82), sm=(0.15, 0.38), lux=(10000, 55000)),
}

MUNICIPIOS = list(MUNICIPIO_CLIMATE.keys())
N_SAMPLES  = 6000


def _score(value: float, opt_min: float, opt_max: float, slope: float = 0.04) -> float:
    if opt_min <= value <= opt_max:
        return 1.0
    dist = min(abs(value - opt_min), abs(value - opt_max))
    return max(0.0, 1.0 - slope * dist)


def compute_yield(row: dict, crop_params: dict) -> float:
    p = crop_params[row["crop"]]
    s_t     = _score(row["temperature"],  p["temp_min"],   p["temp_max"],   slope=0.07)
    s_r     = _score(row["rainfall"],     p["rain_min"],   p["rain_max"],   slope=0.02)
    s_h     = _score(row["humidity"],     p["humidity_min"], p["humidity_max"], slope=0.05)
    s_ph    = _score(row["soil_ph"],      p["ph_min"],     p["ph_max"],     slope=0.30)
    s_sm    = _score(row["soil_moisture"],p["sm_min"],     p["sm_max"],     slope=2.50)
    s_lux   = _score(row["light_lux"],    p["light_min"],  p["light_max"],  slope=0.00005)
    s_green = _score(row["greenness_idx"],p["green_min"],  p["green_max"],  slope=0.08)

    base  = (s_t*0.20 + s_r*0.20 + s_h*0.15 + s_ph*0.18 + s_sm*0.12 + s_lux*0.10 + s_green*0.05) * 100
    noise = RNG.normal(0, 7)
    return float(np.clip(base + noise, 5, 100))


def generate(n: int = N_SAMPLES) -> pd.DataFrame:
    ref_df = build_crop_ref()
    crop_params = {row["crop"]: row.to_dict() for _, row in ref_df.iterrows()}
    crops = list(crop_params.keys())

    rows = []
    for _ in range(n):
        municipio = RNG.choice(MUNICIPIOS)
        crop      = RNG.choice(crops)
        climate   = MUNICIPIO_CLIMATE[municipio]
        month     = int(RNG.integers(1, 13))

        rain_factor = 1.6 if 5 <= month <= 10 else 0.5
        # Más luz en temporada seca (nov-abril)
        lux_factor  = 1.2 if month not in range(5, 11) else 0.8

        temperature   = float(RNG.uniform(*climate["t"]))
        rainfall      = float(np.clip(RNG.uniform(*climate["r"]) * rain_factor, 5, 260))
        humidity      = float(RNG.uniform(*climate["h"]))
        soil_ph       = float(RNG.uniform(4.5, 7.8))
        soil_moisture = float(RNG.uniform(*climate["sm"]))
        light_lux     = float(np.clip(RNG.uniform(*climate["lux"]) * lux_factor, 500, 80000))
        # Verdor correlaciona con condiciones favorables + ruido
        base_green    = 45 + (soil_moisture - climate["sm"][0]) / (climate["sm"][1] - climate["sm"][0]) * 35
        greenness_idx = float(np.clip(base_green + RNG.normal(0, 8), 10, 95))

        row = dict(
            municipio     = municipio,
            crop          = crop,
            month         = month,
            temperature   = round(temperature,   1),
            rainfall      = round(rainfall,      1),
            humidity      = round(humidity,      1),
            soil_ph       = round(soil_ph,       2),
            soil_moisture = round(soil_moisture, 3),
            light_lux     = round(light_lux,     0),
            greenness_idx = round(greenness_idx, 1),
        )
        row["yield_pct"] = round(compute_yield(row, crop_params), 1)
        rows.append(row)

    return pd.DataFrame(rows)


if __name__ == "__main__":
    out_dir  = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "processed")
    out_path = os.path.join(out_dir, "dataset_preliminar.csv")
    os.makedirs(out_dir, exist_ok=True)

    df = generate(N_SAMPLES)
    df.to_csv(out_path, index=False)

    print(f"Dataset generado : {out_path}")
    print(f"Filas            : {len(df)}")
    print(f"Columnas         : {list(df.columns)}")
    print(f"Cultivos unicos  : {df['crop'].nunique()}")
    print()
    print("Rendimiento promedio por cultivo (top 10):")
    print(df.groupby("crop")["yield_pct"].mean().sort_values(ascending=False).head(10).round(1).to_string())
