# Guia de ajuste para tesis AgroClima GT

Documento preparado a partir de la revision de `docs/PLANTILLA_APA 7_FINAL ENERO 2023.pdf` y del estado real del proyecto `PROYECTO_AGROCLIMA_TESIS`.

El objetivo es que puedas copiar por incisos al documento final y luego editar redaccion, numeracion de figuras, tablas y capturas. Se prioriza lo que existe en el proyecto: backend FastAPI, frontend React/Vite, PostgreSQL, datasets CSV/NetCDF/JSON, modelo XGBoost, comparacion con Random Forest, Isolation Forest, data drift, mapa de riesgo, exportacion CSV, reportes, Arduino por serial/simulacion y WebSocket.

## Ajustes generales detectados al comparar PDF vs proyecto

- El PDF debe evitar afirmar validacion de sensores en parcelas reales. El proyecto soporta Arduino por software, lectura serial, simulacion y WebSocket, pero la validacion fisica en campo debe quedar como pendiente.
- El PDF menciona STL, LSTM o metricas de clasificacion como si fueran componentes centrales. En el proyecto real, el nucleo implementado es XGBoost para regresion, Random Forest como comparacion, Isolation Forest para anomalias y reglas agronomicas para alertas.
- La comparacion actual en `backend/data/models/model_comparison.json` es: XGBoost R2 = 0.6334, MAE = 5.91, RMSE = 7.68; Random Forest R2 = 0.3474, MAE = 8.26, RMSE = 10.25. Si el PDF conserva R2 = 0.7157 o Random Forest = 0.4485, actualizalo o aclara que corresponde a una corrida anterior.
- El dataset final disponible es `dataset_faostat.csv` con 2,111,220 registros. Tambien existen `dataset_combinado.csv`, `dataset_v2.csv`, `dataset_openmeteo.csv` y `dataset_preliminar.csv`.
- El sistema ya incluye visualizaciones nuevas que conviene reflejar: tendencia de `yield_pct`, mapa de riesgo, coropletico departamental, comparacion visual de modelos, historial Arduino, modo oscuro, filtros y exportacion CSV.

---

# GLOSARIO

Puedes colocar estos terminos en orden alfabetico. Si tu formato pide sangria francesa o tabla, adapta el formato, pero conserva las definiciones.

**AgroClima GT.** Prototipo web desarrollado para integrar datos climaticos, edaficos y agronomicos con modelos de aprendizaje automatico, con el fin de estimar rendimiento agricola, visualizar riesgo y generar alertas o recomendaciones para cultivos en Guatemala.

**Alerta agroclimatica.** Mensaje generado por el sistema cuando una variable climatica, edafica o de sensor se encuentra fuera de un rango considerado adecuado para un cultivo. En el prototipo, las alertas se clasifican por severidad y se acompanan de recomendaciones.

**Altiplano Occidental.** Region del occidente de Guatemala caracterizada por condiciones de altura y variabilidad termica que pueden influir en cultivos como maiz, frijol, papa, cafe y hortalizas. En esta tesis puede usarse como caso demostrativo, aunque el prototipo cubre mas departamentos.

**API.** Interfaz de programacion de aplicaciones. En AgroClima GT, el backend FastAPI expone endpoints para prediccion, pronostico, datasets, alertas, Arduino, administracion y consulta de metricas.

**Arduino.** Plataforma de hardware libre usada como base para la integracion futura de sensores fisicos. En el prototipo actual, el software ya contempla conexion serial, simulacion de lecturas y transmision por WebSocket.

**Backend.** Capa de software que recibe solicitudes del frontend, valida datos, ejecuta modelos predictivos, consulta archivos, gestiona alertas y expone servicios HTTP/WebSocket.

**CSV.** Formato de archivo tabular separado por comas. En el proyecto se usa para datasets climaticos, agronomicos, recomendaciones, fuentes y exportacion de registros desde la plataforma.

**Data drift.** Cambio en la distribucion de los datos de entrada respecto a la distribucion usada durante el entrenamiento del modelo. En el prototipo se calcula mediante comparacion de variables contra un perfil estadistico de entrenamiento.

**Dataset.** Conjunto de datos estructurado utilizado para analisis, entrenamiento o validacion. AgroClima GT utiliza varios datasets, incluido `dataset_faostat.csv` como conjunto calibrado para el modelo.

**Deteccion de anomalias.** Proceso de identificar observaciones o lecturas que se alejan del comportamiento esperado. En el prototipo se implementa mediante Isolation Forest y reglas de validacion por rango.

**ERA5-Land.** Dataset de reanalisis climatico terrestre utilizado como fuente historica de variables climaticas y de suelo.

**FAOSTAT.** Base de datos estadistica de la Organizacion de las Naciones Unidas para la Alimentacion y la Agricultura. En el proyecto se utiliza para calibrar el rendimiento agricola (`yield_pct`) con registros reales de Guatemala.

**FastAPI.** Framework de Python utilizado para desarrollar la API del backend del prototipo.

**Frontend.** Capa visual de la aplicacion. En AgroClima GT fue construida con React y Vite, e incluye dashboard, dataset, alertas, reportes, pronostico, mapa, Arduino y panel administrativo.

**Indice de verdor.** Indicador numerico que aproxima el estado visual de la vegetacion a partir de canales de color. En el proyecto se expresa como `greenness_idx` y puede calcularse con la proporcion del canal verde respecto a la suma RGB.

**INSIVUMEH.** Instituto Nacional de Sismologia, Vulcanologia, Meteorologia e Hidrologia de Guatemala. En el prototipo se considera como fuente nacional de referencia climatica procesada localmente.

**IoT.** Internet de las Cosas. Se refiere a la integracion de dispositivos fisicos conectados para capturar y transmitir datos. En esta tesis, el IoT fisico completo se plantea como continuidad posterior; el prototipo actual deja lista la base de software para integrarlo.

**Isolation Forest.** Algoritmo de deteccion de anomalias que identifica observaciones atipicas a partir de la facilidad con que pueden ser aisladas dentro de arboles aleatorios.

**MAE.** Error absoluto medio. Metrica de regresion que mide el promedio de las diferencias absolutas entre valores reales y predichos.

**Mapa de riesgo.** Visualizacion geografica que permite observar niveles de riesgo o rendimiento esperado por departamento o municipio.

**Modelo predictivo.** Componente de aprendizaje automatico que estima una salida a partir de variables de entrada. En AgroClima GT, el modelo principal estima `yield_pct`.

**NASA POWER.** Fuente de datos climaticos y energeticos de NASA usada como complemento para variables meteorologicas.

**Open-Meteo.** Servicio de pronostico meteorologico utilizado para consultar condiciones climaticas recientes o futuras mediante coordenadas.

**PostgreSQL.** Sistema gestor de base de datos relacional usado para almacenar usuarios, predicciones, alertas, lecturas, datasets y metadata del modelo cuando la base de datos esta activa.

**R2.** Coeficiente de determinacion. Metrica de regresion que indica que proporcion de la variabilidad de la variable objetivo es explicada por el modelo.

**Random Forest.** Modelo de ensamble basado en multiples arboles de decision. En el proyecto se utiliza como linea base comparativa frente a XGBoost.

**React.** Biblioteca de JavaScript utilizada para construir la interfaz web del prototipo.

**Recomendacion agronomica.** Sugerencia generada por el sistema a partir de variables fuera de rango, cultivo seleccionado y severidad detectada.

**RMSE.** Raiz del error cuadratico medio. Metrica de regresion que penaliza mas los errores grandes.

**SHAP.** Metodo de explicabilidad que descompone una prediccion en contribuciones individuales de cada variable. En el prototipo se contempla para explicar resultados del modelo cuando la dependencia esta disponible.

**SoilGrids.** Fuente global de informacion de suelos usada para variables edaficas como pH.

**WebSocket.** Protocolo de comunicacion bidireccional utilizado en AgroClima GT para transmitir lecturas de Arduino o simulaciones en tiempo real hacia el frontend.

**XGBoost.** Algoritmo de gradient boosting usado como modelo principal para estimar el rendimiento agricola esperado (`yield_pct`).

**Yield_pct.** Variable objetivo del modelo. Representa el porcentaje estimado de rendimiento agricola esperado, en una escala de 0 a 100.

---

# LISTA DE SIMBOLOS

Puedes colocar esta lista despues del glosario y antes del resumen. Los simbolos provienen de la plantilla, del protocolo y de `docs/formulas_tesis.tex`. Si tu documento final separa "simbolos" y "abreviaturas", deja aqui las expresiones matematicas y mueve siglas como API, CSV, FAOSTAT, MAE, RMSE, SHAP, IoT y XGBoost a una lista de abreviaturas.

Nota de consistencia: algunos simbolos cambian de significado segun la ecuacion. Por ejemplo, `T` puede representar temperatura media en las variables agroclimaticas, numero de hojas en la regularizacion de XGBoost o numero de arboles en TreeSHAP. Para evitar confusion en la tesis, explica el significado en cada formula o usa subindices como `T_air`, `T_s`, `T_max` y `T_min` cuando sea necesario.

## Simbolos generales del dataset y del modelo

| Simbolo | Significado | Unidad o uso |
|---|---|---|
| `i` | Indice de una observacion del dataset | Adimensional |
| `j` | Indice de una caracteristica o variable | Adimensional |
| `n` | Numero total de observaciones o muestras | Registros |
| `p` | Numero de caracteristicas de entrada del modelo | Variables |
| `c` | Cultivo analizado | Categoria |
| `a` | Anio de referencia | Anio calendario |
| `y_i` | Valor real u observado de la variable objetivo para la muestra `i` | Porcentaje de rendimiento |
| `hat{y}_i` | Valor predicho por el modelo para la muestra `i` | Porcentaje de rendimiento |
| `bar{y}` | Promedio de los valores reales de la variable objetivo | Porcentaje de rendimiento |
| `yield_pct` | Variable objetivo del sistema; rendimiento agricola esperado normalizado | Porcentaje, escala 0-100 |
| `mathbf{x}` | Vector de caracteristicas de una observacion | Vector |
| `mathbf{x}_i` | Vector de caracteristicas de la muestra `i` | Vector |
| `mathbb{R}^{17}` | Espacio numerico de 17 variables de entrada | Vector de 17 dimensiones |
| `clip(valor, min, max)` | Funcion que limita un valor dentro de un intervalo definido | Operador matematico |

## Variables agroclimaticas y edaficas

| Simbolo | Significado | Unidad o uso |
|---|---|---|
| `T` | Temperatura media del aire, cuando aparece en el vector agroclimatico | Grados Celsius |
| `T_s` | Temperatura del suelo | Grados Celsius |
| `T_max` | Temperatura maxima | Grados Celsius |
| `T_min` | Temperatura minima | Grados Celsius |
| `R` | Precipitacion acumulada o lluvia | Milimetros |
| `H` | Humedad relativa ambiental | Porcentaje |
| `pH` | Potencial de hidrogeno del suelo | Escala de pH |
| `theta_1` | Humedad del suelo en capa superficial de 0 a 7 cm | m3/m3 |
| `theta_2` | Humedad del suelo en capa de 7 a 28 cm | m3/m3 |
| `theta_3` | Humedad del suelo en capa de 28 a 100 cm | m3/m3 |
| `L` | Luminosidad o intensidad de luz | Lux |
| `G` | Indice de verdor de la vegetacion | Porcentaje o indice |
| `R_raw` | Canal rojo de una lectura RGB | Valor digital |
| `G_raw` | Canal verde de una lectura RGB | Valor digital |
| `B_raw` | Canal azul de una lectura RGB | Valor digital |
| `v_w` | Velocidad del viento | m/s |
| `z` | Altitud del punto geografico | Metros sobre el nivel del mar |

## Simbolos del modelo XGBoost

| Simbolo | Significado | Unidad o uso |
|---|---|---|
| `mathcal{L}(theta)` | Funcion objetivo que minimiza el modelo XGBoost | Funcion de perdida regularizada |
| `theta` | Parametros del modelo | Parametros |
| `ell(y_i, hat{y}_i)` | Funcion de perdida entre valor real y valor predicho | Error de prediccion |
| `K` | Numero total de arboles del ensamble | Arboles |
| `k` | Indice de arbol dentro del ensamble o indice de fold en validacion cruzada, segun contexto | Adimensional |
| `f_k` | Arbol de regresion `k` dentro del modelo XGBoost | Funcion predictiva |
| `mathcal{F}` | Espacio de arboles de regresion; en SHAP tambien puede representar el conjunto de caracteristicas | Conjunto |
| `Omega(f_k)` | Termino de regularizacion aplicado al arbol `f_k` | Penalizacion |
| `gamma` | Penalizacion por complejidad estructural o numero de hojas | Hiperparametro |
| `lambda` | Regularizacion L2 sobre los pesos de las hojas | Hiperparametro |
| `eta` | Tasa de aprendizaje del modelo | Hiperparametro |
| `w_j` | Peso asignado a la hoja `j` de un arbol | Valor numerico |
| `g_i` | Gradiente de primer orden de la perdida para la muestra `i` | Derivada |
| `h_i` | Gradiente de segundo orden o Hessiano para la muestra `i` | Derivada |
| `tilde{mathcal{L}}^{(t)}` | Aproximacion de segundo orden de la funcion objetivo en la iteracion `t` | Funcion aproximada |

## Calibracion FAOSTAT e intervalos de prediccion

| Simbolo | Significado | Unidad o uso |
|---|---|---|
| `hat{R}(c,a)` | Rendimiento reportado por FAOSTAT para el cultivo `c` en el anio `a` | kg/ha |
| `R_ref(c)` | Rendimiento historico de referencia para el cultivo `c` | kg/ha |
| `f_FAO(c,a)` | Factor de calibracion FAOSTAT para el cultivo `c` y anio `a` | Factor |
| `bar{f}(c)` | Promedio del factor FAOSTAT para el cultivo `c` | Factor |
| `A_c` | Conjunto de anios con datos FAOSTAT disponibles para el cultivo `c` | Conjunto |
| `hat{y}_{base}` | Prediccion base del rendimiento antes de ajuste | Porcentaje |
| `hat{y}_{adj}` | Prediccion ajustada por el factor FAOSTAT | Porcentaje |
| `mathcal{P}` | Conjunto de predicciones parciales usado para estimar dispersion | Conjunto |
| `k^*` | Punto de corte parcial de arboles usado para construir `mathcal{P}` | Indice |
| `sigma` | Desviacion estandar de las predicciones parciales | Porcentaje |
| `m` | Margen de confianza aplicado al intervalo de prediccion | Porcentaje |
| `hat{y}_{low}` | Limite inferior del intervalo de prediccion | Porcentaje |
| `hat{y}_{high}` | Limite superior del intervalo de prediccion | Porcentaje |

## Explicabilidad, riesgo y alertas

