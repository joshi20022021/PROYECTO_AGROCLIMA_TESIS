import { useEffect, useMemo, useState } from "react";
import { municipioOptions, cropOptions } from "../../data/constants";
import ChartCanvas from "../../components/ChartCanvas";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const PAGE_SIZE = 20;

function buildParams({ limit, offset, filter }) {
  return new URLSearchParams({
    limit,
    offset,
    ...(filter.municipio && { municipio: filter.municipio }),
    ...(filter.cultivo && { cultivo: filter.cultivo }),
    ...(filter.start_date && { start_date: filter.start_date }),
    ...(filter.end_date && { end_date: filter.end_date }),
  });
}

export default function AdminPredictions() {
  const [rows, setRows] = useState([]);
  const [chartRows, setChartRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [chartLoading, setChartLoading] = useState(true);
  const [filter, setFilter] = useState({
    municipio: "",
    cultivo: "",
    start_date: "",
    end_date: "",
  });

  useEffect(() => {
    setLoading(true);
    const params = buildParams({ limit: PAGE_SIZE, offset: page * PAGE_SIZE, filter });
    fetch(`${API}/admin/predictions?${params}`, {
      headers: { "X-Admin-Token": "agroclima-admin-2024" },
    })
      .then((r) => r.json())
      .then((d) => {
        setRows(d.items ?? []);
        setTotal(d.total ?? 0);
      })
      .catch(() => {
        setRows([]);
        setTotal(0);
      })
      .finally(() => setLoading(false));
  }, [page, filter]);

  useEffect(() => {
    setChartLoading(true);
    const params = buildParams({ limit: 240, offset: 0, filter });
    fetch(`${API}/admin/predictions?${params}`, {
      headers: { "X-Admin-Token": "agroclima-admin-2024" },
    })
      .then((r) => r.json())
      .then((d) => setChartRows((d.items ?? []).slice().reverse()))
      .catch(() => setChartRows([]))
      .finally(() => setChartLoading(false));
  }, [filter]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const chartStats = useMemo(() => {
    if (!chartRows.length) {
      return { avgYield: 0, maxYield: 0, minYield: 0 };
    }
    const yields = chartRows.map((row) => Number(row.yield_pct) || 0);
    const avgYield = yields.reduce((sum, value) => sum + value, 0) / yields.length;
    return {
      avgYield: avgYield.toFixed(1),
      maxYield: Math.max(...yields).toFixed(1),
      minYield: Math.min(...yields).toFixed(1),
    };
  }, [chartRows]);

  const historyChart = useMemo(() => ({
    type: "line",
    data: {
      labels: chartRows.map((row) =>
        new Date(row.timestamp).toLocaleDateString("es-GT", { day: "2-digit", month: "short" })
      ),
      datasets: [
        {
          label: "Rendimiento estimado (%)",
          data: chartRows.map((row) => Number(row.yield_pct ?? 0)),
          borderColor: "#0f766e",
          backgroundColor: "rgba(15,118,110,0.14)",
          fill: true,
          tension: 0.35,
          pointRadius: 3,
          pointHoverRadius: 5,
          pointBackgroundColor: "#0f766e",
          pointBorderColor: "#ffffff",
          pointBorderWidth: 1.5,
          borderWidth: 2.5,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => {
              const row = chartRows[items[0].dataIndex];
              return row
                ? `${row.cultivo} · ${row.municipio}`
                : items[0].label;
            },
            label: (ctx) => ` Rendimiento: ${ctx.parsed.y.toFixed(1)}%`,
            afterLabel: (ctx) => {
              const row = chartRows[ctx.dataIndex];
              return row ? ` Fuente: ${row.fuente}` : "";
            },
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: "#64748b", maxRotation: 0, autoSkip: true, maxTicksLimit: 8 },
        },
        y: {
          suggestedMin: 0,
          suggestedMax: 100,
          grid: { color: "rgba(148,163,184,0.14)" },
          ticks: {
            color: "#64748b",
            callback: (value) => `${value}%`,
          },
        },
      },
    },
  }), [chartRows]);

  function updateFilter(key, value) {
    setFilter((current) => ({ ...current, [key]: value }));
    setPage(0);
  }

  return (
    <div className="page-content">
      <div className="card">
        <div className="card-header">
          <h3>Historial de predicciones</h3>
          <span className="chip">{total.toLocaleString()} total</span>
        </div>

        <div className="card-body" style={{ borderBottom: "1px solid var(--border)", display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          {[
            { key: "municipio", placeholder: "Filtrar departamento...", opts: ["", ...municipioOptions], type: "select" },
            { key: "cultivo", placeholder: "Filtrar cultivo...", opts: ["", ...cropOptions], type: "select" },
          ].map(({ key, placeholder, opts }) => (
            <select
              key={key}
              value={filter[key]}
              onChange={(e) => updateFilter(key, e.target.value)}
              style={{
                padding: "0.45rem 0.7rem",
                borderRadius: 7,
                border: "1px solid var(--border)",
                background: "var(--surface)",
                color: "var(--text-primary)",
                fontSize: "0.82rem",
                cursor: "pointer",
              }}
            >
              {opts.map((o) => <option key={o} value={o}>{o || placeholder}</option>)}
            </select>
          ))}

          <input
            type="date"
            value={filter.start_date}
            onChange={(e) => updateFilter("start_date", e.target.value)}
            className="form-input"
            style={{ width: 170 }}
          />
          <input
            type="date"
            value={filter.end_date}
            onChange={(e) => updateFilter("end_date", e.target.value)}
            className="form-input"
            style={{ width: 170 }}
          />
          <button
            className="btn ghost"
            onClick={() => {
              setFilter({ municipio: "", cultivo: "", start_date: "", end_date: "" });
              setPage(0);
            }}
          >
            Limpiar filtros
          </button>
        </div>

        <div className="card-body" style={{ display: "grid", gap: "1rem" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: "0.75rem" }}>
            <div className="card" style={{ margin: 0 }}>
              <div className="card-body">
                <p style={{ margin: 0, fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Promedio</p>
                <strong style={{ fontSize: "1.8rem", color: "#0f766e" }}>{chartStats.avgYield}%</strong>
              </div>
            </div>
            <div className="card" style={{ margin: 0 }}>
              <div className="card-body">
                <p style={{ margin: 0, fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Maximo</p>
                <strong style={{ fontSize: "1.8rem", color: "var(--green)" }}>{chartStats.maxYield}%</strong>
              </div>
            </div>
            <div className="card" style={{ margin: 0 }}>
              <div className="card-body">
                <p style={{ margin: 0, fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Minimo</p>
                <strong style={{ fontSize: "1.8rem", color: "var(--red)" }}>{chartStats.minYield}%</strong>
              </div>
            </div>
          </div>

          <div className="card" style={{ margin: 0 }}>
            <div className="card-header">
              <h3>Rendimiento estimado por periodo</h3>
              <span className="chip blue">{chartRows.length} puntos</span>
            </div>
            <div className="card-body">
              {chartLoading ? (
                <p style={{ margin: 0, color: "var(--text-muted)" }}>Cargando grafico historico...</p>
              ) : chartRows.length === 0 ? (
                <p style={{ margin: 0, color: "var(--text-muted)" }}>No hay registros suficientes para la visualizacion con los filtros actuales.</p>
              ) : (
                <div style={{ height: 280 }}>
                  <ChartCanvas config={historyChart} />
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="card-body" style={{ padding: 0 }}>
          {loading ? (
            <p style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>Cargando...</p>
          ) : (
            <div className="table-wrap" style={{ borderRadius: 0, border: "none" }}>
              <table>
                <thead>
                  <tr>
                    <th>Fecha</th><th>Departamento</th><th>Cultivo</th><th>Mes</th>
                    <th>Temp</th><th>Lluvia</th><th>Humedad</th><th>pH</th>
                    <th>Rendimiento</th><th>Nivel</th><th>Fuente</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.length === 0 ? (
                    <tr><td colSpan={11} style={{ textAlign: "center", padding: "2rem", color: "var(--text-muted)" }}>Sin registros</td></tr>
                  ) : rows.map((p) => (
                    <tr key={p.id}>
                      <td style={{ fontSize: "0.75rem", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                        {new Date(p.timestamp).toLocaleString("es-GT", { dateStyle: "short", timeStyle: "short" })}
                      </td>
                      <td style={{ fontWeight: 600 }}>{p.municipio}</td>
                      <td>{p.cultivo}</td>
                      <td style={{ textAlign: "center" }}>{p.mes}</td>
                      <td>{p.temperatura?.toFixed(1)}°C</td>
                      <td>{p.precipitacion?.toFixed(0)} mm</td>
                      <td>{p.humedad?.toFixed(0)}%</td>
                      <td>{p.ph_suelo?.toFixed(1)}</td>
                      <td style={{ fontWeight: 700, color: p.yield_pct >= 75 ? "var(--green)" : p.yield_pct >= 50 ? "var(--gold)" : "var(--red)" }}>
                        {p.yield_pct?.toFixed(1)}%
                      </td>
                      <td>
                        <span className={`status-pill ${p.yield_level === "alto" ? "low" : p.yield_level === "medio" ? "medium" : "high"}`}>
                          {p.yield_level}
                        </span>
                      </td>
                      <td><span className="chip" style={{ fontSize: "0.7rem" }}>{p.fuente}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {totalPages > 1 && (
          <div style={{ padding: "0.75rem 1.15rem", display: "flex", justifyContent: "flex-end", gap: "0.5rem", borderTop: "1px solid var(--border)" }}>
            <button
              onClick={() => setPage((current) => Math.max(0, current - 1))}
              disabled={page === 0}
              className="btn-secondary"
              style={{ padding: "0.3rem 0.7rem", fontSize: "0.78rem" }}
            >
              Anterior
            </button>
            <span style={{ fontSize: "0.78rem", color: "var(--text-muted)", alignSelf: "center" }}>
              Pag. {page + 1} / {totalPages}
            </span>
            <button
              onClick={() => setPage((current) => Math.min(totalPages - 1, current + 1))}
              disabled={page >= totalPages - 1}
              className="btn-secondary"
              style={{ padding: "0.3rem 0.7rem", fontSize: "0.78rem" }}
            >
              Siguiente
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
