const BASE_URL = "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Error en la API");
  }
  return res.json();
}

export async function getHealth() {
  return request("/health");
}

export async function getMetrics() {
  return request("/metrics");
}

export async function predictYield({ municipio, crop, month, temperature, rainfall, humidity, soilPh, soilMoisture = 0.28 }) {
  return request("/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      municipio,
      crop,
      month,
      temperature,
      rainfall,
      humidity,
      soil_ph:       soilPh,
      soil_moisture: soilMoisture,
    }),
  });
}

export async function predictMultiCrop({ municipio, crop, month, temperature, rainfall, humidity, soilPh, soilMoisture = 0.28 }) {
  return request("/predict/multicrop", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      municipio,
      crop,
      month,
      temperature,
      rainfall,
      humidity,
      soil_ph: soilPh,
      soil_moisture: soilMoisture,
    }),
  });
}

export async function getRiskMap(crop = null) {
  const qs = crop ? `?crop=${encodeURIComponent(crop)}` : "";
  return request(`/risk-map${qs}`);
}

export async function monitorDrift(payload) {
  return request("/monitor/drift", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function monitorAnomaly(payload) {
  return request("/monitor/anomaly", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function submitFeedback(payload) {
  return request("/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getWaterStress(municipio = null) {
  const qs = municipio ? `?municipio=${encodeURIComponent(municipio)}` : "";
  return request(`/agronomy/water-stress${qs}`);
}

export async function getCropOptimalConditions(crop) {
  return request(`/agronomy/optimal-conditions/${encodeURIComponent(crop)}`);
}

export async function getSowingCalendar(municipio = null, crop = null) {
  const params = new URLSearchParams();
  if (municipio) params.set("municipio", municipio);
  if (crop) params.set("crop", crop);
  const qs = params.toString();
  return request(`/agronomy/sowing-calendar${qs ? `?${qs}` : ""}`);
}

export async function getForecast(municipio) {
  return request(`/forecast/${encodeURIComponent(municipio)}`);
}

export async function getSatelliteNdvi(municipio, { daysBack = 21, maxCloudCover = 35, resolutionM = 20 } = {}) {
  const params = new URLSearchParams();
  params.set("days_back", String(daysBack));
  params.set("max_cloud_cover", String(maxCloudCover));
  params.set("resolution_m", String(resolutionM));
  return request(`/satellite/ndvi/${encodeURIComponent(municipio)}?${params.toString()}`);
}

export async function getAgronomyCalculation({ crop, municipio, current_ph, current_rainfall, temperature, weekly_eto }) {
  return request("/agronomy/calculator", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ crop, municipio, current_ph, current_rainfall, temperature, weekly_eto }),
  });
}

export async function retrainModel() {
  return request("/admin/retrain", {
    method: "POST",
    headers: { "x-admin-token": "agroclima-admin-2024" },
  });
}

export async function compareModels({ run = false } = {}) {
  return request("/admin/compare-models", {
    method: run ? "POST" : "GET",
    headers: { "x-admin-token": "agroclima-admin-2024" },
  });
}

export async function getModelInfo() {
  return request("/admin/model-info", {
    headers: { "x-admin-token": "agroclima-admin-2024" },
  });
}

export async function getOpenMeteoUsage() {
  return request("/admin/open-meteo-usage", {
    headers: { "x-admin-token": "agroclima-admin-2024" },
  });
}

export async function getAdminDatasets() {
  return request("/admin/datasets", {
    headers: { "x-admin-token": "agroclima-admin-2024" },
  });
}

export async function getRecommendations(cultivo, { temperatura, precipitacion, humedad, ph_suelo } = {}) {
  const params = new URLSearchParams();
  if (temperatura   != null) params.set("temperatura",   temperatura);
  if (precipitacion != null) params.set("precipitacion", precipitacion);
  if (humedad       != null) params.set("humedad",       humedad);
  if (ph_suelo      != null) params.set("ph_suelo",      ph_suelo);
  return request(`/recommendations/${encodeURIComponent(cultivo)}?${params}`);
}

export async function getDataset() {
  return request("/dataset");
}

export async function uploadDataset(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE_URL}/upload-dataset`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Error al subir archivo");
  }
  return res.json();
}

export function getDatasetTemplateUrl() {
  return `${BASE_URL}/dataset-template`;
}

export async function getArduinoStatus() {
  return request("/arduino/status");
}

export async function connectArduino(port = null, baudRate = 9600) {
  return request("/arduino/connect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ port, baud_rate: baudRate }),
  });
}

export async function disconnectArduino() {
  return request("/arduino/disconnect", { method: "POST" });
}

export async function setArduinoConfig(municipio, crop) {
  return request("/arduino/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ municipio, crop }),
  });
}

export async function simulateArduino(data) {
  return request("/arduino/simulate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function createArduinoSocket(onMessage, onClose) {
  const ws = new WebSocket("ws://localhost:8000/ws/arduino");
  ws.onmessage = (e) => onMessage(JSON.parse(e.data));
  ws.onclose   = onClose || (() => {});
  return ws;
}
