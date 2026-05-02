"""
Procesa archivos NetCDF descargados de ERA5-Land y extrae métricas
agroclimaticas por municipio para ser consumidas por el frontend.

Dependencias:
    pip install xarray netCDF4 numpy pandas
"""

import xarray as xr
import numpy as np
import pandas as pd
import json
import os
import zipfile
import tempfile

# Municipios y coordenadas (deben coincidir con era5_client.py)
MUNICIPIOS = {
    "Chimaltenango": {"lat": 14.6614, "lon": -90.8197},
    "Sacatepequez":  {"lat": 14.5586, "lon": -90.7295},
    "Guatemala":     {"lat": 14.6349, "lon": -90.5069},
}

KELVIN_OFFSET = 273.15  # Conversión K → °C


def extract_metrics(nc_path: str) -> list[dict]:
    """
    Extrae temperatura, precipitación y humedad relativa estimada
    para cada municipio desde un archivo NetCDF de ERA5-Land.

    Args:
        nc_path: Ruta al archivo .nc descargado.

    Returns:
        Lista de dicts con métricas por municipio, lista para el frontend.
    """
    # El nuevo CDS API entrega el NetCDF dentro de un ZIP
    if zipfile.is_zipfile(nc_path):
        with zipfile.ZipFile(nc_path) as z:
            inner = z.namelist()[0]
            tmp_dir = tempfile.mkdtemp()
            nc_path = z.extract(inner, tmp_dir)

    ds = xr.open_dataset(nc_path, engine="netcdf4")
    results = []

    for municipio, coords in MUNICIPIOS.items():
        point = ds.sel(
            latitude=coords["lat"],
            longitude=coords["lon"],
            method="nearest"
        )

        # Temperatura media diaria (°C)
        temp_k = float(point["t2m"].mean().values)
        temperature = round(temp_k - KELVIN_OFFSET, 1)

        # Precipitación total diaria (mm) — ERA5 viene en metros
        precip_m = float(point["tp"].sum().values)
        rainfall = round(precip_m * 1000, 1)

        # Humedad relativa estimada desde temperatura de punto de rocío
        dew_k = float(point["d2m"].mean().values)
        dew_c = dew_k - KELVIN_OFFSET
        humidity = round(_estimate_rh(temperature, dew_c), 1)

        # Humedad volumétrica del suelo capa 1 (proxy de pH indirecto)
        soil_moisture = float(point["swvl1"].mean().values)

        results.append({
            "municipio": municipio,
            "temperature": temperature,
            "rainfall": rainfall,
            "humidity": humidity,
            "soilMoisture": round(soil_moisture, 3),
        })

    ds.close()
    return results


def _estimate_rh(temp_c: float, dew_c: float) -> float:
    """Estima humedad relativa (%) usando la fórmula de Magnus."""
    a, b = 17.625, 243.04
    rh = 100 * np.exp((a * dew_c) / (b + dew_c)) / np.exp((a * temp_c) / (b + temp_c))
    return float(np.clip(rh, 0, 100))


def save_as_json(metrics: list[dict], output_path: str = None) -> str:
    """Guarda las métricas procesadas como JSON para el frontend."""
    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "models", "latest_metrics.json"
        )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"[Process] Métricas guardadas en: {output_path}")
    return output_path


def process_all(raw_dir: str = None) -> str:
    """
    Procesa todos los archivos .nc en raw_dir y guarda el promedio
    de métricas por municipio en latest_metrics.json.
    """
    if raw_dir is None:
        raw_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "raw")

    nc_files = sorted([
        os.path.join(raw_dir, f)
        for f in os.listdir(raw_dir)
        if f.endswith(".nc")
    ])

    if not nc_files:
        print("[Process] No se encontraron archivos .nc en", raw_dir)
        return None

    print(f"[Process] Procesando {len(nc_files)} archivos ERA5-Land...")

    all_records = []
    for i, nc_path in enumerate(nc_files, 1):
        fname = os.path.basename(nc_path)
        print(f"  [{i}/{len(nc_files)}] {fname} ...", end=" ", flush=True)
        try:
            metrics = extract_metrics(nc_path)
            all_records.extend(metrics)
            print("OK")
        except Exception as e:
            print(f"OMITIDO ({e})")

    if not all_records:
        print("[Process] No se pudo extraer ninguna métrica.")
        return None

    # Promediar por municipio
    df = pd.DataFrame(all_records)
    aggregated = (
        df.groupby("municipio", as_index=False)
          .agg({"temperature": "mean", "rainfall": "mean",
                "humidity": "mean", "soilMoisture": "mean"})
          .round({"temperature": 1, "rainfall": 1, "humidity": 1, "soilMoisture": 3})
    )

    result = aggregated.to_dict(orient="records")
    out_path = save_as_json(result)

    print("\n=== Promedios ERA5-Land (2010-2026) ===")
    print(aggregated.to_string(index=False))
    return out_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        # Modo archivo único: python process_era5.py era5_land_2024.nc
        nc_file = sys.argv[1]
        metrics = extract_metrics(nc_file)
        save_as_json(metrics)
        df = pd.DataFrame(metrics)
        print("\n=== Métricas extraídas ===")
        print(df.to_string(index=False))
    else:
        # Modo batch: python process_era5.py  → procesa toda la carpeta raw/
        process_all()
