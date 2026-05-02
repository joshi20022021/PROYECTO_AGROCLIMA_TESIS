"""
Dataset de recomendaciones agronómicas con remedios químicos y biológicos.
Se activan cuando los sensores superan los rangos óptimos definidos en
crop_optimal_conditions.csv.

Estructura:
    crop          — cultivo ("Todos", "Todos_Grano", nombre específico)
    variable      — temperature | light_lux | soil_moisture | greenness_idx
                    humidity | rainfall | soil_ph
    condition     — alto | bajo
    severity      — leve (10-25%) | moderado (25-50%) | severo (>50%)
    problem       — descripción del problema
    consequence   — qué ocurre si no se atiende
    action        — acción principal recomendada
    remedy_type   — quimico | biologico | cultural | fertilizante | riego
    remedy_name   — nombre del producto o práctica
    formula       — fórmula química o composición (N-P-K u otro)
    dose          — dosis recomendada
    application   — foliar | suelo | fertirriego | instalacion | drenaje
    notes         — observaciones adicionales

Fuentes:
    - MAGA Guatemala — Fichas técnicas de manejo integrado de cultivos
    - ICTA Guatemala — Boletines técnicos
    - FAO — Manual de fertilización de suelos tropicales
    - Anacafé — Manual del caficultor (edición 2022)
    - Guía de plaguicidas SENASAG / MAGA
    - Fertilización de cultivos hortícolas (CENTA El Salvador)
    - Manual IFA de nutrición de plantas (Fertilizer Manual 2000)
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd

# ---------------------------------------------------------------------------
# RECOMENDACIONES
# Severity thresholds (% fuera del rango óptimo):
#   leve     : 10 – 25 %
#   moderado : 25 – 50 %
#   severo   : > 50 %
# ---------------------------------------------------------------------------

RECS = [

    # ════════════════════════════════════════════════════════════════════
    # TEMPERATURA — ALTA
    # ════════════════════════════════════════════════════════════════════
    dict(crop="Todos", variable="temperature", condition="alto", severity="leve",
         problem="Temperatura ligeramente superior al optimo del cultivo",
         consequence="Reduccion leve de fotosintesis y aumento de transpiracion",
         action="Aplicar malla sombra del 30% y aumentar frecuencia de riego",
         remedy_type="cultural", remedy_name="Malla sombra raschel",
         formula="-", dose="30% cobertura", application="instalacion",
         notes="Instalar en orientacion norte-sur para maxima efectividad"),

    dict(crop="Todos", variable="temperature", condition="alto", severity="moderado",
         problem="Temperatura moderadamente elevada, estres termico activo",
         consequence="Caida de flores, aborto de frutos, quemadura foliar",
         action="Malla sombra 50% + riego por aspersion en horas de maximo calor",
         remedy_type="cultural", remedy_name="Malla sombra 50% + aspersion",
         formula="-", dose="50% cobertura, riego 15 min cada 2h", application="instalacion",
         notes="El riego por aspersion puede bajar la temperatura foliar hasta 5 grados C"),

    dict(crop="Todos", variable="temperature", condition="alto", severity="severo",
         problem="Temperatura critica, riesgo de muerte de tejidos",
         consequence="Necrosis foliar, perdida total del cultivo sin intervencion",
         action="Aspersion continua + kaolin arcilloso foliar + sombra de emergencia",
         remedy_type="quimico", remedy_name="Kaolin (Surround WP)",
         formula="Al2Si2O5(OH)4", dose="3-5 kg/100 L agua", application="foliar",
         notes="El kaolin refleja la radiacion solar y reduce temperatura foliar 3-5 grados C"),

    dict(crop="Cafe", variable="temperature", condition="alto", severity="moderado",
         problem="Temperatura excede rango para cafe; riesgo de roya acelerada",
         consequence="Proliferacion de Hemileia vastatrix, defoliacion masiva",
         action="Incrementar sombra con Inga spp. o Grevillea + fungicida preventivo",
         remedy_type="quimico", remedy_name="Oxicloruro de cobre (Cupravit)",
         formula="Cu2(OH)3Cl", dose="300-400 g/100 L agua", application="foliar",
         notes="Aplicar cada 21 dias durante periodos de alta temperatura y humedad"),

    dict(crop="Tomate", variable="temperature", condition="alto", severity="moderado",
         problem="Caida de flores por exceso de calor en tomate",
         consequence="Reduccion drastica de cuajado, perdida de hasta 60% del rendimiento",
         action="Riego por aspersion + aplicacion de acido borico para cuajado",
         remedy_type="fertilizante", remedy_name="Acido borico",
         formula="H3BO3", dose="1.5-2 g/L agua", application="foliar",
         notes="El boro mejora la germinacion del polen a altas temperaturas"),

    dict(crop="Papa", variable="temperature", condition="alto", severity="leve",
         problem="Temperatura sobre optimo inhibe formacion de tuberculos",
         consequence="Tubericulos pequenos y deformes, reduccion de almidon",
         action="Mulching con paja para mantener frescura del suelo",
         remedy_type="cultural", remedy_name="Mulch de paja / plastico plateado",
         formula="-", dose="5-8 cm de espesor", application="suelo",
         notes="El plastico plateado refleja calor y reduce temperatura del suelo hasta 4 grados C"),

    dict(crop="Frijol", variable="temperature", condition="alto", severity="moderado",
         problem="Estres termico en frijol durante floración y llenado de vainas",
         consequence="Aborto floral, vainas vacías, reducción de proteína en grano",
         action="Riego por aspersion + potasio para resistencia termica",
         remedy_type="fertilizante", remedy_name="Sulfato de potasio",
         formula="K2SO4 (0-0-50)", dose="10-15 kg/ha foliar diluido al 1%", application="foliar",
         notes="El potasio regula la apertura estomatica y mejora tolerancia termica"),

    # ════════════════════════════════════════════════════════════════════
    # TEMPERATURA — BAJA
    # ════════════════════════════════════════════════════════════════════
    dict(crop="Todos", variable="temperature", condition="bajo", severity="leve",
         problem="Temperatura inferior al optimo, crecimiento lento",
         consequence="Retraso en desarrollo, menor absorcion de nutrientes",
         action="Aplicar mulch negro para conservar calor del suelo",
         remedy_type="cultural", remedy_name="Acolchado plastico negro",
         formula="-", dose="1 lamina de 50 micras", application="suelo",
         notes="El plastico negro aumenta la temperatura del suelo 2-4 grados C"),

    dict(crop="Todos", variable="temperature", condition="bajo", severity="moderado",
         problem="Riesgo de helada o frio prolongado",
         consequence="Necrosis por frio, paralisis de crecimiento vegetativo",
         action="Cobertura flotante + riego antihelada nocturno",
         remedy_type="cultural", remedy_name="Agrotextil (tela flotante)",
         formula="-", dose="Cobertura total nocturna", application="instalacion",
         notes="El riego antihelada libera calor latente al congelarse; activar cuando T < 4 grados C"),

    dict(crop="Todos", variable="temperature", condition="bajo", severity="severo",
         problem="Helada severa o temperatura critica bajo cero",
         consequence="Destruccion de tejidos, muerte de plantas sensibles",
         action="Aspersion antihelada + aplicar silicato de potasio foliar preventivo",
         remedy_type="quimico", remedy_name="Silicato de potasio",
         formula="K2SiO3", dose="2-3 mL/L agua", application="foliar",
         notes="El silicio fortalece las paredes celulares y reduce dano por hielo intracelular"),

    dict(crop="Cafe", variable="temperature", condition="bajo", severity="moderado",
         problem="Frio nocturno daña tejidos del cafe en altiplano",
         consequence="Defoliacion, muerte de ramas terminales",
         action="Cortinas rompevientos + aplicacion foliar de calcio-boro",
         remedy_type="fertilizante", remedy_name="Nitrato de calcio + Boron",
         formula="Ca(NO3)2 + H3BO3", dose="2 kg/ha + 1 kg/ha", application="foliar",
         notes="El calcio fortalece membranas; el boro mejora resistencia al frio"),

    dict(crop="Maiz", variable="temperature", condition="bajo", severity="leve",
         problem="Frio retrasa germinacion y emergencia del maiz",
         consequence="Stand de plantas irregular, mayor presion de malezas",
         action="Biostimulante a base de aminoacidos para acelerar emergencia",
         remedy_type="biologico", remedy_name="Aminoacidos hidrolizados",
         formula="L-aminoacidos (mezcla)", dose="2-3 L/ha al suelo o foliar", application="foliar",
         notes="Los aminoacidos activan enzimas de germination a temperaturas suboptimas"),

    # ════════════════════════════════════════════════════════════════════
    # LUZ (TSL2561) — ALTA
    # ════════════════════════════════════════════════════════════════════
    dict(crop="Todos", variable="light_lux", condition="alto", severity="leve",
         problem="Intensidad luminica sobre el optimo del cultivo",
         consequence="Fotoinhicion, quemadura foliar incipiente",
         action="Instalar malla sombra del 20-30%",
         remedy_type="cultural", remedy_name="Malla sombra 20-30%",
         formula="-", dose="20-30% reduccion luminica", application="instalacion",
         notes="Orientar el sombreado para las horas de mayor irradiacion (10:00-15:00)"),

    dict(crop="Todos", variable="light_lux", condition="alto", severity="moderado",
         problem="Exceso de luz provoca fotooxidacion de clorofila",
         consequence="Blanqueamiento foliar, reduccion de fotosintesis neta",
         action="Malla sombra 40-50% + kaolin foliar",
         remedy_type="quimico", remedy_name="Kaolin micronizado",
         formula="Al2Si2O5(OH)4", dose="3 kg/100 L agua", application="foliar",
         notes="Aplicar 2-3 coberturas semanales en temporada seca"),

    dict(crop="Cafe", variable="light_lux", condition="alto", severity="moderado",
         problem="Cafe expuesto a pleno sol supera su optimo de sombra",
         consequence="Maduracion acelerada y despareja, grano de menor calidad",
         action="Siembra o poda de arboles de sombra (Inga spp.)",
         remedy_type="cultural", remedy_name="Arboles de sombra (Inga sp.)",
         formula="-", dose="1 arbol por 4-6 plantas de cafe", application="instalacion",
         notes="Inga vera fija nitrogeno ademas de dar sombra"),

    dict(crop="Cacao", variable="light_lux", condition="alto", severity="moderado",
         problem="Cacao muy sensible a luz directa intensa",
         consequence="Quemadura de hoja, caida de mazorcas jovenes",
         action="Sombra temporal con palma o platano + magnesio foliar",
         remedy_type="fertilizante", remedy_name="Sulfato de magnesio (Sal de Epsom)",
         formula="MgSO4·7H2O", dose="2-3 kg/100 L agua", application="foliar",
         notes="El Mg es el nucleo de la clorofila; protege contra fotodegradacion"),

    # ════════════════════════════════════════════════════════════════════
    # LUZ (TSL2561) — BAJA
    # ════════════════════════════════════════════════════════════════════
    dict(crop="Todos", variable="light_lux", condition="bajo", severity="leve",
         problem="Luz insuficiente para fotosintesis optima",
         consequence="Etiolacion, crecimiento elongado y debil",
         action="Poda de arboles que generan sombra excesiva",
         remedy_type="cultural", remedy_name="Poda de sombra",
         formula="-", dose="Reducir sombra al nivel optimo del cultivo", application="instalacion",
         notes="Realizar en inicio de temporada lluviosa para evitar quemadura"),

    dict(crop="Todos", variable="light_lux", condition="bajo", severity="moderado",
         problem="Deficit luminico significativo afecta produccion",
         consequence="Reduccion de floracion y fructificacion, mayor susceptibilidad a hongos",
         action="Poda de sombra + aplicacion de potasio para eficiencia fotosintetica",
         remedy_type="fertilizante", remedy_name="Sulfato de potasio",
         formula="K2SO4 (0-0-50)", dose="5 kg/ha foliar al 0.5%", application="foliar",
         notes="El potasio optimiza el uso de la luz disponible"),

    dict(crop="Tomate", variable="light_lux", condition="bajo", severity="moderado",
         problem="Tomate requiere alta luminosidad para cuajado",
         consequence="Frutos palidos, poco solidos solubles (Brix bajo)",
         action="Reflexion con mulch plateado + citocininas para cuajado",
         remedy_type="biologico", remedy_name="Citocininas (alga Ascophyllum nodosum)",
         formula="Citocininas naturales", dose="2-3 mL/L agua", application="foliar",
         notes="El extracto de alga marina estimula division celular con poca luz"),

    # ════════════════════════════════════════════════════════════════════
    # HUMEDAD DEL SUELO (Higrómetro) — ALTA
    # ════════════════════════════════════════════════════════════════════
    dict(crop="Todos", variable="soil_moisture", condition="alto", severity="leve",
         problem="Suelo levemente encharcado, inicio de anaerobiosis radicular",
         consequence="Reduccion de absorcion de nutrientes, inicio de pudricion radicular",
         action="Suspender riego y mejorar drenaje superficial",
         remedy_type="cultural", remedy_name="Drenaje superficial",
         formula="-", dose="Zanjas de 20-30 cm de profundidad", application="drenaje",
         notes="Verificar que el suelo tenga al menos 2% de pendiente para drenaje natural"),

    dict(crop="Todos", variable="soil_moisture", condition="alto", severity="moderado",
         problem="Encharcamiento moderado, hongos radiculares activos",
         consequence="Damping-off, Pythium spp., Phytophthora spp.",
         action="Fungicida sistemico radicular + drenaje urgente",
         remedy_type="quimico", remedy_name="Metalaxil + Mancozeb (Ridomil Gold MZ)",
         formula="Metalaxil-M 4% + Mancozeb 64%", dose="2.5 kg/ha suelo o 250 g/100 L agua", application="suelo",
         notes="Aplicar al suelo o como drench; efectivo contra Oomicetos (Phytophthora, Pythium)"),

    dict(crop="Todos", variable="soil_moisture", condition="alto", severity="severo",
         problem="Encharcamiento severo, muerte inminente de raices",
         consequence="Pudricion radicular total, muerte de planta en 3-7 dias",
         action="Drenaje de emergencia + Fosetil aluminio + camas elevadas",
         remedy_type="quimico", remedy_name="Fosetil aluminio (Aliette)",
         formula="Al(C2H5O3P) — Fosetil-Al 80%", dose="200-300 g/100 L agua", application="foliar",
         notes="Accion sistemica ascendente y descendente; activa defensas de la planta"),

    dict(crop="Papa", variable="soil_moisture", condition="alto", severity="moderado",
         problem="Tizón tardío (Phytophthora infestans) favorecido por humedad excesiva",
         consequence="Defoliacion rapida, pudricion de tuberculos en campo",
         action="Fungicida especifico Phytophthora + drenaje urgente",
         remedy_type="quimico", remedy_name="Dimetomorph + Mancozeb (Forum Star)",
         formula="Dimetomorph 9% + Mancozeb 60%", dose="200 g/100 L agua", application="foliar",
         notes="Rotar con oxicloruro de cobre para evitar resistencia. Aplicar cada 7 dias"),

    dict(crop="Cafe", variable="soil_moisture", condition="alto", severity="moderado",
         problem="Humedad excesiva favorece ojo de gallo (Mycena citricolor)",
         consequence="Defoliacion, perdida de produccion hasta 40%",
         action="Fungicida cuprico + mejorar drenaje entre surcos",
         remedy_type="quimico", remedy_name="Hidroxido de cobre (Kocide)",
         formula="Cu(OH)2", dose="200-250 g/100 L agua", application="foliar",
         notes="Aplicar preventivamente al inicio de la temporada lluviosa"),

    dict(crop="Tomate", variable="soil_moisture", condition="alto", severity="moderado",
         problem="Tizon temprano y tardio favorecidos por suelo saturado",
         consequence="Necrosis foliar ascendente, perdida total sin tratamiento",
         action="Clorotalonil + ajuste de riego a campo de capacidad",
         remedy_type="quimico", remedy_name="Clorotalonil (Bravo 720)",
         formula="Clorotalonil C8Cl4N2 — 72%", dose="200 mL/100 L agua", application="foliar",
         notes="Protectante de amplio espectro; no penetra tejidos, protege superficie foliar"),

    dict(crop="Frijol", variable="soil_moisture", condition="alto", severity="moderado",
         problem="Pudricion de raiz blanca (Sclerotium rolfsii) en suelo humedo",
         consequence="Volcamiento de plantas, perdida de hasta 80% en lotes afectados",
         action="PCNB o Trichoderma + suelo bien aireado",
         remedy_type="biologico", remedy_name="Trichoderma harzianum",
         formula="T. harzianum 1x10^8 UFC/g", dose="2-4 kg/ha en suelo", application="suelo",
         notes="Biocontrolador natural de Sclerotium, Fusarium y Rhizoctonia"),

    # ════════════════════════════════════════════════════════════════════
    # HUMEDAD DEL SUELO — BAJA (SEQUIA)
    # ════════════════════════════════════════════════════════════════════
    dict(crop="Todos", variable="soil_moisture", condition="bajo", severity="leve",
         problem="Inicio de deficit hidrico en zona radicular",
         consequence="Cierre estomatico, reduccion de fotosintesis y crecimiento",
         action="Riego de recuperacion + mulching para retener humedad",
         remedy_type="cultural", remedy_name="Mulch de material organico",
         formula="-", dose="5-10 cm de espesor alrededor de la planta", application="suelo",
         notes="La paja, cascarilla de cafe o plastico negro reducen evaporacion hasta 60%"),

    dict(crop="Todos", variable="soil_moisture", condition="bajo", severity="moderado",
         problem="Estres hidrico moderado, marchitez visible en horas pico",
         consequence="Caida de frutos, disminucion de calidad y rendimiento",
         action="Riego urgente + aplicacion de polimeros hidroretentores",
         remedy_type="quimico", remedy_name="Poliacrilamida hidroretentor (Stockosorb)",
         formula="Poliacrilamida potasica reticulada", dose="3-5 kg/m3 de suelo", application="suelo",
         notes="Retiene hasta 400 veces su peso en agua; reduce frecuencia de riego 30-50%"),

    dict(crop="Todos", variable="soil_moisture", condition="bajo", severity="severo",
         problem="Estres hidrico severo, marchitez permanente inminente",
         consequence="Muerte de plantas, perdida total del cultivo",
         action="Riego de choque + silicato de potasio + bioestimulante antistres",
         remedy_type="quimico", remedy_name="Silicato de potasio + extracto de algas",
         formula="K2SiO3 + Ascophyllum nodosum", dose="2 mL/L + 3 mL/L agua", application="foliar",
         notes="El silicio cierra estomas para reducir perdida de agua; las algas reducen dano oxidativo"),

    dict(crop="Cafe", variable="soil_moisture", condition="bajo", severity="moderado",
         problem="Cafe necesita florecimiento uniforme con estres hidrico controlado",
         consequence="Floracion desuniforme, cosecha escalonada y dificil",
         action="Riego deficitario controlado (70% campo capacidad) durante diferenciacion floral",
         remedy_type="riego", remedy_name="Riego deficitario controlado (RDC)",
         formula="-", dose="70% de la evapotranspiracion de referencia", application="fertirriego",
         notes="El estres leve unifica floracion; NO aplicar en formacion de frutos"),

    dict(crop="Maiz", variable="soil_moisture", condition="bajo", severity="moderado",
         problem="Sequia en maiz durante espigamiento y llenado de grano",
         consequence="Aborto de espiga, grano arrugado, perdida de hasta 70% rendimiento",
         action="Riego de emergencia + potasio para eficiencia hidrica",
         remedy_type="fertilizante", remedy_name="Cloruro de potasio",
         formula="KCl (0-0-60)", dose="150-200 kg/ha al suelo", application="suelo",
         notes="El potasio es el nutriente mas ligado a la eficiencia en el uso del agua"),

    # ════════════════════════════════════════════════════════════════════
    # INDICE DE VERDOR (TCS3200) — BAJO (Clorosis)
    # ════════════════════════════════════════════════════════════════════
    dict(crop="Todos", variable="greenness_idx", condition="bajo", severity="leve",
         problem="Clorosis leve, posible deficiencia de nitrogeno o magnesio",
         consequence="Reduccion de capacidad fotosintetica, crecimiento lento",
         action="Aplicacion foliar de urea + sulfato de magnesio",
         remedy_type="fertilizante", remedy_name="Urea + Sulfato de magnesio",
         formula="CO(NH2)2 46% N + MgSO4·7H2O", dose="3 kg urea + 2 kg MgSO4 / 100 L agua", application="foliar",
         notes="La urea foliar es de rapida absorcion; el Mg activa la clorofila"),

    dict(crop="Todos", variable="greenness_idx", condition="bajo", severity="moderado",
         problem="Clorosis internerval moderada: posible deficiencia de hierro o manganeso",
         consequence="Hojas amarillas con nervios verdes, necrosis marginal en casos avanzados",
         action="Aplicar quelato de hierro + sulfato de manganeso al suelo y foliar",
         remedy_type="fertilizante", remedy_name="Quelato de hierro EDDHA + Sulfato de manganeso",
         formula="Fe-EDDHA (6% Fe) + MnSO4·H2O (32% Mn)", dose="3-5 kg/ha + 1 kg/ha", application="suelo",
         notes="El Fe-EDDHA es el quelato mas estable en suelos alcalinos; aplicar al suelo mojado"),

    dict(crop="Todos", variable="greenness_idx", condition="bajo", severity="severo",
         problem="Clorosis severa o necrosis foliar generalizada",
         consequence="Colapso fotosintetico, muerte inminente de la planta",
         action="Plan de emergencia nutricional: NPK completo + microelementos via fertirriego",
         remedy_type="fertilizante", remedy_name="NPK 20-20-20 + micronutrientes",
         formula="N 20% + P2O5 20% + K2O 20% + microelementos quelatados", dose="2-3 kg/1000 L agua", application="fertirriego",
         notes="Aplicar cada 5-7 dias hasta recuperacion; complementar con Zn, B, Mo"),

    dict(crop="Todos", variable="greenness_idx", condition="bajo", severity="moderado",
         problem="Clorosis por deficiencia de zinc (Zn): hojas pequenas y deformes",
         consequence="Internudos cortos, 'roseta', reduccion severa de rendimiento",
         action="Sulfato de zinc foliar",
         remedy_type="fertilizante", remedy_name="Sulfato de zinc",
         formula="ZnSO4·7H2O (23% Zn)", dose="1-2 kg/100 L agua foliar", application="foliar",
         notes="El zinc es cofactor de mas de 300 enzimas; critico en suelos calcareos"),

    dict(crop="Maiz", variable="greenness_idx", condition="bajo", severity="moderado",
         problem="Clorosis internerval en maiz: probable deficiencia de zinc",
         consequence="Sindrome de 'hoja blanca', reduccion de 30-50% en rendimiento",
         action="Sulfato de zinc al suelo antes de siembra + foliar al inicio",
         remedy_type="fertilizante", remedy_name="Sulfato de zinc (ZnSO4)",
         formula="ZnSO4·7H2O", dose="20-40 kg/ha suelo o 1.5 kg/100 L foliar", application="suelo",
         notes="Guatemala tiene suelos con alta fijacion de Zn; aplicar con materia organica"),

    dict(crop="Cafe", variable="greenness_idx", condition="bajo", severity="moderado",
         problem="Clorosis en cafe: deficiencia de hierro en suelos alcalinos",
         consequence="Reduccion de produccion, debilitamiento general del arbusto",
         action="Quelato de hierro + reducir pH del suelo con azufre",
         remedy_type="fertilizante", remedy_name="Quelato de hierro Fe-DTPA + Azufre",
         formula="Fe-DTPA (10% Fe) + S elemental (99%)", dose="5 L/ha + 200 kg/ha", application="suelo",
         notes="En cafe de sombra el pH tiende a subir; mantener entre 5.5-6.0"),

    dict(crop="Papa", variable="greenness_idx", condition="bajo", severity="leve",
         problem="Clorosis leve en papa: probable deficiencia de magnesio",
         consequence="Reduccion de tamano de tuberculos y contenido de almidon",
         action="Sulfato de magnesio foliar (Sal de Epsom)",
         remedy_type="fertilizante", remedy_name="Sulfato de magnesio (Sal de Epsom)",
         formula="MgSO4·7H2O (10% Mg, 13% S)", dose="2-3 kg/100 L agua", application="foliar",
         notes="Aplicar en horas frescas; el Mg se mueve a hojas jovenes cuando es deficiente"),

    dict(crop="Tomate", variable="greenness_idx", condition="bajo", severity="moderado",
         problem="Amarillamiento en tomate: deficiencia de nitrogeno en etapa de fructificacion",
         consequence="Frutos pequenos, bajo contenido de solidos solubles",
         action="Nitrato de calcio via fertirriego + foliar de aminoacidos",
         remedy_type="fertilizante", remedy_name="Nitrato de calcio + Aminoacidos",
         formula="Ca(NO3)2 (15.5% N, 19% Ca) + aminoacidos", dose="4-6 kg/1000 L agua", application="fertirriego",
         notes="El calcio previene podredumbre apical; el N-NO3 es de rapida absorcion"),

    # ════════════════════════════════════════════════════════════════════
    # pH DEL SUELO — BAJO (ACIDO)
    # ════════════════════════════════════════════════════════════════════
    dict(crop="Todos", variable="soil_ph", condition="bajo", severity="leve",
         problem="Suelo ligeramente acido, posible toxicidad por aluminio",
         consequence="Reduccion de disponibilidad de fosforo, calcio y magnesio",
         action="Encalado con cal agricola (CaCO3)",
         remedy_type="quimico", remedy_name="Cal agricola (Carbonato de calcio)",
         formula="CaCO3 (calcio 40%)", dose="1-2 ton/ha incorporado al suelo", application="suelo",
         notes="Aplicar 2-3 meses antes de la siembra; incorporar con labranza a 20 cm"),

    dict(crop="Todos", variable="soil_ph", condition="bajo", severity="moderado",
         problem="Acidez moderada del suelo, alta saturacion de aluminio y manganeso",
         consequence="Toxicidad por Al y Mn, raices deformadas, bloqueo de nutrientes",
         action="Cal dolomitica para corregir pH y aportar Ca y Mg",
         remedy_type="quimico", remedy_name="Cal dolomitica",
         formula="CaMg(CO3)2 (Ca 21%, Mg 12%)", dose="2-4 ton/ha", application="suelo",
         notes="La cal dolomitica corrige pH y aporta calcio y magnesio simultaneamente"),

    dict(crop="Todos", variable="soil_ph", condition="bajo", severity="severo",
         problem="Acidez severa, pH menor de 4.5, suelo toxicamente acido",
         consequence="Muerte radicular, imposibilidad de absorcion de nutrientes",
         action="Cal viva + cal dolomitica + materia organica para tamponamiento",
         remedy_type="quimico", remedy_name="Cal viva (Oxido de calcio)",
         formula="CaO (oxido de calcio, reaccion rapida)", dose="1-2 ton/ha (USAR CON PRECAUCION)", application="suelo",
         notes="La cal viva reacciona rapidamente pero puede quemar la planta; aplicar 6 sem antes"),

    dict(crop="Papa", variable="soil_ph", condition="bajo", severity="leve",
         problem="Papa tolera acidez moderada pero la sarna comun empeora bajo pH 5.2",
         consequence="Lesiones en tuberculos, reduccion de calidad comercial",
         action="Mantener pH en 5.0-5.5 SIN encalar en exceso (controla Streptomyces scabies)",
         remedy_type="cultural", remedy_name="pH optimo 5.0-5.5 para papa",
         formula="-", dose="No encalar si pH > 5.0 en papa", application="suelo",
         notes="La papa PREFIERE suelo acido para evitar sarna comun; no exceder pH 6.5"),

    dict(crop="Cafe", variable="soil_ph", condition="bajo", severity="moderado",
         problem="pH muy bajo en suelo cafetalero afecta disponibilidad de fosforo",
         consequence="Deficiencia de P y Ca, reduccion de produccion",
         action="Cal dolomitica en dosis moderada para llevar a pH 5.5-6.0",
         remedy_type="quimico", remedy_name="Cal dolomitica",
         formula="CaMg(CO3)2", dose="1-2 ton/ha", application="suelo",
         notes="Para cafe, el optimo es pH 5.5-6.5; no exceder pues favorece clorosis ferrica"),

    # ════════════════════════════════════════════════════════════════════
    # pH DEL SUELO — ALTO (ALCALINO)
    # ════════════════════════════════════════════════════════════════════
    dict(crop="Todos", variable="soil_ph", condition="alto", severity="leve",
         problem="Suelo ligeramente alcalino, inicio de bloqueo de micronutrientes",
         consequence="Disponibilidad reducida de Fe, Mn, Zn, B y Cu",
         action="Azufre elemental para acidificar gradualmente el suelo",
         remedy_type="quimico", remedy_name="Azufre elemental (S)",
         formula="S (99.5%)", dose="200-400 kg/ha incorporado", application="suelo",
         notes="Las bacterias Thiobacillus convierten el azufre en acido sulfurico; tarda 4-8 semanas"),

    dict(crop="Todos", variable="soil_ph", condition="alto", severity="moderado",
         problem="Suelo moderadamente alcalino, clorosis ferrica generalizada",
         consequence="Hojas amarillas con nervios verdes, bajo rendimiento",
         action="Sulfato de aluminio + quelato de hierro para corrección rapida",
         remedy_type="quimico", remedy_name="Sulfato de aluminio",
         formula="Al2(SO4)3·18H2O", dose="500-1000 kg/ha incorporado", application="suelo",
         notes="Accion mas rapida que azufre elemental; bajar pH 1 unidad requiere aprox 500 kg/ha"),

    dict(crop="Todos", variable="soil_ph", condition="alto", severity="severo",
         problem="Suelo fuertemente alcalino (pH > 8.0), posible sodificacion",
         consequence="Destruccion de estructura del suelo, salinidad, imposibilidad de cultivo",
         action="Yeso agricola + azufre + riego de lavado intensivo",
         remedy_type="quimico", remedy_name="Yeso agricola (Sulfato de calcio)",
         formula="CaSO4·2H2O", dose="2-5 ton/ha + riego abundante", application="suelo",
         notes="El yeso desplaza el sodio del complejo de cambio; el riego lo lava hacia capas profundas"),

    dict(crop="Tomate", variable="soil_ph", condition="alto", severity="moderado",
         problem="pH alto bloquea calcio disponible para el tomate",
         consequence="Podredumbre apical (Blossom End Rot) por deficiencia de Ca funcional",
         action="Nitrato de calcio foliar + acidificante del suelo",
         remedy_type="fertilizante", remedy_name="Nitrato de calcio foliar",
         formula="Ca(NO3)2 (15.5% N, 19% Ca)", dose="3-4 kg/1000 L agua", application="foliar",
         notes="Aplicar en horas frescas; el calcio se mueve poco en la planta, aplicacion foliar es clave"),

    # ════════════════════════════════════════════════════════════════════
    # HUMEDAD RELATIVA — ALTA
    # ════════════════════════════════════════════════════════════════════
    dict(crop="Todos", variable="humidity", condition="alto", severity="leve",
         problem="Humedad relativa alta, riesgo de enfermedades fungicas",
         consequence="Proliferacion de esporas, inicio de infecciones foliares",
         action="Mejorar ventilacion del cultivo + fungicida preventivo cuprico",
         remedy_type="quimico", remedy_name="Oxicloruro de cobre",
         formula="Cu2(OH)3Cl (84.2% Cu-equiv.)", dose="250-300 g/100 L agua", application="foliar",
         notes="El cobre es bactericida y fungicida; evitar aplicar bajo lluvia"),

    dict(crop="Todos", variable="humidity", condition="alto", severity="moderado",
         problem="Humedad alta sostenida, enfermedades fungicas establecidas",
         consequence="Mildiu, Botritis, Alternaria, reduccion severa de rendimiento",
         action="Fungicida sistemico (triazol o estrobirulina) + mejorar drenaje",
         remedy_type="quimico", remedy_name="Propiconazol (Tilt)",
         formula="Propiconazol C15H17Cl2N3O2 — 25% EC", dose="50-60 mL/100 L agua", application="foliar",
         notes="Sistemico protectante y curativo; respetar intervalo de seguridad 14 dias"),

    dict(crop="Cafe", variable="humidity", condition="alto", severity="moderado",
         problem="HR > 85% en cafe activa roya del cafe (Hemileia vastatrix)",
         consequence="Defoliacion masiva, perdida de hasta 60% de la cosecha",
         action="Triadimenol + Oxicloruro de cobre en mezcla preventiva",
         remedy_type="quimico", remedy_name="Triadimenol (Bayleton) + Cobre",
         formula="Triadimenol 25% WP + Cu2(OH)3Cl", dose="75 g + 300 g / 100 L agua", application="foliar",
         notes="Iniciar aplicaciones preventivas al inicio de lluvias; cada 21-28 dias"),

    dict(crop="Frijol", variable="humidity", condition="alto", severity="moderado",
         problem="Antracnosis (Colletotrichum lindemuthianum) con HR alta",
         consequence="Manchas en vainas y granos, perdida de calidad comercial",
         action="Mancozeb preventivo + azufre humectable",
         remedy_type="quimico", remedy_name="Mancozeb (Dithane M-45)",
         formula="Mancozeb C4H6MnN2S4·xZn — 80% WP", dose="200-250 g/100 L agua", application="foliar",
         notes="Protectante de contacto; aplicar antes de la lluvia para mayor persistencia"),

    # ════════════════════════════════════════════════════════════════════
    # HUMEDAD RELATIVA — BAJA
    # ════════════════════════════════════════════════════════════════════
    dict(crop="Todos", variable="humidity", condition="bajo", severity="moderado",
         problem="Humedad baja favorece acaros e insectos chupadores",
         consequence="Araña roja (Tetranychus urticae), trips, daño foliar",
         action="Riego por aspersion para aumentar HR + acaricida si hay infestacion",
         remedy_type="quimico", remedy_name="Abamectina (Vertimec)",
         formula="Abamectina B1a+B1b — 1.8% EC", dose="40-60 mL/100 L agua", application="foliar",
         notes="La abamectina es efectiva contra acaros y trips; origen biologico (Streptomyces)"),

    dict(crop="Todos", variable="humidity", condition="bajo", severity="leve",
         problem="Baja humedad relativa aumenta transpiracion excesiva",
         consequence="Cierre estomatico, estres hidrico incluso con suelo humedo",
         action="Riego por aspersion en horas criticas + silicato de potasio",
         remedy_type="quimico", remedy_name="Silicato de potasio",
         formula="K2SiO3", dose="1-2 mL/L agua", application="foliar",
         notes="El silicio reduce la transpiracion y mejora la eficiencia en el uso del agua"),

    # ════════════════════════════════════════════════════════════════════
    # PRECIPITACION / RAINFALL — ALTA
    # ════════════════════════════════════════════════════════════════════
    dict(crop="Todos", variable="rainfall", condition="alto", severity="moderado",
         problem="Lluvia excesiva lava nutrientes del suelo (lixiviacion)",
         consequence="Deficiencia de N, K y micronutrientes moviles; perdida economica",
         action="Fertirrigacion de recuperacion con NPK + boro para sustituir lixiviados",
         remedy_type="fertilizante", remedy_name="NPK 20-10-20 + Boron",
         formula="N 20% + P2O5 10% + K2O 20% + B 0.02%", dose="3 kg/1000 L agua", application="fertirriego",
         notes="Aplicar 24-48 horas despues de la lluvia intensa; el boro se lixivia facilmente"),

    dict(crop="Todos", variable="rainfall", condition="alto", severity="severo",
         problem="Lluvias torrenciales, riesgo de inundacion y erosion",
         consequence="Arrastre de suelo fertil, dano mecanico a plantas, pudricion",
         action="Drenaje de emergencia + fungicida sistemico + enmienda calcarea post-lluvia",
         remedy_type="quimico", remedy_name="Fosetil aluminio (Aliette) + Cal dolomitica",
         formula="Fosetil-Al 80% + CaMg(CO3)2", dose="200 g/100 L agua + 500 kg/ha", application="foliar",
         notes="El fosetil activa mecanismos de defensa de la planta contra Oomicetos"),

    # ════════════════════════════════════════════════════════════════════
    # PRECIPITACION / RAINFALL — BAJA
    # ════════════════════════════════════════════════════════════════════
    dict(crop="Todos", variable="rainfall", condition="bajo", severity="moderado",
         problem="Sequia prolongada, deficit hidrico acumulado",
         consequence="Paralisis del crecimiento, caida de frutos, reduccion de rendimiento",
         action="Riego suplementario + mulching + bioestimulante antistres",
         remedy_type="biologico", remedy_name="Extracto de algas (Ascophyllum nodosum)",
         formula="Betainas, citocininas, acido algínico", dose="3-5 mL/L agua", application="foliar",
         notes="Las betainas del alga marina actuan como osmoprotectores en sequia"),

    dict(crop="Maiz", variable="rainfall", condition="bajo", severity="moderado",
         problem="Sequia en maiz en periodo critico de espigamiento",
         consequence="Aborto de espiga, maiz sin grano, hasta 80% de perdida",
         action="Riego de emergencia inmediato + potasio para eficiencia hidrica",
         remedy_type="riego", remedy_name="Riego de emergencia + K2SO4",
         formula="K2SO4 (0-0-50)", dose="Riego al 100% ETc + 10 kg/ha K2SO4 foliar", application="fertirriego",
         notes="CRITICO: el deficit en espigamiento es irreversible; actuar en menos de 48 horas"),

]


def build_dataframe() -> pd.DataFrame:
    return pd.DataFrame(RECS)


def save_csv(path: str):
    df = build_dataframe()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    return df


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "datasets", "recommendations.csv")
    df  = save_csv(out)
    print(f"Recomendaciones guardadas: {out}")
    print(f"Total entradas : {len(df)}")
    print(f"Variables      : {df['variable'].unique().tolist()}")
    print(f"Severidades    : {df['severity'].value_counts().to_dict()}")
    print(f"Tipos remedio  : {df['remedy_type'].value_counts().to_dict()}")
