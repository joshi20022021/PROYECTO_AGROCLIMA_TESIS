import { useEffect, useMemo, useRef, useState } from "react";
import { getAdminDatasets, uploadDataset, getDatasetTemplateUrl, retrainModel } from "../../services/api";

const ZONAS = [
  { zona: "Region I (Metropolitana)", departamentos: ["Guatemala"], color: "#16a34a" },
  { zona: "Region II (Norte)", departamentos: ["Alta Verapaz", "Baja Verapaz"], color: "#0ea5e9" },
  { zona: "Region III (Nororiente)", departamentos: ["Chiquimula", "El Progreso", "Izabal", "Zacapa"], color: "#8b5cf6" },
  { zona: "Region IV (Suroriente)", departamentos: ["Jutiapa", "Jalapa", "Santa Rosa"], color: "#f59e0b" },
  { zona: "Region V (Central)", departamentos: ["Chimaltenango", "Sacatepequez", "Escuintla"], color: "#ef4444" },
  { zona: "Region VI (Suroccidente)", departamentos: ["Quetzaltenango", "Retalhuleu", "San Marcos", "Suchitepequez", "Solola", "Totonicapan"], color: "#06b6d4" },
  { zona: "Region VII (Noroccidente)", departamentos: ["Huehuetenango", "Quiche"], color: "#84cc16" },
  { zona: "Region VIII (Peten)", departamentos: ["Peten"], color: "#ec4899" },
];

function fmtDate(value) {
  if (!value) return "N/D";
  try {
    return new Date(value).toLocaleString("es-GT");
  } catch {
    return value;
  }
}

function fmtValue(value) {
  if (value === null || value === undefined || value === "") return "N/D";
  if (typeof value === "number") return value.toLocaleString();
  return value;
}

function inferFeatureCount(row) {
  if (row?.metadata?.features) return row.metadata.features;
  if (!Array.isArray(row?.columnas)) return row?.total_columnas ?? "N/D";
  const ignored = new Set(["yield_pct", "year", "month"]);
  return row.columnas.filter((column) => !ignored.has(column)).length;
}

