"""
Genera dataset de entrenamiento desde datos Open-Meteo descargados.

Mapeo de columnas Open-Meteo → features del modelo:
    t2m           → temperature      (°C)
    t2m_max       → temp_max         (°C)
    t2m_min       → temp_min         (°C)
    prectotcorr   → rainfall         (mm/mes)
    rh2m          → humidity         (%)
    soil_moisture → soil_moisture    (m³/m³)
    rad_sw        → light_lux        (MJ/m²/mes → lux via SOLAR_TO_LUX)

Campos derivados (sin fuente directa en Open-Meteo):
    swvl2     ≈ soil_moisture + 0.03  (humedad suelo 7-28 cm)
    swvl3     ≈ soil_moisture + 0.05  (humedad suelo 28-100 cm)
    soil_temp ≈ t2m − 3              (temperatura suelo 0-7 cm)
    soil_ph   → rango por zona (FAO/MAGA)
    greenness → función de soil_moisture + ruido

Input : data/raw/openmeteo/open_meteo_municipios.json
Output: data/datasets/dataset_openmeteo.csv

Uso:
    python generate_dataset_openmeteo.py          → genera CSV y lanza entrenamiento
    python generate_dataset_openmeteo.py nofit    → solo genera CSV
"""

import json
import os
import sys

import numpy as np
import pandas as pd

_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_SCRIPTS, "datasets"))
sys.path.insert(0, os.path.dirname(_SCRIPTS))

from crop_reference import build_dataframe as build_crop_ref

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OMJSON_PATH  = os.path.join(BASE_DIR, "data", "raw", "openmeteo", "open_meteo_municipios.json")
DATASETS_DIR = os.path.join(BASE_DIR, "data", "datasets")
OUT_DATASET  = os.path.join(DATASETS_DIR, "dataset_openmeteo.csv")

RNG = np.random.default_rng(42)

# Open-Meteo rad_sw está en MJ/m²/mes → MJ/m²/día ÷ 30 → lux
# Misma constante que generate_dataset_v2.py (1 MJ/m²/día ≈ 2800 lux)
SOLAR_TO_LUX    = 2_800
SAMPLES_PER_REC = 2   # variantes por registro climático

# ── Zona ecológica por municipio ──────────────────────────────────────────────

MUNICIPIO_ZONA = {
    # Altiplano central
    "Guatemala":                 "altiplano_central",
    "Mixco":                     "altiplano_central",
    "Villa Nueva":               "altiplano_central",
    "San Jose Pinula":           "altiplano_central",
    "Sacatepequez":              "altiplano_central",
    "San Lucas Sacatepequez":    "altiplano_central",
    "Chimaltenango":             "altiplano_central",
    "Patzun":                    "altiplano_central",
    "Tecpan":                    "altiplano_central",
    "Salama":                    "altiplano_central",
    "Rabinal":                   "altiplano_central",
    # Altiplano occidente
    "Solola":                    "altiplano_occidente",
    "Santiago Atitlan":          "altiplano_occidente",
    "Totonicapan":               "altiplano_occidente",
    "Quetzaltenango":            "altiplano_occidente",
    "San Juan Ostuncalco":       "altiplano_occidente",
    "San Marcos":                "altiplano_occidente",
    "Santa Cruz del Quiche":     "altiplano_occidente",
    "Chichicastenango":          "altiplano_occidente",
    # Boca costa / transición
    "Coatepeque":                "boca_costa",
    "Malacatan":                 "boca_costa",
    "Ayutla":                    "boca_costa",
    "Mazatenango":               "boca_costa",
    "Chicacao":                  "boca_costa",
    "Patulul":                   "boca_costa",
    # Costa sur
    "Escuintla":                 "costa_sur",
    "Tiquisate":                 "costa_sur",
    "Santa Lucia Cotzumalguapa": "costa_sur",
    "Cuilapa":                   "costa_sur",
    "Taxisco":                   "costa_sur",
    "Retalhuleu":                "costa_sur",
    "Champerico":                "costa_sur",
    # Oriente seco
    "Guastatoya":                "oriente_seco",
    "San Agustin Acasaguastlan": "oriente_seco",
    "Zacapa":                    "oriente_seco",
    "Gualan":                    "oriente_seco",
    "Chiquimula":                "oriente_seco",
    "Esquipulas":                "oriente_seco",
    "Jocotan":                   "oriente_seco",
    "Jalapa":                    "oriente_seco",
    "Mataquescuintla":           "oriente_seco",
    "Jutiapa":                   "oriente_seco",
    "Asuncion Mita":             "oriente_seco",
    "El Progreso Jutiapa":       "oriente_seco",
    # Verapaces
    "Coban":                     "verapaces",
    "San Pedro Carcha":          "verapaces",
    "Cahabon":                   "verapaces",
    "Fray Bartolome":            "verapaces",
    "Ixcan":                     "verapaces",
    # Petén / Izabal
    "Flores":                    "peten_izabal",
    "San Luis Peten":            "peten_izabal",
    "Poptun":                    "peten_izabal",
    "La Libertad Peten":         "peten_izabal",
    "Sayaxche":                  "peten_izabal",
    "Puerto Barrios":            "peten_izabal",
    "Livingston":                "peten_izabal",
    "Morales":                   "peten_izabal",
    # Noroccidente
    "Huehuetenango":             "noroccidente",
    "Jacaltenango":              "noroccidente",
    "Barillas":                  "noroccidente",
    "Nenton":                    "noroccidente",
}

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

