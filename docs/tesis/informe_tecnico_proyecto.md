# Informe Técnico del Proyecto AgroClima GT

## 1. Propósito del documento

Este informe describe el proyecto **AgroClima GT** a partir de la implementación real contenida en `C:\Users\edgar\Downloads\TESISXD\conferencia`. Su objetivo es servir como base de contraste contra el marco teórico de la tesis, identificando:

- qué hace realmente el sistema
- qué datos usa
- cómo circula la información entre módulos
- qué componentes están implementados
- qué aspectos están en prototipo, simplificados o parcialmente integrados

No está basado solo en `CLAUDE.md`, sino también en el código fuente del backend, frontend, scripts de entrenamiento, archivos de datos y esquema de base de datos.

---

## 2. Resumen ejecutivo del sistema

**AgroClima GT** es una plataforma web de monitoreo agroclimático con cuatro ejes funcionales principales:

1. **Predicción de rendimiento agrícola** mediante un modelo de machine learning con XGBoost.
2. **Monitoreo en tiempo real de sensores conectados a Arduino**.
3. **Consulta de pronóstico meteorológico de 7 días** usando Open-Meteo.
4. **Generación de alertas y recomendaciones agronómicas** basadas en reglas, datos de sensores, clima y parámetros de cultivo.

El sistema está compuesto por:

- un **frontend React/Vite**
- un **backend FastAPI**
- una **base de datos PostgreSQL 16** en Docker
- un **modelo ML persistido en archivos `.joblib`**
- datasets y artefactos CSV/JSON locales

Además, el sistema incorpora módulos para:

- reentrenamiento del modelo
- retroalimentación con rendimiento real
- comparación entre modelos
- inventario de datasets
- configuración de correos de alerta

---

## 3. Arquitectura general del proyecto

### 3.1. Estructura principal del repositorio

El proyecto está organizado en dos carpetas principales:

- `backend/`
- `frontend/`

También existen:

- `docker-compose.yml` para PostgreSQL
- `CLAUDE.md` con descripción operativa del proyecto
- `docs/` para artefactos documentales

### 3.2. Stack tecnológico identificado

#### Backend

- `FastAPI`
- `Uvicorn`
- `psycopg2-binary`
- `pandas`
- `numpy`
- `xgboost`
- `scikit-learn`
- `joblib`
- `shap`
- `pyserial`

#### Frontend

- `React 19`
- `Vite`
- `Chart.js`
- `html2canvas`
- `jsPDF`
- `leaflet`
- `react-leaflet`

#### Base de datos

- `PostgreSQL 16` en contenedor Docker

#### Servicios externos

- `Open-Meteo` para pronóstico
- `SMTP` para alertas por correo

---

## 4. Funcionamiento general del sistema

### 4.1. Flujo funcional principal

El funcionamiento del sistema se puede resumir así:

1. El usuario accede al frontend web.
2. El frontend solicita métricas históricas y/o pronóstico al backend.
3. El usuario ingresa variables del lote o del cultivo.
4. El backend valida los rangos fisiológicos de entrada.
5. El backend prepara la fila de entrada para el modelo ML.
6. El modelo XGBoost estima un `yield_pct` entre 0 y 100.
7. El backend calcula:
   - nivel de rendimiento
   - intervalo de confianza
   - explicación SHAP
   - anomalía de sensores
   - drift de datos
8. Si hay base de datos disponible, la predicción se guarda en PostgreSQL.
9. Si existen variables fuera del rango óptimo del cultivo, se generan alertas.
10. En modo Arduino, las lecturas llegan por serial, se procesan, se persisten y se transmiten por WebSocket al frontend.
11. Si la alerta es severa y el correo está configurado, se notifica vía SMTP.

---

## 5. Backend: análisis detallado

### 5.1. Archivo central `backend/api.py`

El backend está concentrado principalmente en un solo archivo: `backend/api.py`.

Este archivo implementa:

- endpoints REST
- WebSocket para Arduino
- autenticación básica
- integración con base de datos
- lógica de predicción
- lógica de pronóstico
- lógica de agronomía
- carga de datasets
- administración de modelo
- administración de correo

