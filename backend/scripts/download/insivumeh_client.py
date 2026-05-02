"""
Descarga observaciones recientes de INSIVUMEH y las agrega por municipio.

Fuente:
    La pagina oficial de INSIVUMEH publica HTML que consume CSVs del repo:
    https://github.com/Climatologia-INSIVUMEH/monthly_data_by_station_csv

Alcance:
    - Observaciones diarias recientes por estacion (ventana corta, ~30 dias)
    - Agregacion mensual reciente por municipio usando la estacion mas cercana

Salidas:
    data/raw/insivumeh/insivumeh_stations_daily.csv
    data/sources/insivumeh_recent_mensual.csv
    data/raw/insivumeh/insivumeh_station_catalog.json

Uso:
    python insivumeh_client.py
"""

from __future__ import annotations

import csv
import io
import json
import math
import os
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from municipios_nacional import MUNICIPIOS


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw", "insivumeh")
SOURCES_DIR = os.path.join(BASE_DIR, "data", "sources")

OUT_DAILY = os.path.join(RAW_DIR, "insivumeh_stations_daily.csv")
OUT_MONTHLY = os.path.join(SOURCES_DIR, "insivumeh_recent_mensual.csv")
OUT_CATALOG = os.path.join(RAW_DIR, "insivumeh_station_catalog.json")

GITHUB_API_URL = (
    "https://api.github.com/repos/Climatologia-INSIVUMEH/"
    "monthly_data_by_station_csv/contents/outputcsv"
)
OFFICIAL_SITE_URL = "https://insivumeh.gob.gt/img/INSIVUMEH.html"
REQUEST_HEADERS = {"User-Agent": "AgroClimaGT/1.0"}
MAX_ASSIGN_DISTANCE_KM = float(os.getenv("INSIVUMEH_MAX_DISTANCE_KM", "60"))
SLEEP_BETWEEN_FILES = float(os.getenv("INSIVUMEH_SLEEP_SECONDS", "0.1"))


def _fetch_json(url: str):
    req = urllib.request.Request(url, headers=REQUEST_HEADERS)
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers=REQUEST_HEADERS)
    with urllib.request.urlopen(req, timeout=40) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _safe_download_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    safe_path = urllib.parse.quote(urllib.parse.unquote(parts.path), safe="/")
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, safe_path, parts.query, parts.fragment))


def _normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.upper().replace(".CSV", "")
    cleaned = []
    for ch in value:
        cleaned.append(ch if ch.isalnum() else " ")
    return " ".join("".join(cleaned).split())


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _nearest_municipio(lat: float, lon: float) -> tuple[str | None, float | None]:
    best_name = None
    best_dist = None
    for municipio, meta in MUNICIPIOS.items():
        dist = _haversine_km(lat, lon, meta["lat"], meta["lon"])
        if best_dist is None or dist < best_dist:
            best_name = municipio
            best_dist = dist
    if best_dist is None or best_dist > MAX_ASSIGN_DISTANCE_KM:
        return None, best_dist
    return best_name, best_dist


def list_station_files() -> list[dict]:
    payload = _fetch_json(GITHUB_API_URL)
    items = [item for item in payload if item.get("type") == "file" and item.get("name", "").lower().endswith(".csv")]
    deduped: dict[str, dict] = {}
    for item in items:
        key = _normalize_name(item["name"])
        current = deduped.get(key)
        if current is None or len(item["name"]) < len(current["name"]):
            deduped[key] = item
    return sorted(deduped.values(), key=lambda item: _normalize_name(item["name"]))


def _parse_station_csv(file_meta: dict) -> list[dict]:
    text = _fetch_text(_safe_download_url(file_meta["download_url"]))
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        fecha = row.get("fecha")
        if not fecha:
            continue
        try:
            ts = datetime.fromisoformat(fecha)
        except ValueError:
            continue

        def num(key: str):
            raw = row.get(key)
            if raw in (None, "", "NA", "nan"):
                return None
            try:
                return float(raw)
            except ValueError:
                return None

        lat = num("Latitud")
        lon = num("Longitud")
        municipio_match, distance_km = _nearest_municipio(lat, lon) if lat is not None and lon is not None else (None, None)
        temp_mean = num("tseca")
        if temp_mean is None:
            tmin = num("tmin")
            tmax = num("tmax")
            if tmin is not None and tmax is not None:
                temp_mean = round((tmin + tmax) / 2.0, 2)

        rows.append({
            "date": ts.date().isoformat(),
            "year": ts.year,
            "month": ts.month,
            "station_file": file_meta["name"],
            "station_name": row.get("Nombre") or file_meta["name"].replace(".csv", ""),
            "station_id": row.get("ID"),
            "station_code": row.get("ID_INSIVUMEH"),
            "lat": lat,
            "lon": lon,
            "altitud_m": num("Altitud"),
            "municipio": municipio_match,
            "distance_km": round(distance_km, 2) if distance_km is not None else None,
            "rainfall": num("lluvia"),
            "temperature": temp_mean,
            "temp_min": num("tmin"),
            "temp_max": num("tmax"),
            "humidity": num("hum_rel"),
            "wind_speed": num("vel_viento"),
            "solar_brightness": num("bri_solar"),
            "cloudiness": num("nub"),
            "pressure": num("pre_atmos"),
            "evap_tank": num("eva_tan"),
            "source": "INSIVUMEH",
            "source_url": OFFICIAL_SITE_URL,
        })
    return rows


