#!/usr/bin/env python3
"""
import_csv_to_db.py — Importa los archivos CSV/JSON de datos reales a la DB.

Qué importa y por qué:
  era5_mensual.csv      → metricas_climaticas  (reemplaza promedios aproximados con datos ERA5 reales)
  sowing_calendar.csv   → calendario_siembra   (calendario óptimo de siembra por municipio/cultivo)
  water_stress_index.csv→ indice_estres_hidrico (índice mensual de estrés hídrico 2010-2024)

Qué NO importa (y por qué):
  dataset_v2.csv / dataset_openmeteo.csv  → 1-2M filas, solo para entrenamiento ML
  recommendations.csv                     → ya está en recomendaciones_cultivo (243 filas)
  latest_metrics.json                     → solo tenía 3 municipios con totales anuales (obsoleto)
  drift_profile.json / isolation_forest_* → artefactos ML, los lee ml_insights.py directamente
  model_comparison.json                   → lo lee el endpoint admin como archivo

Uso:
    python scripts/import_csv_to_db.py           # importa todo
    python scripts/import_csv_to_db.py --reset   # limpia y re-importa
    python scripts/import_csv_to_db.py era5      # solo métricas ERA5
    python scripts/import_csv_to_db.py sowing    # solo calendario de siembra
    python scripts/import_csv_to_db.py stress    # solo estrés hídrico
"""

import os
import sys

import pandas as pd
from psycopg2.extras import execute_values

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.connection import db_available, get_cursor

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
ERA5_PATH    = os.path.join(BASE_DIR, "data", "sources", "era5_mensual.csv")
SOWING_PATH  = os.path.join(BASE_DIR, "data", "processed", "sowing_calendar.csv")
STRESS_PATH  = os.path.join(BASE_DIR, "data", "processed", "water_stress_index.csv")


# ---------------------------------------------------------------------------
# ERA5 → metricas_climaticas
# ---------------------------------------------------------------------------

def import_era5(cur, reset):
    if not os.path.exists(ERA5_PATH):
        print("  [SKIP] era5_mensual.csv no encontrado.")
        return

    df = pd.read_csv(ERA5_PATH)
    required = {"municipio", "temperature", "rainfall", "humidity", "soil_moisture"}
    if not required.issubset(df.columns):
        print(f"  [ERROR] era5_mensual.csv no tiene las columnas esperadas: {required}")
        return

    # Promedio de todos los años/meses disponibles por municipio
    avg = (
        df.groupby("municipio")[["temperature", "rainfall", "humidity", "soil_moisture"]]
        .mean()
        .round(3)
        .reset_index()
    )
    # Descartar filas con NaN en columnas clave
    avg = avg.dropna(subset=["temperature", "rainfall", "humidity"])

    if reset:
        cur.execute("DELETE FROM metricas_climaticas WHERE fuente = 'ERA5-Land'")
        print(f"  metricas_climaticas: tabla limpiada (ERA5-Land).")

    rows = 0
    for _, row in avg.iterrows():
        cur.execute(
            """INSERT INTO metricas_climaticas
               (municipio, temperatura, precipitacion, humedad, soil_moisture, fuente, periodo)
               VALUES (%s, %s, %s, %s, %s, 'ERA5-Land', '2010-2026')
               ON CONFLICT (municipio, fuente, periodo) DO UPDATE SET
                   temperatura   = EXCLUDED.temperatura,
                   precipitacion = EXCLUDED.precipitacion,
                   humedad       = EXCLUDED.humedad,
                   soil_moisture = EXCLUDED.soil_moisture,
                   fecha_carga   = NOW()""",
            (
                row["municipio"],
                row["temperature"],
                row["rainfall"],
                row["humidity"],
                row.get("soil_moisture"),
            ),
        )
        rows += 1

    print(f"  metricas_climaticas: {rows} municipios importados desde era5_mensual.csv (promedio 2010-2026).")


# ---------------------------------------------------------------------------
# sowing_calendar.csv → calendario_siembra
# ---------------------------------------------------------------------------

