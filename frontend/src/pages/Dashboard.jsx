import { useEffect, useMemo, useState } from "react";
import ChartCanvas from "../components/ChartCanvas";
import { cropOptions, municipioOptions, TRAINED_CROPS } from "../data/constants";
import { getCropOptimalConditions, getSatelliteNdvi } from "../services/api";
import { getRiskLabel, getRecommendation } from "../utils/riskUtils";

const MONTHS_ES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"];

const LEAF_OPTIONS = [
  { value: 80, label: "Hojas verdes", emoji: "🟢", desc: "Sanas y vigorosas" },
  { value: 55, label: "Algo amarillas", emoji: "🟡", desc: "Señales leves de estres" },
  { value: 30, label: "Amarillas/cafes", emoji: "🔴", desc: "Estres visible o enfermedad" },
];

function hasInvalidValues(form) {
  return (
    form.temperature < 5 || form.temperature > 45 ||
    form.humidity < 5 ||
    form.soilPh < 3.5 || form.soilPh > 9.5
  );
}

// ── Colores oficiales de cada variable ────────────────────────
const RAIN_COLOR  = "#0ea5e9"; // celeste – agua
const TEMP_COLOR  = "#f59e0b"; // ámbar  – calor
const HUM_COLOR   = "#8b5cf6"; // violeta – humedad

function buildFarmerAlerts(entry) {
  const alerts = [];

  if (entry.rainfall > 85) {
    alerts.push({ severity: "high", title: "Exceso de lluvia", action: "Destapa drenajes y evita agregar mas riego hasta que el suelo se desocupe.", value: `${entry.rainfall} mm` });
  } else if (entry.rainfall < 30) {
    alerts.push({ severity: "high", title: "Muy poca lluvia", action: "Riega hoy y conserva humedad con cobertura sobre el suelo.", value: `${entry.rainfall} mm` });
  } else if (entry.rainfall < 50) {
    alerts.push({ severity: "medium", title: "Lluvia baja", action: "Vigila humedad del suelo y prepara un riego de apoyo esta semana.", value: `${entry.rainfall} mm` });
  }

  if (entry.temperature >= 30) {
    alerts.push({ severity: "high", title: "Mucho calor", action: "Riega temprano y protege plantas jovenes del sol fuerte del mediodia.", value: `${entry.temperature}°C` });
  } else if (entry.temperature <= 14) {
    alerts.push({ severity: "high", title: "Frio peligroso", action: "Protege el cultivo por la noche con cobertura ligera o barrera contra el frio.", value: `${entry.temperature}°C` });
  } else if (entry.temperature <= 18) {
    alerts.push({ severity: "medium", title: "Temperatura fresca", action: "Refuerza monitoreo porque el crecimiento puede ponerse lento.", value: `${entry.temperature}°C` });
  }

  if (entry.humidity >= 82) {
    alerts.push({ severity: "high", title: "Humedad muy alta", action: "Revisa manchas u hongos en hojas y evita labores con follaje mojado.", value: `${entry.humidity}%` });
  } else if (entry.humidity < 40) {
    alerts.push({ severity: "high", title: "Aire muy seco", action: "No dejes secar el suelo; prioriza riego y cobertura vegetal.", value: `${entry.humidity}%` });
  } else if (entry.humidity < 55) {
    alerts.push({ severity: "medium", title: "Humedad baja", action: "Vigila secado rapido del suelo y aumenta frecuencia de revision.", value: `${entry.humidity}%` });
  }

  if (entry.soilPh < 5.5) {
    alerts.push({ severity: entry.soilPh < 4.5 ? "high" : "medium", title: "Suelo acido", action: "Evalua correccion de pH con apoyo tecnico antes del siguiente manejo fuerte.", value: `pH ${entry.soilPh}` });
  } else if (entry.soilPh > 7.2) {
    alerts.push({ severity: entry.soilPh > 8.0 ? "high" : "medium", title: "Suelo alcalino", action: "Revisa clorosis o falta de vigor y ajusta nutricion segun analisis de suelo.", value: `pH ${entry.soilPh}` });
  }

  const order = { high: 0, medium: 1, low: 2 };
  return alerts.sort((a, b) => order[a.severity] - order[b.severity]);
}

function yieldBand(yieldPct) {
  if (yieldPct >= 80) return { label: "Produccion esperada buena", color: "#16a34a", text: "Si mantienes el manejo actual, el cultivo va en buena direccion." };
  if (yieldPct >= 60) return { label: "Produccion esperada media", color: "#d97706", text: "El cultivo todavia puede responder bien si corriges los factores de riesgo." };
  return { label: "Produccion esperada baja", color: "#dc2626", text: "El cultivo necesita accion pronta para evitar mas perdida de rendimiento." };
}

function parseMetricValue(value) {
  if (value === "" || value == null || Number.isNaN(Number(value))) return null;
  return Number(value);
}

function buildComparisonRows(form, optimal) {
  if (!optimal) return [];

  const rows = [
    {
      key: "rainfall",
      label: "Lluvia",
      unit: "mm",
      value: parseMetricValue(form.rainfall),
      min: optimal.rainfall.min,
      max: optimal.rainfall.max,
      color: RAIN_COLOR,
    },
    {
      key: "temperature",
      label: "Temperatura",
      unit: "C",
      value: parseMetricValue(form.temperature),
      min: optimal.temperature.min,
      max: optimal.temperature.max,
      color: TEMP_COLOR,
    },
    {
      key: "humidity",
      label: "Humedad",
      unit: "%",
      value: parseMetricValue(form.humidity),
      min: optimal.humidity.min,
      max: optimal.humidity.max,
      color: HUM_COLOR,
    },
    {
      key: "soil_ph",
      label: "pH del suelo",
      unit: "pH",
      value: parseMetricValue(form.soilPh),
      min: optimal.soil_ph.min,
      max: optimal.soil_ph.max,
      color: "#16a34a",
    },
  ];

  return rows.map((row) => {
    const span = Math.max(row.max - row.min, 1);
    const displayMin = Math.max(0, row.min - span * 0.75);
    const displayMax = row.max + span * 0.75;
    const displaySpan = Math.max(displayMax - displayMin, 1);
    const idealLeft = ((row.min - displayMin) / displaySpan) * 100;
    const idealWidth = ((row.max - row.min) / displaySpan) * 100;
    const markerLeft = row.value == null ? null : Math.min(100, Math.max(0, ((row.value - displayMin) / displaySpan) * 100));
    const status = row.value == null ? "pending" : row.value < row.min ? "low" : row.value > row.max ? "high" : "ok";
    return {
      ...row,
      idealLeft,
      idealWidth,
      markerLeft,
      status,
    };
  });
}

