#!/usr/bin/env python3
"""
seed_database.py — Pobla la DB de AgroClima GT con datos de demostración realistas.

Tablas que se populan:
  municipios          — los 22 departamentos de Guatemala (fix: init.sql solo tenía 3)
  metricas_climaticas — promedios climáticos ERA5-Land por departamento
  predicciones        — 120 predicciones históricas (últimos 90 días)
  lecturas_arduino    — 60 lecturas de sensores simuladas (últimos 30 días)
  alertas             — alertas vinculadas a predicciones con valores extremos
  usuarios            — 1 usuario demo
  model_feedback      — 15 registros de retroalimentación de campo

NOTA: La tabla `cultivos` del esquema no es consultada por api.py
(la app usa crop_optimal_conditions.csv en su lugar). Se omite del seed.

Uso:
    python scripts/seed_database.py           # inserta solo si las tablas están vacías
    python scripts/seed_database.py --reset   # limpia y re-inserta todo
"""

import json
import os
import random
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import bcrypt
    _BCRYPT = True
except ImportError:
    _BCRYPT = False

from database.connection import db_available, get_cursor

random.seed(42)

# ---------------------------------------------------------------------------
# Datos base
# ---------------------------------------------------------------------------

# 22 departamentos — nombre exacto que usa el frontend (constants.js)
DEPARTAMENTOS = [
    # (nombre, lat, lon, temp_c, precip_mm_mes, humedad_pct, soil_moisture)
    ("Chimaltenango",  14.6614, -90.8197, 18.2, 124, 74, 0.28),
    ("Sacatepequez",   14.5586, -90.7295, 19.1, 115, 73, 0.26),
    ("Guatemala",      14.6349, -90.5069, 20.8,  98, 68, 0.22),
    ("Escuintla",      14.3019, -90.7857, 28.4, 198, 80, 0.34),
    ("Santa Rosa",     14.2136, -90.2975, 24.6, 156, 74, 0.29),
    ("Solola",         14.7752, -91.1820, 16.4, 148, 78, 0.31),
    ("Totonicapan",    14.9133, -91.3598, 14.6, 142, 76, 0.30),
    ("Quetzaltenango", 14.8445, -91.5187, 16.8, 128, 70, 0.27),
    ("Suchitepequez",  14.5319, -91.5099, 27.2, 312, 83, 0.38),
    ("Retalhuleu",     14.5286, -91.6863, 28.8, 246, 81, 0.36),
    ("San Marcos",     14.9599, -91.7952, 18.6, 162, 74, 0.31),
    ("Huehuetenango",  15.3189, -91.4706, 17.4, 138, 72, 0.28),
    ("Quiche",         15.0301, -91.1500, 17.8, 152, 74, 0.30),
    ("Baja Verapaz",   15.1264, -90.3631, 21.4, 168, 75, 0.32),
    ("Coban",          15.4686, -90.3769, 19.8, 284, 85, 0.38),
    ("Peten",          16.9302, -89.8883, 28.2, 186, 80, 0.33),
    ("Izabal",         15.4667, -89.1333, 27.4, 312, 84, 0.37),
    ("Zacapa",         14.9726, -89.5267, 28.6,  76, 58, 0.18),
    ("Chiquimula",     14.7993, -89.5454, 27.4,  82, 60, 0.20),
    ("Jalapa",         14.6333, -89.9833, 21.6,  98, 64, 0.23),
    ("Jutiapa",        14.2936, -89.8963, 24.2,  88, 62, 0.21),
    ("El Progreso",    14.8500, -90.0667, 26.8,  76, 60, 0.19),
]