### 5.2. Versionado de la API

La aplicación FastAPI se declara como:

- título: `AgroClima GT API`
- versión: `1.2.0`

### 5.3. CORS

Permite peticiones desde:

- `http://localhost:5173`
- `http://localhost:3000`

### 5.4. Validación de entradas

Antes de predecir, `_validate_inputs()` restringe valores fisiológicamente plausibles para Guatemala:

- temperatura: `5.0` a `45.0`
- lluvia: `0.0` a `600.0`
- humedad: `5.0` a `100.0`
- pH: `3.5` a `9.5`
- humedad del suelo: `0.01` a `0.65`
- luz: `500` a `130000`

Esto evita predicciones fuera de distribución de entrada.

### 5.5. Endpoints identificados

#### Autenticación

- `POST /auth/register`
- `POST /auth/login`

#### Salud y métricas

- `GET /health`
- `GET /metrics`
- `GET /insivumeh/monthly`
- `GET /insivumeh/daily`

#### Predicción y monitoreo ML

- `POST /predict`
- `POST /predict/multicrop`
- `POST /monitor/anomaly`
- `POST /monitor/drift`
- `POST /feedback`
- `POST /retrain/check`
- `GET /retrain/status`
- `GET /risk-map`

#### Agronomía y clima

- `GET /agronomy/water-stress`
- `GET /agronomy/optimal-conditions/{crop}`
- `GET /agronomy/sowing-calendar`
- `GET /forecast/{municipio}`
- `POST /agronomy/calculator`
- `GET /recommendations/{cultivo}`

#### Datasets

- `GET /dataset`
- `POST /upload-dataset`
- `GET /dataset-template`

#### Arduino y alertas

- `GET /arduino/status`
- `POST /arduino/connect`
- `POST /arduino/disconnect`
- `POST /arduino/config`
- `POST /arduino/simulate`
- `POST /alerts/check`
- `GET /alerts/recommendations`
- `WS /ws/arduino`

#### Administración

- `GET /admin/email-config`
- `POST /admin/email-config`
- `POST /admin/email-test`
- `POST /admin/retrain`
- `GET /admin/open-meteo-usage`
- `GET /admin/compare-models`
- `POST /admin/compare-models`
- `GET /admin/model-info`
- `GET /admin/stats`
- `GET /admin/predictions`
- `GET /admin/readings`
- `GET /admin/datasets`

### 5.6. Observación importante del backend

Aunque `CLAUDE.md` describe el backend como centrado en unos pocos módulos, la implementación real es más amplia. En particular, sí existe:

- autenticación
- administración del modelo
- inventario de datasets
- feedback para reentrenamiento
- consulta de lecturas históricas
- panel administrativo completo

---

## 6. Modelo de machine learning

### 6.1. Archivo principal del modelo

El modelo principal se entrena desde:

- `backend/scripts/training/model_xgboost.py`

La inferencia operativa y la analítica avanzada están en:

- `backend/ml_insights.py`

### 6.2. Tipo de modelo

Se utiliza:

- `XGBRegressor` de XGBoost

con el objetivo:

- `yield_pct`

es decir, un rendimiento porcentual estimado entre 0 y 100.

### 6.3. Hiperparámetros observados

El script de entrenamiento define:

- `n_estimators = 400`
- `max_depth = 6`
- `learning_rate = 0.05`
- `subsample = 0.8`
- `colsample_bytree = 0.8`
- `min_child_weight = 3`
- `reg_alpha = 0.1`
- `reg_lambda = 1.0`
- `random_state = 42`

### 6.4. Variables de entrada del modelo

Las variables activas observadas en `ml_insights.py` y `model_xgboost.py` son:

- `municipio_enc`
- `crop_enc`
- `month`
- `temperature`
- `rainfall`
- `humidity`
- `soil_ph`
- `soil_moisture`
- `light_lux`
- `greenness_idx`
- `swvl2`
- `swvl3`
- `soil_temp`
- `temp_max`
- `temp_min`
- `wind_speed`

