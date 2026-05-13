# Revision del protocolo contra la guia de tesis y el proyecto implementado

Archivos revisados:

- `docs/PROTOCOLO_202112012.pdf`
- `docs/guia_capitulos_3_5_tesis_agroclima.md`
- Proyecto implementado en `backend/` y `frontend/`

Fecha de revision: 2026-05-12.

## Veredicto general

El proyecto actual cumple el objetivo general del protocolo si se interpreta como prototipo funcional de software para identificar escenarios de bajo rendimiento agricola mediante registros climaticos y metricas ingresadas, consultadas o simuladas. Sin embargo, no cumple completamente las partes del protocolo que prometen validacion fisica en sitio, dispositivo IoT inalambrico, redes inalambricas, ESP32/LoRaWAN/MQTT, validacion en Altiplano Occidental y metricas supervisadas de clasificacion como precision/F1.

La guia `guia_capitulos_3_5_tesis_agroclima.md` corrige bien esta diferencia porque delimita el alcance real: XGBoost, Random Forest comparativo, Isolation Forest, reglas agronomicas, FastAPI, React, PostgreSQL, datasets procesados, Arduino por serial/simulacion, WebSocket, mapa, reportes, CSV y visualizaciones. Para que la tesis no contradiga el protocolo, conviene ajustar el lenguaje: presentar lo fisico/IoT inalambrico como diseno propuesto o trabajo futuro, y presentar lo validado como validacion tecnica y funcional del prototipo.

---

# 1. Objetivo general

## Protocolo

> Desarrollar una solucion tecnologica orientada a la identificacion de escenarios de bajo rendimiento agricola en Guatemala mediante el analisis de registros climaticos y metricas en tiempo real.

## Estado frente al proyecto

**Cumple parcialmente alto.**

Se cumple porque existe una plataforma funcional que:

- estima `yield_pct` con XGBoost;
- compara XGBoost contra Random Forest;
- usa registros climaticos y edaficos procesados;
- permite entradas desde formulario, pronostico y simulacion Arduino;
- genera riesgo, alertas, recomendaciones, mapa, reportes y exportacion CSV.

La parte "metricas en tiempo real" se cumple a nivel de software por WebSocket y simulacion/Arduino serial. No queda completamente cumplida si el protocolo exige sensores reales instalados en sitio o red inalambrica.

## Ajuste recomendado

En la tesis escribir:

"El objetivo general se cumple desde la validacion tecnica y funcional del prototipo. El componente de metricas en tiempo real fue implementado mediante soporte de lectura Arduino por serial, simulacion y WebSocket, quedando la validacion fisica en parcela como etapa futura."

---

# 2. Objetivos especificos

## Objetivo especifico 1

### Protocolo

Caracterizar el comportamiento climatico y umbrales de riesgo en zonas de interes de Guatemala mediante registros historicos.

### Estado

**Cumple.**

Evidencia:

- Datasets climaticos y edaficos en `backend/data/sources/`.
- Dataset final `dataset_faostat.csv` con 2,111,220 registros.
- Rangos optimos por cultivo en `crop_optimal_conditions.csv`.
- Reglas de riesgo en `frontend/src/utils/riskUtils.js`.
- Motor de alertas en `backend/alert_engine.py`.
- Mapa de riesgo en `RiskMap.jsx`.

### Mejoras recomendadas

- Agregar tabla de fuentes: ERA5-Land, NASA POWER, SoilGrids, INSIVUMEH procesado, Open-Meteo y FAOSTAT.
- No decir que todo proviene de INSIVUMEH.
- Explicar que el dataset final fue calibrado con FAOSTAT.

---

## Objetivo especifico 2

### Protocolo

Implementar un dispositivo de monitoreo para obtener variables ambientales locales en el sitio de estudio en tiempo real.

### Estado

**Cumple parcialmente / requiere ajuste fuerte de redaccion.**

Lo que si existe:

- Modulo Arduino en backend.
- Endpoints `/arduino/status`, `/arduino/connect`, `/arduino/disconnect`, `/arduino/config`, `/arduino/simulate`.
- WebSocket `/ws/arduino`.
- Vista frontend de Arduino.
- Grafica historica en `Alerts.jsx`.

Lo que no se puede afirmar como cumplido:

- dispositivo validado en campo;
- instalacion en sitio de estudio;
- red inalambrica real;
- ESP32 como hardware final;
- LoRaWAN/MQTT;
- calibracion fisica de sensores.

### Que mejorar/agregar

- Si quieres que el objetivo quede mas cumplido, documenta una prueba real minima: Arduino conectado por USB, captura de datos, captura del frontend y registro en backend.
- Agrega fotos del prototipo fisico si existe.
- Agrega tabla de sensores realmente usados o simulados.
- Si no haras prueba fisica, cambia la redaccion a "implementar soporte de software para monitoreo local mediante Arduino y simulacion".

### Que quitar o bajar de tono

- "redes inalambricas en puntos de prueba";
- "ESP32";
- "telemetria inalambrica";
- "sitio de estudio" si no hubo parcela real.

---

## Objetivo especifico 3

### Protocolo

