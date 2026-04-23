import { useEffect, useMemo, useState } from "react";
import ChartCanvas from "../components/ChartCanvas";
import { compareModels, getModelInfo, retrainModel } from "../services/api";

const GROUP_COLOR = {
  clima: { bar: "#2563eb", bg: "rgba(37,99,235,0.12)", label: "Clima" },
  suelo: { bar: "#16a34a", bg: "rgba(22,163,74,0.12)", label: "Suelo" },
  cultivo: { bar: "#b45309", bg: "rgba(180,83,9,0.12)", label: "Cultivo" },
  sensor: { bar: "#7c3aed", bg: "rgba(124,58,237,0.12)", label: "Sensor" },
  tiempo: { bar: "#0891b2", bg: "rgba(8,145,178,0.12)", label: "Tiempo" },
  lugar: { bar: "#64748b", bg: "rgba(100,116,139,0.12)", label: "Lugar" },
  otros: { bar: "#475569", bg: "rgba(71,85,105,0.12)", label: "Otros" },
};

function fmtPct(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "N/D";
  return `${(Number(value) * 100).toFixed(digits)}%`;
}

function fmtNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "N/D";
  return Number(value).toLocaleString();
}

function fmtSignedPct(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "N/D";
  return `${(Number(value) * 100).toFixed(2)}%`;
}

function fmtDate(value) {
  if (!value) return "N/D";
  try {
    return new Date(value).toLocaleString("es-GT");
  } catch {
    return value;
  }
}

