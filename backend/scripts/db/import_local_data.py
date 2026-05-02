"""
Importa a PostgreSQL los datasets y metricas existentes en backend/data.

Uso:
    python scripts/db/import_local_data.py
"""

import json
import os
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from database.connection import db_available
from database.repository import (
    replace_dataset_rows,
    replace_metricas_climaticas,
    upsert_dataset_registered,
    upsert_source_file,
)


DATA_DIR = BASE_DIR / "data"
DATASETS_DIR = DATA_DIR / "datasets"
SOURCES_DIR = DATA_DIR / "sources"
MODELS_DIR = DATA_DIR / "models"


def _period_from_df(df: pd.DataFrame) -> str | None:
    if "year" in df.columns and not df["year"].dropna().empty:
        years = sorted(int(value) for value in df["year"].dropna().unique())
        return f"{years[0]}-{years[-1]}"
    return None


def import_metrics():
    metrics_path = MODELS_DIR / "latest_metrics.json"
    if not metrics_path.exists():
        return
    with metrics_path.open(encoding="utf-8") as fh:
        metrics = json.load(fh)
    replace_metricas_climaticas(metrics)
    print(f"Metricas climaticas importadas: {len(metrics)}")


def import_datasets():
    dataset_files = [
        ("dataset_preliminar.csv", "entrenamiento", False),
        ("dataset_v2.csv", "entrenamiento", True),
        ("recommendations.csv", "recomendaciones", False),
        ("crop_optimal_conditions.csv", "referencia", False),
    ]

    for filename, tipo, activo in dataset_files:
        path = DATASETS_DIR / filename
        if not path.exists():
            continue
        df = pd.read_csv(path)
        periodo = _period_from_df(df)
        upsert_dataset_registered(
            filename=filename,
            tipo=tipo,
            origen="backend/data/datasets",
            periodo=periodo or ("Estatico" if tipo != "entrenamiento" else None),
            total_filas=len(df),
            total_columnas=len(df.columns),
            columnas=list(df.columns),
            metadata={"path": str(path.relative_to(BASE_DIR)), "activo": activo},
            activo=activo,
        )
        if filename in {"dataset_preliminar.csv", "dataset_v2.csv"}:
            replace_dataset_rows(filename, df)
            print(f"Dataset de entrenamiento importado: {filename} ({len(df)} filas)")
        else:
            print(f"Dataset registrado: {filename} ({len(df)} filas)")


def import_sources():
    source_map = {
        "era5_mensual.csv": "ERA5-Land",
        "nasa_power_mensual.csv": "NASA POWER",
        "soilgrids_suelo.csv": "SoilGrids",
        "insivumeh_recent_mensual.csv": "INSIVUMEH",
    }
    for filename, categoria in source_map.items():
        path = SOURCES_DIR / filename
        if not path.exists():
            continue
        df = pd.read_csv(path)
        upsert_source_file(
            filename=filename,
            categoria=categoria,
            periodo=_period_from_df(df) or "Estatico",
            total_filas=len(df),
            total_columnas=len(df.columns),
            columnas=list(df.columns),
            metadata={"path": str(path.relative_to(BASE_DIR))},
        )
        print(f"Fuente registrada: {filename} ({len(df)} filas)")


def main():
    if not db_available():
        raise RuntimeError("La base de datos no esta disponible. Verifica Docker y las variables DB_*.")
    import_metrics()
    import_datasets()
    import_sources()
    print("Importacion completada.")


if __name__ == "__main__":
    main()
