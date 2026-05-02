"""
Modelo XGBoost para predicción de rendimiento agrícola (yield_pct).
Features incluyen métricas de sensores físicos DS18B20, TSL2561, TCS3200
y el higrómetro capacitivo.

Uso:
    python model_xgboost.py train
    python model_xgboost.py evaluate
    python model_xgboost.py predict '{
        "municipio":"Chimaltenango","crop":"Maiz","month":7,
        "temperature":22,"rainfall":95,"humidity":74,
        "soil_ph":6.3,"soil_moisture":0.31,
        "light_lux":32000,"greenness_idx":68
    }'
"""

import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBRegressor

sys.path.insert(0, BASE_DIR := os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import db_available
from database.repository import load_training_dataframe, sync_model_metadata

DATASET_PATH    = os.path.join(BASE_DIR, "data", "datasets", "dataset_preliminar.csv")
DATASET_OM_PATH = os.path.join(BASE_DIR, "data", "datasets", "dataset_openmeteo.csv")
MODEL_DIR       = os.path.join(BASE_DIR, "data", "models")
MODEL_PATH      = os.path.join(MODEL_DIR, "xgboost_yield.joblib")
ENCODER_PATH    = os.path.join(MODEL_DIR, "label_encoders.joblib")

# Sensores físicos incluidos como features
# Features base (siempre presentes)
FEATURES = [
    "municipio_enc", "crop_enc", "month",
    "temperature",    # DS18B20
    "rainfall",       # ERA5-Land / manual
    "humidity",       # ERA5-Land / manual
    "soil_ph",        # manual
    "soil_moisture",  # Higrómetro capacitivo (swvl1)
    "light_lux",      # TSL2561
    "greenness_idx",  # TCS3200 → G/(R+G+B)*100
    "swvl2",          # ERA5-Land humedad suelo raíces (7-28 cm)
    "swvl3",          # ERA5-Land humedad suelo profunda (28-100 cm)
    "soil_temp",      # ERA5-Land temperatura suelo 0-7 cm (°C)
]
# Features extra (dataset_v2 — NASA POWER)
FEATURES_EXTRA = [
    "temp_max",       # NASA POWER temperatura máxima mensual (°C)
    "temp_min",       # NASA POWER temperatura mínima mensual (°C)
    "wind_speed",     # NASA POWER viento 2m (m/s)
]
TARGET   = "yield_pct"
CAT_COLS = ["municipio", "crop"]


def load_data() -> pd.DataFrame:
    # 1) Preferir dataset Open-Meteo (mayor cobertura: 61 municipios)
    if os.path.exists(DATASET_OM_PATH):
        df = pd.read_csv(DATASET_OM_PATH)
        print(f"Dataset cargado: dataset_openmeteo.csv ({len(df):,} filas, "
              f"{df['municipio'].nunique()} municipios)")
        return df
    # 2) Fallback: base de datos
    if db_available():
        df = load_training_dataframe("dataset_v2.csv")
        if not df.empty:
            return df
        df = load_training_dataframe()
        if not df.empty:
            return df
    # 3) Fallback final: CSV local
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(
            "No hay dataset disponible. Ejecuta primero:\n"
            "  python scripts/datasets/generate_dataset_openmeteo.py nofit"
        )
    return pd.read_csv(DATASET_PATH)


def encode(df: pd.DataFrame, encoders: dict = None, fit: bool = False):
    df = df.copy()
    if fit:
        encoders = {}
        for col in CAT_COLS:
            le = LabelEncoder()
            df[f"{col}_enc"] = le.fit_transform(df[col].astype(str))
            encoders[col] = le
    else:
        for col in CAT_COLS:
            df[f"{col}_enc"] = encoders[col].transform(df[col].astype(str))
    return df, encoders


def build_model() -> XGBRegressor:
    return XGBRegressor(
        n_estimators=400, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        reg_alpha=0.1, reg_lambda=1.0, random_state=42,
        n_jobs=-1, verbosity=0,
    )


def cmd_train():
    print("=== Entrenamiento XGBoost — Rendimiento Agricola ===\n")
    df = load_data()

    # Usar features extra si están disponibles en el dataset
    active_features = FEATURES + [f for f in FEATURES_EXTRA if f in df.columns]
    print(f"Dataset: {len(df)} registros | Features: {active_features}\n")

    df, encoders = encode(df, fit=True)
    X = df[active_features]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = build_model()
    cv = cross_val_score(model, X_train, y_train, cv=5, scoring="r2", n_jobs=-1)
    print(f"Cross-val R2 (5-fold): {cv.mean():.4f} +/- {cv.std():.4f}")

    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    y_pred = model.predict(X_test)
    print(f"\nResultados en test ({len(X_test)} muestras):")
    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred) ** 0.5
    r2 = r2_score(y_test, y_pred)
    print(f"  MAE  : {mae:.2f} %")
    print(f"  RMSE : {rmse:.2f} %")
    print(f"  R2   : {r2:.4f}")

    importance = pd.Series(model.feature_importances_, index=active_features)
    print("\nImportancia de variables:")
    for feat, imp in importance.sort_values(ascending=False).items():
        bar = "#" * int(imp * 40)
        print(f"  {feat:<18} {imp:.4f}  {bar}")

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(encoders, ENCODER_PATH)
    print(f"\nModelo guardado: {MODEL_PATH}")

    if db_available():
        sync_model_metadata({
            "nombre": "XGBoost",
            "version": "v2.1-db",
            "dataset_usado": "dataset_v2.csv",
            "n_filas": len(df),
            "n_features": len(active_features),
            "r2_test": round(r2, 4),
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "crossval_r2": round(float(cv.mean()), 4),
            "crossval_std": round(float(cv.std()), 4),
            "hiperparametros": {
                "n_estimators": 400,
                "max_depth": 6,
                "learning_rate": 0.05,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "min_child_weight": 3,
                "reg_alpha": 0.1,
                "reg_lambda": 1.0,
            },
        })
        print("Metadata del modelo sincronizada en PostgreSQL.")


