import { cropOptions } from "../data/constants";

export function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

export function calculateRisk(entry) {
  // Cada componente suma puntos de riesgo: 0 = condición ideal, mayor = más riesgo.
  // Rango ideal por variable definido con base en agronomía tropical Guatemala.

  const rainfallScore =
    entry.rainfall > 150 ? 35 :
    entry.rainfall > 100 ? 20 :
    entry.rainfall >= 50 && entry.rainfall <= 100 ? 0 :   // rango óptimo
    entry.rainfall >= 30 ? 15 : 28;                        // seco / muy seco

  const temperatureScore =
    entry.temperature >= 34 ? 32 :
    entry.temperature >= 30 ? 18 :
    entry.temperature <= 14 ? 28 :
    entry.temperature <= 18 ? 10 :
    entry.temperature >= 20 && entry.temperature <= 28 ? 0 : 5; // ideal 20-28°C

  const humidityScore =
    entry.humidity >= 88 ? 28 :
    entry.humidity >= 80 ? 8  :
    entry.humidity < 40  ? 28 :
    entry.humidity < 55  ? 16 :
    entry.humidity >= 60 && entry.humidity <= 78 ? 0 : 5;  // ideal 60-78%

  const phScore =
    entry.soilPh < 4.5  ? 32 :
    entry.soilPh < 5.5  ? 18 :
    entry.soilPh > 8.0  ? 28 :
    entry.soilPh > 7.2  ? 12 :
    entry.soilPh >= 6.0 && entry.soilPh <= 7.0 ? 0 : 5;   // ideal 6.0-7.0

  const cropFactor = {
    Maiz: 3, Frijol: 2, Cafe: 5, Arroz: 4,
    Papa: 4, Tomate: 6, Aguacate: 5, Cacao: 4,
  }[entry.crop] ?? 3;

  const score = clamp(rainfallScore + temperatureScore + humidityScore + phScore + cropFactor, 0, 100);
  const level = score >= 55 ? "high" : score <= 18 ? "low" : "medium";
  return { score, level };
}

export function getRiskLabel(level) {
  return { low: "Riesgo bajo", medium: "Riesgo medio", high: "Riesgo alto" }[level];
}

export function getRecommendation(entry, risk) {
  if (entry.crop === "Cafe" && risk.level === "high")
    return "Aplicar monitoreo fitosanitario intensivo y mejorar ventilacion del lote por humedad elevada.";
  if (entry.crop === "Maiz" && entry.temperature >= 30)
    return "Ajustar riego suplementario y revisar cobertura de suelo para mitigar estres termico.";
  if (entry.crop === "Frijol" && entry.humidity >= 70)
    return "Incrementar vigilancia de enfermedades fungicas y evitar exceso de humedad en superficie.";
  if (entry.crop === "Tomate" && entry.soilPh > 7.2)
    return "Corregir alcalinidad del suelo y reforzar nutricion balanceada para evitar perdida de vigor.";
  if (entry.crop === "Papa" && entry.soilPh < 5.6)
    return "Evaluar encalado parcial y seguimiento sanitario del suelo antes de la siguiente ventana de manejo.";
  if (risk.level === "low")
    return "Mantener seguimiento rutinario; las condiciones actuales son estables para el cultivo.";
  return "Mantener observacion semanal, validar drenaje, revisar balance de pH y actualizar metricas climaticas para afinar la prediccion.";
}

export function buildAlerts(dataset) {
  const order = { high: 0, medium: 1, low: 2 };
  return dataset
    .map((entry) => {
      const risk = calculateRisk(entry);
      return {
        level: risk.level,
        text: `${getRiskLabel(risk.level)} en ${entry.crop} de ${entry.municipality}: precipitacion ${entry.rainfall} mm, temperatura ${entry.temperature}\u00b0C, humedad ${entry.humidity}% y pH ${entry.soilPh}.`,
      };
    })
    .sort((a, b) => order[a.level] - order[b.level])
    .slice(0, 4);
}

export function getAverageRiskByCrop(dataset) {
  return cropOptions.map((crop) => {
    const rows = dataset.filter((e) => e.crop === crop);
    if (!rows.length) return 0;
    return Math.round(rows.reduce((sum, e) => sum + calculateRisk(e).score, 0) / rows.length);
  });
}
