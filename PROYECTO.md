# AgroClima GT — Documentación del Proyecto

Sistema de monitoreo climático agrícola para Guatemala. Combina predicción de rendimiento con XGBoost, sensores físicos Arduino, pronóstico meteorológico en tiempo real y recomendaciones agronómicas basadas en datos reales de FAOSTAT.

---

## Índice

1. [Descripción general](#1-descripción-general)
2. [Arquitectura del sistema](#2-arquitectura-del-sistema)
3. [Datos de entrenamiento](#3-datos-de-entrenamiento)
4. [Modelo de machine learning](#4-modelo-de-machine-learning)
5. [Hardware Arduino](#5-hardware-arduino)
6. [Backend (API FastAPI)](#6-backend-api-fastapi)
7. [Frontend (React)](#7-frontend-react)
8. [Base de datos](#8-base-de-datos)
9. [Calibración con datos reales FAOSTAT](#9-calibración-con-datos-reales-faostat)
10. [Instalación y ejecución](#10-instalación-y-ejecución)
11. [Resultados del modelo](#11-resultados-del-modelo)

---

## 1. Descripción general

**AgroClima GT** es un prototipo de tesis universitaria que apoya la toma de decisiones agrícolas en Guatemala. El sistema predice el **porcentaje de rendimiento esperado** (`yield_pct`, 0–100%) de ocho cultivos principales en los 22 departamentos del país, cruzando datos climáticos en tiempo real con un modelo XGBoost entrenado sobre 2.1 millones de registros históricos.

### Cultivos soportados por el modelo

| Cultivo | Código FAOSTAT | Rendimiento promedio Guatemala |
|---------|---------------|-------------------------------|
| Maíz | 56 | 0.20 t/ha |
| Frijol | 176 | 0.09 t/ha |
| Café | 656 | 0.09 t/ha |
| Arroz | 27 | 0.30 t/ha |
| Papa | 116 | 2.55 t/ha |
| Tomate | 388 | 4.14 t/ha |
| Aguacate | 572 | 1.30 t/ha |
| Cacao | 661 | 0.27 t/ha |

### Departamentos cubiertos

Los 22 departamentos de Guatemala, con datos climáticos reales de ERA5-Land, NASA POWER y Open-Meteo.

---

## 2. Arquitectura del sistema

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│              React + Vite  (puerto 3000)                    │
│  Dashboard │ Métricas │ Alertas │ Resultados │ Pronóstico   │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP / WebSocket
┌─────────────────────────▼───────────────────────────────────┐
│                    BACKEND API                              │
│              FastAPI + Python  (puerto 8000)                │
│  /predict │ /forecast │ /recommendations │ /arduino/ws      │
└──────┬──────────────┬──────────────────┬────────────────────┘
       │              │                  │
┌──────▼──────┐ ┌─────▼──────┐ ┌────────▼────────┐
│  XGBoost    │ │ PostgreSQL │ │   Open-Meteo    │
│  (.joblib)  │ │  (p. 5435) │ │   ERA5 / NASA   │
└─────────────┘ └────────────┘ └─────────────────┘
       ▲
┌──────┴──────────────────────────────┐
│          Arduino Uno                │
│  DS18B20 │ TSL2561 │ TCS3200        │
│  Higrómetro capacitivo              │
└─────────────────────────────────────┘
```

### Flujo de datos principal

```
Formulario usuario
    → POST /predict
    → ml_insights.py (XGBoost + SHAP)
    → yield_pct + intervalo de confianza + factores SHAP
    → Dashboard (visualización de riesgo)

Arduino (serial JSON)
    → arduino_reader.py
    → WebSocket /ws/arduino
    → alert_engine.py (umbrales por cultivo)
    → email_notifier.py (alertas críticas)
    → Frontend página Arduino en tiempo real

Open-Meteo API
    → GET /forecast/{departamento}
    → caché 3 horas
    → Página Pronóstico (7 días)
```

---

## 3. Datos de entrenamiento

El modelo se entrenó con datos de cuatro fuentes principales, fusionadas en un único dataset.

### Fuentes de datos

| Fuente | Variables obtenidas | Período |
|--------|---------------------|---------|
| **ERA5-Land** (Copernicus) | temperatura, lluvia, humedad, swvl1/2/3, soil_temp, altitud_m | 2010–2023 |
| **NASA POWER** | temp_max, temp_min, wind_speed | 2010–2023 |
| **SoilGrids (ISRIC)** | soil_ph (pH del suelo) | estático |
| **Open-Meteo** | temperatura, lluvia, humedad, soil_moisture | 2010–2023 |
| **FAOSTAT** | rendimientos nacionales reales (hg/ha) por cultivo | 2010–2023 |

### Pipeline de construcción del dataset

```
dataset_openmeteo.csv (812,520 filas)
        + wind_speed (nasa_power_mensual.csv)
        ↓
dataset_v2.csv (1,320,345 filas)
        + altitud_m (era5_mensual.csv)
        ↓
dataset_combinado.csv (2,111,220 filas · 228 MB)
        + calibración FAOSTAT (factor por cultivo/año)
        ↓
dataset_faostat.csv (2,111,220 filas · 231 MB) ← usado en entrenamiento
```

### Calibración con FAOSTAT

El `yield_pct` original era **sintético** (calculado con una fórmula de condición óptima). Para anclar las predicciones a rendimientos reales de Guatemala, se descargaron 112 registros de la API FAOSTAT (8 cultivos × 14 años) y se aplicó:

```
yield_adj = yield_base × (0.75 + 0.50 × fao_factor)
```

donde `fao_factor` ∈ [0, 1] representa qué tan bueno fue el año para ese cultivo respecto al mejor registrado. Los años sin cobertura FAOSTAT usan el promedio histórico por cultivo, logrando **calibración del 100%** del dataset.

---

## 4. Modelo de machine learning

### Algoritmo: XGBoost (Extreme Gradient Boosting)

```python
XGBRegressor(
    n_estimators=400,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=3,
    reg_alpha=0.1,
    reg_lambda=1.0,
)
```

### Features (17 variables de entrada)

| Feature | Descripción | Fuente / Sensor | Importancia |
|---------|-------------|-----------------|-------------|
| `rainfall` | Precipitación mensual (mm) | Open-Meteo / ERA5 | **30.5%** |
| `crop_enc` | Cultivo codificado | Selección usuario | 15.4% |
| `humidity` | Humedad relativa (%) | Open-Meteo / ERA5 | 8.3% |
| `greenness_idx` | Índice de verdor de hoja G/(R+G+B)×100 | TCS3200 (Arduino) | **8.2%** |
| `soil_moisture` | Humedad volumétrica del suelo 0-7 cm | Higrómetro capacitivo | **7.2%** |
| `soil_temp` | Temperatura del suelo 0-7 cm (°C) | ERA5-Land / derivado | 6.3% |
| `temperature` | Temperatura del aire (°C) | DS18B20 (Arduino) / API | 5.8% |
| `light_lux` | Intensidad de luz solar (lux) | TSL2561 (Arduino) | 4.1% |
| `altitud_m` | Elevación del municipio (m) | ERA5-Land por depto | 3.4% |
| `month` | Mes del análisis (1–12) | Fecha del sistema | 3.3% |
| `swvl2` | Humedad suelo 7-28 cm | ERA5-Land / derivado | 2.5% |
| `soil_ph` | pH del suelo | Kit de pH (manual) | 1.3% |
| `swvl3` | Humedad suelo 28-100 cm | ERA5-Land / derivado | 1.0% |
| `temp_min` | Temperatura mínima mensual (°C) | NASA POWER / derivado | 0.9% |
| `temp_max` | Temperatura máxima mensual (°C) | NASA POWER / derivado | 0.8% |
| `wind_speed` | Velocidad del viento 2m (m/s) | NASA POWER / derivado | 0.7% |
| `municipio_enc` | Departamento codificado | Selección usuario | 0.2% |

### Qué puede ingresar el agricultor

Un agricultor sin equipamiento avanzado solo necesita:

| Dato | Cómo obtenerlo |
|------|----------------|
| Departamento | Selección en pantalla |
| Cultivo | Selección en pantalla |
| Lluvia, temperatura, humedad | Botón "Auto desde API" (Open-Meteo) |
| pH del suelo | Kit de pH (~Q70) |
| Estado de las hojas | Selector visual (🟢🟡🔴) |

Los demás features se estiman automáticamente. Con el Arduino conectado, `soil_moisture`, `light_lux` y `greenness_idx` se llenan con datos reales del sensor, mejorando la precisión en ~20% de las features.

### Interpretabilidad con SHAP

Cada predicción incluye una explicación de los factores que más influyeron:

```
Factores que influyeron en esta predicción:
  lluvia        ████████████  −12.3%   (muy poca lluvia redujo el rendimiento)
  humedad       ██████         −6.1%   (humedad alta afecta el cultivo)
  tipo cultivo  ████           +4.8%   (Maíz es robusto en esta zona)
  pH del suelo  ██             −2.1%   (suelo algo ácido)
```

### Lógica de niveles de riesgo

El sistema combina dos capas:

**Capa 1 — XGBoost ML:**
```
yield_pct ≥ 75% → nivel "alto"  (buena producción)
yield_pct ≥ 50% → nivel "medio"
yield_pct ≥ 25% → nivel "bajo"
yield_pct < 25% → nivel "crítico"
```

**Capa 2 — Reglas agronómicas (fórmula):**
Evalúa lluvia, temperatura, humedad, pH y tipo de cultivo.
Si la fórmula detecta condiciones críticas, el score se toma como `max(mlScore, formulaScore)`.
Esto evita que el modelo sea optimista cuando los sensores indican condiciones extremas.

---

## 5. Hardware Arduino

### Sensores físicos

| Sensor | Mide | Feature del modelo | Conexión |
|--------|------|--------------------|----------|
| **DS18B20** | Temperatura suelo (°C) | `temperature` | D2 + resistencia 4.7kΩ |
| **Higrómetro capacitivo** | Humedad volumétrica suelo (0.0–1.0) | `soil_moisture` | A0 |
| **TSL2561** | Luz solar (lux) | `light_lux` | SDA=A4, SCL=A5 |
| **TCS3200** | Color R,G,B de hoja | `greenness_idx` | OUT=D8, S0-S3=D4-D7 |

### Formato de datos (Serial JSON, 9600 baud)

```json
{"t": 22.5, "lux": 32000, "cr": 145, "cg": 210, "cb": 98, "sm": 0.31}
```

El sistema calcula automáticamente:
```
greenness_idx = cg / (cr + cg + cb) × 100
```

### Calibración del higrómetro

```cpp
#define SOIL_DRY  750   // lectura en suelo completamente seco
#define SOIL_WET  280   // lectura en agua
// Ajustar estos valores con tu sensor específico
```

### Flujo de alertas Arduino

```
Lectura serial → arduino_reader.py → api.py
    → alert_engine.py (verifica umbrales por cultivo)
    → Si alerta crítica: email_notifier.py (cooldown 30 min)
    → WebSocket broadcast → Frontend en tiempo real
```

---

## 6. Backend (API FastAPI)

### Endpoints principales

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `GET /health` | GET | Estado del sistema (API + DB + modelo) |
| `POST /predict` | POST | Predicción XGBoost para un cultivo |
| `POST /predict/multicrop` | POST | Ranking de rendimiento para todos los cultivos |
| `GET /forecast/{departamento}` | GET | Pronóstico 7 días (Open-Meteo, caché 3h) |
| `GET /recommendations/{cultivo}` | GET | Recomendaciones agronómicas por condición |
| `GET /agronomy/optimal-conditions/{cultivo}` | GET | Rangos óptimos por cultivo |
| `GET /risk-map` | GET | Mapa de riesgo por municipio |
| `WS /ws/arduino` | WebSocket | Stream en tiempo real de sensores |
| `GET /admin/stats` | GET | KPIs del dashboard admin |
| `GET /admin/model-info` | GET | Metadata del modelo activo |

### Validación de inputs

El endpoint `/predict` rechaza valores fisiológicamente imposibles antes de pasar al modelo:

```python
_VALID_RANGES = {
    "temperature":   (5.0,  45.0),   # °C
    "rainfall":      (0.0,  600.0),  # mm
    "humidity":      (5.0,  100.0),  # %
    "soil_ph":       (3.5,  9.5),
    "soil_moisture": (0.01, 0.65),
    "light_lux":     (500,  130_000),
}
```

### Respuesta del modelo

```json
{
  "yield_pct": 86.3,
  "yield_level": "alto",
  "confidence": {
    "low": 82.1,
    "high": 91.5,
    "margin": 4.7
  },
  "explanation": {
    "base_value": 78.5,
    "top_contributions": [
      { "feature": "rainfall", "label": "lluvia", "impact": -12.3, "direction": "negativo" },
      { "feature": "crop_enc", "label": "tipo cultivo", "impact": 4.8, "direction": "positivo" }
    ],
    "narrative": "Lluvia=8.7 redujo el rendimiento en -12.3 puntos. ..."
  },
  "anomaly": { "is_anomaly": false, "label": "Normal", "score": 0.12 },
  "drift": { "drift_detected": false, "features_drifted": [] }
}
```

---

## 7. Frontend (React)

### Páginas

| Página | Ruta interna | Descripción |
|--------|-------------|-------------|
| **Inicio** | `dashboard` | Formulario de predicción + visualización de riesgo + SHAP |
| **Métricas** | `dataset` | Tabla histórica de análisis con fechas y nivel de riesgo |
| **Alertas** | `alerts` | Alertas activas de Arduino y del dataset |
| **Resultados** | `reports` | Reporte ejecutivo con semáforo de variables y acciones |
| **Pronóstico** | `forecast` | Clima 7 días + calculadora de riego y siembra |
| **Arduino** | `arduino` | Monitoreo en tiempo real de sensores físicos |

### Panel de Administración (ruta `/admin`)

Protegido con header `X-Admin-Token: agroclima-admin-2024`.

- Estado del sistema (API, DB, modelo)
- KPIs: total predicciones, lecturas Arduino, alertas
- Metadata del modelo activo (R², MAE, dataset usado, filas de entrenamiento)
- Últimas predicciones registradas

### Variables de entorno

```env
VITE_API_URL=http://127.0.0.1:8000   # URL del backend
```

---

## 8. Base de datos

**PostgreSQL 16** en puerto 5435 (Docker).

### Tablas principales

| Tabla | Contenido |
|-------|-----------|
| `predicciones` | Historial de predicciones XGBoost (municipio, cultivo, yield_pct, timestamp) |
| `alertas` | Alertas generadas (severidad, tipo, valor, vinculada a prediccion) |
| `lecturas_arduino` | Lecturas de sensores físicos con timestamp |
| `recomendaciones_cultivo` | Recomendaciones agronómicas filtradas por cultivo y rangos |
| `email_config` | Configuración SMTP para alertas |
| `email_log` | Historial de emails enviados |
| `model_feedback` | Rendimientos reales reportados por usuarios (reentrenamiento) |
| `metricas_climaticas` | Métricas ERA5 por municipio para autocompletar el formulario |

### Inicialización

```bash
cd conferencia
docker compose up -d          # Levanta PostgreSQL en puerto 5435
```

El archivo `init.sql` se ejecuta solo en la primera creación del contenedor.

---

## 9. Calibración con datos reales FAOSTAT

### Problema con el yield_pct sintético

El `yield_pct` original se calculaba con una fórmula de condición óptima (cuánto se acerca el clima a las condiciones ideales por cultivo). Esto producía valores consistentes pero **no anclados a la realidad** de Guatemala.

### Solución: descarga de rendimientos FAOSTAT

```bash
python scripts/datasets/download_faostat.py --user EMAIL --password PASS
# o con token JWT ya obtenido:
python scripts/datasets/download_faostat.py --token TOKEN
# si ya se descargaron los datos:
python scripts/datasets/download_faostat.py --offline
```

**Datos descargados:** 112 registros (8 cultivos × 14 años, 2010–2023)  
**API utilizada:** `https://faostatservices.fao.org/api/v1/en`  
**Elemento FAOSTAT:** código `2413` (Yield en hg/ha)  
**Área FAOSTAT:** código `89` (Guatemala)

### Fórmula de calibración

```
fao_factor = (yield_año - yield_min) / (yield_max - yield_min)

multiplicador = 0.75 + 0.50 × fao_factor
  → factor=0 (peor año):   multiplicador 0.75
  → factor=0.5 (año normal): multiplicador 1.00
  → factor=1 (mejor año):  multiplicador 1.25

yield_adj = clip(yield_base × multiplicador, 5%, 100%)
```

Años sin cobertura FAOSTAT usan el factor promedio del cultivo → **100% del dataset calibrado**.

---

## 10. Instalación y ejecución

### Requisitos

- Python 3.11+
- Node.js 18+
- Docker Desktop
- Arduino IDE (para programar el hardware)

### Paso 1 — Base de datos

```bash
cd conferencia
docker compose up -d
```

### Paso 2 — Backend

```bash
cd conferencia/backend
pip install -r requirements.txt
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

Swagger UI disponible en `http://localhost:8000/docs`

### Paso 3 — Frontend

```bash
cd conferencia/frontend
npm install
npm run dev        # Puerto 3000
```

### Paso 4 — Modelo (primera vez o para reentrenar)

```bash
cd conferencia/backend

# 1. Construir dataset combinado (requiere archivos ERA5/NASA en data/sources/)
python scripts/datasets/merge_datasets.py

# 2. Calibrar con FAOSTAT (requiere credenciales o token)
python scripts/datasets/download_faostat.py --offline   # si ya se descargó

# 3. Entrenar
python scripts/training/model_xgboost.py train

# 4. Comparar XGBoost vs Random Forest
python scripts/training/model_xgboost.py compare
```

### Paso 5 — Sembrar recomendaciones agronómicas

```bash
cd conferencia/backend
python scripts/seed_recommendations.py
```

### Puertos del sistema

| Servicio | Puerto |
|----------|--------|
| Frontend (dev) | 3000 |
| Backend API | 8000 |
| PostgreSQL | 5435 |

---

## 11. Resultados del modelo

### Métricas finales (dataset_faostat.csv, 2,111,220 filas)

| Métrica | Valor |
|---------|-------|
| **R² test** | 0.6334 |
| **MAE** | 5.91% |
| **RMSE** | 7.68% |
| **Cross-val R² (5-fold)** | 0.6321 ± 0.0014 |
| Filas de entrenamiento | 1,688,976 (80%) |
| Filas de prueba | 422,244 (20%) |
| Features activas | 17 |

### Evolución del modelo

| Versión | Dataset | Filas | R² |
|---------|---------|-------|----|
| v1.0 | dataset_preliminar.csv | ~10,000 | ~0.55 |
| v2.0 | dataset_openmeteo.csv | 812,520 | ~0.68 |
| v2.5 | dataset_combinado.csv | 2,111,220 | 0.7045 |
| **v3.0** | **dataset_faostat.csv** | **2,111,220** | **0.6334** |

> El R² de v3.0 es menor que v2.5 porque el dataset FAOSTAT introduce varianza real inter-anual (rendimientos nacionales fluctuantes por clima, plagas y mercado) que el modelo no puede predecir solo con variables climáticas. Un R²=0.63 sobre datos reales calibrados es más valioso académicamente que 0.70 sobre datos sintéticos perfectamente determinísticos.

### Comparación de algoritmos

| Algoritmo | R² | MAE | RMSE |
|-----------|-----|-----|------|
| **XGBoost** | **0.63** | **5.91%** | **7.68%** |
| Random Forest | ~0.61 | ~6.2% | ~8.1% |

XGBoost supera a Random Forest en todas las métricas y tiene mayor velocidad de inferencia, justificando su selección como algoritmo principal.

---

## Estructura de archivos

```
PROYECTO_AGROCLIMA_TESIS/
├── backend/
│   ├── api.py                          # Todos los endpoints FastAPI
│   ├── ml_insights.py                  # XGBoost, SHAP, Isolation Forest
│   ├── alert_engine.py                 # Reglas de alerta por cultivo
│   ├── arduino_reader.py               # Lector serial + sketch Arduino
│   ├── email_notifier.py               # Alertas SMTP con cooldown
│   ├── data/
│   │   ├── datasets/                   # CSVs de entrenamiento (gitignored)
│   │   ├── models/                     # xgboost_yield.joblib (gitignored)
│   │   └── sources/                    # Datos crudos ERA5, NASA, FAOSTAT
│   ├── database/
│   │   ├── connection.py               # Pool psycopg2
│   │   ├── repository.py               # Data access layer
│   │   └── init.sql                    # Schema PostgreSQL
│   └── scripts/
│       ├── datasets/
│       │   ├── merge_datasets.py       # Combina openmeteo + v2 → combinado
│       │   └── download_faostat.py     # Descarga y calibra con FAOSTAT
│       └── training/
│           └── model_xgboost.py        # Entrena, evalúa y compara modelos
├── frontend/
│   └── src/
│       ├── App.jsx                     # Routing + estado global + submit
│       ├── data/constants.js           # Cultivos, departamentos, TRAINED_CROPS
│       ├── services/api.js             # Todas las llamadas fetch al backend
│       ├── pages/
│       │   ├── Dashboard.jsx           # Predicción + SHAP + formulario
│       │   ├── Dataset.jsx             # Tabla de métricas con fechas
│       │   ├── Alerts.jsx              # Alertas activas
│       │   ├── Reports.jsx             # Reporte ejecutivo
│       │   ├── Forecast.jsx            # Pronóstico 7 días + skeleton
│       │   └── admin/AdminDashboard.jsx
│       └── utils/riskUtils.js          # calculateRisk, buildAlerts
└── .gitignore                          # Excluye CSVs >100MB y .joblib
```

---

*AgroClima GT — Proyecto de Tesis · Universidad · Guatemala · 2026*
