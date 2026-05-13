# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AgroClima GT** — Sistema de monitoreo climático agrícola para Guatemala. Combina predicción de rendimiento con XGBoost, monitoreo en tiempo real con Arduino, pronóstico meteorológico (Open-Meteo) y recomendaciones agronómicas basadas en datos. Proyecto de tesis universitaria.

---

## Commands

### Database (Docker)
```bash
cd C:\Users\edgar\Downloads\TESISXD\conferencia
docker compose up -d          # Levantar PostgreSQL en puerto 5435
docker compose down           # Detener contenedor
```
The `init.sql` only runs on first container creation. For schema changes on existing containers, run SQL manually or recreate the container.

### Backend
```bash
cd C:\Users\edgar\Downloads\TESISXD\conferencia\backend
pip install -r requirements.txt
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```
Swagger UI available at `http://localhost:8000/docs`.

### Frontend
```bash
cd C:\Users\edgar\Downloads\TESISXD\conferencia\frontend
npm install
npm run dev       # Dev server on port 3000 (auto-opens browser)
npm run build     # Production build
npm run test      # Run vitest tests
```

### ML Model
```bash
cd C:\Users\edgar\Downloads\TESISXD\conferencia\backend
python scripts/training/model_xgboost.py train
```

### Database Seeds
```bash
cd C:\Users\edgar\Downloads\TESISXD\conferencia\backend
python scripts/seed_recommendations.py           # Seed crop recommendations
python scripts/seed_recommendations.py --reset   # Clear and re-seed
```
The seed script creates the table if it doesn't exist, so it works without recreating the Docker container.

---

## Architecture

### Backend (`backend/`)

Single-file FastAPI app (`api.py`) that handles REST + WebSocket. All ML logic is in `ml_insights.py`. Key modules:

- **`api.py`** — All endpoints, Arduino WebSocket handler, input validation with `_VALID_RANGES`, agronomy calculator, 7-day forecast via Open-Meteo (uses `urllib` not `httpx`)
- **`ml_insights.py`** — XGBoost prediction with confidence intervals, SHAP explanations, multi-crop ranking, drift detection, anomaly detection
- **`alert_engine.py`** — Rule-based threshold checks against crop optimal ranges
- **`arduino_reader.py`** — Serial port reading + simulation mode
- **`email_notifier.py`** — SMTP alerts with 30-minute per-(crop, variable, condition) cooldown
- **`database/`** — `connection.py` (psycopg2 pool), `repository.py` (data access), `init.sql` (full schema)

**Input validation**: `_validate_inputs()` in `api.py` rejects physiologically impossible sensor values (HTTP 422) before they reach the model, preventing out-of-distribution XGBoost predictions.

**Forecast endpoint**: `GET /forecast/{departamento}` calls Open-Meteo using `urllib.request` via `loop.run_in_executor` (async-safe). Results cached 3 hours in `_FORECAST_CACHE`. The 22 Guatemala departments with coordinates are in `_MUNICIPIOS_COORDS`.

**Arduino flow**: Serial data → `arduino_reader.py` → `_on_arduino_data()` in `api.py` → `check_alerts()` → `notify_critical_alerts()` → broadcast via WebSocket to all connected clients.

### Frontend (`frontend/src/`)

Single-page React app with role-based routing in `App.jsx` (user vs admin). State lives in `UserApp` and is passed as props to pages — no global store.

**Navigation**: `sections` object in `constants.js` defines all user-facing pages. The `pages` object in `UserApp` maps section keys to JSX. Adding a new page requires entries in both `constants.js`, `Sidebar.jsx` (icon), and `App.jsx` (import + pages object).

**Key shared data in `constants.js`**:
- `cropOptions` — 8 crops (canonical list used everywhere)
- `municipioOptions` — 22 Guatemala departments (canonical list, import this instead of hardcoding)
- `sections` — Sidebar navigation config
- `initialDataset`, `defaultForm` — Initial app state

