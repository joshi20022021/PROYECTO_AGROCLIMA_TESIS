-- ============================================================
-- AgroClima GT — Migracion de limpieza de la base de datos
-- Ejecutar UNA SOLA VEZ sobre la DB existente:
--   docker exec -i agroclima_db psql -U agroclima -d agroclima_db < migration_cleanup.sql
-- ============================================================

-- 1. Eliminar tablas que nunca se leen en ningun endpoint
DROP TABLE IF EXISTS municipios          CASCADE;
DROP TABLE IF EXISTS cultivos            CASCADE;
DROP TABLE IF EXISTS calendario_siembra  CASCADE;
DROP TABLE IF EXISTS indice_estres_hidrico CASCADE;

-- 2. Vaciar la tabla de entrenamiento (2.1M filas duplicando los CSV)
--    La estructura se conserva como cache opcional; el modelo usa los CSV directamente.
TRUNCATE TABLE dataset_entrenamiento;

-- 3. Agregar columnas de clasificacion a modelos_ml (seccion 5.1 del protocolo)
ALTER TABLE modelos_ml ADD COLUMN IF NOT EXISTS precision           FLOAT;
ALTER TABLE modelos_ml ADD COLUMN IF NOT EXISTS recall              FLOAT;
ALTER TABLE modelos_ml ADD COLUMN IF NOT EXISTS f1                  FLOAT;
ALTER TABLE modelos_ml ADD COLUMN IF NOT EXISTS low_yield_threshold INTEGER DEFAULT 50;

-- 4. Marcar el registro stale como inactivo (dataset_v2.csv, 64935 filas)
--    Se creara uno nuevo correcto al ejecutar: python model_xgboost.py train
UPDATE modelos_ml
SET    activo = FALSE
WHERE  n_filas < 1000000
   OR  dataset_usado = 'dataset_v2.csv';

-- Verificacion final
SELECT
    'predicciones'        AS tabla, COUNT(*) AS filas FROM predicciones      UNION ALL
SELECT 'lecturas_arduino',           COUNT(*) FROM lecturas_arduino           UNION ALL
SELECT 'alertas',                    COUNT(*) FROM alertas                    UNION ALL
SELECT 'modelos_ml',                 COUNT(*) FROM modelos_ml                 UNION ALL
SELECT 'model_feedback',             COUNT(*) FROM model_feedback             UNION ALL
SELECT 'dataset_entrenamiento',      COUNT(*) FROM dataset_entrenamiento      UNION ALL
SELECT 'recomendaciones_cultivo',    COUNT(*) FROM recomendaciones_cultivo    UNION ALL
SELECT 'metricas_climaticas',        COUNT(*) FROM metricas_climaticas        UNION ALL
SELECT 'datasets_registrados',       COUNT(*) FROM datasets_registrados       UNION ALL
SELECT 'fuentes_datos',              COUNT(*) FROM fuentes_datos              UNION ALL
SELECT 'email_config',               COUNT(*) FROM email_config               UNION ALL
SELECT 'email_log',                  COUNT(*) FROM email_log;
