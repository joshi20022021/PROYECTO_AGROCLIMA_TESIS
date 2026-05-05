"""
API REST + WebSocket para AgroClima GT.

Endpoints:
    GET  /health               → estado del servidor
    GET  /metrics              → últimas métricas ERA5-Land
    POST /predict              → predicción XGBoost de rendimiento
    GET  /dataset              → registros del dataset (máx 200)
    POST /upload-dataset       → subir CSV manual
    GET  /dataset-template     → descargar plantilla CSV
    GET  /arduino/status       → estado de conexión del Arduino
    POST /arduino/connect      → conectar Arduino (puerto opcional)
    POST /arduino/disconnect   → desconectar Arduino
    POST /arduino/simulate     → enviar lectura simulada (sin hardware)
    WS   /ws/arduino           → stream en tiempo real de lecturas
"""

import asyncio
import csv
import io
import json
import os
import subprocess
import sys
import threading
import unicodedata
from datetime import datetime, timedelta
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from psycopg2.extras import Json
import bcrypt

from arduino_reader  import reader as arduino_reader
from alert_engine    import check_alerts
from email_notifier  import notify_critical_alerts, is_configured as email_configured
from ml_insights import (
    prepare_input_row,
    predict_with_interval,
    explain_prediction_shap,
    predict_multicrop,
    detect_sensor_anomaly,
    compute_data_drift,
)

try:
    from database.connection import get_cursor, db_available
    from database.repository import (
        get_latest_metrics,
        get_registered_datasets,
        load_training_dataframe,
        upsert_dataset_registered,
    )
    _DB_MODULE = True
except ImportError:
    _DB_MODULE = False
    def db_available(): return False

ADMIN_TOKEN = "agroclima-admin-2024"

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="AgroClima GT API", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Rutas de archivos
# ---------------------------------------------------------------------------

BASE_DIR      = os.path.dirname(__file__)
METRICS_PATH  = os.path.join(BASE_DIR, "data", "models", "latest_metrics.json")
DATASET_PATH  = os.path.join(BASE_DIR, "data", "datasets", "dataset_preliminar.csv")
UPLOADS_DIR   = os.path.join(BASE_DIR, "data", "uploads")
MODEL_PATH    = os.path.join(BASE_DIR, "data", "models", "xgboost_yield.joblib")
ENCODER_PATH  = os.path.join(BASE_DIR, "data", "models", "label_encoders.joblib")
DATASET_OM_PATH = os.path.join(BASE_DIR, "data", "datasets", "dataset_openmeteo.csv")
WATER_STRESS_PATH    = os.path.join(BASE_DIR, "data", "processed", "water_stress_index.csv")
SOWING_CALENDAR_PATH = os.path.join(BASE_DIR, "data", "processed", "sowing_calendar.csv")
CROP_OPTIMAL_PATH    = os.path.join(BASE_DIR, "data", "datasets", "crop_optimal_conditions.csv")
COMPARISON_PATH      = os.path.join(BASE_DIR, "data", "models", "model_comparison.json")
LOGS_DIR             = os.path.join(BASE_DIR, "data", "logs")
OPEN_METEO_USAGE_PATH = os.path.join(LOGS_DIR, "open_meteo_usage.json")
INSIVUMEH_DAILY_PATH = os.path.join(BASE_DIR, "data", "raw", "insivumeh", "insivumeh_stations_daily.csv")
INSIVUMEH_MONTHLY_PATH = os.path.join(BASE_DIR, "data", "sources", "insivumeh_recent_mensual.csv")
DATASETS_DIR = os.path.join(BASE_DIR, "data", "datasets")
SOURCES_DIR = os.path.join(BASE_DIR, "data", "sources")

RETRAIN_THRESHOLD = int(os.getenv("RETRAIN_FEEDBACK_THRESHOLD", "80"))
ALERT_PERSISTENCE_SECONDS = int(os.getenv("ALERT_PERSISTENCE_SECONDS", "120"))

sys.path.insert(0, os.path.join(BASE_DIR, "scripts", "download"))
try:
    from municipios_nacional import MUNICIPIOS as MUNICIPIO_CATALOG
except Exception:
    MUNICIPIO_CATALOG = {
        "Chimaltenango": {"lat": 14.6614, "lon": -90.8197, "zona": "altiplano_central", "depto": "Chimaltenango"},
        "Sacatepequez": {"lat": 14.5586, "lon": -90.7295, "zona": "altiplano_central", "depto": "Sacatepequez"},
        "Guatemala": {"lat": 14.6349, "lon": -90.5069, "zona": "altiplano_central", "depto": "Guatemala"},
    }

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

FEATURES = ["municipio_enc", "crop_enc", "month",
            "temperature", "rainfall", "humidity",
            "soil_ph", "soil_moisture", "light_lux", "greenness_idx",
            "swvl2", "swvl3", "soil_temp",
            "temp_max", "temp_min", "wind_speed"]

MODEL_FEATURE_META = {
    "rainfall":      {"label": "Precipitacion acumulada", "group": "clima", "source": "Open-Meteo / ERA5-Land"},
    "soil_moisture": {"label": "Humedad del suelo 0-7 cm", "group": "suelo", "source": "Sensor / reanalisis"},
    "crop_enc":      {"label": "Tipo de cultivo", "group": "cultivo", "source": "Catalogo agronomico"},
    "humidity":      {"label": "Humedad relativa", "group": "clima", "source": "Open-Meteo / ERA5-Land"},
    "month":         {"label": "Mes agricola", "group": "tiempo", "source": "Calendario"},
    "temperature":   {"label": "Temperatura del aire", "group": "clima", "source": "Open-Meteo / DS18B20"},
    "greenness_idx": {"label": "Indice de verdor", "group": "sensor", "source": "TCS3200"},
    "temp_min":      {"label": "Temperatura minima", "group": "clima", "source": "NASA POWER / Open-Meteo"},
    "soil_temp":     {"label": "Temperatura del suelo", "group": "suelo", "source": "ERA5-Land / Open-Meteo"},
    "temp_max":      {"label": "Temperatura maxima", "group": "clima", "source": "NASA POWER / Open-Meteo"},
    "light_lux":     {"label": "Radiacion solar estimada", "group": "sensor", "source": "TSL2561 / Open-Meteo"},
    "swvl3":         {"label": "Humedad del suelo 28-100 cm", "group": "suelo", "source": "ERA5-Land"},
    "swvl2":         {"label": "Humedad del suelo 7-28 cm", "group": "suelo", "source": "ERA5-Land"},
    "soil_ph":       {"label": "pH del suelo", "group": "suelo", "source": "SoilGrids / laboratorio"},
    "municipio_enc": {"label": "Departamento / Municipio", "group": "lugar", "source": "Ubicacion"},
    "wind_speed":    {"label": "Velocidad del viento", "group": "clima", "source": "NASA POWER"},
}

# Columnas aceptadas en CSV (con aliases)
CSV_COL_MAP = {
    "municipio": "municipio", "municipality": "municipio",
    "crop": "crop", "cultivo": "crop",
    "month": "month", "mes": "month",
    "year": "year", "anio": "year", "año": "year",
    "temperature": "temperature", "temperatura": "temperature",
    "rainfall": "rainfall", "precipitacion": "rainfall", "lluvia": "rainfall",
    "humidity": "humidity", "humedad": "humidity",
    "soil_ph": "soil_ph", "soilph": "soil_ph", "ph": "soil_ph",
    "soil_moisture": "soil_moisture", "soilmoisture": "soil_moisture", "humedad_suelo": "soil_moisture",
    "yield_pct": "yield_pct", "rendimiento": "yield_pct",
}

# ---------------------------------------------------------------------------
# Autenticación y Modelos Base
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    nombre: str = ""
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False

@app.post("/auth/register")
def register_user(user: UserCreate):
    if not db_available():
        raise HTTPException(503, "Base de datos no disponible")
    
    hashed_password = get_password_hash(user.password)
    
    with get_cursor() as cur:
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (user.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="El correo ya o el usuario ya está registrado")
            
        cur.execute(
            "INSERT INTO usuarios (nombre, email, password_hash) VALUES (%s, %s, %s) RETURNING id, email, rol, nombre",
            (user.nombre, user.email, hashed_password)
        )
        new_user = cur.fetchone()
        return {"msg": "Usuario registrado exitosamente", "user": {"email": new_user['email'], "rol": new_user['rol'], "nombre": new_user['nombre']}}

@app.post("/auth/login")
def login_user(user: UserLogin):
    # El usuario pidió explícitamente mantener al administrador quemado, con validación de rol
    if user.email == "admin" and user.password == "agroclima2024":
        return {"msg": "Login exitoso", "user": {"email": "admin", "rol": "admin", "nombre": "Administrador"}}
        
    if not db_available():
        raise HTTPException(503, "Base de datos no disponible")
        
    with get_cursor() as cur:
        cur.execute("SELECT id, nombre, email, password_hash, rol FROM usuarios WHERE email = %s", (user.email,))
        db_user = cur.fetchone()
        
        if not db_user or not verify_password(user.password, db_user['password_hash']):
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
            
        return {
            "msg": "Login exitoso",
            "user": {
                "id": db_user['id'],
                "email": db_user['email'],
                "rol": db_user['rol'],
                "nombre": db_user['nombre']
            }
        }

# ---------------------------------------------------------------------------
# Modelo
# ---------------------------------------------------------------------------

_model    = None
_encoders = None
_crop_optimal_df = None

def get_model():
    global _model, _encoders
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise HTTPException(503, "Modelo no entrenado. Ejecuta: python model_xgboost.py train")
        _model    = joblib.load(MODEL_PATH)
        _encoders = joblib.load(ENCODER_PATH)
    return _model, _encoders


_VALID_RANGES = {
    "temperature":   (5.0,  45.0),
    "rainfall":      (0.0,  600.0),
    "humidity":      (5.0,  100.0),
    "soil_ph":       (3.5,  9.5),
    "soil_moisture": (0.01, 0.65),
    "light_lux":     (500,  130_000),
}

def _validate_inputs(temperature: float, rainfall: float, humidity: float,
                     soil_ph: float, soil_moisture: float, light_lux: float):
    """Rechaza valores fuera del rango fisiológico para Guatemala."""
    out_of_range = []
    for name, value in [
        ("temperature",   temperature),
        ("rainfall",      rainfall),
        ("humidity",      humidity),
        ("soil_ph",       soil_ph),
        ("soil_moisture", soil_moisture),
        ("light_lux",     light_lux),
    ]:
        lo, hi = _VALID_RANGES[name]
        if not (lo <= value <= hi):
            out_of_range.append(f"{name}={value} (rango válido {lo}–{hi})")

    if out_of_range:
        raise HTTPException(
            422,
            detail={
                "error": "Valores fuera del rango fisiológico para agricultura en Guatemala. "
                         "El modelo XGBoost no puede predecir correctamente con estos datos.",
                "campos_invalidos": out_of_range,
                "sugerencia": "Ingresa valores reales medidos en campo.",
            },
        )

