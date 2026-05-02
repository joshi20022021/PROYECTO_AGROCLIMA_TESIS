# Marco teórico corregido y alineado al prototipo AgroClima GT

Este documento sirve como versión corregida para integrar en la tesis la parte correspondiente al prototipo implementado en `C:\Users\edgar\Downloads\TESISXD\conferencia`. La revisión se hizo contra el código real del backend, frontend, datasets, scripts y esquema de base de datos. El archivo `docs/tesis.md` está vacío, por lo que no fue posible hacer una corrección línea por línea del texto original; en su lugar se propone una redacción lista para sustituir o complementar el marco de la sección del prototipo.

## 1. Correcciones necesarias para que la tesis concuerde con el prototipo

### 1.1. Elementos que sí deben describirse como implementados

El prototipo implementado corresponde a una plataforma web denominada AgroClima GT, compuesta por un backend en FastAPI, un frontend en React/Vite, una base de datos PostgreSQL ejecutada mediante Docker Compose y un conjunto de artefactos locales de datos y modelos. El sistema permite registrar, consultar y analizar información agroclimática para apoyar decisiones agrícolas a nivel de municipio y cultivo.

En la tesis debe afirmarse como implementado lo siguiente:

- Backend REST y WebSocket con FastAPI.
- Frontend web con React y Vite.
- Persistencia opcional en PostgreSQL 16 mediante Docker Compose.
- Predicción de rendimiento agrícola con XGBoost.
- Detección de anomalías de sensores con Isolation Forest.
- Cálculo de alertas por reglas agronómicas.
- Consulta de pronóstico meteorológico mediante Open-Meteo.
- Integración de datos locales derivados de ERA5-Land, NASA POWER, SoilGrids, Open-Meteo e INSIVUMEH.
- Monitoreo por Arduino mediante puerto serial y transmisión en tiempo real por WebSocket.
- Carga de datasets CSV, generación de plantilla, inventario de datasets y reentrenamiento desde panel administrativo.
- Generación de reportes en PDF desde el frontend.

### 1.2. Elementos que deben editarse o eliminarse si aparecen en el marco actual

No se debe presentar como implementado lo siguiente, porque no aparece funcionalmente completo en `conferencia`:

- LoRaWAN, Sigfox, NB-Fi o NB-IoT: el prototipo usa Arduino por conexión serial local, no una red LPWAN.
- LSTM, redes neuronales recurrentes, transformers o autoencoders: el modelo implementado para predicción es XGBoost y el monitoreo de anomalías usa Isolation Forest.
- STL u otros métodos formales de descomposición de series temporales: no hay una implementación de STL en el backend.
- Edge computing distribuido: el procesamiento principal se ejecuta en backend local, no en nodos edge.
- Sistema desplegado en producción: el proyecto está preparado como prototipo local con `localhost`, Docker Compose y archivos locales.
- NDVI/Sentinel-2 como funcionalidad completa dentro de `conferencia`: el frontend contiene una llamada a `/satellite/ndvi/{municipio}`, pero el backend de `conferencia` no define ese endpoint. Puede mencionarse solo como funcionalidad en integración o pendiente, no como módulo operativo.
- Autenticación robusta con JWT, OAuth o control avanzado de permisos: existe login básico, usuario administrador fijo y registro con hash de contraseña cuando PostgreSQL está disponible.
- Inferencia basada únicamente en datos reales observados de campo: el dataset combina datos climáticos/fuentes externas con funciones agronómicas y datos generados/procesados para entrenamiento.

### 1.3. Redacción corregida del alcance del prototipo

El prototipo AgroClima GT debe describirse como un sistema de apoyo a la decisión agroclimática en ambiente local. Su finalidad es integrar datos climáticos, datos de suelo, lecturas de sensores y modelos de aprendizaje automático para estimar rendimiento agrícola, identificar condiciones de riesgo y generar recomendaciones agronómicas. El alcance no es reemplazar la asistencia técnica agrícola ni constituir un sistema nacional de alerta temprana en producción, sino demostrar la viabilidad técnica de una arquitectura web que combine datos agroclimáticos, sensores e inteligencia artificial aplicada a cultivos en Guatemala.

