"""
Descarga datos agroclimáticos desde NASA POWER API — cobertura nacional Guatemala.
API gratuita, sin autenticacion, optimizada para agricultura.

¿Por qué NASA POWER ademas de ERA5?
    - ERA5-Land: alta resolución, ideal para suelo y clima local
    - NASA POWER: parametros agronómicos calculados (ETo, PAR, dias grado)
                  proviene de MERRA-2 + CERES/SYN1deg, validado para agricultura

Variables (comunidad AG):
    T2M               → Temperatura media 2m (°C)
    T2M_MAX           → Temperatura maxima mensual (°C)
    T2M_MIN           → Temperatura minima mensual (°C)
    RH2M              → Humedad relativa 2m (%)
    PRECTOTCORR       → Precipitacion corregida (mm/dia)
    ALLSKY_SFC_SW_DWN → Radiacion solar total (MJ/m²/dia)
    CLRSKY_SFC_SW_DWN → Radiacion cielo despejado (MJ/m²/dia)
    WS2M              → Velocidad viento 2m (m/s)
    WS10M             → Velocidad viento 10m (m/s)
    T2MDEW            → Temperatura punto de rocio (°C)

Metadatos agregados por municipio:
    depto, zona, altitud_m

Salida: data/raw/nasa_power/nasa_power_municipios.json

Uso:
    python nasa_power_client.py              → 2010-2024
    python nasa_power_client.py 2015 2024    → rango personalizado
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from municipios_nacional import MUNICIPIOS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR  = os.path.join(BASE_DIR, "data", "raw", "nasa_power")
OUT_PATH = os.path.join(OUT_DIR, "nasa_power_municipios.json")

PARAMETERS = [
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "RH2M",
    "PRECTOTCORR",
    "ALLSKY_SFC_SW_DWN",
    "CLRSKY_SFC_SW_DWN",
    "WS2M",
    "WS10M",
    "T2MDEW",
]

BASE_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"


def fetch_nasa_power(lat: float, lon: float,
                     start_year: int = 2010, end_year: int = 2024) -> dict | None:
    params = {
        "parameters": ",".join(PARAMETERS),
        "community":  "AG",
        "longitude":  lon,
        "latitude":   lat,
        "start":      start_year,
        "end":        end_year,
        "format":     "JSON",
    }
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AgroClimaGT/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"    Error: {e}")
        return None


def parse_response(raw: dict, municipio: str, coords: dict) -> dict:
    param_data = raw.get("properties", {}).get("parameter", {})
    if not param_data:
        return {}

    first_param = next(iter(param_data.values()))
    dates = sorted(first_param.keys())

    records = []
    for date_key in dates:
        if len(date_key) != 6:
            continue
        year  = int(date_key[:4])
        month = int(date_key[4:])

        row = {
            "municipio": municipio,
            "depto": coords.get("depto"),
            "zona": coords.get("zona"),
            "altitud_m": coords.get("altitud_m"),
            "year": year,
            "month": month,
        }
        for param, values in param_data.items():
            val = values.get(date_key)
            row[param.lower()] = round(float(val), 3) if val not in (None, -999, "-999") else None
        records.append(row)

    return {
        "municipio": municipio,
        "depto": coords.get("depto"),
        "zona": coords.get("zona"),
        "altitud_m": coords.get("altitud_m"),
        "records": records,
    }


def fetch_all(start_year: int = 2010, end_year: int = 2024) -> list[dict]:
    results = []
    total = len(MUNICIPIOS)
    for i, (municipio, coords) in enumerate(MUNICIPIOS.items(), 1):
        print(f"  [{i:02d}/{total}] {municipio} ({start_year}-{end_year})...", end=" ", flush=True)
        raw = fetch_nasa_power(coords["lat"], coords["lon"], start_year, end_year)
        if raw:
            parsed = parse_response(raw, municipio, coords)
            results.append(parsed)
            n = len(parsed.get("records", []))
            print(f"{n} registros OK")
        else:
            print("FALLÓ")
        time.sleep(1)  # respetar rate limit
    return results


def print_summary(results: list[dict]):
    import statistics
    print(f"\n{'Municipio':<20} {'Meses':>6}  {'T_media':>8}  {'Precip_media':>12}  {'Zona'}")
    print("-" * 65)
    for entry in results:
        mun  = entry["municipio"]
        recs = entry.get("records", [])
        if not recs:
            continue
        temp = [r["t2m"]         for r in recs if r.get("t2m")         is not None]
        prec = [r["prectotcorr"] for r in recs if r.get("prectotcorr") is not None]
        zona = MUNICIPIOS.get(mun, {}).get("zona", "—")
        t_str = f"{statistics.mean(temp):.1f}°C" if temp else "—"
        p_str = f"{statistics.mean(prec):.1f} mm/d" if prec else "—"
        print(f"  {mun:<18} {len(recs):>6}  {t_str:>8}  {p_str:>12}  {zona}")


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)

    start = int(sys.argv[1]) if len(sys.argv) > 1 else 2010
    end   = int(sys.argv[2]) if len(sys.argv) > 2 else 2024

    print(f"=== NASA POWER — {len(MUNICIPIOS)} municipios ({start}-{end}) ===\n")

    data = fetch_all(start, end)

    if data:
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        total_records = sum(len(e.get("records", [])) for e in data)
        print(f"\nGuardado: {OUT_PATH}")
        print(f"Total registros mensuales: {total_records:,}")
        print_summary(data)
    else:
        print("No se obtuvieron datos.")