| Simbolo | Significado | Unidad o uso |
|---|---|---|
| `phi_0` | Valor base de la explicacion SHAP | Porcentaje de rendimiento |
| `phi_j` | Contribucion SHAP de la caracteristica `j` | Aporte a la prediccion |
| `S` | Subconjunto o coalicion de caracteristicas usado en SHAP | Conjunto |
| `s_R` | Componente de riesgo asociado a precipitacion | Puntaje |
| `s_T` | Componente de riesgo asociado a temperatura | Puntaje |
| `s_H` | Componente de riesgo asociado a humedad | Puntaje |
| `s_pH` | Componente de riesgo asociado al pH del suelo | Puntaje |
| `c_f` | Factor de sensibilidad del cultivo | Factor |
| `score` | Puntaje total de riesgo calculado por reglas | Escala 0-100 |
| `score_ML` | Puntaje de riesgo derivado del modelo predictivo | Escala 0-100 |
| `score_reglas` | Puntaje de riesgo derivado de reglas agronomicas | Escala 0-100 |
| `score_final` | Puntaje final combinado de riesgo | Escala 0-100 |
| `v` | Variable analizada para generar alerta | Variable |
| `x` | Valor observado de una variable | Segun variable |
| `v_min` | Limite inferior del rango optimo de una variable | Segun variable |
| `v_max` | Limite superior del rango optimo de una variable | Segun variable |
| `Delta_v` | Desviacion porcentual de una variable fuera de su rango optimo | Porcentaje |

## Anomalias y data drift

| Simbolo | Significado | Unidad o uso |
|---|---|---|
| `s(mathbf{x}, n)` | Puntaje de anomalia calculado por Isolation Forest | Escala normalizada |
| `E[h(mathbf{x})]` | Longitud esperada del camino para aislar una observacion | Nivel de arbol |
| `h(mathbf{x})` | Longitud del camino de una observacion en Isolation Forest | Nivel de arbol |
| `c(n)` | Factor de normalizacion de la longitud promedio del camino | Factor |
| `H(n)` | Funcion armonica usada en la normalizacion de Isolation Forest; no confundir con humedad `H` | Funcion |
| `d(mathbf{x})` | Funcion de decision del Isolation Forest | Puntaje |
| `z_a` | Puntuacion normalizada de anomalia | Z-score |
| `mu_d` | Media de la funcion de decision | Puntaje |
| `sigma_d` | Desviacion estandar de la funcion de decision | Puntaje |
| `p_05` | Percentil 5 usado como umbral de referencia | Percentil |
| `x_j` | Valor observado de la caracteristica `j` en monitoreo de drift | Segun variable |
| `mu_j` | Media de entrenamiento de la caracteristica `j` | Segun variable |
| `sigma_j` | Desviacion estandar de entrenamiento de la caracteristica `j` | Segun variable |
| `z_j` | Distancia estandarizada de una caracteristica respecto al perfil de entrenamiento | Z-score absoluto |
| `sim_j` | Similitud de la caracteristica `j` respecto a la distribucion de entrenamiento | Porcentaje |
| `bar{sim}` | Similitud global promedio usada para clasificar data drift | Porcentaje |

## Metricas, pronostico y geografia

| Simbolo | Significado | Unidad o uso |
|---|---|---|
| `MAE` | Error absoluto medio entre valores reales y predichos | Porcentaje |
| `RMSE` | Raiz del error cuadratico medio | Porcentaje |
| `R2` | Coeficiente de determinacion del modelo | Proporcion o porcentaje explicado |
| `R^2_k` | Coeficiente de determinacion obtenido en el fold `k` | Metrica de validacion |
| `overline{R^2}_{CV}` | Promedio de `R2` en validacion cruzada | Metrica de validacion |
| `CV` | Validacion cruzada | Procedimiento de evaluacion |
| `lambda_i` | Longitud geografica del departamento o punto `i` | Grados decimales |
| `phi_i` | Latitud geografica del departamento o punto `i` | Grados decimales |
| `Delta t` | Ventana temporal usada para cache de pronostico | Horas |
| `t_actual` | Momento actual del sistema | Fecha y hora |
| `t_consulta` | Momento de la consulta meteorologica almacenada | Fecha y hora |

---

# EXPLICACION DE FORMULAS PRINCIPALES

Esta seccion puede usarse como base para el apartado metodologico. La idea es que cada formula no aparezca aislada, sino acompanada por una explicacion clara de que calcula, que significa cada termino y como se interpreta dentro de AgroClima GT.

## Vector de caracteristicas del modelo

```latex
\mathbf{x}_i =
\left[
T,\; R,\; H,\; \text{pH},\; \theta_1,\; L,\; G,\; \theta_2,\; \theta_3,\;
T_s,\; T_{max},\; T_{min},\; v_w,\; z,\; R_{raw},\; G_{raw},\; B_{raw}
\right]
```

Esta formula representa el conjunto de variables que recibe el modelo para una observacion `i`. El vector `mathbf{x}_i` agrupa variables climaticas, edaficas, geograficas y de sensores. En el proyecto se utiliza para estimar `yield_pct`, es decir, el porcentaje esperado de rendimiento agricola.

Cada termino significa lo siguiente: `T` es temperatura media; `R` es precipitacion; `H` es humedad relativa; `pH` representa acidez o alcalinidad del suelo; `theta_1`, `theta_2` y `theta_3` son humedades del suelo por profundidad; `L` es luminosidad; `G` es indice de verdor; `T_s` es temperatura del suelo; `T_max` y `T_min` son temperatura maxima y minima; `v_w` es velocidad del viento; `z` es altitud; y `R_raw`, `G_raw`, `B_raw` son canales de color capturados o simulados para calcular verdor.

## Indice de verdor

```latex
G = \frac{G_{raw}}{R_{raw} + G_{raw} + B_{raw}} \times 100
```

La formula calcula un porcentaje de verdor usando los canales RGB. El numerador `G_raw` corresponde al canal verde, mientras que el denominador suma los canales rojo, verde y azul. Si el resultado es alto, la lectura tiene mayor proporcion de verde, lo que puede asociarse con vegetacion mas activa o saludable. En la tesis debe explicarse como indicador auxiliar, no como sustituto de una medicion agronomica de laboratorio.

## Valores derivados para sensores o variables no disponibles

```latex
\theta_2 = \theta_1 + 0.03
\qquad
\theta_3 = \theta_1 + 0.05
\qquad
T_s = T - 3.0
\qquad
T_{max} = T + 8.0
\qquad
T_{min} = T - 6.0
```

Estas ecuaciones se usan cuando no existe lectura directa de todas las variables. `theta_1` es humedad superficial del suelo; `theta_2` y `theta_3` son aproximaciones para capas mas profundas. `T_s` aproxima temperatura del suelo a partir de la temperatura del aire `T`. `T_max` y `T_min` aproximan extremos diarios. Debe redactarse como una estrategia de imputacion o aproximacion tecnica del prototipo, no como medicion fisica validada en campo.

## Funcion objetivo de XGBoost

```latex
\mathcal{L}(\theta) =
\sum_{i=1}^{n} \ell(y_i,\hat{y}_i) +
\sum_{k=1}^{K} \Omega(f_k)
```

Esta es la funcion que XGBoost intenta minimizar durante el entrenamiento. La primera suma mide el error entre el valor real `y_i` y el valor predicho `hat{y}_i` para las `n` observaciones. La segunda suma agrega una penalizacion de complejidad para los `K` arboles del modelo.

En terminos de la tesis, esta formula indica que el modelo no solo busca predecir bien el rendimiento, sino tambien evitar que los arboles sean innecesariamente complejos. Por eso XGBoost ayuda a controlar sobreajuste cuando se trabaja con muchos registros climaticos y agronomicos.

## Regularizacion de cada arbol

```latex
\Omega(f_k) = \gamma T + \frac{1}{2}\lambda \sum_{j=1}^{T} w_j^2
```

Esta expresion penaliza la complejidad del arbol `f_k`. En esta formula, `T` representa el numero de hojas del arbol, no temperatura. `gamma` penaliza agregar mas hojas y `lambda` aplica regularizacion L2 sobre los pesos `w_j`. El termino `w_j` es el valor asignado a la hoja `j`.

La interpretacion es que un arbol con demasiadas hojas o pesos muy grandes puede ajustarse demasiado al conjunto de entrenamiento. La regularizacion reduce ese riesgo y favorece modelos mas estables.

## Prediccion por ensamble de arboles

```latex
\hat{y}_i = \sum_{k=1}^{K} f_k(\mathbf{x}_i),
\qquad f_k \in \mathcal{F}
```

La prediccion final `hat{y}_i` se obtiene sumando la contribucion de todos los arboles `f_k`. Cada arbol recibe el vector de caracteristicas `mathbf{x}_i` y aporta una parte de la estimacion. `mathcal{F}` representa el espacio de arboles de regresion.

En AgroClima GT, el resultado de esta suma se interpreta como el rendimiento esperado normalizado (`yield_pct`). Por eso se presenta como un problema de regresion y no de clasificacion.

## Actualizacion iterativa por gradiente

```latex
\tilde{\mathcal{L}}^{(t)} =
\sum_{i=1}^{n}
\left[
g_i f_t(\mathbf{x}_i) +
\frac{1}{2} h_i f_t^2(\mathbf{x}_i)
\right]
+ \Omega(f_t)
```

Esta formula resume como XGBoost agrega un nuevo arbol en cada iteracion `t`. `g_i` representa el gradiente de primer orden de la funcion de perdida y `h_i` representa el gradiente de segundo orden o Hessiano. El nuevo arbol `f_t` intenta corregir los errores que dejaron los arboles anteriores.

La explicacion sencilla para la tesis es que el modelo aprende de forma secuencial: cada arbol nuevo se entrena para mejorar la prediccion anterior, pero manteniendo una penalizacion de complejidad mediante `Omega(f_t)`.

## Factor de calibracion FAOSTAT

```latex
f_{FAO}(c,a) =
\frac{\hat{R}(c,a)}{R_{ref}(c)}
```

Esta formula calcula un factor de calibracion para cada cultivo `c` y anio `a`. `hat{R}(c,a)` es el rendimiento reportado por FAOSTAT en kg/ha, mientras que `R_ref(c)` es el rendimiento historico de referencia para el mismo cultivo.

El objetivo es que `yield_pct` no sea un porcentaje completamente sintetico, sino que quede anclado a estadisticas agricolas reales. Si el factor se acerca a 1, el rendimiento reportado se aproxima al rendimiento de referencia; si es menor, indica un desempeno relativo inferior.

## Ajuste del rendimiento porcentual

```latex
\hat{y}_{adj} =
\text{clip}
\left(
\hat{y}_{base} \times f_{FAO}(c,a),
0,
100
\right)
```

Esta formula ajusta la prediccion base `hat{y}_{base}` usando el factor FAOSTAT. La funcion `clip` limita el resultado entre 0 y 100 para mantenerlo dentro de la escala definida para `yield_pct`.

En la tesis puede explicarse asi: primero se calcula una prediccion base del rendimiento; despues se calibra con informacion historica real por cultivo y anio; finalmente, se restringe el resultado a una escala porcentual valida.

## Promedio FAOSTAT para anios sin dato

```latex
\bar{f}(c) =
\frac{1}{|A_c|}
\sum_{a \in A_c} f_{FAO}(c,a)
```

Cuando un cultivo no tiene dato FAOSTAT para un anio especifico, se usa el promedio historico del factor de calibracion del cultivo. `A_c` es el conjunto de anios disponibles para el cultivo `c`, y `|A_c|` es la cantidad de anios dentro de ese conjunto.

Esta formula permite mantener cobertura en el dataset sin descartar registros por falta de una observacion anual puntual. En el documento debe aclararse que es una aproximacion metodologica.

## Intervalo de prediccion

```latex
\mathcal{P} =
\left\{
f_{k^*}(\mathbf{x})
\;|\;
k^* =
\left\lfloor \frac{K}{10} \right\rfloor,
\left\lfloor \frac{2K}{10} \right\rfloor,
\ldots,
K
\right\}
```

```latex
\sigma = \text{std}(\mathcal{P})
\qquad
m = 1.96\sigma
```

```latex
\hat{y}_{low} =
\text{clip}(\hat{y} - m, 0, 100)
\qquad
\hat{y}_{high} =
\text{clip}(\hat{y} + m, 0, 100)
```

Estas ecuaciones estiman un rango alrededor de la prediccion. `mathcal{P}` contiene predicciones parciales calculadas con diferentes cortes del ensamble. `sigma` mide la dispersion de esas predicciones y `m` representa el margen usado para construir el intervalo. `hat{y}_{low}` y `hat{y}_{high}` son los limites inferior y superior.

La interpretacion es que, ademas de entregar un valor puntual de rendimiento esperado, el sistema puede mostrar un rango de incertidumbre. Si el intervalo es amplio, la prediccion debe interpretarse con mayor cautela.

## Explicabilidad con SHAP

```latex
\hat{y} = \phi_0 + \sum_{j=1}^{p} \phi_j
```

Esta formula indica que la prediccion `hat{y}` puede descomponerse en un valor base `phi_0` mas la suma de contribuciones `phi_j` de cada variable. Si `phi_j` es positivo, la variable empuja la prediccion hacia arriba; si es negativo, la reduce.

```latex
\phi_j =
\sum_{S \subseteq \mathcal{F} \setminus \{j\}}
\frac{|S|!(p-|S|-1)!}{p!}
\left[
f(S \cup \{j\}) - f(S)
\right]
```

Esta segunda formula muestra el calculo teorico de la contribucion SHAP para una caracteristica `j`. `S` representa subconjuntos de caracteristicas, `p` es el numero total de variables y la diferencia `f(S union {j}) - f(S)` mide cuanto cambia la prediccion al incluir la variable `j`. En la redaccion se puede explicar que TreeSHAP permite hacer este calculo eficientemente para modelos basados en arboles.

## Riesgo agroclimatico por reglas

```latex
score =
\text{clip}
\left(
s_R + s_T + s_H + s_{pH} + c_f,
0,
100
\right)
```

El puntaje `score` combina componentes de riesgo asociados a precipitacion (`s_R`), temperatura (`s_T`), humedad (`s_H`), pH (`s_pH`) y sensibilidad del cultivo (`c_f`). La funcion `clip` limita el resultado entre 0 y 100.

Esta formula se usa para explicar que el riesgo no depende solo del modelo de aprendizaje automatico. Tambien incorpora reglas agronomicas simples para detectar condiciones criticas, como exceso de lluvia, riesgo de helada, humedad alta o pH fuera del rango adecuado.

## Clasificacion del riesgo

```latex
\text{riesgo} =
\begin{cases}
\text{alto} & \text{si score} \geq 55 \\
\text{bajo} & \text{si score} \leq 18 \\
\text{medio} & \text{en otro caso}
\end{cases}
```

Esta formula convierte el puntaje numerico de riesgo en una categoria comprensible para el usuario. Si el puntaje es alto, el sistema debe generar una interpretacion mas preventiva. Si es bajo, las condiciones se consideran relativamente favorables. Los valores intermedios se clasifican como riesgo medio.

## Sistema combinado de dos capas