## 2. Marco teórico propuesto para el prototipo

### 2.1. Agricultura de precisión y monitoreo agroclimático

La agricultura de precisión se basa en el uso de datos para observar, interpretar y responder a la variabilidad climática, edáfica y productiva de los cultivos. En contextos agrícolas expuestos a sequías, exceso de lluvia, variaciones térmicas y cambios en la humedad del suelo, los sistemas digitales permiten transformar observaciones dispersas en indicadores útiles para la toma de decisiones. En el prototipo AgroClima GT, esta idea se materializa mediante la integración de variables como temperatura, precipitación, humedad relativa, pH del suelo, humedad del suelo, radiación/luz, temperatura del suelo y velocidad del viento.

El sistema no se limita a mostrar datos climáticos, sino que los relaciona con cultivos y municipios. Esto permite calcular niveles de riesgo, estimar rendimiento y emitir recomendaciones. Esta orientación coincide con los sistemas visuales de apoyo a la decisión agrícola, los cuales organizan información técnica para facilitar el análisis operativo por parte del usuario.

### 2.2. Sistemas de apoyo a la decisión agrícola

Un sistema de apoyo a la decisión agrícola combina datos, reglas, modelos y visualización para entregar información accionable al productor, técnico o administrador. En AgroClima GT, este concepto se refleja en tres capas funcionales. La primera capa captura o consulta datos desde formularios, sensores Arduino y servicios meteorológicos. La segunda capa procesa los datos mediante reglas agronómicas, modelos de machine learning y consultas a datasets locales. La tercera capa presenta resultados en paneles, mapas, alertas, reportes y vistas administrativas.

El valor del sistema está en convertir variables técnicas en salidas comprensibles: porcentaje estimado de rendimiento, nivel de riesgo, alertas por condición climática, calendario de siembra, estrés hídrico y recomendaciones por cultivo. Por ello, el prototipo debe fundamentarse como una herramienta de apoyo, no como un sistema automático de decisión final.

### 2.3. Datos climáticos y reanálisis ERA5-Land

Los datos climáticos históricos son necesarios para entrenar modelos y construir indicadores agroclimáticos. El prototipo utiliza archivos locales derivados de ERA5-Land para representar condiciones mensuales de municipios guatemaltecos. ERA5-Land es un producto de reanálisis orientado a aplicaciones terrestres que describe de forma consistente variables relacionadas con el ciclo del agua y la energía sobre superficie terrestre. Su uso es pertinente para el prototipo porque permite disponer de series históricas homogéneas aun cuando no existan estaciones meteorológicas locales completas para todos los municipios.

En la implementación revisada existen archivos NetCDF anuales de ERA5-Land y CSV procesados, entre ellos `era5_mensual.csv`, `dataset_v2.csv`, `water_stress_index.csv` y `sowing_calendar.csv`. El dataset principal `dataset_v2.csv` contiene 1,320,345 registros, 61 municipios y 37 cultivos. Esto respalda que el marco teórico hable de datos agroclimáticos históricos procesados, pero debe evitar afirmar que todo proviene de mediciones directas de campo.

### 2.4. Fuentes complementarias: Open-Meteo, NASA POWER, SoilGrids e INSIVUMEH

El prototipo usa Open-Meteo para consultar pronósticos meteorológicos a corto plazo desde el backend. Open-Meteo expone una API de pronóstico basada en coordenadas geográficas y devuelve resultados en formato JSON, lo que facilita su integración con aplicaciones web. En AgroClima GT, esta consulta alimenta la vista de pronóstico, el formulario principal y el cálculo de variables como lluvia esperada, temperatura y humedad.