function comparisonStatusCopy(status) {
  if (status === "ok") return { label: "En rango", color: "#16a34a", bg: "rgba(22,163,74,0.1)" };
  if (status === "low") return { label: "Bajo", color: "#d97706", bg: "rgba(245,158,11,0.1)" };
  if (status === "high") return { label: "Alto", color: "#dc2626", bg: "rgba(220,38,38,0.1)" };
  return { label: "Ingresa valor", color: "#64748b", bg: "rgba(100,116,139,0.1)" };
}

function ndviStatusCopy(value) {
  if (value == null) return { label: "Sin NDVI", color: "#64748b", bg: "rgba(100,116,139,0.1)", note: "Aun no hay indice calculado." };
  if (value >= 0.65) return { label: "Vigor alto", color: "#16a34a", bg: "rgba(22,163,74,0.12)", note: "La cobertura vegetal luce sana en la observacion satelital." };
  if (value >= 0.45) return { label: "Vigor medio", color: "#d97706", bg: "rgba(245,158,11,0.12)", note: "Se observa cobertura aceptable, pero conviene vigilar cambios." };
  return { label: "Vigor bajo", color: "#dc2626", bg: "rgba(220,38,38,0.12)", note: "La vegetacion luce debil o con menor cobertura de lo esperado." };
}

function formatSceneDate(value) {
  if (!value) return "Sin fecha";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString("es-GT", { year: "numeric", month: "short", day: "numeric" });
}