def cmd_evaluate():
    model, encoders = joblib.load(MODEL_PATH), joblib.load(ENCODER_PATH)
    df, _ = encode(load_data(), encoders=encoders, fit=False)
    active_features = FEATURES + [f for f in FEATURES_EXTRA if f in df.columns]
    _, X_test, _, y_test = train_test_split(df[active_features], df[TARGET], test_size=0.2, random_state=42)
    y_pred = model.predict(X_test)
    print(f"MAE: {mean_absolute_error(y_test, y_pred):.2f}%  "
          f"RMSE: {mean_squared_error(y_test, y_pred)**0.5:.2f}%  "
          f"R2: {r2_score(y_test, y_pred):.4f}")


def cmd_predict(json_str: str):
    model, encoders = joblib.load(MODEL_PATH), joblib.load(ENCODER_PATH)
    record = json.loads(json_str)
    # Defaults para sensores opcionales
    record.setdefault("light_lux",     20000)
    record.setdefault("greenness_idx", 65)
    record.setdefault("swvl2",         0.35)
    record.setdefault("swvl3",         0.38)
    record.setdefault("soil_temp",     record.get("temperature", 20) - 3)
    df, _ = encode(pd.DataFrame([record]), encoders=encoders, fit=False)
    y = model.predict(df[FEATURES])[0]
    nivel = "ALTO" if y >= 75 else "MEDIO" if y >= 50 else "BAJO" if y >= 25 else "CRITICO"
    print(f"Rendimiento: {y:.1f}%  |  Nivel: {nivel}")
    return y


COMPARE_PATH = os.path.join(MODEL_DIR, "model_comparison.json")

RF_PARAMS = dict(
    n_estimators=300, max_depth=10, min_samples_leaf=3,
    max_features="sqrt", random_state=42, n_jobs=-1,
)


def cmd_compare():
    """Entrena XGBoost y Random Forest sobre el mismo split y guarda métricas comparativas."""
    print("=== Comparacion XGBoost vs Random Forest ===\n")
    df = load_data()
    active_features = FEATURES + [f for f in FEATURES_EXTRA if f in df.columns]
    df, encoders = encode(df, fit=True)
    X = df[active_features]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    models = [
        ("XGBoost",      build_model()),
        ("RandomForest", RandomForestRegressor(**RF_PARAMS)),
    ]

    results = {}
    for name, model in models:
        t0 = datetime.now()
        model.fit(X_train, y_train)
        elapsed = round((datetime.now() - t0).total_seconds(), 1)

        cv = cross_val_score(model, X_train, y_train, cv=5, scoring="r2", n_jobs=-1)
        y_pred = model.predict(X_test)

        results[name] = {
            "r2":           round(float(r2_score(y_test, y_pred)), 4),
            "mae":          round(float(mean_absolute_error(y_test, y_pred)), 2),
            "rmse":         round(float(mean_squared_error(y_test, y_pred) ** 0.5), 2),
            "crossval_r2":  round(float(cv.mean()), 4),
            "crossval_std": round(float(cv.std()), 4),
            "train_time_s": elapsed,
        }
        print(
            f"  {name:<14}  R2={results[name]['r2']:.4f}  "
            f"MAE={results[name]['mae']:.2f}%  RMSE={results[name]['rmse']:.2f}%  "
            f"({elapsed}s)"
        )

    payload = {
        "compared_at": datetime.now().isoformat(),
        "n_train":     len(X_train),
        "n_test":      len(X_test),
        "n_features":  len(active_features),
        "results":     results,
    }
    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(COMPARE_PATH, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nResultados guardados: {COMPARE_PATH}")
    return payload


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "train"
    if cmd == "train":       cmd_train()
    elif cmd == "evaluate":  cmd_evaluate()
    elif cmd == "predict":   cmd_predict(sys.argv[2])
    elif cmd == "compare":   cmd_compare()
    else: print("Opciones: train | evaluate | predict '<json>' | compare")
