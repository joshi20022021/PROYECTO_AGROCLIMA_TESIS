"""
Carga recomendaciones_cultivo.csv → tabla recomendaciones_cultivo en PostgreSQL.

Uso:
    python scripts/seed_recommendations.py            # carga e inserta/actualiza
    python scripts/seed_recommendations.py --reset    # borra todas y recarga
"""

import csv
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "seeds", "recomendaciones_cultivo.csv")

sys.path.insert(0, BASE_DIR)

from database.connection import get_cursor, db_available


def load_csv() -> list[dict]:
    with open(CSV_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def seed(reset: bool = False):
    if not db_available():
        print("ERROR: Base de datos no disponible. Verifica que PostgreSQL esté corriendo.")
        sys.exit(1)

    rows = load_csv()
    print(f"CSV cargado: {len(rows)} recomendaciones")

    with get_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recomendaciones_cultivo (
                id          SERIAL PRIMARY KEY,
                cultivo     VARCHAR(50)  NOT NULL,
                variable    VARCHAR(50)  NOT NULL,
                condicion   VARCHAR(50)  NOT NULL,
                umbral_min  NUMERIC,
                umbral_max  NUMERIC,
                nivel       VARCHAR(20)  NOT NULL,
                icono       VARCHAR(10),
                titulo      VARCHAR(200) NOT NULL,
                recomendacion TEXT       NOT NULL,
                fuente      VARCHAR(200),
                created_at  TIMESTAMP DEFAULT NOW()
            )
        """)

        if reset:
            cur.execute("DELETE FROM recomendaciones_cultivo")
            print("Tabla limpiada (--reset)")

        inserted = 0
        for row in rows:
            cur.execute(
                """
                INSERT INTO recomendaciones_cultivo
                    (cultivo, variable, condicion, umbral_min, umbral_max,
                     nivel, icono, titulo, recomendacion, fuente)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (
                    row["cultivo"].strip(),
                    row["variable"].strip(),
                    row["condicion"].strip(),
                    float(row["umbral_min"]) if row.get("umbral_min", "").strip() else None,
                    float(row["umbral_max"]) if row.get("umbral_max", "").strip() else None,
                    row["nivel"].strip(),
                    row.get("icono", "").strip() or None,
                    row["titulo"].strip(),
                    row["recomendacion"].strip(),
                    row.get("fuente", "").strip() or None,
                ),
            )
            inserted += 1

        cur.execute("SELECT COUNT(*) AS n FROM recomendaciones_cultivo")
        total = cur.fetchone()["n"]

    print(f"Insertadas: {inserted} | Total en tabla: {total}")


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    seed(reset=reset_flag)
