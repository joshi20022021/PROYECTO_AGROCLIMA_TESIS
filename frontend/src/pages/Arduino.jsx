import { useEffect, useMemo, useRef, useState } from "react";
import ChartCanvas from "../components/ChartCanvas";
import { cropOptions, municipioOptions } from "../data/constants";
import {
  connectArduino,
  createArduinoSocket,
  disconnectArduino,
  getArduinoStatus,
  setArduinoConfig,
  simulateArduino,
} from "../services/api";

const MAX_HISTORY = 20;

const YIELD_COLOR = {
  alto:    { bg: "rgba(30,122,74,0.12)",  border: "#1e7a4a", text: "#1e7a4a", label: "Bueno" },
  medio:   { bg: "rgba(184,124,32,0.12)", border: "#b87c20", text: "#b87c20", label: "Revisar" },
  bajo:    { bg: "rgba(192,64,64,0.10)",  border: "#c04040", text: "#c04040", label: "Riesgo" },
  critico: { bg: "rgba(140,20,20,0.12)",  border: "#8c1414", text: "#8c1414", label: "Urgente" },
};

function formatValue(value, decimals = 1) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return "--";
  return Number(value).toFixed(decimals);
}

function SensorCard({ label, value, unit, color, note, decimals = 1 }) {
  return (
    <div className="card kpi-card" style={{ minWidth: 0 }}>
      <span className="kpi-label">{label}</span>
      <div className="kpi-value" style={{ color }}>
        {formatValue(value, decimals)}
        <span style={{ fontSize: "0.85rem", fontWeight: 500, marginLeft: "0.25rem" }}>{unit}</span>
      </div>
      {note && <p className="kpi-sub" style={{ marginBottom: 0 }}>{note}</p>}
    </div>
  );
}

