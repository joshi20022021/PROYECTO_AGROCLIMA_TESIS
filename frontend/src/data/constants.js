export const cropOptions = [
  // Granos
  "Maiz", "Frijol", "Arroz", "Trigo", "Sorgo", "Avena", "Soya",
  // Hortalizas
  "Tomate", "Papa", "Zanahoria", "Cebolla", "Repollo", "Brocoli", "Coliflor",
  "Lechuga", "Espinaca", "Pepino", "Chile", "Berenjena", "Zucchini",
  // Frutas
  "Aguacate", "Mango", "Naranja", "Limon", "Banano", "Pina", "Papaya",
  "Melon", "Sandia", "Fresa",
  // Comerciales
  "Cafe", "Cacao", "Cana de azucar", "Cardamomo", "Mani",
  // Raices y tuberculos
  "Yuca", "Camote",
];

export const municipioOptions = [
  "Chimaltenango", "Sacatepequez", "Guatemala", "Escuintla",
  "Santa Rosa",    "Solola",       "Totonicapan", "Quetzaltenango",
  "Suchitepequez", "Retalhuleu",   "San Marcos",  "Huehuetenango",
  "Quiche",        "Baja Verapaz", "Coban",       "Peten",
  "Izabal",        "Zacapa",       "Chiquimula",  "Jalapa",
  "Jutiapa",       "El Progreso",
];

export const sections = {
  dashboard: {
    label: "Inicio",
    title: "Resumen General",
    subtitle: "Monitoreo multicultivo con variables climaticas, pH del suelo y prediccion de riesgo agricola.",
  },
  dataset: {
    label: "Metricas",
    title: "Metricas del Dataset",
    subtitle: "Registro de precipitacion, temperatura, humedad y pH del suelo por cultivo y municipio.",
  },
  alerts: {
    label: "Alertas",
    title: "Alertas y Acciones",
    subtitle: "Eventos de riesgo y recomendaciones operativas por cultivo y municipio.",
  },
  reports: {
    label: "Resultados",
    title: "Resultados Ejecutivos",
    subtitle: "Salida ejecutiva con indicadores, hallazgos y lectura operativa del analisis.",
  },
  forecast: {
    label: "Pronostico",
    title: "Pronostico del Clima",
    subtitle: "Pronostico de 7 dias con temperatura, lluvia y calculadora de riego y fertilizacion.",
  },
  arduino: {
    label: "Arduino",
    title: "Monitoreo en Tiempo Real",
    subtitle: "Lecturas vivas de temperatura, luz, verdor y humedad del suelo.",
  },
};

export const initialDataset = [
  { municipality: "Chimaltenango", crop: "Maiz",     rainfall: 78, temperature: 22, humidity: 76, soilPh: 6.2 },
  { municipality: "Chimaltenango", crop: "Frijol",   rainfall: 63, temperature: 21, humidity: 71, soilPh: 6.0 },
  { municipality: "Sacatepequez",  crop: "Cafe",     rainfall: 88, temperature: 20, humidity: 84, soilPh: 5.8 },
  { municipality: "Guatemala",     crop: "Tomate",   rainfall: 55, temperature: 26, humidity: 66, soilPh: 6.7 },
  { municipality: "Sacatepequez",  crop: "Aguacate", rainfall: 74, temperature: 19, humidity: 80, soilPh: 6.5 },
  { municipality: "Guatemala",     crop: "Maiz",     rainfall: 49, temperature: 27, humidity: 62, soilPh: 6.3 },
  { municipality: "Chimaltenango", crop: "Papa",     rainfall: 52, temperature: 18, humidity: 69, soilPh: 5.9 },
  { municipality: "Sacatepequez",  crop: "Cacao",    rainfall: 81, temperature: 21, humidity: 82, soilPh: 6.1 },
];

export const initialTrendSeries = {
  labels: ["Reg 1", "Reg 2", "Reg 3", "Reg 4", "Reg 5", "Reg 6"],
  rainfall:    [56, 62, 71, 68, 77, 82],
  temperature: [24, 25, 26, 27, 27, 28],
  humidity:    [60, 64, 67, 70, 72, 74],
};


export const defaultForm = {
  municipality: "Chimaltenango",
  crop: "Maiz",
  rainfall: "",
  temperature: "",
  humidity: "",
  soilPh: "",
  leafCondition: 65,
};

// Cultivos con los que fue entrenado el modelo XGBoost
export const TRAINED_CROPS = ["Aguacate", "Arroz", "Cacao", "Cafe", "Frijol", "Maiz", "Papa", "Tomate"];
