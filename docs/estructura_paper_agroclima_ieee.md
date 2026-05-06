# Estructura propuesta del paper IEEE - AgroClima GT

> Basado en el formato observado en `C:\Users\edgar\Downloads\TESISXD\ARTICULO.pdf`.
> El PDF corresponde a una plantilla tipo IEEE: titulo, autores, resumen, palabras clave, secciones numeradas con numeros romanos, figuras, tablas, agradecimientos y referencias numeradas.

---

# Un sistema de alerta temprana basado en XGBoost para evaluar el riesgo en el rendimiento de cultivos mediante sensores IoT y fusion de APIs climaticas

**Autor:** Edgar [Apellido]  
**Afiliacion:** [Universidad / Facultad / Escuela]  
**Ciudad, pais:** Guatemala, Guatemala  
**Correo:** [correo institucional o personal]  

---

## Abstract

El rendimiento agricola en Guatemala es vulnerable a variaciones de temperatura, precipitacion, humedad ambiental y condiciones del suelo. Aunque existen fuentes climaticas publicas como ERA5-Land, NASA POWER, Open-Meteo, INSIVUMEH y FAOSTAT, su uso integrado en sistemas operativos de apoyo a la decision agricola sigue siendo limitado. Este trabajo presenta **AgroClima GT**, un prototipo web que combina sensores IoT de bajo costo, un modelo XGBoost para estimacion de rendimiento agricola, reglas agronomicas por cultivo y pronostico meteorologico externo para generar alertas tempranas y recomendaciones especificas.

El sistema integra un backend FastAPI, una interfaz React, una base de datos PostgreSQL y un modulo de lectura Arduino. El modelo XGBoost utiliza variables climaticas, edaficas y de sensores como temperatura, lluvia, humedad, pH del suelo, humedad del suelo, intensidad luminica e indice de verdor. Ademas, incorpora explicabilidad mediante SHAP, deteccion de anomalias y monitoreo de deriva de datos. Los resultados preliminares muestran que XGBoost supera a Random Forest en la comparacion local del proyecto, alcanzando un R2 de 0.7157, MAE de 4.86 y RMSE de 6.04 en la evaluacion registrada.

El prototipo demuestra que es posible fusionar datos historicos, APIs climaticas y sensores fisicos para apoyar decisiones agricolas en contextos con infraestructura limitada. Su principal aporte no es solo predecir riesgo, sino traducir las variables criticas en acciones agronomicas comprensibles para el productor.

## Keywords

XGBoost; agricultura inteligente; sensores IoT; alerta temprana; prediccion agricola; Open-Meteo; ERA5-Land; NASA POWER; PostgreSQL; FastAPI; React; SHAP; agricultura de precision; Guatemala.

---

## I. Introduction

### A. Contexto del problema

Guatemala depende fuertemente de la produccion agricola, especialmente en cultivos sensibles a la variabilidad climatica como maiz, frijol, cafe, papa, tomate, arroz, aguacate y cacao. La alteracion de patrones de lluvia, temperatura y humedad incrementa el riesgo de bajo rendimiento, plagas, enfermedades y estres hidrico.

Aunque existen datos climaticos historicos y servicios meteorologicos abiertos, muchos pequenos productores no cuentan con herramientas que traduzcan esos datos en decisiones practicas. El problema no es unicamente la falta de informacion, sino la falta de integracion entre datos climaticos, sensores locales, modelos predictivos y recomendaciones agronomicas accionables.

### B. Problema de investigacion

Los sistemas tradicionales de monitoreo agricola suelen operar de forma separada: sensores por un lado, prediccion meteorologica por otro y analisis de rendimiento en herramientas externas. Esto limita la capacidad de anticipar condiciones de riesgo antes de que afecten el rendimiento del cultivo.

### C. Objetivo del trabajo

Desarrollar y evaluar un prototipo de alerta temprana agricola que combine sensores IoT, APIs climaticas y aprendizaje automatico para estimar rendimiento, detectar condiciones de riesgo y generar recomendaciones agronomicas por cultivo.