```latex
score_{final} =
\begin{cases}
\max(score_{ML}, score_{reglas}) & \text{si existen alertas criticas} \\
score_{ML} & \text{en otro caso}
\end{cases}
```

Esta regla evita que el sistema subestime el riesgo cuando hay condiciones extremas. `score_ML` proviene del modelo predictivo y `score_reglas` proviene de reglas agronomicas o umbrales. Si existen alertas criticas, se conserva el valor mas alto entre ambos.

En la tesis debe presentarse como una decision de seguridad: aunque el modelo estime buen rendimiento, una lectura extrema de sensores o clima puede elevar el riesgo final.

## Desviacion porcentual para alertas

```latex
\Delta_v =
\begin{cases}
\frac{v_{min} - x}{v_{min}} \times 100 & \text{si } x < v_{min} \\
\frac{x - v_{max}}{v_{max}} \times 100 & \text{si } x > v_{max} \\
0 & \text{si } v_{min} \leq x \leq v_{max}
\end{cases}
```

Esta formula mide cuanto se aleja una variable `v` de su rango optimo. `x` es el valor observado, `v_min` es el limite inferior y `v_max` el limite superior. Si `x` esta dentro del rango, la desviacion es cero. Si esta por debajo o por encima, se calcula el porcentaje de separacion respecto al limite correspondiente.

La desviacion permite clasificar alertas como leves, moderadas o severas. En el documento conviene asociarla con recomendaciones agronomicas, por ejemplo riego, drenaje, sombra, monitoreo de plagas o revision de sensor.

## Isolation Forest para deteccion de anomalias

```latex
s(\mathbf{x}, n) =
2^{-\frac{E[h(\mathbf{x})]}{c(n)}}
```

Esta formula expresa el puntaje de anomalia de Isolation Forest. `h(mathbf{x})` es la longitud del camino necesario para aislar una observacion y `E[h(mathbf{x})]` es su valor esperado. `c(n)` normaliza el resultado segun el numero de muestras `n`.

Una observacion anomala suele aislarse con menos particiones, por lo que tiene un comportamiento distinto al conjunto de entrenamiento. En AgroClima GT se usa para detectar entradas climaticas o de sensores que se alejan del patron esperado.

## Puntaje normalizado de anomalia

```latex
z_a =
\frac{d(\mathbf{x}) - \mu_d}{\sigma_d}
```

```latex
score_{anomalia} =
\text{clip}
\left(
100 - (z_a + 2) \times 25,
0,
100
\right)
```

`d(mathbf{x})` es la funcion de decision del Isolation Forest. `mu_d` y `sigma_d` son la media y desviacion estandar de esa funcion. El valor `z_a` expresa que tan alejada esta una observacion respecto al comportamiento esperado. Luego se transforma a una escala de 0 a 100 para facilitar su interpretacion en la interfaz.

## Monitoreo de data drift

```latex
z_j =
\left|
\frac{x_j - \mu_j}{\sigma_j}
\right|
```

```latex
sim_j =
\text{clip}
\left(
100 - 22z_j,
0,
100
\right)
```

```latex
\bar{sim} =
\frac{1}{p}
\sum_{j=1}^{p} sim_j
```

Estas formulas comparan las entradas actuales contra el perfil de entrenamiento. `x_j` es el valor actual de la caracteristica `j`; `mu_j` y `sigma_j` son la media y desviacion estandar observadas durante el entrenamiento. `z_j` mide la distancia estandarizada, `sim_j` convierte esa distancia en similitud porcentual y `bar{sim}` resume la similitud global.

Si `bar{sim}` baja demasiado, el sistema puede indicar data drift. Esto significa que los datos actuales ya no se parecen suficientemente a los datos con los que se entreno el modelo, por lo que la prediccion debe interpretarse con precaucion o requerir reentrenamiento.

## Metricas de evaluacion del modelo

```latex
MAE =
\frac{1}{n}
\sum_{i=1}^{n}
|y_i - \hat{y}_i|
```

El MAE mide el error absoluto promedio. En esta tesis se interpreta en puntos porcentuales de `yield_pct`. Por ejemplo, un MAE de 5.91 significa que, en promedio, la prediccion se aleja aproximadamente 5.91 puntos porcentuales del valor observado.

```latex
RMSE =
\sqrt{
\frac{1}{n}
\sum_{i=1}^{n}
(y_i - \hat{y}_i)^2
}
```

El RMSE tambien mide error de prediccion, pero penaliza mas los errores grandes porque eleva las diferencias al cuadrado antes de promediarlas. Es util para identificar si el modelo comete errores fuertes en algunos casos.

```latex
R^2 =
1 -
\frac{
\sum_{i=1}^{n}(y_i - \hat{y}_i)^2
}{
\sum_{i=1}^{n}(y_i - \bar{y})^2
}
```

El coeficiente `R^2` mide que proporcion de la variabilidad de `yield_pct` explica el modelo. Un valor mas cercano a 1 indica mejor ajuste. En la comparacion actual del proyecto, XGBoost supera a Random Forest porque presenta mayor `R2` y menores errores `MAE` y `RMSE`.

## Validacion cruzada

```latex
\overline{R^2}_{CV} =
\frac{1}{5}
\sum_{k=1}^{5}
R^2_k
```

Esta formula calcula el promedio del `R2` obtenido en cinco particiones o folds. `R^2_k` es el resultado del fold `k`. La validacion cruzada sirve para evaluar si el desempeno del modelo es estable y no depende solamente de una division especifica entre entrenamiento y prueba.

## Cache de pronostico meteorologico

```latex
\text{usar cache} =
\begin{cases}
\text{si} & \text{si } t_{actual} - t_{consulta} < \Delta t \\
\text{no} & \text{en otro caso}
\end{cases}
```

Esta regla indica cuando reutilizar datos de pronostico ya consultados. `t_actual` es el momento actual, `t_consulta` es el momento en que se obtuvo el dato meteorologico y `Delta t` es la ventana maxima de cache. En el proyecto se usa para reducir consultas repetidas a Open-Meteo y mantener respuestas rapidas en el sistema.

---

# RESUMEN

## Version lista para insertar

La variabilidad climatica representa un desafio para la produccion agricola en Guatemala, especialmente en cultivos sensibles a cambios de temperatura, precipitacion, humedad y condiciones de suelo. Ante esta problematica, se desarrollo AgroClima GT, un prototipo web basado en aprendizaje automatico y visualizacion de datos para identificar escenarios de bajo rendimiento agricola y apoyar la toma de decisiones mediante indicadores, alertas y recomendaciones.

El sistema integra fuentes climaticas, edaficas y agronomicas, incluyendo datos procesados de ERA5-Land, NASA POWER, SoilGrids, Open-Meteo, INSIVUMEH y FAOSTAT. A partir de estas fuentes se construyo un dataset tabular para entrenar y evaluar modelos predictivos. El modelo principal utiliza XGBoost para estimar el porcentaje de rendimiento esperado (`yield_pct`), mientras Random Forest se emplea como referencia comparativa. La evaluacion interna actual muestra que XGBoost obtuvo R2 = 0.6334, MAE = 5.91 y RMSE = 7.68, superando a Random Forest en la comparacion registrada.

La arquitectura del prototipo esta compuesta por un frontend desarrollado con React/Vite, un backend construido con FastAPI, una base de datos PostgreSQL, archivos locales de datos y modelos, y modulos de analisis para prediccion, deteccion de anomalias, monitoreo de data drift y generacion de alertas. La interfaz permite ingresar variables agroclimaticas, consultar pronostico, revisar tendencias del dataset, visualizar riesgo en mapa, exportar informacion en CSV, generar reportes y consultar alertas. Asimismo, el sistema deja implementada la base de software para integrar sensores fisicos mediante Arduino, lectura serial, simulacion y WebSocket. La instalacion fisica, calibracion en campo y comunicacion inalambrica mediante tecnologias como MQTT o LoRaWAN se plantean como una fase posterior de continuidad.

Los resultados demuestran la factibilidad tecnica de integrar datos publicos, aprendizaje automatico, reglas agronomicas y visualizacion web en una herramienta de apoyo a la decision agricola. La validacion realizada corresponde a una etapa tecnica y funcional del prototipo; por tanto, la validacion agronomica con sensores instalados en parcelas reales y eventos etiquetados queda como trabajo futuro.

## Palabras clave sugeridas

Aprendizaje automatico; agricultura; XGBoost; riesgo agroclimatico; rendimiento agricola; Guatemala; sensores; FastAPI; React; alertas tempranas.

---

# OBJETIVOS

## Objetivo general

Desarrollar un prototipo tecnologico basado en aprendizaje automatico y visualizacion web para identificar escenarios de bajo rendimiento agricola en Guatemala, mediante el analisis de registros climaticos, variables edaficas, datos agronomicos y metricas locales obtenidas por entrada manual, consulta externa, simulacion o integracion posterior de sensores.

## Objetivos especificos

1. Caracterizar variables climaticas, edaficas y agronomicas asociadas al rendimiento agricola en Guatemala mediante la integracion de fuentes historicas y recientes como ERA5-Land, NASA POWER, SoilGrids, Open-Meteo, INSIVUMEH y FAOSTAT.

2. Construir y procesar un dataset tabular que permita entrenar y evaluar modelos predictivos de rendimiento agricola, incorporando variables como municipio/departamento, cultivo, mes, temperatura, precipitacion, humedad, pH del suelo, humedad de suelo, luminosidad, indice de verdor, viento, altitud y rendimiento estimado.

3. Entrenar y comparar modelos de aprendizaje automatico para estimar el porcentaje de rendimiento agricola esperado (`yield_pct`), utilizando metricas de regresion como R2, MAE y RMSE para seleccionar el modelo principal.

4. Implementar un motor de analisis y alertas que combine prediccion de rendimiento, deteccion de anomalias, monitoreo de data drift y reglas agronomicas por cultivo para identificar condiciones de riesgo y generar recomendaciones.

5. Desarrollar una interfaz web de apoyo a la toma de decisiones que permita ingresar datos, visualizar predicciones, consultar pronosticos, revisar tendencias, analizar mapas de riesgo, exportar CSV, generar reportes y consultar alertas.

6. Dejar implementada la base de software para la integracion posterior de sensores fisicos mediante Arduino, simulacion de lecturas y transmision en tiempo real por WebSocket, considerando la validacion fisica en campo como una fase futura del proyecto.

## Nota para defensa

Si tu terna compara estos objetivos con el protocolo original, explica que el objetivo de sensores no se elimino: se delimito como infraestructura de software ya preparada y validacion fisica posterior. Esa redaccion evita decir que algo esta probado en campo cuando todavia no lo esta.

---

# INTRODUCCION

## Version lista para insertar

La agricultura guatemalteca depende de condiciones climaticas que pueden variar significativamente entre regiones, temporadas y cultivos. La precipitacion irregular, los cambios de temperatura, la humedad ambiental, las propiedades del suelo y la disponibilidad de agua influyen directamente en el desarrollo de los cultivos y en el rendimiento esperado. En este contexto, los productores y tecnicos agricolas requieren herramientas que permitan interpretar informacion climatica y agronomica de forma oportuna, comprensible y orientada a la toma de decisiones.

El avance de las tecnologias de informacion, los servicios climaticos abiertos, los sistemas de informacion geografica, los sensores de bajo costo y los modelos de aprendizaje automatico ha permitido desarrollar soluciones de apoyo a la decision en agricultura. Estas soluciones pueden integrar datos historicos, pronosticos, mediciones locales y modelos predictivos para anticipar escenarios de riesgo. Sin embargo, para que estas herramientas sean utiles en un contexto academico y operativo, deben presentar resultados de forma clara, documentar sus limitaciones y diferenciar entre predicciones tecnicas, validaciones funcionales y validaciones agronomicas en campo.

El presente trabajo desarrolla AgroClima GT, un prototipo web orientado a la identificacion de escenarios de bajo rendimiento agricola en Guatemala. El sistema utiliza datos climaticos, edaficos y agronomicos procesados desde fuentes como ERA5-Land, NASA POWER, SoilGrids, Open-Meteo, INSIVUMEH y FAOSTAT. Con estos datos se construye un dataset para entrenar modelos de aprendizaje automatico, siendo XGBoost el modelo principal para estimar el porcentaje de rendimiento agricola esperado (`yield_pct`). Ademas, el prototipo incorpora comparacion con Random Forest, deteccion de anomalias mediante Isolation Forest, monitoreo de data drift, reglas agronomicas por cultivo y visualizaciones interactivas.

La plataforma fue implementada mediante una arquitectura compuesta por frontend React/Vite, backend FastAPI, base de datos PostgreSQL, archivos locales de datos y modelos, y modulos de comunicacion para lecturas Arduino por serial o simulacion. La interfaz permite al usuario ingresar variables agroclimaticas, obtener predicciones, consultar pronostico, revisar registros del dataset, filtrar informacion, exportar datos, generar reportes, observar mapas de riesgo y visualizar alertas. De esta forma, el prototipo no se limita al calculo del modelo, sino que transforma la informacion tecnica en elementos utiles para la interpretacion y el seguimiento agricola.

Es importante delimitar el alcance del proyecto. La version actual valida la factibilidad tecnica y funcional del sistema de software. El componente de sensores fisicos forma parte de la continuidad del proyecto: el sistema ya incluye soporte para lectura Arduino, simulacion y transmision WebSocket, pero la instalacion del nodo sensor, la calibracion de hardware, la comunicacion inalambrica y la validacion en parcelas reales quedan como etapas posteriores. Esta delimitacion permite conservar la vision planteada en el protocolo, sin atribuir al prototipo resultados de campo que todavia no han sido ejecutados.

El documento se organiza en capitulos que describen el contexto agricola y climatico, el fundamento teorico de aprendizaje automatico y sistemas de alerta, la metodologia de procesamiento de datos, el diseno e implementacion del prototipo, y el analisis de resultados obtenidos. Finalmente, se presentan conclusiones y recomendaciones orientadas a fortalecer la validacion futura del sistema, especialmente mediante pruebas con sensores fisicos, datos etiquetados de eventos reales y evaluacion en condiciones agricolas de campo.

## Problema de investigacion sugerido

Los productores agricolas en Guatemala enfrentan variabilidad climatica y condiciones edaficas que pueden afectar el rendimiento de los cultivos. Aunque existen fuentes climaticas y datos publicos, estos no siempre se integran en herramientas practicas que permitan estimar riesgo, visualizar patrones y generar recomendaciones accionables. Por ello, surge la necesidad de desarrollar un prototipo que combine datos agroclimaticos, aprendizaje automatico y visualizacion web para apoyar la identificacion temprana de escenarios de bajo rendimiento agricola.

## Pregunta de investigacion sugerida

¿Como puede un prototipo basado en datos agroclimaticos, aprendizaje automatico y visualizacion web apoyar la identificacion temprana de escenarios de bajo rendimiento agricola en Guatemala?

## Justificacion breve sugerida