### 6.5. Origen conceptual de las variables

- `temperature`: sensor DS18B20 o clima agregado
- `rainfall`: Open-Meteo, ERA5-Land o entrada manual
- `humidity`: Open-Meteo, ERA5-Land o entrada manual
- `soil_ph`: SoilGrids, laboratorio o entrada manual
- `soil_moisture`: higrómetro capacitivo o reanálisis
- `light_lux`: TSL2561
- `greenness_idx`: derivado del TCS3200
- `swvl2`, `swvl3`, `soil_temp`: ERA5-Land
- `temp_max`, `temp_min`, `wind_speed`: NASA POWER o dataset consolidado

### 6.6. Artefactos del modelo encontrados

En `backend/data/models/` se identificaron:

- `xgboost_yield.joblib`
- `label_encoders.joblib`
- `latest_metrics.json`
- `model_comparison.json`
- `isolation_forest_sensor.joblib`
- `isolation_forest_sensor_meta.json`
- `drift_profile.json`

### 6.7. Capacidades analíticas implementadas

El módulo `ml_insights.py` añade:

- predicción puntual
- intervalo de confianza
- explicabilidad SHAP
- ranking multicultivo
- detección de anomalías con Isolation Forest
- monitoreo de drift

### 6.8. Intervalo de confianza

La función `predict_with_interval()` calcula:

- predicción base
- límite inferior
- límite superior
- margen

La estrategia usada es una estimación basada en dispersión por árboles y `iteration_range`, no un método bayesiano formal.

### 6.9. Explicabilidad

La función `explain_prediction_shap()`:

- intenta usar `shap.TreeExplainer`
- si falla, usa contribuciones del booster de XGBoost
- devuelve:
  - valor base
  - contribuciones más importantes
  - narrativa textual

### 6.10. Niveles de rendimiento

En varias partes del sistema, el rendimiento se clasifica así:

- `alto`: `yield_pct >= 75`
- `medio`: `yield_pct >= 50`
- `bajo`: `yield_pct >= 25`
- `critico`: por debajo de `25`

### 6.11. Comparación de modelos

`model_xgboost.py` también permite comparar:

- `XGBoost`
- `RandomForestRegressor`

Según `backend/data/models/model_comparison.json`, la comparación observada fue:

- XGBoost:
  - `R² = 0.7157`
  - `MAE = 4.86`
  - `RMSE = 6.04`
- Random Forest:
  - `R² = 0.4485`
  - `MAE = 6.84`
  - `RMSE = 8.42`

Esto respalda técnicamente la decisión de usar XGBoost como modelo principal.

---

## 7. Datasets y datos cargados

### 7.1. Datasets principales localizados

En `backend/data/datasets/` se localizaron, entre otros:

- `dataset_openmeteo.csv`
- `dataset_v2.csv`
- `dataset_preliminar.csv`
- `recommendations.csv`
- `crop_optimal_conditions.csv`

### 7.2. Dataset preferido por el entrenamiento

El script de entrenamiento **prefiere primero**:

- `dataset_openmeteo.csv`

Si no existe, intenta cargar desde base de datos. Si tampoco, usa:

- `dataset_preliminar.csv`

### 7.3. Estructura de `dataset_openmeteo.csv`

Cabecera observada:

```csv
municipio,altitud_m,crop,month,year,temperature,rainfall,humidity,soil_moisture,swvl2,swvl3,soil_temp,soil_ph,light_lux,greenness_idx,temp_max,temp_min,yield_pct
```

Esto indica que incluye:

- localización
- altitud
- cultivo
- tiempo
- clima
- humedad del suelo
- propiedades de suelo
- proxy de sensor/luz
- variable objetivo

### 7.4. Magnitud observada de `dataset_openmeteo.csv`

Conteos medidos directamente sobre el archivo:

- filas: `812,520`
- municipios únicos: `61`
- cultivos únicos: `37`
- periodo: `2010` a `2024`

### 7.5. Estructura de `dataset_v2.csv`

Cabecera observada:

```csv
municipio,crop,month,year,temperature,rainfall,humidity,soil_moisture,swvl2,swvl3,soil_temp,soil_ph,light_lux,greenness_idx,temp_max,temp_min,wind_speed,yield_pct
```

### 7.6. Magnitud observada de `dataset_v2.csv`

Conteo medido directamente:

- filas: `1,320,345`

### 7.7. Archivo de condiciones óptimas

Cabecera observada en `crop_optimal_conditions.csv`:

```csv
crop,temp_min,temp_max,rain_min,rain_max,humidity_min,humidity_max,ph_min,ph_max,sm_min,sm_max,light_min,light_max,green_min,green_max,category,notes
```

Este archivo define rangos agronómicos óptimos por cultivo.

### 7.8. Archivo de recomendaciones

Se observó el archivo:

- `backend/data/seeds/recomendaciones_cultivo.csv`

Cabecera:

```csv
cultivo,variable,condicion,umbral_min,umbral_max,nivel,icono,titulo,recomendacion,fuente
```

Este archivo almacena recomendaciones agronómicas parametrizadas por:

- cultivo
- variable
- condición
- severidad
- fuente

### 7.9. Métricas cargadas para el frontend

`backend/data/models/latest_metrics.json` contiene un ejemplo de métricas consumidas por el frontend:

- Chimaltenango
- Guatemala
- Sacatepéquez

con variables:

- temperatura
- lluvia
- humedad
- humedad de suelo

Estas métricas parecen funcionar como resumen inicial o dataset de arranque para la interfaz.

---

## 8. Fuentes de datos científicas y operativas

### 8.1. Fuentes identificadas en el repositorio

Se localizaron archivos y scripts asociados a:

- `ERA5-Land`
- `NASA POWER`
- `Open-Meteo`
- `INSIVUMEH`
- `SoilGrids`

### 8.2. Scripts de adquisición y procesamiento

En `backend/scripts/` existen subcarpetas:

- `download/`
- `processing/`
- `datasets/`
- `training/`
- `db/`

Esto sugiere un pipeline general:

1. descarga o consolidación de fuentes
2. procesamiento agronómico
3. generación de datasets
4. entrenamiento del modelo
5. carga a base de datos

### 8.3. Datos crudos encontrados

En `backend/data/raw/` existen archivos asociados a:

- ERA5
- Open-Meteo
- NASA POWER
- INSIVUMEH

Esto demuestra que el sistema no trabaja solo con datos sintéticos; también preserva insumos crudos para procesamiento.

---

## 9. Módulo de alertas

### 9.1. Archivo

- `backend/alert_engine.py`

### 9.2. Función principal

- `check_alerts(sensors, crop)`

### 9.3. Variables evaluadas

El motor de alertas evalúa, según disponibilidad:

- `temperature`
- `light_lux`
- `soil_moisture`
- `greenness_idx`
- `humidity`
- `rainfall`
- `soil_ph`

### 9.4. Severidad

Los niveles de severidad se calculan por porcentaje de desviación respecto al rango óptimo:

- `leve`: desde 10%
- `moderado`: desde 25%
- `severo`: desde 50%

### 9.5. Salida del motor

Cada alerta puede incluir:

- variable
- condición (`alto` o `bajo`)
- valor medido
- rango óptimo
- desviación porcentual
- severidad
- nivel UI (`high`, `medium`, `low`)
- problema
- consecuencia
- acción
- remedio
- cultivo

### 9.6. Rol del motor de alertas

Este módulo no predice rendimiento. Su función es **reglamentaria y agronómica**:

- contrasta mediciones contra rangos
- prioriza eventos
- adjunta recomendaciones

Por tanto, es un motor complementario al modelo ML.

---

## 10. Módulo Arduino y monitoreo en tiempo real

### 10.1. Archivo

- `backend/arduino_reader.py`

### 10.2. Sensores físicos contemplados

El sistema documenta explícitamente el uso de:

- `DS18B20` para temperatura
- `TSL2561` para luz
- `TCS3200` para color
- higrómetro capacitivo para humedad del suelo

### 10.3. Variables físicas derivadas