# Luz por mes como fallback si rad_sw es nulo
LUX_BY_MONTH = {
    1: 38000, 2: 42000, 3: 44000, 4: 40000,
    5: 28000, 6: 22000, 7: 26000, 8: 24000,
    9: 22000, 10: 24000, 11: 32000, 12: 36000,
}


# ── Función de rendimiento (idéntica a generate_dataset_v2.py) ────────────────

def _score(value: float, opt_min: float, opt_max: float, slope: float = 0.04) -> float:
    if opt_min <= value <= opt_max:
        return 1.0
    dist = min(abs(value - opt_min), abs(value - opt_max))
    return max(0.0, 1.0 - slope * dist)


def compute_yield(row: dict, p: dict) -> float:
    s_t     = _score(row["temperature"],   p["temp_min"],     p["temp_max"],   0.07)
    s_r     = _score(row["rainfall"],      p["rain_min"],     p["rain_max"],   0.02)
    s_h     = _score(row["humidity"],      p["humidity_min"], p["humidity_max"], 0.05)
    s_ph    = _score(row["soil_ph"],       p["ph_min"],       p["ph_max"],     0.30)
    s_sm    = _score(row["soil_moisture"], p["sm_min"],       p["sm_max"],     2.50)
    s_lux   = _score(row["light_lux"],     p["light_min"],    p["light_max"],  0.00005)
    s_green = _score(row["greenness_idx"], p["green_min"],    p["green_max"],  0.08)
    s_stl1  = _score(row["soil_temp"],     p["stl1_min"],     p["stl1_max"],   0.07)
    s_swvl2 = _score(row["swvl2"],         p["swvl2_min"],    p["swvl2_max"],  2.50)
    s_swvl3 = _score(row["swvl3"],         p["swvl3_min"],    p["swvl3_max"],  2.00)

    base = (s_t*0.18 + s_r*0.18 + s_h*0.12 + s_ph*0.15 +
            s_sm*0.10 + s_lux*0.08 + s_green*0.05 +
            s_stl1*0.07 + s_swvl2*0.05 + s_swvl3*0.02) * 100
    return float(np.clip(base + RNG.normal(0, 6), 5, 100))


# ── Pipeline ──────────────────────────────────────────────────────────────────

