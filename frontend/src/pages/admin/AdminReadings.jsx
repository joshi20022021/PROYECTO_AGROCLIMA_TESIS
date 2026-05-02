import { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const PAGE_SIZE = 20;

export default function AdminReadings() {
  const [rows, setRows]     = useState([]);
  const [total, setTotal]   = useState(0);
  const [page, setPage]     = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({ limit: PAGE_SIZE, offset: page * PAGE_SIZE });
    fetch(`${API}/admin/readings?${params}`, {
      headers: { "X-Admin-Token": "agroclima-admin-2024" },
    })
      .then((r) => r.json())
      .then((d) => { setRows(d.items ?? []); setTotal(d.total ?? 0); })
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, [page]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="page-content">
      <div className="card">
        <div className="card-header">
          <h3>Lecturas de sensores Arduino</h3>
          <span className="chip">{total.toLocaleString()} registros</span>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          {loading ? (
            <p style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>Cargando...</p>
          ) : (
            <div className="table-wrap" style={{ borderRadius: 0, border: "none" }}>
              <table>
                <thead>
                  <tr>
                    <th>Timestamp</th><th>Departamento</th><th>Cultivo</th>
                    <th>Temp</th><th>Humedad</th><th>Suelo</th>
                    <th>Luz (lux)</th><th>Verdor</th><th>pH</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.length === 0 ? (
                    <tr><td colSpan={9} style={{ textAlign: "center", padding: "2rem", color: "var(--text-muted)" }}>
                      Sin lecturas registradas. Conecta el Arduino para comenzar.
                    </td></tr>
                  ) : rows.map((r) => (
                    <tr key={r.id}>
                      <td style={{ fontSize: "0.75rem", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                        {new Date(r.timestamp).toLocaleString("es-GT", { dateStyle: "short", timeStyle: "short" })}
                      </td>
                      <td style={{ fontWeight: 600 }}>{r.municipio ?? "—"}</td>
                      <td>{r.cultivo ?? "—"}</td>
                      <td>{r.temperatura != null ? r.temperatura.toFixed(1) + "°C" : "—"}</td>
                      <td>{r.humedad != null ? r.humedad.toFixed(0) + "%" : "—"}</td>
                      <td>{r.soil_moisture != null ? r.soil_moisture.toFixed(3) : "—"}</td>
                      <td>{r.light_lux != null ? r.light_lux.toFixed(0) : "—"}</td>
                      <td>{r.greenness_idx != null ? r.greenness_idx.toFixed(1) + "%" : "—"}</td>
                      <td>{r.ph_suelo != null ? r.ph_suelo.toFixed(1) : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        {totalPages > 1 && (
          <div style={{ padding: "0.75rem 1.15rem", display: "flex", justifyContent: "flex-end", gap: "0.5rem", borderTop: "1px solid var(--border)" }}>
            <button onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0}
              className="btn-secondary" style={{ padding: "0.3rem 0.7rem", fontSize: "0.78rem" }}>Anterior</button>
            <span style={{ fontSize: "0.78rem", color: "var(--text-muted)", alignSelf: "center" }}>
              Pag. {page + 1} / {totalPages}
            </span>
            <button onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1}
              className="btn-secondary" style={{ padding: "0.3rem 0.7rem", fontSize: "0.78rem" }}>Siguiente</button>
          </div>
        )}
      </div>
    </div>
  );
}