NASA POWER aparece como fuente local procesada para variables complementarias como radiación solar, temperatura máxima, temperatura mínima y viento. SoilGrids se usa como fuente de propiedades de suelo por municipio. INSIVUMEH aparece integrado como fuente reciente mediante archivos diarios y mensuales procesados, con endpoints `/insivumeh/monthly` y `/insivumeh/daily`. Estas fuentes deben describirse como fuentes de datos integradas o procesadas localmente, no como servicios en línea consultados en todos los casos.

### 2.5. Internet de las Cosas agrícola y sensores con Arduino

El Internet de las Cosas aplicado a la agricultura permite recopilar variables ambientales y de suelo mediante sensores conectados. En el prototipo, esta función se implementa con Arduino por puerto serial, no con redes inalámbricas de largo alcance. El backend incluye un lector serial, detección de puertos, conexión/desconexión, simulación de lecturas y transmisión de datos al frontend mediante WebSocket.

Las variables esperadas incluyen temperatura, humedad, humedad del suelo, luz, índice de verdor, pH y precipitación estimada o capturada. Con estas lecturas, el backend puede ejecutar predicciones, detectar anomalías, guardar registros en PostgreSQL y emitir alertas. Por tanto, las referencias sobre IoT agrícola sí son pertinentes como base general, pero las referencias centradas en LoRaWAN deben usarse solo como contexto de conectividad agrícola, no como descripción del prototipo implementado.

### 2.6. API web, backend y comunicación en tiempo real

El backend del prototipo usa FastAPI para exponer endpoints REST y un canal WebSocket. FastAPI es adecuado para este tipo de prototipo porque se basa en estándares abiertos como OpenAPI y JSON Schema, además de ofrecer validación de datos y documentación automática. En AgroClima GT, los endpoints gestionan predicción, datasets, pronóstico, alertas, Arduino, autenticación, administración, comparación de modelos y reportes de estado.

El WebSocket se usa para entregar al frontend lecturas de Arduino en tiempo real. Esta decisión técnica es coherente con la necesidad de mostrar lecturas continuas de sensores sin depender de recargas manuales. En la tesis debe diferenciarse entre endpoints REST, usados para solicitudes puntuales, y WebSocket, usado para flujo continuo de datos.

### 2.7. Frontend web y visualización de información agroclimática

El frontend está desarrollado con React y Vite. React organiza la interfaz en componentes reutilizables y permite construir vistas interactivas a partir de estado, propiedades y eventos. En el prototipo existen vistas para tablero principal, dataset, alertas, resultados, pronóstico, Arduino, modelos, mapa de riesgo y administración.

La visualización es una parte central del sistema porque convierte datos técnicos en indicadores interpretables. El uso de Chart.js, Leaflet, html2canvas y jsPDF permite graficar métricas, representar puntos de riesgo, generar reportes y exportar resultados. Por ello, el marco teórico debe incluir visualización de datos y sistemas de apoyo a la decisión, no solo machine learning.

### 2.8. Predicción de rendimiento con XGBoost

XGBoost es una biblioteca optimizada de gradient boosting que implementa modelos basados en árboles de decisión. En el prototipo se usa para estimar `yield_pct`, un porcentaje de rendimiento esperado a partir de variables climáticas, edáficas y de cultivo. El modelo se carga desde `xgboost_yield.joblib` y utiliza codificadores guardados en `label_encoders.joblib`.

La implementación incluye validación de entradas, preparación de variables, predicción, clasificación del rendimiento y explicación de los factores que influyen en la salida. El archivo `model_comparison.json` registra una comparación local donde XGBoost obtuvo R2 de 0.7157, MAE de 4.86 y RMSE de 6.04 frente a Random Forest con R2 de 0.4485, MAE de 6.84 y RMSE de 8.42. Estos resultados pueden citarse como resultados internos del prototipo, no como resultados generalizables a producción.

### 2.9. Explicabilidad con SHAP

El prototipo incluye funciones para explicar predicciones mediante contribuciones SHAP cuando el modelo y las dependencias lo permiten. La explicabilidad es importante porque una predicción agrícola no debe presentarse como una caja cerrada: el usuario necesita saber si la estimación se debe principalmente a lluvia, temperatura, humedad, pH, humedad del suelo u otras variables.

