# Revision estricta del paper IEEE contra AgroClima GT

Archivo revisado: `paper_agroclima_ieee_actualizado.tex`  
Proyecto revisado: `PROYECTO_AGROCLIMA_TESIS`  
Fecha de revision: 2026-05-13

## Veredicto general

El paper concuerda en lo esencial con el proyecto actual: presenta AgroClima GT como prototipo tecnico y funcional, usa XGBoost como modelo principal, Random Forest como linea base, Isolation Forest para anomalias, FAOSTAT para calibracion del dataset, FastAPI/React/PostgreSQL como arquitectura y Arduino serial/WebSocket como integracion tecnica inicial.

No obstante, no puede marcarse como "estrictamente consistente" todavia por dos puntos concretos:

1. El vector matematico de variables del paper resume menos variables que las usadas realmente por el modelo.
2. El motor de alertas importado por `api.py` apunta a rutas de archivos que no existen en la estructura actual, aunque los CSV correctos si existen en `backend/data/datasets`.

## Coincidencias confirmadas

| Tema | Paper | Proyecto | Estado |
|---|---|---|---|
| Modelo principal | XGBoost/XGBRegressor | `backend/scripts/training/model_xgboost.py` usa `XGBRegressor` | Correcto |
| Modelo comparativo | Random Forest | `RandomForestRegressor` en `model_xgboost.py` | Correcto |
| Dataset activo | `dataset_faostat.csv` con 2,111,220 registros | `backend/data/models/dataset_meta.json` reporta 2,111,220 filas, 61 municipios, 37 cultivos | Correcto |
| Metricas | XGBoost R2 0.6334, MAE 5.91, RMSE 7.68; RF R2 0.3474, MAE 8.26, RMSE 10.25 | `backend/data/models/model_comparison.json` coincide | Correcto |
| Split | 80/20 | `train_test_split(..., test_size=0.2, random_state=42)` | Correcto |
| Validacion cruzada | 5 folds | `cross_val_score(..., cv=5, scoring="r2")` | Correcto |
| Hiperparametros XGBoost | 400 arboles, max_depth 6, learning_rate 0.05, subsample 0.8, colsample 0.8, min_child_weight 3, L1 0.1, L2 1.0 | Coincide con `build_model()` | Correcto |
| Fuentes | ERA5-Land, NASA POWER, SoilGrids, Open-Meteo, INSIVUMEH, FAOSTAT | Existen en `backend/data/raw`, `backend/data/sources` y scripts de descarga/procesamiento | Correcto |
| Arduino serial | DS18B20, TSL2561, TCS3200, higrometro capacitivo | `backend/core/arduino_reader.py` contempla esos sensores y aliases | Correcto |
| WebSocket | `/ws/arduino` | Endpoint existe en `backend/api.py` | Correcto |
| Frontend | React/Vite, dashboard, alertas, Arduino, mapa, reportes, admin | Existen vistas en `frontend/src/pages` | Correcto |
| Visualizaciones | graficas, mapa, reportes | Chart.js, Leaflet, html2canvas y jsPDF presentes | Correcto |
| Limitaciones | sensores fisicos y validacion agronomica quedan como futuro | Paper lo aclara en abstract, discusion y conclusiones | Correcto |
| IoT avanzado | MQTT/LoRaWAN/edge como futuro | No implementado actualmente | Correcto porque el paper lo trata como futuro |

## Inconsistencias o ajustes necesarios

### 1. Vector de entrada del paper incompleto

En el paper, la ecuacion del vector de entrada aparece como:

```latex
\mathbf{x}_i = [m_i, c_i, t_i, T_i, R_i, H_i, pH_i, SM_i, L_i, G_i, W_i, Z_i]
```

Pero el dataset activo `dataset_faostat.csv` contiene:

```text
municipio, altitud_m, crop, month, year, temperature, rainfall, humidity,
soil_moisture, swvl2, swvl3, soil_temp, soil_ph, light_lux, greenness_idx,
temp_max, temp_min, wind_speed, yield_pct
```

Y el entrenamiento usa 17 variables:

```text
municipio_enc, crop_enc, month, temperature, rainfall, humidity, soil_ph,
soil_moisture, light_lux, greenness_idx, swvl2, swvl3, soil_temp,
altitud_m, temp_max, temp_min, wind_speed
```

Recomendacion: reemplazar el vector del paper por una version completa:

```latex
\mathbf{x}_i =
[m_i, c_i, t_i, T_i, R_i, H_i, pH_i, \theta_{1i}, L_i, G_i,
\theta_{2i}, \theta_{3i}, T_{s,i}, z_i, T_{max,i}, T_{min,i}, v_{w,i}]
```