def build_daily_dataframe() -> pd.DataFrame:
    station_files = list_station_files()
    rows = []
    catalog = []

    print(f"=== INSIVUMEH recientes — {len(station_files)} estaciones CSV ===\n")
    for idx, file_meta in enumerate(station_files, 1):
        print(f"[{idx:03d}/{len(station_files)}] {file_meta['name']}...", end=" ", flush=True)
        try:
            parsed = _parse_station_csv(file_meta)
            rows.extend(parsed)
            if parsed:
                sample = parsed[0]
                catalog.append({
                    "station_file": file_meta["name"],
                    "station_name": sample["station_name"],
                    "station_id": sample["station_id"],
                    "station_code": sample["station_code"],
                    "lat": sample["lat"],
                    "lon": sample["lon"],
                    "altitud_m": sample["altitud_m"],
                    "municipio": sample["municipio"],
                    "distance_km": sample["distance_km"],
                    "records": len(parsed),
                    "min_date": min(r["date"] for r in parsed),
                    "max_date": max(r["date"] for r in parsed),
                })
            print(f"{len(parsed)} filas")
        except Exception as exc:
            print(f"omitido ({exc})")
        time.sleep(SLEEP_BETWEEN_FILES)

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["municipio", "station_name", "date"]).reset_index(drop=True)

    os.makedirs(RAW_DIR, exist_ok=True)
    with open(OUT_CATALOG, "w", encoding="utf-8") as fh:
        json.dump(catalog, fh, ensure_ascii=False, indent=2)
    return df


def build_recent_monthly(df_daily: pd.DataFrame) -> pd.DataFrame:
    if df_daily.empty:
        return pd.DataFrame(columns=[
            "municipio", "year", "month", "temperature", "rainfall", "humidity",
            "temp_min", "temp_max", "wind_speed", "station_count", "sample_days",
            "min_date", "max_date", "source", "source_url",
        ])

    usable = df_daily[df_daily["municipio"].notna()].copy()
    grouped = (
        usable.groupby(["municipio", "year", "month"], as_index=False)
        .agg(
            temperature=("temperature", "mean"),
            rainfall=("rainfall", "sum"),
            humidity=("humidity", "mean"),
            temp_min=("temp_min", "mean"),
            temp_max=("temp_max", "mean"),
            wind_speed=("wind_speed", "mean"),
            station_count=("station_name", "nunique"),
            sample_days=("date", "nunique"),
            min_date=("date", "min"),
            max_date=("date", "max"),
            mean_distance_km=("distance_km", "mean"),
        )
    )

    for col in ["temperature", "rainfall", "humidity", "temp_min", "temp_max", "wind_speed", "mean_distance_km"]:
        grouped[col] = grouped[col].round(3)

    grouped["source"] = "INSIVUMEH"
    grouped["source_url"] = OFFICIAL_SITE_URL
    return grouped.sort_values(["municipio", "year", "month"]).reset_index(drop=True)


def main() -> int:
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(SOURCES_DIR, exist_ok=True)

    daily_df = build_daily_dataframe()
    daily_df.to_csv(OUT_DAILY, index=False)
    monthly_df = build_recent_monthly(daily_df)
    monthly_df.to_csv(OUT_MONTHLY, index=False)

    if daily_df.empty:
        print("\nNo se obtuvieron observaciones de INSIVUMEH.")
        return 1

    print(f"\nGuardado diario : {OUT_DAILY} ({len(daily_df)} filas)")
    print(f"Guardado mensual: {OUT_MONTHLY} ({len(monthly_df)} filas)")
    print(f"Municipios con datos recientes: {monthly_df['municipio'].nunique() if not monthly_df.empty else 0}")
    if not monthly_df.empty:
        print(
            "Ventana observada: "
            f"{monthly_df['min_date'].min()} a {monthly_df['max_date'].max()}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