La propuesta es relevante porque integra fuentes climaticas y agronomicas disponibles con modelos predictivos y una interfaz visual orientada a la toma de decisiones. Su aporte principal es demostrar la viabilidad tecnica de una plataforma que estima rendimiento, identifica riesgo y presenta recomendaciones de manera accesible. Ademas, el prototipo deja preparada la base para integrar sensores fisicos en una fase posterior, lo que permitiria avanzar hacia monitoreo local y validacion en campo.

---

# REVISION Y GUIA PARA CAPITULOS 1 Y 2

Esta seccion cubre lo que aparece antes de `3. METODOLOGIA Y PROCESAMIENTO DE DATOS` en `PLANTILLA_APA 7_FINAL ENERO 2023.pdf`. El PDF organiza esa parte asi:

- `1. MARCO CONTEXTUAL: AGRICULTURA Y CLIMA EN GUATEMALA`, con incisos `1.1` a `1.7`.
- `2. MARCO TEORICO: MACHINE LEARNING Y DETECCION DE ANOMALIA`, con incisos `2.1` a `2.9`.

La conclusion principal de la revision es esta: el capitulo 1 puede mantenerse como contexto, pero debe ajustarse para no limitar toda la tesis al Altiplano Occidental si la aplicacion ya cubre mas departamentos. El capitulo 2 debe separar claramente las tecnologias implementadas de las tecnologias que quedan como antecedentes o trabajo futuro. XGBoost, Random Forest, Isolation Forest, reglas agronomicas, SHAP, FastAPI, React, Leaflet, Chart.js, PostgreSQL, Open-Meteo y WebSocket si corresponden al proyecto. LSTM, STL, LoRaWAN, MQTT y edge/fog computing pueden mantenerse como marco teorico o continuidad posterior, pero no deben redactarse como componentes ya implementados.

## Tabla de ajuste rapido para capitulos 1 y 2

| Seccion del PDF | Estado frente al proyecto | Ajuste recomendado |
|---|---|---|
| 1.1 Agricultura nacional | Pertinente | Mantener como justificacion macroeconomica y social. Actualizar cifras solo si tienes fuente institucional verificable. |
| 1.2 Ocho regiones agroclimaticas | Pertinente | Mantener, pero conectar con que el sistema trabaja por departamentos/municipios y no solo con una region. |
| 1.3 Heladas y anomalias termicas | Pertinente como problema | Ampliar a riesgo agroclimatico general: sequia, exceso de lluvia, humedad, temperatura, pH y humedad del suelo. |
| 1.4 Cultivos estrategicos | Pertinente | Mantener maiz, frijol y cafe como ejemplos principales; aclarar que el dataset/prototipo puede manejar mas cultivos. |
| 1.5 INSIVUMEH y MAGA | Pertinente | Mantener como fuentes e instituciones de referencia, sin decir que el sistema reemplaza alertas oficiales. |
| 1.6 Fenologia | Pertinente parcial | Mantener como base agronomica; en el proyecto actual las fases fenologicas son apoyo conceptual, no modulo completo validado por cultivo. |
| 1.7 Altiplano Occidental | Pertinente si es caso de estudio | Redactar como area prioritaria o caso demostrativo, porque la aplicacion incluye Guatemala de forma mas amplia. |
| 2.1 Machine Learning | Pertinente | Orientar a aprendizaje automatico tabular aplicado a rendimiento agricola y riesgo. |
| 2.2 Supervisado vs no supervisado | Pertinente | XGBoost = supervisado/regresion; Isolation Forest = no supervisado/anomalias. |
| 2.3 Series temporales, LSTM e hibridos | Requiere correccion | Mantener LSTM e hibridos como antecedentes. El sistema implementado no usa LSTM ni transformers. |
| 2.4 Deteccion de anomalias | Pertinente | Centrar en Isolation Forest y reglas por umbral. Modified Z-Score solo como antecedente si no esta implementado. |
| 2.5 Sistemas de alerta temprana | Pertinente | Presentar AgroClima GT como apoyo a decision, no como alerta oficial. |
| 2.6 STL | No implementado | Mantener solo como antecedente teorico. En metodologia usar Isolation Forest, data drift y reglas. |
| 2.7 IoT, MQTT, LoRaWAN, edge | Futuro/antecedente | Redactar como arquitectura futura. El prototipo actual usa Arduino serial/simulacion/WebSocket. |
| 2.8 DSS y visualizacion | Muy pertinente | Fortalecer con dashboard, mapas, graficas, reportes, CSV y panel admin. |
| 2.9 Etica y privacidad | Pertinente | Mantener, pero adaptar: datos anonimizados, uso academico, consentimiento futuro en parcelas, no venta a terceros. |

---

# 1. MARCO CONTEXTUAL: AGRICULTURA Y CLIMA EN GUATEMALA

## 1.1. Importancia del sector agricola a nivel nacional

### Contenido sugerido

Guatemala depende de forma significativa de la actividad agricola, tanto por su aporte economico como por su relacion directa con empleo rural, seguridad alimentaria y generacion de ingresos familiares. En este contexto, la variabilidad climatica representa un riesgo para productores que dependen de lluvia, temperatura, humedad y condiciones de suelo. Por ello, las herramientas digitales de analisis agroclimatico pueden apoyar la toma de decisiones al transformar datos dispersos en indicadores utiles sobre rendimiento, riesgo y recomendaciones.

Para conectar este inciso con AgroClima GT, agrega un parrafo al cierre: el prototipo no busca sustituir la asistencia tecnica ni los sistemas oficiales, sino demostrar que es viable integrar fuentes climaticas, edaficas y agronomicas en una plataforma web que estime rendimiento y alerte sobre condiciones de riesgo.

### Referencias que puedes usar

- Banco de Guatemala o Banco Mundial para contexto economico agricola.
- FAO/FAOSTAT para rendimiento agricola y cultivos.
- SEGEPLAN para cambio climatico y vulnerabilidad en Guatemala.
- MAGA para produccion agricola, seguridad alimentaria y region agroclimatica.

### Imagen o tabla recomendada

- Tabla breve con aporte del sector agricola, empleo rural y cultivos estrategicos.
- Grafica simple de importancia del agro en Guatemala si tienes fuente institucional.

### Ajuste importante

Evita cifras sin fuente o proyecciones que no puedas defender. Si una cifra del PDF proviene de 2025 o 2026, verifica que la fuente exista y que puedas citarla formalmente. Si no, redacta de forma cualitativa o usa un dato historico institucional verificable.

## 1.2. Las ocho regiones agroclimaticas de Guatemala

### Contenido sugerido

La clasificacion agroclimatica del MAGA permite comprender que Guatemala no presenta condiciones uniformes de produccion. La altitud, el relieve, la precipitacion, la temperatura y la humedad cambian entre regiones, lo que afecta calendarios de siembra, seleccion de cultivos y riesgo de eventos extremos. Esta variabilidad justifica que un sistema como AgroClima GT organice la informacion por ubicacion geografica, cultivo y variables ambientales.

En la tesis conviene mantener la tabla de regiones agroclimaticas, pero vincularla con la aplicacion: el mapa de riesgo y el dataset permiten visualizar diferencias por departamento o municipio, mientras el modelo estima `yield_pct` usando variables climaticas y edaficas.

### Referencias que puedes usar

- MAGA para regiones agroclimaticas y calendarios agricolas.
- INSIVUMEH para patrones climaticos.
- SEGEPLAN para variabilidad climatica y vulnerabilidad territorial.

### Imagen o tabla recomendada

- Mapa de Guatemala por regiones agroclimaticas.
- Captura del mapa coropletico o mapa de riesgo de AgroClima GT.
- Tabla: region, departamentos, riesgos principales y cultivos sensibles.

## 1.3. Anomalias termicas y heladas agricolas en Guatemala

### Contenido sugerido

Las anomalias termicas son desviaciones respecto a las condiciones esperadas para una zona y epoca del anio. En regiones de altura, las heladas pueden afectar tejidos vegetales y reducir rendimiento; en regiones calidas, el exceso de temperatura puede aumentar estres hidrico, afectar floracion y reducir productividad. Aunque el PDF se enfoca bastante en heladas, el proyecto implementado debe presentarse con un alcance mas amplio: temperatura, lluvia, humedad, pH, humedad del suelo, luminosidad, verdor y viento.

Puedes redactarlo asi: AgroClima GT toma el problema de las anomalias agroclimaticas como base para estimar riesgo. El sistema no se limita a detectar heladas; tambien evalua variables fuera de rango, calcula puntajes de riesgo, genera alertas y permite observar tendencias del rendimiento estimado.

### Referencias que puedes usar

- SEGEPLAN para cambio climatico y amenaza por heladas.
- MAGA/CIEA para perspectivas agroclimaticas.
- INSIVUMEH para datos climaticos y pronosticos nacionales.

### Imagen o tabla recomendada

- Tabla de eventos de riesgo: helada, sequia, exceso de lluvia, humedad alta, pH fuera de rango.
- Captura de alertas de AgroClima GT.
- Captura de grafica de tendencias de `yield_pct`.

## 1.4. Vulnerabilidad de cultivos estrategicos: maiz, frijol y cafe

### Contenido sugerido

Maiz, frijol y cafe son cultivos estrategicos para Guatemala por su peso alimentario, economico y social. Cada cultivo tiene sensibilidad distinta frente a temperatura, precipitacion, humedad y condiciones del suelo. El maiz puede verse afectado por estres termico durante floracion y polinizacion; el frijol es sensible al deficit hidrico y a temperaturas fuera de rango durante floracion y llenado de vainas; el cafe depende de condiciones termicas y de lluvia relativamente estables.

Conecta este inciso con el proyecto explicando que AgroClima GT usa reglas por cultivo y variables agroclimaticas para emitir recomendaciones. Si el dataset incluye mas cultivos, maiz, frijol y cafe pueden quedar como ejemplos principales por importancia nacional, no como los unicos cultivos soportados.

### Referencias que puedes usar

- ICTA para maiz y frijol en Guatemala.
- FAO/FAOSTAT para rendimiento agricola.
- MAGA para cultivos estrategicos y seguridad alimentaria.
- Literatura agronomica sobre cafe en Centroamerica.

### Imagen o tabla recomendada

- Tabla por cultivo: rango de temperatura, lluvia, humedad, pH y fase sensible.
- Captura de recomendaciones por cultivo.
- Captura del formulario de prediccion con cultivo seleccionado.

## 1.5. Rol del INSIVUMEH y MAGA en la vigilancia climatica agricola

### Contenido sugerido

INSIVUMEH y MAGA cumplen funciones complementarias en la vigilancia agroclimatica. INSIVUMEH aporta observacion meteorologica, pronosticos y analisis climaticos; MAGA traduce esa informacion hacia recomendaciones productivas, perspectivas agroclimaticas y apoyo tecnico. Esta coordinacion institucional es el marco de referencia para cualquier herramienta academica de apoyo agroclimatico.

AgroClima GT debe presentarse como una herramienta complementaria y academica. No reemplaza al INSIVUMEH ni al MAGA, ni emite alertas oficiales. Su aporte es integrar datos abiertos, fuentes procesadas y modelos de aprendizaje automatico en una interfaz que facilite analisis, visualizacion y reportes.

### Referencias que puedes usar

- INSIVUMEH para productos climaticos y datos meteorologicos.
- MAGA/CIEA para perspectivas agroclimaticas y monitoreo agricola.
- UNEP o marcos de alerta temprana para fundamento general.

### Imagen o tabla recomendada

- Diagrama: INSIVUMEH/MAGA/fuentes abiertas -> procesamiento -> AgroClima GT -> usuario.
- Tabla de fuentes: INSIVUMEH, ERA5-Land, NASA POWER, SoilGrids, Open-Meteo, FAOSTAT.

## 1.6. Fenologia y fases criticas de desarrollo ante estres termico

### Contenido sugerido

La fenologia permite explicar por que una misma condicion climatica puede tener impactos diferentes segun la etapa del cultivo. Una temperatura baja o una sequia moderada no afecta igual durante germinacion, floracion, llenado de fruto o maduracion. Este fundamento justifica que los sistemas de alerta consideren cultivo, variable y rango optimo.

En el proyecto actual, la fenologia debe tratarse como base conceptual y como mejora futura si no existe un modulo completo que determine automaticamente la fase fenologica de cada cultivo. Puedes decir que el prototipo incorpora rangos optimos por cultivo y recomendaciones, pero que la incorporacion dinamica de fases fenologicas queda como ampliacion posterior.

### Referencias que puedes usar

- ICTA, MAGA o manuales agronomicos para fases de maiz/frijol.
- Literatura tecnica de cafe para fases productivas.
- FAO para relacion clima-cultivo.

### Imagen o tabla recomendada

- Tabla: cultivo, fase critica, variable de riesgo, posible efecto.
- Diagrama de ciclo fenologico simplificado para maiz/frijol/cafe.

## 1.7. Contexto agroclimatico del Altiplano Occidental como area de estudio

### Contenido sugerido

El Altiplano Occidental puede mantenerse como caso prioritario por su exposicion a heladas, variabilidad topografica, poblacion rural agricola y presencia de cultivos sensibles. Sin embargo, la aplicacion implementada no se limita unicamente a esa region, ya que maneja datos por departamentos, municipios y multiples cultivos. Por eso, la redaccion debe distinguir entre area prioritaria de motivacion y cobertura tecnica del prototipo.

Redaccion recomendada: El Altiplano Occidental se adopta como escenario de referencia por su vulnerabilidad agroclimatica, pero el diseno de AgroClima GT permite escalar el analisis a otros departamentos de Guatemala mediante fuentes climaticas, edaficas y agronomicas integradas en el dataset.

### Referencias que puedes usar

- SEGEPLAN para vulnerabilidad climatica.
- MAGA/CIEA para riesgos por heladas.
- MAGA para regiones agroclimaticas.

### Imagen o tabla recomendada

- Mapa de Guatemala resaltando Altiplano Occidental.
- Captura del mapa de riesgo del sistema con departamentos.
- Tabla: riesgo del Altiplano vs cobertura general del prototipo.

---

# 2. MARCO TEORICO: MACHINE LEARNING Y DETECCION DE ANOMALIAS

## 2.1. Fundamentos de Machine Learning para agricultura

### Contenido sugerido

El aprendizaje automatico permite identificar patrones en conjuntos de datos climaticos, edaficos y productivos. En agricultura, estos patrones pueden apoyar estimaciones de rendimiento, deteccion de condiciones anomalas, clasificacion de riesgo y generacion de recomendaciones. AgroClima GT aplica esta idea mediante un modelo XGBoost para estimar `yield_pct`, comparacion con Random Forest, deteccion de anomalias con Isolation Forest y reglas agronomicas para alertas.

El marco teorico debe enfatizar aprendizaje automatico tabular, porque el proyecto trabaja con variables estructuradas en CSV/JSON/NetCDF procesado. Evita orientar todo el fundamento a imagenes satelitales, redes neuronales profundas o series minuto a minuto si no son el nucleo implementado.

### Referencias que puedes usar