Del flujo Arduino se obtienen:

- temperatura
- luz
- humedad del suelo
- canales RGB
- índice de verdor `greenness_idx`

El índice de verdor se calcula como:

- `cg / (cr + cg + cb) * 100`

### 10.4. Comunicación serial

La comunicación se realiza por:

- puerto serial
- baud rate `9600`

### 10.5. Formato esperado

JSON serial tipo:

```json
{"t":22.5,"lux":32000,"cr":145,"cg":210,"cb":98,"sm":0.31}
```

### 10.6. Alias aceptados

El lector permite aliases cortos:

- `t` → `temperature`
- `lux` → `light_lux`
- `cr`, `cg`, `cb` → color
- `sm` → `soil_moisture`
- opcionalmente `h`, `r`, `ph`

### 10.7. Comportamiento operativo

El lector:

- detecta puertos seriales
- abre un hilo en background
- parsea líneas
- transforma datos
- calcula `greenness_idx`
- marca timestamp
- envía la lectura al callback del backend

### 10.8. Integración con el backend

Cuando llega una lectura:

1. se normaliza
2. se asocia a municipio/cultivo configurado
3. se evalúan alertas
4. se puede generar predicción automática
5. se persiste
6. se transmite por WebSocket a la interfaz

---

## 11. Correo electrónico y notificaciones

### 11.1. Archivo

- `backend/email_notifier.py`

### 11.2. Configuración requerida

Se soportan variables `.env` como:

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `ALERT_EMAIL_FROM`
- `ALERT_EMAIL_TO`

### 11.3. Política de envío

El sistema:

- solo envía correo para alertas `severo`
- usa cooldown por `(cultivo, variable, condición)`
- el cooldown por defecto es `30 minutos`

### 11.4. Contenido del correo

El correo HTML incluye:

- cultivo
- municipio
- timestamp
- resumen de lecturas
- tabla de alertas
- acción recomendada

### 11.5. Estado híbrido de configuración

Hay dos niveles de configuración:

- variables de entorno `.env`
- registros en tabla `email_config`

Además, desde `/admin/email-config` el sistema actualiza en tiempo de ejecución `ALERT_EMAIL_TO`.

---

## 12. Base de datos PostgreSQL

### 12.1. Despliegue

La base de datos se levanta con `docker-compose.yml`:

- imagen: `postgres:16-alpine`
- puerto host: `5435`
- base: `agroclima`
- usuario: `agroclima`
- contraseña: `agroclima2024`

### 12.2. Pool de conexiones

`backend/database/connection.py` usa:

- `ThreadedConnectionPool`
- mínimo 1 conexión
- máximo 10 conexiones

### 12.3. Tablas identificadas

El esquema `backend/database/init.sql` crea, entre otras:

- `usuarios`
- `municipios`
- `cultivos`
- `predicciones`
- `lecturas_arduino`
- `alertas`
- `modelos_ml`
- `datasets_registrados`
- `fuentes_datos`
- `metricas_climaticas`
- `dataset_entrenamiento`
- `email_config`
- `email_log`
- `recomendaciones_cultivo`
- `model_feedback`

### 12.4. Persistencia funcional por tabla

#### `predicciones`

Guarda:

- variables de entrada
- predicción
- nivel de rendimiento
- fuente

#### `lecturas_arduino`

Guarda:

- lecturas de sensores
- municipio
- cultivo
- JSON crudo

#### `alertas`

Guarda:

- municipio
- cultivo
- variable
- condición
- severidad
- mensaje

#### `modelos_ml`

Guarda metadata del modelo:

- versión
- dataset usado
- número de filas
- métricas
- hiperparámetros

#### `datasets_registrados` y `fuentes_datos`

Permiten inventariar datasets cargados al sistema y archivos fuente.

#### `metricas_climaticas`

Sirve como resumen climático consumido por el frontend.

#### `dataset_entrenamiento`

Guarda el dataset con el que se entrena o reentrena el modelo.

#### `model_feedback`

Registra:

- municipio
- cultivo
- mes
- rendimiento predicho
- rendimiento real
- error absoluto
- notas