### D. Contribuciones principales

- Integracion de sensores Arduino con una aplicacion web de monitoreo en tiempo real.
- Entrenamiento y uso de un modelo XGBoost para estimar rendimiento agricola.
- Fusion de fuentes climaticas como ERA5-Land, NASA POWER, Open-Meteo, INSIVUMEH y FAOSTAT.
- Generacion de alertas por desviacion respecto a rangos optimos de cultivo.
- Incorporacion de explicabilidad SHAP, deteccion de anomalias y monitoreo de drift.
- Visualizacion operativa mediante dashboard web y panel administrativo.

---

## II. Related Work

### A. Agricultura de precision e IoT

Describir trabajos sobre sensores en agricultura, monitoreo ambiental, estaciones agroclimaticas y sistemas IoT de bajo costo.

**Citas sugeridas desde `docs/referencias.md`:**

- Friha et al. (2021), IoT for smart agriculture.
- Karunathilake et al. (2025), IoT sensors and ML for precision agroecology.
- Davoli et al. (2020), LoRaFarM.
- Prasetya et al. (2022), IoT monitoring for smart greenhouse.

### B. Machine learning para prediccion agricola

Explicar el uso de modelos supervisados para prediccion de rendimiento agricola, destacando XGBoost por su capacidad con datos tabulares y variables heterogeneas.

**Citas sugeridas:**

- Miller et al. (2025), IoT and AI in precision agriculture.
- Tripathy et al. (2025), cloud-edge-device collaborative computing.

### C. Deteccion de anomalias y sistemas de alerta temprana

Relacionar el uso de Isolation Forest, reglas de umbral y sistemas de alerta temprana.

**Citas sugeridas:**

- Liu et al. (2008), Isolation Forest.
- Kaya et al. (2023), anomaly detection in weather forecasting at IoT edges.
- Thalheimer et al. (2025), AI for early warning systems.

### D. Brecha identificada

La literatura suele abordar sensores, prediccion climatica o modelos de rendimiento por separado. AgroClima GT propone una integracion practica: sensores fisicos, APIs climaticas, modelo ML, alertas y recomendaciones agronomicas en una sola plataforma web.

---

## III. Materials and Methods

### A. Arquitectura general del sistema

El prototipo se compone de cuatro capas:

- **Frontend:** React + Vite.
- **Backend:** FastAPI.
- **Persistencia:** PostgreSQL 16 en Docker.
- **Analitica:** XGBoost, SHAP, Isolation Forest y reglas agronomicas.

**Figura sugerida:**

```markdown
![Arquitectura general de AgroClima GT](plantuml/arquitectura_general.png)
Fig. 1. Arquitectura general del sistema AgroClima GT.
```

Si no existe la imagen, generar desde `docs/plantuml/agroclima_gt_diagramas.puml`.

### B. Fuentes de datos

| Fuente | Variables utilizadas | Uso dentro del sistema |
|---|---|---|
| ERA5-Land | temperatura, lluvia, humedad de suelo, temperatura de suelo | entrenamiento y variables historicas |
| NASA POWER | temperatura maxima, temperatura minima, viento | enriquecimiento climatico |
| SoilGrids | pH del suelo | variable edafica |
| Open-Meteo | pronostico de 7 dias, lluvia, temperatura, humedad, ETo | pronostico operativo |
| INSIVUMEH | datos meteorologicos nacionales | contraste y datos locales |
| FAOSTAT | rendimiento agricola por cultivo | calibracion de rendimiento |
| Arduino | temperatura, luz, humedad del suelo, color/verdor | monitoreo en tiempo real |

### C. Dataset de entrenamiento

El proyecto contiene datasets locales en `backend/data/datasets/`. Los principales son:

- `dataset_preliminar.csv`
- `dataset_openmeteo.csv`
- `dataset_v2.csv`
- `crop_optimal_conditions.csv`
- `recommendations.csv`

**Tabla sugerida:**

