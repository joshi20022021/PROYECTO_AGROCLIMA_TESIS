"""
Descarga datos REALES de suelo desde SoilGrids v2.0 (ISRIC).
API gratuita, sin autenticación.

Variables descargadas:
    phh2o    → pH real del suelo en agua        ← reemplaza el pH aleatorio del modelo
    soc      → carbono orgánico (g/kg)          ← fertilidad del suelo
    clay     → contenido de arcilla (g/kg)      ← retención de agua
    sand     → contenido de arena (g/kg)        ← drenaje
    silt     → contenido de limo (g/kg)         ← textura
    bdod     → densidad aparente (cg/cm³)       ← compactación
    nitrogen → nitrógeno total (cg/kg)          ← fertilidad

Profundidades consultadas: 0-5 cm, 5-15 cm, 15-30 cm

Salida: data/processed/soilgrids_municipios.json

Uso:
    python soilgrids_client.py
"""

import json
import os
import time
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_PATH = os.path.join(BASE_DIR, "data", "sources", "soilgrids_municipios.json")

MUNICIPIOS = {
    "Chimaltenango": {"lat": 14.6614, "lon": -90.8197},
    "Sacatepequez":  {"lat": 14.5586, "lon": -90.7295},
    "Guatemala":     {"lat": 14.6349, "lon": -90.5069},
}

PROPERTIES = ["phh2o", "soc", "clay", "sand", "silt", "bdod", "nitrogen"]
DEPTHS     = ["0-5cm", "5-15cm", "15-30cm"]

BASE_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"


def build_url(lat: float, lon: float) -> str:
    props  = "&".join(f"property={p}" for p in PROPERTIES)
    depths = "&".join(f"depth={d}"    for d in DEPTHS)
    return f"{BASE_URL}?lon={lon}&lat={lat}&{props}&{depths}&value=mean"


def fetch_soilgrids(lat: float, lon: float, retries: int = 3) -> dict | None:
    url = build_url(lat, lon)
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={"Accept": "application/json", "User-Agent": "AgroClimaGT/1.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            print(f"    HTTP {e.code} — intento {attempt}/{retries}")
            if e.code == 429:
                time.sleep(10 * attempt)
            else:
                time.sleep(3)
        except Exception as e:
            print(f"    Error: {e} — intento {attempt}/{retries}")
            time.sleep(5)
    return None


def parse_response(raw: dict, municipio: str) -> dict:
    """Extrae valores promedio por profundidad desde la respuesta de SoilGrids."""
    result = {"municipio": municipio}

    layers = raw.get("properties", {}).get("layers", [])
    for layer in layers:
        prop = layer.get("name")
        unit = layer.get("unit_measure", {}).get("d_factor", 1)

        for depth_info in layer.get("depths", []):
            depth_label = depth_info.get("label", "")
            mean_raw    = depth_info.get("values", {}).get("mean")
            if mean_raw is None:
                continue

            # Convertir al valor real (dividir por d_factor)
            value = round(mean_raw / unit, 3) if unit else mean_raw

            # Clave: propiedad_profundidad (ej. phh2o_0-5cm)
            depth_key  = depth_label.replace(" ", "")
            result_key = f"{prop}_{depth_key}"
            result[result_key] = value

    return result


def fetch_all() -> list[dict]:
    results = []
    for municipio, coords in MUNICIPIOS.items():
        print(f"  Consultando {municipio} ({coords['lat']}, {coords['lon']})...")
        raw = fetch_soilgrids(coords["lat"], coords["lon"])
        if raw:
            parsed = parse_response(raw, municipio)
            results.append(parsed)
            # Mostrar pH como muestra
            ph = parsed.get("phh2o_0-5cm", "N/A")
            soc = parsed.get("soc_0-5cm", "N/A")
            print(f"    pH (0-5cm): {ph}  |  C.Org (0-5cm): {soc} g/kg")
        else:
            print(f"    No se pudo obtener datos para {municipio}")
        time.sleep(1)  # respetar rate limit
    return results


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    print("=== SoilGrids — Datos reales de suelo por municipio ===\n")
    print("Variables:", ", ".join(PROPERTIES))
    print("Profundidades:", ", ".join(DEPTHS))
    print()

    data = fetch_all()

    if data:
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nGuardado: {OUT_PATH}")
        print(f"Municipios: {len(data)}")

        print("\n=== Resumen de pH por municipio ===")
        for row in data:
            mun = row["municipio"]
            for depth in ["0-5cm", "5-15cm", "15-30cm"]:
                key = f"phh2o_{depth}"
                print(f"  {mun:15s} {depth}: pH = {row.get(key, 'N/A')}")
    else:
        print("\nNo se obtuvieron datos. Verifica la conexión o intenta más tarde.")
        print("Estado del servicio: https://rest.isric.org/")
