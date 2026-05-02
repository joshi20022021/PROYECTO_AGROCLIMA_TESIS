import { useEffect, useMemo, useRef, useState } from "react";
import { cropOptions, municipioOptions } from "../data/constants";
import { createArduinoSocket, setArduinoConfig } from "../services/api";
import { calculateRisk, getRecommendation } from "../utils/riskUtils";

const SEVERITY_STYLE = {
  severo: {
    bg: "rgba(180,30,30,0.08)",
    border: "#b41e1e",
    badge: "#b41e1e",
    label: "Urgente",
  },
  moderado: {
    bg: "rgba(184,124,32,0.10)",
    border: "#b87c20",
    badge: "#b87c20",
    label: "Revisar",
  },
  leve: {
    bg: "rgba(30,100,74,0.08)",
    border: "#1e7a4a",
    badge: "#1e7a4a",
    label: "Estable",
  },
};

const VAR_LABELS = {
  temperature: "Temperatura",
  light_lux: "Luz",
  soil_moisture: "Humedad del suelo",
  greenness_idx: "Color de hoja",
  humidity: "Humedad del aire",
  rainfall: "Lluvia",
  soil_ph: "pH del suelo",
};

const REMEDY_TYPE_LABELS = {
  quimico: "Manejo quimico",
  biologico: "Manejo biologico",
  fertilizante: "Nutrientes",
  cultural: "Manejo cultural",
  riego: "Riego",
};

function mapLevelToSeverity(level) {
  if (level === "high") return "severo";
  if (level === "medium") return "moderado";
  return "leve";
}

function formatValue(alert) {
  if (alert.value === undefined || alert.value === null) return null;
  if (alert.variable === "soil_ph") return `pH ${alert.value}`;
  if (alert.variable === "humidity" || alert.variable === "soil_moisture") return `${alert.value}%`;
  if (alert.variable === "temperature") return `${alert.value} °C`;
  if (alert.variable === "rainfall") return `${alert.value} mm`;
  return String(alert.value);
}

function buildHistoricalAlerts(dataset, municipio, crop) {
  if (!Array.isArray(dataset) || dataset.length === 0) return [];

  return dataset
    .filter((entry) => entry.municipality === municipio && entry.crop === crop)
    .map((entry) => {
      const risk = calculateRisk(entry);
      const severity = mapLevelToSeverity(risk.level);
      const variableHints = [];

      if (entry.rainfall > 100) variableHints.push(`lluvia alta (${entry.rainfall} mm)`);
      else if (entry.rainfall < 30) variableHints.push(`lluvia muy baja (${entry.rainfall} mm)`);

      if (entry.temperature >= 30) variableHints.push(`temperatura alta (${entry.temperature} °C)`);
      else if (entry.temperature <= 18) variableHints.push(`temperatura baja (${entry.temperature} °C)`);

      if (entry.humidity >= 80) variableHints.push(`humedad alta (${entry.humidity}%)`);
      else if (entry.humidity < 55) variableHints.push(`humedad baja (${entry.humidity}%)`);

      if (entry.soilPh < 5.5) variableHints.push(`suelo acido (pH ${entry.soilPh})`);
      else if (entry.soilPh > 7.2) variableHints.push(`suelo alcalino (pH ${entry.soilPh})`);

      const summary =
        variableHints.length > 0
          ? variableHints.slice(0, 2).join(", ")
          : "sin desviaciones fuertes en las variables principales";

      return {
        source: "historical",
        severity,
        variable: "dataset",
        problem: `En los datos analizados de ${crop} para ${municipio} predomina ${summary}.`,
        action: getRecommendation(entry, risk),
        consequence:
          risk.level === "high"
            ? "Conviene priorizar seguimiento cercano porque las condiciones salen del rango estable."
            : risk.level === "medium"
              ? "Hay senales para vigilar antes de que se conviertan en una alerta fuerte."
              : "Las condiciones se ven manejables con seguimiento normal.",
        value: `Riesgo ${risk.score}/100`,
      };
    })
    .sort((a, b) => {
      const order = { severo: 0, moderado: 1, leve: 2 };
      return order[a.severity] - order[b.severity];
    })
    .slice(0, 3);
}