| Dataset | Descripcion | Columnas clave |
|---|---|---|
| `dataset_openmeteo.csv` | Dataset historico con variables climaticas y de cultivo | municipio, crop, month, year, temperature, rainfall, humidity, soil_ph, yield_pct |
| `dataset_v2.csv` | Dataset enriquecido con NASA POWER y variables extra | temp_max, temp_min, wind_speed |
| `crop_optimal_conditions.csv` | Rangos optimos por cultivo | temp_min, temp_max, rain_min, rain_max, ph_min, ph_max |
| `recommendations.csv` | Recomendaciones por variable y condicion | variable, condition, action, remedy |

### D. Variables del modelo

Las variables usadas por el modelo incluyen:

- municipio codificado
- cultivo codificado
- mes
- temperatura
- precipitacion
- humedad
- pH del suelo
- humedad del suelo
- luz
- indice de verdor
- humedad de suelo profunda
- temperatura del suelo
- temperatura maxima
- temperatura minima
- velocidad del viento

### E. Modelo predictivo

El modelo principal es `XGBRegressor`, entrenado para predecir `yield_pct`, un porcentaje estimado de rendimiento agricola.

**Hiperparametros registrados:**

| Parametro | Valor |
|---|---:|
| `n_estimators` | 400 |
| `max_depth` | 6 |
| `learning_rate` | 0.05 |
| `subsample` | 0.8 |
| `colsample_bytree` | 0.8 |
| `min_child_weight` | 3 |
| `reg_alpha` | 0.1 |
| `reg_lambda` | 1.0 |

### F. Deteccion de anomalias y drift

El sistema usa:

- `Isolation Forest` para detectar anomalias en combinaciones de sensores.
- perfil de distribucion historica para monitorear drift.
- validacion de rangos fisiologicos antes de ejecutar inferencia.

### G. Alertas y recomendaciones

Las alertas se generan comparando lecturas contra rangos optimos por cultivo. La severidad depende del porcentaje de desviacion:

| Nivel | Umbral |
|---|---:|
| Leve | 10% |
| Moderado | 25% |
| Severo | 50% |

Cuando una alerta es severa, el sistema puede enviar correo mediante SMTP.

---

## IV. System Implementation

### A. Backend FastAPI

El backend implementa endpoints para:

- prediccion de rendimiento
- ranking multicultivo
- pronostico meteorologico
- recomendaciones agronomicas
- monitoreo Arduino
- carga de datasets
- administracion del modelo
- historial de predicciones y lecturas

**Tabla sugerida:**

| Endpoint | Funcion |
|---|---|
| `POST /predict` | Predice rendimiento con XGBoost |
| `GET /forecast/{municipio}` | Consulta pronostico de 7 dias |
| `POST /arduino/simulate` | Simula lectura de sensores |
| `WS /ws/arduino` | Transmite lecturas en tiempo real |
| `GET /admin/model-info` | Devuelve metadata del modelo |
| `POST /admin/retrain` | Ejecuta reentrenamiento |

### B. Frontend React

La interfaz incluye:

- panel de inicio
- metricas del dataset
- alertas
- resultados ejecutivos
- pronostico
- monitoreo Arduino
- panel administrativo

**Captura sugerida:**

```markdown
![Dashboard principal](capturas/dashboard_principal.png)
Fig. 2. Dashboard principal de AgroClima GT.
```

### C. Base de datos

PostgreSQL almacena:

- usuarios
- predicciones
- lecturas Arduino
- alertas
- modelos ML
- datasets registrados
- recomendaciones
- feedback del modelo
- configuracion de correo

**Captura sugerida:**

```markdown
![Modelo de datos o tablas principales](capturas/base_datos_tablas.png)
Fig. 3. Tablas principales de PostgreSQL utilizadas por AgroClima GT.
```

### D. Hardware IoT

El modulo Arduino contempla:

- DS18B20 para temperatura.
- TSL2561 para intensidad luminica.
- TCS3200 para color.
- Higrometro capacitivo para humedad del suelo.