def build() -> pd.DataFrame:
    print("=== Generando dataset desde Open-Meteo ===\n")

    if not os.path.exists(OMJSON_PATH):
        raise FileNotFoundError(f"No se encontró: {OMJSON_PATH}")

    with open(OMJSON_PATH, encoding="utf-8") as f:
        raw = json.load(f)

    # Aplanar lista de registros
    climate_records = [rec for entry in raw for rec in entry["records"]]
    climate_df      = pd.DataFrame(climate_records)

    n_mun   = climate_df["municipio"].nunique()
    n_years = climate_df["year"].nunique()
    print(f"Registros climaticos : {len(climate_df)}")
    print(f"Municipios           : {n_mun}")
    print(f"Años cubiertos       : {climate_df['year'].min()} – {climate_df['year'].max()} ({n_years} años)")

    ref_df      = build_crop_ref()
    crop_params = {r["crop"]: r.to_dict() for _, r in ref_df.iterrows()}
    crops       = list(crop_params.keys())
    print(f"Cultivos             : {len(crops)}")
    print(f"Filas estimadas      : {len(climate_df)} × {len(crops)} × {SAMPLES_PER_REC} = "
          f"{len(climate_df) * len(crops) * SAMPLES_PER_REC:,}\n")

    rows = []
    total = len(climate_df)

    for idx, clim in climate_df.iterrows():
        if idx % 2000 == 0:
            pct = idx / total * 100
            print(f"  Progreso: {idx}/{total} ({pct:.0f}%)...", end="\r")

        municipio = clim["municipio"]
        month     = int(clim["month"])
        zona      = MUNICIPIO_ZONA.get(municipio, "altiplano_central")
        ph_lo, ph_hi = _PH_RANGES_ZONA[zona]

        # rad_sw: MJ/m²/mes → MJ/m²/día → lux
        if pd.notna(clim.get("rad_sw")) and float(clim["rad_sw"]) > 0:
            lux_base = (float(clim["rad_sw"]) / 30.0) * SOLAR_TO_LUX
        else:
            lux_base = LUX_BY_MONTH[month]

        sm = float(clim["soil_moisture"])

        for crop in crops:
            for _ in range(SAMPLES_PER_REC):
                soil_ph   = round(float(RNG.uniform(ph_lo, ph_hi)), 2)
                lux_noise = float(RNG.uniform(0.80, 1.20))
                light_lux = round(float(np.clip(lux_base * lux_noise, 500, 120_000)), 0)
                sm_norm   = float(np.clip((sm - 0.10) / 0.40, 0.0, 1.0))
                greenness = round(float(np.clip(35 + sm_norm * 40 + RNG.normal(0, 7), 10, 95)), 1)

                # Capas profundas de suelo estimadas
                swvl2 = round(float(np.clip(sm + 0.03 + RNG.uniform(-0.01, 0.02), 0.05, 0.60)), 4)
                swvl3 = round(float(np.clip(sm + 0.05 + RNG.uniform(-0.01, 0.02), 0.05, 0.60)), 4)
                soil_temp = round(float(clim["t2m"]) - 3.0 + float(RNG.normal(0, 0.5)), 2)

                row = {
                    "municipio":     municipio,
                    "altitud_m":     clim.get("altitud_m"),
                    "crop":          crop,
                    "month":         month,
                    "year":          int(clim["year"]),
                    "temperature":   round(float(clim["t2m"]), 2),
                    "rainfall":      round(float(clim["prectotcorr"]), 1),
                    "humidity":      round(float(clim["rh2m"]), 1),
                    "soil_moisture": round(sm, 4),
                    "swvl2":         swvl2,
                    "swvl3":         swvl3,
                    "soil_temp":     soil_temp,
                    "soil_ph":       soil_ph,
                    "light_lux":     light_lux,
                    "greenness_idx": greenness,
                    "temp_max":      round(float(clim["t2m_max"]), 2),
                    "temp_min":      round(float(clim["t2m_min"]), 2),
                }
                row["yield_pct"] = round(compute_yield(row, crop_params[crop]), 1)
                rows.append(row)

    print()  # newline after progress
    df = pd.DataFrame(rows)

    print(f"\nDataset generado:")
    print(f"  Filas         : {len(df):,}")
    print(f"  Municipios    : {df['municipio'].nunique()}")
    print(f"  Cultivos      : {df['crop'].nunique()}")
    print(f"  Años          : {df['year'].min()} – {df['year'].max()}")
    print(f"  yield_pct     : {df['yield_pct'].mean():.1f}% promedio "
          f"(min={df['yield_pct'].min():.1f}%, max={df['yield_pct'].max():.1f}%)")

    os.makedirs(DATASETS_DIR, exist_ok=True)
    df.to_csv(OUT_DATASET, index=False)
    print(f"\nGuardado en: {OUT_DATASET}")
    return df


if __name__ == "__main__":
    df = build()

    nofit = len(sys.argv) > 1 and sys.argv[1] == "nofit"
    if nofit:
        print("\nModo nofit: solo se generó el CSV.")
        sys.exit(0)

    print("\n=== Iniciando reentrenamiento XGBoost ===")
    train_script = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "training", "model_xgboost.py",
    )
    os.execv(sys.executable, [sys.executable, train_script, "train"])