Evaluar el desempeño de modelos analiticos en la identificacion de anomalias climaticas vinculadas al rendimiento agricola.

### Estado

**Cumple parcialmente.**

Se cumple para evaluacion de modelos predictivos de rendimiento:

- XGBoost: R2 = 0.6334, MAE = 5.91, RMSE = 7.68.
- Random Forest: R2 = 0.3474, MAE = 8.26, RMSE = 10.25.
- Archivo: `backend/data/models/model_comparison.json`.

Se cumple funcionalmente para deteccion de anomalias:

- Isolation Forest implementado en `ml_insights.py`.
- Data drift implementado en `ml_insights.py`.
- Alertas por reglas implementadas en `alert_engine.py`.

No se cumple como evaluacion supervisada de anomalias si se requieren precision, recall, F1 o matriz de confusion, porque no hay eventos reales etiquetados.

### Que mejorar/agregar

- En resultados, separar "evaluacion de regresion" y "validacion funcional de anomalias".
- Dejar precision/F1 como metrica futura.
- Agregar capturas de anomalia simulada.
- Agregar formula de Isolation Forest y formula de desviacion por rango optimo.

### Que quitar o cambiar

- Quitar "Precision, F1-Score" como metrica principal de resultados actuales.
- Cambiarlo por "R2, MAE, RMSE para regresion; validacion funcional para alertas/anomalias".

---

## Objetivo especifico 4

### Protocolo

Desarrollar una interfaz de visualizacion para seguimiento de indicadores generados por el sistema.

### Estado

**Cumple.**

Evidencia:

- Dashboard principal.
- Dataset con filtros, tendencia y CSV.
- Mapa de riesgo y coropletico.
- Alertas con historial Arduino.
- Reportes PDF.
- Pronostico.
- Panel admin.
- Grafica XGBoost vs Random Forest.
- Modo oscuro.

### Mejoras recomendadas

- Incluir capturas actualizadas de las nuevas vistas.
- En 4.6, explicar que la interfaz no solo muestra resultados, sino que apoya la toma de decisiones.

---

# 3. Alcances y limites

## Limite 1 del protocolo

Obtencion y limpieza de series temporales de temperatura, humedad y precipitacion de los ultimos 30 anios, climatologias 1981-2010 y 1991-2020.

### Estado

**Cumple parcialmente.**

El proyecto tiene datos historicos procesados principalmente 2010-2026 en varias fuentes. No queda demostrado que use exactamente los ultimos 30 anios ni climatologias 1981-2010 y 1991-2020 como base principal.

### Ajuste recomendado

Cambiar en la tesis a:

"Se procesaron registros climaticos historicos disponibles en el proyecto, principalmente para el periodo 2010-2026, complementados con referencias climatologicas nacionales cuando aplica."

Si quieres cumplir literalmente el protocolo, debes agregar datos 1981-2010/1991-2020 o justificar por que se cambio el periodo.

---

## Limite 2 del protocolo

Focalizacion de la validacion del prototipo en el Altiplano Occidental.

### Estado

**No cumple de forma estricta.**

El proyecto cubre Guatemala y la interfaz maneja 22 departamentos. No se ve una validacion focalizada exclusivamente en Altiplano Occidental.

### Opciones

1. Ajustar la tesis: decir que el prototipo cubre Guatemala y puede filtrar departamentos del Altiplano Occidental como caso de estudio.
2. Agregar una seccion de caso de estudio: seleccionar Chimaltenango, Quetzaltenango, Totonicapan, Solola, San Marcos, Huehuetenango y Quiche, ejecutar pruebas y mostrar resultados.

### Recomendacion

Agregar en capitulo 4.2 una tabla "Departamentos del Altiplano Occidental usados como caso demostrativo" y en capitulo 5 incluir una prueba con 2-3 cultivos.

---

## Limite 3 del protocolo

Implementacion de algoritmos de identificacion de anomalias termicas contextuales basados en datos historicos.

### Estado

**Cumple parcialmente.**

Existe Isolation Forest y data drift, pero no una validacion especifica de anomalias termicas con eventos reales. La anomalia se evalua sobre multiples variables, no solo temperatura.

### Ajuste recomendado

Redactar como:

"El prototipo implementa deteccion funcional de condiciones anomalas mediante Isolation Forest y validacion de rangos, incluyendo temperatura como una de las variables evaluadas."

---

## Limite 4 del protocolo

Dashboard interactivo que presente metricas de precision y estados de riesgo.

### Estado

**Cumple parcialmente alto.**

Cumple dashboard y estados de riesgo. La palabra "precision" debe corregirse porque el proyecto usa metricas de regresion, no precision de clasificacion.

### Ajuste recomendado

Cambiar "metricas de precision" por:

"metricas de desempeno del modelo: R2, MAE y RMSE, ademas de estados de riesgo."

---

## Alcance 1 del protocolo

Investigacion restringida a validacion tecnica y prototipo funcional.

### Estado

**Cumple.**

Este es el punto mas importante para defender la tesis. La guia lo respeta.

---

## Alcance 2 del protocolo

Captura de datos en tiempo real supeditada a disponibilidad de redes inalambricas.

