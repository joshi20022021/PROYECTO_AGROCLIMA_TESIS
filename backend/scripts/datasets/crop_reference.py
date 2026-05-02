"""
Dataset de referencia agronómica para AgroClima GT.
Condiciones óptimas para 37 cultivos relevantes en Guatemala/Centroamérica.

Sensores físicos del proyecto:
    - DS18B20              → temperatura del suelo/ambiente (°C)
    - TSL2561              → intensidad de luz (lux)
    - TCS3200              → color hoja/suelo → índice de verdor (%)
    - Higrómetro capacitivo → humedad volumétrica del suelo (0.0-1.0)

Fuentes:
    - FAO Crop Water Requirements (Doorenbos & Pruitt)
    - ICTA Guatemala — fichas técnicas de cultivos
    - CIMMYT — guías de producción de maíz y frijol
    - Anacafé Guatemala — manual del caficultor
    - MAGA Guatemala — manuales de producción agrícola

Salida: data/processed/crop_optimal_conditions.csv
"""

import os
import pandas as pd

# ---------------------------------------------------------------------------
# Tabla de condiciones óptimas por cultivo
#
# Nuevas columnas de sensores:
#   light_min / light_max     — intensidad de luz óptima (lux, TSL2561)
#   green_min / green_max     — índice de verdor óptimo (%, TCS3200)
#                               greenness = G/(R+G+B)*100 desde el TCS3200
# ---------------------------------------------------------------------------

