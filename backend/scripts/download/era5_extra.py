"""
ERA5-Land variables adicionales para AgroClima GT — cobertura nacional Guatemala.

Variables (2 lotes para no exceder límite CDS ~4000 campos/solicitud):

    Lote A — radiacion y evapotranspiracion:
        surface_solar_radiation_downwards        → radiacion solar real (J/m²)
        potential_evaporation                    → estres hidrico (m)
        evaporation_from_vegetation_transpiration → transpiracion real (m)

    Lote B — suelo profundo:
        volumetric_soil_water_layer_2  → humedad raices 7-28 cm (m³/m³)
        volumetric_soil_water_layer_3  → humedad profunda 28-100 cm (m³/m³)
        soil_temperature_level_1       → temperatura suelo 0-7 cm (K)

Salida: data/raw/era5/era5_extra_rad_YYYY.nc
        data/raw/era5/era5_extra_soil_YYYY.nc

Uso:
    python era5_extra.py              → rango 2010-2026
    python era5_extra.py 2020 2023    → rango especifico
    python era5_extra.py 2022         → un solo año
"""

import os
import sys
import cdsapi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from municipios_nacional import AREA_BBOX_NACIONAL

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR  = os.path.join(BASE_DIR, "data", "raw", "era5")

LOTE_A = [
    "surface_solar_radiation_downwards",
    "potential_evaporation",
    "evaporation_from_vegetation_transpiration",
]

LOTE_B = [
    "volumetric_soil_water_layer_2",
    "volumetric_soil_water_layer_3",
    "soil_temperature_level_1",
]


def _fetch_lote(year: int, variables: list, suffix: str) -> str:
    os.makedirs(RAW_DIR, exist_ok=True)
    output_path = os.path.join(RAW_DIR, f"era5_extra_{suffix}_{year}.nc")

    if os.path.exists(output_path):
        print(f"  [ya existe] {os.path.basename(output_path)}")
        return output_path

    client = cdsapi.Client()
    request = {
        "variable":    variables,
        "year":        [str(year)],
        "month":       [f"{m:02d}" for m in range(1, 13)],
        "day":         [f"{d:02d}" for d in range(1, 32)],
        "time":        ["12:00"],
        "data_format": "netcdf",
        "area":        AREA_BBOX_NACIONAL,
    }
    client.retrieve("reanalysis-era5-land", request, output_path)
    print(f"  Guardado: {os.path.basename(output_path)}")
    return output_path


def fetch_extra_year(year: int) -> tuple[str, str]:
    print(f"\n[ERA5-Extra] Año {year}")
    print(f"  Lote A: radiacion + evapotranspiracion...")
    path_a = _fetch_lote(year, LOTE_A, "rad")
    print(f"  Lote B: humedad profunda + temperatura suelo...")
    path_b = _fetch_lote(year, LOTE_B, "soil")
    return path_a, path_b


def fetch_extra_range(start_year: int = 2010, end_year: int = 2026):
    print(f"\n[ERA5-Extra] Descargando {start_year}-{end_year}")
    print(f"             Zona: {AREA_BBOX_NACIONAL}")
    print(f"             Salida: {RAW_DIR}\n")
    all_paths = []
    for year in range(start_year, end_year + 1):
        paths = fetch_extra_year(year)
        all_paths.extend(paths)
    print(f"\n[ERA5-Extra] Completado. {len(all_paths)} archivos descargados.")
    return all_paths


if __name__ == "__main__":
    if len(sys.argv) == 3:
        fetch_extra_range(int(sys.argv[1]), int(sys.argv[2]))
    elif len(sys.argv) == 2:
        fetch_extra_year(int(sys.argv[1]))
    else:
        fetch_extra_range(2010, 2026)