- Chen y Guestrin (2016) para XGBoost.
- scikit-learn para modelos y metricas.
- FAO, ERA5-Land y fuentes agroclimaticas para contexto de datos.

### Imagen o tabla recomendada

- Esquema: datos agroclimaticos -> features -> modelo -> `yield_pct`/riesgo.
- Tabla de modelos usados: XGBoost, Random Forest, Isolation Forest.

## 2.2. Aprendizaje supervisado vs no supervisado

### Contenido sugerido

El aprendizaje supervisado utiliza datos con una variable objetivo conocida. En AgroClima GT, este enfoque se aplica a la prediccion de rendimiento mediante XGBoost y Random Forest, donde la salida esperada es `yield_pct`. El aprendizaje no supervisado busca patrones sin etiquetas previas; en el prototipo se usa con Isolation Forest para identificar entradas atipicas o lecturas que se alejan del comportamiento esperado.

Esta division es clave para defender el sistema: la prediccion de rendimiento se evalua con metricas de regresion como `R2`, `MAE` y `RMSE`, mientras que las anomalias se presentan como deteccion tecnica no supervisada, no como clasificacion validada con eventos reales etiquetados.

### Referencias que puedes usar

- scikit-learn para definicion practica de modelos supervisados/no supervisados.
- Liu, Ting y Zhou (2008) para Isolation Forest.
- Chen y Guestrin (2016) para XGBoost.

### Imagen o tabla recomendada

| Enfoque | Uso en AgroClima GT | Salida |
|---|---|---|
| Supervisado | XGBoost/Random Forest | `yield_pct` |
| No supervisado | Isolation Forest | normal/sospechoso/anomalia |
| Reglas | Umbrales agronomicos | alerta/recomendacion |

## 2.3. Algoritmos para analisis agroclimatico

### Ajuste principal

El PDF incluye LSTM, XGBoost y modelos hibridos. Para que coincida con el proyecto, deja LSTM y modelos hibridos como antecedentes de la literatura, y centra la implementacion en XGBoost. No digas que AgroClima GT entrena LSTM, transformers o autoencoders.

## 2.3.1. Redes LSTM

### Contenido sugerido

Las redes LSTM son utiles para series temporales porque pueden modelar dependencias entre observaciones pasadas y futuras. En agricultura se han usado para prediccion climatica, humedad, temperatura y eventos extremos. Sin embargo, en AgroClima GT no constituyen el modelo implementado. Deben aparecer como antecedente teorico o posible linea futura cuando existan series continuas de sensores fisicos validadas en campo.

### Redaccion corta para evitar contradiccion

Aunque las redes LSTM son pertinentes para series temporales agroclimaticas, el presente prototipo utiliza un enfoque tabular basado en XGBoost debido a la estructura del dataset disponible y a la necesidad de integrar variables climaticas, edaficas, geograficas y de cultivo en registros mensuales o agregados. La aplicacion de LSTM se considera una ampliacion futura cuando se disponga de series continuas etiquetadas provenientes de sensores instalados en campo.

## 2.3.2. Arboles de decision y XGBoost

### Contenido sugerido

XGBoost es el algoritmo central del modelo predictivo. Su ventaja es que maneja relaciones no lineales, variables heterogeneas y grandes cantidades de registros tabulares. En AgroClima GT se usa para estimar `yield_pct` a partir de variables como temperatura, precipitacion, humedad, pH, humedad del suelo, luminosidad, verdor, viento, altitud, cultivo y municipio.

Debes incluir aqui la formula de funcion objetivo de XGBoost o referenciar la seccion `EXPLICACION DE FORMULAS PRINCIPALES`. Tambien conviene mencionar que Random Forest se usa como linea base comparativa y que, segun `model_comparison.json`, XGBoost obtiene mejores metricas internas.

### Referencias que puedes usar

- Chen, T., & Guestrin, C. (2016). XGBoost.
- Documentacion oficial de XGBoost.
- scikit-learn para Random Forest y metricas.

### Imagen o tabla recomendada

- Grafica de barras XGBoost vs Random Forest.
- Tabla de metricas: R2, MAE, RMSE y CV R2.

## 2.3.3. Modelos hibridos para prediccion agroclimatica

### Contenido sugerido

Los modelos hibridos combinan varios enfoques para mejorar prediccion y deteccion de eventos atipicos. En la literatura pueden combinarse redes neuronales, modelos de arboles, autoencoders o tecnicas de anomalias. En AgroClima GT, el enfoque hibrido implementado es mas pragmatico: XGBoost para prediccion de rendimiento, Isolation Forest para anomalias, reglas agronomicas para alertas y visualizaciones para decision.

### Ajuste de redaccion

Si el PDF afirma que hay transformers, autoencoders o LSTM implementados, cambialo por: "estos modelos se consideran referentes teoricos; la version implementada usa XGBoost, Isolation Forest y reglas agronomicas".

## 2.4. Tecnicas de deteccion de anomalias

### Contenido sugerido

La deteccion de anomalias permite identificar valores que se alejan del comportamiento esperado. En un sistema agroclimatico, una anomalia puede ser un evento real, como temperatura extrema, o un problema tecnico, como una lectura de sensor incorrecta. AgroClima GT aborda este problema con Isolation Forest y validacion por rangos.

### Referencias que puedes usar

- Liu, Ting y Zhou (2008) para Isolation Forest.
- scikit-learn IsolationForest para implementacion.

### Imagen o tabla recomendada

- Captura del modulo de alertas.
- Tabla: tipo de anomalia, ejemplo, accion del sistema.

## 2.4.1. Isolation Forest

### Contenido sugerido

Isolation Forest es el metodo de anomalias implementado. Funciona aislando observaciones mediante particiones aleatorias; las observaciones anomalas suelen requerir menos particiones para separarse del resto. En AgroClima GT se usa para analizar entradas de clima/sensores y apoyar la clasificacion `normal`, `sospechoso` o `anomalia`.

Incluye la formula ya agregada en `EXPLICACION DE FORMULAS PRINCIPALES` y explica que el resultado no equivale todavia a una validacion agronomica con eventos reales etiquetados.

## 2.4.2. Z-Score y Modified Z-Score

### Ajuste recomendado

El PDF puede conservar Z-Score como base conceptual, pero no debe presentarlo como nucleo implementado si el backend no lo usa como metodo principal de anomalias. El proyecto si usa distancias tipo z-score para data drift, por lo que puedes relacionarlo con monitoreo de cambio de distribucion y no con clasificacion final de alertas.

### Redaccion sugerida

El Z-Score permite medir cuantas desviaciones estandar se aleja una observacion respecto a una media de referencia. En AgroClima GT este principio se aplica al monitoreo de data drift, comparando entradas actuales contra el perfil estadistico usado durante el entrenamiento. Para deteccion de anomalias operativa, el prototipo utiliza principalmente Isolation Forest y reglas por umbral.

## 2.5. Estado del arte de sistemas de alerta temprana agroclimatica

### Contenido sugerido

Los sistemas de alerta temprana combinan monitoreo, analisis de riesgo, comunicacion y recomendaciones de accion. En agricultura, su valor depende de que la informacion sea oportuna, comprensible y accionable. AgroClima GT toma este principio para presentar alertas, mapas, reportes y recomendaciones; sin embargo, debe definirse como prototipo academico de apoyo a decision, no como alerta oficial.

### Referencias que puedes usar

- UNEP para sistemas de informacion climatica y alerta temprana.
- MAGA/INSIVUMEH para experiencias nacionales.
- Gutiérrez et al. (2022) para sistemas visuales de apoyo a decisiones agricolas.

### Imagen o tabla recomendada

- Flujo: monitoreo -> analisis -> alerta -> recomendacion -> decision.
- Captura de panel de alertas.
- Captura de reporte PDF generado.

## 2.5.1. Sistemas internacionales de referencia

### Contenido sugerido

Puedes mencionar sistemas internacionales como referencia de buenas practicas: integracion de datos climaticos, comunicacion de riesgo, mapas, boletines y acciones anticipatorias. No es necesario afirmar que AgroClima GT tenga el mismo alcance. La comparacion debe servir para justificar elementos del prototipo: mapa, alertas, dashboard, recomendaciones y reportes.

## 2.5.2. Experiencias y referentes aplicables a Guatemala

### Contenido sugerido

Guatemala ya cuenta con instituciones y espacios tecnicos, como INSIVUMEH, MAGA, CIEA y Mesas Tecnicas Agroclimaticas. AgroClima GT puede presentarse como un ejercicio academico que toma inspiracion de ese ecosistema institucional para construir una herramienta de visualizacion y prediccion. Debe quedar claro que no reemplaza esos mecanismos.

## 2.6. Descomposicion de series temporales: tendencia, estacionalidad y residuo

### Ajuste principal

STL puede quedarse como antecedente teorico, pero no como metodologia implementada. El proyecto actual no ejecuta descomposicion STL como nucleo del sistema. La metodologia real usa datasets tabulares, XGBoost, Isolation Forest, reglas por umbral y data drift.

### Redaccion sugerida

La descomposicion de series temporales permite separar tendencia, estacionalidad y residuo, lo cual es util para estudiar eventos extremos en registros continuos. En esta tesis se incluye como antecedente teorico para comprender el analisis de anomalias en datos agroclimaticos; sin embargo, la version implementada de AgroClima GT emplea un enfoque tabular basado en XGBoost para prediccion, Isolation Forest para anomalias y comparacion estadistica para data drift.

### Formula opcional

```latex
y_t = T_t + S_t + R_t
```

Donde `y_t` es la serie observada, `T_t` es tendencia, `S_t` es estacionalidad y `R_t` es residuo. Si la incluyes, aclara que es base teorica, no modulo implementado.

## 2.7. Arquitectura IoT y protocolos de comunicacion para agricultura de precision

### Ajuste principal

Esta es la seccion con mayor riesgo de contradiccion. El PDF habla de MQTT, LoRaWAN, LPWAN y edge computing. Eso puede mantenerse como arquitectura futura de sensores, pero el proyecto actual implementa Arduino por serial, simulacion local y WebSocket hacia el frontend. Como el usuario ya indico que sensores fisicos se implementaran posteriormente, la tesis debe dejar evidencia de continuidad sin afirmar despliegue en campo.

### Redaccion lista para insertar

La arquitectura IoT completa se plantea como una fase de continuidad del proyecto. La version actual de AgroClima GT deja implementada la base de software para recibir lecturas de sensores mediante Arduino, conexion serial, simulacion de datos y transmision en tiempo real por WebSocket hacia el frontend. Tecnologias como MQTT, LoRaWAN y edge computing se consideran alternativas de ampliacion para despliegues en parcelas rurales, especialmente cuando se requiera comunicacion inalambrica de largo alcance, bajo consumo energetico y procesamiento local.

## 2.7.1. Arquitectura por capas: percepcion, red, nube y aplicacion

### Contenido sugerido

Usa esta seccion para presentar la arquitectura ideal y luego la equivalencia actual del prototipo.

| Capa IoT | Arquitectura ideal | Estado en AgroClima GT |
|---|---|---|
| Percepcion | Sensores fisicos en parcela | Arduino serial/simulacion preparado |
| Red | LoRaWAN, MQTT, gateway | WebSocket y backend local implementados |
| Datos/nube | Base de datos y procesamiento | PostgreSQL, CSV, JSON, modelos Joblib |
| Aplicacion | Dashboard y alertas | React/Vite, mapas, graficas, reportes |

## 2.7.2. Protocolo MQTT y modelo publish-subscribe

### Ajuste recomendado

MQTT debe redactarse como tecnologia futura. El sistema actual no depende de un broker MQTT; usa endpoints REST y WebSocket. Puedes explicar MQTT como una mejora para cuando los sensores se instalen en campo.

## 2.7.3. LoRaWAN y redes LPWAN para zonas rurales

### Ajuste recomendado

LoRaWAN es pertinente por el contexto rural, pero no esta implementado. Mantenlo como justificacion de escalabilidad futura: permitiria conectar sensores de bajo consumo en parcelas alejadas. No lo pongas en diagramas de arquitectura actual salvo que este claramente marcado como "fase futura".

## 2.7.4. Comparacion con otras tecnologias de comunicacion

### Contenido sugerido

La tabla de comparacion WiFi/LoRaWAN/Sigfox/NB-IoT puede quedarse, pero agregale una columna `Uso en esta tesis` para no confundir.

| Tecnologia | Ventaja | Uso en esta tesis |
|---|---|---|
| Serial Arduino | Simple, local, bajo costo | Implementado en prototipo |
| WebSocket | Tiempo real en web | Implementado en prototipo |
| MQTT | Mensajeria IoT eficiente | Futuro |
| LoRaWAN | Largo alcance y bajo consumo | Futuro |
| WiFi | Facil acceso local | Alternativa de pruebas |

## 2.7.5. Edge computing y fog computing en monitoreo agricola

### Ajuste recomendado

Edge/fog computing puede quedar como antecedente de sistemas avanzados. En AgroClima GT, el procesamiento principal ocurre en backend FastAPI. Si lo mencionas, usa esta redaccion: "en una fase futura, parte del filtrado de lecturas o deteccion de umbrales podria ejecutarse en gateway o microcontrolador antes de enviar datos al servidor".

## 2.8. Arquitectura de sistemas de soporte a decisiones y visualizacion de alertas

### Contenido sugerido

Esta seccion debe fortalecerse porque coincide muy bien con el proyecto. AgroClima GT funciona como sistema de soporte a decisiones: integra datos, procesa modelos, calcula riesgo y presenta resultados en dashboard, mapa, graficas, reportes, alertas y exportacion CSV. La interfaz es importante porque traduce variables tecnicas en informacion util para usuarios no especializados.

### Referencias que puedes usar

- Gutiérrez et al. (2022) para DSS visuales en agricultura.
- UNEP para sistemas de alerta e informacion climatica.
- Documentacion de React, Chart.js y Leaflet solo si tu marco teorico tambien cubre tecnologias de visualizacion.

### Imagen o tabla recomendada

- Captura del dashboard.
- Captura del mapa coropletico.
- Captura de alertas.
- Captura del reporte PDF.
- Captura de dataset con filtros y exportacion CSV.

## 2.9. Consideraciones eticas y de privacidad de datos agroclimaticos

### Contenido sugerido

La etica de datos es pertinente porque un sistema agroclimatico puede manejar informacion de parcelas, ubicaciones, productores, practicas agricolas y rendimiento estimado. En la version actual, AgroClima GT trabaja principalmente con datos publicos/procesados, registros locales y pruebas de prototipo. Cuando se incorporen sensores fisicos en campo, sera necesario establecer consentimiento informado, propiedad de datos, anonimato, resguardo de ubicaciones sensibles y reglas de uso de informacion.

### Redaccion lista para insertar

Aunque el prototipo actual se valida en ambiente academico y local, su evolucion hacia sensores instalados en parcelas exige considerar principios de privacidad, consentimiento informado y gobernanza de datos. Las lecturas agroclimaticas pueden revelar condiciones productivas de una finca, por lo que el sistema debe evitar transferencias no autorizadas, anonimizar informacion sensible y comunicar al usuario que las predicciones son apoyo tecnico, no decisiones obligatorias ni alertas oficiales.