export default function Models() {
  const [modelInfo, setModelInfo] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(true);
  const [compareLoading, setCompareLoading] = useState(false);
  const [retrainLoading, setRetrainLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState("");

  async function loadModelPanel() {
    setLoading(true);
    try {
      const info = await getModelInfo();
      setModelInfo(info);
      setComparison(info.comparison || null);
    } catch {
      setModelInfo(null);
      setComparison(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadModelPanel();
  }, []);

  useEffect(() => {
    if (!modelInfo?.retraining?.running) return undefined;
    const timer = setInterval(() => {
      getModelInfo().then((info) => {
        setModelInfo(info);
        setComparison(info.comparison || null);
      }).catch(() => {});
    }, 5000);
    return () => clearInterval(timer);
  }, [modelInfo?.retraining?.running]);

  const model = modelInfo?.model;
  const retraining = modelInfo?.retraining;
  const featureImportance = model?.featureImportance || [];

  const groupedImportance = useMemo(() => {
    const totals = {};
    featureImportance.forEach((item) => {
      totals[item.group] = (totals[item.group] || 0) + Number(item.imp || 0);
    });
    return Object.entries(totals)
      .map(([key, value]) => ({
        key,
        label: GROUP_COLOR[key]?.label || key,
        value,
        color: GROUP_COLOR[key]?.bar || GROUP_COLOR.otros.bar,
        bg: GROUP_COLOR[key]?.bg || GROUP_COLOR.otros.bg,
      }))
      .sort((a, b) => b.value - a.value);
  }, [featureImportance]);

  const importanceChart = useMemo(() => ({
    type: "bar",
    data: {
      labels: featureImportance.map((item) => item.label),
      datasets: [{
        label: "Importancia porcentual",
        data: featureImportance.map((item) => +(Number(item.imp || 0) * 100).toFixed(2)),
        backgroundColor: featureImportance.map((item) => (GROUP_COLOR[item.group] || GROUP_COLOR.otros).bg),
        borderColor: featureImportance.map((item) => (GROUP_COLOR[item.group] || GROUP_COLOR.otros).bar),
        borderWidth: 1.4,
        borderRadius: 8,
        barThickness: 14,
      }],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: { right: 14 } },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.parsed.x.toFixed(2)}% del peso total`,
          },
        },
      },
      scales: {
        x: {
          suggestedMax: 32,
          grid: { color: "rgba(148,163,184,0.18)" },
          ticks: { color: "#64748b", callback: (value) => `${value}%` },
        },
        y: {
          grid: { display: false },
          ticks: { color: "#475569", font: { size: 11, weight: 600 } },
        },
      },
    },
  }), [featureImportance]);

  const precisionChart = useMemo(() => ({
    type: "doughnut",
    data: {
      labels: ["Varianza explicada", "Varianza residual"],
      datasets: [{
        data: [
          +(Number(model?.r2 || 0) * 100).toFixed(2),
          +((1 - Number(model?.r2 || 0)) * 100).toFixed(2),
        ],
        backgroundColor: ["#475569", "rgba(100,116,139,0.12)"],
        borderColor: ["#334155", "rgba(100,116,139,0.2)"],
        borderWidth: 2,
        hoverOffset: 4,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "72%",
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (ctx) => ` ${ctx.label}: ${ctx.parsed.toFixed(2)}%` } },
      },
    },
  }), [model?.r2]);

  async function handleRetrain() {
    setRetrainLoading(true);
    setActionMsg("");
    try {
      const response = await retrainModel();
      setActionMsg(response.message || "Reentrenamiento iniciado.");
      const info = await getModelInfo();
      setModelInfo(info);
      setComparison(info.comparison || null);
    } catch (error) {
      setActionMsg(`Error: ${error.message}`);
    } finally {
      setRetrainLoading(false);
    }
  }

  async function handleCompare() {
    setCompareLoading(true);
    setActionMsg("");
    try {
      const nextComparison = await compareModels({ run: true });
      setComparison(nextComparison);
      const info = await getModelInfo();
      setModelInfo(info);
    } catch (error) {
      setActionMsg(`Error: ${error.message}`);
    } finally {
      setCompareLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="page-content">
        <div className="card">
          <div className="card-body" style={{ padding: "2rem", color: "var(--text-secondary)" }}>
            Cargando panel de modelos...
          </div>
        </div>
      </div>
    );
  }

  if (!model) {
    return (
      <div className="page-content">
        <div className="card">
          <div className="card-body" style={{ padding: "2rem", color: "#dc2626" }}>
            No se pudo leer la informacion del modelo activo.
          </div>
        </div>
      </div>
    );
  }

  const rows = [
    { label: "R² test", key: "r2", fmt: (v) => fmtPct(v), higher: true },
    { label: "R² cross-validation", key: "crossval_r2", fmt: (v) => fmtPct(v), higher: true },
    { label: "MAE", key: "mae", fmt: (v) => `${Number(v).toFixed(2)}%`, higher: false },
    { label: "RMSE", key: "rmse", fmt: (v) => `${Number(v).toFixed(2)}%`, higher: false },
    { label: "Tiempo de entreno", key: "train_time_s", fmt: (v) => `${v}s`, higher: false },
  ];

  const xgb = comparison?.results?.XGBoost;
  const rf = comparison?.results?.RandomForest;

  return (
    <div className="page-content">
      <section className="model-hero">
        <div>
          <div className="model-hero-eyebrow">Modelo principal de produccion</div>
          <h3>{model.name}</h3>
          <p>
            Panel operativo del modelo activo. Esta vista ahora lee metadata real del backend,
            el artefacto XGBoost cargado y el estado actual del reentrenamiento.
          </p>
        </div>
        <div className="model-hero-meta">
          <div className="chip">{model.status}</div>
          <div className="model-meta-grid">
            <div>
              <span>Version</span>
              <strong>{model.version || "N/D"}</strong>
            </div>
            <div>
              <span>Dataset</span>
              <strong>{model.dataset || "N/D"}</strong>
            </div>
            <div>
              <span>Entrenado</span>
              <strong>{fmtDate(model.trained_at)}</strong>
            </div>
            <div>
              <span>Cobertura</span>
              <strong>{fmtNumber(model.nCrops)} cultivos</strong>
            </div>
          </div>
        </div>
      </section>

      <div className="ml-score-grid">
        {[
          {
            label: "R2 del modelo",
            value: fmtPct(model.r2, 1),
            desc: `Validacion cruzada: ${fmtPct(model.crossValR2)} +/- ${fmtSignedPct(model.crossValStd)}`,
            color: "var(--green)",
          },
          {
            label: "MAE",
            value: model.mae != null ? `${Number(model.mae).toFixed(2)}%` : "N/D",
            desc: "Error absoluto promedio sobre rendimiento proyectado",
            color: "var(--text-secondary)",
          },
          {
            label: "RMSE",
            value: model.rmse != null ? `${Number(model.rmse).toFixed(2)}%` : "N/D",
            desc: `Sensibilidad a errores grandes sobre ${fmtNumber(model.testSamples)} muestras de test`,
            color: "var(--text-secondary)",
          },
          {
            label: "Variables activas",
            value: fmtNumber(model.nFeatures),
            desc: `${fmtNumber(model.totalRows)} filas y ${fmtNumber(model.coveredMunicipalities)} municipios`,
            color: "var(--blue)",
          },
        ].map((card) => (
          <div key={card.label} className="ml-score-card">
            <p className="score-label">{card.label}</p>
            <div className="score-value" style={{ color: card.color }}>{card.value}</div>
            <p className="score-desc">{card.desc}</p>
          </div>
        ))}
      </div>

      <div className="models-layout">
        <div className="card">
          <div className="card-header">
            <h3>Importancia de variables</h3>
            <span className="chip blue">{fmtNumber(featureImportance.length)} features desde el modelo</span>
          </div>
          <div className="card-body">
            <div className="models-group-chips">
              {groupedImportance.map((group) => (
                <span key={group.key} className="chip" style={{ background: group.bg, color: group.color, border: `1px solid ${group.color}` }}>
                  {group.label} {(group.value * 100).toFixed(1)}%
                </span>
              ))}
            </div>
            <div className="models-chart-wrap">
              <ChartCanvas config={importanceChart} />
            </div>
            <div className="models-feature-list">
              {featureImportance.slice(0, 5).map((item, index) => (
                <div key={item.feature} className="models-feature-item">
                  <span className="models-feature-rank">0{index + 1}</span>
                  <div>
                    <strong>{item.label}</strong>
                    <p>{item.source}</p>
                  </div>
                  <span style={{ color: (GROUP_COLOR[item.group] || GROUP_COLOR.otros).bar }}>
                    {(Number(item.imp) * 100).toFixed(2)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="models-side-column">
          <div className="card">
            <div className="card-header">
              <h3>Lectura de desempeno</h3>
              <span className="chip">{model.version || "sin version"}</span>
            </div>
            <div className="card-body">
              <div className="models-donut-wrap">
                <div className="models-donut-chart">
                  <ChartCanvas config={precisionChart} />
                </div>
                <div className="models-donut-copy">
                  <strong>{fmtPct(model.r2, 1)} explicado</strong>
                  <p>
                    El panel usa las metricas reales del modelo activo y no una ficha estatica.
                  </p>
                </div>
              </div>

              <div className="models-metric-table">
                {[
                  ["R2 test", fmtPct(model.r2, 2)],
                  ["R2 cross-validation", fmtPct(model.crossValR2, 2)],
                  ["Desviacion cross-validation", fmtSignedPct(model.crossValStd)],
                  ["Muestras de entrenamiento", fmtNumber(model.trainSamples)],
                  ["Muestras de prueba", fmtNumber(model.testSamples)],
                  ["Ventana temporal", model.yearsRange || "N/D"],
                  ["Dataset", model.dataset || "N/D"],
                  ["Modelo cargado", model.modelLoaded ? "Si" : "No"],
                ].map(([label, value]) => (
                  <div key={label} className="models-metric-row">
                    <span>{label}</span>
                    <strong>{value}</strong>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h3>Estado de reentrenamiento</h3>
              <span className={`chip ${retraining?.running ? "orange" : "green"}`}>
                {retraining?.running ? "En proceso" : retraining?.last_status || "inactivo"}
              </span>
            </div>
            <div className="card-body">
              <div className="models-metric-table">
                {[
                  ["Ultimo inicio", fmtDate(retraining?.last_started)],
                  ["Ultimo fin", fmtDate(retraining?.last_finished)],
                  ["Estado", retraining?.last_status || "N/D"],
                  ["Ultimo error", retraining?.last_error || "Sin errores"],
                ].map(([label, value]) => (
                  <div key={label} className="models-metric-row">
                    <span>{label}</span>
                    <strong style={{ maxWidth: 220, textAlign: "right", overflowWrap: "anywhere" }}>{value}</strong>
                  </div>
                ))}
              </div>
              <button className="btn btn-secondary" style={{ marginTop: 16 }} disabled={retrainLoading || retraining?.running} onClick={handleRetrain}>
                {retrainLoading ? "Iniciando..." : retraining?.running ? "Reentrenando..." : "Reentrenar modelo"}
              </button>
              {actionMsg && (
                <p style={{ marginTop: 12, fontSize: 12, color: actionMsg.startsWith("Error") ? "#dc2626" : "#16a34a" }}>
                  {actionMsg}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 24 }}>
        <div className="card-header">
          <h3>Comparativa de modelos</h3>
          <span className="chip blue">Evaluacion formal</span>
        </div>
        <div className="card-body">
          <p style={{ color: "var(--text-secondary)", marginBottom: 16, fontSize: 13 }}>
            XGBoost es el modelo en produccion. Random Forest se mantiene como linea base para
            documentar la ventaja del boosting cuando se ejecuta una comparacion formal.
          </p>

          {!comparison && (
            <div style={{ color: "var(--text-secondary)", fontSize: 13, padding: "12px 0" }}>
              No hay comparacion disponible todavia.
            </div>
          )}

          {comparison && (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border)" }}>
                    <th style={{ textAlign: "left", padding: "8px 12px", color: "var(--text-secondary)", fontWeight: 600 }}>Metrica</th>
                    <th style={{ textAlign: "center", padding: "8px 12px", color: "#2563eb", fontWeight: 700 }}>XGBoost</th>
                    <th style={{ textAlign: "center", padding: "8px 12px", color: "#64748b", fontWeight: 700 }}>Random Forest</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map(({ label, key, fmt, higher }) => {
                    const xVal = xgb?.[key];
                    const rVal = rf?.[key];
                    const xWins = xVal != null && rVal != null && (higher ? xVal > rVal : xVal < rVal);
                    const rWins = xVal != null && rVal != null && (higher ? rVal > xVal : rVal < xVal);
                    return (
                      <tr key={key} style={{ borderBottom: "1px solid var(--border)" }}>
                        <td style={{ padding: "8px 12px", color: "var(--text-secondary)" }}>{label}</td>
                        <td style={{ padding: "8px 12px", textAlign: "center", fontWeight: 700, color: xWins ? "#16a34a" : "var(--text-primary)" }}>
                          {xVal != null ? fmt(xVal) : "N/D"}
                          {xWins && <span style={{ marginLeft: 6, fontSize: 11, color: "#16a34a" }}>▲</span>}
                        </td>
                        <td style={{ padding: "8px 12px", textAlign: "center", fontWeight: 600, color: rWins ? "#16a34a" : rVal == null ? "var(--text-secondary)" : "var(--text-primary)" }}>
                          {rVal != null ? fmt(rVal) : <span style={{ fontSize: 12, fontStyle: "italic" }}>pendiente</span>}
                          {rWins && <span style={{ marginLeft: 6, fontSize: 11, color: "#16a34a" }}>▲</span>}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {comparison.compared_at && (
                <p style={{ marginTop: 12, fontSize: 11, color: "var(--text-secondary)" }}>
                  Ultima comparacion: {fmtDate(comparison.compared_at)} · {fmtNumber(comparison.n_train)} muestras entreno / {fmtNumber(comparison.n_test)} test
                </p>
              )}
              {!comparison.compared_at && comparison.note && (
                <p style={{ marginTop: 12, fontSize: 11, color: "var(--text-secondary)", fontStyle: "italic" }}>
                  {comparison.note}
                </p>
              )}
            </div>
          )}

          <button className="btn btn-secondary" style={{ marginTop: 16 }} disabled={compareLoading} onClick={handleCompare}>
            {compareLoading ? "Generando comparacion..." : "Generar comparacion formal"}
          </button>
        </div>
      </div>
    </div>
  );
}
