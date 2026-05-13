-- ============================================================
-- AgroClima GT — Esquema PostgreSQL (limpio)
-- Ejecutado automaticamente por Docker al primer inicio
-- ============================================================

-- Usuarios del sistema
CREATE TABLE IF NOT EXISTS usuarios (
    id            SERIAL PRIMARY KEY,
    nombre        VARCHAR(100),
    email         VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol           VARCHAR(20) DEFAULT 'usuario',
    creado_en     TIMESTAMP DEFAULT NOW()
);

-- Historial de predicciones XGBoost
CREATE TABLE IF NOT EXISTS predicciones (
    id            SERIAL PRIMARY KEY,
    timestamp     TIMESTAMP DEFAULT NOW(),
    municipio     VARCHAR(100) NOT NULL,
    cultivo       VARCHAR(100) NOT NULL,
    mes           SMALLINT,
    temperatura   FLOAT,
    precipitacion FLOAT,
    humedad       FLOAT,
    ph_suelo      FLOAT,
    soil_moisture FLOAT,
    light_lux     FLOAT,
    greenness_idx FLOAT,
    swvl2         FLOAT,
    swvl3         FLOAT,
    soil_temp     FLOAT,
    temp_max      FLOAT,
    temp_min      FLOAT,
    wind_speed    FLOAT,
    yield_pct     FLOAT,
    yield_level   VARCHAR(20),
    fuente        VARCHAR(20)  DEFAULT 'manual',
    modelo_ver    VARCHAR(50)  DEFAULT 'xgboost_v3'
);

-- Lecturas de sensores Arduino
CREATE TABLE IF NOT EXISTS lecturas_arduino (
    id            SERIAL PRIMARY KEY,
    timestamp     TIMESTAMP DEFAULT NOW(),
    municipio     VARCHAR(100),
    cultivo       VARCHAR(100),
    temperatura   FLOAT,
    humedad       FLOAT,
    soil_moisture FLOAT,
    light_lux     FLOAT,
    greenness_idx FLOAT,
    ph_suelo      FLOAT,
    precipitacion FLOAT,
    raw_json      JSONB
);

-- Historial de alertas generadas
CREATE TABLE IF NOT EXISTS alertas (
    id            SERIAL PRIMARY KEY,
    timestamp     TIMESTAMP DEFAULT NOW(),
    prediccion_id INTEGER REFERENCES predicciones(id) ON DELETE SET NULL,
    municipio     VARCHAR(100),
    cultivo       VARCHAR(100),
    variable      VARCHAR(50),
    condicion     VARCHAR(20),
    severidad     VARCHAR(20),
    mensaje       TEXT
);

-- Versiones del modelo ML entrenado
CREATE TABLE IF NOT EXISTS modelos_ml (
    id                   SERIAL PRIMARY KEY,
    nombre               VARCHAR(100) DEFAULT 'XGBoost',
    version              VARCHAR(50),
    fecha_entrenamiento  TIMESTAMP DEFAULT NOW(),
    dataset_usado        VARCHAR(200),
    n_filas              INTEGER,
    n_features           INTEGER,
    r2_test              FLOAT,
    mae                  FLOAT,
    rmse                 FLOAT,
    precision            FLOAT,
    recall               FLOAT,
    f1                   FLOAT,
    low_yield_threshold  INTEGER DEFAULT 50,
    crossval_r2          FLOAT,
    crossval_std         FLOAT,
    hiperparametros      JSONB,
    activo               BOOLEAN DEFAULT FALSE
);

-- Catalogo de archivos/datasets cargados al sistema
CREATE TABLE IF NOT EXISTS datasets_registrados (
    id              SERIAL PRIMARY KEY,
    nombre_archivo  VARCHAR(200) UNIQUE NOT NULL,
    tipo            VARCHAR(50)  NOT NULL,
    origen          VARCHAR(100),
    periodo         VARCHAR(50),
    total_filas     INTEGER,
    total_columnas  INTEGER,
    columnas        JSONB,
    metadata        JSONB,
    activo          BOOLEAN DEFAULT FALSE,
    fecha_carga     TIMESTAMP DEFAULT NOW()
);

-- Archivos fuente usados para construir datasets de entrenamiento
CREATE TABLE IF NOT EXISTS fuentes_datos (
    id              SERIAL PRIMARY KEY,
    nombre_archivo  VARCHAR(200) UNIQUE NOT NULL,
    categoria       VARCHAR(50)  NOT NULL,
    periodo         VARCHAR(50),
    total_filas     INTEGER,
    total_columnas  INTEGER,
    columnas        JSONB,
    metadata        JSONB,
    fecha_carga     TIMESTAMP DEFAULT NOW()
);

