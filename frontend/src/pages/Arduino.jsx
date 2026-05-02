import { useEffect, useRef, useState } from "react";
import ChartCanvas from "../components/ChartCanvas";
import { cropOptions, municipioOptions } from "../data/constants";
import {
  connectArduino, disconnectArduino, getArduinoStatus,
  simulateArduino, setArduinoConfig,
  uploadDataset, getDatasetTemplateUrl, createArduinoSocket,
} from "../services/api";

const MAX_HISTORY = 20;
const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const YIELD_COLOR = {
  alto:    { bg: "rgba(30,122,74,0.12)",  border: "#1e7a4a", text: "#1e7a4a" },
  medio:   { bg: "rgba(184,124,32,0.12)", border: "#b87c20", text: "#b87c20" },
  bajo:    { bg: "rgba(192,64,64,0.10)",  border: "#c04040", text: "#c04040" },
  critico: { bg: "rgba(140,20,20,0.12)",  border: "#8c1414", text: "#8c1414" },
};

export default function Arduino() {
  // ── Conexión ────────────────────────────────────────────────────────
  const [connected,   setConnected]   = useState(false);
  const [port,        setPort]        = useState("");
  const [availPorts,  setAvailPorts]  = useState([]);
  const [statusMsg,   setStatusMsg]   = useState("Sin conexión");
  const [wsReady,     setWsReady]     = useState(false);
  const wsRef = useRef(null);

  // ── Config cultivo ───────────────────────────────────────────────────
  const [municipio, setMunicipio] = useState("Chimaltenango");
  const [crop,      setCrop]      = useState("Maiz");

  // ── Lectura actual ───────────────────────────────────────────────────
  const [sensors,    setSensors]    = useState(null);
  const [prediction, setPrediction] = useState(null);

  // ── Historial para gráfico ───────────────────────────────────────────
  const [history, setHistory] = useState([]);

  // ── Upload CSV ───────────────────────────────────────────────────────
  const [uploadMsg,  setUploadMsg]  = useState("");
  const [uploading,  setUploading]  = useState(false);
  const fileInputRef = useRef(null);

  // ── Alertas por correo ───────────────────────────────────────────────
  const [emailTo,       setEmailTo]       = useState("");
  const [emailSaving,   setEmailSaving]   = useState(false);
  const [emailMsg,      setEmailMsg]      = useState({ text: "", ok: true });
  const [emailTesting,  setEmailTesting]  = useState(false);

  const ADMIN_TOKEN = "agroclima-admin-2024";

  // ── Simular ──────────────────────────────────────────────────────────
  const [simForm, setSimForm] = useState({
    temperature: 22,      // DS18B20
    light_lux:   32000,   // TSL2561
    color_r:     145,     // TCS3200
    color_g:     210,     // TCS3200
    color_b:     98,      // TCS3200
    soil_moisture: 0.31,  // Higrómetro capacitivo
    humidity:    74,      // manual/ERA5
    rainfall:    45,      // manual/ERA5
    soil_ph:     6.3,     // manual
  });

  // ------------------------------------------------------------------
  // WebSocket
  // ------------------------------------------------------------------

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
      () => { setWsReady(false); setStatusMsg("WebSocket desconectado."); }
    );
    ws.onopen = () => { setWsReady(true); sendConfig(ws, municipio, crop); };
    wsRef.current = ws;
  }

  function sendConfig(ws, mun, cr) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ municipio: mun, crop: cr }));
    }
  }

  useEffect(() => {
    // Cargar puertos disponibles
    getArduinoStatus()
      .then((s) => {
        setAvailPorts(s.ports || []);
        setConnected(s.connected);
        if (s.connected) { setPort(s.port || ""); setStatusMsg(`Conectado en ${s.port}`); }
      })
      .catch(() => {});
    openSocket();
    return () => { if (wsRef.current) wsRef.current.close(); };
  }, []);

  // Cuando cambia crop/municipio, actualizar config en backend y socket
  useEffect(() => {
    setArduinoConfig(municipio, crop).catch(() => {});
    sendConfig(wsRef.current, municipio, crop);
  }, [municipio, crop]);

  // ------------------------------------------------------------------
  // Acciones
  // ------------------------------------------------------------------

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

  async function handleSaveEmail() {
    if (!emailTo.trim()) return;
    setEmailSaving(true);
    setEmailMsg({ text: "", ok: true });
    try {
      const res = await fetch(`${API}/admin/email-config`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-admin-token": ADMIN_TOKEN },
        body: JSON.stringify({ email_to: emailTo.trim(), severidad_min: "severo" }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Error");
      setEmailMsg({ text: "Correo guardado correctamente.", ok: true });
    } catch (e) {
      setEmailMsg({ text: `Error: ${e.message}`, ok: false });
    } finally {
      setEmailSaving(false);
    }
  }

  async function handleTestEmail() {
    setEmailTesting(true);
    setEmailMsg({ text: "", ok: true });
    try {
      const res = await fetch(`${API}/admin/email-test`, {
        method: "POST",
        headers: { "x-admin-token": ADMIN_TOKEN },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Error");
      setEmailMsg({ text: data.message, ok: true });
    } catch (e) {
      setEmailMsg({ text: `Error: ${e.message}`, ok: false });
    } finally {
      setEmailTesting(false);
    }
  }

  async function handleUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setUploadMsg("");
    try {
      const res = await uploadDataset(file);
      setUploadMsg(`${res.message}`);
    } catch (err) {
      setUploadMsg(`Error: ${err.message}`);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  // ------------------------------------------------------------------
  // Gráfico de historial
  // ------------------------------------------------------------------

  const historyChart = {
    type: "line",
    data: {
      labels: history.map((h) => h.ts),
      datasets: [
        { label: "Temperatura (°C)",  data: history.map((h) => h.temperature),   borderColor: "#b87c20", tension: 0.4, pointRadius: 2, yAxisID: "y" },
        { label: "Verdor (%)",        data: history.map((h) => h.greenness_idx),  borderColor: "#1e7a4a", tension: 0.4, pointRadius: 2, yAxisID: "y" },
        { label: "Humedad suelo",     data: history.map((h) => h.soil_moisture ? (h.soil_moisture * 100).toFixed(1) : null), borderColor: "#5a7a35", tension: 0.4, pointRadius: 2, yAxisID: "y" },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: "bottom", labels: { boxWidth: 10, padding: 12 } } },
      scales: {
        x: { ticks: { maxTicksLimit: 8 }, grid: { color: "rgba(80,60,35,0.06)" } },
        y: { grid: { color: "rgba(80,60,35,0.06)" } },
      },
    },
  };

  // ------------------------------------------------------------------
  // Render helpers
  // ------------------------------------------------------------------

  const yieldColors = prediction ? (YIELD_COLOR[prediction.yield_level] || YIELD_COLOR.medio) : null;

  function SensorCard({ label, value, unit, color = "#1e7a4a" }) {
    return (
      <div className="card kpi-card" style={{ minWidth: 0 }}>
        <span className="kpi-label">{label}</span>
        <div className="kpi-value" style={{ color }}>
          {value !== undefined && value !== null ? value : "—"}
          <span style={{ fontSize: "0.85rem", fontWeight: 400, marginLeft: "0.25rem" }}>{unit}</span>
        </div>
      </div>
    );
  }

  // ------------------------------------------------------------------
  // JSX
  // ------------------------------------------------------------------

  return (
    <div className="page-content">
      <div className="two-col">

        {/* ── Conexión Arduino ─────────────────────────────────────── */}
        <div className="card">
          <div className="card-header">
            <h3>Conexion Arduino</h3>
            <span className={`chip ${connected ? "green" : "orange"}`}>
              {connected ? "Conectado" : "Desconectado"}
            </span>
          </div>
          <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <label className="form-label">
              Puerto Serial
              <select
                className="form-select"
                value={port}
                onChange={(e) => setPort(e.target.value)}
              >
                <option value="">-- Auto detectar --</option>
                {availPorts.map((p) => (
                  <option key={p.device} value={p.device}>
                    {p.device} {p.description ? `— ${p.description}` : ""}
                  </option>
                ))}
              </select>
            </label>

            <div style={{ display: "flex", gap: "0.5rem" }}>
              {!connected
                ? <button className="btn primary" style={{ flex: 1 }} onClick={handleConnect}>Conectar</button>
                : <button className="btn ghost"   style={{ flex: 1 }} onClick={handleDisconnect}>Desconectar</button>
              }
            </div>

            <p style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>{statusMsg}</p>
            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              WS: <span style={{ color: wsReady ? "#1e7a4a" : "#c04040", fontWeight: 600 }}>
                {wsReady ? "activo" : "inactivo"}
              </span>
            </p>
          </div>
        </div>

        {/* ── Config cultivo ───────────────────────────────────────── */}
        <div className="card">
          <div className="card-header">
            <h3>Cultivo analizado</h3>
            <span className="chip">XGBoost</span>
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
              <div style={{ padding: "0.75rem 1rem", borderRadius: "8px", background: yieldColors.bg, borderLeft: `3px solid ${yieldColors.border}` }}>
                <p style={{ fontSize: "0.72rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)", marginBottom: "0.3rem" }}>
                  Rendimiento estimado
                </p>
                <p style={{ fontSize: "1.8rem", fontWeight: 800, color: yieldColors.text, margin: 0 }}>
                  {prediction.yield_pct}%
                  <span style={{ fontSize: "0.85rem", fontWeight: 500, marginLeft: "0.5rem", textTransform: "capitalize" }}>
                    — {prediction.yield_level}
                  </span>
                </p>
              </div>
            )}
          </div>
        </div>

        {/* ── Sensores en tiempo real ───────────────────────────────── */}
        <div className="card full-span">
          <div className="card-header">
            <h3>Lecturas del sensor</h3>
            <span className="chip">{sensors ? new Date(sensors.timestamp).toLocaleTimeString() : "Sin datos"}</span>
          </div>
          <div className="card-body">
            <div className="kpi-grid">
              <SensorCard label="Temperatura (DS18B20)"    value={sensors?.temperature}   unit="°C"  color="#b87c20" />
              <SensorCard label="Luz (TSL2561)"            value={sensors?.light_lux}     unit="lux" color="#c8a020" />
              <SensorCard label="Verdor (TCS3200)"         value={sensors?.greenness_idx} unit="%"   color="#1e7a4a" />
              <SensorCard label="Humedad suelo (Higrom.)"  value={sensors?.soil_moisture} unit="vol" color="#5a7a35" />
            </div>
            {sensors && (
              <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                {[["R", sensors.color_r, "#c04040"], ["G", sensors.color_g, "#1e7a4a"], ["B", sensors.color_b, "#2a6090"]].map(([ch, val, col]) => (
                  <div key={ch} style={{ flex: 1, minWidth: "80px", background: "var(--bg-subtle, rgba(0,0,0,0.04))", borderRadius: "8px", padding: "0.5rem 0.75rem", borderLeft: `3px solid ${col}` }}>
                    <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", margin: 0 }}>TCS3200 {ch}</p>
                    <p style={{ fontSize: "1.1rem", fontWeight: 700, color: col, margin: 0 }}>{val ?? "—"}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ── Historial ────────────────────────────────────────────── */}
        <div className="card full-span">
          <div className="card-header">
            <h3>Historial de lecturas</h3>
            <span className="chip">Ultimas {MAX_HISTORY}</span>
          </div>
          <div className="card-body">
            {history.length > 1
              ? <div style={{ height: "220px" }}><ChartCanvas config={historyChart} /></div>
              : <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>Esperando lecturas del Arduino...</p>
            }
          </div>
        </div>

        {/* ── Simulador ────────────────────────────────────────────── */}
        <div className="card">
          <div className="card-header">
            <h3>Simular lectura</h3>
            <span className="chip orange">Sin hardware</span>
          </div>
          <div className="card-body">
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem 1rem" }}>
              {Object.entries(simForm).map(([k, v]) => (
                <label key={k} className="form-label" style={{ marginBottom: 0 }}>
                  {k.replace("_", " ")}
                  <input
                    className="form-input"
                    type="number"
                    step="0.1"
                    value={v}
                    onChange={(e) => setSimForm((p) => ({ ...p, [k]: Number(e.target.value) }))}
                  />
                </label>
              ))}
            </div>
            <button className="btn primary" style={{ marginTop: "1rem", width: "100%", justifyContent: "center" }} onClick={handleSimulate}>
              Enviar simulacion
            </button>
          </div>
        </div>

        {/* ── Importar CSV ─────────────────────────────────────────── */}
        <div className="card">
          <div className="card-header">
            <h3>Importar dataset CSV</h3>
            <span className="chip">Manual</span>
          </div>
          <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <p style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
              Sube un CSV con columnas: <strong>municipio, crop, temperature, rainfall, humidity, soil_ph</strong>.
              Columnas opcionales: month, soil_moisture, yield_pct.
            </p>
            <a
              href={getDatasetTemplateUrl()}
              download
              className="btn ghost"
              style={{ textAlign: "center", justifyContent: "center" }}
            >
              Descargar plantilla
            </a>
            <button
              className="btn primary"
              style={{ width: "100%", justifyContent: "center" }}
              onClick={() => fileInputRef.current.click()}
              disabled={uploading}
            >
              {uploading ? "Subiendo..." : "Seleccionar archivo CSV"}
            </button>
            <input ref={fileInputRef} type="file" accept=".csv" style={{ display: "none" }} onChange={handleUpload} />
            {uploadMsg && (
              <p style={{ fontSize: "0.8rem", color: uploadMsg.startsWith("Error") ? "#c04040" : "#1e7a4a" }}>
                {uploadMsg}
              </p>
            )}
          </div>
        </div>

        {/* ── Alertas por correo ──────────────────────────────────── */}
        <div className="card full-span">
          <div className="card-header">
            <h3>Alertas criticas por correo electronico</h3>
            <span className="chip orange">Requiere .env configurado</span>
          </div>
          <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
            <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              Cuando el Arduino detecta una condicion <strong>severa</strong> (temperatura extrema, pH crítico, sequía, etc.),
              el sistema envía automaticamente un correo de alerta. Se respeta un intervalo minimo de <strong>30 minutos</strong> entre
              correos del mismo tipo para evitar spam.
            </p>

            <div style={{ background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 10, padding: "1rem", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
              <strong style={{ color: "var(--text-primary)", display: "block", marginBottom: "0.5rem" }}>
                Configuracion SMTP (archivo <code>.env</code> en el backend)
              </strong>
              <div style={{ fontFamily: "monospace", lineHeight: 1.8, color: "var(--text-muted)" }}>
                SMTP_HOST=smtp.gmail.com<br />
                SMTP_PORT=587<br />
                SMTP_USER=tucorreo@gmail.com<br />
                SMTP_PASSWORD=xxxx xxxx xxxx xxxx<br />
                ALERT_EMAIL_FROM=tucorreo@gmail.com
              </div>
              <p style={{ margin: "0.5rem 0 0", fontSize: "0.75rem" }}>
                Para Gmail: Mi cuenta → Seguridad → Verificacion en 2 pasos → <strong>Contraseñas de aplicacion</strong>
              </p>
            </div>

            <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-end", flexWrap: "wrap" }}>
              <label className="form-label" style={{ flex: 1, minWidth: 220, margin: 0 }}>
                Correo destinatario
                <input
                  className="form-input"
                  type="email"
                  placeholder="ejemplo@gmail.com"
                  value={emailTo}
                  onChange={(e) => setEmailTo(e.target.value)}
                />
              </label>
              <button
                className="btn primary"
                onClick={handleSaveEmail}
                disabled={emailSaving || !emailTo.trim()}
              >
                {emailSaving ? "Guardando..." : "Guardar correo"}
              </button>
              <button
                className="btn ghost"
                onClick={handleTestEmail}
                disabled={emailTesting}
                title="Envia un correo de prueba para verificar la configuracion SMTP"
              >
                {emailTesting ? "Enviando..." : "Enviar prueba"}
              </button>
            </div>

            {emailMsg.text && (
              <p style={{ margin: 0, fontSize: "0.8rem", fontWeight: 600, color: emailMsg.ok ? "#16a34a" : "#dc2626" }}>
                {emailMsg.ok ? "✓" : "✗"} {emailMsg.text}
              </p>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