# Cultivos principales por zona agroecológica
CROPS_BY_DEPTO = {
    "Chimaltenango":  ["Maiz", "Papa", "Frijol", "Repollo", "Zanahoria", "Brocoli"],
    "Sacatepequez":   ["Cafe", "Aguacate", "Maiz", "Frijol", "Tomate"],
    "Guatemala":      ["Tomate", "Chile", "Maiz", "Cebolla", "Lechuga"],
    "Escuintla":      ["Cana de azucar", "Banano", "Mango", "Maiz", "Arroz"],
    "Santa Rosa":     ["Cafe", "Maiz", "Frijol", "Tomate", "Sorgo"],
    "Solola":         ["Papa", "Maiz", "Frijol", "Cebolla", "Zanahoria"],
    "Totonicapan":    ["Papa", "Maiz", "Trigo", "Avena", "Repollo"],
    "Quetzaltenango": ["Papa", "Maiz", "Frijol", "Cafe", "Brocoli"],
    "Suchitepequez":  ["Cafe", "Cacao", "Banano", "Cana de azucar", "Cardamomo"],
    "Retalhuleu":     ["Cana de azucar", "Banano", "Mango", "Arroz", "Maiz"],
    "San Marcos":     ["Cafe", "Papa", "Maiz", "Frijol", "Mango"],
    "Huehuetenango":  ["Cafe", "Maiz", "Frijol", "Papa", "Trigo"],
    "Quiche":         ["Maiz", "Frijol", "Papa", "Cardamomo", "Tomate"],
    "Baja Verapaz":   ["Maiz", "Frijol", "Cafe", "Tomate", "Chile"],
    "Coban":          ["Cafe", "Cardamomo", "Cacao", "Maiz", "Banano"],
    "Peten":          ["Maiz", "Banano", "Arroz", "Cacao", "Yuca"],
    "Izabal":         ["Banano", "Pina", "Cacao", "Arroz", "Maiz"],
    "Zacapa":         ["Maiz", "Sorgo", "Tomate", "Melon", "Sandia"],
    "Chiquimula":     ["Maiz", "Frijol", "Sorgo", "Tomate", "Chile"],
    "Jalapa":         ["Maiz", "Frijol", "Tomate", "Papa", "Chile"],
    "Jutiapa":        ["Maiz", "Frijol", "Sorgo", "Tomate", "Cafe"],
    "El Progreso":    ["Maiz", "Sorgo", "Tomate", "Melon", "Cana de azucar"],
}

