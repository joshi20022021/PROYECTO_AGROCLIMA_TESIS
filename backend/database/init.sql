-- ============================================================
-- AgroClima GT — Esquema PostgreSQL
-- Ejecutado automaticamente por Docker al primer inicio
-- ============================================================

-- Usuarios del sistema
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100),
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) DEFAULT 'usuario',
    creado_en TIMESTAMP DEFAULT NOW()
);

-- Municipios de cobertura
CREATE TABLE IF NOT EXISTS municipios (
    id      SERIAL PRIMARY KEY,
    nombre  VARCHAR(100) UNIQUE NOT NULL,
    lat     FLOAT NOT NULL,
    lon     FLOAT NOT NULL
);

-- Referencia agronómica de cultivos
CREATE TABLE IF NOT EXISTS cultivos (
    id           SERIAL PRIMARY KEY,
    nombre       VARCHAR(100) UNIQUE NOT NULL,
    categoria    VARCHAR(50),
    temp_min     FLOAT, temp_max     FLOAT,
    rain_min     FLOAT, rain_max     FLOAT,
    humidity_min FLOAT, humidity_max FLOAT,
    ph_min       FLOAT, ph_max       FLOAT,
    sm_min       FLOAT, sm_max       FLOAT,
    light_min    INT,   light_max    INT,
    green_min    FLOAT, green_max    FLOAT,
    notas        TEXT
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
    fuente        VARCHAR(20) DEFAULT 'manual',
    modelo_ver    VARCHAR(50) DEFAULT 'xgboost_v2'
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
    crossval_r2          FLOAT,
    crossval_std         FLOAT,
    hiperparametros      JSONB,
    activo               BOOLEAN DEFAULT FALSE
);

-- Catalogo de archivos/datasets cargados al sistema
CREATE TABLE IF NOT EXISTS datasets_registrados (
    id              SERIAL PRIMARY KEY,
    nombre_archivo  VARCHAR(200) UNIQUE NOT NULL,
    tipo            VARCHAR(50) NOT NULL,
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
    categoria       VARCHAR(50) NOT NULL,
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
    fuente          VARCHAR(50) DEFAULT 'ERA5-Land',
    periodo         VARCHAR(50),
    fecha_carga     TIMESTAMP DEFAULT NOW(),
    UNIQUE (municipio, fuente, periodo)
);

