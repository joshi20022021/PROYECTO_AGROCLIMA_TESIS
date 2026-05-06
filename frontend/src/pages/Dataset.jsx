import { calculateRisk, getRiskLabel } from "../utils/riskUtils";

function fmtDate(ts) {
  if (!ts) return "—";
  const d = new Date(ts);
  if (isNaN(d.getTime())) return "—";
  return d.toLocaleString("es-GT", { dateStyle: "short", timeStyle: "short" });
}

export default function Dataset({ dataset }) {
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
          <span className="chip">{dataset.length} registros</span>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          <p style={{ padding: "0.75rem 1.15rem", fontSize: "0.82rem", color: "var(--text-muted)", borderBottom: "1px solid var(--border)", margin: 0 }}>
            Registro central de precipitacion, temperatura, humedad y pH del suelo para los cultivos priorizados de la investigacion.
          </p>
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
                  <th>Nivel de riesgo</th>
                  <th>Puntuacion</th>
                </tr>
              </thead>
              <tbody>
                {dataset.map((entry, i) => {
                  const risk = calculateRisk(entry);
                  return (
                    <tr key={`${entry.municipality}-${entry.crop}-${i}`}>
                      <td style={{ fontSize: "0.74rem", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                        {fmtDate(entry.timestamp)}
                      </td>
                      <td style={{ fontWeight: 600, color: "var(--text-primary)" }}>{entry.municipality}</td>
                      <td>{entry.crop}</td>
                      <td>{entry.rainfall} mm</td>
                      <td>{entry.temperature}°C</td>
                      <td>{entry.humidity}%</td>
                      <td>{entry.soilPh}</td>
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