def import_sowing(cur, reset):
    if not os.path.exists(SOWING_PATH):
        print("  [SKIP] sowing_calendar.csv no encontrado.")
        return

    df = pd.read_csv(SOWING_PATH)
    required = {"municipio", "crop", "month"}
    if not required.issubset(df.columns):
        print(f"  [ERROR] sowing_calendar.csv no tiene las columnas esperadas: {required}")
        return

    if reset:
        cur.execute("DELETE FROM calendario_siembra")

    col_map = {
        "municipio":       "municipio",
        "crop":            "cultivo",
        "month":           "mes",
        "rank":            "rank",
        "is_top3":         "is_top3",
        "mean_yield":      "mean_yield",
        "std_yield":       "std_yield",
        "high_yield_rate": "high_yield_rate",
        "n_samples":       "n_samples",
        "score":           "score",
        "recommendation":  "recommendation",
    }

    rows_data = []
    for _, row in df.iterrows():
        rows_data.append((
            row.get("municipio"),
            row.get("crop"),
            int(row.get("month", 0)),
            int(row["rank"]) if "rank" in df.columns and pd.notna(row.get("rank")) else None,
            bool(row["is_top3"]) if "is_top3" in df.columns and pd.notna(row.get("is_top3")) else None,
            float(row["mean_yield"]) if "mean_yield" in df.columns and pd.notna(row.get("mean_yield")) else None,
            float(row["std_yield"]) if "std_yield" in df.columns and pd.notna(row.get("std_yield")) else None,
            float(row["high_yield_rate"]) if "high_yield_rate" in df.columns and pd.notna(row.get("high_yield_rate")) else None,
            int(row["n_samples"]) if "n_samples" in df.columns and pd.notna(row.get("n_samples")) else None,
            float(row["score"]) if "score" in df.columns and pd.notna(row.get("score")) else None,
            str(row["recommendation"]) if "recommendation" in df.columns and pd.notna(row.get("recommendation")) else None,
        ))

    execute_values(
        cur,
        """INSERT INTO calendario_siembra
           (municipio, cultivo, mes, rank, is_top3, mean_yield, std_yield,
            high_yield_rate, n_samples, score, recommendation)
           VALUES %s
           ON CONFLICT (municipio, cultivo, mes) DO UPDATE SET
               rank            = EXCLUDED.rank,
               is_top3         = EXCLUDED.is_top3,
               mean_yield      = EXCLUDED.mean_yield,
               std_yield       = EXCLUDED.std_yield,
               high_yield_rate = EXCLUDED.high_yield_rate,
               n_samples       = EXCLUDED.n_samples,
               score           = EXCLUDED.score,
               recommendation  = EXCLUDED.recommendation""",
        rows_data,
        page_size=500,
    )
    print(f"  calendario_siembra: {len(rows_data)} filas importadas ({df['municipio'].nunique()} municipios, {df['crop'].nunique()} cultivos).")


# ---------------------------------------------------------------------------
# water_stress_index.csv → indice_estres_hidrico
# ---------------------------------------------------------------------------

def import_stress(cur, reset):
    if not os.path.exists(STRESS_PATH):
        print("  [SKIP] water_stress_index.csv no encontrado.")
        return

    df = pd.read_csv(STRESS_PATH)
    required = {"municipio", "year", "month"}
    if not required.issubset(df.columns):
        print(f"  [ERROR] water_stress_index.csv no tiene las columnas esperadas: {required}")
        return

    if reset:
        cur.execute("DELETE FROM indice_estres_hidrico")

    rows_data = []
    for _, row in df.iterrows():
        rows_data.append((
            row.get("municipio"),
            row.get("zona") if "zona" in df.columns else None,
            float(row["altitud_m"]) if "altitud_m" in df.columns and pd.notna(row.get("altitud_m")) else None,
            int(row.get("year", 0)),
            int(row.get("month", 0)),
            float(row["rainfall"])           if "rainfall" in df.columns           and pd.notna(row.get("rainfall")) else None,
            float(row["eto_mm_day"])         if "eto_mm_day" in df.columns         and pd.notna(row.get("eto_mm_day")) else None,
            float(row["rain_mm_day"])        if "rain_mm_day" in df.columns        and pd.notna(row.get("rain_mm_day")) else None,
            float(row["water_stress_index"]) if "water_stress_index" in df.columns and pd.notna(row.get("water_stress_index")) else None,
            str(row["stress_level"])         if "stress_level" in df.columns       and pd.notna(row.get("stress_level")) else None,
        ))

    execute_values(
        cur,
        """INSERT INTO indice_estres_hidrico
           (municipio, zona, altitud_m, anio, mes, precipitacion, eto_mm_day,
            rain_mm_day, water_stress_index, stress_level)
           VALUES %s
           ON CONFLICT (municipio, anio, mes) DO UPDATE SET
               zona               = EXCLUDED.zona,
               altitud_m          = EXCLUDED.altitud_m,
               precipitacion      = EXCLUDED.precipitacion,
               eto_mm_day         = EXCLUDED.eto_mm_day,
               rain_mm_day        = EXCLUDED.rain_mm_day,
               water_stress_index = EXCLUDED.water_stress_index,
               stress_level       = EXCLUDED.stress_level""",
        rows_data,
        page_size=500,
    )
    years = f"{int(df['year'].min())}–{int(df['year'].max())}"
    print(f"  indice_estres_hidrico: {len(rows_data)} filas importadas ({df['municipio'].nunique()} municipios, {years}).")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    reset = "--reset" in sys.argv
    targets = args if args else ["era5", "sowing", "stress"]

    if not db_available():
        print("ERROR: No se puede conectar a la base de datos.")
        print("Asegúrate de que el contenedor Docker esté corriendo:")
        print("  docker compose up -d")
        sys.exit(1)

    action = "Limpiando y re-importando" if reset else "Importando"
    print(f"\nAgroClima GT — Importación de CSV a DB ({action})\n")

    with get_cursor(dict_cursor=True) as cur:
        if "era5" in targets:
            import_era5(cur, reset)
        if "sowing" in targets:
            import_sowing(cur, reset)
        if "stress" in targets:
            import_stress(cur, reset)

    print("\nImportación completada. Estado de tablas:")
    with get_cursor() as cur:
        for tabla in ["metricas_climaticas", "calendario_siembra", "indice_estres_hidrico"]:
            cur.execute(f"SELECT COUNT(*) AS n FROM {tabla}")
            n = cur.fetchone()["n"]
            print(f"  {tabla:<30} {n:>6} filas")
    print()


if __name__ == "__main__":
    main()
