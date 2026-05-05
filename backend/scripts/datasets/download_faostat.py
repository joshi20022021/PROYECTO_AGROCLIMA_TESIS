"""
download_faostat.py — Descarga rendimientos reales FAOSTAT para Guatemala
y los usa para calibrar el yield_pct sintetico del dataset de entrenamiento.

Uso:
  Con credenciales (recomendado - obtiene token automaticamente):
    python scripts/datasets/download_faostat.py --user EMAIL --password PASS

  Con token ya obtenido (expira en 1 hora):
    python scripts/datasets/download_faostat.py --token TOKEN

  Solo procesar datos ya descargados (sin red):
    python scripts/datasets/download_faostat.py --offline
"""

import json
import os
import sys
import urllib.request
import urllib.parse
import argparse

import numpy as np
import pandas as pd

# ── Argumentos ────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser()
parser.add_argument("--user",     help="Email FAOSTAT")
parser.add_argument("--password", help="Password FAOSTAT")
parser.add_argument("--token",    help="JWT token ya obtenido")
parser.add_argument("--offline",  action="store_true", help="Solo procesar datos ya descargados")
# Compatibilidad: primer arg posicional = token
if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
    sys.argv = [sys.argv[0], "--token", sys.argv[1]] + sys.argv[2:]
ARGS = parser.parse_args()

BASE_URL = "https://faostatservices.fao.org/api/v1/en"
AUTH_URL = "https://faostatservices.fao.org/api/v1/auth/login"

# Guatemala = area 89
AREA = 89
YEARS = list(range(2010, 2024))  # 2010-2023

# Mapeo cultivo del modelo → código FAOSTAT + etiqueta oficial
CROP_ITEMS = {
    "Maiz":     (56,  "Maize (corn)"),
    "Frijol":   (176, "Beans, dry"),
    "Cafe":     (656, "Coffee, green"),
    "Arroz":    (27,  "Rice, paddy"),
    "Papa":     (116, "Potatoes"),
    "Tomate":   (388, "Tomatoes"),
    "Aguacate": (572, "Avocados"),
    "Cacao":    (661, "Cocoa beans"),
}

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASETS_DIR = os.path.join(BASE_DIR, "data", "datasets")
SOURCES_DIR  = os.path.join(BASE_DIR, "data", "sources")

COMB_PATH    = os.path.join(DATASETS_DIR, "dataset_combinado.csv")
OM_PATH      = os.path.join(DATASETS_DIR, "dataset_openmeteo.csv")
FAOSTAT_RAW  = os.path.join(SOURCES_DIR,  "faostat_yields_guatemala.csv")
OUT_PATH     = os.path.join(DATASETS_DIR, "dataset_faostat.csv")

RNG = np.random.default_rng(42)


# ── Auth y fetch ─────────────────────────────────────────────────────────────

_token_cache = {"token": ARGS.token or ""}


