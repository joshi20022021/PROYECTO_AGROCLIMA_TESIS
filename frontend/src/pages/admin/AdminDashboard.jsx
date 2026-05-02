import { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const STAT_ICONS = {
  predicciones: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
    </svg>
  ),
  lecturas: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="2" y="7" width="20" height="14" rx="2"/>
      <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>
    </svg>
  ),
  alertas: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
      <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>
  ),
  modelo: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
    </svg>
  ),
};

export default function AdminDashboard() {
  const [stats, setStats]   = useState(null);
  const [dbOk, setDbOk]     = useState(null);
  const [apiOk, setApiOk]   = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/health`).then((r) => r.json()).catch(() => null),
      fetch(`${API}/admin/stats`, { headers: { "X-Admin-Token": "agroclima-admin-2024" } })
        .then((r) => r.json()).catch(() => null),
    ]).then(([health, adminStats]) => {
      setApiOk(!!health);
      setDbOk(health?.db_online ?? false);
      setStats(adminStats);
      setLoading(false);
    });
  }, []);

  const statCards = stats ? [
    { key: "predicciones", label: "Predicciones totales",  value: stats.predicciones ?? 0,  color: "#16a34a" },
    { key: "lecturas",     label: "Lecturas Arduino",       value: stats.lecturas_arduino ?? 0, color: "#2563eb" },
    { key: "alertas",      label: "Alertas registradas",    value: stats.alertas ?? 0,       color: "#b45309" },
    { key: "modelo",       label: "Version modelo activo",  value: stats.modelo_activo ?? "v2.0", color: "#7c3aed" },
  ] : [];

  const modelCoverage = [
    { label: "Municipios en el modelo", value: 61, detail: "8 zonas agroclimaticas de Guatemala" },
    { label: "Registros de entrenamiento", value: "812,520", detail: "Open-Meteo, 2010-2024" },
    { label: "Cultivos modelados", value: 37, detail: "Granos, hortalizas, frutas y comerciales" },
  ];

  return (
    <div className="page-content">
      {/* Estado del sistema */}
      <div className="card">
        <div className="card-header">
          <h3>Estado del sistema</h3>
          <span className="chip">{loading ? "Verificando..." : "Actualizado"}</span>
        </div>
        <div className="card-body">
          <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
            {[
              { label: "API FastAPI",    ok: apiOk },
              { label: "PostgreSQL DB",  ok: dbOk  },
              { label: "Modelo XGBoost", ok: !!stats?.modelo_activo },
            ].map((s) => (
              <div key={s.label} className={`status-badge ${s.ok === null ? "unknown" : s.ok ? "ok" : "error"}`}>
                <div className="status-badge-dot" />
                <span style={{ color: "var(--text-primary)" }}>{s.label}</span>
                <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginLeft: "0.25rem" }}>
                  {s.ok === null ? "—" : s.ok ? "Activo" : "Inactivo"}
                </span>
              </div>
            ))}
          </div>

          {dbOk === false && (
            <div style={{
              marginTop: "1rem", padding: "0.75rem 1rem",
              background: "rgba(239,68,68,0.06)", border: "1px solid rgba(239,68,68,0.2)",
              borderRadius: 8, fontSize: "0.82rem", color: "#ef4444",
            }}>
              Base de datos no disponible. Ejecuta: <code style={{ fontFamily: "monospace", background: "rgba(0,0,0,0.06)", padding: "0.1rem 0.4rem", borderRadius: 4 }}>docker-compose up -d</code>
            </div>
          )}
        </div>
      </div>

      {/* KPI cards */}
      {stats && (
        <div className="stat-grid-3" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
          {statCards.map((c) => (
            <div key={c.key} className="card" style={{ padding: "1rem 1.15rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.5rem" }}>
                <span className="kpi-label">{c.label}</span>
                <span style={{ color: c.color, opacity: 0.7 }}>{STAT_ICONS[c.key]}</span>
              </div>
              <div className="kpi-value" style={{ color: c.color }}>{c.value}</div>
            </div>
          ))}
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <h3>Cobertura del modelo</h3>
          <span className="chip">Datos tecnicos</span>
        </div>
        <div className="card-body" style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.75rem" }}>
          {modelCoverage.map((item) => (
            <div key={item.label} style={{ padding: "0.9rem 1rem", borderRadius: 8, border: "1px solid var(--border)", background: "var(--surface-alt)" }}>
              <span className="kpi-label">{item.label}</span>
              <div className="kpi-value" style={{ color: "var(--text-primary)" }}>{item.value}</div>
              <p className="kpi-sub" style={{ marginBottom: 0 }}>{item.detail}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Ultimas predicciones */}
      {stats?.ultimas_predicciones?.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3>Ultimas predicciones</h3>
            <span className="chip">{stats.ultimas_predicciones.length} registros recientes</span>
          </div>
          <div className="card-body" style={{ padding: 0 }}>
            <div className="table-wrap" style={{ borderRadius: 0, border: "none" }}>
              <table>
                <thead>
                  <tr>
                    <th>Fecha</th><th>Departamento</th><th>Cultivo</th>
                    <th>Rendimiento</th><th>Nivel</th><th>Fuente</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.ultimas_predicciones.map((p) => (
                    <tr key={p.id}>
                      <td style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                        {new Date(p.timestamp).toLocaleString("es-GT", { dateStyle: "short", timeStyle: "short" })}
                      </td>
                      <td style={{ fontWeight: 600 }}>{p.municipio}</td>
                      <td>{p.cultivo}</td>
                      <td style={{ fontWeight: 700 }}>{p.yield_pct?.toFixed(1)}%</td>
                      <td>
                        <span className={`status-pill ${p.yield_level === "alto" ? "low" : p.yield_level === "medio" ? "medium" : "high"}`}>
                          {p.yield_level}
                        </span>
                      </td>
                      <td><span className="chip" style={{ fontSize: "0.72rem" }}>{p.fuente}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {!stats && !loading && (
        <div className="card">
          <div className="card-body" style={{ textAlign: "center", padding: "2rem", color: "var(--text-muted)" }}>
            No se pudo conectar con la API. Verifica que el backend este en ejecucion.
          </div>
        </div>
      )}
    </div>
  );
}
