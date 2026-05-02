"""
Motor de alertas en tiempo real para AgroClima GT.
Compara lecturas de sensores contra rangos óptimos del cultivo
y devuelve alertas priorizadas con recomendaciones químicas/biológicas.
"""

import os
import pandas as pd

BASE_DIR      = os.path.dirname(__file__)
OPTIMAL_PATH  = os.path.join(BASE_DIR, "data", "processed", "crop_optimal_conditions.csv")
RECS_PATH     = os.path.join(BASE_DIR, "data", "processed", "recommendations.csv")

# Porcentaje de desviación fuera del rango óptimo para cada nivel
SEVERITY_THRESHOLDS = {"leve": 10, "moderado": 25, "severo": 50}

# Qué sensores físicos están disponibles (solo estos se evalúan en tiempo real)
SENSOR_VARIABLE_MAP = {
    "temperature":   ("temp_min",  "temp_max"),
    "light_lux":     ("light_min", "light_max"),
    "soil_moisture": ("sm_min",    "sm_max"),
    "greenness_idx": ("green_min", "green_max"),
    # Opcionales (si vienen de ERA5 o entrada manual)
    "humidity":      ("humidity_min", "humidity_max"),
    "rainfall":      ("rain_min",     "rain_max"),
    "soil_ph":       ("ph_min",       "ph_max"),
}

_optimal_df:  pd.DataFrame = None
_recs_df:     pd.DataFrame = None


def _load():
    global _optimal_df, _recs_df
    if _optimal_df is None:
        if not os.path.exists(OPTIMAL_PATH):
            raise FileNotFoundError("Ejecuta: python crop_reference.py")
        _optimal_df = pd.read_csv(OPTIMAL_PATH)
    if _recs_df is None:
        if not os.path.exists(RECS_PATH):
            raise FileNotFoundError("Ejecuta: python recommendations_dataset.py")
        _recs_df = pd.read_csv(RECS_PATH)


def _severity_from_pct(pct: float) -> str:
    if pct >= SEVERITY_THRESHOLDS["severo"]:   return "severo"
    if pct >= SEVERITY_THRESHOLDS["moderado"]: return "moderado"
    return "leve"


def _find_recommendation(variable: str, condition: str, severity: str, crop: str) -> dict:
    """
    Busca la recomendación más específica disponible:
    1. Crop específico + severidad exacta
    2. Crop específico + cualquier severidad
    3. Genérico (Todos) + severidad exacta
    4. Genérico (Todos) + cualquier severidad
    """
    df = _recs_df
    for crop_filter in [crop, "Todos"]:
        mask = (df["variable"] == variable) & (df["condition"] == condition) & (df["crop"] == crop_filter)
        candidates = df[mask]
        if candidates.empty:
            continue
        # Intentar match exacto de severidad
        exact = candidates[candidates["severity"] == severity]
        row = exact.iloc[0] if not exact.empty else candidates.iloc[0]
        return row.to_dict()
    return {}


def check_alerts(sensors: dict, crop: str) -> list[dict]:
    """
    Evalúa las lecturas de sensores contra los rangos óptimos del cultivo.

    Args:
        sensors: dict con valores de los sensores
                 (temperature, light_lux, soil_moisture, greenness_idx, etc.)
        crop:    nombre del cultivo (debe estar en crop_optimal_conditions.csv)

    Returns:
        Lista de alertas ordenadas por severidad (severo → moderado → leve)
    """
    _load()

    crop_row = _optimal_df[_optimal_df["crop"] == crop]
    if crop_row.empty:
        return []
    params = crop_row.iloc[0].to_dict()

    alerts = []
    for sensor_key, (col_min, col_max) in SENSOR_VARIABLE_MAP.items():
        value = sensors.get(sensor_key)
        if value is None:
            continue
        if col_min not in params or col_max not in params:
            continue

        opt_min = float(params[col_min])
        opt_max = float(params[col_max])
        value   = float(value)

        if value < opt_min:
            condition  = "bajo"
            # % fuera del rango (respecto al ancho del rango óptimo)
            range_span = max(opt_max - opt_min, 1)
            pct_out    = abs(opt_min - value) / range_span * 100
        elif value > opt_max:
            condition  = "alto"
            range_span = max(opt_max - opt_min, 1)
            pct_out    = abs(value - opt_max) / range_span * 100
        else:
            continue  # dentro del rango óptimo → sin alerta

        if pct_out < SEVERITY_THRESHOLDS["leve"]:
            continue  # desviación mínima, no generar alerta

        severity = _severity_from_pct(pct_out)
        rec      = _find_recommendation(sensor_key, condition, severity, crop)

        # Mapeo de nivel UI
        level_map = {"severo": "high", "moderado": "medium", "leve": "low"}

        alerts.append({
            "variable":      sensor_key,
            "condition":     condition,
            "value":         round(value, 2),
            "optimal_min":   opt_min,
            "optimal_max":   opt_max,
            "pct_deviation": round(pct_out, 1),
            "severity":      severity,
            "level":         level_map[severity],
            "problem":       rec.get("problem", f"{sensor_key} {condition} del rango óptimo"),
            "consequence":   rec.get("consequence", ""),
            "action":        rec.get("action", "Revisar condiciones del cultivo"),
            "remedy": {
                "type":        rec.get("remedy_type", ""),
                "name":        rec.get("remedy_name", ""),
                "formula":     rec.get("formula", ""),
                "dose":        rec.get("dose", ""),
                "application": rec.get("application", ""),
                "notes":       rec.get("notes", ""),
            },
            "crop": crop,
        })

    # Ordenar: severo > moderado > leve
    order = {"severo": 0, "moderado": 1, "leve": 2}
    alerts.sort(key=lambda a: order[a["severity"]])
    return alerts
