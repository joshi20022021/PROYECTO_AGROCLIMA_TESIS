"""
Cobertura nacional Guatemala — 22 departamentos, ~60 municipios.
Importado por era5_client.py, era5_extra.py, nasa_power_client.py
y build_source_csvs.py para mantener consistencia.

Criterios de selección:
    - Cabecera departamental de los 22 departamentos (cobertura mínima garantizada)
    - Municipios con vocación agrícola relevante (café, caña, cardamomo, etc.)
    - Distribución geográfica que cubra gradientes altitudinales y climáticos
    - Municipios en zonas fronterizas para capturar variabilidad extrema

Con 60 municipios × 12 meses × 17 años × 37 cultivos ≈ 450,000 registros de entrenamiento.

Zonas agroclimáticas cubiertas:
    altiplano_central   — tierras altas centrales (Chimaltenango, Sacatepéquez, Guatemala)
    altiplano_occidente — altiplano frío/lluvioso (Quetzaltenango, San Marcos, Huehuetenango, Totonicapán, Sololá, Quiché)
    costa_sur           — planicie costera caliente (Escuintla, Retalhuleu, Suchitepéquez, S. Rosa, Jutiapa-costa)
    boca_costa          — franja volcánica de transición (café/cacao)
    oriente_seco        — corredor seco del Motagua (Zacapa, Chiquimula, Jalapa, Jutiapa, El Progreso)
    verapaces           — zona húmeda interior (Alta y Baja Verapaz)
    peten_izabal        — trópico bajo húmedo (Petén, Izabal)
    noroccidente        — zona alta fronteriza con México (norte Huehuetenango, Quiché-Ixcán)
"""