**Captura/foto sugerida:**

```markdown
![Prototipo Arduino con sensores](capturas/prototipo_arduino.jpg)
Fig. 4. Prototipo fisico de sensores conectado al sistema.
```

### E. Flujo operativo

```text
Sensor Arduino / Formulario web
        -> Backend FastAPI
        -> Validacion de rangos
        -> Modelo XGBoost
        -> Alertas y recomendaciones
        -> Persistencia PostgreSQL
        -> Dashboard web / correo SMTP
```

---

## V. Results

### A. Resultados del modelo

Segun el archivo `backend/data/models/model_comparison.json`, la comparacion local registra:

| Modelo | R2 | MAE | RMSE |
|---|---:|---:|---:|
| XGBoost | 0.7157 | 4.86 | 6.04 |
| Random Forest | 0.4485 | 6.84 | 8.42 |

Esto indica que XGBoost tuvo mejor desempeno para el conjunto de datos utilizado.

### B. Interpretabilidad

El sistema genera explicaciones SHAP para mostrar que variables aportaron positiva o negativamente a la prediccion.

**Captura sugerida:**

```markdown
![Explicacion SHAP o importancia de variables](capturas/importancia_variables.png)
Fig. 5. Importancia de variables del modelo predictivo.
```

### C. Monitoreo en tiempo real

El modulo Arduino transmite lecturas por WebSocket y actualiza la interfaz en tiempo real.

**Captura sugerida:**

```markdown
![Monitoreo Arduino en tiempo real](capturas/monitoreo_arduino.png)
Fig. 6. Lecturas de sensores visualizadas en tiempo real.
```

### D. Pronostico y calculadora agronomica

El modulo de pronostico consulta Open-Meteo y calcula:

- lluvia semanal
- evapotranspiracion
- deficit de riego
- calendario de siembra
- recomendaciones de riego y pH

**Captura sugerida:**

```markdown
![Pronostico climatico y calculadora agronomica](capturas/pronostico_agronomico.png)
Fig. 7. Pronostico semanal y apoyo agronomico.
```

### E. Alertas y recomendaciones

El sistema no solo marca una condicion de riesgo, tambien devuelve recomendaciones especificas por variable:

| Variable | Condicion | Respuesta esperada |
|---|---|---|
| Temperatura | Alta | Riego de apoyo, proteccion de plantas jovenes |
| Humedad del suelo | Baja | Revisar frecuencia de riego |
| pH | Acido o alcalino | Encalado o acidificacion gradual |
| Luz | Baja o alta | Revisar sombra o exposicion |

---

## VI. Discussion

### A. Valor del enfoque hibrido

AgroClima GT no depende solo de un modelo predictivo. Combina:

- aprendizaje automatico
- reglas agronomicas
- sensores IoT
- APIs climaticas
- recomendaciones interpretables

Este enfoque es adecuado para agricultura porque una prediccion numerica aislada no siempre es suficiente para tomar decisiones en campo.

### B. Fortalezas

- Integracion completa frontend-backend-base de datos.
- Uso de sensores fisicos y simulacion.
- Modelo XGBoost con mejores metricas que Random Forest.
- Explicabilidad con SHAP.
- Alertas accionables.
- Pronostico operativo de 7 dias.

### C. Limitaciones

- El frontend aun usa login local para el acceso principal.
- Algunas funciones existen pero pueden requerir mayor integracion visual, como mapa de riesgo.
- Las recomendaciones dependen de reglas y rangos predefinidos.
- El rendimiento real en campo requiere validacion posterior con productores.
- La calidad del modelo depende de la representatividad de los datos historicos.

### D. Amenazas a la validez

- Datos historicos agregados pueden no representar microclimas locales.
- Sensores de bajo costo requieren calibracion.
- FAOSTAT opera a escalas agregadas, no siempre a escala de parcela.
- El rendimiento estimado `yield_pct` es una aproximacion operacional, no una medicion directa.

