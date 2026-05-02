"""
ERA5-Land data client for AgroClima GT — cobertura nacional Guatemala.
Descarga variables climaticas base desde Copernicus Climate Data Store (CDS).

Variables:
    2m_temperature              → temperatura media (convertir K→°C)
    total_precipitation         → precipitacion total (convertir m→mm)
    2m_dewpoint_temperature     → punto de rocio (para estimar HR)
    volumetric_soil_water_layer_1 → humedad suelo 0-7 cm (swvl1)

Salida:
    data/raw/era5/era5_land_YYYY.nc
    data/raw/era5/era5_municipios_metadata.json

Requirements:
    pip install "cdsapi>=0.7.7"

Setup:
    Crear %USERPROFILE%\\.cdsapirc con:
        url: https://cds.climate.copernicus.eu/api
        key: <YOUR-PERSONAL-ACCESS-TOKEN>

Uso:
    python era5_client.py              → rango 2010-2026
    python era5_client.py 2010 2026    → rango personalizado
    python era5_client.py 2022         → un solo año
"""

import os
import sys
import cdsapi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from municipios_nacional import MUNICIPIOS, AREA_BBOX_NACIONAL

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR  = os.path.join(BASE_DIR, "data", "raw", "era5")
META_PATH = os.path.join(RAW_DIR, "era5_municipios_metadata.json")

ERA5_VARIABLES = [
    "2m_temperature",
    "total_precipitation",
    "2m_dewpoint_temperature",
    "volumetric_soil_water_layer_1",
]


def write_metadata():
    os.makedirs(RAW_DIR, exist_ok=True)
    metadata = []
    for municipio, coords in MUNICIPIOS.items():
        metadata.append({
            "municipio": municipio,
            "lat": coords["lat"],
            "lon": coords["lon"],
            "depto": coords.get("depto"),
            "zona": coords.get("zona"),
            "altitud_m": coords.get("altitud_m"),
        })
    with open(META_PATH, "w", encoding="utf-8") as f:
        import json
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"[ERA5] Metadata de municipios guardada: {META_PATH}")


def fetch_year(year: int) -> str:
    os.makedirs(RAW_DIR, exist_ok=True)
    output_path = os.path.join(RAW_DIR, f"era5_land_{year}.nc")

    if os.path.exists(output_path):
        print(f"[ERA5] {year} ya existe, se omite: {output_path}")
        return output_path

    client = cdsapi.Client()
    request = {
        "variable":    ERA5_VARIABLES,
        "year":        [str(year)],
        "month":       [f"{m:02d}" for m in range(1, 13)],
        "day":         [f"{d:02d}" for d in range(1, 32)],
        "time":        ["06:00", "12:00", "18:00"],
        "data_format": "netcdf",
        "area":        AREA_BBOX_NACIONAL,
    }

    print(f"[ERA5] Descargando año {year} ({len(MUNICIPIOS)} municipios)...")
    client.retrieve("reanalysis-era5-land", request, output_path)
    print(f"[ERA5] Guardado: {output_path}")
    return output_path


def fetch_range(start_year: int = 2010, end_year: int = 2026) -> list[str]:
    print(f"\n[ERA5] Descargando {start_year}-{end_year} para {len(MUNICIPIOS)} municipios.")
    print(f"       Zona: {AREA_BBOX_NACIONAL}")
    print(f"       Salida: {RAW_DIR}\n")
    write_metadata()
    paths = []
    for year in range(start_year, end_year + 1):
        path = fetch_year(year)
        paths.append(path)
    return paths


if __name__ == "__main__":
    if len(sys.argv) == 3:
        fetch_range(int(sys.argv[1]), int(sys.argv[2]))
    elif len(sys.argv) == 2:
        write_metadata()
        fetch_year(int(sys.argv[1]))
    else:
        fetch_range(2010, 2026)