En la tesis puede justificarse SHAP como mecanismo de interpretación del modelo, pero conviene redactarlo como explicación técnica auxiliar. Si en una ejecución local SHAP no está disponible o falla, el sistema debe seguir funcionando con la predicción base.

### 2.10. Detección de anomalías y drift

La detección de anomalías se implementa mediante Isolation Forest, un método no supervisado que identifica observaciones inusuales a partir de particiones aleatorias de los datos. En AgroClima GT se aplica a lecturas o entradas de sensores para detectar valores fuera del comportamiento esperado. El backend también calcula drift comparando entradas actuales contra un perfil de entrenamiento guardado en `drift_profile.json`.

Esta sección debe reemplazar cualquier explicación sobre LSTM, transformers, STL o autoencoders, ya que esos métodos no están implementados en el prototipo. El fundamento correcto es aprendizaje automático tabular con XGBoost para predicción e Isolation Forest para anomalías.

### 2.11. Alertas y recomendaciones agronómicas

El sistema de alertas usa reglas agronómicas y rangos óptimos por cultivo. La fuente local `crop_optimal_conditions.csv` contiene 37 cultivos con rangos de temperatura, lluvia, humedad, pH, humedad de suelo, luz e índice de verdor. La fuente `recommendations.csv` contiene recomendaciones por cultivo, variable y condición.

Cuando una variable está fuera de rango, el sistema clasifica severidad y genera mensajes de acción. En modo Arduino, las alertas persistentes pueden enviarse por correo si SMTP está configurado. Esta parte debe describirse como un motor de reglas complementario al modelo ML, no como un sistema experto completo ni como una alerta temprana oficial.

### 2.12. Persistencia, trazabilidad y administración

PostgreSQL se usa para almacenar usuarios, predicciones, lecturas Arduino, alertas, modelos, datasets, fuentes de datos, métricas climáticas, feedback, configuración de correo y recomendaciones. Docker Compose define el servicio de base de datos, credenciales locales, puerto `5435` y volumen persistente.

La capa administrativa permite consultar estadísticas, predicciones, lecturas, datasets, estado del modelo, comparación de modelos y reentrenamiento. Esta trazabilidad es relevante para una tesis porque muestra que el prototipo no solo predice, sino que registra evidencia operativa para revisión posterior.

### 2.13. Limitaciones técnicas del prototipo

El prototipo tiene límites que deben declararse para evitar sobreafirmaciones:

- Funciona principalmente en ambiente local.
- La calidad de la predicción depende de datasets procesados y supuestos agronómicos.
- Las lecturas Arduino requieren hardware compatible o simulación.
- La base de datos es opcional; si PostgreSQL no está activo, algunas funciones operan con CSV locales.
- El envío de correo depende de configuración SMTP.
- El endpoint de NDVI/Sentinel-2 no está implementado en el backend de `conferencia`.
- El sistema no sustituye validación agronómica en campo ni recomendaciones de instituciones oficiales.

## 3. Referencias: mantener, usar con cuidado o retirar

### 3.1. Referencias que sí son relevantes para este prototipo

- Muñoz-Sabater et al. (2021), ERA5-Land: base climática histórica y reanálisis terrestre.
- Open-Meteo (documentación oficial): consulta de pronóstico meteorológico por API.
- XGBoost documentation: fundamento del modelo de predicción tabular.
- Liu, Ting y Zhou (2008), Isolation Forest: detección de anomalías.
- scikit-learn IsolationForest documentation: implementación práctica usada por el prototipo.
- FastAPI documentation: backend REST, validación y documentación OpenAPI.
- React documentation: construcción de interfaz por componentes.
- PostgreSQL documentation: persistencia relacional.
- Docker Compose documentation: servicio local de base de datos y volumen.
- Friha et al. (2021), IoT en agricultura: contexto general para sensores agrícolas.
- Gutiérrez et al. (2022), sistemas visuales de apoyo a la decisión agrícola.
- MAGA, INSIVUMEH, SEGEPLAN y Banco Mundial: contexto climático y agrícola de Guatemala.