export default function AdminDatasets() {
  const [inventory, setInventory] = useState({ datasets: [], sources: [], uploads: [], active_dataset: null, db_available: false });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [uploadMsg, setUploadMsg] = useState("");
  const [uploading, setUploading] = useState(false);
  const [retraining, setRetraining] = useState(false);
  const [retrainMsg, setRetrainMsg] = useState("");
  const fileInputRef = useRef(null);

  async function loadInventory() {
    setLoading(true);
    setError("");
    try {
      const data = await getAdminDatasets();
      setInventory(data);
    } catch (err) {
      setError(err.message);
      setInventory({ datasets: [], sources: [], uploads: [], active_dataset: null, db_available: false });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadInventory();
  }, []);

  async function handleUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setUploadMsg("");
    try {
      const res = await uploadDataset(file);
      setUploadMsg(res.message || "CSV importado correctamente.");
      await loadInventory();
    } catch (err) {
      setUploadMsg(`Error: ${err.message}`);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function handleRetrain() {
    setRetraining(true);
    setRetrainMsg("");
    try {
      const res = await retrainModel();
      setRetrainMsg(res.message || "Reentrenamiento iniciado.");
    } catch (err) {
      setRetrainMsg(`Error: ${err.message}`);
    } finally {
      setRetraining(false);
    }
  }

  const datasets = inventory.datasets || [];
  const sources = inventory.sources || [];
  const uploads = inventory.uploads || [];

  const summary = useMemo(() => ({
    datasets: datasets.length,
    sources: sources.length,
    uploads: uploads.length,
    active: inventory.active_dataset || "N/D",
  }), [datasets, sources, uploads, inventory.active_dataset]);

  return (
    <div className="page-content">
      <div className="card">
        <div className="card-header">
          <h3>Resumen del inventario</h3>
          <span className="chip">{inventory.db_available ? "Con BD" : "Lectura desde archivos"}</span>
        </div>
        <div className="card-body" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "0.75rem" }}>
          {[
            { label: "Datasets detectados", value: summary.datasets, color: "#2563eb" },
            { label: "Fuentes procesadas", value: summary.sources, color: "#16a34a" },
            { label: "Cargas manuales", value: summary.uploads, color: "#b45309" },
            { label: "Dataset activo", value: summary.active, color: "var(--text-primary)" },
          ].map((item) => (
            <div key={item.label} style={{ padding: "0.8rem 0.9rem", borderRadius: 10, border: "1px solid var(--border)", background: "var(--surface)" }}>
              <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase" }}>{item.label}</div>
              <div style={{ marginTop: "0.3rem", fontSize: "1.1rem", fontWeight: 800, color: item.color }}>{item.value}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Cobertura nacional - 22 departamentos</h3>
          <span className="chip">22 departamentos · 8 regiones</span>
        </div>
        <div className="card-body">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: "0.75rem" }}>
            {ZONAS.map((zona) => (
              <div key={zona.zona} style={{ padding: "0.85rem", background: `${zona.color}10`, border: `1px solid ${zona.color}30`, borderRadius: 10 }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
                  <div style={{ width: 10, height: 10, borderRadius: "50%", background: zona.color, flexShrink: 0 }} />
                  <span style={{ fontWeight: 700, fontSize: "0.82rem", color: "var(--text-primary)" }}>{zona.zona}</span>
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.3rem" }}>
                  {zona.departamentos.map((dep) => (
                    <span key={dep} style={{ fontSize: "0.7rem", padding: "0.15rem 0.5rem", background: `${zona.color}18`, border: `1px solid ${zona.color}40`, borderRadius: 20, color: zona.color, fontWeight: 600 }}>
                      {dep}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Datasets de entrenamiento</h3>
          <span className="chip">{loading ? "Cargando..." : `${datasets.length} archivos detectados`}</span>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          {error ? (
            <p style={{ margin: 0, padding: "1rem", color: "#dc2626", fontSize: "0.82rem" }}>{error}</p>
          ) : (
            <div className="table-wrap" style={{ borderRadius: 0, border: "none" }}>
              <table>
                <thead>
                  <tr>
                    <th>Archivo</th>
                    <th>Tipo</th>
                    <th>Municipios</th>
                    <th>Variables</th>
                    <th>Cultivos</th>
                    <th>Periodo</th>
                    <th>Tamano</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {datasets.map((item) => (
                    <tr key={item.nombre_archivo}>
                      <td style={{ fontFamily: "monospace", fontSize: "0.8rem", fontWeight: 600, color: "var(--text-primary)" }}>
                        {item.nombre_archivo}
                      </td>
                      <td><span className="chip" style={{ fontSize: "0.72rem" }}>{item.tipo || "Dataset"}</span></td>
                      <td style={{ textAlign: "center" }}>{fmtValue(item.metadata?.municipios)}</td>
                      <td style={{ textAlign: "center" }}>{fmtValue(inferFeatureCount(item))}</td>
                      <td style={{ textAlign: "center" }}>{fmtValue(item.metadata?.cultivos)}</td>
                      <td><span className="chip">{fmtValue(item.periodo)}</span></td>
                      <td style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{fmtValue(item.metadata?.tamanio)}</td>
                      <td>
                        <span className={`status-pill ${item.activo ? "low" : "medium"}`}>
                          {item.activo ? "Activo" : "Disponible"}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {datasets.length === 0 && (
                    <tr>
                      <td colSpan="8" style={{ padding: "1rem", color: "var(--text-muted)" }}>
                        No se encontraron datasets en esta instalacion.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Archivos fuente procesados</h3>
          <span className="chip">{loading ? "Cargando..." : `${sources.length} fuentes detectadas`}</span>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          <div className="table-wrap" style={{ borderRadius: 0, border: "none" }}>
            <table>
              <thead>
                <tr>
                  <th>Archivo</th>
                  <th>Categoria</th>
                  <th>Filas</th>
                  <th>Columnas</th>
                  <th>Periodo</th>
                  <th>Tamano</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((item) => (
                  <tr key={item.nombre_archivo}>
                    <td style={{ fontFamily: "monospace", fontSize: "0.8rem", fontWeight: 600 }}>{item.nombre_archivo}</td>
                    <td><span className="chip">{item.categoria || "Fuente"}</span></td>
                    <td>{fmtValue(item.total_filas)}</td>
                    <td>{fmtValue(item.total_columnas)}</td>
                    <td><span className="chip">{fmtValue(item.periodo)}</span></td>
                    <td style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{fmtValue(item.metadata?.tamanio)}</td>
                  </tr>
                ))}
                {sources.length === 0 && (
                  <tr>
                    <td colSpan="6" style={{ padding: "1rem", color: "var(--text-muted)" }}>
                      No se encontraron archivos fuente procesados.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Cargas manuales</h3>
          <span className="chip">{uploads.length} en data/uploads/</span>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          <div className="table-wrap" style={{ borderRadius: 0, border: "none" }}>
            <table>
              <thead>
                <tr>
                  <th>Archivo</th>
                  <th>Filas</th>
                  <th>Columnas</th>
                  <th>Municipios</th>
                  <th>Cultivos</th>
                  <th>Fecha</th>
                </tr>
              </thead>
              <tbody>
                {uploads.map((item) => (
                  <tr key={item.nombre_archivo}>
                    <td style={{ fontFamily: "monospace", fontSize: "0.8rem", fontWeight: 600 }}>{item.nombre_archivo}</td>
                    <td>{fmtValue(item.total_filas)}</td>
                    <td>{fmtValue(item.total_columnas)}</td>
                    <td>{fmtValue(item.metadata?.municipios)}</td>
                    <td>{fmtValue(item.metadata?.cultivos)}</td>
                    <td style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{fmtDate(item.fecha_carga)}</td>
                  </tr>
                ))}
                {uploads.length === 0 && (
                  <tr>
                    <td colSpan="6" style={{ padding: "1rem", color: "var(--text-muted)" }}>
                      Aun no hay cargas manuales registradas.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Importar CSV y reentrenar modelo</h3>
          <span className="chip">XGBoost</span>
        </div>
        <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
            Sube un CSV con nuevos datos de campo para dejarlo registrado en `data/uploads/`.
            La plantilla ahora incluye `year` y el sistema registra metadata del archivo para el panel admin.
          </p>
          <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start", flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 240, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "monospace" }}>
                Columnas requeridas: municipio, crop, temperature, rainfall, humidity, soil_ph
              </p>
              <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "monospace" }}>
                Recomendadas: year, month, soil_moisture, yield_pct
              </p>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button className="btn ghost" style={{ flex: 1 }} onClick={() => fileInputRef.current.click()} disabled={uploading}>
                  {uploading ? "Subiendo..." : "Seleccionar CSV"}
                </button>
                <a href={getDatasetTemplateUrl()} download className="btn ghost">
                  Plantilla
                </a>
              </div>
              <input ref={fileInputRef} type="file" accept=".csv" style={{ display: "none" }} onChange={handleUpload} />
              {uploadMsg && (
                <p style={{ margin: 0, fontSize: "0.78rem", fontWeight: 600, color: uploadMsg.startsWith("Error") ? "#dc2626" : "#16a34a" }}>
                  {uploadMsg}
                </p>
              )}
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", minWidth: 200 }}>
              <button className="btn primary" onClick={handleRetrain} disabled={retraining} style={{ justifyContent: "center" }}>
                {retraining ? "Iniciando..." : "Reentrenar modelo"}
              </button>
              {retrainMsg && (
                <p style={{ margin: 0, fontSize: "0.78rem", fontWeight: 600, color: retrainMsg.startsWith("Error") ? "#dc2626" : "#16a34a" }}>
                  {retrainMsg}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