MUNICIPIOS = {

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE GUATEMALA
    # ══════════════════════════════════════════════════════════════════
    "Guatemala":           {"lat": 14.6349, "lon": -90.5069, "depto": "Guatemala",      "zona": "altiplano_central",   "altitud_m": 1502},
    "Mixco":               {"lat": 14.6333, "lon": -90.6000, "depto": "Guatemala",      "zona": "altiplano_central",   "altitud_m": 1640},
    "Villa Nueva":         {"lat": 14.5250, "lon": -90.5833, "depto": "Guatemala",      "zona": "altiplano_central",   "altitud_m": 1330},
    "San Jose Pinula":     {"lat": 14.5500, "lon": -90.4167, "depto": "Guatemala",      "zona": "altiplano_central",   "altitud_m": 1680},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE EL PROGRESO
    # ══════════════════════════════════════════════════════════════════
    "Guastatoya":          {"lat": 14.8667, "lon": -90.0667, "depto": "El Progreso",    "zona": "oriente_seco",        "altitud_m":  428},
    "San Agustin Acasaguastlan": {"lat": 14.9417, "lon": -89.9667, "depto": "El Progreso", "zona": "oriente_seco",    "altitud_m":  270},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE SACATEPEQUEZ
    # ══════════════════════════════════════════════════════════════════
    "Sacatepequez":        {"lat": 14.5586, "lon": -90.7295, "depto": "Sacatepéquez",   "zona": "altiplano_central",   "altitud_m": 1530},
    "San Lucas Sacatepequez": {"lat": 14.6089, "lon": -90.6556, "depto": "Sacatepéquez", "zona": "altiplano_central", "altitud_m": 1910},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE CHIMALTENANGO
    # ══════════════════════════════════════════════════════════════════
    "Chimaltenango":       {"lat": 14.6614, "lon": -90.8197, "depto": "Chimaltenango",  "zona": "altiplano_central",   "altitud_m": 1800},
    "Patzun":              {"lat": 14.6861, "lon": -91.0111, "depto": "Chimaltenango",  "zona": "altiplano_central",   "altitud_m": 2240},
    "Tecpan":              {"lat": 14.7581, "lon": -90.9942, "depto": "Chimaltenango",  "zona": "altiplano_central",   "altitud_m": 2290},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE ESCUINTLA
    # ══════════════════════════════════════════════════════════════════
    "Escuintla":           {"lat": 14.3042, "lon": -90.7858, "depto": "Escuintla",      "zona": "costa_sur",           "altitud_m":  346},
    "Tiquisate":           {"lat": 14.2833, "lon": -91.3667, "depto": "Escuintla",      "zona": "costa_sur",           "altitud_m":   55},
    "Santa Lucia Cotzumalguapa": {"lat": 14.3333, "lon": -91.0167, "depto": "Escuintla", "zona": "costa_sur",          "altitud_m":  370},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE SANTA ROSA
    # ══════════════════════════════════════════════════════════════════
    "Cuilapa":             {"lat": 14.2792, "lon": -90.2969, "depto": "Santa Rosa",     "zona": "oriente_seco",        "altitud_m":  895},
    "Taxisco":             {"lat": 14.0667, "lon": -90.4667, "depto": "Santa Rosa",     "zona": "costa_sur",           "altitud_m":   30},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE SOLOLA
    # ══════════════════════════════════════════════════════════════════
    "Solola":              {"lat": 14.7757, "lon": -91.1825, "depto": "Sololá",         "zona": "altiplano_occidente", "altitud_m": 2113},
    "Santiago Atitlan":    {"lat": 14.6419, "lon": -91.2278, "depto": "Sololá",         "zona": "boca_costa",          "altitud_m": 1592},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE TOTONICAPAN
    # ══════════════════════════════════════════════════════════════════
    "Totonicapan":         {"lat": 14.9125, "lon": -91.3614, "depto": "Totonicapán",    "zona": "altiplano_occidente", "altitud_m": 2495},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE QUETZALTENANGO
    # ══════════════════════════════════════════════════════════════════
    "Quetzaltenango":      {"lat": 14.8436, "lon": -91.5178, "depto": "Quetzaltenango", "zona": "altiplano_occidente", "altitud_m": 2333},
    "Coatepeque":          {"lat": 14.7003, "lon": -91.8742, "depto": "Quetzaltenango", "zona": "costa_sur",           "altitud_m":  496},
    "San Juan Ostuncalco": {"lat": 14.8667, "lon": -91.6167, "depto": "Quetzaltenango", "zona": "boca_costa",          "altitud_m": 2510},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE SUCHITEPEQUEZ
    # ══════════════════════════════════════════════════════════════════
    "Mazatenango":         {"lat": 14.5327, "lon": -91.5022, "depto": "Suchitepéquez",  "zona": "boca_costa",          "altitud_m":  370},
    "Chicacao":            {"lat": 14.4500, "lon": -91.3333, "depto": "Suchitepéquez",  "zona": "boca_costa",          "altitud_m":  370},
    "Patulul":             {"lat": 14.4167, "lon": -91.1667, "depto": "Suchitepéquez",  "zona": "boca_costa",          "altitud_m":  550},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE RETALHULEU
    # ══════════════════════════════════════════════════════════════════
    "Retalhuleu":          {"lat": 14.5389, "lon": -91.6864, "depto": "Retalhuleu",     "zona": "costa_sur",           "altitud_m":  239},
    "Champerico":          {"lat": 14.3000, "lon": -91.9167, "depto": "Retalhuleu",     "zona": "costa_sur",           "altitud_m":    5},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE SAN MARCOS
    # ══════════════════════════════════════════════════════════════════
    "San Marcos":          {"lat": 14.9638, "lon": -91.7953, "depto": "San Marcos",     "zona": "altiplano_occidente", "altitud_m": 2398},
    "Malacatan":           {"lat": 14.9000, "lon": -92.0667, "depto": "San Marcos",     "zona": "boca_costa",          "altitud_m":  365},
    "Ayutla":              {"lat": 14.6833, "lon": -92.1667, "depto": "San Marcos",     "zona": "costa_sur",           "altitud_m":   40},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE HUEHUETENANGO
    # ══════════════════════════════════════════════════════════════════
    "Huehuetenango":       {"lat": 15.3195, "lon": -91.4712, "depto": "Huehuetenango",  "zona": "altiplano_occidente", "altitud_m": 1901},
    "Jacaltenango":        {"lat": 15.6500, "lon": -91.7167, "depto": "Huehuetenango",  "zona": "noroccidente",        "altitud_m": 1550},
    "Barillas":            {"lat": 15.7833, "lon": -91.3167, "depto": "Huehuetenango",  "zona": "noroccidente",        "altitud_m": 1375},
    "Nenton":              {"lat": 15.8000, "lon": -91.7667, "depto": "Huehuetenango",  "zona": "noroccidente",        "altitud_m": 1050},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE QUICHE
    # ══════════════════════════════════════════════════════════════════
    "Santa Cruz del Quiche": {"lat": 15.0294, "lon": -91.1500, "depto": "Quiché",      "zona": "altiplano_occidente", "altitud_m": 2021},
    "Chichicastenango":    {"lat": 14.9444, "lon": -91.1153, "depto": "Quiché",         "zona": "altiplano_occidente", "altitud_m": 2073},
    "Ixcan":               {"lat": 15.8333, "lon": -90.7500, "depto": "Quiché",         "zona": "noroccidente",        "altitud_m":  170},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE BAJA VERAPAZ
    # ══════════════════════════════════════════════════════════════════
    "Salama":              {"lat": 15.1000, "lon": -90.3167, "depto": "Baja Verapaz",   "zona": "verapaces",           "altitud_m":  970},
    "Rabinal":             {"lat": 15.0833, "lon": -90.4833, "depto": "Baja Verapaz",   "zona": "verapaces",           "altitud_m": 1060},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE ALTA VERAPAZ
    # ══════════════════════════════════════════════════════════════════
    "Coban":               {"lat": 15.4719, "lon": -90.3722, "depto": "Alta Verapaz",   "zona": "verapaces",           "altitud_m": 1316},
    "San Pedro Carcha":    {"lat": 15.4789, "lon": -90.2867, "depto": "Alta Verapaz",   "zona": "verapaces",           "altitud_m": 1350},
    "Cahabon":             {"lat": 15.6000, "lon": -89.8167, "depto": "Alta Verapaz",   "zona": "verapaces",           "altitud_m":  200},
    "Fray Bartolome":      {"lat": 15.8333, "lon": -89.8667, "depto": "Alta Verapaz",   "zona": "peten_izabal",        "altitud_m":  120},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE PETEN
    # ══════════════════════════════════════════════════════════════════
    "Flores":              {"lat": 16.9333, "lon": -89.8833, "depto": "Petén",          "zona": "peten_izabal",        "altitud_m":  127},
    "San Luis Peten":      {"lat": 16.1833, "lon": -89.4333, "depto": "Petén",          "zona": "peten_izabal",        "altitud_m":  170},
    "Poptun":              {"lat": 16.3167, "lon": -89.4167, "depto": "Petén",          "zona": "peten_izabal",        "altitud_m":  430},
    "La Libertad Peten":   {"lat": 16.7833, "lon": -90.1167, "depto": "Petén",          "zona": "peten_izabal",        "altitud_m":  140},
    "Sayaxche":            {"lat": 16.5333, "lon": -90.1833, "depto": "Petén",          "zona": "peten_izabal",        "altitud_m":  110},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE IZABAL
    # ══════════════════════════════════════════════════════════════════
    "Puerto Barrios":      {"lat": 15.7167, "lon": -88.6000, "depto": "Izabal",         "zona": "peten_izabal",        "altitud_m":    3},
    "Livingston":          {"lat": 15.8333, "lon": -88.7500, "depto": "Izabal",         "zona": "peten_izabal",        "altitud_m":    5},
    "Morales":             {"lat": 15.4667, "lon": -88.8167, "depto": "Izabal",         "zona": "peten_izabal",        "altitud_m":   30},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE ZACAPA
    # ══════════════════════════════════════════════════════════════════
    "Zacapa":              {"lat": 14.9719, "lon": -89.5283, "depto": "Zacapa",         "zona": "oriente_seco",        "altitud_m":  230},
    "Gualan":              {"lat": 15.1167, "lon": -89.3667, "depto": "Zacapa",         "zona": "oriente_seco",        "altitud_m":  130},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE CHIQUIMULA
    # ══════════════════════════════════════════════════════════════════
    "Chiquimula":          {"lat": 14.7986, "lon": -89.5478, "depto": "Chiquimula",     "zona": "oriente_seco",        "altitud_m":  424},
    "Esquipulas":          {"lat": 14.5667, "lon": -89.3500, "depto": "Chiquimula",     "zona": "oriente_seco",        "altitud_m":  1000},
    "Jocotan":             {"lat": 14.8167, "lon": -89.4000, "depto": "Chiquimula",     "zona": "oriente_seco",        "altitud_m":  430},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE JALAPA
    # ══════════════════════════════════════════════════════════════════
    "Jalapa":              {"lat": 14.6333, "lon": -89.9833, "depto": "Jalapa",         "zona": "oriente_seco",        "altitud_m": 1363},
    "Mataquescuintla":     {"lat": 14.5333, "lon": -90.1833, "depto": "Jalapa",         "zona": "oriente_seco",        "altitud_m": 1620},

    # ══════════════════════════════════════════════════════════════════
    # DEPARTAMENTO DE JUTIAPA
    # ══════════════════════════════════════════════════════════════════
    "Jutiapa":             {"lat": 14.2929, "lon": -89.8967, "depto": "Jutiapa",        "zona": "oriente_seco",        "altitud_m":  905},
    "Asuncion Mita":       {"lat": 14.3333, "lon": -89.7167, "depto": "Jutiapa",        "zona": "oriente_seco",        "altitud_m":  500},
    "El Progreso Jutiapa": {"lat": 14.3500, "lon": -89.9333, "depto": "Jutiapa",        "zona": "oriente_seco",        "altitud_m":  860},

}

# Bounding box que cubre los 60 municipios con margen [N, W, S, E]
# Petén norte: 16.93°N | Nentón/Barillas: 15.80°N | Ayutla: 14.68°N, -92.17°W
# Puerto Barrios: -88.60°W | Taxisco/costa: 14.07°N
AREA_BBOX_NACIONAL = [17.2, -92.3, 13.9, -88.3]