Y explicar:

- `m_i`: municipio codificado.
- `c_i`: cultivo codificado.
- `t_i`: mes.
- `T_i`: temperatura media.
- `R_i`: precipitacion.
- `H_i`: humedad relativa.
- `pH_i`: pH del suelo.
- `theta_1`: humedad superficial del suelo.
- `L_i`: luminosidad.
- `G_i`: indice de verdor.
- `theta_2` y `theta_3`: humedad de suelo en capas derivadas/procesadas.
- `T_s`: temperatura del suelo.
- `z_i`: altitud.
- `T_max` y `T_min`: temperaturas maxima y minima.
- `v_w`: velocidad del viento.

### 2. Rutas del motor de alertas no coinciden con la estructura actual

El paper afirma que las alertas combinan rangos optimos y recomendaciones. Conceptualmente es correcto, y la formula de desviacion coincide con `backend/core/alert_engine.py`.

El problema es funcional: `alert_engine.py` busca estos archivos:

```text
backend/core/data/processed/crop_optimal_conditions.csv
backend/core/data/processed/recommendations.csv
```

Pero los archivos reales estan en:

```text
backend/data/datasets/crop_optimal_conditions.csv
backend/data/datasets/recommendations.csv
```

Resultado comprobado: al llamar `check_alerts(...)`, lanza `FileNotFoundError`.

Impacto: la afirmacion de "reglas agronomicas para alertas" es correcta como diseno y como datos disponibles, pero no es estrictamente correcta como funcionamiento operativo hasta corregir rutas o agregar fallback.

Correccion recomendada en `backend/core/alert_engine.py`:

```python
BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
OPTIMAL_PATH = os.path.join(BACKEND_DIR, "data", "datasets", "crop_optimal_conditions.csv")
RECS_PATH = os.path.join(BACKEND_DIR, "data", "datasets", "recommendations.csv")
```

### 3. La formula de verdor coincide con el codigo, pero requiere cautela de calibracion

El paper usa:

```latex
G = \frac{G_{raw}}{R_{raw}+G_{raw}+B_{raw}}\times 100
```

El backend calcula:

```python
greenness_idx = cg / (cr + cg + cb) * 100
```

Esto coincide matematicamente con el sistema. Sin embargo, el comentario del sketch indica que en el TCS3200 las lecturas pueden comportarse como frecuencias o periodos inversos, por lo que el paper hace bien al decir que es indicador auxiliar y no medicion agronomica de laboratorio.

Recomendacion: mantener la advertencia de calibracion del sensor de color.

## Calculos revisados

| Calculo | Paper | Codigo | Estado |
|---|---|---|---|
| Funcion objetivo XGBoost | Incluida | Coherente con XGBoost | Correcto |
| Regularizacion XGBoost | Incluida | Hiperparametros `reg_alpha`/`reg_lambda`; formula teorica valida | Correcto |
| MAE | Incluido | `mean_absolute_error` | Correcto |
| RMSE | Incluido | raiz de `mean_squared_error` | Correcto |
| R2 | Incluido | `r2_score` | Correcto |
| Desviacion de alertas | Denominador `max(vmax-vmin,1)` | Coincide con `alert_engine.py` | Correcto |
| Severidad de alertas | 10/25/50 % | `SEVERITY_THRESHOLDS = {"leve": 10, "moderado": 25, "severo": 50}` | Correcto |
| Isolation Forest | Formula teorica incluida | `IsolationForest(n_estimators=300, contamination=0.05)` | Correcto |
| Data drift | Mencionado en arquitectura | Implementado con similitud `100 - 22z` | Correcto, aunque el paper podria explicar la formula si hay espacio |
| Intervalos de prediccion | No detallado en paper | Implementado en `predict_with_interval()` | No es inconsistencia; podria agregarse si se quiere fortalecer metodologia |
| SHAP | No aparece fuerte en el paper | Implementado como explicabilidad si dependencia disponible | No es inconsistencia; podria mencionarse como explicabilidad auxiliar |

## Recomendacion final

El paper esta alineado en metodologia, funcionamiento general, metricas y limites academicos, pero antes de considerarlo estrictamente consistente conviene hacer dos correcciones:

1. Actualizar el vector de variables para reflejar las 17 features reales del modelo.
2. Corregir las rutas de `alert_engine.py` o aclarar que las alertas por reglas requieren esa correccion operativa.

Despues de esos ajustes, el paper queda coherente con el estado actual de AgroClima GT y con los documentos de tesis ya trabajados.
