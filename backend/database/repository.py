import json
from pathlib import Path

import pandas as pd
from psycopg2.extras import Json, execute_values

from .connection import get_cursor


TRAINING_COLUMNS = [
    "dataset_nombre", "municipio", "cultivo", "mes", "anio", "temperatura",
    "precipitacion", "humedad", "ph_suelo", "soil_moisture", "light_lux",
    "greenness_idx", "swvl2", "swvl3", "soil_temp", "temp_max", "temp_min",
    "wind_speed", "yield_pct",
]


def _safe_json(value):
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return Json(value)
    return Json(value)


def replace_dataset_rows(dataset_name: str, df: pd.DataFrame):
    rows = []
    for row in df.to_dict(orient="records"):
        rows.append((
            dataset_name,
            row.get("municipio"),
            row.get("crop"),
            row.get("month"),
            row.get("year"),
            row.get("temperature"),
            row.get("rainfall"),
            row.get("humidity"),
            row.get("soil_ph"),
            row.get("soil_moisture"),
            row.get("light_lux"),
            row.get("greenness_idx"),
            row.get("swvl2"),
            row.get("swvl3"),
            row.get("soil_temp"),
            row.get("temp_max"),
            row.get("temp_min"),
            row.get("wind_speed"),
            row.get("yield_pct"),
        ))

    with get_cursor(dict_cursor=False) as cur:
        cur.execute("DELETE FROM dataset_entrenamiento WHERE dataset_nombre = %s", (dataset_name,))
        execute_values(
            cur,
            f"""INSERT INTO dataset_entrenamiento ({", ".join(TRAINING_COLUMNS)})
                VALUES %s""",
            rows,
            page_size=1000,
        )


def upsert_dataset_registered(
    filename: str,
    tipo: str,
    origen: str | None,
    periodo: str | None,
    total_filas: int | None,
    total_columnas: int | None,
    columnas,
    metadata=None,
    activo: bool = False,
):
    with get_cursor(dict_cursor=False) as cur:
        cur.execute(
            """
            INSERT INTO datasets_registrados
            (nombre_archivo, tipo, origen, periodo, total_filas, total_columnas, columnas, metadata, activo)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (nombre_archivo) DO UPDATE SET
                tipo = EXCLUDED.tipo,
                origen = EXCLUDED.origen,
                periodo = EXCLUDED.periodo,
                total_filas = EXCLUDED.total_filas,
                total_columnas = EXCLUDED.total_columnas,
                columnas = EXCLUDED.columnas,
                metadata = EXCLUDED.metadata,
                activo = EXCLUDED.activo,
                fecha_carga = NOW()
            """,
            (
                filename, tipo, origen, periodo, total_filas, total_columnas,
                _safe_json(columnas), _safe_json(metadata), activo,
            ),
        )


def upsert_source_file(
    filename: str,
    categoria: str,
    periodo: str | None,
    total_filas: int | None,
    total_columnas: int | None,
    columnas,
    metadata=None,
):
    with get_cursor(dict_cursor=False) as cur:
        cur.execute(
            """
            INSERT INTO fuentes_datos
            (nombre_archivo, categoria, periodo, total_filas, total_columnas, columnas, metadata)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (nombre_archivo) DO UPDATE SET
                categoria = EXCLUDED.categoria,
                periodo = EXCLUDED.periodo,
                total_filas = EXCLUDED.total_filas,
                total_columnas = EXCLUDED.total_columnas,
                columnas = EXCLUDED.columnas,
                metadata = EXCLUDED.metadata,
                fecha_carga = NOW()
            """,
            (
                filename, categoria, periodo, total_filas, total_columnas,
                _safe_json(columnas), _safe_json(metadata),
            ),
        )


def replace_metricas_climaticas(metrics: list[dict], fuente: str = "ERA5-Land", periodo: str = "2010-2026"):
    with get_cursor(dict_cursor=False) as cur:
        cur.execute("DELETE FROM metricas_climaticas WHERE fuente = %s AND periodo = %s", (fuente, periodo))
        execute_values(
            cur,
            """
            INSERT INTO metricas_climaticas
            (municipio, temperatura, precipitacion, humedad, soil_moisture, fuente, periodo)
            VALUES %s
            """,
            [
                (
                    item.get("municipio"),
                    item.get("temperature"),
                    item.get("rainfall"),
                    item.get("humidity"),
                    item.get("soilMoisture") if "soilMoisture" in item else item.get("soil_moisture"),
                    fuente,
                    periodo,
                )
                for item in metrics
            ],
        )


def load_training_dataframe(dataset_name: str | None = None) -> pd.DataFrame:
    query = """
        SELECT municipio, cultivo AS crop, mes AS month, anio AS year,
               temperatura AS temperature, precipitacion AS rainfall, humedad AS humidity,
               ph_suelo AS soil_ph, soil_moisture, light_lux, greenness_idx,
               swvl2, swvl3, soil_temp, temp_max, temp_min, wind_speed, yield_pct
        FROM dataset_entrenamiento
    """
    params = []
    if dataset_name:
        query += " WHERE dataset_nombre = %s"
        params.append(dataset_name)
    query += " ORDER BY id"

    with get_cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
    return pd.DataFrame(rows)


_VALID_DEPTOS = [
    "Chimaltenango", "Sacatepequez", "Guatemala", "Escuintla",
    "Santa Rosa", "Solola", "Totonicapan", "Quetzaltenango",
    "Suchitepequez", "Retalhuleu", "San Marcos", "Huehuetenango",
    "Quiche", "Baja Verapaz", "Coban", "Peten",
    "Izabal", "Zacapa", "Chiquimula", "Jalapa",
    "Jutiapa", "El Progreso",
]


def get_latest_metrics():
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT municipio, temperatura AS temperature, precipitacion AS rainfall,
                   humedad AS humidity, soil_moisture
            FROM metricas_climaticas
            WHERE municipio = ANY(%s)
            ORDER BY municipio
            """,
            (_VALID_DEPTOS,),
        )
        rows = cur.fetchall()
    return rows


def get_registered_datasets():
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT nombre_archivo, tipo, origen, periodo, total_filas, total_columnas,
                   columnas, metadata, activo, fecha_carga
            FROM datasets_registrados
            ORDER BY activo DESC, nombre_archivo
            """
        )
        datasets = cur.fetchall()
        cur.execute(
            """
            SELECT nombre_archivo, categoria, periodo, total_filas, total_columnas,
                   columnas, metadata, fecha_carga
            FROM fuentes_datos
            ORDER BY nombre_archivo
            """
        )
        sources = cur.fetchall()
    return {"datasets": datasets, "sources": sources}


def sync_model_metadata(payload: dict):
    with get_cursor(dict_cursor=False) as cur:
        cur.execute("UPDATE modelos_ml SET activo = FALSE")
        cur.execute(
            """
            INSERT INTO modelos_ml
            (nombre, version, dataset_usado, n_filas, n_features, r2_test, mae, rmse,
             crossval_r2, crossval_std, hiperparametros, activo)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,TRUE)
            """,
            (
                payload.get("nombre", "XGBoost"),
                payload.get("version"),
                payload.get("dataset_usado"),
                payload.get("n_filas"),
                payload.get("n_features"),
                payload.get("r2_test"),
                payload.get("mae"),
                payload.get("rmse"),
                payload.get("crossval_r2"),
                payload.get("crossval_std"),
                Json(payload.get("hiperparametros", {})),
            ),
        )
