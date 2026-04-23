import { calculateRisk, getRiskLabel } from "../utils/riskUtils";

export default function Dataset({ dataset }) {
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
          {
            label: "pH promedio",
            value: (dataset.reduce((s, e) => s + e.soilPh, 0) / dataset.length).toFixed(2),
            sub: "Promedio general del lote",
          },
          {
            label: "Temp. promedio",
            value: `${(dataset.reduce((s, e) => s + e.temperature, 0) / dataset.length).toFixed(1)}°C`,
            sub: "Temperatura media registrada",
          },
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