### 3.2. Referencias que pueden quedarse solo como contexto, no como tecnología implementada

- LoRaWAN, Sigfox, NB-Fi y LPWAN: útiles para antecedentes de IoT agrícola, pero el prototipo usa Arduino serial.
- Edge computing: útil como tendencia, pero no como arquitectura implementada.
- STL: útil para antecedentes de análisis de series temporales, pero no se implementó descomposición STL.
- LSTM, transformers y autoencoders: útiles como comparación académica, pero deben retirarse del marco del prototipo si se presentan como parte del sistema.

### 3.3. Referencias que conviene revisar o sustituir

- Referencias fechadas en 2026 o 2025 que parezcan futuras o no verificables deben revisarse antes de incluirse como fuente formal. En particular, no conviene apoyar el marco central en documentos con fechas posteriores a la entrega real del prototipo si no fueron efectivamente usados.
- Las referencias de leyes de privacidad o ética pueden mantenerse solo si la tesis incluye una sección de tratamiento responsable de datos. No son centrales para explicar el prototipo técnico.
- Las referencias de modelos no implementados deben moverse a antecedentes o eliminarse del marco teórico del prototipo.

## 4. Referencias recomendadas para el marco corregido

FastAPI. (2026). Features. FastAPI documentation. https://fastapi.tiangolo.com/features/

Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008). Isolation forest. Proceedings of the 8th IEEE International Conference on Data Mining, 413-422. https://doi.org/10.1109/ICDM.2008.17

Muñoz-Sabater, J., Dutra, E., Agustí-Panareda, A., Albergel, C., Arduini, G., Balsamo, G., Boussetta, S., Choulga, M., Harrigan, S., Martens, B., Miralles, D. G., Piles, M., Rodríguez-Fernández, N. J., Zsoter, E., Buontempo, C., & Thépaut, J.-N. (2021). ERA5-Land: A state-of-the-art global reanalysis dataset for land applications. Earth System Science Data, 13, 4349-4383. https://doi.org/10.5194/essd-13-4349-2021

Open-Meteo. (2026). Weather Forecast API documentation. https://open-meteo.com/en/docs

PostgreSQL Global Development Group. (2026). PostgreSQL 16 Documentation. https://www.postgresql.org/docs/16/

React. (2026). Quick Start. React documentation. https://react.dev/learn

scikit-learn developers. (2026). IsolationForest. scikit-learn documentation. https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html

XGBoost developers. (2026). XGBoost documentation. https://xgboost.readthedocs.io/en/stable/

Docker. (2026). How Compose works. Docker Docs. https://docs.docker.com/compose/intro/compose-application-model/

Friha, O., Ferrag, M. A., Shu, L., Maglaras, L., & Wang, X. (2021). Internet of Things for the future of smart agriculture: A comprehensive survey of emerging technologies. IEEE/CAA Journal of Automatica Sinica, 8(4), 718-752. https://doi.org/10.1109/JAS.2021.1003925

Gutiérrez, F., Htun, N. N., Schlenz, F., Kasimati, A., & Verbert, K. (2022). Developing visual-assisted decision support systems across diverse agricultural use cases. Agriculture, 12(7), 1027. https://doi.org/10.3390/agriculture12071027

## 5. Texto breve recomendado para insertar como delimitación del prototipo

El presente prototipo se desarrolló como una plataforma local de apoyo a la decisión agroclimática. Integra datos históricos y recientes de fuentes climáticas, propiedades de suelo, lecturas de sensores Arduino y modelos de aprendizaje automático para estimar rendimiento agrícola y emitir alertas por condiciones de riesgo. La arquitectura está compuesta por un backend FastAPI, un frontend React/Vite, una base PostgreSQL opcional en Docker y artefactos locales de datos y modelos. Su alcance es demostrativo y académico; por tanto, los resultados deben interpretarse como apoyo técnico preliminar y no como sustituto de validación agronómica en campo ni de servicios oficiales de alerta.