-- Resumen de metricas climaticas consumidas por el frontend
CREATE TABLE IF NOT EXISTS metricas_climaticas (
    id              SERIAL PRIMARY KEY,
    municipio       VARCHAR(100) NOT NULL,
    temperatura     FLOAT,
    precipitacion   FLOAT,
    humedad         FLOAT,
    soil_moisture   FLOAT,
    fuente          VARCHAR(50)  DEFAULT 'ERA5-Land',
    periodo         VARCHAR(50),
    fecha_carga     TIMESTAMP DEFAULT NOW(),
    UNIQUE (municipio, fuente, periodo)
);

-- Cache de muestras de entrenamiento (opcional — el modelo prefiere los CSV)
CREATE TABLE IF NOT EXISTS dataset_entrenamiento (
    id              BIGSERIAL PRIMARY KEY,
    dataset_nombre  VARCHAR(200) NOT NULL,
    municipio       VARCHAR(100) NOT NULL,
    cultivo         VARCHAR(100) NOT NULL,
    mes             SMALLINT    NOT NULL,
    anio            SMALLINT,
    temperatura     FLOAT,
    precipitacion   FLOAT,
    humedad         FLOAT,
    ph_suelo        FLOAT,
    soil_moisture   FLOAT,
    light_lux       FLOAT,
    greenness_idx   FLOAT,
    swvl2           FLOAT,
    swvl3           FLOAT,
    soil_temp       FLOAT,
    temp_max        FLOAT,
    temp_min        FLOAT,
    wind_speed      FLOAT,
    yield_pct       FLOAT,
    fecha_carga     TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dataset_entrenamiento_dataset   ON dataset_entrenamiento(dataset_nombre);
CREATE INDEX IF NOT EXISTS idx_dataset_entrenamiento_municipio ON dataset_entrenamiento(municipio);
CREATE INDEX IF NOT EXISTS idx_dataset_entrenamiento_cultivo   ON dataset_entrenamiento(cultivo);

-- Configuracion de correo para alertas criticas
CREATE TABLE IF NOT EXISTS email_config (
    id            SERIAL PRIMARY KEY,
    email_to      TEXT        NOT NULL,
    cultivo       VARCHAR(100),
    severidad_min VARCHAR(20) DEFAULT 'severo',
    activo        BOOLEAN DEFAULT TRUE,
    actualizado   TIMESTAMP DEFAULT NOW()
);

-- Historial de correos enviados
CREATE TABLE IF NOT EXISTS email_log (
    id            SERIAL PRIMARY KEY,
    timestamp     TIMESTAMP DEFAULT NOW(),
    cultivo       VARCHAR(100),
    municipio     VARCHAR(100),
    variables     JSONB,
    destinatarios TEXT,
    ok            BOOLEAN DEFAULT TRUE,
    error_msg     TEXT
);

-- Recomendaciones agronomicas por cultivo y condicion climatica
CREATE TABLE IF NOT EXISTS recomendaciones_cultivo (
    id            SERIAL PRIMARY KEY,
    cultivo       VARCHAR(100) NOT NULL,
    variable      VARCHAR(50)  NOT NULL,
    condicion     VARCHAR(20)  NOT NULL,
    umbral_min    FLOAT,
    umbral_max    FLOAT,
    nivel         VARCHAR(20)  NOT NULL,
    icono         VARCHAR(10),
    titulo        VARCHAR(120) NOT NULL,
    recomendacion TEXT         NOT NULL,
    fuente        VARCHAR(200),
    activo        BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_recom_cultivo  ON recomendaciones_cultivo(cultivo);
CREATE INDEX IF NOT EXISTS idx_recom_variable ON recomendaciones_cultivo(variable);

-- Feedback real de campo para ciclo de reentrenamiento automatico
CREATE TABLE IF NOT EXISTS model_feedback (
    id                SERIAL PRIMARY KEY,
    created_at        TIMESTAMP DEFAULT NOW(),
    municipio         VARCHAR(100) NOT NULL,
    cultivo           VARCHAR(100) NOT NULL,
    mes               SMALLINT,
    predicted_yield   FLOAT NOT NULL,
    actual_yield      FLOAT NOT NULL,
    abs_error         FLOAT,
    notes             TEXT,
    processed_retrain BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_model_feedback_pending  ON model_feedback(processed_retrain);
CREATE INDEX IF NOT EXISTS idx_model_feedback_crop_loc ON model_feedback(cultivo, municipio);