---

## VII. Conclusion

Este trabajo presenta AgroClima GT, un prototipo funcional de alerta temprana agricola que integra sensores IoT, datos climaticos abiertos, aprendizaje automatico y recomendaciones agronomicas. El sistema demuestra que XGBoost puede utilizarse para estimar riesgo de rendimiento agricola a partir de variables climaticas y edaficas, mientras que las reglas agronomicas complementan la prediccion con acciones practicas.

La arquitectura implementada permite monitoreo en tiempo real, consulta de pronostico, persistencia historica y administracion del modelo. Como trabajo futuro se propone validar el sistema con datos de campo, mejorar la autenticacion, integrar completamente el mapa de riesgo y evaluar el impacto de las recomendaciones en decisiones reales de productores.

---

## Acknowledgment

El autor agradece a [Universidad/Facultad], docentes asesores y personas que apoyaron el desarrollo del prototipo AgroClima GT. Tambien se reconoce el uso de fuentes abiertas como Open-Meteo, NASA POWER, ERA5-Land, SoilGrids, INSIVUMEH y FAOSTAT.

---

## References

> En formato IEEE, las referencias deben ir numeradas segun orden de aparicion. Puedes tomar la base desde `docs/referencias.md` y reducirla a las fuentes realmente citadas.

[1] J. Muñoz-Sabater et al., "ERA5-Land: A state-of-the-art global reanalysis dataset for land applications," *Earth System Science Data*, vol. 13, no. 9, pp. 4349-4383, 2021.

[2] F. T. Liu, K. M. Ting, and Z.-H. Zhou, "Isolation forest," in *Proc. 8th IEEE Int. Conf. Data Mining*, 2008, pp. 413-422.

[3] O. Friha, M. A. Ferrag, L. Shu, L. Maglaras, and X. Wang, "Internet of Things for the future of smart agriculture: A comprehensive survey of emerging technologies," *IEEE/CAA Journal of Automatica Sinica*, vol. 8, no. 4, pp. 718-752, 2021.

[4] E. M. B. T. Karunathilake et al., "Integrating IoT sensors and machine learning for sustainable precision agroecology," *Discover Agriculture*, 2025.

[5] A. K. Tripathy et al., "Cloud-edge-device collaborative computing in smart agriculture: Architectures, applications, and future perspectives," *Frontiers in Plant Science*, 2025.

[6] NASA POWER Project, "Prediction of Worldwide Energy Resources," NASA Langley Research Center.

[7] Open-Meteo, "Weather Forecast API," Open-Meteo.

[8] FAOSTAT, "Crops and livestock products," Food and Agriculture Organization of the United Nations.

---

## Capturas que faltan colocar

| Captura | Ruta sugerida | Donde va |
|---|---|---|
| Dashboard principal | `docs/capturas/dashboard_principal.png` | Fig. 2 |
| Panel de resultados | `docs/capturas/resultados_prediccion.png` | Seccion V |
| Importancia de variables | `docs/capturas/importancia_variables.png` | Fig. 5 |
| Arduino en tiempo real | `docs/capturas/monitoreo_arduino.png` | Fig. 6 |
| Pronostico y calculadora | `docs/capturas/pronostico_agronomico.png` | Fig. 7 |
| Panel admin/modelo | `docs/capturas/panel_modelo.png` | Resultados o implementacion |
| Diagrama de arquitectura | `docs/capturas/arquitectura_general.png` | Fig. 1 |

---

## Informacion que debes completar antes de convertirlo a PDF/Word IEEE

- Nombre completo del autor.
- Universidad, facultad y carrera.
- Correo u ORCID.
- Nombre del asesor.
- Metricas finales del modelo que vas a defender.
- Tamano definitivo del dataset usado para entrenamiento.
- Capturas reales de la interfaz.
- Tabla final de sensores fisicos usados.
- Referencias finales en formato IEEE.
- Confirmar si el articulo se enfocara en 8 cultivos o en la cobertura ampliada del proyecto.