ALERT_TEMPLATES = [
    {
        "variable": "temperature",
        "condicion": "alto",
        "severidad": "moderado",
        "mensaje": "Temperatura por encima del rango óptimo. Aumentar riego y aplicar sombreado temporal.",
    },
    {
        "variable": "temperature",
        "condicion": "bajo",
        "severidad": "leve",
        "mensaje": "Temperatura baja detectada. Riesgo de daño por helada en zonas de altiplano.",
    },
    {
        "variable": "humidity",
        "condicion": "alto",
        "severidad": "moderado",
        "mensaje": "Humedad relativa elevada. Riesgo de hongos y enfermedades foliares.",
    },
    {
        "variable": "soil_moisture",
        "condicion": "bajo",
        "severidad": "severo",
        "mensaje": "Déficit hídrico crítico en el suelo. Activar riego de emergencia.",
    },
    {
        "variable": "soil_moisture",
        "condicion": "alto",
        "severidad": "leve",
        "mensaje": "Exceso de humedad en el suelo. Evaluar drenaje para evitar asfixia radicular.",
    },
    {
        "variable": "rainfall",
        "condicion": "bajo",
        "severidad": "moderado",
        "mensaje": "Precipitación insuficiente para el ciclo del cultivo. Complementar con riego.",
    },
    {
        "variable": "soil_ph",
        "condicion": "bajo",
        "severidad": "leve",
        "mensaje": "pH ácido fuera del rango óptimo. Aplicar cal agrícola según análisis de suelo.",
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rnd(base, pct=0.12):
    """Variación aleatoria ±pct% sobre el valor base."""
    delta = base * pct
    return round(base + random.uniform(-delta, delta), 2)


def _yield_level(pct):
    if pct >= 75:
        return "alto"
    if pct >= 50:
        return "medio"
    return "bajo"


def _hash_password(password):
    if _BCRYPT:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    return f"pbkdf2_sha256$mock${password}"


def _count(cur, table):
    cur.execute(f"SELECT COUNT(*) AS n FROM {table}")
    return cur.fetchone()["n"]


# ---------------------------------------------------------------------------
# Seeders
# ---------------------------------------------------------------------------

def seed_municipios(cur, reset):
    if not reset and _count(cur, "municipios") >= 22:
        print("  municipios: ya tiene 22+ filas, omitiendo.")
        return
    if reset:
        cur.execute("DELETE FROM municipios")
    for nombre, lat, lon, *_ in DEPARTAMENTOS:
        cur.execute(
            "INSERT INTO municipios (nombre, lat, lon) VALUES (%s,%s,%s) ON CONFLICT (nombre) DO NOTHING",
            (nombre, lat, lon),
        )
    print(f"  municipios: {len(DEPARTAMENTOS)} departamentos insertados.")


def seed_metricas_climaticas(cur, reset):
    if not reset and _count(cur, "metricas_climaticas") > 0:
        print("  metricas_climaticas: ya tiene datos, omitiendo.")
        return
    if reset:
        cur.execute("DELETE FROM metricas_climaticas WHERE fuente = 'ERA5-Land' AND periodo = '2010-2026'")

    rows = 0
    for nombre, _, _, temp, precip, humedad, sm in DEPARTAMENTOS:
        cur.execute(
            """INSERT INTO metricas_climaticas
               (municipio, temperatura, precipitacion, humedad, soil_moisture, fuente, periodo)
               VALUES (%s,%s,%s,%s,%s,'ERA5-Land','2010-2026')
               ON CONFLICT (municipio, fuente, periodo) DO UPDATE SET
                   temperatura = EXCLUDED.temperatura,
                   precipitacion = EXCLUDED.precipitacion,
                   humedad = EXCLUDED.humedad,
                   soil_moisture = EXCLUDED.soil_moisture,
                   fecha_carga = NOW()""",
            (nombre, temp, precip, humedad, sm),
        )
        rows += 1
    print(f"  metricas_climaticas: {rows} filas insertadas (ERA5-Land 2010-2026).")


def seed_predicciones(cur, reset):
    if not reset and _count(cur, "predicciones") > 0:
        print("  predicciones: ya tiene datos, omitiendo.")
        return
    if reset:
        cur.execute("DELETE FROM alertas")
        cur.execute("DELETE FROM predicciones")

    now = datetime.now()
    inserted = 0
    pred_ids_with_alerts = []

    # 120 predicciones en los últimos 90 días
    for i in range(120):
        depto_row = random.choice(DEPARTAMENTOS)
        nombre, _, _, base_temp, base_precip, base_hum, base_sm = depto_row
        crop = random.choice(CROPS_BY_DEPTO[nombre])
        ts = now - timedelta(days=random.uniform(0, 90), hours=random.uniform(0, 24))
        mes = ts.month

        temp       = round(_rnd(base_temp, 0.15), 1)
        precip     = round(max(0, _rnd(base_precip, 0.25)), 1)
        humedad    = round(min(100, max(20, _rnd(base_hum, 0.10))), 1)
        sm         = round(min(0.65, max(0.01, _rnd(base_sm, 0.20))), 3)
        ph         = round(random.uniform(5.5, 7.2), 1)
        light      = round(random.uniform(8000, 65000), 0)
        green      = round(random.uniform(45, 80), 1)
        temp_max   = round(temp + random.uniform(3, 8), 1)
        temp_min   = round(temp - random.uniform(3, 8), 1)
        wind       = round(random.uniform(1.0, 5.5), 2)
        swvl2      = round(sm * random.uniform(0.85, 1.1), 3)
        swvl3      = round(sm * random.uniform(0.70, 0.95), 3)
        soil_temp  = round(temp - random.uniform(1, 4), 1)

        # Distribución: 40% alto, 45% medio, 15% bajo
        r = random.random()
        if r < 0.40:
            yield_pct = round(random.uniform(75, 93), 1)
        elif r < 0.85:
            yield_pct = round(random.uniform(50, 74.9), 1)
        else:
            yield_pct = round(random.uniform(28, 49.9), 1)

        fuente = "arduino" if random.random() < 0.25 else "manual"

        cur.execute(
            """INSERT INTO predicciones
               (timestamp, municipio, cultivo, mes, temperatura, precipitacion, humedad,
                ph_suelo, soil_moisture, light_lux, greenness_idx,
                swvl2, swvl3, soil_temp, temp_max, temp_min, wind_speed,
                yield_pct, yield_level, fuente, modelo_ver)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'xgboost_v2')
               RETURNING id""",
            (
                ts, nombre, crop, mes, temp, precip, humedad, ph, sm,
                light, green, swvl2, swvl3, soil_temp, temp_max, temp_min, wind,
                yield_pct, _yield_level(yield_pct), fuente,
            ),
        )
        pred_id = cur.fetchone()["id"]
        inserted += 1

        # Generar alertas para predicciones con valores extremos o bajo rendimiento
        if yield_pct < 50 or temp > 32 or sm < 0.12 or humedad > 88:
            pred_ids_with_alerts.append({
                "id": pred_id,
                "municipio": nombre,
                "cultivo": crop,
                "temp": temp,
                "sm": sm,
                "humedad": humedad,
            })

    print(f"  predicciones: {inserted} registros (últimos 90 días).")
    return pred_ids_with_alerts


def seed_alertas(cur, pred_ids_with_alerts):
    if not pred_ids_with_alerts:
        print("  alertas: sin predicciones extremas para generar alertas.")
        return

    inserted = 0
    for p in pred_ids_with_alerts:
        templates = []
        if p["temp"] > 32:
            templates.append(ALERT_TEMPLATES[0])  # temperatura alta
        if p["sm"] < 0.12:
            templates.append(ALERT_TEMPLATES[3])  # soil_moisture bajo severo
        if p["humedad"] > 88:
            templates.append(ALERT_TEMPLATES[2])  # humedad alta
        if not templates:
            templates.append(random.choice(ALERT_TEMPLATES))

        for tmpl in templates:
            cur.execute(
                """INSERT INTO alertas
                   (prediccion_id, municipio, cultivo, variable, condicion, severidad, mensaje)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (
                    p["id"], p["municipio"], p["cultivo"],
                    tmpl["variable"], tmpl["condicion"],
                    tmpl["severidad"], tmpl["mensaje"],
                ),
            )
            inserted += 1

    print(f"  alertas: {inserted} alertas vinculadas a predicciones extremas.")


def seed_lecturas_arduino(cur, reset):
    if not reset and _count(cur, "lecturas_arduino") > 0:
        print("  lecturas_arduino: ya tiene datos, omitiendo.")
        return
    if reset:
        cur.execute("DELETE FROM lecturas_arduino")

    now = datetime.now()
    inserted = 0
    deptos_arduino = ["Chimaltenango", "Guatemala", "Quetzaltenango", "Escuintla", "Coban"]

    for _ in range(60):
        nombre = random.choice(deptos_arduino)
        depto_row = next(d for d in DEPARTAMENTOS if d[0] == nombre)
        _, _, _, base_temp, base_precip, base_hum, base_sm = depto_row
        crop = random.choice(CROPS_BY_DEPTO[nombre][:3])
        ts = now - timedelta(days=random.uniform(0, 30), minutes=random.randint(0, 1440))

        temp  = round(_rnd(base_temp, 0.10), 1)
        sm    = round(min(0.65, max(0.01, _rnd(base_sm, 0.15))), 3)
        light = round(random.uniform(5000, 80000), 0)
        green = round(random.uniform(40, 85), 1)
        hum   = round(min(100, max(20, _rnd(base_hum, 0.08))), 1)
        precip = round(max(0, _rnd(base_precip * 0.4, 0.30)), 1)
        ph    = round(random.uniform(5.5, 7.2), 1)

        raw = {
            "temperature": temp, "soil_moisture": sm,
            "light_lux": light, "greenness_idx": green,
            "humidity": hum, "rainfall": precip,
            "soil_ph": ph, "timestamp": ts.isoformat(),
        }

        from psycopg2.extras import Json
        cur.execute(
            """INSERT INTO lecturas_arduino
               (timestamp, municipio, cultivo, temperatura, humedad, soil_moisture,
                light_lux, greenness_idx, ph_suelo, precipitacion, raw_json)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (ts, nombre, crop, temp, hum, sm, light, green, ph, precip, Json(raw)),
        )
        inserted += 1

    print(f"  lecturas_arduino: {inserted} lecturas de sensores (últimos 30 días).")


def seed_usuarios(cur, reset):
    if not reset and _count(cur, "usuarios") > 0:
        print("  usuarios: ya tiene datos, omitiendo.")
        return
    if reset:
        cur.execute("DELETE FROM usuarios WHERE email != 'admin'")

    pw_hash = _hash_password("demo2024")
    cur.execute(
        """INSERT INTO usuarios (nombre, email, password_hash, rol)
           VALUES (%s,%s,%s,'usuario')
           ON CONFLICT (email) DO NOTHING""",
        ("Usuario Demo", "demo@agroclima.gt", pw_hash),
    )
    print("  usuarios: usuario demo insertado (demo@agroclima.gt / demo2024).")


def seed_model_feedback(cur, reset):
    if not reset and _count(cur, "model_feedback") > 0:
        print("  model_feedback: ya tiene datos, omitiendo.")
        return
    if reset:
        cur.execute("DELETE FROM model_feedback")

    now = datetime.now()
    inserted = 0
    sample_data = [
        ("Chimaltenango", "Maiz",     5, 72.4, 68.0),
        ("Guatemala",     "Tomate",   6, 65.8, 58.0),
        ("Sacatepequez",  "Cafe",     4, 81.2, 84.0),
        ("Escuintla",     "Banano",   7, 76.0, 72.0),
        ("Coban",         "Cardamomo",8, 69.5, 74.0),
        ("Quetzaltenango","Papa",     3, 58.3, 61.0),
        ("Solola",        "Cebolla",  5, 63.2, 55.0),
        ("Peten",         "Maiz",     6, 71.8, 66.0),
        ("Zacapa",        "Sorgo",    7, 54.6, 52.0),
        ("Jalapa",        "Frijol",   8, 60.1, 58.0),
        ("Huehuetenango", "Cafe",     4, 78.4, 82.0),
        ("San Marcos",    "Papa",     5, 66.7, 70.0),
        ("Izabal",        "Banano",   9, 80.3, 77.0),
        ("El Progreso",   "Melon",   10, 55.9, 61.0),
        ("Jutiapa",       "Maiz",     6, 61.4, 59.0),
    ]
    for municipio, cultivo, mes, pred, actual in sample_data:
        created = now - timedelta(days=random.randint(1, 60))
        cur.execute(
            """INSERT INTO model_feedback
               (created_at, municipio, cultivo, mes, predicted_yield, actual_yield, abs_error, processed_retrain)
               VALUES (%s,%s,%s,%s,%s,%s,%s, FALSE)""",
            (created, municipio, cultivo, mes, pred, actual, round(abs(pred - actual), 2)),
        )
        inserted += 1

    print(f"  model_feedback: {inserted} registros de retroalimentación de campo.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    reset = "--reset" in sys.argv

    if not db_available():
        print("ERROR: No se puede conectar a la base de datos.")
        print("Asegúrate de que el contenedor Docker esté corriendo:")
        print("  cd conferencia && docker compose up -d")
        sys.exit(1)

    action = "Limpiando y re-insertando" if reset else "Insertando"
    print(f"\nAgroClima GT — Seed de base de datos ({action})\n")

    with get_cursor(dict_cursor=True) as cur:
        seed_municipios(cur, reset)
        seed_metricas_climaticas(cur, reset)
        pred_extremas = seed_predicciones(cur, reset)
        if pred_extremas:
            seed_alertas(cur, pred_extremas)
        seed_lecturas_arduino(cur, reset)
        seed_usuarios(cur, reset)
        seed_model_feedback(cur, reset)

    print("\nSeed completado.\n")
    print("Resumen de tablas:")
    with get_cursor() as cur:
        for tabla in [
            "municipios", "metricas_climaticas", "predicciones", "alertas",
            "lecturas_arduino", "usuarios", "model_feedback", "recomendaciones_cultivo",
        ]:
            cur.execute(f"SELECT COUNT(*) AS n FROM {tabla}")
            n = cur.fetchone()["n"]
            print(f"  {tabla:<28} {n:>6} filas")

    print()


if __name__ == "__main__":
    main()