def _load_crop_optimal_reference():
    global _crop_optimal_df
    if _crop_optimal_df is None:
        path = CROP_OPTIMAL_PATH
        if not os.path.exists(path):
            fallback = os.path.join(BASE_DIR, "data", "processed", "crop_optimal_conditions.csv")
            path = fallback if os.path.exists(fallback) else path
        if not os.path.exists(path):
            raise HTTPException(503, "No se encontrÃ³ crop_optimal_conditions.csv")
        _crop_optimal_df = pd.read_csv(path)
    return _crop_optimal_df


def _build_crop_optimal_payload(crop: str):
    df = _load_crop_optimal_reference()
    matches = df[df["crop"].astype(str).str.lower() == crop.lower()]
    if matches.empty:
        raise HTTPException(404, f"No hay rangos Ã³ptimos registrados para {crop}")

    row = matches.iloc[0]
    return {
        "crop": row.get("crop", crop),
        "category": row.get("category"),
        "notes": row.get("notes"),
        "temperature": {
            "min": float(row["temp_min"]),
            "max": float(row["temp_max"]),
            "unit": "C",
        },
        "rainfall": {
            "min": float(row["rain_min"]),
            "max": float(row["rain_max"]),
            "unit": "mm",
        },
        "humidity": {
            "min": float(row["humidity_min"]),
            "max": float(row["humidity_max"]),
            "unit": "%",
        },
        "soil_ph": {
            "min": float(row["ph_min"]),
            "max": float(row["ph_max"]),
            "unit": "pH",
        },
    }


def _yield_level(yield_pct: float) -> str:
    if yield_pct >= 75:
        return "alto"
    if yield_pct >= 50:
        return "medio"
    if yield_pct >= 25:
        return "bajo"
    return "critico"


def _build_payload_dict(municipio: str, crop: str, month: int,
                        temperature: float, soil_moisture: float,
                        light_lux: float, greenness_idx: float,
                        rainfall: float = 0.0, humidity: float = 70.0,
                        soil_ph: float = 6.5,
                        swvl2: float = None, swvl3: float = None,
                        soil_temp: float = None,
                        temp_max: float = None, temp_min: float = None,
                        wind_speed: float = None) -> dict:
    return {
        "municipio": municipio,
        "crop": crop,
        "month": month,
        "temperature": temperature,
        "rainfall": rainfall,
        "humidity": humidity,
        "soil_ph": soil_ph,
        "soil_moisture": soil_moisture,
        "light_lux": light_lux,
        "greenness_idx": greenness_idx,
        "swvl2": swvl2 if swvl2 is not None else soil_moisture + 0.03,
        "swvl3": swvl3 if swvl3 is not None else soil_moisture + 0.05,
        "soil_temp": soil_temp if soil_temp is not None else temperature - 3.0,
        "temp_max": temp_max if temp_max is not None else temperature + 8.0,
        "temp_min": temp_min if temp_min is not None else temperature - 6.0,
        "wind_speed": wind_speed if wind_speed is not None else 2.5,
    }


def run_prediction(municipio: str, crop: str, month: int,
                   temperature: float, soil_moisture: float,
                   light_lux: float, greenness_idx: float,
                   rainfall: float = 0.0, humidity: float = 70.0,
                   soil_ph: float = 6.5,
                   swvl2: float = None, swvl3: float = None,
                   soil_temp: float = None,
                   temp_max: float = None, temp_min: float = None,
                   wind_speed: float = None,
                   include_explain: bool = True,
                   include_monitoring: bool = True) -> dict:
    _validate_inputs(temperature, rainfall, humidity, soil_ph, soil_moisture, light_lux)
    model, encoders = get_model()
    payload = _build_payload_dict(
        municipio, crop, month,
        temperature, soil_moisture,
        light_lux, greenness_idx,
        rainfall, humidity, soil_ph,
        swvl2, swvl3, soil_temp,
        temp_max, temp_min, wind_speed,
    )

    prepared = prepare_input_row(payload, encoders)
    interval = predict_with_interval(model, prepared.row_df)
    yield_pct = interval["prediction"]
    level = _yield_level(yield_pct)

    result = {
        "yield_pct": yield_pct,
        "yield_level": level,
        "confidence": {
            "low": interval["low"],
            "high": interval["high"],
            "margin": interval["margin"],
        },
    }

    if include_explain:
        result["explanation"] = explain_prediction_shap(model, prepared.row_df, prepared.row_raw)

    if include_monitoring:
        result["anomaly"] = detect_sensor_anomaly(encoders, payload)
        result["drift"] = compute_data_drift(encoders, payload)

    return result


def _store_alerts(cur, alerts: list[dict], municipio: str, cultivo: str, prediccion_id: int | None = None):
    for alert in alerts:
        cur.execute(
            """INSERT INTO alertas
               (prediccion_id, municipio, cultivo, variable, condicion, severidad, mensaje)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (
                prediccion_id,
                municipio,
                cultivo,
                alert.get("variable"),
                alert.get("condition"),
                alert.get("severity"),
                alert.get("action") or alert.get("problem") or "Alerta generada por el motor de reglas",
            ),
        )


_retrain_state = {
    "running": False,
    "last_started": None,
    "last_finished": None,
    "last_status": "idle",
    "last_error": None,
}


def _ensure_feedback_table():
    if not (_DB_MODULE and db_available()):
        return
    try:
        with get_cursor(dict_cursor=False) as cur:
            cur.execute(
                """CREATE TABLE IF NOT EXISTS model_feedback (
                       id SERIAL PRIMARY KEY,
                       created_at TIMESTAMP DEFAULT NOW(),
                       municipio VARCHAR(100) NOT NULL,
                       cultivo VARCHAR(100) NOT NULL,
                       mes SMALLINT,
                       predicted_yield FLOAT NOT NULL,
                       actual_yield FLOAT NOT NULL,
                       abs_error FLOAT,
                       notes TEXT,
                       processed_retrain BOOLEAN DEFAULT FALSE
                   )"""
            )
    except Exception:
        pass


def _feedback_pending_count() -> int:
    if not (_DB_MODULE and db_available()):
        return 0
    _ensure_feedback_table()
    try:
        with get_cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM model_feedback WHERE processed_retrain = FALSE")
            return int(cur.fetchone()["n"])
    except Exception:
        return 0


def _mark_feedback_processed():
    if not (_DB_MODULE and db_available()):
        return
    try:
        with get_cursor() as cur:
            cur.execute("UPDATE model_feedback SET processed_retrain = TRUE WHERE processed_retrain = FALSE")
    except Exception:
        pass


def _run_retraining_job():
    script_path = os.path.join(BASE_DIR, "scripts", "training", "model_xgboost.py")
    _retrain_state["running"] = True
    _retrain_state["last_started"] = datetime.now().isoformat()
    _retrain_state["last_status"] = "running"
    _retrain_state["last_error"] = None

    try:
        proc = subprocess.run(
            [sys.executable, script_path, "train"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            global _model, _encoders
            _model = None
            _encoders = None
            _mark_feedback_processed()
            _retrain_state["last_status"] = "success"
        else:
            _retrain_state["last_status"] = "failed"
            _retrain_state["last_error"] = (proc.stderr or proc.stdout or "Fallo desconocido")[-1200:]
    except Exception as e:
        _retrain_state["last_status"] = "failed"
        _retrain_state["last_error"] = str(e)
    finally:
        _retrain_state["running"] = False
        _retrain_state["last_finished"] = datetime.now().isoformat()


def _maybe_trigger_retraining() -> dict:
    pending = _feedback_pending_count()
    if pending < RETRAIN_THRESHOLD:
        return {
            "triggered": False,
            "pending_feedback": pending,
            "threshold": RETRAIN_THRESHOLD,
            "state": _retrain_state,
        }

    if _retrain_state["running"]:
        return {
            "triggered": False,
            "pending_feedback": pending,
            "threshold": RETRAIN_THRESHOLD,
            "state": _retrain_state,
            "message": "Reentrenamiento ya en ejecucion.",
        }

    threading.Thread(target=_run_retraining_job, daemon=True).start()
    return {
        "triggered": True,
        "pending_feedback": pending,
        "threshold": RETRAIN_THRESHOLD,
        "state": _retrain_state,
    }


def _normalize_location_key(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.casefold().split())


def _resolve_coords(municipio: str) -> tuple[float | None, float | None, str | None, str | None]:
    requested = _normalize_location_key(municipio)
    for known, meta in MUNICIPIO_CATALOG.items():
        if _normalize_location_key(known) == requested:
            return meta.get("lat"), meta.get("lon"), meta.get("depto"), meta.get("zona")
    return None, None, None, None


def _risk_level_from_score(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


_alert_persistence_state: dict[tuple[str, str, str, str], dict] = {}
_alert_persistence_lock = threading.Lock()


def _parse_event_timestamp(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            pass
    return datetime.now()


def _alert_key(municipio: str, crop: str, alert: dict) -> tuple[str, str, str, str]:
    return (
        municipio,
        crop,
        str(alert.get("variable") or ""),
        str(alert.get("condition") or ""),
    )


def _filter_persistent_alerts(alerts: list[dict], municipio: str, crop: str, event_ts) -> list[dict]:
    if not alerts:
        return []

    current_ts = _parse_event_timestamp(event_ts)
    active_keys = {_alert_key(municipio, crop, alert) for alert in alerts}
    promoted: list[dict] = []

    with _alert_persistence_lock:
        for key in list(_alert_persistence_state):
            key_municipio, key_crop, _, _ = key
            if key_municipio == municipio and key_crop == crop and key not in active_keys:
                _alert_persistence_state.pop(key, None)

        for alert in alerts:
            key = _alert_key(municipio, crop, alert)
            state = _alert_persistence_state.get(key)

            if state is None:
                _alert_persistence_state[key] = {
                    "first_seen": current_ts,
                    "last_seen": current_ts,
                    "samples": 1,
                }
                continue

            if current_ts < state["first_seen"]:
                state["first_seen"] = current_ts

            state["last_seen"] = current_ts
            state["samples"] += 1

            duration_s = max((current_ts - state["first_seen"]).total_seconds(), 0.0)
            if duration_s < ALERT_PERSISTENCE_SECONDS:
                continue

            alert_with_persistence = dict(alert)
            alert_with_persistence["persistence"] = {
                "active": True,
                "seconds": round(duration_s, 1),
                "threshold_seconds": ALERT_PERSISTENCE_SECONDS,
                "samples": state["samples"],
                "first_seen": state["first_seen"].isoformat(),
            }
            promoted.append(alert_with_persistence)

        stale_before = current_ts.timestamp() - (ALERT_PERSISTENCE_SECONDS * 4)
        for key, state in list(_alert_persistence_state.items()):
            if state["last_seen"].timestamp() < stale_before:
                _alert_persistence_state.pop(key, None)

    return promoted


# ---------------------------------------------------------------------------
# WebSocket — gestor de conexiones
# ---------------------------------------------------------------------------

class _WsManager:
    def __init__(self):
        self._clients: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._clients.append(ws)

    def disconnect(self, ws: WebSocket):
        self._clients.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self._clients:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._clients.remove(ws)

ws_manager = _WsManager()


# Callback que se ejecuta en el hilo del arduino_reader
def _on_arduino_data(raw: dict):
    """Procesa lectura del Arduino, genera predicción y alertas, hace broadcast."""
    result = {
        "sensors":    raw,
        "prediction": None,
        "alerts":     [],
        "timestamp":  raw.get("timestamp"),
    }

    crop      = _arduino_config.get("crop", "Maiz")
    municipio = _arduino_config.get("municipio", "Chimaltenango")

    if crop and municipio:
        # Predicción XGBoost
        try:
            result["prediction"] = run_prediction(
                municipio     = municipio,
                crop          = crop,
                month         = datetime.now().month,
                temperature   = raw["temperature"],
                soil_moisture = raw["soil_moisture"],
                light_lux     = raw.get("light_lux",     20000),
                greenness_idx = raw.get("greenness_idx", 65),
                rainfall      = raw.get("rainfall",      0.0),
                humidity      = raw.get("humidity",      70.0),
                soil_ph       = raw.get("soil_ph",       6.5),
                include_explain = False,
            )
        except Exception:
            pass

        # Alertas en tiempo real
        try:
            instant_alerts = check_alerts(raw, crop)
            result["alerts"] = _filter_persistent_alerts(
                instant_alerts,
                municipio=municipio,
                crop=crop,
                event_ts=raw.get("timestamp"),
            )
        except Exception:
            pass

        # Notificación por correo para alertas críticas
        if result["alerts"] and crop and municipio:
            try:
                sent_vars = notify_critical_alerts(
                    alerts    = result["alerts"],
                    crop      = crop,
                    municipio = municipio,
                    sensors   = raw,
                    timestamp = raw.get("timestamp"),
                )
                if sent_vars and _DB_MODULE and db_available():
                    with get_cursor() as cur:
                        cur.execute(
                            """INSERT INTO email_log
                               (cultivo, municipio, variables, destinatarios, ok)
                               VALUES (%s, %s, %s, %s, TRUE)""",
                            (crop, municipio,
                             json.dumps(sent_vars),
                             os.getenv("ALERT_EMAIL_TO", "")),
                        )
            except Exception as _e:
                print(f"[email] fallo silencioso: {_e}")

    if _DB_MODULE and db_available():
        try:
            with get_cursor() as cur:
                prediccion_id = None
                if result["prediction"]:
                    cur.execute(
                        """INSERT INTO predicciones
                           (municipio, cultivo, mes, temperatura, precipitacion, humedad,
                            ph_suelo, soil_moisture, light_lux, greenness_idx,
                            yield_pct, yield_level, fuente)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                           RETURNING id""",
                        (
                            municipio,
                            crop,
                            datetime.now().month,
                            raw.get("temperature"),
                            raw.get("rainfall"),
                            raw.get("humidity"),
                            raw.get("soil_ph"),
                            raw.get("soil_moisture"),
                            raw.get("light_lux"),
                            raw.get("greenness_idx"),
                            result["prediction"]["yield_pct"],
                            result["prediction"]["yield_level"],
                            "arduino",
                        ),
                    )
                    prediccion_id = cur.fetchone()["id"]

                cur.execute(
                    """INSERT INTO lecturas_arduino
                       (municipio, cultivo, temperatura, soil_moisture, light_lux,
                        greenness_idx, humedad, precipitacion, ph_suelo, raw_json)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (municipio, crop,
                     raw.get("temperature"), raw.get("soil_moisture"), raw.get("light_lux"),
                     raw.get("greenness_idx"), raw.get("humidity"), raw.get("rainfall"),
                     raw.get("soil_ph"), Json(raw)),
                )

                if result["alerts"]:
                    _store_alerts(cur, result["alerts"], municipio, crop, prediccion_id)
        except Exception:
            pass

    asyncio.run_coroutine_threadsafe(
        ws_manager.broadcast(result),
        _event_loop,
    )