CROPS = [
    # ── Granos básicos ──────────────────────────────────────────────────────
    dict(crop="Maiz",        temp_min=18, temp_max=30, rain_min=60,  rain_max=150, humidity_min=50, humidity_max=80, ph_min=5.8, ph_max=7.0, sm_min=0.22, sm_max=0.40, light_min=25000, light_max=60000, green_min=55, green_max=82, category="Grano",    notes="Sensible a heladas; critico en floracion"),
    dict(crop="Frijol",      temp_min=15, temp_max=27, rain_min=30,  rain_max=100, humidity_min=45, humidity_max=75, ph_min=6.0, ph_max=7.0, sm_min=0.20, sm_max=0.38, light_min=20000, light_max=50000, green_min=52, green_max=80, category="Grano",    notes="No tolera encharcamiento; sensible a alta humedad en vaina"),
    dict(crop="Arroz",       temp_min=20, temp_max=35, rain_min=100, rain_max=200, humidity_min=70, humidity_max=90, ph_min=5.5, ph_max=7.0, sm_min=0.35, sm_max=0.55, light_min=30000, light_max=65000, green_min=58, green_max=85, category="Grano",    notes="Requiere suelos con buena capacidad de retencion hidrica"),
    dict(crop="Trigo",       temp_min=10, temp_max=24, rain_min=25,  rain_max=75,  humidity_min=40, humidity_max=70, ph_min=6.0, ph_max=7.5, sm_min=0.18, sm_max=0.35, light_min=15000, light_max=45000, green_min=50, green_max=78, category="Grano",    notes="Altiplano guatemalteco; sensible a roya en humedad alta"),
    dict(crop="Sorgo",       temp_min=21, temp_max=35, rain_min=40,  rain_max=100, humidity_min=40, humidity_max=75, ph_min=5.5, ph_max=7.5, sm_min=0.18, sm_max=0.38, light_min=28000, light_max=65000, green_min=50, green_max=78, category="Grano",    notes="Alta tolerancia a sequia; bajo costo de produccion"),
    dict(crop="Avena",       temp_min=8,  temp_max=22, rain_min=30,  rain_max=80,  humidity_min=50, humidity_max=75, ph_min=5.5, ph_max=7.0, sm_min=0.18, sm_max=0.35, light_min=12000, light_max=40000, green_min=50, green_max=78, category="Grano",    notes="Tierras altas; sensible a temperaturas extremas"),

    # ── Hortalizas ──────────────────────────────────────────────────────────
    dict(crop="Tomate",      temp_min=18, temp_max=27, rain_min=25,  rain_max=75,  humidity_min=55, humidity_max=75, ph_min=6.0, ph_max=7.0, sm_min=0.22, sm_max=0.40, light_min=20000, light_max=50000, green_min=52, green_max=80, category="Hortaliza", notes="Alta humedad favorece tizon tardio; riego controlado"),
    dict(crop="Papa",        temp_min=10, temp_max=20, rain_min=40,  rain_max=100, humidity_min=55, humidity_max=80, ph_min=5.0, ph_max=6.5, sm_min=0.22, sm_max=0.42, light_min=15000, light_max=40000, green_min=55, green_max=82, category="Hortaliza", notes="Susceptible a Phytophthora; pH bajo esencial"),
    dict(crop="Zanahoria",   temp_min=10, temp_max=22, rain_min=30,  rain_max=70,  humidity_min=50, humidity_max=75, ph_min=6.0, ph_max=7.0, sm_min=0.20, sm_max=0.38, light_min=15000, light_max=40000, green_min=50, green_max=78, category="Hortaliza", notes="Suelos sueltos sin piedras; raiz bifurcada en compactados"),
    dict(crop="Cebolla",     temp_min=13, temp_max=24, rain_min=20,  rain_max=60,  humidity_min=45, humidity_max=70, ph_min=6.0, ph_max=7.0, sm_min=0.18, sm_max=0.35, light_min=15000, light_max=45000, green_min=48, green_max=76, category="Hortaliza", notes="Bulbificacion afectada por fotoperiodo; evitar exceso agua"),
    dict(crop="Repollo",     temp_min=10, temp_max=20, rain_min=30,  rain_max=80,  humidity_min=60, humidity_max=80, ph_min=6.0, ph_max=7.5, sm_min=0.22, sm_max=0.40, light_min=12000, light_max=38000, green_min=55, green_max=82, category="Hortaliza", notes="Clima fresco; requiere calcio para cabeza compacta"),
    dict(crop="Brocoli",     temp_min=10, temp_max=20, rain_min=30,  rain_max=70,  humidity_min=60, humidity_max=80, ph_min=6.0, ph_max=7.0, sm_min=0.22, sm_max=0.40, light_min=12000, light_max=38000, green_min=55, green_max=82, category="Hortaliza", notes="Altiplano 1800-3000 msnm; exportacion principal Guatemala"),
    dict(crop="Coliflor",    temp_min=10, temp_max=20, rain_min=30,  rain_max=70,  humidity_min=60, humidity_max=80, ph_min=6.0, ph_max=7.5, sm_min=0.22, sm_max=0.40, light_min=12000, light_max=38000, green_min=52, green_max=80, category="Hortaliza", notes="Similar al brocoli; intolerante a altas temperaturas"),
    dict(crop="Lechuga",     temp_min=10, temp_max=20, rain_min=30,  rain_max=60,  humidity_min=60, humidity_max=80, ph_min=6.0, ph_max=7.0, sm_min=0.20, sm_max=0.38, light_min=8000,  light_max=30000, green_min=55, green_max=82, category="Hortaliza", notes="Bolting prematuro con altas temperaturas"),
    dict(crop="Espinaca",    temp_min=8,  temp_max=20, rain_min=25,  rain_max=60,  humidity_min=60, humidity_max=80, ph_min=6.0, ph_max=7.5, sm_min=0.20, sm_max=0.38, light_min=8000,  light_max=28000, green_min=58, green_max=85, category="Hortaliza", notes="Alta demanda de nitrogeno; sensible a suelos acidos"),
    dict(crop="Pepino",      temp_min=18, temp_max=30, rain_min=30,  rain_max=80,  humidity_min=60, humidity_max=80, ph_min=6.0, ph_max=7.0, sm_min=0.22, sm_max=0.42, light_min=20000, light_max=50000, green_min=55, green_max=82, category="Hortaliza", notes="Sensible a heladas; alta evapotranspiracion"),
    dict(crop="Chile",       temp_min=18, temp_max=28, rain_min=30,  rain_max=80,  humidity_min=60, humidity_max=75, ph_min=6.0, ph_max=7.0, sm_min=0.22, sm_max=0.40, light_min=18000, light_max=48000, green_min=52, green_max=80, category="Hortaliza", notes="Bacteriosis con lluvia excesiva; importante en Guatemala"),
    dict(crop="Berenjena",   temp_min=20, temp_max=30, rain_min=30,  rain_max=80,  humidity_min=55, humidity_max=75, ph_min=6.0, ph_max=7.0, sm_min=0.22, sm_max=0.40, light_min=22000, light_max=52000, green_min=52, green_max=80, category="Hortaliza", notes="Requiere temperaturas calidas; intolerante a heladas"),
    dict(crop="Zucchini",    temp_min=18, temp_max=28, rain_min=30,  rain_max=80,  humidity_min=55, humidity_max=75, ph_min=6.0, ph_max=7.5, sm_min=0.22, sm_max=0.40, light_min=18000, light_max=48000, green_min=52, green_max=80, category="Hortaliza", notes="Crecimiento rapido; buena rotacion con maiz"),

    # ── Frutas ──────────────────────────────────────────────────────────────
    dict(crop="Aguacate",    temp_min=15, temp_max=25, rain_min=60,  rain_max=130, humidity_min=60, humidity_max=80, ph_min=5.5, ph_max=7.0, sm_min=0.22, sm_max=0.42, light_min=20000, light_max=55000, green_min=55, green_max=82, category="Fruta",    notes="Sensible a encharcamiento; exportacion importante GT"),
    dict(crop="Mango",       temp_min=24, temp_max=32, rain_min=50,  rain_max=150, humidity_min=50, humidity_max=80, ph_min=5.5, ph_max=7.5, sm_min=0.20, sm_max=0.40, light_min=30000, light_max=70000, green_min=52, green_max=80, category="Fruta",    notes="Sequia previa a floracion mejora produccion"),
    dict(crop="Naranja",     temp_min=18, temp_max=30, rain_min=60,  rain_max=120, humidity_min=60, humidity_max=80, ph_min=5.5, ph_max=7.0, sm_min=0.22, sm_max=0.40, light_min=22000, light_max=55000, green_min=55, green_max=82, category="Fruta",    notes="Produccion citrica; sensible a heladas"),
    dict(crop="Limon",       temp_min=20, temp_max=32, rain_min=50,  rain_max=100, humidity_min=55, humidity_max=75, ph_min=5.5, ph_max=7.0, sm_min=0.20, sm_max=0.38, light_min=25000, light_max=60000, green_min=52, green_max=80, category="Fruta",    notes="Tolerante a sequia moderada; costa sur Guatemala"),
    dict(crop="Banano",      temp_min=22, temp_max=32, rain_min=100, rain_max=200, humidity_min=70, humidity_max=90, ph_min=5.5, ph_max=7.0, sm_min=0.30, sm_max=0.50, light_min=28000, light_max=65000, green_min=58, green_max=85, category="Fruta",    notes="Region atlantica; altamente sensible a vientos"),
    dict(crop="Pina",        temp_min=20, temp_max=32, rain_min=80,  rain_max=160, humidity_min=60, humidity_max=80, ph_min=4.5, ph_max=6.5, sm_min=0.22, sm_max=0.42, light_min=25000, light_max=60000, green_min=50, green_max=78, category="Fruta",    notes="Suelos muy bien drenados; tolerante a pH bajo"),
    dict(crop="Papaya",      temp_min=22, temp_max=32, rain_min=80,  rain_max=150, humidity_min=60, humidity_max=80, ph_min=5.5, ph_max=7.0, sm_min=0.25, sm_max=0.42, light_min=28000, light_max=65000, green_min=55, green_max=82, category="Fruta",    notes="Sensible a virus del mosaico; requiere buena ventilacion"),
    dict(crop="Melon",       temp_min=20, temp_max=32, rain_min=30,  rain_max=80,  humidity_min=40, humidity_max=70, ph_min=6.0, ph_max=7.5, sm_min=0.20, sm_max=0.38, light_min=25000, light_max=60000, green_min=50, green_max=78, category="Fruta",    notes="Clima calido seco; riego por goteo ideal"),
    dict(crop="Sandia",      temp_min=22, temp_max=35, rain_min=30,  rain_max=80,  humidity_min=40, humidity_max=70, ph_min=6.0, ph_max=7.0, sm_min=0.20, sm_max=0.38, light_min=28000, light_max=65000, green_min=50, green_max=78, category="Fruta",    notes="Valles calidos; humedad alta favorece antracnosis"),
    dict(crop="Fresa",       temp_min=10, temp_max=22, rain_min=30,  rain_max=80,  humidity_min=60, humidity_max=80, ph_min=5.5, ph_max=6.5, sm_min=0.22, sm_max=0.40, light_min=15000, light_max=42000, green_min=52, green_max=80, category="Fruta",    notes="Altiplano; alta demanda de mano de obra"),

    # ── Cultivos comerciales ─────────────────────────────────────────────────
    dict(crop="Cafe",        temp_min=18, temp_max=25, rain_min=80,  rain_max=180, humidity_min=65, humidity_max=85, ph_min=5.5, ph_max=6.5, sm_min=0.25, sm_max=0.45, light_min=5000,  light_max=25000, green_min=58, green_max=85, category="Comercial", notes="Principal cultivo exportacion GT; roya con >85% HR; crece en sombra"),
    dict(crop="Cacao",       temp_min=20, temp_max=30, rain_min=100, rain_max=200, humidity_min=75, humidity_max=90, ph_min=5.5, ph_max=7.5, sm_min=0.28, sm_max=0.48, light_min=3000,  light_max=20000, green_min=60, green_max=86, category="Comercial", notes="Requiere sombra; regiones bajas humedas"),
    dict(crop="Cana de azucar", temp_min=20, temp_max=35, rain_min=80, rain_max=150, humidity_min=60, humidity_max=80, ph_min=6.0, ph_max=7.5, sm_min=0.25, sm_max=0.45, light_min=30000, light_max=70000, green_min=55, green_max=82, category="Comercial", notes="Costa sur Guatemala; zafra nov-mayo"),
    dict(crop="Cardamomo",   temp_min=18, temp_max=28, rain_min=80,  rain_max=180, humidity_min=70, humidity_max=90, ph_min=5.5, ph_max=7.0, sm_min=0.28, sm_max=0.48, light_min=4000,  light_max=18000, green_min=58, green_max=85, category="Comercial", notes="Guatemala mayor exportador mundial; Alta Verapaz; sombra parcial"),
    dict(crop="Soya",        temp_min=20, temp_max=30, rain_min=50,  rain_max=120, humidity_min=55, humidity_max=80, ph_min=6.0, ph_max=7.0, sm_min=0.22, sm_max=0.42, light_min=22000, light_max=55000, green_min=52, green_max=80, category="Comercial", notes="Fijacion de nitrogeno; rotacion con maiz"),
    dict(crop="Mani",        temp_min=22, temp_max=35, rain_min=40,  rain_max=100, humidity_min=50, humidity_max=75, ph_min=5.5, ph_max=7.0, sm_min=0.20, sm_max=0.38, light_min=25000, light_max=60000, green_min=50, green_max=78, category="Comercial", notes="Suelos arenosos bien drenados; semi-arido"),

    # ── Raíces y tubérculos ─────────────────────────────────────────────────
    dict(crop="Yuca",        temp_min=22, temp_max=35, rain_min=60,  rain_max=130, humidity_min=55, humidity_max=80, ph_min=5.5, ph_max=7.0, sm_min=0.20, sm_max=0.40, light_min=20000, light_max=55000, green_min=50, green_max=78, category="Raiz",     notes="Alta tolerancia a sequia; suelos pobres"),
    dict(crop="Camote",      temp_min=20, temp_max=30, rain_min=50,  rain_max=100, humidity_min=55, humidity_max=75, ph_min=5.5, ph_max=7.5, sm_min=0.20, sm_max=0.38, light_min=18000, light_max=50000, green_min=50, green_max=78, category="Raiz",     notes="Tolerante a suelos marginales; seguridad alimentaria"),
]