-- Muestras de entrenamiento usadas por el modelo ML
CREATE TABLE IF NOT EXISTS dataset_entrenamiento (
    id              BIGSERIAL PRIMARY KEY,
    dataset_nombre  VARCHAR(200) NOT NULL,
    municipio       VARCHAR(100) NOT NULL,
    cultivo         VARCHAR(100) NOT NULL,
    mes             SMALLINT NOT NULL,
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

CREATE INDEX IF NOT EXISTS idx_dataset_entrenamiento_dataset ON dataset_entrenamiento(dataset_nombre);
CREATE INDEX IF NOT EXISTS idx_dataset_entrenamiento_municipio ON dataset_entrenamiento(municipio);
CREATE INDEX IF NOT EXISTS idx_dataset_entrenamiento_cultivo ON dataset_entrenamiento(cultivo);

-- Configuración de correo para alertas críticas
CREATE TABLE IF NOT EXISTS email_config (
    id              SERIAL PRIMARY KEY,
    email_to        TEXT NOT NULL,          -- destinatarios separados por coma
    cultivo         VARCHAR(100),           -- NULL = aplica a todos los cultivos
    severidad_min   VARCHAR(20) DEFAULT 'severo',  -- severo|moderado
    activo          BOOLEAN DEFAULT TRUE,
    actualizado     TIMESTAMP DEFAULT NOW()
);

-- Historial de correos enviados
CREATE TABLE IF NOT EXISTS email_log (
    id          SERIAL PRIMARY KEY,
    timestamp   TIMESTAMP DEFAULT NOW(),
    cultivo     VARCHAR(100),
    municipio   VARCHAR(100),
    variables   JSONB,
    destinatarios TEXT,
    ok          BOOLEAN DEFAULT TRUE,
    error_msg   TEXT
);

-- Recomendaciones agronómicas por cultivo y condición climática
CREATE TABLE IF NOT EXISTS recomendaciones_cultivo (
    id            SERIAL PRIMARY KEY,
    cultivo       VARCHAR(100) NOT NULL,
    variable      VARCHAR(50)  NOT NULL,   -- temperatura|precipitacion|humedad|ph_suelo|general|plaga|enfermedad
    condicion     VARCHAR(20)  NOT NULL,   -- muy_alto|alto|bajo|muy_bajo|cualquiera
    umbral_min    FLOAT,                   -- valor mínimo que activa la recomendación (NULL si condicion=cualquiera)
    umbral_max    FLOAT,                   -- valor máximo que activa la recomendación (NULL si condicion=cualquiera)
    nivel         VARCHAR(20)  NOT NULL,   -- info|advertencia|critica
    icono         VARCHAR(10),
    titulo        VARCHAR(120) NOT NULL,
    recomendacion TEXT         NOT NULL,
    fuente        VARCHAR(200),
    activo        BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_recom_cultivo ON recomendaciones_cultivo(cultivo);
CREATE INDEX IF NOT EXISTS idx_recom_variable ON recomendaciones_cultivo(variable);

-- Calendario de siembra óptimo por municipio/cultivo/mes (desde sowing_calendar.csv)
CREATE TABLE IF NOT EXISTS calendario_siembra (
    id              SERIAL PRIMARY KEY,
    municipio       VARCHAR(100) NOT NULL,
    cultivo         VARCHAR(100) NOT NULL,
    mes             SMALLINT    NOT NULL,
    rank            SMALLINT,
    is_top3         BOOLEAN,
    mean_yield      FLOAT,
    std_yield       FLOAT,
    high_yield_rate FLOAT,
    n_samples       INTEGER,
    score           FLOAT,
    recommendation  VARCHAR(50),
    UNIQUE (municipio, cultivo, mes)
);

CREATE INDEX IF NOT EXISTS idx_cal_siembra_municipio ON calendario_siembra(municipio);
CREATE INDEX IF NOT EXISTS idx_cal_siembra_cultivo   ON calendario_siembra(cultivo);

-- Índice de estrés hídrico mensual por municipio/año (desde water_stress_index.csv)
CREATE TABLE IF NOT EXISTS indice_estres_hidrico (
    id                 SERIAL PRIMARY KEY,
    municipio          VARCHAR(100) NOT NULL,
    zona               VARCHAR(50),
    altitud_m          FLOAT,
    anio               SMALLINT    NOT NULL,
    mes                SMALLINT    NOT NULL,
    precipitacion      FLOAT,
    eto_mm_day         FLOAT,
    rain_mm_day        FLOAT,
    water_stress_index FLOAT,
    stress_level       VARCHAR(20),
    UNIQUE (municipio, anio, mes)
);

CREATE INDEX IF NOT EXISTS idx_estres_hidrico_municipio ON indice_estres_hidrico(municipio);
CREATE INDEX IF NOT EXISTS idx_estres_hidrico_anio      ON indice_estres_hidrico(anio);

-- Feedback real de campo para ciclo de aprendizaje y reentrenamiento automatico
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

CREATE INDEX IF NOT EXISTS idx_model_feedback_pending ON model_feedback(processed_retrain);
CREATE INDEX IF NOT EXISTS idx_model_feedback_crop_loc ON model_feedback(cultivo, municipio);

-- ── Datos iniciales ──────────────────────────────────────────

INSERT INTO municipios (nombre, lat, lon) VALUES
    ('Chimaltenango',  14.6614, -90.8197),
    ('Sacatepequez',   14.5586, -90.7295),
    ('Guatemala',      14.6349, -90.5069),
    ('Escuintla',      14.3019, -90.7857),
    ('Santa Rosa',     14.2136, -90.2975),
    ('Solola',         14.7752, -91.1820),
    ('Totonicapan',    14.9133, -91.3598),
    ('Quetzaltenango', 14.8445, -91.5187),
    ('Suchitepequez',  14.5319, -91.5099),
    ('Retalhuleu',     14.5286, -91.6863),
    ('San Marcos',     14.9599, -91.7952),
    ('Huehuetenango',  15.3189, -91.4706),
    ('Quiche',         15.0301, -91.1500),
    ('Baja Verapaz',   15.1264, -90.3631),
    ('Coban',          15.4686, -90.3769),
    ('Peten',          16.9302, -89.8883),
    ('Izabal',         15.4667, -89.1333),
    ('Zacapa',         14.9726, -89.5267),
    ('Chiquimula',     14.7993, -89.5454),
    ('Jalapa',         14.6333, -89.9833),
    ('Jutiapa',        14.2936, -89.8963),
    ('El Progreso',    14.8500, -90.0667)
ON CONFLICT DO NOTHING;

-- Modelo actual (entrenado con dataset_v2.csv)
INSERT INTO modelos_ml
    (nombre, version, dataset_usado, n_filas, n_features, r2_test, mae, rmse, crossval_r2, crossval_std, hiperparametros, activo)
VALUES (
    'XGBoost', 'v2.0',
    'dataset_v2.csv',
    64935, 16,
    0.6833, 4.98, 6.24,
    0.6784, 0.0028,
    '{"n_estimators":400,"max_depth":6,"learning_rate":0.05,"subsample":0.8,"colsample_bytree":0.8,"min_child_weight":3,"reg_alpha":0.1,"reg_lambda":1.0}'::jsonb,
    TRUE
)
ON CONFLICT DO NOTHING;
