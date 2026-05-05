"""
Analitica avanzada para AgroClima GT:
- Explicabilidad SHAP para XGBoost
- Intervalos de confianza para predicciones
- Comparacion multi-cultivo
- Deteccion de anomalias (Isolation Forest)
- Monitoreo de data drift vs distribucion de entrenamiento
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from xgboost import DMatrix

try:
    import shap  # type: ignore
except Exception:
    shap = None

BASE_DIR = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE_DIR, "data", "models")
DATASET_DIR = os.path.join(BASE_DIR, "data", "datasets")

ANOMALY_MODEL_PATH = os.path.join(MODEL_DIR, "isolation_forest_sensor.joblib")
ANOMALY_META_PATH = os.path.join(MODEL_DIR, "isolation_forest_sensor_meta.json")
DRIFT_PROFILE_PATH = os.path.join(MODEL_DIR, "drift_profile.json")

FEATURES = [
    "municipio_enc", "crop_enc", "month",
    "temperature", "rainfall", "humidity",
    "soil_ph", "soil_moisture", "light_lux", "greenness_idx",
    "swvl2", "swvl3", "soil_temp",
    "temp_max", "temp_min", "wind_speed",
    "altitud_m",
]

SENSOR_FEATURES = [
    "temperature", "rainfall", "humidity", "soil_ph", "soil_moisture",
    "light_lux", "greenness_idx", "swvl2", "swvl3", "soil_temp",
    "temp_max", "temp_min", "wind_speed", "altitud_m",
]

FEATURE_LABELS = {
    "temperature": "temperatura",
    "rainfall": "precipitacion",
    "humidity": "humedad",
    "soil_ph": "pH",
    "soil_moisture": "humedad del suelo",
    "light_lux": "luz",
    "greenness_idx": "indice de verdor",
    "swvl2": "humedad subsuelo (7-28cm)",
    "swvl3": "humedad profunda (28-100cm)",
    "soil_temp": "temperatura del suelo",
    "temp_max": "temperatura maxima",
    "temp_min": "temperatura minima",
    "wind_speed": "viento",
    "altitud_m": "altitud",
    "month": "mes",
    "municipio_enc": "municipio",
    "crop_enc": "cultivo",
}

# Altitudes (m) por municipio — cubre los 22 departamentos del frontend
# y los 61 municipios del dataset de entrenamiento (era5_mensual / openmeteo).
_ALTITUDES: dict[str, float] = {
    # 22 departamentos del frontend
    "Chimaltenango": 1800, "Sacatepequez": 1530, "Guatemala": 1502,
    "Escuintla": 346,  "Santa Rosa": 896,   "Solola": 2113,
    "Totonicapan": 2500, "Quetzaltenango": 2333, "Suchitepequez": 372,
    "Retalhuleu": 239, "San Marcos": 2400,  "Huehuetenango": 1901,
    "Quiche": 2021,   "Baja Verapaz": 940,  "Coban": 1317,
    "Peten": 127,     "Izabal": 2,          "Zacapa": 230,
    "Chiquimula": 424, "Jalapa": 1360,      "Jutiapa": 905,
    "El Progreso": 428,
    # Municipios adicionales del dataset de entrenamiento (era5 / openmeteo)
    "Asuncion Mita": 500, "Ayutla": 50, "Barillas": 1350, "Cahabon": 180,
    "Champerico": 5, "Chicacao": 370, "Chichicastenango": 2070,
    "Chiquimulilla": 152, "Cuilapa": 896, "Flores": 110, "Guanagazapa": 520,
    "Huehuetenango_muni": 1901, "Ixcan": 180, "Jalapa_muni": 1360,
    "La Democracia": 55, "Livingston": 5, "Malacatan": 380,
    "Mazatenango": 372, "Morazan": 780, "Morales": 18, "Nebaj": 1906,
    "Nueva Concepcion": 20, "Palin": 1100, "Panzos": 90, "Patulul": 450,
    "Puerto Barrios": 2, "Puerto San Jose": 2, "Quetzaltenango_muni": 2333,
    "Salamá": 940, "San Cristobal Verapaz": 1430, "San Marcos_muni": 2400,
    "San Pedro Carchá": 1320, "Santa Cruz del Quiche": 2021,
    "Santa Lucia Cotzumalguapa": 356, "Santiago Atitlan": 1592,
    "Sayaxche": 120, "Solola_muni": 2113, "Tecun Uman": 40,
    "Tikal": 250, "Todos Santos Cuchumatan": 2480, "Totonicapan_muni": 2500,
    "Zacapa_muni": 230, "Zunilito": 500,
}


def _get_altitude(municipio: str) -> float:
    """Devuelve la altitud en metros para un municipio. Carga era5_mensual.csv si es necesario."""
    if municipio in _ALTITUDES:
        return _ALTITUDES[municipio]
    # Intento case-insensitive
    lower = municipio.lower()
    for k, v in _ALTITUDES.items():
        if k.lower() == lower:
            return v
    # Fallback: cargar desde era5_mensual.csv una sola vez
    era5_path = os.path.join(BASE_DIR, "data", "sources", "era5_mensual.csv")
    if os.path.exists(era5_path):
        try:
            df_alt = pd.read_csv(era5_path, usecols=["municipio", "altitud_m"])
            row = df_alt[df_alt["municipio"].str.lower() == lower]
            if not row.empty:
                return float(row.iloc[0]["altitud_m"])
        except Exception:
            pass
    return 800.0  # promedio Guatemala si no se encuentra


@dataclass
class PreparedInput:
    row_df: pd.DataFrame
    row_raw: dict[str, Any]


def _load_training_dataframe() -> pd.DataFrame:
    """Carga dataset de entrenamiento desde DB si existe, o desde CSV local."""
    try:
        from database.connection import db_available
        from database.repository import load_training_dataframe

        if db_available():
            df = load_training_dataframe("dataset_v2.csv")
            if not df.empty:
                return df
            df = load_training_dataframe()
            if not df.empty:
                return df
    except Exception:
        pass

    candidate_files = [
        os.path.join(DATASET_DIR, "dataset_v2.csv"),
        os.path.join(DATASET_DIR, "dataset_preliminar.csv"),
    ]
    for path in candidate_files:
        if os.path.exists(path):
            return pd.read_csv(path)
    return pd.DataFrame()


def _safe_encode(label_encoder, value: str) -> int:
    classes = list(label_encoder.classes_)
    if value in classes:
        return int(label_encoder.transform([value])[0])

    # Intento case-insensitive para robustez del frontend.
    val_lower = str(value).lower()
    for known in classes:
        if str(known).lower() == val_lower:
            return int(label_encoder.transform([known])[0])

    # Fallback: usar primera clase conocida para no bloquear la prediccion
    return 0


def _fill_optional_values(payload: dict[str, Any]) -> dict[str, Any]:
    data = dict(payload)
    t = float(data.get("temperature", 22.0))
    sm = float(data.get("soil_moisture", 0.30))

    data.setdefault("rainfall", 0.0)
    data.setdefault("humidity", 70.0)
    data.setdefault("soil_ph", 6.5)
    data.setdefault("light_lux", 20000.0)
    data.setdefault("greenness_idx", 65.0)

    data.setdefault("swvl2", sm + 0.03)
    data.setdefault("swvl3", sm + 0.05)
    data.setdefault("soil_temp", t - 3.0)
    data.setdefault("temp_max", t + 8.0)
    data.setdefault("temp_min", t - 6.0)
    data.setdefault("wind_speed", 2.5)
    data.setdefault("altitud_m", _get_altitude(str(data.get("municipio", ""))))
    return data


def prepare_input_row(payload: dict[str, Any], encoders: dict[str, Any]) -> PreparedInput:
    """Normaliza y codifica un payload para inferencia."""
    data = _fill_optional_values(payload)

    municipio = str(data["municipio"])
    crop = str(data["crop"])

    row = {
        "municipio_enc": _safe_encode(encoders["municipio"], municipio),
        "crop_enc": _safe_encode(encoders["crop"], crop),
        "month": int(data["month"]),
        "temperature": float(data["temperature"]),
        "rainfall": float(data["rainfall"]),
        "humidity": float(data["humidity"]),
        "soil_ph": float(data["soil_ph"]),
        "soil_moisture": float(data["soil_moisture"]),
        "light_lux": float(data["light_lux"]),
        "greenness_idx": float(data["greenness_idx"]),
        "swvl2": float(data["swvl2"]),
        "swvl3": float(data["swvl3"]),
        "soil_temp": float(data["soil_temp"]),
        "temp_max": float(data["temp_max"]),
        "temp_min": float(data["temp_min"]),
        "wind_speed": float(data["wind_speed"]),
        "altitud_m": float(data["altitud_m"]),
    }
    return PreparedInput(row_df=pd.DataFrame([row]), row_raw=data)


def _model_features(model) -> list[str]:
    """Devuelve los feature names con los que fue entrenado el modelo."""
    try:
        names = model.get_booster().feature_names
        if names:
            return names
    except Exception:
        pass
    return FEATURES  # fallback al listado global


def predict_with_interval(model, row_df: pd.DataFrame) -> dict[str, float]:
    """Calcula prediccion puntual e intervalo usando dispersion por arboles."""
    feats = _model_features(model)
    base_pred = float(model.predict(row_df[feats])[0])
    base_pred = float(np.clip(base_pred, 0.0, 100.0))

    preds = []
    try:
        booster = model.get_booster()
        total_rounds = int(booster.num_boosted_rounds())
        step = max(1, total_rounds // 10)
        dmat = DMatrix(row_df[feats])
        for end_round in range(step, total_rounds + 1, step):
            p = float(booster.predict(dmat, iteration_range=(0, end_round))[0])
            preds.append(p)
    except Exception:
        preds = [base_pred]

    sigma = float(np.std(preds)) if len(preds) > 1 else 4.0
    margin = max(1.96 * sigma, 3.5)

    low = float(np.clip(base_pred - margin, 0.0, 100.0))
    high = float(np.clip(base_pred + margin, 0.0, 100.0))
    return {
        "prediction": round(base_pred, 1),
        "low": round(low, 1),
        "high": round(high, 1),
        "margin": round((high - low) / 2, 1),
    }


def explain_prediction_shap(model, row_df: pd.DataFrame, row_raw: dict[str, Any], top_k: int = 4) -> dict[str, Any]:
    """Genera explicacion SHAP y narrativa textual entendible para tesis."""
    feats      = _model_features(model)
    feature_df = row_df[feats]

    values = None
    base_value = None

    try:
        if shap is not None:
            explainer = shap.TreeExplainer(model)
            raw_values = explainer.shap_values(feature_df)
            values = np.array(raw_values[0], dtype=float)
            expected = explainer.expected_value
            base_value = float(expected[0] if isinstance(expected, (list, np.ndarray)) else expected)
        else:
            booster = model.get_booster()
            contrib = booster.predict(DMatrix(feature_df), pred_contribs=True)[0]
            values = np.array(contrib[:-1], dtype=float)
            base_value = float(contrib[-1])
    except Exception:
        values = np.zeros(len(feats), dtype=float)
        base_value = 0.0

    contributions = []
    for i, feat in enumerate(feats):
        impact = float(values[i])
        if feat.endswith("_enc"):
            shown_value = row_raw["municipio"] if feat == "municipio_enc" else row_raw["crop"]
        else:
            shown_value = row_raw.get(feat)
        contributions.append({
            "feature": feat,
            "label": FEATURE_LABELS.get(feat, feat),
            "value": shown_value,
            "impact": round(impact, 2),
            "direction": "positivo" if impact >= 0 else "negativo",
        })

    top = sorted(contributions, key=lambda c: abs(c["impact"]), reverse=True)[:top_k]
    sentences = []
    for c in top:
        direction = "aumento" if c["impact"] >= 0 else "redujo"
        sentences.append(
            f"{c['label'].capitalize()}={c['value']} {direction} el rendimiento en {c['impact']:+.1f} puntos."
        )

    return {
        "base_value": round(float(base_value), 2),
        "top_contributions": top,
        "narrative": " ".join(sentences),
    }


def predict_multicrop(model, encoders: dict[str, Any], payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Predice rendimiento para todos los cultivos del encoder con mismo clima."""
    ranking: list[dict[str, Any]] = []
    crops = list(encoders["crop"].classes_)

    for crop in crops:
        cloned = dict(payload)
        cloned["crop"] = crop
        prepared = prepare_input_row(cloned, encoders)
        interval = predict_with_interval(model, prepared.row_df)

        y = interval["prediction"]
        if y >= 75:
            level = "alto"
        elif y >= 50:
            level = "medio"
        elif y >= 25:
            level = "bajo"
        else:
            level = "critico"

        ranking.append({
            "crop": crop,
            "yield_pct": y,
            "yield_level": level,
            "confidence_low": interval["low"],
            "confidence_high": interval["high"],
        })

    ranking.sort(key=lambda r: r["yield_pct"], reverse=True)
    for idx, item in enumerate(ranking, start=1):
        item["rank"] = idx
    return ranking


