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

const DEPARTMENT_TILES = {
  Peten: [330, 72],
  Huehuetenango: [150, 220],
  Quiche: [235, 225],
  "Alta Verapaz": [320, 230],
  Coban: [320, 230],
  Izabal: [440, 248],
  "San Marcos": [108, 315],
  Quetzaltenango: [170, 322],
  Totonicapan: [230, 315],
  Solola: [235, 382],
  Chimaltenango: [300, 382],
  Sacatepequez: [332, 430],
  Guatemala: [380, 405],
  "Baja Verapaz": [360, 330],
  "El Progreso": [430, 360],
  Zacapa: [490, 355],
  Chiquimula: [520, 430],
  Retalhuleu: [148, 410],
  Suchitepequez: [212, 438],
  Escuintla: [315, 490],
  "Santa Rosa": [420, 492],
  Jalapa: [465, 430],
  Jutiapa: [500, 515],
};

function hexPoints(cx, cy, radius = 34) {
  return Array.from({ length: 6 }, (_, i) => {
    const angle = (Math.PI / 180) * (60 * i - 30);
    return `${cx + radius * Math.cos(angle)},${cy + radius * Math.sin(angle)}`;
  }).join(" ");
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

  const departmentRisk = useMemo(() => {
    const grouped = {};
    points.forEach((point) => {
      const depto = point.depto || point.municipio;
      if (!depto) return;
      if (!grouped[depto]) grouped[depto] = { depto, score: 0, samples: 0, high: 0, medium: 0, low: 0 };
      grouped[depto].score += Number(point.risk_score || 0);
      grouped[depto].samples += Number(point.samples || 1);
      grouped[depto][point.risk_level || "low"] += 1;
    });
    return Object.values(grouped).map((row) => {
      const totalLevels = row.high + row.medium + row.low || 1;
      const level = row.high / totalLevels >= 0.34
        ? "high"
        : row.medium / totalLevels >= 0.34
          ? "medium"
          : "low";
      return {
        ...row,
        avgScore: Math.round(row.score / totalLevels),
        level,
      };
    });
  }, [points]);

  const tileRows = useMemo(() => departmentRisk.map((row) => ({
    ...row,
    tile: DEPARTMENT_TILES[row.depto] || DEPARTMENT_TILES[row.depto?.replace("Alta Verapaz", "Coban")],
  })).filter((row) => row.tile), [departmentRisk]);

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

      <div className="card">
        <div className="card-header">
          <h3>Coropletico departamental</h3>
          <span className="chip">{tileRows.length} departamentos</span>
        </div>
        <div className="card-body risk-choropleth-shell">
          <svg className="risk-choropleth" viewBox="60 30 520 540" role="img" aria-label="Mapa coropletico de riesgo por departamento">
            {tileRows.map((row) => {
              const [cx, cy] = row.tile;
              return (
                <g key={row.depto} className="risk-tile">
                  <polygon points={hexPoints(cx, cy)} fill={colorByRisk(row.level)} opacity={0.78} />
                  <title>{`${row.depto}: riesgo ${row.level}, score ${row.avgScore}/100`}</title>
                  <text x={cx} y={cy - 2} textAnchor="middle">{row.depto.length > 12 ? row.depto.slice(0, 11) : row.depto}</text>
                  <text x={cx} y={cy + 14} textAnchor="middle" className="risk-tile-score">{row.avgScore}</text>
                </g>
              );
            })}
          </svg>
          <div className="risk-map-legend">
            <span><i style={{ background: "#dc2626" }} /> Alto</span>
            <span><i style={{ background: "#d97706" }} /> Medio</span>
            <span><i style={{ background: "#16a34a" }} /> Bajo</span>
          </div>
        </div>
      </div>
    </div>
  );
}