# Config dinámica del Arduino (crop/municipio elegidos desde el frontend)
_arduino_config = {"municipio": "Chimaltenango", "crop": "Maiz"}
_event_loop: asyncio.AbstractEventLoop = None

arduino_reader.on_data = _on_arduino_data


@app.on_event("startup")
async def startup():
    global _event_loop
    _event_loop = asyncio.get_event_loop()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PredictRequest(BaseModel):
    municipio:     str
    crop:          str
    month:         int
    # Sensores físicos
    temperature:   float           # DS18B20
    soil_moisture: float = 0.28    # Higrómetro capacitivo (swvl1)
    light_lux:     float = 20000.0 # TSL2561
    greenness_idx: float = 65.0    # TCS3200 → G/(R+G+B)*100
    # Sin sensor físico → vienen de ERA5 o entrada manual
    rainfall:      float  = 0.0
    humidity:      float  = 70.0
    soil_ph:       float  = 6.5
    # ERA5-Land extra (opcionales — se estiman si no se envían)
    swvl2:         Optional[float] = None   # humedad suelo 7-28 cm
    swvl3:         Optional[float] = None   # humedad suelo 28-100 cm
    soil_temp:     Optional[float] = None   # temperatura suelo 0-7 cm (°C)
    # NASA POWER extra (opcionales)
    temp_max:      Optional[float] = None   # temperatura máxima mensual (°C)
    temp_min:      Optional[float] = None   # temperatura mínima mensual (°C)
    wind_speed:    Optional[float] = None   # velocidad viento 2m (m/s)

class ArduinoConnectRequest(BaseModel):
    port: Optional[str] = None
    baud_rate: int = 9600

class ArduinoConfigRequest(BaseModel):
    municipio: str
    crop:      str

class SimulateRequest(BaseModel):
    # Sensores físicos
    temperature:   float = 22.0    # DS18B20
    light_lux:     float = 32000.0 # TSL2561
    color_r:       float = 145.0   # TCS3200
    color_g:       float = 210.0   # TCS3200
    color_b:       float = 98.0    # TCS3200
    soil_moisture: float = 0.31    # Higrómetro capacitivo
    # Opcionales
    humidity:      float = 74.0
    rainfall:      float = 45.0
    soil_ph:       float = 6.3


class FeedbackRequest(BaseModel):
    municipio: str
    crop: str
    month: int
    predicted_yield: float
    actual_yield: float
    notes: Optional[str] = None


class RetrainCheckRequest(BaseModel):
    threshold: Optional[int] = None


# ---------------------------------------------------------------------------
# Endpoints — General
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    pending_feedback = _feedback_pending_count() if (_DB_MODULE and db_available()) else 0
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "model_ready":   os.path.exists(MODEL_PATH),
        "metrics_ready": os.path.exists(METRICS_PATH),
        "water_stress_ready": os.path.exists(WATER_STRESS_PATH),
        "sowing_calendar_ready": os.path.exists(SOWING_CALENDAR_PATH),
        "insivumeh_ready": os.path.exists(INSIVUMEH_MONTHLY_PATH),
        "pending_feedback": pending_feedback,
        "retrain_threshold": RETRAIN_THRESHOLD,
        "alert_persistence_seconds": ALERT_PERSISTENCE_SECONDS,
        "retraining": _retrain_state,
        "arduino": arduino_reader.connected,
        "db_online": _DB_MODULE and db_available(),
    }


@app.get("/metrics")
def get_metrics():
    if _DB_MODULE and db_available():
        rows = get_latest_metrics()
        if rows:
            return rows
    if not os.path.exists(METRICS_PATH):
        raise HTTPException(404, "No hay métricas ERA5. Ejecuta: python process_era5.py")
    with open(METRICS_PATH, encoding="utf-8") as f:
        return json.load(f)


@app.get("/insivumeh/monthly")
def insivumeh_monthly(municipio: str = None, year: int | None = None, month: int | None = None):
    if not os.path.exists(INSIVUMEH_MONTHLY_PATH):
        raise HTTPException(
            404,
            "No existe la fuente INSIVUMEH procesada. Ejecuta: python scripts/download/insivumeh_client.py",
        )

    df = pd.read_csv(INSIVUMEH_MONTHLY_PATH)
    if municipio:
        df = df[df["municipio"].astype(str).str.lower() == municipio.lower()]
    if year is not None:
        df = df[df["year"] == year]
    if month is not None:
        df = df[df["month"] == month]
    return df.sort_values(["municipio", "year", "month"], ascending=[True, False, False]).to_dict(orient="records")


@app.get("/insivumeh/daily")
def insivumeh_daily(municipio: str = None, station: str = None, days: int = 30):
    if not os.path.exists(INSIVUMEH_DAILY_PATH):
        raise HTTPException(
            404,
            "No existe la fuente INSIVUMEH procesada. Ejecuta: python scripts/download/insivumeh_client.py",
        )

    df = pd.read_csv(INSIVUMEH_DAILY_PATH)
    if municipio:
        df = df[df["municipio"].fillna("").astype(str).str.lower() == municipio.lower()]
    if station:
        df = df[df["station_name"].fillna("").astype(str).str.lower().str.contains(station.lower())]
    if days > 0 and "date" in df.columns:
        df = df.sort_values("date", ascending=False).head(days * 10)
    return df.sort_values(["date", "station_name"], ascending=[False, True]).head(max(days * 20, 50)).to_dict(orient="records")


@app.post("/predict")
def predict(req: PredictRequest):
    result = run_prediction(
        req.municipio, req.crop, req.month,
        req.temperature, req.soil_moisture,
        req.light_lux, req.greenness_idx,
        req.rainfall, req.humidity, req.soil_ph,
        req.swvl2, req.swvl3, req.soil_temp,
        req.temp_max, req.temp_min, req.wind_speed,
    )
    if _DB_MODULE and db_available():
        try:
            with get_cursor() as cur:
                cur.execute(
                    """INSERT INTO predicciones
                       (municipio, cultivo, mes, temperatura, precipitacion, humedad,
                        ph_suelo, soil_moisture, light_lux, greenness_idx,
                        swvl2, swvl3, soil_temp, temp_max, temp_min, wind_speed,
                        yield_pct, yield_level, fuente)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       RETURNING id""",
                    (
                        req.municipio,
                        req.crop,
                        req.month,
                        req.temperature,
                        req.rainfall,
                        req.humidity,
                        req.soil_ph,
                        req.soil_moisture,
                        req.light_lux,
                        req.greenness_idx,
                        req.swvl2,
                        req.swvl3,
                        req.soil_temp,
                        req.temp_max,
                        req.temp_min,
                        req.wind_speed,
                        result["yield_pct"],
                        result["yield_level"],
                        "manual",
                    ),
                )
                prediccion_id = cur.fetchone()["id"]

                alerts = check_alerts(
                    {
                        "temperature": req.temperature,
                        "soil_moisture": req.soil_moisture,
                        "light_lux": req.light_lux,
                        "greenness_idx": req.greenness_idx,
                        "humidity": req.humidity,
                        "rainfall": req.rainfall,
                        "soil_ph": req.soil_ph,
                    },
                    req.crop,
                )
                if alerts:
                    _store_alerts(cur, alerts, req.municipio, req.crop, prediccion_id)
        except Exception:
            pass
    return result


