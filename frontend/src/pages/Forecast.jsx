import { useEffect, useMemo, useState } from "react";
import { cropOptions, municipioOptions } from "../data/constants";
import { getForecast, getAgronomyCalculation, getSowingCalendar } from "../services/api";

// Calendario de siembra para Guatemala (ICTA / FAO / MAGA)
// siembra = meses de plantación (0=Ene..11=Dic), cosecha = meses de cosecha
const SOWING_DATA = {
  "Maiz":          { siembra:[4,5,7,8],   cosecha:[7,8,10,11],  ciclo:"90-120 días",  nota:"Primera may-ago · Postrera ago-nov" },
  "Frijol":        { siembra:[7,8,9],     cosecha:[10,11],      ciclo:"75-100 días",  nota:"Ciclo principal ago-nov" },
  "Cafe":          { siembra:[4,5],       cosecha:[10,11,0,1],  ciclo:"Perenne",      nota:"Trasplante en lluvia; cosecha oct-ene" },
  "Arroz":         { siembra:[4,5,6],     cosecha:[8,9,10],     ciclo:"120-150 días", nota:"Temporada lluviosa" },
  "Papa":          { siembra:[1,2,6,7],   cosecha:[4,5,9,10],   ciclo:"90-120 días",  nota:"Dos ciclos: feb-may · jul-oct" },
  "Tomate":        { siembra:[10,11,0,1], cosecha:[1,2,3,4],    ciclo:"75-90 días",   nota:"Temporada seca con riego" },
  "Aguacate":      { siembra:[4,5,6],     cosecha:[5,6,7,8,9,10,11], ciclo:"Perenne", nota:"Plantación en lluvia" },
  "Cacao":         { siembra:[4,5,6],     cosecha:[9,10,11,0,1,2],  ciclo:"Perenne",  nota:"Cosecha principal oct-feb" },
  "Trigo":         { siembra:[10,11],     cosecha:[1,2,3],      ciclo:"120-140 días", nota:"Altiplano con riego" },
  "Sorgo":         { siembra:[4,5,7,8],   cosecha:[8,9,11,0],   ciclo:"90-120 días",  nota:"Zonas secas de oriente" },
  "Avena":         { siembra:[9,10],      cosecha:[1,2,3],      ciclo:"120-140 días", nota:"Altiplano" },
  "Soya":          { siembra:[5,6],       cosecha:[9,10],       ciclo:"90-120 días",  nota:"Temporada lluviosa" },
  "Zanahoria":     { siembra:[0,1,6,7],   cosecha:[3,4,9,10],   ciclo:"90-120 días",  nota:"Temporada seca y lluviosa" },
  "Cebolla":       { siembra:[10,11,0],   cosecha:[1,2,3],      ciclo:"90-120 días",  nota:"Temporada seca" },
  "Repollo":       { siembra:[7,8,9],     cosecha:[10,11,0],    ciclo:"60-90 días",   nota:"Altiplano guatemalteco" },
  "Brocoli":       { siembra:[7,8,9],     cosecha:[10,11],      ciclo:"60-80 días",   nota:"Clima fresco" },
  "Coliflor":      { siembra:[7,8,9],     cosecha:[10,11,0],    ciclo:"60-80 días",   nota:"Altiplano fresco" },
  "Lechuga":       { siembra:[0,7,8,9,10,11], cosecha:[2,3,10,11,0,1], ciclo:"45-70 días", nota:"Clima fresco todo el año" },
  "Espinaca":      { siembra:[0,9,10,11], cosecha:[2,3,0,1],    ciclo:"40-60 días",   nota:"Clima fresco" },
  "Pepino":        { siembra:[1,2,10,11], cosecha:[3,4,0,1],    ciclo:"55-70 días",   nota:"Con riego" },
  "Chile":         { siembra:[1,2,3],     cosecha:[5,6,7],      ciclo:"90-120 días",  nota:"Temporada seca" },
  "Berenjena":     { siembra:[2,3],       cosecha:[5,6,7],      ciclo:"75-90 días",   nota:"Costa sur" },
  "Zucchini":      { siembra:[1,2,3],     cosecha:[3,4,5],      ciclo:"50-70 días",   nota:"Con riego" },
  "Mango":         { siembra:[4,5],       cosecha:[3,4,5,6],    ciclo:"Perenne",      nota:"Cosecha abr-jun" },
  "Naranja":       { siembra:[4,5],       cosecha:[10,11,0,1],  ciclo:"Perenne",      nota:"Cosecha oct-ene" },
  "Limon":         { siembra:[4,5],       cosecha:[0,1,2,3,4,5,6,7,8,9,10,11], ciclo:"Perenne", nota:"Producción casi continua" },
  "Banano":        { siembra:[4,5,6],     cosecha:[8,9,10],     ciclo:"Perenne 9-12 m", nota:"Trópico húmedo" },
  "Pina":          { siembra:[4,5,6],     cosecha:[4,5,6,7],    ciclo:"12-18 meses",  nota:"Costa sur" },
  "Papaya":        { siembra:[4,5,6],     cosecha:[8,9,10,11],  ciclo:"Perenne 8-10 m", nota:"Todo el año con riego" },
  "Melon":         { siembra:[1,2,3],     cosecha:[4,5,6],      ciclo:"75-90 días",   nota:"Costa sur con riego" },
  "Sandia":        { siembra:[2,3],       cosecha:[5,6],        ciclo:"80-100 días",  nota:"Temporada seca con riego" },
  "Fresa":         { siembra:[9,10],      cosecha:[0,1,2,3],    ciclo:"90-120 días",  nota:"Altiplano frío" },
  "Cana de azucar":{ siembra:[10,11,0],   cosecha:[0,1,2,3,4],  ciclo:"12-14 meses",  nota:"Costa sur; cosecha dic-abr" },
  "Cardamomo":     { siembra:[4,5],       cosecha:[9,10,11,0],  ciclo:"Perenne",      nota:"Alta Verapaz" },
  "Mani":          { siembra:[4,5],       cosecha:[8,9],        ciclo:"90-120 días",  nota:"Temporada lluviosa" },
  "Yuca":          { siembra:[4,5,6],     cosecha:[10,11,0,1,2,3], ciclo:"8-12 meses", nota:"Cosecha escalonada" },
  "Camote":        { siembra:[4,5,6],     cosecha:[9,10,11],    ciclo:"90-120 días",  nota:"Temporada lluviosa" },
};