def _build_training_matrix(df: pd.DataFrame, encoders: dict[str, Any]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=SENSOR_FEATURES)

    data = df.copy()
    required_cols = {
        "municipio": "Desconocido",
        "crop": "Maiz",
        "month": 6,
        "temperature": 22.0,
        "rainfall": 0.0,
        "humidity": 70.0,
        "soil_ph": 6.5,
        "soil_moisture": 0.30,
        "light_lux": 20000.0,
        "greenness_idx": 65.0,
        "swvl2": 0.33,
        "swvl3": 0.35,
        "soil_temp": 19.0,
        "temp_max": 30.0,
        "temp_min": 16.0,
        "wind_speed": 2.5,
    }
    for col, default in required_cols.items():
        if col not in data.columns:
            data[col] = default

    # Coercion numerica segura.
    for col in SENSOR_FEATURES + ["month"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.dropna(subset=["temperature", "soil_moisture", "humidity"])
    if data.empty:
        return pd.DataFrame(columns=SENSOR_FEATURES)

    for col in SENSOR_FEATURES:
        med = float(data[col].median()) if col in data.columns else 0.0
        data[col] = data[col].fillna(med)

    return data[SENSOR_FEATURES]


def _train_anomaly_and_profile(encoders: dict[str, Any]) -> tuple[IsolationForest, dict[str, Any], dict[str, Any]]:
    os.makedirs(MODEL_DIR, exist_ok=True)

    train_df = _load_training_dataframe()
    X = _build_training_matrix(train_df, encoders)

    if X.empty:
        synthetic = pd.DataFrame([
            {k: v for k, v in {
                "temperature": 24.0,
                "rainfall": 60.0,
                "humidity": 72.0,
                "soil_ph": 6.4,
                "soil_moisture": 0.30,
                "light_lux": 35000.0,
                "greenness_idx": 63.0,
                "swvl2": 0.33,
                "swvl3": 0.35,
                "soil_temp": 20.0,
                "temp_max": 31.0,
                "temp_min": 16.0,
                "wind_speed": 2.5,
            }.items()}
            for _ in range(32)
        ])
        X = synthetic

    model = IsolationForest(
        n_estimators=300,
        contamination=0.05,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X)

    train_scores = model.decision_function(X)
    meta = {
        "score_mean": float(np.mean(train_scores)),
        "score_std": float(np.std(train_scores) + 1e-6),
        "score_p05": float(np.percentile(train_scores, 5)),
        "score_p95": float(np.percentile(train_scores, 95)),
    }

    profile = {
        "features": {
            feat: {
                "mean": float(X[feat].mean()),
                "std": float(X[feat].std(ddof=0) + 1e-6),
                "p05": float(X[feat].quantile(0.05)),
                "p95": float(X[feat].quantile(0.95)),
            }
            for feat in SENSOR_FEATURES
        }
    }

    joblib.dump(model, ANOMALY_MODEL_PATH)
    with open(ANOMALY_META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    with open(DRIFT_PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    return model, meta, profile


def _load_or_train_monitoring(encoders: dict[str, Any]) -> tuple[IsolationForest, dict[str, Any], dict[str, Any]]:
    try:
        if os.path.exists(ANOMALY_MODEL_PATH) and os.path.exists(ANOMALY_META_PATH) and os.path.exists(DRIFT_PROFILE_PATH):
            model = joblib.load(ANOMALY_MODEL_PATH)
            with open(ANOMALY_META_PATH, encoding="utf-8") as f:
                meta = json.load(f)
            with open(DRIFT_PROFILE_PATH, encoding="utf-8") as f:
                profile = json.load(f)
            return model, meta, profile
    except Exception:
        pass

    return _train_anomaly_and_profile(encoders)


def detect_sensor_anomaly(encoders: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Evalua una lectura y detecta si es anomala contra historico."""
    model, meta, _ = _load_or_train_monitoring(encoders)
    data = _fill_optional_values(payload)

    row = pd.DataFrame([{k: float(data[k]) for k in SENSOR_FEATURES}])
    decision = float(model.decision_function(row)[0])
    pred = int(model.predict(row)[0])

    z = (decision - float(meta["score_mean"])) / float(meta["score_std"])
    anomaly_score = float(np.clip(100.0 - (z + 2.0) * 25.0, 0.0, 100.0))

    if pred == -1 or decision <= float(meta["score_p05"]):
        label = "anomalia"
    elif anomaly_score >= 60:
        label = "sospechoso"
    else:
        label = "normal"

    return {
        "label": label,
        "is_anomaly": label == "anomalia",
        "score": round(anomaly_score, 1),
        "decision_function": round(decision, 4),
    }


def compute_data_drift(encoders: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Calcula similitud de entrada vs distribucion de entrenamiento."""
    _, _, profile = _load_or_train_monitoring(encoders)
    data = _fill_optional_values(payload)

    feature_results = []
    similarities = []

    for feat in SENSOR_FEATURES:
        stats = profile["features"][feat]
        val = float(data[feat])
        mean = float(stats["mean"])
        std = float(stats["std"])

        z = abs((val - mean) / std)
        similarity = float(np.clip(100.0 - z * 22.0, 0.0, 100.0))

        if z >= 3.0:
            level = "alto"
        elif z >= 2.0:
            level = "medio"
        else:
            level = "bajo"

        feature_results.append({
            "feature": feat,
            "label": FEATURE_LABELS.get(feat, feat),
            "value": round(val, 3),
            "mean": round(mean, 3),
            "z_score": round(float(z), 2),
            "drift_level": level,
            "similarity": round(similarity, 1),
        })
        similarities.append(similarity)

    overall = float(np.mean(similarities)) if similarities else 0.0
    if overall >= 75:
        status = "estable"
    elif overall >= 55:
        status = "vigilancia"
    else:
        status = "drift_detectado"

    feature_results.sort(key=lambda x: x["similarity"])

    return {
        "similarity_score": round(overall, 1),
        "status": status,
        "features": feature_results,
    }
