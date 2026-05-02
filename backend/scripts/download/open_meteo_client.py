"""
Cliente de Open-Meteo Historical Archive API para métricas compatibles con sensores Arduino.
Extrae datos agrometeorológicos (2010-2024) y los agrega a nivel mensual por municipio en Guatemala.

Variables objetivo (Arduino-compatibles):
    temperature_2m_mean          → Temp. Media DHT22 (°C)
    temperature_2m_max           → Temperatura Máxima
    temperature_2m_min           → Temperatura Mínima
    precipitation_sum            → Lluvia acumulada Pluviómetro (mm)
    soil_moisture_0_to_7cm_mean  → Humedad del suelo YL-69 (m³/m³)
    relative_humidity_2m         → Humedad relativa DHT22 (%) -> Extraído por horas y promediado
    shortwave_radiation_sum      → Radiación solar LDR (MJ/m²)

Metadatos agregados por municipio:
    depto, zona, altitud_m

Salida:
    data/raw/openmeteo/open_meteo_municipios.json  (Consolidado con promedios mensuales)
"""

import os
import sys
import time
import json
import urllib.request
import urllib.parse
import urllib.error
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from municipios_nacional import MUNICIPIOS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR  = os.path.join(BASE_DIR, "data", "raw", "openmeteo")
OUT_PATH = os.path.join(OUT_DIR, "open_meteo_municipios.json")

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"