export default function Dashboard({ form, selectedEntry, predictionRisk, trendSeries, avgRisk, yieldResult, analysisReady, apiOnline, updateForm, submitForm, submitting, weatherLoading, weatherSource }) {
  const [optimal, setOptimal] = useState(null);
  const [optimalLoading, setOptimalLoading] = useState(false);
  const [satellite, setSatellite] = useState(null);
  const [satelliteLoading, setSatelliteLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (!form.crop) {
      setOptimal(null);
      return;
    }

    setOptimalLoading(true);
    getCropOptimalConditions(form.crop)
      .then((data) => {
        if (!cancelled) setOptimal(data);
      })
      .catch(() => {
        if (!cancelled) setOptimal(null);
      })
      .finally(() => {
        if (!cancelled) setOptimalLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [form.crop]);

  useEffect(() => {
    let cancelled = false;
    if (!apiOnline || !form.municipality) {
      setSatellite(null);
      return;
    }

    setSatelliteLoading(true);
    getSatelliteNdvi(form.municipality)
      .then((data) => {
        if (!cancelled) setSatellite(data);
      })
      .catch(() => {
        if (!cancelled) setSatellite(null);
      })
      .finally(() => {
        if (!cancelled) setSatelliteLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [form.municipality]);

  // ── Gráfica de líneas – variables climáticas (eje dual) ────
  const climateChart = useMemo(() => ({
    type: "line",
    data: {
      labels: trendSeries.labels,
      datasets: [
        {
          label: "Precipitación (mm)",
          data: trendSeries.rainfall,
          yAxisID: "yRain",
          borderColor: RAIN_COLOR,
          backgroundColor: (ctx) => {
            const canvas = ctx.chart.ctx;
            const grad = canvas.createLinearGradient(0, 0, 0, ctx.chart.height);
            grad.addColorStop(0, "rgba(14,165,233,0.28)");
            grad.addColorStop(1, "rgba(14,165,233,0.01)");
            return grad;
          },
          tension: 0.42,
          fill: true,
          pointRadius: 4,
          pointHoverRadius: 7,
          pointBackgroundColor: RAIN_COLOR,
          pointBorderColor: "#fff",
          pointBorderWidth: 2,
          borderWidth: 2.5,
          order: 3,
        },
        {
          label: "Temperatura (°C)",
          data: trendSeries.temperature,
          yAxisID: "yRight",
          borderColor: TEMP_COLOR,
          backgroundColor: "rgba(245,158,11,0.0)",
          tension: 0.42,
          fill: false,
          pointRadius: 4,
          pointHoverRadius: 7,
          pointBackgroundColor: TEMP_COLOR,
          pointBorderColor: "#fff",
          pointBorderWidth: 2,
          borderWidth: 2.5,
          borderDash: [],
          order: 2,
        },
        {
          label: "Humedad (%)",
          data: trendSeries.humidity,
          yAxisID: "yRight",
          borderColor: HUM_COLOR,
          backgroundColor: "rgba(139,92,246,0.0)",
          tension: 0.42,
          fill: false,
          pointRadius: 4,
          pointHoverRadius: 7,
          pointBackgroundColor: HUM_COLOR,
          pointBorderColor: "#fff",
          pointBorderWidth: 2,
          borderWidth: 2.5,
          borderDash: [5, 3],
          order: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      animation: { duration: 800, easing: "easeInOutQuart" },
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            boxWidth: 12,
            boxHeight: 3,
            padding: 18,
            usePointStyle: true,
            pointStyle: "circle",
            font: { size: 11, weight: "600" },
            color: "#475569",
          },
        },
        tooltip: {
          backgroundColor: "rgba(15,23,42,0.92)",
          titleColor: "#f1f5f9",
          bodyColor: "#cbd5e1",
          borderColor: "rgba(255,255,255,0.1)",
          borderWidth: 1,
          padding: 12,
          cornerRadius: 10,
          titleFont: { size: 12, weight: "700" },
          bodyFont: { size: 11 },
          callbacks: {
            label: (ctx) => {
              const unit = ctx.dataset.yAxisID === "yRain" ? " mm" : ctx.dataset.label.includes("Temp") ? " °C" : "%";
              return `  ${ctx.dataset.label}: ${ctx.parsed.y}${unit}`;
            },
          },
        },
      },
      scales: {
        x: {
          grid: { color: "rgba(15,23,42,0.05)", drawTicks: false },
          border: { display: false },
          ticks: { font: { size: 11 }, color: "#64748b", padding: 8 },
        },
        yRain: {
          type: "linear",
          position: "left",
          title: {
            display: true,
            text: "Precipitación (mm)",
            color: RAIN_COLOR,
            font: { size: 10, weight: "700" },
          },
          grid: { color: "rgba(14,165,233,0.08)" },
          border: { display: false },
          ticks: { color: RAIN_COLOR, font: { size: 10 }, padding: 6 },
          suggestedMin: 0,
        },
        yRight: {
          type: "linear",
          position: "right",
          title: {
            display: true,
            text: "Temp (°C) / Humedad (%)",
            color: "#94a3b8",
            font: { size: 10, weight: "700" },
          },
          grid: { drawOnChartArea: false },
          border: { display: false },
          ticks: { color: "#64748b", font: { size: 10 }, padding: 6 },
          suggestedMin: 0,
          suggestedMax: 100,
        },
      },
    },
  }), [trendSeries]);

  // ── Gráfica de barras – índice de riesgo por cultivo ────────
  const CROP_ICON = {
    "Maiz":"🌽","Frijol":"🫘","Cafe":"☕","Arroz":"🌾","Papa":"🥔","Tomate":"🍅",
    "Aguacate":"🥑","Cacao":"🍫","Trigo":"🌾","Sorgo":"🌿","Avena":"🌿","Soya":"🫛",
    "Zanahoria":"🥕","Cebolla":"🧅","Repollo":"🥬","Brocoli":"🥦","Coliflor":"🥦",
    "Lechuga":"🥬","Espinaca":"🥬","Pepino":"🥒","Chile":"🌶️","Berenjena":"🍆",
    "Zucchini":"🥒","Mango":"🥭","Naranja":"🍊","Limon":"🍋","Banano":"🍌",
    "Pina":"🍍","Papaya":"🍈","Melon":"🍈","Sandia":"🍉","Fresa":"🍓",
    "Cana de azucar":"🌿","Cardamomo":"🌿","Mani":"🥜","Yuca":"🌿","Camote":"🍠",
  };

  const riskChart = useMemo(() => ({
    type: "bar",
    data: {
      labels: cropOptions.map((c) => `${CROP_ICON[c] || "🌿"} ${c}`),
      datasets: [{
        label: "Índice de riesgo (/100)",
        data: avgRisk,
        backgroundColor: avgRisk.map((v) =>
          v >= 75
            ? "rgba(239,68,68,0.82)"
            : v <= 40
            ? "rgba(34,197,94,0.80)"
            : "rgba(251,146,60,0.82)"
        ),
        borderColor: avgRisk.map((v) =>
          v >= 75 ? "#ef4444" : v <= 40 ? "#22c55e" : "#fb923c"
        ),
        borderWidth: 1.5,
        borderRadius: 8,
        borderSkipped: false,
        hoverBackgroundColor: avgRisk.map((v) =>
          v >= 75
            ? "rgba(239,68,68,0.95)"
            : v <= 40
            ? "rgba(34,197,94,0.95)"
            : "rgba(251,146,60,0.95)"
        ),
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 900, easing: "easeOutBounce" },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(15,23,42,0.92)",
          titleColor: "#f1f5f9",
          bodyColor: "#cbd5e1",
          borderColor: "rgba(255,255,255,0.1)",
          borderWidth: 1,
          padding: 12,
          cornerRadius: 10,
          titleFont: { size: 12, weight: "700" },
          bodyFont: { size: 11 },
          callbacks: {
            title: (items) => items[0].label,
            label: (ctx) => {
              const v = ctx.parsed.y;
              const nivel = v >= 75 ? "🔴 ALTO" : v <= 40 ? "🟢 BAJO" : "🟡 MEDIO";
              return [`  Riesgo: ${v}/100`, `  Nivel: ${nivel}`];
            },
          },
        },
        annotation: undefined,
      },
      scales: {
        y: {
          suggestedMax: 105,
          suggestedMin: 0,
          grid: { color: "rgba(15,23,42,0.05)", drawTicks: false },
          border: { display: false },
          ticks: { color: "#64748b", font: { size: 10 }, padding: 6,
            callback: (v) => v + "%",
          },
          // Líneas de umbral manuales via afterDraw (plugin)
        },
        x: {
          grid: { display: false },
          border: { display: false },
          ticks: {
            color: "#64748b",
            font: { size: 10.5, weight: "600" },
            maxRotation: 35,
            minRotation: 20,
            padding: 4,
          },
        },
      },
    },
    plugins: [
      {
        id: "thresholdLines",
        afterDraw(chart) {
          const { ctx, chartArea: { left, right }, scales: { y } } = chart;
          const thresholds = [
            { value: 40, color: "rgba(34,197,94,0.55)",  label: "Bajo ≤40",  dash: [6,4] },
            { value: 75, color: "rgba(239,68,68,0.55)",  label: "Alto ≥75",  dash: [6,4] },
          ];
          ctx.save();
          thresholds.forEach(({ value, color, label, dash }) => {
            const yPos = y.getPixelForValue(value);
            ctx.setLineDash(dash);
            ctx.strokeStyle = color;
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(left, yPos);
            ctx.lineTo(right, yPos);
            ctx.stroke();
            ctx.setLineDash([]);
            ctx.fillStyle = color;
            ctx.font = "bold 9px Inter, system-ui";
            ctx.fillText(label, right - 48, yPos - 4);
          });
          ctx.restore();
        },
      },
    ],
  }), [avgRisk]);

  const comparisonRows = useMemo(() => buildComparisonRows(form, optimal), [form, optimal]);
  const scoreBarWidth = `${predictionRisk.score}%`;
  const farmerAlerts = useMemo(
    () => (analysisReady && !selectedEntry?.pending ? buildFarmerAlerts(selectedEntry) : []),
    [analysisReady, selectedEntry],
  );
  const primaryAlert = farmerAlerts[0] || null;
  const quickActions = farmerAlerts.slice(0, 3);
  const productionBand = yieldResult
    ? predictionRisk.level === "high"
      ? { label: "Produccion en riesgo", color: "#dc2626", text: "Las condiciones actuales amenazan el rendimiento. Corrige los factores criticos antes de continuar." }
      : predictionRisk.level === "medium"
        ? { label: yieldResult.yield_pct >= 80 ? "Produccion esperada aceptable" : yieldBand(yieldResult.yield_pct).label, color: "#d97706", text: "Corrige los factores en alerta para mantener un rendimiento estable." }
        : yieldBand(yieldResult.yield_pct)
    : null;
  const ndviValue = satellite?.ndvi?.available ? satellite.ndvi.latest_mean : null;
  const ndviStatus = ndviStatusCopy(ndviValue);

  return (
    <div className="page-content">
      <div className="two-col">
        {/* Metrics Form */}
        <div className="card">
          <div className="card-header">
            <h3>Ingreso de metricas climaticas</h3>
            <span className="chip">Variables clave</span>
          </div>
          <div className="card-body">
            <form className="metrics-form" onSubmit={submitForm}>
              <label className="form-label">
                Departamento
                <select className="form-select" name="municipality" value={form.municipality} onChange={updateForm}>
                  {municipioOptions.map((m) => <option key={m}>{m}</option>)}
                </select>
              </label>
              <label className="form-label">
                Cultivo
                <select className="form-select" name="crop" value={form.crop} onChange={updateForm}>
                  {cropOptions.map((c) => <option key={c}>{c}</option>)}
                </select>
              </label>
              {!TRAINED_CROPS.includes(form.crop) && (
                <div className="form-full" style={{ background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.3)", borderRadius: 8, padding: "0.55rem 0.8rem", fontSize: "0.75rem", color: "#b45309" }}>
                  <strong>{form.crop}</strong> no esta en los 8 cultivos con los que fue entrenado el modelo. La prediccion usara el cultivo mas similar disponible. Cultivos con datos reales: {TRAINED_CROPS.join(", ")}.
                </div>
              )}
              <label className="form-label">
                Precipitacion (mm)
                <input className="form-input" name="rainfall" type="number" min="0" max="600" step="0.1" value={form.rainfall} onChange={updateForm} placeholder="0 – 600 mm" />
              </label>
              <label className="form-label">
                Temperatura (°C)
                <input className="form-input" name="temperature" type="number" min="5" max="45" step="0.1" value={form.temperature} onChange={updateForm} placeholder="5 – 45 °C" />
              </label>
              <label className="form-label">
                Humedad (%)
                <input className="form-input" name="humidity" type="number" min="5" max="100" step="0.1" value={form.humidity} onChange={updateForm} placeholder="5 – 100 %" />
              </label>
              <label className="form-label">
                pH del suelo
                <input className="form-input" name="soilPh" type="number" min="3.5" max="9.5" step="0.1" value={form.soilPh} onChange={updateForm} placeholder="3.5 – 9.5" />
              </label>
              <div className="form-full">
                <div style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "0.75rem",
                  flexWrap: "wrap",
                  padding: "0.55rem 0.7rem",
                  borderRadius: 8,
                  background: "rgba(37,99,235,0.06)",
                  border: "1px solid rgba(37,99,235,0.16)",
                  fontSize: "0.74rem",
                  color: "var(--text-secondary)",
                }}>
                  <span>
                    {weatherLoading
                      ? "Actualizando clima reciente del departamento..."
                      : weatherSource
                      ? `Datos autocompletados desde ${weatherSource}`
                      : "Puedes ingresar manualmente o usar datos recientes del departamento."}
                  </span>
                  {weatherSource && !weatherLoading && (
                    <span className="chip blue" style={{ fontSize: "0.68rem" }}>Auto desde API</span>
                  )}
                </div>
              </div>
              {/* Selector estado de hojas */}
              <div className="form-full">
                <p style={{ margin: "0 0 0.4rem", fontSize: "0.78rem", fontWeight: 700, color: "var(--text-secondary)" }}>
                  Estado de las hojas del cultivo
                </p>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  {LEAF_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => updateForm({ target: { name: "leafCondition", value: opt.value } })}
                      style={{
                        flex: 1, padding: "0.5rem 0.4rem", borderRadius: 8, cursor: "pointer",
                        border: `2px solid ${form.leafCondition === opt.value ? "var(--accent)" : "var(--border)"}`,
                        background: form.leafCondition === opt.value ? "rgba(22,163,74,0.07)" : "var(--surface-alt)",
                        fontSize: "0.72rem", fontWeight: 600, color: "var(--text-primary)",
                        textAlign: "center", lineHeight: 1.4,
                      }}
                    >
                      <div style={{ fontSize: "1.1rem", marginBottom: "0.2rem" }}>{opt.emoji}</div>
                      <div>{opt.label}</div>
                      <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontWeight: 400 }}>{opt.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Mes del analisis */}
              <div className="form-full" style={{ fontSize: "0.73rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                Analizando para: <strong style={{ color: "var(--text-secondary)" }}>{MONTHS_ES[new Date().getMonth()]} {new Date().getFullYear()}</strong>
              </div>

              {hasInvalidValues(form) && (
                <div className="form-full" style={{ background: "rgba(220,38,38,0.08)", border: "1px solid rgba(220,38,38,0.3)", borderRadius: 8, padding: "0.6rem 0.8rem", fontSize: "0.75rem", color: "#dc2626" }}>
                  Algunos valores estan fuera del rango agricola valido. Verifica temperatura (5–45 °C), humedad (5–100%) y pH (3.5–9.5).
                </div>
              )}
              <div className="form-full">
                <button
                  className="btn primary"
                  style={{ width: "100%", justifyContent: "center" }}
                  type="submit"
                  disabled={submitting}
                >
                  {submitting ? "Analizando..." : "Analizar riesgo"}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Prediction */}
        <div className="card">
          <div className="card-header">
            <h3>Prediccion de riesgo</h3>
            <span className={`chip ${apiOnline ? "green" : "orange"}`}>
              {apiOnline ? "XGBoost activo" : "ML simulado"}
            </span>
          </div>
          <div className="card-body">
            <div className="prediction-hero">
              <p className="prediction-eyebrow">Escenario analizado</p>
              <h4 className="prediction-title">
                {analysisReady ? `${selectedEntry.crop} — ${selectedEntry.municipality}` : `${form.crop} — ${form.municipality}`}
              </h4>
              {analysisReady && (
                <div className={`risk-badge risk-${predictionRisk.level}`}>
                  {getRiskLabel(predictionRisk.level)}
                </div>
              )}

              {!analysisReady ? (
                <div style={{
                  marginTop: "0.8rem",
                  background: "rgba(15,23,42,0.03)",
                  border: "1px dashed rgba(15,23,42,0.15)",
                  borderRadius: 12,
                  padding: "1rem",
                }}>
                  <p style={{ margin: 0, fontSize: "0.95rem", fontWeight: 800, color: "var(--text-primary)" }}>
                    Nuevo analisis listo
                  </p>
                  <p style={{ margin: "0.35rem 0 0", fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                    Ingresa lluvia, temperatura, humedad y pH del suelo. Cuando pulses "Analizar riesgo" aqui veras el rendimiento esperado, el problema principal y la accion sugerida.
                  </p>
                </div>
              ) : yieldResult ? (
                <div style={{ margin: "0.6rem 0 0.4rem" }}>
                  <p style={{ fontSize: "0.7rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", margin: "0 0 0.3rem" }}>
                    Resumen para agricultor
                  </p>
                  <div style={{ display: "flex", alignItems: "flex-end", gap: "0.6rem" }}>
                    <span style={{ fontSize: "2.2rem", fontWeight: 900, lineHeight: 1, color: productionBand?.color || (predictionRisk.level === "low" ? "#16a34a" : predictionRisk.level === "medium" ? "#d97706" : "#dc2626") }}>
                      {yieldResult.yield_pct}%
                    </span>
                    <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "0.25rem", textTransform: "capitalize" }}>
                      de rendimiento esperado
                    </span>
                  </div>
                  <div className="score-bar-track" style={{ marginTop: "0.5rem" }}>
                    <div
                      className={`score-bar-fill ${predictionRisk.level}`}
                      style={{ width: `${yieldResult.yield_pct}%` }}
                    />
                  </div>
                  {yieldResult.confidence && (
                    <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", marginTop: "0.35rem" }}>
                      <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Rango del modelo:</span>
                      <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-secondary)" }}>
                        {yieldResult.confidence.low.toFixed(1)}% – {yieldResult.confidence.high.toFixed(1)}%
                      </span>
                      <span style={{ fontSize: "0.67rem", color: "var(--text-muted)" }}>
                        (±{yieldResult.confidence.margin.toFixed(1)}%)
                      </span>
                    </div>
                  )}
                  <p style={{ fontSize: "0.8rem", color: productionBand?.color || "var(--text-secondary)", margin: "0.42rem 0 0", fontWeight: 700 }}>
                    {productionBand?.label}
                  </p>
                  <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", margin: "0.18rem 0 0", lineHeight: 1.5 }}>
                    {productionBand?.text}
                  </p>

                  {/* SHAP: factores que influyeron */}
                  {yieldResult?.explanation?.top_contributions?.length > 0 && (
                    <div style={{ marginTop: "0.75rem", padding: "0.75rem 0.85rem", borderRadius: 9, background: "var(--surface-alt)", border: "1px solid var(--border)" }}>
                      <p style={{ margin: "0 0 0.5rem", fontSize: "0.68rem", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.07em", color: "var(--text-muted)" }}>
                        Factores que influyeron
                      </p>
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                        {yieldResult.explanation.top_contributions.map((c) => {
                          const isPos = c.impact >= 0;
                          const maxImpact = Math.max(...yieldResult.explanation.top_contributions.map(x => Math.abs(x.impact)));
                          const barWidth = Math.round((Math.abs(c.impact) / Math.max(maxImpact, 1)) * 100);
                          return (
                            <div key={c.feature} style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                              <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)", width: 80, flexShrink: 0, textAlign: "right" }}>
                                {c.label}
                              </span>
                              <div style={{ flex: 1, height: 8, borderRadius: 4, background: "rgba(0,0,0,0.07)", overflow: "hidden" }}>
                                <div style={{
                                  height: "100%", width: `${barWidth}%`, borderRadius: 4,
                                  background: isPos ? "#16a34a" : "#dc2626",
                                  transition: "width 0.4s ease",
                                }} />
                              </div>
                              <span style={{ fontSize: "0.7rem", fontWeight: 700, color: isPos ? "#16a34a" : "#dc2626", width: 42, flexShrink: 0 }}>
                                {isPos ? "+" : ""}{c.impact.toFixed(1)}%
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  <div style={{
                    marginTop: "0.7rem",
                    background: primaryAlert?.severity === "high" ? "rgba(220,38,38,0.07)" : "rgba(245,158,11,0.08)",
                    border: `1px solid ${primaryAlert?.severity === "high" ? "rgba(220,38,38,0.2)" : "rgba(245,158,11,0.22)"}`,
                    borderRadius: 10,
                    padding: "0.75rem 0.85rem",
                  }}>
                    <p style={{ margin: "0 0 0.2rem", fontSize: "0.68rem", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)" }}>
                      Problema principal
                    </p>
                    <p style={{ margin: 0, fontSize: "0.95rem", fontWeight: 800, color: primaryAlert?.severity === "high" ? "#dc2626" : "#d97706" }}>
                      {primaryAlert ? `${primaryAlert.title} · ${primaryAlert.value}` : "Sin alertas fuertes en este momento"}
                    </p>
                    <p style={{ margin: "0.3rem 0 0", fontSize: "0.78rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                      {primaryAlert ? primaryAlert.action : "Las condiciones actuales no muestran un problema dominante para intervencion inmediata."}
                    </p>
                  </div>

                  <div style={{ marginTop: "0.75rem" }}>
                    <p style={{ margin: "0 0 0.45rem", fontSize: "0.68rem", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)" }}>
                      Que hacer ahora
                    </p>
                    <div style={{ display: "grid", gap: "0.45rem" }}>
                      {quickActions.length ? quickActions.map((item) => (
                        <div key={`${item.title}-${item.value}`} style={{
                          background: "var(--surface-alt)",
                          border: "1px solid var(--border)",
                          borderLeft: `3px solid ${item.severity === "high" ? "#dc2626" : "#d97706"}`,
                          borderRadius: 9,
                          padding: "0.55rem 0.7rem",
                        }}>
                          <p style={{ margin: 0, fontSize: "0.8rem", fontWeight: 700, color: "var(--text-primary)" }}>{item.title}</p>
                          <p style={{ margin: "0.18rem 0 0", fontSize: "0.76rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>{item.action}</p>
                        </div>
                      )) : (
                        <div style={{
                          background: "rgba(22,163,74,0.08)",
                          border: "1px solid rgba(22,163,74,0.18)",
                          borderRadius: 9,
                          padding: "0.55rem 0.7rem",
                          color: "#166534",
                          fontSize: "0.78rem",
                          lineHeight: 1.5,
                        }}>
                          Sigue con el manejo normal y vuelve a revisar el lote en tu siguiente jornada de monitoreo.
                        </div>
                      )}
                    </div>
                  </div>

                  <details style={{ marginTop: "0.8rem" }}>
                    <summary style={{ cursor: "pointer", fontSize: "0.78rem", fontWeight: 700, color: "var(--text-secondary)" }}>
                      Ver detalle tecnico
                    </summary>

                    <div style={{ marginTop: "0.65rem" }}>
                      <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", margin: "0.3rem 0 0" }}>
                        Indice de riesgo combinado: {predictionRisk.score}/100
                      </p>
                      <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", margin: "0.22rem 0 0" }}>
                        ML por rendimiento: {predictionRisk.mlScore}/100 · Reglas agronomicas: {predictionRisk.formulaScore}/100
                      </p>
                      <p style={{ fontSize: "0.68rem", color: "var(--text-muted)", margin: "0.18rem 0 0" }}>
                        Metodo: {predictionRisk.combination === "max_guardrail" ? "guardrail por condicion extrema" : "combinacion ponderada 60/40"}
                      </p>

                      {yieldResult.confidence && (() => {
                        const lo = yieldResult.confidence.low;
                        const hi = yieldResult.confidence.high;
                        const est = yieldResult.yield_pct;
                        const barColor = predictionRisk.level === "low" ? "#16a34a" : predictionRisk.level === "medium" ? "#d97706" : "#dc2626";
                        return (
                          <div style={{ marginTop: "0.55rem", background: "rgba(0,0,0,0.03)", border: "1px solid var(--border)", borderRadius: 8, padding: "0.6rem 0.75rem" }}>
                            <p style={{ margin: "0 0 0.4rem", fontSize: "0.68rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)" }}>
                              Intervalo de confianza (95%)
                            </p>
                            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                              <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-secondary)", minWidth: 30 }}>{lo}%</span>
                              <div style={{ flex: 1, position: "relative", height: 10, background: "rgba(0,0,0,0.08)", borderRadius: 5 }}>
                                <div style={{
                                  position: "absolute", left: `${lo}%`, width: `${hi - lo}%`,
                                  height: "100%", background: `${barColor}55`, borderRadius: 5,
                                }} />
                                <div style={{
                                  position: "absolute", left: `${est}%`, transform: "translateX(-50%)",
                                  width: 3, height: "100%", background: barColor, borderRadius: 2,
                                }} />
                              </div>
                              <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-secondary)", minWidth: 30, textAlign: "right" }}>{hi}%</span>
                            </div>
                            <p style={{ margin: "0.25rem 0 0", fontSize: "0.68rem", color: "var(--text-muted)" }}>
                              Estimado central: <strong style={{ color: barColor }}>{est}%</strong> · Margen: ±{yieldResult.confidence.margin}%
                            </p>
                          </div>
                        );
                      })()}

                      {yieldResult.anomaly && (
                        <div style={{ marginTop: "0.55rem", display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
                          <span className="chip" style={{
                            background: yieldResult.anomaly.is_anomaly ? "rgba(220,38,38,0.1)" : yieldResult.anomaly.label === "sospechoso" ? "rgba(245,158,11,0.1)" : "rgba(22,163,74,0.1)",
                            color: yieldResult.anomaly.is_anomaly ? "#dc2626" : yieldResult.anomaly.label === "sospechoso" ? "#d97706" : "#16a34a",
                            border: `1px solid ${yieldResult.anomaly.is_anomaly ? "rgba(220,38,38,0.25)" : yieldResult.anomaly.label === "sospechoso" ? "rgba(245,158,11,0.25)" : "rgba(22,163,74,0.25)"}`,
                          }}>
                            Anomalia operativa: {yieldResult.anomaly.label} ({yieldResult.anomaly.score}/100)
                          </span>

                          {yieldResult.drift && (
                            <span className="chip" style={{
                              background: yieldResult.drift.status === "drift_detectado" ? "rgba(220,38,38,0.1)" : "rgba(37,99,235,0.1)",
                              color: yieldResult.drift.status === "drift_detectado" ? "#dc2626" : "#2563eb",
                              border: `1px solid ${yieldResult.drift.status === "drift_detectado" ? "rgba(220,38,38,0.25)" : "rgba(37,99,235,0.25)"}`,
                            }}>
                              Drift: {yieldResult.drift.similarity_score}% ({yieldResult.drift.status})
                            </span>
                          )}
                        </div>
                      )}

                      {yieldResult.explanation?.narrative && (
                        <div style={{ marginTop: "0.65rem", background: "rgba(37,99,235,0.05)", border: "1px solid rgba(37,99,235,0.18)", borderRadius: 8, padding: "0.6rem 0.75rem" }}>
                          <p style={{ margin: "0 0 0.35rem", fontSize: "0.68rem", textTransform: "uppercase", fontWeight: 800, letterSpacing: "0.08em", color: "#2563eb" }}>
                            Explicabilidad SHAP
                          </p>
                          <p style={{ margin: 0, fontSize: "0.78rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
                            {yieldResult.explanation.narrative}
                          </p>
                        </div>
                      )}
                    </div>
                  </details>
                </div>
              ) : (
                /* Sin XGBoost: mostrar score de fórmula local */
                <>
                  <div className="prediction-score">
                    <span style={{ fontWeight: 700, fontSize: "0.78rem", width: "60px" }}>
                      {predictionRisk.score}/100
                    </span>
                    <div className="score-bar-track">
                      <div
                        className={`score-bar-fill ${predictionRisk.level}`}
                        style={{ width: scoreBarWidth }}
                      />
                    </div>
                  </div>
                  <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", margin: "0.3rem 0 0" }}>
                    Riesgo basado solo en reglas agronomicas locales.
                  </p>
                </>
              )}

              {analysisReady && (
                <p className="prediction-meta">
                  Lluvia <strong>{selectedEntry.rainfall} mm</strong> · Temperatura <strong>{selectedEntry.temperature}°C</strong> · Humedad <strong>{selectedEntry.humidity}%</strong> · pH <strong>{selectedEntry.soilPh}</strong>
                </p>
              )}
            </div>
            <div className="recommendation-box">
              <strong style={{ display: "block", fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: "0.4rem" }}>
                Accion recomendada
              </strong>
              {analysisReady
                ? getRecommendation(selectedEntry, predictionRisk)
                : "Completa las metricas del lote y ejecuta el analisis para recibir una recomendacion concreta."}
            </div>
          </div>
        </div>


        {/* Charts — full width */}
        <div className="card full-span">
          <div className="card-header">
            <h3>Lectura reciente y referencia por cultivo</h3>
            <span className="chip">Ultimos 6 registros</span>
          </div>
          <div className="card-body">
            <div className="chart-grid">

              {/* ── Gráfica de líneas ── */}
              <div className="chart-card">
                <div className="chart-card-header">
                  <div>
                    <h4>Variables recientes</h4>
                    <p className="chart-card-sub">Ultimos 6 registros cargados · vista referencial</p>
                  </div>
                  <div className="chart-legend-pills">
                    <span className="legend-pill" style={{ color: "#0ea5e9", borderColor: "rgba(14,165,233,0.3)", background: "rgba(14,165,233,0.07)" }}>
                      <span className="legend-pill-dot" style={{ background: "#0ea5e9" }} />Lluvia (mm)
                    </span>
                    <span className="legend-pill" style={{ color: "#f59e0b", borderColor: "rgba(245,158,11,0.3)", background: "rgba(245,158,11,0.07)" }}>
                      <span className="legend-pill-dot" style={{ background: "#f59e0b" }} />Temp (°C)
                    </span>
                    <span className="legend-pill" style={{ color: "#8b5cf6", borderColor: "rgba(139,92,246,0.3)", background: "rgba(139,92,246,0.07)" }}>
                      <span className="legend-pill-dot" style={{ background: "#8b5cf6" }} />Humedad (%)
                    </span>
                  </div>
                </div>
                <ChartCanvas config={climateChart} />
              </div>

              {/* ── Gráfica de barras ── */}
              <div className="chart-card">
                <div className="chart-card-header">
                  <div>
                    <h4>Estado actual vs rango optimo</h4>
                    <p className="chart-card-sub">Comparacion directa para {form.crop}</p>
                  </div>
                  <div className="chart-legend-pills">
                    <span className="legend-pill" style={{ color: "#16a34a", borderColor: "rgba(22,163,74,0.25)", background: "rgba(22,163,74,0.07)" }}>
                      <span className="legend-pill-dot" style={{ background: "#16a34a" }} />Rango ideal
                    </span>
                    <span className="legend-pill" style={{ color: "#0f172a", borderColor: "rgba(15,23,42,0.15)", background: "rgba(15,23,42,0.04)" }}>
                      <span className="legend-pill-dot" style={{ background: "#0f172a" }} />Valor actual
                    </span>
                  </div>
                </div>
                <div style={{ display: "grid", gap: "0.9rem" }}>
                  {optimalLoading ? (
                    <div style={{ padding: "1rem", borderRadius: 12, background: "rgba(15,23,42,0.03)", color: "var(--text-secondary)", fontSize: "0.82rem" }}>
                      Cargando rangos optimos del cultivo...
                    </div>
                  ) : comparisonRows.length ? comparisonRows.map((row) => {
                    const statusCopy = comparisonStatusCopy(row.status);
                    return (
                      <div key={row.key} style={{ background: "var(--surface-alt)", border: "1px solid var(--border)", borderRadius: 12, padding: "0.85rem 0.9rem" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", gap: "0.75rem", flexWrap: "wrap", alignItems: "center" }}>
                          <div>
                            <p style={{ margin: 0, fontSize: "0.82rem", fontWeight: 800, color: "var(--text-primary)" }}>{row.label}</p>
                            <p style={{ margin: "0.18rem 0 0", fontSize: "0.74rem", color: "var(--text-secondary)" }}>
                              Ideal: {row.min}-{row.max} {row.unit}
                            </p>
                          </div>
                          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap", justifyContent: "flex-end" }}>
                            <span style={{ fontSize: "0.82rem", fontWeight: 800, color: row.color }}>
                              {row.value == null ? "Sin dato" : `${row.value} ${row.unit}`}
                            </span>
                            <span style={{ fontSize: "0.7rem", fontWeight: 800, padding: "0.28rem 0.6rem", borderRadius: 999, background: statusCopy.bg, color: statusCopy.color }}>
                              {statusCopy.label}
                            </span>
                          </div>
                        </div>
                        <div style={{ position: "relative", marginTop: "0.7rem", height: 12, borderRadius: 999, background: "rgba(15,23,42,0.08)", overflow: "hidden" }}>
                          <div style={{ position: "absolute", left: `${row.idealLeft}%`, width: `${row.idealWidth}%`, top: 0, bottom: 0, background: "rgba(22,163,74,0.35)" }} />
                          {row.markerLeft != null && (
                            <div style={{ position: "absolute", left: `${row.markerLeft}%`, top: "50%", transform: "translate(-50%, -50%)", width: 12, height: 12, borderRadius: 999, background: row.color, border: "2px solid #fff", boxShadow: "0 0 0 1px rgba(15,23,42,0.08)" }} />
                          )}
                        </div>
                      </div>
                    );
                  }) : (
                    <div style={{ padding: "1rem", borderRadius: 12, background: "rgba(15,23,42,0.03)", color: "var(--text-secondary)", fontSize: "0.82rem", lineHeight: 1.6 }}>
                      No hay referencia disponible para este cultivo.
                    </div>
                  )}
                  {optimal?.notes && (
                    <div style={{ fontSize: "0.74rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                      <strong style={{ color: "var(--text-primary)" }}>Nota agronomica:</strong> {optimal.notes}
                    </div>
                  )}
                </div>
              </div>

              <div className="chart-card">
                <div className="chart-card-header">
                  <div>
                    <h4>Vigor vegetal satelital</h4>
                    <p className="chart-card-sub">Sentinel-2 sobre {form.municipality}</p>
                  </div>
                  <div className="chart-legend-pills">
                    <span className="legend-pill" style={{ color: "#16a34a", borderColor: "rgba(22,163,74,0.25)", background: "rgba(22,163,74,0.07)" }}>
                      <span className="legend-pill-dot" style={{ background: "#16a34a" }} />NDVI
                    </span>
                    <span className="legend-pill" style={{ color: "#64748b", borderColor: "rgba(100,116,139,0.2)", background: "rgba(100,116,139,0.07)" }}>
                      <span className="legend-pill-dot" style={{ background: "#64748b" }} />Escena reciente
                    </span>
                  </div>
                </div>

                {satelliteLoading ? (
                  <div style={{ padding: "1rem", borderRadius: 12, background: "rgba(15,23,42,0.03)", color: "var(--text-secondary)", fontSize: "0.82rem" }}>
                    Consultando observacion satelital para Guatemala...
                  </div>
                ) : satellite ? (
                  <div style={{ display: "grid", gap: "0.9rem" }}>
                    <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1.4fr) minmax(220px, 0.9fr)", gap: "0.9rem" }}>
                      <div style={{ background: "var(--surface-alt)", border: "1px solid var(--border)", borderRadius: 12, padding: "0.95rem" }}>
                        <p style={{ margin: 0, fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", fontWeight: 800 }}>
                          Estado satelital
                        </p>
                        <div style={{ display: "flex", alignItems: "baseline", gap: "0.55rem", marginTop: "0.4rem", flexWrap: "wrap" }}>
                          <span style={{ fontSize: "2rem", fontWeight: 900, color: ndviStatus.color, lineHeight: 1 }}>
                            {ndviValue == null ? "--" : ndviValue.toFixed(2)}
                          </span>
                          <span style={{ fontSize: "0.78rem", color: "var(--text-secondary)" }}>
                            NDVI actual
                          </span>
                        </div>
                        <div style={{ marginTop: "0.55rem", display: "inline-flex", fontSize: "0.72rem", fontWeight: 800, padding: "0.3rem 0.6rem", borderRadius: 999, background: ndviStatus.bg, color: ndviStatus.color }}>
                          {ndviStatus.label}
                        </div>
                        <p style={{ margin: "0.6rem 0 0", fontSize: "0.78rem", color: "var(--text-secondary)", lineHeight: 1.55 }}>
                          {satellite.ndvi?.available
                            ? ndviStatus.note
                            : satellite.ndvi?.message || "Solo se encontro la escena reciente; no hay indice disponible en este momento."}
                        </p>
                        {satellite.ndvi?.available && satellite.ndvi.latest_interval && (
                          <p style={{ margin: "0.45rem 0 0", fontSize: "0.72rem", color: "var(--text-muted)" }}>
                            Ventana NDVI: {formatSceneDate(satellite.ndvi.latest_interval.from)} - {formatSceneDate(satellite.ndvi.latest_interval.to)}
                          </p>
                        )}
                      </div>

                      <div style={{ background: "var(--surface-alt)", border: "1px solid var(--border)", borderRadius: 12, padding: "0.95rem" }}>
                        <p style={{ margin: 0, fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", fontWeight: 800 }}>
                          Ultima escena
                        </p>
                        <p style={{ margin: "0.45rem 0 0", fontSize: "0.92rem", fontWeight: 800, color: "var(--text-primary)" }}>
                          {formatSceneDate(satellite.latest_scene?.datetime)}
                        </p>
                        <p style={{ margin: "0.3rem 0 0", fontSize: "0.78rem", color: "var(--text-secondary)" }}>
                          Nubes: <strong>{satellite.latest_scene?.cloud_cover ?? "s/d"}%</strong>
                        </p>
                        <p style={{ margin: "0.3rem 0 0", fontSize: "0.78rem", color: "var(--text-secondary)" }}>
                          Plataforma: <strong>{satellite.latest_scene?.platform || "Sentinel-2"}</strong>
                        </p>
                        <p style={{ margin: "0.3rem 0 0", fontSize: "0.72rem", color: "var(--text-muted)", lineHeight: 1.55 }}>
                          {satellite.configured_for_ndvi
                            ? "Tu backend esta listo para calcular NDVI sobre la escena mas reciente."
                            : "Sin credenciales CDSE: por ahora solo se muestra la escena publica mas reciente."}
                        </p>
                      </div>
                    </div>

                    {satellite.latest_scene?.thumbnail && (
                      <div style={{ background: "var(--surface-alt)", border: "1px solid var(--border)", borderRadius: 12, padding: "0.9rem" }}>
                        <p style={{ margin: "0 0 0.55rem", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", fontWeight: 800 }}>
                          Vista satelital reciente
                        </p>
                        <img
                          src={satellite.latest_scene.thumbnail}
                          alt={`Escena satelital reciente de ${form.municipality}`}
                          style={{ width: "100%", borderRadius: 10, border: "1px solid rgba(15,23,42,0.08)", objectFit: "cover", maxHeight: 220 }}
                        />
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ padding: "1rem", borderRadius: 12, background: "rgba(15,23,42,0.03)", color: "var(--text-secondary)", fontSize: "0.82rem", lineHeight: 1.6 }}>
                    No se pudo cargar la referencia satelital para este municipio.
                  </div>
                )}
              </div>

            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