### Referencias que puedes usar

- AgGateway o marcos de gobernanza de datos agricolas.
- Literatura de etica de datos en agricultura digital.
- Normativa local aplicable si decides incluir proteccion de datos personales.

### Imagen o tabla recomendada

| Riesgo etico | Medida propuesta |
|---|---|
| Uso no autorizado de datos de parcela | Consentimiento informado |
| Identificacion de ubicaciones sensibles | Anonimizacion o agregacion |
| Dependencia ciega del modelo | Mensajes de apoyo a decision |
| Datos de sensores en campo | Politica de almacenamiento y eliminacion |

## Incisos adicionales recomendados si decides ampliar el capitulo 2

El PDF termina en `2.9`, pero el proyecto se entiende mejor si agregas uno o dos incisos despues, siempre que tu asesor acepte modificar el indice:

### 2.10. Explicabilidad de modelos con SHAP

SHAP ayuda a explicar que variables influyen mas en una prediccion. En AgroClima GT puede justificar por que el sistema no solo entrega `yield_pct`, sino tambien interpretacion de factores como lluvia, temperatura, humedad, pH o humedad del suelo. Si no quieres agregar `2.10`, integra esta explicacion dentro de `2.3.2 XGBoost` o `2.8 DSS`.

### 2.11. Limitaciones tecnicas del prototipo

Este inciso puede declarar desde el marco teorico que el sistema es academico, local y requiere validacion fisica posterior. Si no quieres agregarlo al capitulo 2, usa la seccion `5.5` de resultados y limitaciones.

---

# 3. METODOLOGIA Y PROCESAMIENTO DE DATOS

## 3.1. Enfoque metodologico de la investigacion

### Contenido sugerido

La investigacion se desarrolla bajo un enfoque aplicado y tecnologico, porque no se limita a describir el problema agroclimatico, sino que construye un prototipo funcional para integrar datos climaticos, edaficos y agricolas en una plataforma web de apoyo a la decision. El sistema AgroClima GT procesa fuentes historicas y recientes, ejecuta modelos de aprendizaje automatico, genera alertas y presenta resultados mediante una interfaz web.

El prototipo se valida desde una perspectiva tecnica y funcional. La validacion tecnica revisa la disponibilidad de datos, la estructura del dataset, el entrenamiento del modelo, la respuesta de la API y la persistencia de informacion. La validacion funcional revisa que el usuario pueda ingresar variables, obtener una prediccion de rendimiento, visualizar riesgo, filtrar registros, exportar datos y consultar recomendaciones. La validacion agronomica en campo queda delimitada como trabajo futuro, debido a que el componente fisico con sensores no ha sido probado todavia en parcelas reales.

El desarrollo se organiza en cinco etapas: adquisicion de datos, procesamiento y limpieza, ingenieria de caracteristicas, entrenamiento/evaluacion de modelos e implementacion del prototipo web. Este flujo permite relacionar las fuentes originales con los productos finales del sistema: prediccion de `yield_pct`, nivel de riesgo, alertas, recomendaciones y visualizaciones.

### Referencias a citar en el texto

Usar citas como: los sistemas de soporte a decisiones agricolas requieren convertir datos tecnicos en recomendaciones accionables y visualizaciones comprensibles para el usuario (Gutierrez et al., 2022). Para el componente de aprendizaje automatico tabular, XGBoost es adecuado por su eficiencia y rendimiento en datos estructurados (Chen & Guestrin, 2016).

### Figuras o tablas recomendadas

- Figura: flujo metodologico general del proyecto. Fuente: elaboracion propia.
- Tabla: relacion entre etapa metodologica, archivos del proyecto y resultado obtenido.

### Formula o esquema que puede ir

```text
Fuentes de datos -> Dataset procesado -> Ingenieria de variables -> Modelo XGBoost -> API FastAPI -> Visualizacion React
```

---

## 3.2. Adquisicion y procesamiento del dataset ERA5-Land

### Contenido sugerido

El dataset se construyo a partir de varias fuentes complementarias. ERA5-Land se utiliza como base climatica historica por su cobertura terrestre y consistencia espacial; NASA POWER complementa variables meteorologicas; SoilGrids aporta propiedades de suelo, especialmente pH; Open-Meteo se usa para pronostico y consulta climatica; INSIVUMEH funciona como referencia nacional procesada; y FAOSTAT se utiliza para calibrar el rendimiento agricola con datos reales de Guatemala.

En el proyecto, los datos se almacenan y procesan en archivos locales dentro de `backend/data/`. Los archivos principales son `era5_mensual.csv`, `nasa_power_mensual.csv`, `soilgrids_suelo.csv`, `insivumeh_recent_mensual.csv`, `faostat_yields_guatemala.csv`, `dataset_v2.csv`, `dataset_combinado.csv` y `dataset_faostat.csv`.

### Evidencia del proyecto

- `backend/data/sources/era5_mensual.csv`
- `backend/data/sources/nasa_power_mensual.csv`
- `backend/data/sources/soilgrids_suelo.csv`
- `backend/data/sources/faostat_yields_guatemala.csv`
- `backend/data/datasets/dataset_faostat.csv`
- `backend/scripts/datasets/merge_datasets.py`
- `backend/scripts/datasets/download_faostat.py`

### Tabla recomendada

Tabla 3.1. Fuentes de datos integradas en AgroClima GT.

| Fuente | Archivo local | Variables principales | Uso en el sistema |
|---|---|---|---|
| ERA5-Land | `era5_mensual.csv`, NetCDF anuales | temperatura, lluvia, humedad, humedad de suelo, temperatura de suelo | base climatica historica |
| NASA POWER | `nasa_power_mensual.csv` | temperatura maxima, temperatura minima, viento | variables meteorologicas complementarias |
| SoilGrids | `soilgrids_suelo.csv` | pH y propiedades edaficas | referencia de suelo |
| INSIVUMEH | `insivumeh_recent_mensual.csv`, `insivumeh_stations_daily.csv` | observaciones recientes procesadas | contraste nacional y contexto |
| Open-Meteo | API y archivos raw | pronostico, clima historico/diario | autocompletado y pronostico |
| FAOSTAT | `faostat_yields_guatemala.csv` | rendimiento agricola | calibracion de `yield_pct` |

### Referencias a citar

ERA5-Land esta descrito como un dataset de reanalisis terrestre adecuado para aplicaciones de superficie y clima (Munoz-Sabater et al., 2021). NASA POWER ofrece servicios API para datos meteorologicos y energeticos (NASA POWER, s.f.). SoilGrids proporciona mapas globales de propiedades de suelo como pH y carbono organico (ISRIC, s.f.). Open-Meteo permite consultar pronosticos mediante coordenadas geograficas (Open-Meteo, s.f.).

---

## 3.2.1. Fuentes de datos climaticos: estaciones INSIVUMEH y ERA5-Land

### Contenido sugerido

Este inciso debe explicar que INSIVUMEH y ERA5-Land no cumplen exactamente el mismo papel. ERA5-Land ofrece una base historica espacialmente continua para construir el dataset de entrenamiento. INSIVUMEH representa una fuente nacional de referencia y contexto, pero en el prototipo se maneja como dato procesado localmente, no como red oficial conectada en tiempo real.

La redaccion recomendada es: "En AgroClima GT, ERA5-Land se utiliza como fuente historica principal para variables climaticas y terrestres, mientras que datos recientes de INSIVUMEH se emplean como referencia nacional procesada para enriquecer la interpretacion agroclimatica. Esta combinacion permite aprovechar la cobertura espacial de un reanalisis global y, al mismo tiempo, conservar una referencia institucional del contexto guatemalteco."

### Imagen o tabla recomendada

- Tabla: "Diferencia entre datos de reanalisis y datos observados".
- Figura opcional: mapa de cobertura de departamentos o captura del mapa de riesgo.

### Nota de correccion

No escribir que "todo el dataset proviene de estaciones INSIVUMEH". El proyecto integra varias fuentes.

---

## 3.2.2. Descarga, limpieza y normalizacion de datos

### Contenido sugerido

La limpieza se orienta a convertir archivos heterogeneos en una estructura tabular comun. Los scripts del proyecto normalizan nombres de columnas, convierten formatos, integran datos por municipio, cultivo, mes y anio, revisan rangos de variables y generan datasets incrementales. El resultado final usado por el entrenamiento actual es `dataset_faostat.csv`, que contiene 2,111,220 registros.

Los datasets disponibles muestran una evolucion progresiva:

| Archivo | Registros | Funcion |
|---|---:|---|
| `dataset_preliminar.csv` | 64,935 | dataset base inicial |
| `dataset_openmeteo.csv` | 812,520 | ampliacion con Open-Meteo |
| `dataset_v2.csv` | 1,320,345 | integracion climatica ampliada |
| `dataset_combinado.csv` | 2,111,220 | union de fuentes historicas |
| `dataset_faostat.csv` | 2,111,220 | dataset calibrado con FAOSTAT |

### Figura recomendada

Figura 3.2. Flujo de preparacion del dataset.

```text
ERA5-Land + NASA POWER + SoilGrids + Open-Meteo + INSIVUMEH
        -> normalizacion por municipio/mes/anio
        -> union con cultivos y variables agronomicas
        -> dataset_combinado.csv
        -> calibracion FAOSTAT
        -> dataset_faostat.csv
```

### Formula recomendada: normalizacion min-max para calibracion relativa

```latex
f_{FAO}(c,a)=\frac{R(c,a)-R_{min}(c)}{R_{max}(c)-R_{min}(c)}
```

Donde `R(c,a)` es el rendimiento del cultivo `c` en el anio `a`.

---

## 3.2.3. Validacion de ERA5-Land con datos observados

### Contenido sugerido

La validacion entre ERA5-Land e INSIVUMEH debe presentarse con alcance limitado. El proyecto cuenta con datos INSIVUMEH procesados, pero no se observa una validacion estadistica formal por estacion con sesgo, correlacion o RMSE por variable. Por ello, conviene redactar este inciso como contraste de coherencia y preparacion para validacion futura.

Texto sugerido: "En esta fase, la comparacion entre ERA5-Land e INSIVUMEH se utiliza como revision de coherencia y no como validacion climatologica definitiva. ERA5-Land aporta continuidad espacial y temporal; INSIVUMEH aporta referencia nacional observada. Una validacion formal posterior deberia comparar pares estacion-reanalisis mediante sesgo medio, MAE, RMSE, correlacion y analisis por epoca seca/lluviosa."

### Formulas recomendadas si quieres fortalecer el inciso

```latex
Bias=\frac{1}{n}\sum_{i=1}^{n}(\hat{x_i}-x_i)
```

```latex
RMSE=\sqrt{\frac{1}{n}\sum_{i=1}^{n}(\hat{x_i}-x_i)^2}
```

```latex
MAE=\frac{1}{n}\sum_{i=1}^{n}|\hat{x_i}-x_i|
```

### Tabla recomendada

Tabla 3.3. Alcance actual de validacion ERA5-Land/INSIVUMEH.

| Elemento | Estado actual | Recomendacion |
|---|---|---|
| Datos ERA5-Land | integrados y procesados | conservar como base historica |
| Datos INSIVUMEH | procesados localmente | usar como referencia nacional |
| Validacion estadistica formal | no documentada completamente | agregar si se calculan pares estacion-reanalisis |

---

## 3.3. Tratamiento de datos y limpieza de series temporales

### Contenido sugerido

El tratamiento de datos en AgroClima GT consiste en depurar y alinear registros climaticos, edaficos y agronomicos para formar una matriz tabular. Las variables se organizan por municipio, cultivo, mes y anio. Se validan rangos plausibles para evitar que el modelo reciba valores fisiologicamente imposibles. Esta validacion tambien existe en el backend antes de ejecutar `/predict`.

### Evidencia del proyecto

En `backend/api.py`, los rangos validos son:

```python
temperature:   5.0 a 45.0
rainfall:      0.0 a 600.0
humidity:      5.0 a 100.0
soil_ph:       3.5 a 9.5
soil_moisture: 0.01 a 0.65
light_lux:     500 a 130000
```

### Tabla recomendada

Tabla 3.4. Rangos de validacion de variables de entrada.

---

## 3.3.1. Integracion de datos historicos y datos en tiempo real

### Contenido sugerido

El sistema combina dos tipos de datos. Los datos historicos alimentan el entrenamiento del modelo XGBoost y provienen de archivos climaticos, edaficos y de rendimiento. Los datos en tiempo real o simulados provienen del modulo Arduino y llegan al backend mediante lectura serial o endpoint de simulacion. Estos datos se transmiten al frontend mediante WebSocket para construir alertas y graficas historicas recientes.

### Evidencia del proyecto

- `backend/arduino_reader.py`
- `backend/alert_engine.py`
- Endpoint `POST /arduino/simulate`
- WebSocket `WS /ws/arduino`
- Frontend `frontend/src/pages/Alerts.jsx` y `frontend/src/pages/Arduino.jsx`

### Figura recomendada

Figura 3.4. Integracion de historico y tiempo real.

```text
Dataset historico -> XGBoost -> prediccion
Arduino/simulacion -> WebSocket -> alertas -> grafica en tiempo real
```

---

## 3.3.2. Alineacion temporal y espacial de registros

### Contenido sugerido

La alineacion temporal usa `month` y `year` como llaves de organizacion para integrar informacion climatica y agricola. La alineacion espacial usa `municipio` o departamento como unidad geografica. En el frontend se trabaja con 22 departamentos; el dataset de entrenamiento contiene una cobertura mas amplia de municipios. Esta diferencia debe explicarse como una decision de interfaz: se simplifica la seleccion para el usuario final, mientras el dataset conserva mayor granularidad tecnica.

### Formula o esquema

```latex
D = \{(m,c,t,x_1,x_2,\ldots,x_p,y)\}
```

Donde `m` es municipio/departamento, `c` cultivo, `t` mes/anio, `x` variables predictoras y `y` el `yield_pct`.

### Imagen sugerida

- Captura del mapa de riesgo.
- Tabla de municipios/departamentos cubiertos.

---

## 3.3.3. Tratamiento de valores faltantes e inconsistencias

### Contenido sugerido

El prototipo aplica valores por defecto y derivaciones cuando algunas variables no estan disponibles en una entrada del usuario. Esto permite que el endpoint de prediccion funcione aun si no existe lectura de todos los sensores. Por ejemplo, si no se proporciona humedad de suelo profunda, temperatura de suelo o temperaturas extremas, el backend deriva aproximaciones a partir de temperatura y humedad de suelo.

### Formulas implementadas en `ml_insights.py`

```latex
swvl2 = soil\_moisture + 0.03
```

```latex
swvl3 = soil\_moisture + 0.05
```

```latex
soil\_temp = temperature - 3.0
```

```latex
temp\_max = temperature + 8.0
```

```latex
temp\_min = temperature - 6.0
```

