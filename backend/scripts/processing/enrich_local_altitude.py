"""
Enriquece archivos locales ya descargados con metadata estática por municipio.

Agrega o corrige:
    - altitud_m
    - zona
    - depto

Sin volver a descargar datos remotos. No modifica archivos .nc de ERA5;
en su lugar genera un archivo companion con la metadata por municipio.

Archivos objetivo:
    data/raw/openmeteo/open_meteo_municipios.json
    data/raw/nasa_power/nasa_power_municipios.json
    data/raw/era5/era5_municipios_metadata.json
    data/sources/era5_mensual.csv
    data/sources/nasa_power_mensual.csv
    data/datasets/dataset_openmeteo.csv   (si existe)
"""

import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "download"))
from municipios_nacional import MUNICIPIOS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OPENMETEO_JSON = os.path.join(BASE_DIR, "data", "raw", "openmeteo", "open_meteo_municipios.json")
NASA_JSON = os.path.join(BASE_DIR, "data", "raw", "nasa_power", "nasa_power_municipios.json")
ERA5_META_JSON = os.path.join(BASE_DIR, "data", "raw", "era5", "era5_municipios_metadata.json")

ERA5_CSV = os.path.join(BASE_DIR, "data", "sources", "era5_mensual.csv")
NASA_CSV = os.path.join(BASE_DIR, "data", "sources", "nasa_power_mensual.csv")
OPENMETEO_DATASET = os.path.join(BASE_DIR, "data", "datasets", "dataset_openmeteo.csv")


def get_meta(municipio: str) -> dict:
    meta = MUNICIPIOS.get(municipio, {})
    return {
        "depto": meta.get("depto"),
        "zona": meta.get("zona"),
        "altitud_m": meta.get("altitud_m"),
    }


def enrich_json(path: str) -> tuple[int, int]:
    if not os.path.exists(path):
        print(f"[SKIP] No existe: {path}")
        return 0, 0

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    municipios = 0
    records = 0
    for entry in data:
        municipio = entry.get("municipio")
        if not municipio:
            continue
        meta = get_meta(municipio)
        entry.update(meta)
        municipios += 1

        for record in entry.get("records", []):
            record.update(meta)
            records += 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return municipios, records


def enrich_csv(path: str, ensure_zona: bool = False, ensure_depto: bool = False) -> tuple[int, int]:
    if not os.path.exists(path):
        print(f"[SKIP] No existe: {path}")
        return 0, 0

    df = pd.read_csv(path)
    if "municipio" not in df.columns:
        print(f"[SKIP] Sin columna municipio: {path}")
        return 0, 0

    meta_df = pd.DataFrame(
        [{"municipio": municipio, **get_meta(municipio)} for municipio in MUNICIPIOS]
    )

    cols_to_drop = [c for c in ("depto", "zona", "altitud_m") if c in df.columns]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)

    df = df.merge(meta_df, on="municipio", how="left")

    ordered = list(df.columns)
    if not ensure_depto and "depto" in ordered:
        ordered.remove("depto")
    if not ensure_zona and "zona" in ordered:
        ordered.remove("zona")
    if "altitud_m" in ordered:
        ordered.remove("altitud_m")

    insert_after = "municipio"
    if "zona" in df.columns and ensure_zona:
        ordered.insert(ordered.index(insert_after) + 1, "zona")
        insert_after = "zona"
    if "depto" in df.columns and ensure_depto:
        ordered.insert(ordered.index(insert_after) + 1, "depto")
        insert_after = "depto"
    ordered.insert(ordered.index(insert_after) + 1, "altitud_m")

    df = df[ordered]
    df.to_csv(path, index=False)
    return len(df), int(df["altitud_m"].notna().sum()) if "altitud_m" in df.columns else 0


def write_era5_metadata() -> int:
    os.makedirs(os.path.dirname(ERA5_META_JSON), exist_ok=True)
    payload = [
        {
            "municipio": municipio,
            "lat": coords["lat"],
            "lon": coords["lon"],
            "depto": coords.get("depto"),
            "zona": coords.get("zona"),
            "altitud_m": coords.get("altitud_m"),
        }
        for municipio, coords in MUNICIPIOS.items()
    ]
    with open(ERA5_META_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return len(payload)


def main():
    print("=== Enriquecimiento local de altitud/metadata ===\n")

    mun, rec = enrich_json(OPENMETEO_JSON)
    print(f"[OK] Open-Meteo JSON    : {mun} municipios, {rec} registros enriquecidos")

    mun, rec = enrich_json(NASA_JSON)
    print(f"[OK] NASA POWER JSON   : {mun} municipios, {rec} registros enriquecidos")

    total = write_era5_metadata()
    print(f"[OK] ERA5 metadata     : {total} municipios en {ERA5_META_JSON}")

    rows, with_alt = enrich_csv(ERA5_CSV, ensure_zona=True, ensure_depto=False)
    print(f"[OK] ERA5 CSV          : {rows} filas, {with_alt} con altitud_m")

    rows, with_alt = enrich_csv(NASA_CSV, ensure_zona=True, ensure_depto=False)
    print(f"[OK] NASA POWER CSV    : {rows} filas, {with_alt} con altitud_m")

    rows, with_alt = enrich_csv(OPENMETEO_DATASET, ensure_zona=False, ensure_depto=False)
    if rows:
        print(f"[OK] Dataset OpenMeteo : {rows} filas, {with_alt} con altitud_m")

    print("\nListo. No se modificaron archivos .nc.")


if __name__ == "__main__":
    main()