const MESES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"];
const MES_ACTUAL = new Date().getMonth(); // 0-based

const DAY_ES = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"];
const MONTH_ES = ["ene", "feb", "mar", "abr", "may", "jun",
                  "jul", "ago", "sep", "oct", "nov", "dic"];

function formatDate(iso) {
  const d = new Date(iso + "T12:00:00");
  return `${DAY_ES[d.getDay()]} ${d.getDate()} ${MONTH_ES[d.getMonth()]}`;
}

function RainBar({ prob }) {
  const color = prob >= 75 ? "#2563eb" : prob >= 40 ? "#60a5fa" : "#bfdbfe";
  return (
    <div style={{ height: 4, borderRadius: 2, background: "#e5e7eb", overflow: "hidden", marginTop: 4 }}>
      <div style={{ height: "100%", width: `${prob}%`, background: color, borderRadius: 2, transition: "width .4s" }} />
    </div>
  );
}

function StatBox({ label, value, unit, color = "var(--text-primary)", sub }) {
  return (
    <div style={{ textAlign: "center", padding: "0.75rem 1rem", background: "var(--surface)", borderRadius: 10, border: "1px solid var(--border)" }}>
      <div style={{ fontSize: "1.6rem", fontWeight: 900, color, lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: 2 }}>{unit}</div>
      <div style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--text-secondary)", marginTop: 4 }}>{label}</div>
      {sub && <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

function CalcResult({ icon, title, color, lines }) {
  return (
    <div style={{ background: "var(--surface)", border: `1px solid var(--border)`, borderLeft: `4px solid ${color}`, borderRadius: 10, padding: "1rem" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.6rem" }}>
        <span style={{ fontSize: "1.2rem" }}>{icon}</span>
        <strong style={{ fontSize: "0.85rem", color: "var(--text-primary)" }}>{title}</strong>
      </div>
      {lines.map((l, i) => (
        <p key={i} style={{ margin: i === 0 ? 0 : "0.35rem 0 0", fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>{l}</p>
      ))}
    </div>
  );
}

function buildForecastSummary(forecast) {
  if (!forecast?.summary || !forecast?.days?.length) return null;

  const summary = forecast.summary;
  const days = forecast.days;
  const heavyRain = days.filter((d) => d.rain_mm > 20).length;
  const hotDays = days.filter((d) => d.tmax > 32).length;
  const coldDays = days.filter((d) => d.tmin < 12).length;
  const alerts = [];

  if (summary.irrigation_deficit_mm > 20) {
    alerts.push({
      severity: "high",
      title: "Riego necesario",
      action: "Prepara riego de apoyo esta semana para evitar estres por falta de agua.",
      value: `${summary.irrigation_deficit_mm} mm`,
    });
  } else if (summary.irrigation_deficit_mm > 5) {
    alerts.push({
      severity: "medium",
      title: "Vigila humedad del suelo",
      action: "Hay una falta moderada de agua. Revisa el lote antes de decidir el riego.",
      value: `${summary.irrigation_deficit_mm} mm`,
    });
  }

  if (heavyRain > 0) {
    alerts.push({
      severity: "high",
      title: "Lluvia fuerte",
      action: "Revisa drenajes y evita encharcamientos en las partes bajas del terreno.",
      value: `${heavyRain} dia(s)`,
    });
  }

  if (hotDays > 0) {
    alerts.push({
      severity: "medium",
      title: "Dias de calor fuerte",
      action: "Riega temprano y evita labores pesadas cuando el suelo este muy seco.",
      value: `${hotDays} dia(s)`,
    });
  }

  if (coldDays > 0) {
    alerts.push({
      severity: "medium",
      title: "Noches frias",
      action: "Protege plantulas jovenes o cultivos sensibles durante la noche.",
      value: `${coldDays} noche(s)`,
    });
  }

  const primary = alerts[0] || {
    severity: "low",
    title: "Semana estable",
    action: "El pronostico no muestra una amenaza fuerte. Mantiene observacion normal.",
    value: "Sin alertas fuertes",
  };

  const status =
    primary.severity === "high"
      ? { label: "Atencion esta semana", color: "#ef4444" }
      : primary.severity === "medium"
        ? { label: "Revisar condiciones", color: "#f59e0b" }
        : { label: "Condicion estable", color: "#16a34a" };

  return { status, primary, alerts, heavyRain, hotDays, coldDays };
}

export default function Forecast({ form }) {
  const [municipio, setMunicipio] = useState(form?.municipality || "Chimaltenango");
  const [forecast,  setForecast]  = useState(null);
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState("");

  // ── Calculadora ──────────────────────────────────────────────────────────
  const [calcForm, setCalcForm] = useState({
    crop:             form?.crop || "Maiz",
    current_ph:       form?.soilPh || 6.2,
    current_rainfall: form?.rainfall || 0,
    temperature:      form?.temperature || 22,
  });
  const [calcResult,  setCalcResult]  = useState(null);
  const [calcLoading, setCalcLoading] = useState(false);
  const [calcError,   setCalcError]   = useState("");
  const [sowingRows, setSowingRows] = useState([]);
  const [sowingLoading, setSowingLoading] = useState(false);
  const [sowingError, setSowingError] = useState("");

  // Auto-carga al cambiar municipio
  useEffect(() => {
    loadForecast();
  }, [municipio]);

  useEffect(() => {
    loadSowingCalendar();
  }, [municipio, calcForm.crop]);

  async function loadForecast() {
    setLoading(true);
    setError("");
    setForecast(null);
    try {
      const data = await getForecast(municipio);
      setForecast(data);
      // Pre-llenar rainfall con total semanal del pronóstico
      setCalcForm((prev) => ({ ...prev, current_rainfall: data.summary.total_rain_mm }));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function runCalculator() {
    setCalcLoading(true);
    setCalcError("");
    setCalcResult(null);
    try {
      const result = await getAgronomyCalculation({
        crop:             calcForm.crop,
        municipio,
        current_ph:       Number(calcForm.current_ph),
        current_rainfall: Number(calcForm.current_rainfall),
        temperature:      Number(calcForm.temperature),
        weekly_eto:       forecast?.summary?.total_eto_mm ?? undefined,
      });
      setCalcResult(result);
    } catch (e) {
      setCalcError(e.message);
    } finally {
      setCalcLoading(false);
    }
  }

  async function loadSowingCalendar() {
    setSowingLoading(true);
    setSowingError("");
    try {
      const rows = await getSowingCalendar(municipio, calcForm.crop);
      setSowingRows(rows);
    } catch (e) {
      setSowingRows([]);
      setSowingError(e.message);
    } finally {
      setSowingLoading(false);
    }
  }

  const s = forecast?.summary;
  const remoteSowingRows = sowingRows.filter((row) => Number(row.month) >= 1 && Number(row.month) <= 12);
  const activeSowingData = !sowingError && remoteSowingRows.length ? null : SOWING_DATA[calcForm.crop];
  const forecastSummary = useMemo(() => buildForecastSummary(forecast), [forecast]);

  return (
    <div className="page-content">

      {/* ── Selector de municipio ── */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
        <label style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--text-secondary)" }}>Departamento</label>
        <select
          className="form-select"
          style={{ width: "auto", minWidth: 200 }}
          value={municipio}
          onChange={(e) => setMunicipio(e.target.value)}
        >
          {municipioOptions.map((m) => <option key={m}>{m}</option>)}
        </select>
        <button className="btn ghost" onClick={loadForecast} disabled={loading}>
          {loading ? "Actualizando..." : "Actualizar"}
        </button>
        {forecast && (
          <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
            Fuente: Open-Meteo · Actualizado: {new Date(forecast.generated_at).toLocaleTimeString("es-GT")}
          </span>
        )}
      </div>

      {error && (
        <div style={{ background: "rgba(220,38,38,0.08)", border: "1px solid rgba(220,38,38,0.2)", borderRadius: 10, padding: "0.85rem 1rem", fontSize: "0.82rem", color: "#dc2626" }}>
          Error al obtener pronóstico: {error}. Verifica que el backend esté corriendo.
        </div>
      )}

      {loading && (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {/* Skeleton banner */}
          <div style={{ borderRadius: 14, padding: "1.4rem 1.5rem", background: "var(--surface-alt)", border: "1px solid var(--border)", display: "flex", justifyContent: "space-between", gap: "1rem" }}>
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "0.6rem" }}>
              <div style={{ height: 12, width: 120, borderRadius: 6, background: "var(--border)", animation: "pulse 1.4s ease-in-out infinite" }} />
              <div style={{ height: 28, width: 220, borderRadius: 6, background: "var(--border)", animation: "pulse 1.4s ease-in-out infinite" }} />
              <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.3rem" }}>
                {[80, 100, 70].map((w, i) => <div key={i} style={{ height: 24, width: w, borderRadius: 999, background: "var(--border)", animation: "pulse 1.4s ease-in-out infinite" }} />)}
              </div>
            </div>
            <div style={{ display: "flex", gap: "0.75rem" }}>
              {[0,1,2].map(i => <div key={i} style={{ width: 80, height: 80, borderRadius: 10, background: "var(--border)", animation: "pulse 1.4s ease-in-out infinite" }} />)}
            </div>
          </div>
          {/* Skeleton 7-day cards */}
          <div className="card">
            <div style={{ padding: "1rem 1.15rem", borderBottom: "1px solid var(--border)", height: 24, width: 140, borderRadius: 6, background: "var(--border)", animation: "pulse 1.4s ease-in-out infinite" }} />
            <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: "0.5rem", padding: "1rem" }}>
              {Array.from({ length: 7 }).map((_, i) => (
                <div key={i} style={{ display: "flex", flexDirection: "column", gap: "0.4rem", alignItems: "center" }}>
                  <div style={{ height: 12, width: 30, borderRadius: 4, background: "var(--border)", animation: "pulse 1.4s ease-in-out infinite" }} />
                  <div style={{ height: 32, width: 32, borderRadius: "50%", background: "var(--border)", animation: "pulse 1.4s ease-in-out infinite" }} />
                  <div style={{ height: 10, width: 40, borderRadius: 4, background: "var(--border)", animation: "pulse 1.4s ease-in-out infinite" }} />
                  <div style={{ height: 10, width: 36, borderRadius: 4, background: "var(--border)", animation: "pulse 1.4s ease-in-out infinite" }} />
                </div>
              ))}
            </div>
          </div>
          <p style={{ textAlign: "center", fontSize: "0.78rem", color: "var(--text-muted)", margin: 0 }}>
            Consultando Open-Meteo para {municipio}...
          </p>
        </div>
      )}

      {forecast && forecastSummary && (
        <>
          <div style={{
            background: `${forecastSummary.status.color}10`,
            border: `1px solid ${forecastSummary.status.color}33`,
            borderRadius: 14,
            padding: "1.4rem 1.5rem",
            display: "flex",
            justifyContent: "space-between",
            gap: "1rem",
            flexWrap: "wrap",
          }}>
            <div>
              <p style={{ margin: "0 0 0.3rem", fontSize: "0.76rem", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)" }}>
                Pronostico semanal
              </p>
              <h3 style={{ margin: 0, fontSize: "1.5rem", color: "var(--text-primary)" }}>
                {calcForm.crop} - {municipio}
              </h3>
              <div style={{ display: "flex", gap: "0.55rem", flexWrap: "wrap", marginTop: "0.75rem" }}>
                <span style={{
                  fontSize: "0.74rem",
                  fontWeight: 800,
                  padding: "0.35rem 0.7rem",
                  borderRadius: 999,
                  background: `${forecastSummary.status.color}12`,
                  color: forecastSummary.status.color,
                }}>
                  {forecastSummary.status.label}
                </span>
                <span style={{
                  fontSize: "0.74rem",
                  fontWeight: 700,
                  padding: "0.35rem 0.7rem",
                  borderRadius: 999,
                  background: "var(--surface-hover)",
                  color: "var(--text-secondary)",
                }}>
                  Principal: {forecastSummary.primary.title}
                </span>
              </div>
              <p style={{ margin: "0.8rem 0 0", fontSize: "0.84rem", color: "var(--text-secondary)", maxWidth: 560 }}>
                {forecastSummary.primary.action}
              </p>
            </div>
            <div style={{
              minWidth: 190,
              textAlign: "center",
              background: "var(--surface)",
              border: "1px solid var(--border-strong)",
              borderRadius: 12,
              padding: "0.8rem 1rem",
            }}>
              <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.08em" }}>
                Que esperar
              </div>
              <div style={{ fontSize: "1.55rem", fontWeight: 900, color: forecastSummary.status.color, lineHeight: 1.1, marginTop: "0.35rem" }}>
                {s.total_rain_mm} mm
              </div>
              <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)", fontWeight: 700, marginTop: 4 }}>
                de lluvia total
              </div>
              <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", marginTop: 8 }}>
                Riego faltante: {s.irrigation_deficit_mm} mm
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h3>Lo mas importante esta semana</h3>
              <span className="chip">{forecastSummary.alerts.length} avisos</span>
            </div>
            <div className="card-body" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "0.75rem" }}>
              <div style={{ padding: "0.9rem 1rem", borderRadius: 10, background: "var(--bg)", border: "1px solid var(--border)" }}>
                <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "0.3rem" }}>
                  Lluvia esperada
                </div>
                <div style={{ fontSize: "1.1rem", fontWeight: 800, color: s.total_rain_mm > 50 ? "#2563eb" : s.total_rain_mm < 15 ? "#ef4444" : "#16a34a" }}>
                  {s.total_rain_mm} mm en 7 dias
                </div>
                <p style={{ margin: "0.4rem 0 0", fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                  {s.rainy_days > 0 ? `${s.rainy_days} dia(s) con lluvia probable.` : "No se esperan lluvias fuertes."}
                </p>
              </div>
              <div style={{ padding: "0.9rem 1rem", borderRadius: 10, background: "var(--bg)", border: "1px solid var(--border)" }}>
                <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "0.3rem" }}>
                  Agua para el cultivo
                </div>
                <div style={{ fontSize: "1.1rem", fontWeight: 800, color: s.irrigation_deficit_mm > 20 ? "#ef4444" : s.irrigation_deficit_mm > 5 ? "#f59e0b" : "#16a34a" }}>
                  {s.irrigation_deficit_mm > 5 ? "Puede faltar agua" : "Sin falta fuerte"}
                </div>
                <p style={{ margin: "0.4rem 0 0", fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                  {s.irrigation_deficit_mm > 5 ? `El sistema estima ${s.irrigation_deficit_mm} mm por suplir.` : "La lluvia cubre casi toda la necesidad estimada."}
                </p>
              </div>
              <div style={{ padding: "0.9rem 1rem", borderRadius: 10, background: "var(--bg)", border: "1px solid var(--border)" }}>
                <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "0.3rem" }}>
                  Temperatura
                </div>
                <div style={{ fontSize: "1.1rem", fontWeight: 800, color: forecastSummary.hotDays > 0 ? "#ef4444" : forecastSummary.coldDays > 0 ? "#2563eb" : "#16a34a" }}>
                  Max {s.avg_tmax} C / Min {s.avg_tmin} C
                </div>
                <p style={{ margin: "0.4rem 0 0", fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                  {forecastSummary.hotDays > 0
                    ? `${forecastSummary.hotDays} dia(s) con calor fuerte.`
                    : forecastSummary.coldDays > 0
                    ? `${forecastSummary.coldDays} noche(s) frias.`
                    : "Se espera temperatura manejable esta semana."}
                </p>
              </div>
            </div>
          </div>
          {/* ── Resumen semanal ── */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px,1fr))", gap: "0.65rem" }}>
            <StatBox label="Lluvia total" value={s.total_rain_mm} unit="mm esta semana"
              color={s.total_rain_mm > 50 ? "#2563eb" : s.total_rain_mm < 15 ? "#ef4444" : "#16a34a"} />
            <StatBox label="Demanda de agua" value={s.total_eto_mm} unit="mm estimados"
              color="#b87c20"
              sub="Dato tecnico de apoyo" />
            <StatBox label="Riego faltante" value={s.irrigation_deficit_mm} unit="mm por suplir"
              color={s.irrigation_deficit_mm > 20 ? "#ef4444" : s.irrigation_deficit_mm > 5 ? "#f59e0b" : "#16a34a"}
              sub={s.irrigation_deficit_mm > 5 ? "Conviene revisar" : "Sin apoyo fuerte"} />
            <StatBox label="Dias con lluvia" value={s.rainy_days} unit="de 7 dias"
              color="var(--text-primary)" />
            <StatBox label="Temp. maxima prom." value={s.avg_tmax} unit="C"
              color={s.avg_tmax > 30 ? "#ef4444" : "#b87c20"} />
            <StatBox label="Temp. minima prom." value={s.avg_tmin} unit="C"
              color={s.avg_tmin < 15 ? "#2563eb" : "var(--text-primary)"} />
          </div>

          {/* ── Cards de 7 días ── */}
          <div className="card">
            <div className="card-header">
              <h3>Pronostico dia a dia</h3>
              <span className="chip">{forecast.altitud_m} m s.n.m.</span>
            </div>
            <div className="card-body">
              <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: "0.5rem" }}>
                {forecast.days.map((day) => {
                  const isRainy = day.rain_mm > 5;
                  return (
                    <div key={day.date} style={{
                      background: isRainy ? "rgba(37,99,235,0.04)" : "var(--bg)",
                      border: `1px solid ${isRainy ? "rgba(37,99,235,0.2)" : "var(--border)"}`,
                      borderRadius: 10, padding: "0.75rem 0.5rem", textAlign: "center",
                    }}>
                      <div style={{ fontSize: "0.68rem", fontWeight: 700, color: "var(--text-muted)", marginBottom: 4, textTransform: "uppercase" }}>
                        {formatDate(day.date)}
                      </div>
                      <div style={{ fontSize: "1.8rem", lineHeight: 1, margin: "0.3rem 0" }}>{day.icon}</div>
                      <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginBottom: 6 }}>{day.desc}</div>

                      <div style={{ fontSize: "0.92rem", fontWeight: 800, color: "#b87c20" }}>{day.tmax} C</div>
                      <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>{day.tmin} C</div>

                      <div style={{ marginTop: "0.5rem", fontSize: "0.75rem", fontWeight: 700, color: day.rain_mm > 10 ? "#2563eb" : "var(--text-muted)" }}>
                        {day.rain_mm} mm
                      </div>
                      <RainBar prob={day.rain_prob} />
                      <div style={{ fontSize: "0.62rem", color: "var(--text-muted)", marginTop: 2 }}>{day.rain_prob}% prob.</div>

                      <div style={{ marginTop: "0.4rem", fontSize: "0.62rem", color: "var(--text-muted)" }}>
                        Dato tecnico: ETo {day.eto_mm} mm
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Alerta semanal narrativa */}
              {(() => {
                const heavyRain = forecast.days.filter((d) => d.rain_mm > 20).length;
                const hotDays   = forecast.days.filter((d) => d.tmax > 32).length;
                const coldDays  = forecast.days.filter((d) => d.tmin < 12).length;
                if (!heavyRain && !hotDays && !coldDays) return null;
                return (
                  <div style={{ marginTop: "0.85rem", background: "rgba(245,158,11,0.07)", border: "1px solid rgba(245,158,11,0.25)", borderRadius: 8, padding: "0.75rem 1rem", fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                    <strong style={{ color: "#d97706" }}>Acciones sugeridas esta semana:</strong>{" "}
                    {heavyRain > 0 && `${heavyRain} dia(s) con lluvia intensa. Revisa drenajes y protege cultivos sensibles. `}
                    {hotDays   > 0 && `${hotDays} dia(s) con calor extremo. Incrementa el riego matutino. `}
                    {coldDays  > 0 && `${coldDays} noche(s) con temperatura baja. Protege plantulas jovenes.`}
                  </div>
                );
              })()}
            </div>
          </div>
        </>
      )}

      {/* ── Calendario de siembra ── */}
      {(() => {
        const crop = calcForm.crop;

        if (sowingLoading) {
          return (
            <div className="card">
              <div className="card-header">
                <h3>Mejor momento para sembrar</h3>
                <span className="chip">Consultando historial</span>
              </div>
              <div className="card-body">
                <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-muted)" }}>
                  Cargando meses recomendados para {municipio}...
                </p>
              </div>
            </div>
          );
        }

        if (remoteSowingRows.length) {
          return (
            <div className="card">
              <div className="card-header">
                <h3>Mejor momento para sembrar</h3>
                <span className="chip">{municipio} segun historial</span>
              </div>
              <div className="card-body">
                <p style={{ margin: "0 0 0.85rem", fontSize: "0.82rem", color: "var(--text-secondary)" }}>
                  Usa esta guia para decidir si conviene sembrar ahora o esperar un mes con mejores condiciones para {crop}.
                </p>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(58px, 1fr))", gap: "0.3rem", marginBottom: "0.85rem" }}>
                  {Array.from({ length: 12 }, (_, index) => {
                    const monthNumber = index + 1;
                    const row = remoteSowingRows.find((item) => Number(item.month) === monthNumber);
                    const isTop3 = Boolean(row?.is_top3);
                    const isCurrent = index === MES_ACTUAL;
                    const bg = isTop3 ? "#16a34a" : row ? "#d97706" : "var(--bg)";
                    const color = row ? "#fff" : "var(--text-muted)";
                    const label = isTop3 ? "SI" : row ? "OK" : "NO";
                    return (
                      <div key={monthNumber} style={{
                        textAlign: "center",
                        padding: "0.5rem 0.2rem",
                        borderRadius: 8,
                        background: bg,
                        color,
                        border: isCurrent ? "2px solid #d97706" : `1px solid ${row ? "transparent" : "var(--border)"}`,
                        fontWeight: isTop3 ? 800 : row ? 700 : 400,
                      }}>
                        <div style={{ fontSize: "0.68rem" }}>{MESES[index]}</div>
                        <div style={{ fontSize: "0.95rem", lineHeight: 1.2, marginTop: 2 }}>
                          {label}
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: "0.65rem", marginBottom: "0.75rem" }}>
                  {remoteSowingRows.slice(0, 3).map((row) => (
                    <div key={`${row.crop}-${row.month}`} style={{ border: "1px solid var(--border)", borderRadius: 10, padding: "0.8rem", background: "var(--surface)" }}>
                      <p style={{ margin: 0, fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>
                        Mes recomendado
                      </p>
                      <strong style={{ display: "block", marginTop: "0.25rem", fontSize: "1rem", color: "#2563eb" }}>
                        {MESES[Number(row.month) - 1]}
                      </strong>
                      <p style={{ margin: "0.2rem 0 0", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                        Buen momento para planificar siembra.
                      </p>
                    </div>
                  ))}
                </div>
                <div style={{ display: "flex", gap: "1.25rem", flexWrap: "wrap", fontSize: "0.76rem", color: "var(--text-secondary)" }}>
                  <span><span style={{ display:"inline-block", width:10, height:10, borderRadius:3, background:"#16a34a", marginRight:5, verticalAlign:"middle" }}/>Mejor momento</span>
                  <span><span style={{ display:"inline-block", width:10, height:10, borderRadius:3, background:"#d97706", marginRight:5, verticalAlign:"middle" }}/>Bueno si hay manejo</span>
                  <span><span style={{ display:"inline-block", width:10, height:10, borderRadius:3, border:"2px solid #d97706", marginRight:5, verticalAlign:"middle" }}/>Mes actual</span>
                </div>
              </div>
            </div>
          );
        }

        const data = activeSowingData;
        if (!data) return null;
        return (
          <div className="card">
            <div className="card-header">
              <h3>Mejor momento para sembrar</h3>
              <span className="chip">{data.ciclo} · referencia local</span>
            </div>
            <div className="card-body">
              {sowingError && (
                <p style={{ margin: "0 0 0.65rem", fontSize: "0.78rem", color: "#b45309" }}>
                  No se pudo consultar el historial del backend. Mostrando referencia agronomica local.
                </p>
              )}
              <p style={{ margin: "0 0 0.85rem", fontSize: "0.82rem", color: "var(--text-secondary)" }}>
                {data.nota}
              </p>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(58px, 1fr))", gap: "0.3rem", marginBottom: "0.75rem" }}>
                {MESES.map((m, i) => {
                  const esSiembra = data.siembra.includes(i);
                  const esCosecha = data.cosecha.includes(i);
                  const esHoy = i === MES_ACTUAL;
                  const bg = esCosecha ? "#1e7a4a" : esSiembra ? "#2563eb" : "var(--bg)";
                  const color = (esSiembra || esCosecha) ? "#fff" : "var(--text-muted)";
                  return (
                    <div key={m} style={{
                      textAlign: "center", padding: "0.5rem 0.2rem", borderRadius: 8,
                      background: bg, color,
                      border: esHoy ? "2px solid #d97706" : `1px solid ${esSiembra || esCosecha ? "transparent" : "var(--border)"}`,
                      fontWeight: esHoy ? 800 : (esSiembra || esCosecha) ? 700 : 400,
                    }}>
                      <div style={{ fontSize: "0.68rem" }}>{m}</div>
                      <div style={{ fontSize: "1rem", lineHeight: 1.2, marginTop: 2 }}>
                        {esCosecha ? "C" : esSiembra ? "S" : "-"}
                      </div>
                    </div>
                  );
                })}
              </div>
              <div style={{ display: "flex", gap: "1.25rem", flexWrap: "wrap", fontSize: "0.76rem", color: "var(--text-secondary)" }}>
                <span><span style={{ display:"inline-block", width:10, height:10, borderRadius:3, background:"#2563eb", marginRight:5, verticalAlign:"middle" }}/>S = Siembra recomendada</span>
                <span><span style={{ display:"inline-block", width:10, height:10, borderRadius:3, background:"#1e7a4a", marginRight:5, verticalAlign:"middle" }}/>C = Cosecha esperada</span>
                <span><span style={{ display:"inline-block", width:10, height:10, borderRadius:3, border:"2px solid #d97706", marginRight:5, verticalAlign:"middle" }}/>Mes actual</span>
              </div>
            </div>
          </div>
        );
      })()}

      {/* ── Calculadora de riego y fertilización ── */}
      <div className="card">
        <div className="card-header">
          <h3>Apoyo para riego y nutricion</h3>
          <span className="chip">Usa lluvia, temperatura y pH</span>
        </div>
        <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px,1fr))", gap: "0.75rem", alignItems: "end" }}>
            <label className="form-label">
              Cultivo
              <select className="form-select" value={calcForm.crop} onChange={(e) => setCalcForm((p) => ({ ...p, crop: e.target.value }))}>
                {cropOptions.map((c) => <option key={c}>{c}</option>)}
              </select>
            </label>
            <label className="form-label">
              pH del suelo actual
              <input className="form-input" type="number" min="3.5" max="9.5" step="0.1"
                value={calcForm.current_ph}
                onChange={(e) => setCalcForm((p) => ({ ...p, current_ph: e.target.value }))} />
            </label>
            <label className="form-label">
              Lluvia esta semana (mm)
              <input className="form-input" type="number" min="0" max="500" step="0.5"
                value={calcForm.current_rainfall}
                onChange={(e) => setCalcForm((p) => ({ ...p, current_rainfall: e.target.value }))} />
            </label>
            <label className="form-label">
              Temperatura media (C)
              <input className="form-input" type="number" min="5" max="45" step="0.5"
                value={calcForm.temperature}
                onChange={(e) => setCalcForm((p) => ({ ...p, temperature: e.target.value }))} />
            </label>
            <div style={{ paddingBottom: "0.1rem" }}>
              <button className="btn primary" style={{ width: "100%", justifyContent: "center" }}
                onClick={runCalculator} disabled={calcLoading}>
                {calcLoading ? "Calculando..." : "Calcular apoyo"}
              </button>
            </div>
          </div>

          {forecast && (
            <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Referencia automatica del pronostico: lluvia <strong>{forecast.summary.total_rain_mm} mm</strong> · demanda de agua <strong>{forecast.summary.total_eto_mm} mm</strong>
            </p>
          )}

          {calcError && (
            <p style={{ margin: 0, fontSize: "0.8rem", color: "#dc2626" }}>Error: {calcError}</p>
          )}

          {calcResult && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px,1fr))", gap: "0.75rem" }}>

              {/* Riego */}
              <CalcResult
                icon="💧"
                title="Riego"
                color={calcResult.irrigation.deficit_mm > 20 ? "#ef4444" : calcResult.irrigation.deficit_mm > 5 ? "#f59e0b" : "#16a34a"}
                lines={[
                  calcResult.irrigation.recomendacion,
                  `Faltante estimado: ${calcResult.irrigation.deficit_mm} mm -> ${calcResult.irrigation.litros_por_cuerda.toLocaleString()} litros/cuerda`,
                  `Dato tecnico: ETc ${calcResult.irrigation.etc_cultivo_mm} mm, lluvia ${calcResult.irrigation.lluvia_semana_mm} mm`,
                ]}
              />

              {/* Cal */}
              <CalcResult
                icon="🪣"
                title={calcResult.lime.accion === "encalar" ? "Cal agricola" : calcResult.lime.accion === "acidificar" ? "Correccion alcalinidad" : "pH del suelo"}
                color={calcResult.lime.accion === "ninguna" ? "#16a34a" : "#f59e0b"}
                lines={[
                  calcResult.lime.recomendacion,
                  `pH actual: ${calcResult.lime.ph_actual} -> Objetivo para ${calcResult.crop}: ${calcResult.lime.ph_objetivo}`,
                  ...(calcResult.lime.cal_kg_cuerda
                    ? [`Aplicacion sugerida: ${calcResult.lime.cal_kg_cuerda} kg/cuerda (${calcResult.lime.cal_qq_cuerda} qq) de ${calcResult.lime.producto}`]
                    : calcResult.lime.azufre_kg_cuerda
                    ? [`Aplicacion sugerida: ${calcResult.lime.azufre_kg_cuerda} kg/cuerda de ${calcResult.lime.producto}`]
                    : []),
                ]}
              />

              {/* Nitrógeno */}
              <CalcResult
                icon="🌱"
                title="Nitrogeno"
                color="#1e7a4a"
                lines={[
                  calcResult.nitrogen.recomendacion,
                  `Dosis estimada: ${calcResult.nitrogen.n_kg_por_cuerda} kg N/cuerda`,
                  `Urea 46%: ${calcResult.nitrogen.fuentes.urea_46pct_kg} kg · Sulfato de amonio 21%: ${calcResult.nitrogen.fuentes.sulfato_amonio_21pct_kg} kg`,
                  `Aplicacion sugerida: ${calcResult.nitrogen.fraccionamiento}`,
                ]}
              />

            </div>
          )}
        </div>
      </div>

    </div>
  );
}