def _get_token() -> str:
    if _token_cache["token"]:
        return _token_cache["token"]
    if not (ARGS.user and ARGS.password):
        raise ValueError(
            "Sin credenciales. Usa:\n"
            "  python scripts/datasets/download_faostat.py --user EMAIL --password PASS\n"
            "  o: python scripts/datasets/download_faostat.py --token TOKEN"
        )
    print("Obteniendo token FAOSTAT...")
    body = urllib.parse.urlencode({"username": ARGS.user, "password": ARGS.password}).encode()
    req = urllib.request.Request(
        AUTH_URL, data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "AgroClimaGT/1.0"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        resp = json.loads(r.read())
    token = resp.get("access_token") or resp.get("AccessToken") or resp.get("token")
    if not token:
        raise ValueError(f"No se obtuvo token. Respuesta: {resp}")
    _token_cache["token"] = token
    print("  Token obtenido correctamente.")
    return token


def _fetch(path: str) -> dict:
    token = _get_token()
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={"Authorization": f"Bearer {token}", "User-Agent": "AgroClimaGT/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def _discover_codes() -> tuple[str, str]:
    """Descubre el codigo de area para Guatemala y el codigo de elemento Yield."""
    print("  Descubriendo codigos FAOSTAT...")

    # Buscar Guatemala en codelist de areas
    areas = _fetch("/codes/area/QCL")
    area_code = None
    for a in areas.get("data", []):
        label = str(a.get("label", "") or a.get("Label", "") or list(a.values())[1] if len(a) > 1 else "")
        code  = str(a.get("code", "") or a.get("Code", "") or list(a.values())[0])
        if "uatemala" in label and "City" not in label:
            area_code = code
            print(f"  Guatemala: code={code}, label={label}")
            break

    if not area_code:
        print("  Guatemala no encontrada, usando codigo 89")
        area_code = "89"

    # Buscar elemento Yield en codelist de elementos
    elems = _fetch("/codes/element/QCL")
    elem_code = None
    for e in elems.get("data", []):
        label = str(e.get("label", "") or e.get("Label", "") or "")
        code  = str(e.get("code", "") or e.get("Code", "") or "")
        if "ield" in label and "hg" in label.lower():
            elem_code = code
            print(f"  Yield element: code={code}, label={label}")
            break
        if "ield" in label and elem_code is None:
            elem_code = code
            print(f"  Yield element (fallback): code={code}, label={label}")

    if not elem_code:
        print("  Elemento Yield no encontrado, usando 5419")
        elem_code = "5419"

    return area_code, elem_code


def download_yields() -> pd.DataFrame:
    """Descarga yield (hg/ha) por cultivo y año para Guatemala."""
    area_code, elem_code = _discover_codes()

    item_codes = ",".join(str(v[0]) for v in CROP_ITEMS.values())
    year_str   = ",".join(str(y) for y in YEARS)
    path = f"/data/QCL?area={area_code}&element={elem_code}&item={item_codes}&year={year_str}"

    print(f"Descargando: {len(CROP_ITEMS)} cultivos x {len(YEARS)} anos...")
    data = _fetch(path)
    records = data.get("data", [])

    # Si sigue vacío, intentar sin filtro de item para ver qué hay disponible
    if not records:
        print("  Sin datos con items especificos. Probando solo Maiz...")
        data2 = _fetch(f"/data/QCL?area={area_code}&element={elem_code}&item=56&year=2022")
        sample = data2.get("data", [])
        if sample:
            print(f"  Muestra: {sample[0]}")
        else:
            print(f"  Respuesta completa: {json.dumps(data2)[:500]}")
        raise ValueError("Sin datos en FAOSTAT QCL para Guatemala. Revisa los codigos.")

    code_to_crop = {v[0]: k for k, v in CROP_ITEMS.items()}

    rows = []
    for rec in records:
        item_code = int(rec.get("Item Code", 0))
        crop = code_to_crop.get(item_code)
        if not crop:
            continue
        val = rec.get("Value")
        if val is None:
            continue
        rows.append({
            "crop":       crop,
            "year":       int(rec["Year"]),
            "yield_hgha": float(val),
            "unit":       rec.get("Unit", "hg/ha"),
            "item_fao":   rec.get("Item", ""),
        })

    df = pd.DataFrame(rows)
    print(f"  Registros descargados: {len(df)}")
    for crop in CROP_ITEMS:
        n = (df["crop"] == crop).sum()
        if n:
            mean_tha = df[df["crop"] == crop]["yield_hgha"].mean() / 10_000
            print(f"    {crop:<12} {n} años | promedio: {mean_tha:.2f} t/ha")
        else:
            print(f"    {crop:<12} SIN DATOS")

    os.makedirs(SOURCES_DIR, exist_ok=True)
    df.to_csv(FAOSTAT_RAW, index=False)
    print(f"  Guardado en: {FAOSTAT_RAW}")
    return df


# ── Normalización ─────────────────────────────────────────────────────────────

def build_year_factors(df_fao: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada cultivo, normaliza los rendimientos entre 0 (peor año) y 1 (mejor año).
    Años sin dato FAOSTAT reciben factor 0.5 (neutro).
    """
    rows = []
    for crop, grp in df_fao.groupby("crop"):
        mn, mx = grp["yield_hgha"].min(), grp["yield_hgha"].max()
        rng = mx - mn if mx > mn else 1.0
        for _, r in grp.iterrows():
            factor = (r["yield_hgha"] - mn) / rng
            rows.append({"crop": crop, "year": int(r["year"]), "fao_factor": round(factor, 4)})
    return pd.DataFrame(rows)


# ── Aplicar calibración ───────────────────────────────────────────────────────

def calibrate_dataset(df: pd.DataFrame, factors: pd.DataFrame) -> pd.DataFrame:
    """
    Ajusta yield_pct del dataset usando los factores FAOSTAT.
    yield_adj = yield_base x (0.75 + 0.50 x factor)
      factor=0   -> multiplicador 0.75 (anio muy malo)
      factor=0.5 -> multiplicador 1.00 (anio neutro)
      factor=1   -> multiplicador 1.25 (anio muy bueno)
    Anios sin cobertura FAOSTAT usan el factor promedio del cultivo (100% cobertura).
    """
    factor_map = {(r["crop"], r["year"]): r["fao_factor"] for _, r in factors.iterrows()}
    # Factor promedio por cultivo para anos sin cobertura FAOSTAT
    crop_avg = factors.groupby("crop")["fao_factor"].mean().to_dict()

    def adjust(row):
        factor = factor_map.get((row["crop"], row["year"]))
        if factor is None:
            factor = crop_avg.get(row["crop"], 0.5)
        multiplier = 0.75 + 0.50 * factor
        return float(np.clip(row["yield_pct"] * multiplier, 5.0, 100.0))

    df = df.copy()
    df["yield_pct"] = df.apply(adjust, axis=1)
    return df


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=== Calibracion FAOSTAT - dataset de entrenamiento ===\n")

    # 1) Descargar (o cargar si ya existe)
    if os.path.exists(FAOSTAT_RAW):
        print(f"Usando datos FAOSTAT ya descargados: {FAOSTAT_RAW}")
        df_fao = pd.read_csv(FAOSTAT_RAW)
    else:
        df_fao = download_yields()

    # 2) Factores de normalización
    factors = build_year_factors(df_fao)
    print(f"\nFactores calculados: {len(factors)} combinaciones cultivo-año")
    print(factors.pivot(index="year", columns="crop", values="fao_factor").round(2).to_string())

    # 3) Cargar dataset base
    base_path = COMB_PATH if os.path.exists(COMB_PATH) else OM_PATH
    print(f"\nCargando dataset base: {os.path.basename(base_path)}…")
    df = pd.read_csv(base_path)
    print(f"  {len(df):,} filas | yield_pct promedio: {df['yield_pct'].mean():.1f}%")

    # 4) Calibrar
    print("Aplicando calibración FAOSTAT…")
    df_cal = calibrate_dataset(df, factors)

    direct = df_cal.merge(factors, on=["crop", "year"]).shape[0]
    print(f"  Cobertura directa FAOSTAT: {direct:,} / {len(df_cal):,} "
          f"({100*direct/len(df_cal):.0f}%)")
    print(f"  Cobertura total (incl. promedio por cultivo): {len(df_cal):,} (100%)")
    print(f"  yield_pct promedio: {df['yield_pct'].mean():.1f}% -> {df_cal['yield_pct'].mean():.1f}%")
    print(f"  yield_pct std:      {df['yield_pct'].std():.1f}% -> {df_cal['yield_pct'].std():.1f}%")

    # 5) Guardar
    os.makedirs(DATASETS_DIR, exist_ok=True)
    df_cal.to_csv(OUT_PATH, index=False)
    size_mb = os.path.getsize(OUT_PATH) / 1_048_576
    print(f"\nGuardado: {OUT_PATH}  ({size_mb:.1f} MB)")

    print("\nPara reentrenar con el dataset calibrado:")
    print("  python scripts/training/model_xgboost.py train")


if __name__ == "__main__":
    main()