def load_existing_results() -> list[dict]:
    if not os.path.exists(OUT_PATH):
        return []
    try:
        with open(OUT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except Exception as e:
        print(f"[!] No se pudo leer el archivo de respaldo existente: {e}")
    return []


def save_results(results: list[dict]):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def fetch_open_meteo(lat: float, lon: float, start_year: int = 2010, end_year: int = 2024) -> dict | None:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": f"{start_year}-01-01",
        "end_date": f"{end_year}-12-31",
        "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,shortwave_radiation_sum,soil_moisture_0_to_7cm_mean",
        "hourly": "relative_humidity_2m",
        "timezone": "America/Guatemala",
    }
    
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AgroClimaGT-Research/1.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait_time = (attempt + 1) * 15  # 15s, 30s, 45s...
                print(f"\n    [!] Error 429 (Too Many Requests). Reintentando en {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"\n    Error HTTP Open-Meteo: {e}")
                return None
        except Exception as e:
            print(f"\n    Error genérico Open-Meteo: {e}")
            return None
            
    print("\n    [!] Se agotaron los reintentos.")
    return None

def parse_and_aggregate(raw: dict, municipio: str, coords: dict) -> dict:
    # 1. Procesar datos diarios
    daily = raw.get("daily", {})
    if not daily or "time" not in daily:
        return {}
        
    df_daily = pd.DataFrame(daily)
    df_daily["date"] = pd.to_datetime(df_daily["time"])
    
    # 2. Procesar datos horarios (convertir a media diaria para HR)
    hourly = raw.get("hourly", {})
    if hourly and "time" in hourly:
        df_hourly = pd.DataFrame(hourly)
        df_hourly["date"] = pd.to_datetime(df_hourly["time"]).dt.date
        df_hourly["date"] = pd.to_datetime(df_hourly["date"])
        
        # Calcular media diaria de HR
        hr_daily = df_hourly.groupby("date")["relative_humidity_2m"].mean().reset_index()
        # Unir al dataset diario
        df_daily = pd.merge(df_daily, hr_daily, on="date", how="left")
    else:
        # Failsafe si no hay humedad
        df_daily["relative_humidity_2m"] = None

    # 3. Extraer mes y año
    df_daily["year"] = df_daily["date"].dt.year
    df_daily["month"] = df_daily["date"].dt.month
    
    # 4. Agrupar mensualmente 
    mensual = df_daily.groupby(["year", "month"]).agg({
        "temperature_2m_mean": "mean",
        "temperature_2m_max": "mean",
        "temperature_2m_min": "mean",
        "precipitation_sum": "sum",
        "shortwave_radiation_sum": "sum",
        "soil_moisture_0_to_7cm_mean": "mean",
        "relative_humidity_2m": "mean"
    }).reset_index()
    
    records = []
    for _, row in mensual.iterrows():
        records.append({
            "municipio": municipio,
            "depto": coords.get("depto"),
            "zona": coords.get("zona"),
            "altitud_m": coords.get("altitud_m"),
            "year": int(row["year"]),
            "month": int(row["month"]),
            "t2m": round(row["temperature_2m_mean"], 2) if pd.notna(row["temperature_2m_mean"]) else None,
            "t2m_max": round(row["temperature_2m_max"], 2) if pd.notna(row["temperature_2m_max"]) else None,
            "t2m_min": round(row["temperature_2m_min"], 2) if pd.notna(row["temperature_2m_min"]) else None,
            "prectotcorr": round(row["precipitation_sum"], 2) if pd.notna(row["precipitation_sum"]) else None,
            "rad_sw": round(row["shortwave_radiation_sum"], 2) if pd.notna(row["shortwave_radiation_sum"]) else None,
            "soil_moisture": round(row["soil_moisture_0_to_7cm_mean"], 4) if pd.notna(row["soil_moisture_0_to_7cm_mean"]) else None,
            "rh2m": round(row["relative_humidity_2m"], 2) if pd.notna(row["relative_humidity_2m"]) else None,
        })
        
    return {
        "municipio": municipio,
        "depto": coords.get("depto"),
        "zona": coords.get("zona"),
        "altitud_m": coords.get("altitud_m"),
        "records": records,
    }


def fetch_all(start_year: int = 2010, end_year: int = 2024, resume: bool = True) -> list[dict]:
    results = load_existing_results() if resume else []
    total = len(MUNICIPIOS)
    completed = {
        entry.get("municipio")
        for entry in results
        if entry.get("municipio") and entry.get("records")
    }

    if resume and completed:
        print(f"[i] Reanudando desde respaldo: {len(completed)} municipio(s) ya descargado(s).")

    for i, (municipio, coords) in enumerate(MUNICIPIOS.items(), 1):
        if resume and municipio in completed:
            print(f"  [{i:02d}/{total}] {municipio} ({start_year}-{end_year})... YA EXISTE, se omite")
            continue

        print(f"  [{i:02d}/{total}] {municipio} ({start_year}-{end_year})...", end=" ", flush=True)
        raw = fetch_open_meteo(coords["lat"], coords["lon"], start_year, end_year)
        
        if raw:
            parsed = parse_and_aggregate(raw, municipio, coords)
            if parsed:
                results.append(parsed)
                completed.add(municipio)
                n = len(parsed.get("records", []))
                print(f"{n} registros mensuales OK")
            else:
                print("FALLO EN PARSEO")
        else:
            print("FALLÓ API")
            
        # Autoguardado incremental para no perder datos de la hora de ejecución
        save_results(results)
            
        print("    (Pausa anti-bloqueo 60s...)")
        time.sleep(60)  # Rate limit estricto
        
    return results


def print_summary(results: list[dict]):
    print(f"\n{'Municipio':<20} {'Meses':>6}  {'T_media':>8}  {'Precip_media':>12}  {'Humedad_Suelo':>15}")
    print("-" * 68)
    for entry in results:
        mun  = entry["municipio"]
        recs = entry.get("records", [])
        if not recs:
            continue
            
        temp = [r["t2m"] for r in recs if r.get("t2m") is not None]
        prec = [r["prectotcorr"] for r in recs if r.get("prectotcorr") is not None]
        soil = [r["soil_moisture"] for r in recs if r.get("soil_moisture") is not None]
        
        t_str = f"{sum(temp)/len(temp):.1f}°C" if temp else "—"
        p_str = f"{sum(prec)/len(prec):.1f} mm" if prec else "—"
        s_str = f"{sum(soil)/len(soil):.3f} m³/m³" if soil else "—"
        
        print(f"  {mun:<18} {len(recs):>6}  {t_str:>8}  {p_str:>12}  {s_str:>15}")


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)

    args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    flags = {arg for arg in sys.argv[1:] if arg.startswith("--")}

    start = int(args[0]) if len(args) > 0 else 2010
    end   = int(args[1]) if len(args) > 1 else 2024
    resume = "--fresh" not in flags

    print(f"=== Open-Meteo Historical — {len(MUNICIPIOS)} municipios ({start}-{end}) ===\n")
    print("Variables: Temp Med/Max/Min, Precipitacion, Humedad Suelo, HR, Radiacion (Compatibles con Arduino)")
    if resume:
        print(f"Modo: reanudacion automatica desde {OUT_PATH}")
    else:
        print("Modo: ejecucion limpia (--fresh), se ignorara el respaldo existente")

    data = fetch_all(start, end, resume=resume)

    if data:
        save_results(data)
            
        total_records = sum(len(e.get("records", [])) for e in data)
        print(f"\nGuardado: {OUT_PATH}")
        print(f"Total registros mensuales procesados: {total_records:,}")
        print_summary(data)
    else:
        print("No se obtuvieron datos.")