@app.post("/predict/multicrop")
def predict_all_crops(req: PredictRequest):
    _validate_inputs(req.temperature, req.rainfall, req.humidity, req.soil_ph, req.soil_moisture, req.light_lux)
    model, encoders = get_model()
    payload = _build_payload_dict(
        req.municipio, req.crop, req.month,
        req.temperature, req.soil_moisture,
        req.light_lux, req.greenness_idx,
        req.rainfall, req.humidity, req.soil_ph,
        req.swvl2, req.swvl3, req.soil_temp,
        req.temp_max, req.temp_min, req.wind_speed,
    )
    ranking = predict_multicrop(model, encoders, payload)
    return {
        "municipio": req.municipio,
        "month": req.month,
        "ranking": ranking,
        "top_recommendation": ranking[0] if ranking else None,
    }


@app.post("/monitor/anomaly")
def monitor_anomaly(req: PredictRequest):
    _, encoders = get_model()
    payload = _build_payload_dict(
        req.municipio, req.crop, req.month,
        req.temperature, req.soil_moisture,
        req.light_lux, req.greenness_idx,
        req.rainfall, req.humidity, req.soil_ph,
        req.swvl2, req.swvl3, req.soil_temp,
        req.temp_max, req.temp_min, req.wind_speed,
    )
    return detect_sensor_anomaly(encoders, payload)


@app.post("/monitor/drift")
def monitor_drift(req: PredictRequest):
    _, encoders = get_model()
    payload = _build_payload_dict(
        req.municipio, req.crop, req.month,
        req.temperature, req.soil_moisture,
        req.light_lux, req.greenness_idx,
        req.rainfall, req.humidity, req.soil_ph,
        req.swvl2, req.swvl3, req.soil_temp,
        req.temp_max, req.temp_min, req.wind_speed,
    )
    return compute_data_drift(encoders, payload)


@app.post("/feedback")
def save_feedback(req: FeedbackRequest):
    if not (_DB_MODULE and db_available()):
        raise HTTPException(503, "Base de datos no disponible")

    _ensure_feedback_table()

    abs_error = abs(float(req.predicted_yield) - float(req.actual_yield))
    try:
        with get_cursor() as cur:
            cur.execute(
                """INSERT INTO model_feedback
                   (municipio, cultivo, mes, predicted_yield, actual_yield, abs_error, notes)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)
                   RETURNING id""",
                (
                    req.municipio,
                    req.crop,
                    req.month,
                    req.predicted_yield,
                    req.actual_yield,
                    abs_error,
                    req.notes,
                ),
            )
            feedback_id = cur.fetchone()["id"]
    except Exception as e:
        raise HTTPException(500, f"No se pudo guardar feedback: {e}")

    retrain_info = _maybe_trigger_retraining()
    return {
        "ok": True,
        "feedback_id": feedback_id,
        "abs_error": round(abs_error, 2),
        "retraining": retrain_info,
    }


@app.post("/retrain/check")
def retrain_check(req: RetrainCheckRequest):
    global RETRAIN_THRESHOLD
    if req.threshold is not None and req.threshold > 0:
        RETRAIN_THRESHOLD = int(req.threshold)
    return _maybe_trigger_retraining()


@app.get("/retrain/status")
def retrain_status():
    return {
        "threshold": RETRAIN_THRESHOLD,
        "pending_feedback": _feedback_pending_count(),
        "state": _retrain_state,
    }


@app.get("/risk-map")
def risk_map(crop: Optional[str] = None):
    rows = []
    if _DB_MODULE and db_available():
        try:
            with get_cursor() as cur:
                if crop:
                    cur.execute(
                        """SELECT municipio, AVG(yield_pct) AS avg_yield, COUNT(*) AS samples
                           FROM predicciones
                           WHERE yield_pct IS NOT NULL AND cultivo ILIKE %s
                           GROUP BY municipio
                           ORDER BY municipio""",
                        (crop,),
                    )
                else:
                    cur.execute(
                        """SELECT municipio, AVG(yield_pct) AS avg_yield, COUNT(*) AS samples
                           FROM predicciones
                           WHERE yield_pct IS NOT NULL
                           GROUP BY municipio
                           ORDER BY municipio"""
                    )
                rows = cur.fetchall()
        except Exception:
            rows = []

    if not rows:
        df = pd.DataFrame()
        if _DB_MODULE and db_available():
            df = load_training_dataframe("dataset_v2.csv")
            if df.empty:
                df = load_training_dataframe()
        if df.empty and os.path.exists(os.path.join(BASE_DIR, "data", "datasets", "dataset_v2.csv")):
            df = pd.read_csv(os.path.join(BASE_DIR, "data", "datasets", "dataset_v2.csv"))
        if not df.empty:
            if crop:
                df = df[df["crop"].str.lower() == crop.lower()]
            agg = (
                df.groupby("municipio", as_index=False)
                .agg(avg_yield=("yield_pct", "mean"), samples=("yield_pct", "size"))
            )
            rows = agg.to_dict(orient="records")

    points = []
    for row in rows:
        municipio = row["municipio"]
        avg_yield = float(row["avg_yield"])
        samples = int(row.get("samples", 0))
        score = float(np.clip(100.0 - avg_yield, 0.0, 100.0))
        lat, lon, depto, zona = _resolve_coords(municipio)
        if lat is None or lon is None:
            continue
        points.append({
            "municipio": municipio,
            "lat": lat,
            "lon": lon,
            "depto": depto,
            "zona": zona,
            "avg_yield": round(avg_yield, 1),
            "risk_score": round(score, 1),
            "risk_level": _risk_level_from_score(score),
            "samples": samples,
        })

    points.sort(key=lambda p: p["risk_score"], reverse=True)
    return {
        "crop": crop or "todos",
        "points": points,
        "total": len(points),
    }


@app.get("/agronomy/water-stress")
def agronomy_water_stress(municipio: Optional[str] = None, top: int = 200):
    if not os.path.exists(WATER_STRESS_PATH):
        raise HTTPException(404, "Indice de estres hidrico no disponible. Ejecuta scripts/processing/agronomic_indices.py")
    df = pd.read_csv(WATER_STRESS_PATH)
    if municipio:
        df = df[df["municipio"].str.lower() == municipio.lower()]
    df = df.sort_values(["municipio", "year", "month"]).head(max(1, min(top, 2000)))
    return df.to_dict(orient="records")


@app.get("/agronomy/optimal-conditions/{crop}")
def agronomy_optimal_conditions(crop: str):
    return _build_crop_optimal_payload(crop)


@app.get("/agronomy/sowing-calendar")
def agronomy_sowing_calendar(municipio: Optional[str] = None, crop: Optional[str] = None, top: int = 120):
    if not os.path.exists(SOWING_CALENDAR_PATH):
        raise HTTPException(404, "Calendario de siembra no disponible. Ejecuta scripts/processing/agronomic_indices.py")
    df = pd.read_csv(SOWING_CALENDAR_PATH)
    if municipio:
        df = df[df["municipio"].str.lower() == municipio.lower()]
    if crop:
        df = df[df["crop"].str.lower() == crop.lower()]
    df = df.sort_values(["municipio", "crop", "rank"]).head(max(1, min(top, 3000)))
    return df.to_dict(orient="records")


# ---------------------------------------------------------------------------
# Pronóstico del clima (Open-Meteo)
# ---------------------------------------------------------------------------

_MUNICIPIOS_COORDS = {
    "Chimaltenango":  {"lat": 14.6614, "lon": -90.8197, "altitud_m": 1800},
    "Sacatepequez":   {"lat": 14.5586, "lon": -90.7295, "altitud_m": 1530},
    "Guatemala":      {"lat": 14.6349, "lon": -90.5069, "altitud_m": 1502},
    "Escuintla":      {"lat": 14.3042, "lon": -90.7858, "altitud_m":  346},
    "Santa Rosa":     {"lat": 14.2775, "lon": -90.2997, "altitud_m":  896},
    "Solola":         {"lat": 14.7757, "lon": -91.1825, "altitud_m": 2113},
    "Totonicapan":    {"lat": 14.9167, "lon": -91.3667, "altitud_m": 2500},
    "Quetzaltenango": {"lat": 14.8444, "lon": -91.5181, "altitud_m": 2333},
    "Suchitepequez":  {"lat": 14.5333, "lon": -91.5000, "altitud_m":  372},
    "Retalhuleu":     {"lat": 14.5361, "lon": -91.6861, "altitud_m":  239},
    "San Marcos":     {"lat": 14.9667, "lon": -91.7833, "altitud_m": 2400},
    "Huehuetenango":  {"lat": 15.3197, "lon": -91.4703, "altitud_m": 1901},
    "Quiche":         {"lat": 15.0333, "lon": -91.1500, "altitud_m": 2021},
    "Baja Verapaz":   {"lat": 15.1006, "lon": -90.3158, "altitud_m":  940},
    "Coban":          {"lat": 15.4692, "lon": -90.3797, "altitud_m": 1317},
    "Peten":          {"lat": 16.9333, "lon": -89.8833, "altitud_m":  127},
    "Izabal":         {"lat": 15.7167, "lon": -88.5833, "altitud_m":    2},
    "Zacapa":         {"lat": 14.9717, "lon": -89.5253, "altitud_m":  230},
    "Chiquimula":     {"lat": 14.7992, "lon": -89.5486, "altitud_m":  424},
    "Jalapa":         {"lat": 14.6333, "lon": -89.9833, "altitud_m": 1360},
    "Jutiapa":        {"lat": 14.2833, "lon": -89.8833, "altitud_m":  905},
    "El Progreso":    {"lat": 14.8500, "lon": -90.0667, "altitud_m":  428},
}


def _resolve_weather_coords(municipio: str) -> tuple[str | None, dict | None]:
    requested = _normalize_location_key(municipio)
    for known, coords in _MUNICIPIOS_COORDS.items():
        if _normalize_location_key(known) == requested:
            return known, coords
    for known, meta in MUNICIPIO_CATALOG.items():
        if _normalize_location_key(known) == requested:
            return known, {
                "lat": meta.get("lat"),
                "lon": meta.get("lon"),
                "altitud_m": meta.get("altitud_m"),
            }
    return None, None

_WEATHER_OPEN_METEO = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}"
    "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
    "precipitation_probability_max,relative_humidity_2m_max,"
    "windspeed_10m_max,et0_fao_evapotranspiration"
    "&timezone=America%2FGuatemala&forecast_days=7"
)

_FORECAST_CACHE: dict = {}   # {municipio: (timestamp, data)}
_CACHE_TTL_HOURS = 3
_open_meteo_usage_lock = threading.Lock()