**API client** (`services/api.js`): All `fetch()` calls centralized here. Backend base URL hardcoded to `http://localhost:8000`.

**Risk display coherence**: `effectiveRisk()` in `Reports.jsx` overrides ML risk level when semaphore variables are red, so the UI is never misleadingly optimistic when sensors show extreme values.

**Admin panel** (`pages/admin/`): Separate `AdminApp` component in `App.jsx` with its own sidebar and pages. Protected by `ADMIN_TOKEN` header (`agroclima-admin-2024`).

### Data Flow

```
Arduino sensors → arduino_reader.py → api.py WebSocket → Alerts.jsx
ERA5/NASA data  → scripts/download/ → scripts/processing/ → training CSV
Training CSV    → model_xgboost.py → xgboost_yield.joblib
User form input → api.js → POST /predict → ml_insights.py → Dashboard.jsx
Departamento    → GET /forecast/{dep} → Open-Meteo API → Forecast.jsx
```

### Database

PostgreSQL 16 on port **5435** (not default 5432). Key tables:
- `predicciones` — XGBoost prediction history
- `alertas` — Generated alerts (linked to predictions)
- `lecturas_arduino` — Sensor readings
- `recomendaciones_cultivo` — CSV-seeded agronomy recommendations (filterable by crop + variable thresholds)
- `email_config` / `email_log` — SMTP configuration and send history
- `model_feedback` — User-reported actual yields for retraining

### ML Model

XGBoost trained on 64,935 rows across 22 Guatemala departments and 8 crops. Features include ERA5-Land climate variables, NASA POWER data, SoilGrids pH, and encoded crop/department. Model file: `backend/data/models/xgboost_yield.joblib`.

The model returns `yield_pct` (0–100). Risk level derives from yield: alto ≥ 75%, medio ≥ 50%, bajo < 50%. The `effectiveRisk()` override in `Reports.jsx` can elevate risk regardless of ML output.

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` for email alert configuration. The backend loads it automatically via `email_notifier.py`. Without `.env`, email alerts are disabled but everything else works.

## Ports

| Service | Port |
|---------|------|
| Frontend (dev) | 3000 |
| Backend API | 8000 |
| PostgreSQL | 5435 |

---

## Token-Saving Rules

1. **No programar sin contexto** — Leer archivos relevantes antes de escribir código. Preguntar si falta contexto.
2. **Respuestas cortas** — 1-3 oraciones. Sin preámbulos ni resumen final. Sin repetir lo que dijo el usuario.
3. **No reescribir archivos completos** — Usar Edit (parcial). Write solo si el cambio es >80% del archivo.
4. **No releer archivos ya leídos** — Si ya se leyó en esta conversación, no releer salvo que haya cambiado.
5. **Validar antes de declarar hecho** — Compilar, correr tests o verificar antes de decir "listo".
6. **Cero charla aduladora** — No decir "Excelente pregunta", "Gran idea", etc. Ir directo al trabajo.
7. **Soluciones simples** — Implementar lo mínimo. Sin abstracciones, helpers o features no pedidos.
8. **No pelear con el usuario** — Si el usuario dice "hazlo así", hacerlo. Mencionar concern en 1 oración si aplica.
9. **Leer solo lo necesario** — Usar offset/limit. Si se sabe la ruta exacta, usar Read directo sin Glob+Grep.
10. **No narrar el plan antes de ejecutar** — No anunciar pasos. Solo ejecutar. El usuario ve los tool calls.
11. **Paralelizar tool calls** — Leer múltiples archivos independientes en un solo mensaje, no uno por uno.
12. **No duplicar código en la respuesta** — Si se editó un archivo, no copiar el resultado en texto. El usuario lo ve en el diff.
13. **No usar Agent cuando Grep/Read basta** — Agent duplica el contexto. Usarlo solo para búsquedas amplias o tareas complejas.