function AlertCard({ alert, sourceLabel }) {
  const style = SEVERITY_STYLE[alert.severity] || SEVERITY_STYLE.leve;
  const valueText = formatValue(alert);
  const remedyLabel = alert.remedy?.type ? REMEDY_TYPE_LABELS[alert.remedy.type] || alert.remedy.type : null;

  return (
    <div
      style={{
        padding: "0.95rem 1rem",
        borderRadius: 10,
        background: style.bg,
        borderLeft: `4px solid ${style.border}`,
        border: `1px solid ${style.border}22`,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: "0.75rem", flexWrap: "wrap" }}>
        <div style={{ display: "flex", gap: "0.45rem", flexWrap: "wrap", alignItems: "center" }}>
          <span
            style={{
              fontSize: "0.68rem",
              fontWeight: 800,
              letterSpacing: "0.06em",
              padding: "0.18rem 0.5rem",
              borderRadius: 999,
              background: style.badge,
              color: "#fff",
            }}
          >
            {style.label}
          </span>
          <span
            style={{
              fontSize: "0.68rem",
              fontWeight: 700,
              padding: "0.18rem 0.5rem",
              borderRadius: 999,
              background: "rgba(15,23,42,0.06)",
              color: "var(--text-secondary)",
            }}
          >
            {sourceLabel}
          </span>
          {alert.variable && alert.variable !== "dataset" && (
            <span style={{ fontSize: "0.76rem", color: "var(--text-muted)", fontWeight: 700 }}>
              {VAR_LABELS[alert.variable] || alert.variable}
            </span>
          )}
        </div>
        {valueText && (
          <span style={{ fontSize: "0.78rem", color: "var(--text-secondary)", fontWeight: 700 }}>
            {valueText}
          </span>
        )}
      </div>

      <p style={{ fontSize: "0.88rem", fontWeight: 700, margin: "0.6rem 0 0", color: "var(--text-primary)" }}>
        {alert.problem}
      </p>

      {alert.consequence && (
        <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", margin: "0.45rem 0 0" }}>
          <strong>Que puede pasar:</strong> {alert.consequence}
        </p>
      )}

      <div
        style={{
          marginTop: "0.65rem",
          padding: "0.75rem 0.85rem",
          borderRadius: 8,
          background: "rgba(255,255,255,0.72)",
          border: "1px solid rgba(15,23,42,0.08)",
        }}
      >
        <div style={{ fontSize: "0.72rem", fontWeight: 800, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
          Que hacer ahora
        </div>
        <p style={{ fontSize: "0.82rem", margin: "0.35rem 0 0", color: "var(--text-primary)", lineHeight: 1.5 }}>
          {alert.action}
        </p>

        {remedyLabel && alert.remedy?.name && (
          <div style={{ marginTop: "0.55rem", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
            <strong>{remedyLabel}:</strong> {alert.remedy.name}
          </div>
        )}
        {alert.remedy?.dose && (
          <div style={{ marginTop: "0.25rem", fontSize: "0.74rem", color: "var(--text-muted)" }}>
            Dosis sugerida: {alert.remedy.dose}
          </div>
        )}
        {alert.remedy?.notes && (
          <div style={{ marginTop: "0.25rem", fontSize: "0.74rem", color: "var(--text-muted)" }}>
            Nota: {alert.remedy.notes}
          </div>
        )}
      </div>
    </div>
  );
}

export default function Alerts({ dataset = [], showToast, setActiveSection }) {
  const [municipio, setMunicipio] = useState("Chimaltenango");
  const [crop, setCrop] = useState("Maiz");
  const [liveAlerts, setLiveAlerts] = useState([]);
  const [wsReady, setWsReady] = useState(false);
  const wsRef = useRef(null);

  const historicalAlerts = useMemo(
    () => buildHistoricalAlerts(dataset, municipio, crop),
    [dataset, municipio, crop]
  );

  const liveSummary = useMemo(() => {
    return {
      severe: liveAlerts.filter((a) => a.severity === "severo").length,
      moderate: liveAlerts.filter((a) => a.severity === "moderado").length,
      stable: liveAlerts.filter((a) => a.severity === "leve").length,
    };
  }, [liveAlerts]);

  function openSocket() {
    if (wsRef.current) wsRef.current.close();
    const ws = createArduinoSocket(
      (msg) => {
        if (Array.isArray(msg.alerts)) {
          setLiveAlerts(msg.alerts);
        }
      },
      () => setWsReady(false)
    );

    ws.onopen = () => {
      setWsReady(true);
      ws.send(JSON.stringify({ municipio, crop }));
    };

    wsRef.current = ws;
  }

  useEffect(() => {
    openSocket();
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  useEffect(() => {
    setLiveAlerts([]);
    setArduinoConfig(municipio, crop).catch(() => {});
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ municipio, crop }));
    }
  }, [municipio, crop]);

  return (
    <div className="page-content">
      <div className="two-col">
        <div className="card">
          <div className="card-header">
            <h3>Monitoreo actual</h3>
            <span className={`chip ${wsReady ? "green" : "orange"}`}>
              {wsReady ? "Sensor conectado" : "Sin conexion"}
            </span>
          </div>
          <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <label className="form-label">
              Departamento
              <select className="form-select" value={municipio} onChange={(e) => setMunicipio(e.target.value)}>
                {municipioOptions.map((item) => (
                  <option key={item}>{item}</option>
                ))}
              </select>
            </label>
            <label className="form-label">
              Cultivo
              <select className="form-select" value={crop} onChange={(e) => setCrop(e.target.value)}>
                {cropOptions.map((item) => (
                  <option key={item}>{item}</option>
                ))}
              </select>
            </label>
            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              Elige el cultivo y departamento para ver solo avisos que requieren atencion.
            </div>
          </div>
        </div>

        <div className="card full-span">
          <div className="card-header">
            <h3>Alertas en tiempo real</h3>
            <span className="chip">{liveAlerts.length} activas</span>
          </div>
          <div className="card-body">
            {liveAlerts.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                No hay alertas activas del sensor para este cultivo en este momento.
                {!wsReady && " Conecta el Arduino para ver monitoreo en vivo."}
              </p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.7rem" }}>
                {liveAlerts.map((alert, index) => (
                  <AlertCard key={`live-${index}`} alert={alert} sourceLabel="Tiempo real" />
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="card full-span">
          <div className="card-header">
            <h3>Riesgos detectados en analisis</h3>
            <span className="chip">{historicalAlerts.length} registros</span>
          </div>
          <div className="card-body">
            {historicalAlerts.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                No hay riesgos destacados en los datos analizados para {crop} en {municipio}.
              </p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.7rem" }}>
                {historicalAlerts.map((alert, index) => (
                  <AlertCard key={`historical-${index}`} alert={alert} sourceLabel="Cultivo" />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