### Nota metodologica

Estas derivaciones deben presentarse como aproximaciones operativas para inferencia, no como mediciones reales. Si el sensor o fuente real existe, debe priorizarse el valor medido.

---

## 3.4. Ingenieria de caracteristicas para el modelo predictivo

### Contenido sugerido

La ingenieria de caracteristicas transforma datos climaticos, edaficos, temporales y agronomicos en un vector de entrada para el modelo. El modelo XGBoost usa 17 variables: municipio codificado, cultivo codificado, mes, temperatura, lluvia, humedad, pH, humedad de suelo, luz, indice de verdor, humedad de subsuelo, humedad profunda, temperatura de suelo, temperatura maxima, temperatura minima, velocidad del viento y altitud.

### Formula recomendada: vector de caracteristicas

```latex
\mathbf{x} = [municipio_{enc}, crop_{enc}, month, T, R, H, pH, SM, L, G, swvl2, swvl3, T_s, T_{max}, T_{min}, W, Z]
```

Donde:

- `T`: temperatura.
- `R`: precipitacion.
- `H`: humedad relativa.
- `SM`: humedad de suelo.
- `L`: luz.
- `G`: indice de verdor.
- `W`: viento.
- `Z`: altitud.

### Tabla recomendada

Tabla 3.5. Variables del modelo predictivo.

| Variable | Tipo | Fuente | Implementacion |
|---|---|---|---|
| `municipio_enc` | categorica codificada | seleccion usuario/dataset | `LabelEncoder` |
| `crop_enc` | categorica codificada | seleccion usuario/dataset | `LabelEncoder` |
| `month` | temporal | fecha | entero 1-12 |
| `temperature` | climatica | API/sensor/dataset | entrada al modelo |
| `rainfall` | climatica | API/dataset | entrada al modelo |
| `humidity` | climatica | API/dataset | entrada al modelo |
| `soil_ph` | edafica | SoilGrids/manual | entrada al modelo |
| `soil_moisture` | edafica/sensor | Arduino/ERA5 | entrada al modelo |
| `light_lux` | sensor | Arduino/estimado | entrada al modelo |
| `greenness_idx` | sensor/vegetacion | TCS3200/estimado | entrada al modelo |
| `swvl2`, `swvl3` | edafica | ERA5/derivada | entrada al modelo |
| `soil_temp` | edafica | ERA5/derivada | entrada al modelo |
| `temp_max`, `temp_min` | climatica | NASA POWER/derivada | entrada al modelo |
| `wind_speed` | climatica | NASA POWER | entrada al modelo |
| `altitud_m` | geografica | referencia local | entrada al modelo |

---

## 3.4.1. Horas frio, estres termico y variables derivadas

### Ajuste recomendado

El titulo del PDF menciona "horas frio", pero el proyecto no muestra una formula de horas frio como variable central del modelo. Conviene ampliar el inciso hacia "variables derivadas de clima, suelo y estres agroclimatico". Si mantienes "horas frio", presentalo como variable futura o como indicador no central.

### Contenido sugerido

AgroClima GT incorpora variables derivadas para representar condiciones que no siempre se capturan directamente desde el formulario del usuario. Entre ellas estan temperatura de suelo, humedad de suelo en capas, temperatura maxima, temperatura minima, velocidad de viento, altitud, indice de verdor y un indice de estres hidrico disponible en `water_stress_index.csv`. Estas variables amplian el contexto del modelo y permiten relacionar condiciones climaticas con respuesta agricola.

### Formula recomendada: indice de verdor

```latex
G = \frac{G_{raw}}{R_{raw}+G_{raw}+B_{raw}} \times 100
```

### Imagen o tabla recomendada

- Tabla: variables derivadas y archivo/fuente.
- Captura: vista Arduino o grafica historica de sensores.

---

## 3.4.2. Incorporacion de fases fenologicas como variables predictoras

### Ajuste recomendado

El proyecto no contiene una variable explicita de fase fenologica por cultivo. Lo que si existe es `month`, calendario de siembra (`sowing_calendar.csv`) y rangos optimos por cultivo. Por eso, este inciso debe redactarse como aproximacion temporal/fenologica.

### Contenido sugerido

La fase fenologica no se modela como etiqueta directa en esta version del prototipo. En su lugar, el sistema usa el mes (`month`) y el calendario de siembra como aproximaciones temporales que permiten capturar estacionalidad agricola. Esta decision reduce la complejidad del prototipo y evita afirmar disponibilidad de observaciones fenologicas que no fueron recolectadas en campo.

### Tabla recomendada

Tabla 3.6. Representacion temporal y fenologica aproximada.

| Elemento | Estado en proyecto | Uso |
|---|---|---|
| `month` | implementado | variable temporal del modelo |
| `sowing_calendar.csv` | implementado | recomendacion de meses favorables |
| fase fenologica observada | no implementada | trabajo futuro |

---

## 3.4.3. Descomposicion STL y transformacion de series

### Ajuste recomendado

STL no aparece como componente implementado en el codigo. No debe presentarse como metodo usado. Puedes mantenerlo como antecedente teorico o reemplazar este inciso por "transformacion de series y deteccion de anomalias con Isolation Forest".

### Contenido sugerido

Aunque la literatura usa metodos como STL para separar tendencia, estacionalidad y residuo en series temporales, la version implementada de AgroClima GT utiliza un enfoque mas directo: validacion de rangos, perfil de distribucion de entrenamiento, Isolation Forest y calculo de data drift. Este enfoque es consistente con un prototipo tabular y permite detectar entradas atipicas sin requerir series largas por sensor.

### Formula recomendada si dejas STL como antecedente

```latex
Y_t = T_t + S_t + R_t
```

Donde `T_t` es tendencia, `S_t` estacionalidad y `R_t` residuo. Aclara: "Esta descomposicion se considera como alternativa metodologica, no como componente implementado en la version actual".

### Formula implementada: Isolation Forest

```latex
s(x,n)=2^{-\frac{E(h(x))}{c(n)}}
```

Citar a Liu et al. (2008).

---

## 3.5. Estrategia de entrenamiento, validacion y ajuste de modelos

### Contenido sugerido

El entrenamiento se realiza con `backend/scripts/training/model_xgboost.py`. El script carga el dataset disponible con prioridad: `dataset_faostat.csv`, `dataset_combinado.csv`, `dataset_openmeteo.csv`, base de datos y finalmente `dataset_preliminar.csv`. Luego codifica municipio y cultivo con `LabelEncoder`, separa entrenamiento/prueba con `train_test_split` 80/20, ejecuta validacion cruzada de 5 folds para XGBoost y guarda el modelo en `xgboost_yield.joblib`.

El modelo principal es `XGBRegressor` con 400 arboles, profundidad maxima 6, tasa de aprendizaje 0.05, submuestreo 0.8 y regularizacion L1/L2. Random Forest se usa como linea base comparativa.

### Hiperparametros a colocar

| Hiperparametro | Valor |
|---|---:|
| `n_estimators` | 400 |
| `max_depth` | 6 |
| `learning_rate` | 0.05 |
| `subsample` | 0.8 |
| `colsample_bytree` | 0.8 |
| `min_child_weight` | 3 |
| `reg_alpha` | 0.1 |
| `reg_lambda` | 1.0 |
| `random_state` | 42 |

### Formula recomendada: objetivo XGBoost

```latex
\mathcal{L}(\theta)=\sum_{i=1}^{n} l(y_i,\hat{y}_i)+\sum_{k=1}^{K}\Omega(f_k)
```

```latex
\Omega(f)=\gamma T + \frac{1}{2}\lambda \sum_{j=1}^{T}w_j^2
```

### Referencia

XGBoost debe citarse con Chen y Guestrin (2016).

---

## 3.6. Metricas de evaluacion y validacion de modelos

### Contenido sugerido

La evaluacion del modelo se realiza como problema de regresion, porque la variable objetivo es `yield_pct`. Las metricas principales son R2, MAE y RMSE. R2 mide capacidad explicativa, MAE expresa el error absoluto promedio en puntos porcentuales y RMSE penaliza con mayor fuerza los errores grandes.

### Metricas actuales del proyecto

| Modelo | R2 | MAE | RMSE | CV R2 | Tiempo de entreno |
|---|---:|---:|---:|---:|---:|
| XGBoost | 0.6334 | 5.91 | 7.68 | 0.6051 +/- 0.0083 | 44.8 s |
| Random Forest | 0.3474 | 8.26 | 10.25 | 0.3479 +/- 0.0046 | 86.5 s |

### Formulas

```latex
MAE=\frac{1}{n}\sum_{i=1}^{n}|y_i-\hat{y}_i|
```

```latex
RMSE=\sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i-\hat{y}_i)^2}
```

```latex
R^2=1-\frac{\sum_{i=1}^{n}(y_i-\hat{y}_i)^2}{\sum_{i=1}^{n}(y_i-\bar{y})^2}
```

### Imagen recomendada

- Captura del panel Admin/Modelos con grafica de barras XGBoost vs Random Forest.
- Tabla de metricas extraida de `model_comparison.json`.

---

## 3.6.1. Metricas de regresion: RMSE, MAE y R2

### Contenido sugerido

Estas metricas deben ocupar el centro de la evaluacion porque el objetivo del modelo es continuo. El MAE se interpreta directamente como desviacion promedio del porcentaje de rendimiento esperado. El RMSE permite identificar si existen errores grandes que afecten la confiabilidad. El R2 se utiliza para comparar la capacidad explicativa entre modelos.

### Nota para el PDF

Actualizar cualquier valor viejo con los datos actuales del archivo `backend/data/models/model_comparison.json`.

---

## 3.6.2. Metricas de clasificacion: precision, recall, F1-Score y matriz de confusion

### Ajuste recomendado

No hay etiquetas reales de campo para evaluar anomalias o alertas como clasificacion supervisada. Por tanto, no conviene presentar precision, recall, F1 o matriz de confusion como resultados concluyentes.

### Contenido sugerido

En esta version, las metricas de clasificacion se dejan como propuesta para una fase de validacion en campo. Para calcular precision, recall, F1-score y matriz de confusion seria necesario contar con eventos reales etiquetados, por ejemplo: alerta correcta, falsa alarma, evento no detectado y condicion normal. Actualmente, el sistema valida funcionalmente las alertas mediante reglas y simulaciones, no mediante un conjunto etiquetado de eventos agronomicos reales.

### Formula opcional para trabajo futuro

```latex
Precision=\frac{TP}{TP+FP}
```

```latex
Recall=\frac{TP}{TP+FN}
```

```latex
F1=2\cdot\frac{Precision\cdot Recall}{Precision+Recall}
```

---

# 4. DISENO E IMPLEMENTACION DEL PROTOTIPO

## 4.1. Arquitectura general del sistema predictivo

### Contenido sugerido

AgroClima GT utiliza una arquitectura modular compuesta por frontend, backend, capa de datos, modelo predictivo y modulo de sensores. El frontend React/Vite concentra la experiencia de usuario. El backend FastAPI valida entradas, ejecuta el modelo, consulta fuentes procesadas, gestiona alertas y expone endpoints HTTP/WebSocket. PostgreSQL almacena usuarios, predicciones, lecturas, alertas, datasets y metadata del modelo cuando el servicio esta activo. Los modelos se guardan como artefactos Joblib y los datasets como archivos CSV/NetCDF/JSON.

### Figura recomendada

Figura 4.1. Arquitectura general de AgroClima GT.

```text
Usuario -> React/Vite -> FastAPI -> XGBoost/Isolation Forest
                         |        -> CSV/JSON/NetCDF/Joblib
                         |        -> PostgreSQL
                         |        -> Open-Meteo / datos procesados
Arduino/simulacion -> WebSocket -> Alertas -> Frontend
```

### Referencias

FastAPI puede citarse por su soporte de OpenAPI y validacion automatica. React se puede citar por su modelo de componentes. PostgreSQL y Docker Compose deben citarse desde documentacion oficial.

---

## 4.2. Seleccion y justificacion del area de estudio

### Contenido sugerido

El area de estudio corresponde a Guatemala. La interfaz de usuario trabaja con los 22 departamentos para simplificar el uso operativo, mientras el dataset de entrenamiento puede incluir municipios adicionales para mejorar la representacion espacial. Esta seleccion responde a la necesidad de adaptar el prototipo al contexto agricola guatemalteco y permitir analisis por departamento, cultivo y condiciones climaticas.

### Imagen recomendada

- Captura del mapa de riesgo y coropletico departamental.
- Tabla de departamentos cubiertos.

### Nota de precision

Si usas "municipio" en el texto, revisa que no se contradiga con el frontend, donde muchas opciones son departamentos. Puedes escribir "departamento/municipio" cuando hables de la unidad espacial general.

---

## 4.3. Diseno del pipeline de datos y flujo operacional del sistema

### Contenido sugerido

El pipeline operativo inicia con fuentes climaticas y edaficas, continua con procesamiento local, genera datasets de entrenamiento, entrena el modelo XGBoost y finalmente expone predicciones mediante FastAPI. Durante la ejecucion, el usuario ingresa variables o las obtiene desde el pronostico; el backend prepara el vector de caracteristicas, ejecuta el modelo, calcula intervalos de confianza, genera explicaciones SHAP cuando estan disponibles, detecta anomalias y devuelve resultados a la interfaz.

### Figura recomendada

Figura 4.2. Pipeline operativo de AgroClima GT.

```text
Fuentes -> scripts de procesamiento -> dataset_faostat.csv
dataset_faostat.csv -> model_xgboost.py -> xgboost_yield.joblib
React -> POST /predict -> FastAPI -> modelo -> yield_pct + riesgo + explicacion
```

### Formula: intervalo de confianza implementado

```latex
m=\max(1.96\sigma, 3.5)
```

```latex
\hat{y}_{low}=clip(\hat{y}-m,0,100)
```

```latex
\hat{y}_{high}=clip(\hat{y}+m,0,100)
```

---

## 4.4. Desarrollo del motor de deteccion de anomalias y generacion de alertas

### Contenido sugerido

El motor de alertas combina tres capas. La primera valida rangos fisiologicamente plausibles antes de ejecutar predicciones. La segunda utiliza Isolation Forest para identificar entradas atipicas respecto al comportamiento esperado. La tercera aplica reglas agronomicas por cultivo y variable, comparando lecturas contra rangos optimos y generando severidad leve, moderada o severa.

### Formula de desviacion usada por alertas

```latex
\Delta_v =
\begin{cases}
\frac{v_{min}-x}{\max(v_{max}-v_{min},1)}\times 100, & x<v_{min}\\
\frac{x-v_{max}}{\max(v_{max}-v_{min},1)}\times 100, & x>v_{max}\\
0, & v_{min}\leq x \leq v_{max}
\end{cases}
```

### Clasificacion

```latex
severidad =
\begin{cases}
severo, & \Delta_v \geq 50\\
moderado, & 25 \leq \Delta_v < 50\\
leve, & 10 \leq \Delta_v < 25
\end{cases}
```