export default function Arduino() {
  const [connected, setConnected] = useState(false);
  const [port, setPort] = useState("");
  const [availPorts, setAvailPorts] = useState([]);
  const [statusMsg, setStatusMsg] = useState("Sin conexion");
  const [wsReady, setWsReady] = useState(false);
  const wsRef = useRef(null);

  const [municipio, setMunicipio] = useState("Chimaltenango");
  const [crop, setCrop] = useState("Maiz");
  const [sensors, setSensors] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [history, setHistory] = useState([]);

  const [simForm, setSimForm] = useState({
    temperature: 22,
    light_lux: 32000,
    color_r: 145,
    color_g: 210,
    color_b: 98,
    soil_moisture: 0.31,
    humidity: 74,
    rainfall: 45,
    soil_ph: 6.3,
  });

  function sendConfig(ws, mun, cr) {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ municipio: mun, crop: cr }));
    }
  }

  function openSocket() {
    if (wsRef.current) wsRef.current.close();
    const ws = createArduinoSocket(
      (msg) => {
        if (msg.sensors) {
          setSensors(msg.sensors);
          setHistory((prev) => {
            const next = [...prev, { ...msg.sensors, ts: new Date().toLocaleTimeString() }];
            return next.slice(-MAX_HISTORY);
          });
        }
        if (msg.prediction) setPrediction(msg.prediction);
      },
      () => {
        setWsReady(false);
        setStatusMsg("Canal de lectura desconectado.");
      }
    );
    ws.onopen = () => {
      setWsReady(true);
      sendConfig(ws, municipio, crop);
    };
    wsRef.current = ws;
  }

  useEffect(() => {
    getArduinoStatus()
      .then((s) => {
        setAvailPorts(s.ports || []);
        setConnected(s.connected);
        if (s.connected) {
          setPort(s.port || "");
          setStatusMsg(`Conectado en ${s.port}`);
        }
      })
      .catch(() => {});
    openSocket();
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  useEffect(() => {
    setArduinoConfig(municipio, crop).catch(() => {});
    sendConfig(wsRef.current, municipio, crop);
  }, [municipio, crop]);

  async function handleConnect() {
    try {
      setStatusMsg("Conectando...");
      const res = await connectArduino(port || null);
      setConnected(true);
      setStatusMsg(res.message);
      openSocket();
    } catch (e) {
      setStatusMsg(e.message);
    }
  }

  async function handleDisconnect() {
    await disconnectArduino().catch(() => {});
    setConnected(false);
    setStatusMsg("Desconectado.");
  }

  async function handleSimulate() {
    try {
      await simulateArduino(simForm);
    } catch (e) {
      setStatusMsg(e.message);
    }
  }

  const historyChart = useMemo(() => ({
    type: "line",
    data: {
      labels: history.map((h) => h.ts),
      datasets: [
        { label: "Temperatura", data: history.map((h) => h.temperature), borderColor: "#b87c20", tension: 0.4, pointRadius: 2, yAxisID: "y" },
        { label: "Verdor", data: history.map((h) => h.greenness_idx), borderColor: "#1e7a4a", tension: 0.4, pointRadius: 2, yAxisID: "y" },
        { label: "Humedad suelo", data: history.map((h) => h.soil_moisture ? Number(h.soil_moisture) * 100 : null), borderColor: "#5a7a35", tension: 0.4, pointRadius: 2, yAxisID: "y" },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom", labels: { boxWidth: 10, padding: 12 } } },
      scales: {
        x: { ticks: { maxTicksLimit: 8 }, grid: { color: "rgba(80,60,35,0.06)" } },
        y: { grid: { color: "rgba(80,60,35,0.06)" } },
      },
    },
  }), [history]);

  const yieldColors = prediction ? (YIELD_COLOR[prediction.yield_level] || YIELD_COLOR.medio) : null;
  const lastUpdate = sensors?.timestamp ? new Date(sensors.timestamp).toLocaleTimeString() : null;

  return (
    <div className="page-content">
      <div className="two-col">
        <div className="card">
          <div className="card-header">
            <h3>Conexion Arduino</h3>
            <span className={`chip ${connected ? "green" : "orange"}`}>
              {connected ? "Conectado" : "Desconectado"}
            </span>
          </div>
          <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <label className="form-label">
              Puerto serial
              <select className="form-select" value={port} onChange={(e) => setPort(e.target.value)}>
                <option value="">Auto detectar</option>
                {availPorts.map((p) => (
                  <option key={p.device} value={p.device}>
                    {p.device} {p.description ? `- ${p.description}` : ""}
                  </option>
                ))}
              </select>
            </label>

            {!connected ? (
              <button className="btn primary" onClick={handleConnect}>Conectar Arduino</button>
            ) : (
              <button className="btn ghost" onClick={handleDisconnect}>Desconectar</button>
            )}

            <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", margin: 0 }}>{statusMsg}</p>
            <div style={{
              padding: "0.65rem 0.75rem",
              borderRadius: 8,
              background: wsReady ? "rgba(22,163,74,0.08)" : "rgba(245,158,11,0.1)",
              color: wsReady ? "#166534" : "#92400e",
              fontSize: "0.78rem",
              fontWeight: 700,
            }}>
              {wsReady ? "Canal en vivo activo" : "Esperando canal en vivo"}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Parcela monitoreada</h3>
            <span className="chip">{crop}</span>
          </div>
          <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <label className="form-label">
              Departamento
              <select className="form-select" value={municipio} onChange={(e) => setMunicipio(e.target.value)}>
                {municipioOptions.map((m) => <option key={m}>{m}</option>)}
              </select>
            </label>
            <label className="form-label">
              Cultivo
              <select className="form-select" value={crop} onChange={(e) => setCrop(e.target.value)}>
                {cropOptions.map((c) => <option key={c}>{c}</option>)}
              </select>
            </label>
            {prediction && yieldColors && (
              <div style={{ padding: "0.75rem 1rem", borderRadius: 8, background: yieldColors.bg, borderLeft: `3px solid ${yieldColors.border}` }}>
                <p style={{ fontSize: "0.72rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)", margin: "0 0 0.3rem" }}>
                  Estado estimado
                </p>
                <p style={{ fontSize: "1.8rem", fontWeight: 800, color: yieldColors.text, margin: 0 }}>
                  {prediction.yield_pct}%
                  <span style={{ fontSize: "0.85rem", fontWeight: 600, marginLeft: "0.5rem" }}>
                    {yieldColors.label}
                  </span>
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="card full-span">
          <div className="card-header">
            <h3>Lectura en vivo</h3>
            <span className={`chip ${sensors ? "green" : "orange"}`}>
              {lastUpdate ? `Actualizado ${lastUpdate}` : "Sin lecturas"}
            </span>
          </div>
          <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {!sensors && (
              <div style={{
                padding: "1rem",
                borderRadius: 10,
                background: "rgba(37,99,235,0.06)",
                border: "1px solid rgba(37,99,235,0.14)",
                color: "var(--text-secondary)",
                fontSize: "0.86rem",
                lineHeight: 1.55,
              }}>
                Conecta el Arduino o usa la prueba sin hardware para ver como se actualizan las lecturas.
              </div>
            )}

            <div className="kpi-grid">
              <SensorCard label="Temperatura" value={sensors?.temperature} unit="C" color="#b87c20" note="Sensor DS18B20" />
              <SensorCard label="Luz recibida" value={sensors?.light_lux} unit="lux" color="#c8a020" note="Sensor TSL2561" decimals={0} />
              <SensorCard label="Verdor de hoja" value={sensors?.greenness_idx} unit="%" color="#1e7a4a" note="Sensor TCS3200" />
              <SensorCard label="Humedad suelo" value={sensors?.soil_moisture} unit="vol" color="#5a7a35" note="Higrometro capacitivo" decimals={2} />
            </div>

            {sensors && (
              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                {[["Rojo", sensors.color_r, "#c04040"], ["Verde", sensors.color_g, "#1e7a4a"], ["Azul", sensors.color_b, "#2a6090"]].map(([label, value, color]) => (
                  <div key={label} style={{ flex: 1, minWidth: 110, background: "rgba(15,23,42,0.03)", borderRadius: 8, padding: "0.6rem 0.8rem", borderLeft: `3px solid ${color}` }}>
                    <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", margin: 0 }}>Color {label}</p>
                    <p style={{ fontSize: "1.1rem", fontWeight: 800, color, margin: 0 }}>{value ?? "--"}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="card full-span">
          <div className="card-header">
            <h3>Tendencia reciente</h3>
            <span className="chip">{history.length}/{MAX_HISTORY} lecturas</span>
          </div>
          <div className="card-body">
            {history.length > 1 ? (
              <div style={{ height: 220 }}><ChartCanvas config={historyChart} /></div>
            ) : (
              <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>Esperando lecturas del Arduino...</p>
            )}
          </div>
        </div>

        <div className="card full-span">
          <div className="card-header">
            <h3>Prueba sin hardware</h3>
            <span className="chip orange">Simulador</span>
          </div>
          <div className="card-body">
            <p style={{ margin: "0 0 0.8rem", fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              Usa esta prueba para validar la vista en vivo cuando el Arduino no este conectado.
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "0.5rem 1rem" }}>
              {Object.entries(simForm).map(([key, value]) => (
                <label key={key} className="form-label" style={{ marginBottom: 0 }}>
                  {key.replace("_", " ")}
                  <input
                    className="form-input"
                    type="number"
                    step="0.1"
                    value={value}
                    onChange={(e) => setSimForm((prev) => ({ ...prev, [key]: Number(e.target.value) }))}
                  />
                </label>
              ))}
            </div>
            <button className="btn primary" style={{ marginTop: "1rem", width: "100%", justifyContent: "center" }} onClick={handleSimulate}>
              Enviar lectura de prueba
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