### Estado

**No cumple literalmente / ya no aplica.**

El proyecto usa Arduino serial, simulacion y WebSocket local. No depende de redes inalambricas en puntos de prueba.

### Ajuste recomendado

Cambiar a:

"La captura de datos en tiempo real se limita a conexion local por Arduino serial o simulacion dentro del prototipo; la transmision inalambrica queda como ampliacion futura."

---

## Alcance 3 del protocolo

No incluye medidas de mitigacion fisicas automatizadas en cultivos.

### Estado

**Cumple.**

El sistema genera recomendaciones y alertas, no acciona riego, ventilacion ni actuadores.

---

## Alcance 4 del protocolo

Uso de recursos tecnologicos convencionales y bases meteorologicas publicas.

### Estado

**Cumple.**

El proyecto usa herramientas y fuentes publicas/convencionales: Python, FastAPI, React, PostgreSQL, Docker, ERA5-Land, NASA POWER, SoilGrids, Open-Meteo, FAOSTAT e INSIVUMEH procesado.

---

# 4. Indice del protocolo vs guia actual

## Lo que se mantiene bien

- Machine Learning para agricultura.
- XGBoost.
- Isolation Forest.
- Sistemas de alerta.
- Arquitectura IoT como antecedente.
- Dashboard de visualizacion.
- Analisis de bajo rendimiento.
- Factibilidad y escalabilidad.

## Lo que debe corregirse

| Tema del protocolo | Problema | Ajuste recomendado |
|---|---|---|
| LSTM | no implementado | dejar solo como antecedente teorico |
| Z-Score | no es nucleo principal | mencionar como alternativa o para drift si aplica |
| STL | no implementado | dejar como antecedente, no metodologia usada |
| MQTT/LoRaWAN | no implementado | antecedente/futuro, no componente actual |
| ESP32 | proyecto usa Arduino/serial | cambiar a Arduino o dejar ESP32 como propuesta futura |
| precision/F1 | no hay etiquetas reales | cambiar a R2/MAE/RMSE |
| Altiplano Occidental | no hay validacion focalizada | agregar caso demostrativo o ampliar alcance a Guatemala |
| ultimos 30 anios | dataset real visible 2010-2026 | ajustar periodo o agregar fuente 30 anios |

---

# 5. Que debe agregarse a la tesis para cerrar brechas

## Prioridad alta

1. Una seccion clara de "alcance real del prototipo": software funcional, sensores por serial/simulacion, sin validacion fisica en campo.
2. Una tabla de cumplimiento de objetivos del protocolo.
3. Una tabla de limitaciones: sin campo, sin red inalambrica, sin etiquetas reales, sin validacion formal ERA5-Land vs estaciones.
4. Actualizar metricas a `model_comparison.json`.
5. Cambiar metricas de clasificacion por metricas de regresion.

## Prioridad media

1. Caso demostrativo del Altiplano Occidental con departamentos filtrados.
2. Capturas del mapa/coropletico y dataset con tendencia.
3. Captura de alerta Arduino simulada.
4. Tabla de fuentes de datos con periodo real usado.

## Prioridad baja

1. Agregar una subseccion de trabajo futuro para LoRaWAN/MQTT/ESP32.
2. Mantener LSTM/STL como marco teorico, pero no en metodologia.
3. Agregar modo oscuro como mejora UX, no como requisito academico central.

---

# 6. Que debe quitarse o reescribirse

- Quitar afirmaciones de "sensores desplegados en campo" si no existen pruebas reales.
- Quitar "redes inalambricas en puntos de prueba" como requisito cumplido.
- Quitar "ESP32 programado y telemetria" si no hay evidencia.
- Quitar "precision y F1-score" como resultado actual.
- Quitar "datasets historicos del INSIVUMEH" como fuente unica.
- Quitar "validacion final en Altiplano Occidental" si no se hizo caso de estudio formal.
- Reescribir "deteccion de anomalias termicas" como "deteccion funcional de condiciones anomalas y desviaciones de variables agroclimaticas".

---

# 7. Redaccion recomendada para alinear protocolo y tesis

Texto sugerido:

"El protocolo planteo una solucion basada en machine learning e IoT para identificar escenarios de bajo rendimiento agricola. Durante el desarrollo, el alcance se concreto en un prototipo funcional de software que integra fuentes climaticas y edaficas, modelo XGBoost, comparacion con Random Forest, deteccion de anomalias con Isolation Forest, reglas agronomicas, backend FastAPI, frontend React y soporte de lectura Arduino por serial o simulacion. Por tanto, la investigacion cumple la validacion tecnica y funcional del sistema, mientras que la validacion fisica del dispositivo en campo, la transmision inalambrica y la evaluacion supervisada de alertas quedan como trabajo futuro."

---

# 8. Conclusion de la revision

La guia de tesis esta mejor alineada con el proyecto real que el protocolo original. El protocolo sirve como intencion inicial, pero debe reinterpretarse en la tesis para no prometer componentes no implementados. La tesis debe defender que se cumplio la fase de prototipo funcional y validacion tecnica, no una solucion IoT completamente desplegada en campo.