Esto permite un ciclo de mejora supervisada del modelo.

---

## 13. Frontend: análisis detallado

### 13.1. Estructura general

El frontend está en `frontend/src/` y la aplicación principal es:

- `frontend/src/App.jsx`

### 13.2. Patrón de funcionamiento

El frontend es una SPA con:

- panel de usuario
- panel de administrador
- estado local en React
- cliente API centralizado en `services/api.js`

No se usa Redux ni store global.

### 13.3. Secciones del usuario observadas

En `constants.js` y `App.jsx` se usan:

- `dashboard`
- `dataset`
- `alerts`
- `reports`
- `forecast`
- `arduino`

### 13.4. Panel administrativo observado

En `App.jsx` y `pages/admin/`:

- dashboard administrativo
- panel de modelos
- historial de predicciones
- historial de lecturas
- administración de datasets

### 13.5. Flujo del panel de usuario

Al iniciar:

1. intenta cargar `/metrics`
2. si recibe datos, completa el formulario inicial
3. al cambiar el municipio, consulta `/forecast/{municipio}`
4. al ir a resultados, dispara predicción si aún no hay una previa
5. combina riesgo basado en ML con riesgo por reglas locales

### 13.6. Riesgo en frontend

El frontend no depende exclusivamente del modelo ML.

En `riskUtils.js` y `Reports.jsx` implementa:

- reglas locales de riesgo basadas en lluvia, temperatura, humedad y pH
- combinación de riesgo por fórmula con riesgo por ML
- elevación del riesgo si hay variables “rojas”

Esto significa que el sistema tiene una lógica híbrida:

- **ML para rendimiento**
- **reglas heurísticas para semaforización y coherencia visual**

### 13.7. Exportación de resultados

`Reports.jsx` permite exportar el reporte como PDF usando:

- `html2canvas`
- `jsPDF`

### 13.8. Estado del modelo en frontend

`Models.jsx` consume:

- `/admin/model-info`
- `/admin/compare-models`
- `/admin/retrain`

y muestra:

- métricas del modelo
- importancia de variables
- agrupación por tipo de variable
- comparación con Random Forest

---

## 14. Cliente API frontend

### 14.1. Archivo

- `frontend/src/services/api.js`

### 14.2. URL base

Está hardcodeada como:

```js
const BASE_URL = "http://localhost:8000";
```

### 14.3. Servicios realmente conectados

El frontend sí tiene funciones para:

- predicción
- multicrop
- risk-map
- drift
- anomaly
- feedback
- water stress
- condiciones óptimas
- calendario de siembra
- forecast
- NDVI satelital
- calculadora agronómica
- reentrenamiento
- comparación de modelos
- información del modelo
- datasets admin
- recomendaciones
- Arduino
- WebSocket

### 14.4. Observación importante

No todas esas funciones están necesariamente visibles en la navegación principal actual. Por ejemplo:

- existe `RiskMap.jsx`
- existe `getSatelliteNdvi()`

pero no están integrados en la navegación principal mostrada por `App.jsx`.

Esto indica funcionalidades desarrolladas o parcialmente preparadas, pero no completamente expuestas al usuario final.

---

## 15. Seguridad, autenticación y control de acceso

### 15.1. Backend

El backend sí implementa:

- registro de usuarios
- login con hash `bcrypt`
- validación por token de administrador en endpoints `/admin/*`

El token admin está hardcodeado como:

- `agroclima-admin-2024`

### 15.2. Frontend

La UI de login actual tiene un comportamiento mixto:

- el acceso de usuario entra sin credenciales
- el acceso admin usa credenciales hardcodeadas:
  - usuario: `admin`
  - contraseña: `agroclima2024`

### 15.3. Hallazgo de consistencia

Existe un **desacople entre autenticación backend y frontend**:

- el backend tiene `/auth/register` y `/auth/login`
- el frontend actual no consume esos endpoints para el flujo principal
- el acceso de usuario es local en la interfaz
- el acceso admin se valida localmente en frontend y luego usa `x-admin-token`

Para una tesis, esto debe describirse como:

- implementación funcional de prototipo
- autenticación parcialmente integrada
- seguridad operativa simplificada para entorno académico/local

---

## 16. Funcionalidades agronómicas implementadas

### 16.1. Pronóstico meteorológico

`GET /forecast/{municipio}`:

- consulta Open-Meteo
- construye 7 días de pronóstico
- resume:
  - lluvia total
  - ETo total
  - déficit de riego
  - días lluviosos
  - promedio de Tmax/Tmin
- usa caché de 3 horas

### 16.2. Calculadora agronómica

`POST /agronomy/calculator` calcula:

- déficit de riego
- litros por cuerda
- necesidad de cal o azufre según pH
- recomendaciones de nitrógeno

El módulo usa parámetros por cultivo para:

- pH objetivo
- necesidad base de nitrógeno
- factor térmico
- coeficiente de cultivo `Kc`

### 16.3. Calendario de siembra

`GET /agronomy/sowing-calendar` y `Forecast.jsx` brindan apoyo a:

- ventanas de siembra
- ventanas de cosecha
- ciclo del cultivo

### 16.4. Estrés hídrico

`GET /agronomy/water-stress` entrega datos desde:

- `backend/data/processed/water_stress_index.csv`

---

## 17. Flujo detallado de datos

### 17.1. Flujo de predicción manual

1. El usuario llena el formulario.
2. El frontend llama a `predictYield()`.
3. El backend recibe `/predict`.
4. Se validan rangos.
5. Se arma el payload completo.
6. `prepare_input_row()` codifica municipio y cultivo.
7. XGBoost produce `yield_pct`.
8. Se calcula intervalo.
9. Se calcula explicación SHAP.
10. Se detecta anomalía.
11. Se estima drift.
12. Se almacena en `predicciones`.
13. Si aplica, se generan alertas en `alertas`.
14. El frontend muestra resultados y recomendaciones.

### 17.2. Flujo de Arduino

1. El Arduino envía JSON serial.
2. `arduino_reader.py` parsea la línea.
3. Se calcula `greenness_idx`.
4. `api.py` recibe la lectura.
5. Se asocia a cultivo y municipio activos.
6. Se guardan lecturas en `lecturas_arduino`.
7. Se ejecuta evaluación de alertas.
8. Si hay alertas severas, se intenta enviar correo.
9. Se transmite la lectura y predicción por WebSocket.
10. Las páginas `Arduino.jsx` y `Alerts.jsx` consumen el stream.

### 17.3. Flujo de entrenamiento

1. Se descargan o procesan fuentes climáticas.
2. Se generan datasets tabulares.
3. Se entrena `XGBoost`.
4. Se guardan:
   - `xgboost_yield.joblib`
   - `label_encoders.joblib`
5. Se actualiza metadata de `modelos_ml`.

### 17.4. Flujo de reentrenamiento

1. El usuario admin dispara `/admin/retrain`.
2. Se ejecuta `model_xgboost.py train` en segundo plano.
3. Se actualiza el artefacto del modelo.
4. Se sincroniza metadata del modelo.

### 17.5. Flujo de feedback

1. Se envía rendimiento real por `/feedback`.
2. Se almacena en `model_feedback`.
3. Se calcula error absoluto.
4. Se verifica si se alcanzó el umbral de reentrenamiento.
5. Si aplica, se inicia un nuevo entrenamiento.

---

## 18. Diferencias y tensiones entre teoría e implementación

Esta sección es especialmente útil para contrastar con el marco teórico.

### 18.1. Cobertura de cultivos

En `CLAUDE.md` se menciona una lista reducida de cultivos en algunas partes, pero la implementación real del frontend y `dataset_openmeteo.csv` manejan:

- `37 cultivos`

Por tanto, si tu marco teórico habla de 8 cultivos, hoy el sistema implementado ya está por encima de ese alcance.

### 18.2. Cobertura geográfica

La interfaz de usuario maneja una lista canónica visible de:

- `22 departamentos/opciones`

pero el dataset `dataset_openmeteo.csv` contiene:

- `61 municipios`

Esto sugiere que el modelo está entrenado con cobertura mayor a la que la UI principal expone.

### 18.3. Tamaño de dataset

El frontend muestra KPIs hardcodeados como:

- `812,520` registros
- `61` municipios
- `37` cultivos

Ese dato sí coincide con `dataset_openmeteo.csv`, pero no con `dataset_v2.csv`, que es más grande.

### 18.4. Dataset realmente usado

Hay una tensión importante:

- el script de entrenamiento prefiere `dataset_openmeteo.csv`
- la metadata histórica y algunos endpoints siguen refiriéndose a `dataset_v2.csv`

Eso significa que debes distinguir en tu tesis:

- dataset de entrenamiento originalmente documentado
- dataset preferido por la versión actual del script

### 18.5. Pronóstico meteorológico

`CLAUDE.md` menciona el uso de `urllib`, y eso sí coincide con la implementación actual en `/forecast/{municipio}`. Sin embargo:

- `requirements.txt` todavía incluye `httpx`

Es decir, hay dependencias que no reflejan exactamente el método usado en producción local.

### 18.6. Autenticación

El backend implementa autenticación real con `bcrypt`, pero el frontend principal sigue usando:

- acceso de usuario sin login real
- acceso admin con validación local hardcodeada

Esto debe presentarse como una implementación parcial o simplificada, no como un sistema de seguridad plenamente integrado.

### 18.7. Riesgo agronómico

El sistema no depende exclusivamente del modelo ML. Usa también:

- reglas heurísticas en frontend
- rangos óptimos por cultivo
- alertas por desviación

Por lo tanto, desde el punto de vista teórico, AgroClima GT es mejor descrito como un **sistema híbrido ML + reglas agronómicas**, no como una solución puramente predictiva.

### 18.8. Funcionalidades preparadas pero no plenamente expuestas

Se detectaron elementos existentes pero no integrados del todo en la navegación visible:

- `RiskMap.jsx`
- función para NDVI satelital

Esto indica expansión funcional futura o implementación parcial.

---

## 19. Conclusión técnica

El proyecto **AgroClima GT** implementa una solución de tesis con un grado de desarrollo considerable y con alcance superior al mínimo esperado para un prototipo académico. Técnicamente, el sistema ya integra:

- machine learning supervisado con XGBoost
- explicabilidad y métricas del modelo
- datos climáticos históricos y operativos
- monitoreo por hardware real con Arduino
- reglas agronómicas por cultivo
- persistencia en PostgreSQL
- administración de datasets y del ciclo del modelo
- pronóstico meteorológico externo
- generación de reportes y alertas

Desde la perspectiva de tesis, la descripción más precisa del sistema sería:

> Una plataforma web híbrida de apoyo a la decisión agrícola para Guatemala, que combina analítica predictiva con XGBoost, monitoreo en tiempo real basado en sensores Arduino, fuentes climáticas externas, reglas agronómicas por cultivo y persistencia operativa en PostgreSQL.

La comparación con el marco teórico debería poner atención en cinco puntos:

1. si el marco describe un sistema solo predictivo, habría que ampliarlo a sistema híbrido
2. si el marco describe 8 cultivos o 22 departamentos únicamente, la implementación actual ya excede ese alcance en datos
3. si el marco supone autenticación completa, la implementación actual todavía es parcial
4. si el marco menciona un único dataset de entrenamiento, conviene diferenciar entre `dataset_v2.csv` y `dataset_openmeteo.csv`
5. si el marco plantea únicamente monitoreo o únicamente pronóstico, la implementación real ya integra ambos

---

## 20. Recomendación para usar este informe en la tesis

Este informe te sirve para construir o corregir:

- marco teórico
- marco metodológico
- capítulo de análisis y diseño
- capítulo de implementación
- capítulo de resultados

En especial, conviene contrastar cada apartado teórico con:

- módulo implementado
- dataset real
- actor del sistema
- algoritmo real
- limitación actual

De esa forma puedes defender no solo lo que investigaste, sino también lo que realmente quedó funcionando en la tesis.
