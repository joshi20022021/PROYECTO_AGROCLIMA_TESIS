import { useEffect, useMemo, useState } from "react";
import ChartCanvas from "../components/ChartCanvas";
import { calculateRisk, getRiskLabel } from "../utils/riskUtils";

function fmtDate(ts) {
  if (!ts) return "—";
  const d = new Date(ts);
  if (isNaN(d.getTime())) return "—";
  return d.toLocaleString("es-GT", { dateStyle: "short", timeStyle: "short" });
}

export default function Dataset({ dataset }) {
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    crop: "Todos",
    department: "Todos",
    from: "",
    to: "",
  });

  useEffect(() => {
    const id = window.setTimeout(() => setLoading(false), 350);
    return () => window.clearTimeout(id);
  }, []);

  const normalizedDataset = useMemo(() => (
    (dataset || []).map((entry, index) => {
      const risk = calculateRisk(entry);
      const yieldPct = Number(entry.yieldPct ?? entry.yield_pct ?? Math.max(0, 100 - risk.score));
      return {
        ...entry,
        _index: index,
        _risk: risk,
        yieldPct: Number.isFinite(yieldPct) ? yieldPct : 0,
      };
    })
  ), [dataset]);

  const crops = useMemo(() => ["Todos", ...new Set(normalizedDataset.map((entry) => entry.crop).filter(Boolean))], [normalizedDataset]);
  const departments = useMemo(() => ["Todos", ...new Set(normalizedDataset.map((entry) => entry.municipality).filter(Boolean))], [normalizedDataset]);

  const filteredDataset = useMemo(() => {
    const fromTime = filters.from ? new Date(`${filters.from}T00:00:00`).getTime() : null;
    const toTime = filters.to ? new Date(`${filters.to}T23:59:59`).getTime() : null;
    return normalizedDataset.filter((entry) => {
      const entryTime = entry.timestamp ? new Date(entry.timestamp).getTime() : null;
      if (filters.crop !== "Todos" && entry.crop !== filters.crop) return false;
      if (filters.department !== "Todos" && entry.municipality !== filters.department) return false;
      if (fromTime && entryTime && entryTime < fromTime) return false;
      if (toTime && entryTime && entryTime > toTime) return false;
      return true;
    });
  }, [filters, normalizedDataset]);

  const trendChart = useMemo(() => {
    const ordered = [...filteredDataset].reverse();
    return {
      type: "line",
      data: {
        labels: ordered.map((entry, index) => entry.timestamp ? new Date(entry.timestamp).toLocaleDateString("es-GT") : `Reg ${index + 1}`),
        datasets: [{
          label: "yield_pct",
          data: ordered.map((entry) => Number(entry.yieldPct.toFixed(1))),
          borderColor: "#246222",
          backgroundColor: "rgba(38,99,36,0.12)",
          pointBackgroundColor: "#246222",
          pointRadius: 4,
          tension: 0.35,
          fill: true,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (ctx) => ` yield_pct: ${ctx.parsed.y.toFixed(1)}%` } },
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: "#64748b", maxRotation: 0 } },
          y: {
            min: 0,
            max: 100,
            grid: { color: "rgba(148,163,184,0.18)" },
            ticks: { color: "#64748b", callback: (value) => `${value}%` },
          },
        },
      },
    };
  }, [filteredDataset]);

  function csvEscape(value) {
    if (value == null) return "";
    const text = String(value);
    return /[",\n]/.test(text) ? `"${text.replace(/"/g, "\"\"")}"` : text;
  }

  function exportFilteredCsv() {
    const headers = ["fecha", "departamento", "cultivo", "precipitacion_mm", "temperatura_c", "humedad_pct", "ph_suelo", "yield_pct", "riesgo_nivel", "riesgo_score"];
    const rows = filteredDataset.map((entry) => [
      entry.timestamp || "",
      entry.municipality,
      entry.crop,
      entry.rainfall,
      entry.temperature,
      entry.humidity,
      entry.soilPh,
      entry.yieldPct.toFixed(2),
      entry._risk.level,
      entry._risk.score,
    ]);
    const csv = [headers, ...rows].map((row) => row.map(csvEscape).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = Object.assign(document.createElement("a"), {
      href: url,
      download: `dataset_agroclima_${new Date().toISOString().slice(0, 10)}.csv`,
    });
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loading) {
    return (
      <div className="page-content">
        <div className="card">
          <div className="card-body skeleton-panel">
            <div className="skeleton-line wide" />
            <div className="skeleton-line" />
            <div className="skeleton-box" />
          </div>
        </div>
      </div>
    );
  }

  if (!dataset || dataset.length === 0) {
    return (
      <div className="page-content">
        <div className="card">
          <div className="card-header">
            <h3>Metricas climaticas de entrada</h3>
            <span className="chip">0 registros</span>
          </div>
          <div className="card-body" style={{ textAlign: "center", padding: "3rem 1.5rem", color: "var(--text-muted)" }}>
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ opacity: 0.3, marginBottom: "0.75rem" }}>
              <path d="M3 3h18v4H3z"/><path d="M3 10h18v4H3z"/><path d="M3 17h18v4H3z"/>
            </svg>
            <p style={{ margin: 0, fontSize: "0.9rem", fontWeight: 600 }}>No hay registros aun</p>
            <p style={{ margin: "0.4rem 0 0", fontSize: "0.8rem", lineHeight: 1.6 }}>
              Ve a <strong>Inicio</strong>, ingresa las metricas del lote y pulsa <strong>Analizar riesgo</strong> para agregar datos aqui.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const avgPh   = dataset.reduce((s, e) => s + e.soilPh, 0) / dataset.length;
  const avgTemp = dataset.reduce((s, e) => s + e.temperature, 0) / dataset.length;

  return (
    <div className="page-content">
      <div className="card">
        <div className="card-header">
          <h3>Metricas climaticas de entrada</h3>
          <span className="chip">{filteredDataset.length}/{dataset.length} registros</span>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          <p style={{ padding: "0.75rem 1.15rem", fontSize: "0.82rem", color: "var(--text-muted)", borderBottom: "1px solid var(--border)", margin: 0 }}>
            Registro central de precipitacion, temperatura, humedad y pH del suelo para los cultivos priorizados de la investigacion.
          </p>
          <div className="dataset-filters">
            <label className="form-label">
              Cultivo
              <select className="form-select" value={filters.crop} onChange={(e) => setFilters((prev) => ({ ...prev, crop: e.target.value }))}>
                {crops.map((item) => <option key={item}>{item}</option>)}
              </select>
            </label>
            <label className="form-label">
              Departamento
              <select className="form-select" value={filters.department} onChange={(e) => setFilters((prev) => ({ ...prev, department: e.target.value }))}>
                {departments.map((item) => <option key={item}>{item}</option>)}
              </select>
            </label>
            <label className="form-label">
              Desde
              <input className="form-input" type="date" value={filters.from} onChange={(e) => setFilters((prev) => ({ ...prev, from: e.target.value }))} />
            </label>
            <label className="form-label">
              Hasta
              <input className="form-input" type="date" value={filters.to} onChange={(e) => setFilters((prev) => ({ ...prev, to: e.target.value }))} />
            </label>
            <button className="btn ghost" type="button" onClick={exportFilteredCsv}>Exportar CSV</button>
          </div>
          <div className="dataset-trend">
            <div className="dataset-trend-copy">
              <span className="kpi-label">Tendencia de rendimiento</span>
              <strong>{filteredDataset.length ? `${(filteredDataset.reduce((sum, entry) => sum + entry.yieldPct, 0) / filteredDataset.length).toFixed(1)}%` : "N/D"}</strong>
              <p>Serie temporal de yield_pct por filtros activos.</p>
            </div>
            <div className="dataset-trend-chart">
              <ChartCanvas config={trendChart} />
            </div>
          </div>
          <div className="table-wrap" style={{ borderRadius: 0, border: "none" }}>
            <table>
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Departamento</th>
                  <th>Cultivo</th>
                  <th>Precipitacion</th>
                  <th>Temperatura</th>
                  <th>Humedad</th>
                  <th>pH suelo</th>
                  <th>Yield pct</th>
                  <th>Nivel de riesgo</th>
                  <th>Puntuacion</th>
                </tr>
              </thead>
              <tbody>
                {filteredDataset.map((entry, i) => {
                  const risk = entry._risk;
                  return (
                    <tr key={`${entry.municipality}-${entry.crop}-${entry._index}`}>
                      <td style={{ fontSize: "0.74rem", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                        {fmtDate(entry.timestamp)}
                      </td>
                      <td style={{ fontWeight: 600, color: "var(--text-primary)" }}>{entry.municipality}</td>
                      <td>{entry.crop}</td>
                      <td>{entry.rainfall} mm</td>
                      <td>{entry.temperature}°C</td>
                      <td>{entry.humidity}%</td>
                      <td>{entry.soilPh}</td>
                      <td>{entry.yieldPct.toFixed(1)}%</td>
                      <td>
                        <span className={`status-pill ${risk.level}`}>
                          {getRiskLabel(risk.level)}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                          <div style={{ flex: 1, height: "6px", background: "rgba(80,60,35,0.1)", borderRadius: "999px", overflow: "hidden", minWidth: "60px" }}>
                            <div style={{
                              height: "100%",
                              width: `${risk.score}%`,
                              borderRadius: "999px",
                              background: risk.level === "high" ? "var(--red)" : risk.level === "medium" ? "var(--gold)" : "var(--green)",
                            }} />
                          </div>
                          <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-secondary)", width: "32px" }}>
                            {risk.score}
                          </span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Summary stats */}
      <div className="stat-grid-3">
        {[
          { label: "Total registros", value: dataset.length, sub: "Entradas activas en el dataset" },
          { label: "pH promedio", value: avgPh.toFixed(2), sub: "Promedio general del lote" },
          { label: "Temp. promedio", value: `${avgTemp.toFixed(1)}°C`, sub: "Temperatura media registrada" },
        ].map((stat) => (
          <div key={stat.label} className="card" style={{ padding: "1rem 1.15rem" }}>
            <span className="kpi-label">{stat.label}</span>
            <div className="kpi-value">{stat.value}</div>
            <p className="kpi-sub">{stat.sub}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