def build_dataframe() -> pd.DataFrame:
    df = pd.DataFrame(CROPS)
    # Derive optimal ranges for ERA5-Land extra variables (from existing parameters)
    # stl1: soil temperature 0-7 cm (°C) — roughly 3°C below air temperature
    df["stl1_min"]  = df["temp_min"] - 3
    df["stl1_max"]  = df["temp_max"] - 3
    # swvl2/swvl3: deeper soil moisture retains slightly more water than surface
    df["swvl2_min"] = (df["sm_min"] + 0.03).round(3)
    df["swvl2_max"] = (df["sm_max"] + 0.05).round(3)
    df["swvl3_min"] = (df["sm_min"] + 0.05).round(3)
    df["swvl3_max"] = (df["sm_max"] + 0.08).round(3)
    return df


def save_csv(df: pd.DataFrame, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")


if __name__ == "__main__":
    out_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "datasets", "crop_optimal_conditions.csv"
    )
    df = build_dataframe()
    save_csv(df, out_path)

    print(f"Dataset guardado: {out_path}")
    print(f"Total cultivos  : {len(df)}")
    print(f"Categorias      : {df['category'].value_counts().to_dict()}")
    print()
    print(df[["crop", "category", "light_min", "light_max", "green_min", "green_max"]].to_string(index=False))