def _read_open_meteo_usage() -> dict:
    if not os.path.exists(OPEN_METEO_USAGE_PATH):
        return {
            "totals": {
                "external_requests": 0,
                "cache_hits": 0,
            },
            "by_day": {},
            "last_request_at": None,
        }
    try:
        with open(OPEN_METEO_USAGE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {
            "totals": {
                "external_requests": 0,
                "cache_hits": 0,
            },
            "by_day": {},
            "last_request_at": None,
        }

    data.setdefault("totals", {})
    data["totals"].setdefault("external_requests", 0)
    data["totals"].setdefault("cache_hits", 0)
    data.setdefault("by_day", {})
    data.setdefault("last_request_at", None)
    return data


def _record_open_meteo_usage(municipio: str, source: str):
    now = datetime.now()
    day_key = now.strftime("%Y-%m-%d")

    with _open_meteo_usage_lock:
        usage = _read_open_meteo_usage()
        usage["last_request_at"] = now.isoformat()

        day_stats = usage["by_day"].setdefault(day_key, {
            "external_requests": 0,
            "cache_hits": 0,
            "by_municipio": {},
        })
        mun_stats = day_stats["by_municipio"].setdefault(municipio, {
            "external_requests": 0,
            "cache_hits": 0,
        })

        if source == "external":
            usage["totals"]["external_requests"] += 1
            day_stats["external_requests"] += 1
            mun_stats["external_requests"] += 1
        elif source == "cache":
            usage["totals"]["cache_hits"] += 1
            day_stats["cache_hits"] += 1
            mun_stats["cache_hits"] += 1

        with open(OPEN_METEO_USAGE_PATH, "w", encoding="utf-8") as f:
            json.dump(usage, f, ensure_ascii=False, indent=2)


@app.get("/admin/open-meteo-usage")
def admin_open_meteo_usage(x_admin_token: Optional[str] = Header(default=None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(401, "Token de administrador invalido")
    return _read_open_meteo_usage()


@app.get("/forecast/{municipio}")
async def get_forecast(municipio: str):
    import urllib.request
    import urllib.error
    from datetime import timedelta

    canonical_municipio, coords = _resolve_weather_coords(municipio)
    if not coords:
        raise HTTPException(404, f"Municipio '{municipio}' no disponible")
    municipio = canonical_municipio

    # Cache simple: evita llamar Open-Meteo en cada render
    cached = _FORECAST_CACHE.get(municipio)
    if cached:
        cached_at, data = cached
        if datetime.now() - cached_at < timedelta(hours=_CACHE_TTL_HOURS):
            _record_open_meteo_usage(municipio, "cache")
            return data

    url = _WEATHER_OPEN_METEO.format(**coords)
    try:
        loop = asyncio.get_event_loop()
        def _fetch():
            with urllib.request.urlopen(url, timeout=10) as r:
                return json.loads(r.read().decode())
        raw = await loop.run_in_executor(None, _fetch)
        _record_open_meteo_usage(municipio, "external")
    except Exception as e:
        raise HTTPException(502, f"Error al contactar Open-Meteo: {e}")

    d   = raw["daily"]

    days = []
    for i in range(7):
        rain      = d["precipitation_sum"][i] or 0.0
        rain_prob = d["precipitation_probability_max"][i] or 0
        eto       = d["et0_fao_evapotranspiration"][i] or 0.0
        tmax      = d["temperature_2m_max"][i]
        tmin      = d["temperature_2m_min"][i]

        if rain > 25 or rain_prob > 75:
            icon, desc = "⛈️", "Lluvia fuerte"
        elif rain > 10 or rain_prob > 50:
            icon, desc = "🌧️", "Lluvia moderada"
        elif rain > 2 or rain_prob > 25:
            icon, desc = "🌦️", "Lluvia leve"
        elif tmax > 30:
            icon, desc = "☀️", "Soleado y caluroso"
        else:
            icon, desc = "🌤️", "Parcialmente nublado"

        days.append({
            "date":      d["time"][i],
            "icon":      icon,
            "desc":      desc,
            "tmax":      tmax,
            "tmin":      tmin,
            "rain_mm":   round(rain, 1),
            "rain_prob": rain_prob,
            "humidity":  d["relative_humidity_2m_max"][i],
            "wind_kmh":  d["windspeed_10m_max"][i],
            "eto_mm":    round(eto, 1),
        })

    total_rain = round(sum(d["rain_mm"] for d in days), 1)
    total_eto  = round(sum(d["eto_mm"]  for d in days), 1)
    rainy_days = sum(1 for d in days if d["rain_mm"] > 3)

    result = {
        "municipio":   municipio,
        "altitud_m":   coords["altitud_m"],
        "generated_at": datetime.now().isoformat(),
        "days": days,
        "summary": {
            "total_rain_mm":         total_rain,
            "total_eto_mm":          total_eto,
            "irrigation_deficit_mm": round(max(0.0, total_eto - total_rain), 1),
            "rainy_days":            rainy_days,
            "avg_tmax":              round(sum(d["tmax"] for d in days) / 7, 1),
            "avg_tmin":              round(sum(d["tmin"] for d in days) / 7, 1),
        },
    }
    _FORECAST_CACHE[municipio] = (datetime.now(), result)
    return result


# ---------------------------------------------------------------------------
# Calculadora de riego y fertilización
# ---------------------------------------------------------------------------

@app.get("/satellite/ndvi/{municipio}")
def get_satellite_ndvi(municipio: str, days_back: int = 21, max_cloud_cover: int = 35, resolution_m: int = 20):
    canonical_municipio, coords = _resolve_weather_coords(municipio)
    if not coords:
        raise HTTPException(404, f"Municipio '{municipio}' no disponible")
    municipio = canonical_municipio

    bounded_days = max(1, min(days_back, 90))
    bounded_clouds = max(0, min(max_cloud_cover, 100))
    bounded_resolution = max(10, min(resolution_m, 60))
    scene_date = datetime.now() - timedelta(days=min(5, bounded_days))

    return {
        "municipio": municipio,
        "coordinates": {
            "lat": coords["lat"],
            "lon": coords["lon"],
            "altitud_m": coords["altitud_m"],
        },
        "configured_for_ndvi": False,
        "request": {
            "days_back": bounded_days,
            "max_cloud_cover": bounded_clouds,
            "resolution_m": bounded_resolution,
        },
        "latest_scene": {
            "datetime": scene_date.isoformat(),
            "cloud_cover": bounded_clouds,
            "platform": "Sentinel-2",
            "thumbnail": None,
        },
        "ndvi": {
            "available": False,
            "latest_mean": None,
            "latest_interval": None,
            "message": (
                "Endpoint satelital disponible en modo local. Configura credenciales CDSE "
                "para descargar escenas y calcular NDVI real."
            ),
        },
    }


_CROP_AGRONOMY = {
    #           target_ph  N_base  N_temp_factor  water_sensitivity
    "Maiz":     {"ph": 6.5, "n_base": 4.0, "n_hot": 1.20, "kc": 1.15},
    "Frijol":   {"ph": 6.2, "n_base": 1.0, "n_hot": 1.00, "kc": 1.10},  # fija N propio
    "Cafe":     {"ph": 6.0, "n_base": 2.5, "n_hot": 1.10, "kc": 0.95},
    "Arroz":    {"ph": 6.0, "n_base": 3.5, "n_hot": 1.15, "kc": 1.20},
    "Papa":     {"ph": 5.8, "n_base": 3.0, "n_hot": 1.10, "kc": 1.15},
    "Tomate":   {"ph": 6.5, "n_base": 5.0, "n_hot": 1.25, "kc": 1.15},
    "Aguacate": {"ph": 6.5, "n_base": 2.0, "n_hot": 1.05, "kc": 0.85},
    "Cacao":    {"ph": 6.5, "n_base": 1.8, "n_hot": 1.05, "kc": 1.00},
}

# 1 cuerda guatemalteca = 0.0439 ha = 439 m²
_CUERDA_HA = 0.0439


class CalculatorRequest(BaseModel):
    crop:             str
    municipio:        str
    current_ph:       float
    current_rainfall: float          # mm caídos esta semana
    temperature:      float          # temperatura media actual °C
    weekly_eto:       Optional[float] = None   # si viene del pronóstico


@app.post("/agronomy/calculator")
def agronomy_calculator(req: CalculatorRequest):
    _CROP_AGRONOMY_DEFAULT = {"ph": 6.2, "n_base": 2.5, "n_hot": 1.10, "kc": 1.00}
    agro = _CROP_AGRONOMY.get(req.crop, _CROP_AGRONOMY_DEFAULT)

    # ── 1. Déficit de riego ─────────────────────────────────────────
    kc  = agro["kc"]
    eto = req.weekly_eto if req.weekly_eto is not None else (
        # Hargreaves simplificado si no viene el pronóstico
        round((0.0023 * (req.temperature + 17.8) * 5) * kc, 1)
    )
    etc              = round(eto * kc, 1)          # ETo × Kc = ETc del cultivo
    deficit_mm       = round(max(0.0, etc - req.current_rainfall), 1)
    applications     = max(0, round(deficit_mm / 15))   # ~15 mm por aplicación
    liters_per_cuerda = round(deficit_mm * 439)          # 1 mm = 1 L/m²

    irrigation = {
        "eto_semana_mm":         round(eto, 1),
        "etc_cultivo_mm":        etc,
        "lluvia_semana_mm":      req.current_rainfall,
        "deficit_mm":            deficit_mm,
        "aplicaciones":          applications,
        "litros_por_cuerda":     liters_per_cuerda,
        "recomendacion":         (
            f"Aplica {deficit_mm} mm de riego ({applications} aplicaciones de ~15 mm cada una). "
            f"Necesitas {liters_per_cuerda:,} litros por cuerda."
            if deficit_mm > 5
            else "No se requiere riego suplementario esta semana. La lluvia cubre la demanda del cultivo."
        ),
    }

    # ── 2. Cal agrícola ─────────────────────────────────────────────
    target_ph = agro["ph"]
    ph_gap    = round(target_ph - req.current_ph, 2)

    if ph_gap > 0.15:
        # ~25 kg cal por 0.1 unidades pH por cuerda (suelos arcillo-limosos Guatemala altiplano)
        lime_kg   = round(ph_gap * 25, 1)
        lime_qq   = round(lime_kg / 46, 2)    # 1 qq ≈ 46 kg
        lime = {
            "accion":          "encalar",
            "ph_actual":       req.current_ph,
            "ph_objetivo":     target_ph,
            "diferencia":      ph_gap,
            "cal_kg_cuerda":   lime_kg,
            "cal_qq_cuerda":   lime_qq,
            "producto":        "Cal dolomítica agrícola (CaCO₃·MgCO₃) — 80% pureza",
            "recomendacion":   (
                f"Aplica {lime_kg} kg ({lime_qq} qq) de cal dolomítica por cuerda. "
                f"Distribuye uniformemente e incorpora con azadón. "
                f"Espera mínimo 30 días antes de sembrar o fertilizar."
            ),
        }
    elif ph_gap < -0.3:
        sulfur_kg = round(abs(ph_gap) * 4.5, 1)
        lime = {
            "accion":          "acidificar",
            "ph_actual":       req.current_ph,
            "ph_objetivo":     target_ph,
            "diferencia":      ph_gap,
            "azufre_kg_cuerda": sulfur_kg,
            "producto":        "Azufre agrícola elemental (S 90%) o sulfato de amonio",
            "recomendacion":   (
                f"El suelo está demasiado alcalino para {req.crop}. "
                f"Aplica {sulfur_kg} kg de azufre elemental por cuerda. "
                f"El efecto es gradual (2-3 meses). Combina con materia orgánica."
            ),
        }
    else:
        lime = {
            "accion":      "ninguna",
            "ph_actual":   req.current_ph,
            "ph_objetivo": target_ph,
            "diferencia":  ph_gap,
            "recomendacion": f"El pH {req.current_ph} está dentro del rango óptimo para {req.crop} (objetivo: {target_ph}). No se requiere corrección.",
        }

    # ── 3. Nitrógeno ────────────────────────────────────────────────
    temp_factor = agro["n_hot"] if req.temperature > 28 else 1.0
    n_kg        = round(agro["n_base"] * temp_factor, 1)
    urea_kg     = round(n_kg / 0.46, 1)      # Urea 46% N
    sulfato_kg  = round(n_kg / 0.21, 1)      # Sulfato de amonio 21% N
    nitrato_kg  = round(n_kg / 0.27, 1)      # Nitrato de calcio 27% N

    nitrogen = {
        "n_kg_por_cuerda":        n_kg,
        "fuentes": {
            "urea_46pct_kg":      urea_kg,
            "sulfato_amonio_21pct_kg": sulfato_kg,
            "nitrato_calcio_27pct_kg": nitrato_kg,
        },
        "factor_temperatura":     temp_factor,
        "fraccionamiento":        "1/3 a la siembra · 1/3 a los 30 días · 1/3 en floración",
        "recomendacion":          (
            f"Aplica {n_kg} kg de N por cuerda ({urea_kg} kg de urea o {sulfato_kg} kg de sulfato de amonio). "
            + (f"Se aplica +{round((temp_factor-1)*100)}% por la temperatura alta ({req.temperature}°C). " if temp_factor > 1 else "")
            + "Fraccionarlo en 3 aplicaciones mejora la eficiencia y reduce pérdidas."
        ),
    }

    return {
        "crop":        req.crop,
        "municipio":   req.municipio,
        "irrigation":  irrigation,
        "lime":        lime,
        "nitrogen":    nitrogen,
    }


@app.get("/recommendations/{cultivo}")
def get_recommendations(cultivo: str,
                        temperatura: Optional[float] = None,
                        precipitacion: Optional[float] = None,
                        humedad: Optional[float] = None,
                        ph_suelo: Optional[float] = None):
    """
    Devuelve recomendaciones para un cultivo filtradas por las condiciones actuales.
    Las recomendaciones de variable='general'|'plaga'|'enfermedad' se incluyen siempre.
    Las demás se filtran según los umbrales y los valores enviados.
    """
    seed_path = os.path.join(BASE_DIR, "data", "seeds", "recomendaciones_cultivo.csv")

    all_rows = []
    if _DB_MODULE and db_available():
        with get_cursor() as cur:
            cur.execute(
                """SELECT id, cultivo, variable, condicion, umbral_min, umbral_max,
                          nivel, icono, titulo, recomendacion, fuente
                   FROM recomendaciones_cultivo
                   WHERE LOWER(cultivo) = LOWER(%s) AND activo = TRUE
                   ORDER BY
                     CASE nivel WHEN 'critica' THEN 1 WHEN 'advertencia' THEN 2 ELSE 3 END,
                     id""",
                (cultivo,),
            )
            all_rows = cur.fetchall()

    if not all_rows and os.path.exists(seed_path):
        df = pd.read_csv(seed_path)
        df = df[df["cultivo"].str.lower() == cultivo.lower()].copy()
        level_order = {"critica": 1, "advertencia": 2, "info": 3}
        df["_sort"] = df["nivel"].map(level_order).fillna(4)
        df = df.sort_values(["_sort", "cultivo"]).drop(columns=["_sort"])
        all_rows = df.where(pd.notnull(df), None).to_dict(orient="records")

    if not all_rows and not (_DB_MODULE and db_available()):
        raise HTTPException(503, "Base de datos no disponible")

    param_map = {
        "temperatura":   temperatura,
        "precipitacion": precipitacion,
        "humedad":       humedad,
        "ph_suelo":      ph_suelo,
    }

    result = []
    for r in all_rows:
        var = r["variable"]
        # Recomendaciones generales: siempre incluir
        if var in ("general", "plaga", "enfermedad"):
            result.append(dict(r))
            continue
        # Recomendaciones de variable: filtrar por umbrales si tenemos el valor
        val = param_map.get(var)
        if val is None:
            continue
        cond    = r["condicion"]
        lo      = r["umbral_min"]
        hi      = r["umbral_max"]
        matches = False
        if cond in ("muy_alto", "alto") and lo is not None:
            matches = val >= lo
        elif cond in ("muy_bajo", "bajo") and hi is not None:
            matches = val <= hi
        if matches:
            result.append(dict(r))

    deduped = []
    seen_recommendations = set()
    seen_condition_variables = set()
    for item in result:
        var = item.get("variable")
        if var in param_map:
            if var in seen_condition_variables:
                continue
            seen_condition_variables.add(var)

        key = " ".join((item.get("recomendacion") or "").casefold().split())
        if key and key in seen_recommendations:
            continue
        if key:
            seen_recommendations.add(key)
        deduped.append(item)

    return deduped


@app.get("/dataset")
def get_dataset():
    if _DB_MODULE and db_available():
        df = load_training_dataframe("dataset_v2.csv")
        if df.empty:
            df = load_training_dataframe()
        if not df.empty:
            return df.head(200).to_dict(orient="records")
    if not os.path.exists(DATASET_PATH):
        raise HTTPException(404, "Dataset no encontrado. Ejecuta: python generate_dataset.py")
    return pd.read_csv(DATASET_PATH).head(200).to_dict(orient="records")


# ---------------------------------------------------------------------------
# Endpoints — CSV Upload
# ---------------------------------------------------------------------------

@app.post("/upload-dataset")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Sube un CSV con datos de cultivos. Columnas requeridas:
    municipio, crop, temperature, rainfall, humidity, soil_ph
    Columnas opcionales: month, soil_moisture, yield_pct
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Solo se aceptan archivos .csv")

    content = await file.read()
    try:
        df = pd.read_csv(io.StringIO(content.decode("utf-8")))
    except Exception as e:
        raise HTTPException(400, f"Error al leer CSV: {e}")

    # Normalizar nombres de columnas
    df.columns = [CSV_COL_MAP.get(c.lower().strip().replace(" ", "_"), c.lower()) for c in df.columns]

    required = {"municipio", "crop", "temperature", "rainfall", "humidity", "soil_ph"}
    missing  = required - set(df.columns)
    if missing:
        raise HTTPException(400, f"Columnas faltantes: {missing}. Descarga la plantilla en /dataset-template")

    # Añadir columnas opcionales con valores por defecto
    if "year"          not in df.columns: df["year"]          = datetime.now().year
    if "month"         not in df.columns: df["month"]         = datetime.now().month
    if "soil_moisture" not in df.columns: df["soil_moisture"] = 0.28
    if "yield_pct"     not in df.columns: df["yield_pct"]     = None

    # Guardar en uploads con timestamp
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(UPLOADS_DIR, f"upload_{ts}_{file.filename}")
    df.to_csv(out_path, index=False)

    if _DB_MODULE and db_available():
        try:
            upsert_dataset_registered(
                filename=os.path.basename(out_path),
                tipo="Carga manual",
                origen="Upload",
                periodo=f"{int(df['year'].min())}-{int(df['year'].max())}" if "year" in df.columns else "Estatico",
                total_filas=len(df),
                total_columnas=len(df.columns),
                columnas=list(df.columns),
                metadata={
                    "municipios": int(df["municipio"].nunique()) if "municipio" in df.columns else None,
                    "cultivos": int(df["crop"].nunique()) if "crop" in df.columns else None,
                    "tamanio": _human_size(os.path.getsize(out_path)),
                    "ruta": out_path,
                },
                activo=False,
            )
        except Exception:
            pass

    return {
        "message":  f"CSV importado correctamente: {len(df)} registros",
        "rows":     len(df),
        "columns":  list(df.columns),
        "saved_as": os.path.basename(out_path),
        "preview":  df.head(3).to_dict(orient="records"),
    }


@app.get("/dataset-template")
def dataset_template():
    """Descarga una plantilla CSV con las columnas correctas y 3 filas de ejemplo."""
    rows = [
        ["municipio",      "crop",   "year", "month", "temperature", "rainfall", "humidity", "soil_ph", "soil_moisture", "yield_pct"],
        ["Chimaltenango",  "Maiz",   2025,   7,       22.0,          95.0,       74.0,       6.3,       0.31,            None],
        ["Sacatepequez",   "Cafe",   2025,   8,       20.0,          140.0,      82.0,       5.9,       0.38,            None],
        ["Guatemala",      "Tomate", 2025,   3,       26.0,          40.0,       64.0,       6.7,       0.24,            None],
    ]
    buf = io.StringIO()
    csv.writer(buf).writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=plantilla_agroclima.csv"},
    )


# ---------------------------------------------------------------------------
# Endpoints — Arduino
# ---------------------------------------------------------------------------

@app.get("/arduino/status")
def arduino_status():
    return {
        "connected":    arduino_reader.connected,
        "port":         arduino_reader.port,
        "last_reading": arduino_reader.last_reading,
        "error":        arduino_reader.error_msg,
        "ports":        arduino_reader.list_ports(),
        "config":       _arduino_config,
    }


@app.post("/arduino/connect")
def arduino_connect(req: ArduinoConnectRequest):
    if arduino_reader.connected:
        return {"message": "Arduino ya está conectado.", "port": arduino_reader.port}
    arduino_reader.baud_rate = req.baud_rate
    ok = arduino_reader.start(req.port)
    if not ok:
        raise HTTPException(503, f"No se pudo conectar: {arduino_reader.error_msg}")
    return {"message": f"Arduino conectado en {arduino_reader.port}", "port": arduino_reader.port}


@app.post("/arduino/disconnect")
def arduino_disconnect():
    arduino_reader.stop()
    return {"message": "Arduino desconectado."}


@app.post("/arduino/config")
def arduino_config(req: ArduinoConfigRequest):
    """Actualiza el cultivo/municipio para las predicciones en tiempo real."""
    _arduino_config["municipio"] = req.municipio
    _arduino_config["crop"]      = req.crop
    return {"message": "Configuración actualizada.", "config": _arduino_config}


@app.post("/arduino/simulate")
async def arduino_simulate(req: SimulateRequest):
    """Envía una lectura simulada al WebSocket (para probar sin hardware)."""
    total = req.color_r + req.color_g + req.color_b
    greenness = round((req.color_g / total * 100) if total > 0 else 50.0, 1)
    data = {
        "temperature":   req.temperature,
        "light_lux":     req.light_lux,
        "color_r":       req.color_r,
        "color_g":       req.color_g,
        "color_b":       req.color_b,
        "greenness_idx": greenness,
        "soil_moisture": req.soil_moisture,
        "humidity":      req.humidity,
        "rainfall":      req.rainfall,
        "soil_ph":       req.soil_ph,
        "timestamp":     datetime.now().isoformat(),
    }
    _on_arduino_data(data)
    return {"message": "Lectura simulada enviada.", "data": data}


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Endpoint — Alertas manuales
# ---------------------------------------------------------------------------

class AlertCheckRequest(BaseModel):
    municipio:     str
    crop:          str
    temperature:   float
    soil_moisture: float
    light_lux:     float           = 20000
    greenness_idx: float           = 65
    humidity:      float           = 70.0
    rainfall:      float           = 0.0
    soil_ph:       float           = 6.5

@app.post("/alerts/check")
def alerts_check(req: AlertCheckRequest):
    """Evalúa sensores contra rangos óptimos y devuelve alertas con recomendaciones."""
    sensors = req.model_dump()
    sensors.pop("municipio")
    sensors.pop("crop")
    return {"alerts": check_alerts(sensors, req.crop), "crop": req.crop}


@app.get("/alerts/recommendations")
def alerts_recommendations(variable: str = None, condition: str = None, crop: str = None):
    """Lista recomendaciones del dataset filtradas opcionalmente."""
    import pandas as pd
    recs_path = os.path.join(BASE_DIR, "data", "datasets", "recommendations.csv")
    if not os.path.exists(recs_path):
        raise HTTPException(404, "Ejecuta: python recommendations_dataset.py")
    df = pd.read_csv(recs_path)
    if variable:  df = df[df["variable"]  == variable]
    if condition: df = df[df["condition"] == condition]
    if crop:      df = df[(df["crop"] == crop) | (df["crop"] == "Todos")]
    return df.to_dict(orient="records")


# ---------------------------------------------------------------------------
# WebSocket — Stream en tiempo real
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Endpoints — Admin (requieren X-Admin-Token)
# ---------------------------------------------------------------------------

def _check_admin(x_admin_token: str = Header(None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(403, "Token de administrador invalido.")


class EmailConfigRequest(BaseModel):
    email_to:      str
    cultivo:       Optional[str] = None
    severidad_min: str = "severo"
    activo:        bool = True


@app.get("/admin/email-config")
def admin_get_email_config(x_admin_token: str = Header(None)):
    _check_admin(x_admin_token)
    import email_notifier as _en
    status = {
        "configured":    email_configured(),
        "smtp_host":     _en.SMTP_HOST,
        "smtp_port":     _en.SMTP_PORT,
        "smtp_user":     _en.SMTP_USER,
        "email_from":    _en.EMAIL_FROM,
        "email_to":      _en.EMAIL_TO_RAW,
        "cooldown_min":  _en.COOLDOWN_MINUTES,
    }
    if _DB_MODULE and db_available():
        with get_cursor() as cur:
            cur.execute("SELECT * FROM email_config ORDER BY id")
            status["db_configs"] = cur.fetchall()
            cur.execute(
                """SELECT timestamp, cultivo, municipio, variables, destinatarios, ok, error_msg
                   FROM email_log ORDER BY timestamp DESC LIMIT 20"""
            )
            status["recent_log"] = cur.fetchall()
    return status


@app.post("/admin/email-config")
def admin_save_email_config(req: EmailConfigRequest,
                             x_admin_token: str = Header(None)):
    _check_admin(x_admin_token)
    if not (_DB_MODULE and db_available()):
        raise HTTPException(503, "Base de datos no disponible")
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO email_config (email_to, cultivo, severidad_min, activo)
               VALUES (%s, %s, %s, %s) RETURNING id""",
            (req.email_to, req.cultivo, req.severidad_min, req.activo),
        )
        new_id = cur.fetchone()["id"]
    # Actualizar variable de entorno en tiempo de ejecución
    import email_notifier as _en
    _en.EMAIL_TO_RAW = req.email_to
    os.environ["ALERT_EMAIL_TO"] = req.email_to
    return {"ok": True, "id": new_id}


@app.post("/admin/email-test")
def admin_test_email(x_admin_token: str = Header(None)):
    """Envía un correo de prueba para verificar la configuración SMTP."""
    _check_admin(x_admin_token)
    if not email_configured():
        raise HTTPException(400, "Correo no configurado. Define SMTP_USER, SMTP_PASSWORD y ALERT_EMAIL_TO en el archivo .env")
    import email_notifier as _en
    fake_alert = [{
        "variable":    "temperature",
        "condition":   "alto",
        "value":       38.5,
        "optimal_min": 20.0,
        "optimal_max": 28.0,
        "severity":    "severo",
        "action":      "Este es un correo de prueba de AgroClima GT.",
    }]
    # Forzar envío sin cooldown
    result = _en._build_html(fake_alert, "Prueba", "Chimaltenango", {}, datetime.now().strftime("%d/%m/%Y %H:%M"))
    try:
        import smtplib, ssl
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "✅ AgroClima GT — Correo de prueba"
        msg["From"]    = _en.EMAIL_FROM
        msg["To"]      = ", ".join(_en._get_recipients())
        msg.attach(MIMEText(result, "html", "utf-8"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP(_en.SMTP_HOST, _en.SMTP_PORT) as server:
            server.starttls(context=ctx)
            server.login(_en.SMTP_USER, _en.SMTP_PASSWORD)
            server.sendmail(_en.EMAIL_FROM, _en._get_recipients(), msg.as_string())
        return {"ok": True, "message": f"Correo de prueba enviado a: {_en.EMAIL_TO_RAW}"}
    except Exception as e:
        raise HTTPException(500, f"Error SMTP: {e}")


@app.post("/admin/retrain")
async def trigger_retrain(x_admin_token: str = Header(None)):
    """Lanza reentrenamiento del modelo XGBoost en segundo plano."""
    _check_admin(x_admin_token)
    script = os.path.join(BASE_DIR, "scripts", "training", "model_xgboost.py")
    if not os.path.exists(script):
        raise HTTPException(500, "Script de entrenamiento no encontrado")
    loop = asyncio.get_event_loop()
    def _run():
        proc = subprocess.Popen(
            [sys.executable, script, "train"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=BASE_DIR,
        )
        return proc.pid
    pid = await loop.run_in_executor(None, _run)
    return {"message": f"Reentrenamiento iniciado (PID {pid}). El modelo se actualizara en varios minutos.", "pid": pid}


def _read_model_comparison_payload():
    if os.path.exists(COMPARISON_PATH):
        with open(COMPARISON_PATH) as f:
            return json.load(f)
    return {
        "compared_at": None,
        "n_train": 51948,
        "n_test":  12987,
        "n_features": 16,
        "results": {
            "XGBoost": {
                "r2": 0.6833, "mae": 4.98, "rmse": 6.24,
                "crossval_r2": 0.6784, "crossval_std": 0.0028,
                "train_time_s": None,
            },
            "RandomForest": None,
        },
        "note": "Ejecuta 'python model_xgboost.py compare' para generar la comparacion completa.",
    }


def _read_active_model_row():
    if not db_available():
        return None
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT nombre, version, dataset_usado, n_filas, n_features, r2_test, mae, rmse,
                       crossval_r2, crossval_std, hiperparametros, activo, fecha_entrenamiento
                FROM modelos_ml
                WHERE activo = TRUE
                ORDER BY fecha_entrenamiento DESC
                LIMIT 1
                """
            )
            return cur.fetchone()
    except Exception:
        return None


def _read_training_summary(dataset_name: str | None = None):
    if not db_available():
        return {}
    try:
        with get_cursor() as cur:
            if dataset_name:
                cur.execute(
                    """
                    SELECT COUNT(*) AS total_rows,
                           COUNT(DISTINCT cultivo) AS n_crops,
                           COUNT(DISTINCT municipio) AS n_municipalities,
                           MIN(anio) AS min_year,
                           MAX(anio) AS max_year
                    FROM dataset_entrenamiento
                    WHERE dataset_nombre = %s
                    """,
                    (dataset_name,),
                )
                row = cur.fetchone()
                if row and row["total_rows"]:
                    return row
            cur.execute(
                """
                SELECT COUNT(*) AS total_rows,
                       COUNT(DISTINCT cultivo) AS n_crops,
                       COUNT(DISTINCT municipio) AS n_municipalities,
                       MIN(anio) AS min_year,
                       MAX(anio) AS max_year
                FROM dataset_entrenamiento
                """
            )
            return cur.fetchone() or {}
    except Exception:
        return {}


def _infer_feature_order(model):
    importances = getattr(model, "feature_importances_", None)
    n_importances = int(len(importances)) if importances is not None else 0
    if n_importances <= 0:
        return []
    if n_importances == 13:
        return FEATURES[:13]
    if n_importances <= len(FEATURES):
        return FEATURES[:n_importances]
    return FEATURES + [f"feature_{i}" for i in range(len(FEATURES), n_importances)]


def _build_feature_importance_payload(model):
    feature_names = _infer_feature_order(model)
    importances = getattr(model, "feature_importances_", None)
    if importances is None or not len(feature_names):
        return []
    rows = []
    for feature, imp in zip(feature_names, importances):
        meta = MODEL_FEATURE_META.get(feature, {})
        rows.append({
            "feature": feature,
            "label": meta.get("label", feature),
            "imp": round(float(imp), 6),
            "group": meta.get("group", "otros"),
            "source": meta.get("source", "Modelo"),
        })
    rows.sort(key=lambda item: item["imp"], reverse=True)
    return rows


def _build_model_info_payload():
    comparison = _read_model_comparison_payload()
    comparison_xgb = (comparison.get("results") or {}).get("XGBoost") or {}
    active_row = _read_active_model_row() or {}

    trained_at = active_row.get("fecha_entrenamiento")
    dataset_name = active_row.get("dataset_usado")
    summary = _read_training_summary(dataset_name)

    model_name = active_row.get("nombre") or "XGBoost Yield Predictor"
    version = active_row.get("version") or "sin version"
    total_rows = active_row.get("n_filas") or summary.get("total_rows") or comparison.get("n_train")
    n_features = active_row.get("n_features") or comparison.get("n_features") or len(FEATURES)
    train_samples = comparison.get("n_train")
    test_samples = comparison.get("n_test")
    if not train_samples and total_rows:
        train_samples = int(round(total_rows * 0.8))
    if not test_samples and total_rows:
        test_samples = int(total_rows) - int(train_samples or 0)

    years_range = None
    if summary.get("min_year") and summary.get("max_year"):
        years_range = f"{summary['min_year']}-{summary['max_year']}"

    feature_importance = []
    model_loaded = False
    model_file_mtime = None
    if os.path.exists(MODEL_PATH):
        try:
            model, _ = get_model()
            feature_importance = _build_feature_importance_payload(model)
            model_loaded = True
        except Exception:
            feature_importance = []
        try:
            model_file_mtime = datetime.fromtimestamp(os.path.getmtime(MODEL_PATH)).isoformat()
        except Exception:
            model_file_mtime = None

    return {
        "model": {
            "name": model_name,
            "version": version,
            "status": "Activo" if os.path.exists(MODEL_PATH) else "No disponible",
            "dataset": dataset_name or ("dataset_openmeteo.csv" if os.path.exists(DATASET_OM_PATH) else "dataset_preliminar.csv"),
            "trained_at": trained_at.isoformat() if trained_at else model_file_mtime,
            "r2": active_row.get("r2_test", comparison_xgb.get("r2")),
            "mae": active_row.get("mae", comparison_xgb.get("mae")),
            "rmse": active_row.get("rmse", comparison_xgb.get("rmse")),
            "crossValR2": active_row.get("crossval_r2", comparison_xgb.get("crossval_r2")),
            "crossValStd": active_row.get("crossval_std", comparison_xgb.get("crossval_std")),
            "trainSamples": train_samples,
            "testSamples": test_samples,
            "totalRows": total_rows,
            "nFeatures": n_features,
            "nCrops": summary.get("n_crops"),
            "coveredMunicipalities": summary.get("n_municipalities"),
            "yearsRange": years_range,
            "hyperparams": active_row.get("hiperparametros") or {},
            "featureImportance": feature_importance,
            "modelLoaded": model_loaded,
        },
        "retraining": _retrain_state,
        "comparison": comparison,
    }


def _human_size(num_bytes: int | None):
    if not num_bytes:
        return "0 B"
    size = float(num_bytes)
    units = ["B", "KB", "MB", "GB"]
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{num_bytes} B"


def _infer_dataset_type(filename: str):
    name = filename.lower()
    if "recommend" in name:
        return "Recomendaciones"
    if "openmeteo" in name:
        return "Entrenamiento Open-Meteo"
    if "preliminar" in name:
        return "Entrenamiento preliminar"
    if "dataset_v2" in name:
        return "Entrenamiento v2"
    if "optimal" in name:
        return "Referencia agronomica"
    if name.startswith("upload_"):
        return "Carga manual"
    return "Dataset"


def _infer_source_category(filename: str):
    name = filename.lower()
    if "era5" in name:
        return "ERA5-Land"
    if "nasa" in name:
        return "NASA POWER"
    if "soilgrid" in name:
        return "SoilGrids"
    if "insivumeh" in name:
        return "INSIVUMEH"
    if "openmeteo" in name or "open_meteo" in name:
        return "Open-Meteo"
    return "Fuente"


def _normalize_header(name: str):
    return CSV_COL_MAP.get(name.lower().strip().replace(" ", "_"), name.lower().strip().replace(" ", "_"))


def _profile_csv_file(path: str):
    total_rows = 0
    columns = []
    municipios = set()
    cultivos = set()
    years = []

    with open(path, "r", encoding="utf-8", errors="ignore", newline="") as fh:
        reader = csv.reader(fh)
        raw_header = next(reader, [])
        columns = [_normalize_header(col) for col in raw_header]
        idx = {col: pos for pos, col in enumerate(columns)}

        for row in reader:
            if not row:
                continue
            total_rows += 1
            if "municipio" in idx and idx["municipio"] < len(row):
                value = row[idx["municipio"]].strip()
                if value:
                    municipios.add(value)
            if "crop" in idx and idx["crop"] < len(row):
                value = row[idx["crop"]].strip()
                if value:
                    cultivos.add(value)
            if "year" in idx and idx["year"] < len(row):
                value = row[idx["year"]].strip()
                if value:
                    try:
                        years.append(int(float(value)))
                    except Exception:
                        pass

    period = f"{min(years)}-{max(years)}" if years else "Estatico"
    return {
        "total_rows": total_rows,
        "total_columns": len(columns),
        "columns": columns,
        "municipios": len(municipios) or None,
        "cultivos": len(cultivos) or None,
        "periodo": period,
    }


def _scan_inventory_dir(directory: str, inventory_type: str, active_dataset: str | None = None):
    if not os.path.isdir(directory):
        return []
    rows = []
    for entry in sorted(os.scandir(directory), key=lambda item: item.name.lower()):
        if not entry.is_file() or not entry.name.lower().endswith(".csv"):
            continue
        profile = _profile_csv_file(entry.path)
        payload = {
            "nombre_archivo": entry.name,
            "periodo": profile["periodo"],
            "total_filas": profile["total_rows"],
            "total_columnas": profile["total_columns"],
            "columnas": profile["columns"],
            "metadata": {
                "municipios": profile["municipios"],
                "cultivos": profile["cultivos"],
                "tamanio": _human_size(entry.stat().st_size),
                "ruta": entry.path,
            },
            "fecha_carga": datetime.fromtimestamp(entry.stat().st_mtime).isoformat(),
            "activo": entry.name == active_dataset if inventory_type == "dataset" else False,
            "_from_scan": True,
        }
        if inventory_type == "dataset":
            payload.update({
                "tipo": _infer_dataset_type(entry.name),
                "origen": "Filesystem",
            })
        elif inventory_type == "source":
            payload.update({
                "categoria": _infer_source_category(entry.name),
            })
        rows.append(payload)
    return rows


def _build_admin_datasets_payload():
    active_row = _read_active_model_row() or {}
    active_dataset = active_row.get("dataset_usado")
    db_payload = {"datasets": [], "sources": []}

    if _DB_MODULE and db_available():
        try:
            db_payload = get_registered_datasets()
        except Exception:
            db_payload = {"datasets": [], "sources": []}

    datasets = db_payload.get("datasets") or _scan_inventory_dir(DATASETS_DIR, "dataset", active_dataset=active_dataset)
    sources = db_payload.get("sources") or _scan_inventory_dir(SOURCES_DIR, "source")
    uploads = _scan_inventory_dir(UPLOADS_DIR, "dataset")

    return {
        "datasets": datasets,
        "sources": sources,
        "uploads": uploads,
        "active_dataset": active_dataset,
        "db_available": bool(_DB_MODULE and db_available()),
    }


@app.get("/admin/compare-models")
def compare_models(x_admin_token: str = Header(None)):
    """Devuelve comparativa XGBoost vs Random Forest."""
    _check_admin(x_admin_token)
    return _read_model_comparison_payload()


@app.get("/admin/model-info")
def admin_model_info(x_admin_token: str = Header(None)):
    """Devuelve metadata operativa del modelo activo y el estado de reentrenamiento."""
    _check_admin(x_admin_token)
    return _build_model_info_payload()


@app.post("/admin/compare-models")
def run_compare_models(x_admin_token: str = Header(None)):
    """Ejecuta la comparacion formal entre XGBoost y Random Forest y devuelve el resultado."""
    _check_admin(x_admin_token)
    script = os.path.join(BASE_DIR, "scripts", "training", "model_xgboost.py")
    if not os.path.exists(script):
        raise HTTPException(500, "Script de comparacion no encontrado")

    proc = subprocess.run(
        [sys.executable, script, "compare"],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise HTTPException(500, (proc.stderr or proc.stdout or "No se pudo ejecutar la comparacion")[-1200:])

    return _read_model_comparison_payload()


@app.get("/admin/stats")
def admin_stats(x_admin_token: str = Header(None)):
    _check_admin(x_admin_token)
    db_ok = _DB_MODULE and db_available()
    stats = {
        "predicciones": 0,
        "lecturas_arduino": 0,
        "alertas": 0,
        "modelo_activo": None,
        "ultimas_predicciones": [],
    }
    if db_ok:
        try:
            with get_cursor() as cur:
                cur.execute("SELECT COUNT(*) AS n FROM predicciones")
                stats["predicciones"] = cur.fetchone()["n"]
                cur.execute("SELECT COUNT(*) AS n FROM lecturas_arduino")
                stats["lecturas_arduino"] = cur.fetchone()["n"]
                cur.execute("SELECT COUNT(*) AS n FROM alertas")
                stats["alertas"] = cur.fetchone()["n"]
                cur.execute("SELECT version FROM modelos_ml WHERE activo = TRUE ORDER BY fecha_entrenamiento DESC LIMIT 1")
                row = cur.fetchone()
                if row:
                    stats["modelo_activo"] = row["version"]
                cur.execute(
                    """SELECT id, timestamp, municipio, cultivo, yield_pct, yield_level, fuente
                       FROM predicciones
                       ORDER BY timestamp DESC
                       LIMIT 5"""
                )
                rows = [dict(r) for r in cur.fetchall()]
                for row in rows:
                    if row.get("timestamp"):
                        row["timestamp"] = row["timestamp"].isoformat()
                stats["ultimas_predicciones"] = rows
        except Exception:
            pass
    return stats


@app.get("/admin/predictions")
def admin_predictions(
    page: int | None = None, page_size: int | None = None,
    limit: int | None = None, offset: int | None = None,
    municipio: str = None, cultivo: str = None,
    start_date: str | None = None, end_date: str | None = None,
    x_admin_token: str = Header(None),
):
    _check_admin(x_admin_token)
    if not (_DB_MODULE and db_available()):
        raise HTTPException(503, "Base de datos no disponible.")
    if limit is not None or offset is not None:
        page_size = limit or 20
        offset = offset or 0
    else:
        page = page or 1
        page_size = page_size or 20
        offset = (page - 1) * page_size
    filters, params = [], []
    if municipio:
        filters.append("municipio ILIKE %s"); params.append(f"%{municipio}%")
    if cultivo:
        filters.append("cultivo ILIKE %s");   params.append(f"%{cultivo}%")
    if start_date:
        filters.append("timestamp::date >= %s"); params.append(start_date)
    if end_date:
        filters.append("timestamp::date <= %s"); params.append(end_date)
    where = ("WHERE " + " AND ".join(filters)) if filters else ""
    with get_cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS n FROM predicciones {where}", params)
        total = cur.fetchone()["n"]
        cur.execute(
            f"SELECT * FROM predicciones {where} ORDER BY timestamp DESC LIMIT %s OFFSET %s",
            params + [page_size, offset],
        )
        rows = [dict(r) for r in cur.fetchall()]
    for r in rows:
        if r.get("timestamp"):
            r["timestamp"] = r["timestamp"].isoformat()
    current_page = (offset // page_size) + 1 if page_size else 1
    return {"total": total, "page": current_page, "page_size": page_size, "items": rows}


@app.get("/admin/readings")
def admin_readings(
    page: int | None = None, page_size: int | None = None,
    limit: int | None = None, offset: int | None = None,
    x_admin_token: str = Header(None),
):
    _check_admin(x_admin_token)
    if not (_DB_MODULE and db_available()):
        raise HTTPException(503, "Base de datos no disponible.")
    if limit is not None or offset is not None:
        page_size = limit or 20
        offset = offset or 0
    else:
        page = page or 1
        page_size = page_size or 20
        offset = (page - 1) * page_size
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM lecturas_arduino")
        total = cur.fetchone()["n"]
        cur.execute(
            "SELECT * FROM lecturas_arduino ORDER BY timestamp DESC LIMIT %s OFFSET %s",
            [page_size, offset],
        )
        rows = [dict(r) for r in cur.fetchall()]
    for r in rows:
        if r.get("timestamp"):
            r["timestamp"] = r["timestamp"].isoformat()
    current_page = (offset // page_size) + 1 if page_size else 1
    return {"total": total, "page": current_page, "page_size": page_size, "items": rows}


@app.get("/admin/datasets")
def admin_datasets(x_admin_token: str = Header(None)):
    _check_admin(x_admin_token)
    return _build_admin_datasets_payload()


# ---------------------------------------------------------------------------
# WebSocket — Stream en tiempo real
# ---------------------------------------------------------------------------

@app.websocket("/ws/arduino")
async def websocket_arduino(ws: WebSocket):
    await ws_manager.connect(ws)
    # Enviar el último dato disponible al conectarse
    if arduino_reader.last_reading:
        await ws.send_json({"sensors": arduino_reader.last_reading, "prediction": None})
    try:
        while True:
            # Recibir config desde el frontend (crop/municipio)
            msg = await ws.receive_json()
            if "municipio" in msg and "crop" in msg:
                _arduino_config["municipio"] = msg["municipio"]
                _arduino_config["crop"]      = msg["crop"]
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