### Imagen recomendada

- Captura del modulo de alertas con historial Arduino.
- Captura de una simulacion con alerta.

---

## 4.5. Integracion de sensores IoT y transmision de datos

### Ajuste recomendado

Redactar como integracion de software con Arduino y simulacion, no como red IoT desplegada en campo.

### Contenido sugerido

El prototipo incluye soporte para un nodo Arduino conectado por puerto serial. El backend puede abrir/cerrar conexion, consultar estado, recibir lecturas, simular sensores y transmitir datos al frontend por WebSocket. Las variables esperadas incluyen temperatura, humedad, humedad de suelo, luz, pH, precipitacion e indice de verdor. La instalacion fisica, calibracion y comparacion contra instrumentos de referencia quedan como etapa futura.

### Tabla recomendada

Tabla 4.1. Estado del componente de sensores.

| Componente | Estado actual | Evidencia |
|---|---|---|
| Conexion Arduino serial | implementada | `arduino_reader.py`, endpoints `/arduino/*` |
| Simulacion de lecturas | implementada | `POST /arduino/simulate` |
| WebSocket en vivo | implementado | `WS /ws/arduino` |
| Grafica historica frontend | implementada | `Alerts.jsx` |
| Calibracion fisica en campo | pendiente | trabajo futuro |

### Imagen recomendada

- Captura del modulo Arduino.
- Captura de la grafica historica de lecturas en Alerts.

---

## 4.6. Diseno de la interfaz de visualizacion y apoyo a la toma de decisiones

### Contenido sugerido

La interfaz web traduce el resultado tecnico del modelo en elementos interpretables para el usuario: rendimiento esperado, nivel de riesgo, recomendaciones, mapa, graficas, alertas y reportes. El usuario puede ingresar condiciones de cultivo, consultar pronostico, revisar tendencias de `yield_pct`, filtrar dataset, exportar CSV, visualizar riesgo geograficamente y generar reportes.

### Capturas recomendadas

1. Pantalla de login/onboarding.
2. Dashboard principal con formulario y prediccion.
3. Dataset con filtros, tendencia `yield_pct` y boton exportar CSV.
4. Mapa de riesgo con coropletico departamental.
5. Alertas con grafica historica Arduino.
6. Reporte ejecutivo.
7. Pronostico.
8. Panel Modelos/Admin con grafica XGBoost vs Random Forest.
9. Modo oscuro como captura opcional visible.

### Referencia

Los DSS agricolas visuales deben reducir la carga cognitiva y convertir datos complejos en informacion accionable (Gutierrez et al., 2022).

---

## 4.7. Herramientas, frameworks y stack tecnologico utilizado

### Contenido sugerido

El stack se compone de React y Vite para el frontend; FastAPI para el backend; PostgreSQL para persistencia; Docker Compose para levantar la base de datos; XGBoost, scikit-learn, pandas, numpy y joblib para procesamiento y aprendizaje automatico; Chart.js para graficas; Leaflet para mapas; html2canvas y jsPDF para reportes; y WebSocket para transmision de lecturas Arduino.

### Tabla recomendada

Tabla 4.2. Stack tecnologico de AgroClima GT.

| Capa | Herramientas | Funcion |
|---|---|---|
| Frontend | React, Vite, Chart.js, Leaflet | interfaz, graficas, mapa |
| Backend | FastAPI, Python | API, validacion, prediccion |
| ML | XGBoost, scikit-learn, SHAP, joblib | entrenamiento, inferencia, explicabilidad |
| Datos | pandas, CSV, JSON, NetCDF | procesamiento local |
| Persistencia | PostgreSQL, Docker Compose | usuarios, predicciones, alertas |
| Sensores | Arduino serial, WebSocket | lectura y transmision en vivo |

---

# 5. ANALISIS DE RESULTADOS Y VALIDACION

## 5.1. Evaluacion del desempeno de los modelos

### Contenido sugerido

La evaluacion compara XGBoost contra Random Forest usando el mismo conjunto de datos y el mismo esquema de division entrenamiento/prueba. XGBoost obtuvo mejor desempeno en las tres metricas principales: mayor R2 y menores errores MAE/RMSE. Ademas, su tiempo de entrenamiento fue menor que Random Forest en la corrida registrada.

### Texto listo para insertar

En la comparacion interna del prototipo, XGBoost alcanzo R2 = 0.6334, MAE = 5.91 y RMSE = 7.68, mientras Random Forest obtuvo R2 = 0.3474, MAE = 8.26 y RMSE = 10.25. Estos resultados respaldan la seleccion de XGBoost como modelo principal, porque explica una mayor proporcion de la variabilidad del `yield_pct` y reduce el error promedio de prediccion. La validacion cruzada tambien favorece a XGBoost, con CV R2 = 0.6051 frente a 0.3479 de Random Forest.

### Imagen recomendada

- Captura de la grafica de barras en el panel de Modelos.
- Tabla 5.1 con los valores de `model_comparison.json`.

---

## 5.2. Resultados de deteccion de anomalias termicas

### Ajuste recomendado

No presentar como deteccion validada de heladas reales si no hay eventos etiquetados. Presentar como prueba funcional de deteccion de entradas anomalas.

### Contenido sugerido

El modulo de anomalias evalua si una entrada se aleja del comportamiento esperado en el perfil de entrenamiento. Para ello se usa Isolation Forest sobre variables de sensores y clima. El resultado se reporta como `normal`, `sospechoso` o `anomalia`. Esta salida permite activar una revision tecnica cuando los datos ingresados o simulados estan fuera de la distribucion esperada.

### Formula implementada: score de anomalia

```latex
z_a=\frac{d(x)-\mu_d}{\sigma_d}
```

```latex
score_{anomalia}=clip(100-(z_a+2)\times25,0,100)
```

### Imagen recomendada

- Captura de una prediccion o simulacion con anomalia.
- Captura del panel de alertas con condicion severa.

---

## 5.3. Analisis de efectividad en la deteccion de riesgo de bajo rendimiento

### Contenido sugerido

El riesgo de bajo rendimiento se calcula a partir del `yield_pct` estimado por el modelo y de reglas agronomicas que evalúan lluvia, temperatura, humedad y pH. Esta combinacion evita depender de una sola fuente de decision. Si el modelo estima buen rendimiento pero las reglas detectan condiciones extremas, el sistema conserva la alerta de riesgo.

### Formula de clasificacion de rendimiento

```latex
nivel =
\begin{cases}
alto, & yield\_pct \geq 75\\
medio, & 50 \leq yield\_pct < 75\\
bajo, & 25 \leq yield\_pct < 50\\
critico, & yield\_pct < 25
\end{cases}
```

### Formula de riesgo por reglas

```latex
score = clip(s_R+s_T+s_H+s_{pH}+c_f,0,100)
```

### Imagen recomendada

- Captura del dashboard luego de ejecutar "Analizar riesgo".
- Captura del reporte ejecutivo.
- Captura del mapa de riesgo para el cultivo seleccionado.

---

## 5.4. Validacion del sistema de alertas en el caso de estudio

### Contenido sugerido

La validacion funcional del sistema de alertas se realiza mediante entradas manuales y lecturas simuladas de Arduino. El objetivo es comprobar que el backend recibe datos, calcula desviaciones respecto a rangos optimos, asigna severidad, genera recomendacion y transmite el resultado al frontend. Esta validacion demuestra funcionamiento del flujo software, aunque no sustituye una validacion agronomica con sensores instalados en campo.

### Evidencia del proyecto

- Endpoint `POST /alerts/check`
- Endpoint `POST /arduino/simulate`
- `alert_engine.py`
- `email_notifier.py`
- Tabla `alertas`
- Vista `Alerts.jsx`

### Imagen recomendada

- Captura de alerta generada.
- Captura del correo de prueba si tienes SMTP configurado.
- Captura del historial de lecturas Arduino.

---

## 5.5. Discusion sobre factibilidad, escalabilidad y limitaciones

### Contenido sugerido

AgroClima GT demuestra factibilidad tecnica al integrar datos, modelo predictivo, API, base de datos, interfaz web, alertas, mapa y modulo Arduino en una sola plataforma. La arquitectura permite ampliar el prototipo con nuevas fuentes, sensores calibrados, validacion de campo, despliegue cloud y mayor automatizacion de reentrenamiento.

Entre las limitaciones principales estan: ausencia de validacion de sensores en parcela, falta de eventos reales etiquetados para evaluar anomalias con precision/recall, dependencia de fuentes externas para pronostico, aproximaciones cuando faltan sensores y necesidad de validar los resultados con productores o tecnicos agronomos.

### Tabla recomendada

Tabla 5.2. Limitaciones y mejoras futuras.

| Limitacion | Impacto | Mejora futura |
|---|---|---|
| sensores no validados en campo | limita conclusiones fisicas | calibracion e instalacion piloto |
| anomalias sin etiquetas reales | no permite F1/recall | recolectar eventos confirmados |
| variables derivadas por defecto | introduce aproximacion | medir mas variables directamente |
| datos por departamento/municipio | generalizacion espacial | aumentar resolucion geografica |
| API de pronostico externa | dependencia operativa | cache robusto y fuentes alternas |

---

# CONCLUSIONES

## Contenido sugerido

1. AgroClima GT demuestra que es tecnicamente viable integrar datos climaticos, edaficos y agronomicos en una plataforma web para estimar rendimiento agricola y riesgo agroclimatico en Guatemala.
2. El modelo XGBoost fue el algoritmo con mejor desempeno interno frente a Random Forest, con R2 = 0.6334, MAE = 5.91 y RMSE = 7.68 sobre la comparacion registrada en el proyecto.
3. La incorporacion de fuentes como ERA5-Land, NASA POWER, SoilGrids, Open-Meteo, INSIVUMEH procesado y FAOSTAT permite construir un dataset mas robusto que una fuente unica.
4. La interfaz web facilita la interpretacion de resultados mediante dashboard, reportes, dataset filtrable, exportacion CSV, mapa de riesgo, coropletico, alertas y visualizacion de lecturas Arduino.
5. El componente Arduino esta implementado a nivel de software y simulacion, pero requiere calibracion, instalacion y validacion en campo antes de presentarlo como sistema IoT operativo.
6. Las alertas funcionan como validacion funcional basada en reglas y anomalias, pero la evaluacion con precision, recall y F1 requiere eventos reales etiquetados.

---

# RECOMENDACIONES

## Contenido sugerido

1. Realizar una prueba piloto en campo con sensores calibrados para validar temperatura, humedad de suelo, luminosidad e indice de verdor.
2. Construir un conjunto de eventos etiquetados para evaluar anomalias y alertas con matriz de confusion, precision, recall y F1-score.
3. Comparar ERA5-Land con estaciones INSIVUMEH mediante MAE, RMSE, sesgo y correlacion por variable.
4. Documentar capturas actualizadas del sistema: dashboard, dataset con tendencia, mapa, alertas, Arduino, reporte y panel de modelos.
5. Mantener `model_comparison.json` actualizado cada vez que se reentrene para evitar contradicciones en la tesis.
6. Separar claramente "implementado", "simulado" y "trabajo futuro" en cada capitulo.
7. Ampliar el componente de seguridad si el prototipo se despliega fuera del entorno local, especialmente autenticacion, tokens, CORS y proteccion de credenciales.

---

# REFERENCIAS SUGERIDAS EN APA 7

Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. En *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining* (pp. 785-794). Association for Computing Machinery. https://doi.org/10.1145/2939672.2939785

Docker. (s.f.). *Docker Compose overview*. Docker Docs. https://docs.docker.com/compose/

FastAPI. (s.f.). *FastAPI documentation*. https://fastapi.tiangolo.com/

Gutiérrez, F., Htun, N. N., Schlenz, F., Kasimati, A., & Verbert, K. (2022). Developing visual-assisted decision support systems across diverse agricultural use cases. *Agriculture, 12*(7), 1027. https://doi.org/10.3390/agriculture12071027

ISRIC. (s.f.). *SoilGrids: Global gridded soil information*. https://www.isric.org/explore/soilgrids

Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008). Isolation forest. En *2008 Eighth IEEE International Conference on Data Mining* (pp. 413-422). IEEE. https://doi.org/10.1109/ICDM.2008.17

Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. En *Advances in Neural Information Processing Systems 30*. https://papers.neurips.cc/paper/7062-a-unified-approach-to-interpreting-model-predictions

Muñoz-Sabater, J., Dutra, E., Agustí-Panareda, A., Albergel, C., Arduini, G., Balsamo, G., Boussetta, S., Choulga, M., Harrigan, S., Hersbach, H., Martens, B., Miralles, D. G., Piles, M., Rodríguez-Fernández, N. J., Zsoter, E., Buontempo, C., & Thépaut, J.-N. (2021). ERA5-Land: A state-of-the-art global reanalysis dataset for land applications. *Earth System Science Data, 13*(9), 4349-4383. https://doi.org/10.5194/essd-13-4349-2021

NASA POWER. (s.f.). *NASA POWER API documentation*. https://power.larc.nasa.gov/api/pages/

Open-Meteo. (s.f.). *Weather Forecast API documentation*. https://open-meteo.com/en/docs

PostgreSQL Global Development Group. (2025). *PostgreSQL 16 documentation*. https://www.postgresql.org/docs/16/

React. (s.f.). *React documentation*. https://react.dev/

scikit-learn developers. (s.f.). *IsolationForest*. https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html

XGBoost developers. (s.f.). *XGBoost documentation*. https://xgboost.readthedocs.io/

---

# Lista rapida de capturas que debes tomar

1. Login/onboarding.
2. Dashboard antes de analizar.
3. Dashboard con prediccion ejecutada.
4. Dataset con filtros y grafica `yield_pct`.
5. Exportacion CSV visible o archivo descargado.
6. Mapa de riesgo y coropletico departamental.
7. Alertas con grafica historica Arduino.
8. Arduino con lectura simulada o conectado.
9. Reporte ejecutivo.
10. Pronostico.
11. Modelos/Admin con grafica XGBoost vs Random Forest.
12. Panel admin de datasets/predicciones/lecturas.
13. Modo oscuro mostrando una pantalla importante.

# Incisos que conviene agregar si el formato de tesis lo permite

## 3.7. Calibracion de rendimiento con FAOSTAT

Agregar este inciso si quieres explicar por que `yield_pct` no es solo una formula sintetica. Debe ir despues de metricas o al final de procesamiento de datos.

```latex
yield_{adj}=clip(yield_{base}\times(0.75+0.50\times f_{FAO}),5,100)
```

## 4.8. Exportacion, reportes y trazabilidad de resultados

Agregar este inciso para justificar CSV y PDF como funciones necesarias en investigacion. Menciona que Dataset permite exportar CSV filtrado y Reports permite generar PDF.

## 5.6. Comparacion visual y usabilidad del prototipo

Agregar este inciso si quieres aprovechar las nuevas visualizaciones: mapa, tendencia, barras de modelos, modo oscuro y graficas Arduino. Puedes apoyarlo con Gutierrez et al. (2022).
