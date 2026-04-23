import { useEffect, useMemo, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";
import { getRiskMap } from "../services/api";

const MAP_CENTER = [15.2, -90.3];
const MAP_BOUNDS = [
  [13.7, -92.4],
  [17.3, -88.0],
];

function colorByRisk(level) {
  if (level === "high") return "#dc2626";
  if (level === "medium") return "#d97706";
  return "#16a34a";
}

export default function RiskMap({ selectedCrop }) {
  const [loading, setLoading] = useState(true);
  const [points, setPoints] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    getRiskMap(selectedCrop)
      .then((res) => setPoints(res.points || []))
      .catch(() => setError("No se pudo cargar el mapa de riesgo"))
      .finally(() => setLoading(false));
  }, [selectedCrop]);

  const summary = useMemo(() => {
    const high = points.filter((p) => p.risk_level === "high").length;
    const medium = points.filter((p) => p.risk_level === "medium").length;
    const low = points.filter((p) => p.risk_level === "low").length;
    return { high, medium, low };
  }, [points]);

  return (
    <div className="page-content">
      <div className="card" style={{ marginBottom: "0.9rem" }}>
        <div className="card-header">
          <h3>Mapa de riesgo agricola de Guatemala</h3>
          <span className="chip">{points.length} municipios</span>
        </div>
        <div className="card-body" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "0.6rem" }}>
          <div style={{ background: "rgba(220,38,38,0.08)", border: "1px solid rgba(220,38,38,0.2)", borderRadius: 10, padding: "0.6rem" }}>
            <div style={{ fontSize: "0.72rem", color: "#991b1b", textTransform: "uppercase", fontWeight: 700 }}>Riesgo alto</div>
            <div style={{ fontSize: "1.35rem", fontWeight: 800, color: "#dc2626" }}>{summary.high}</div>
          </div>
          <div style={{ background: "rgba(217,119,6,0.08)", border: "1px solid rgba(217,119,6,0.2)", borderRadius: 10, padding: "0.6rem" }}>
            <div style={{ fontSize: "0.72rem", color: "#92400e", textTransform: "uppercase", fontWeight: 700 }}>Riesgo medio</div>
            <div style={{ fontSize: "1.35rem", fontWeight: 800, color: "#d97706" }}>{summary.medium}</div>
          </div>
          <div style={{ background: "rgba(22,163,74,0.08)", border: "1px solid rgba(22,163,74,0.2)", borderRadius: 10, padding: "0.6rem" }}>
            <div style={{ fontSize: "0.72rem", color: "#166534", textTransform: "uppercase", fontWeight: 700 }}>Riesgo bajo</div>
            <div style={{ fontSize: "1.35rem", fontWeight: 800, color: "#16a34a" }}>{summary.low}</div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-body" style={{ padding: "0.75rem" }}>
          {loading && <p style={{ padding: "0.75rem", color: "var(--text-muted)" }}>Cargando mapa...</p>}
          {error && <p style={{ padding: "0.75rem", color: "#dc2626" }}>{error}</p>}
          {!loading && !error && (
            <div style={{ width: "100%", height: "560px", borderRadius: 12, overflow: "hidden", border: "1px solid var(--border)" }}>
              <MapContainer center={MAP_CENTER} zoom={7} minZoom={6} maxBounds={MAP_BOUNDS} style={{ width: "100%", height: "100%" }}>
                <TileLayer
                  attribution='&copy; OpenStreetMap contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {points.map((p) => (
                  <CircleMarker
                    key={`${p.municipio}-${p.lat}-${p.lon}`}
                    center={[p.lat, p.lon]}
                    radius={Math.max(5, Math.min(14, Math.round((p.risk_score || 0) / 9)))}
                    pathOptions={{
                      color: colorByRisk(p.risk_level),
                      fillColor: colorByRisk(p.risk_level),
                      fillOpacity: 0.6,
                      weight: 1.5,
                    }}
                  >
                    <Popup>
                      <div style={{ minWidth: 190 }}>
                        <strong>{p.municipio}</strong>
                        <div>Depto: {p.depto || "N/A"}</div>
                        <div>Zona: {p.zona || "N/A"}</div>
                        <div>Riesgo: {p.risk_score}/100 ({p.risk_level})</div>
                        <div>Yield promedio: {p.avg_yield}%</div>
                        <div>Muestras: {p.samples}</div>
                      </div>
                    </Popup>
                  </CircleMarker>
                ))}
              </MapContainer>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
