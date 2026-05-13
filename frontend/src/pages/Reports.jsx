import { useEffect, useRef, useState } from "react";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import { getRecommendations } from "../services/api";

function rainfallStatus(mm) {
  if (mm > 85) {
    return {
      color: "#ef4444",
      label: "Lluvia excesiva",
      tag: "LLUVIA",
      msg: "Demasiada lluvia. Revisa drenajes, evita encharcamientos y no agregues mas riego.",
    };
  }
  if (mm > 65) {
    return {
      color: "#16a34a",
      label: "Lluvia normal",
      tag: "LLUVIA",
      msg: "La lluvia esta en un rango bueno para esta semana.",
    };
  }
  if (mm > 45) {
    return {
      color: "#f59e0b",
      label: "Lluvia baja",
      tag: "LLUVIA",
      msg: "La lluvia viene baja. Revisa si el suelo ya necesita apoyo con riego.",
    };
  }
  return {
    color: "#ef4444",
    label: "Muy poca lluvia",
    tag: "LLUVIA",
    msg: "Hay sequia. Riega pronto y cubre el suelo para guardar humedad.",
  };
}

function temperatureStatus(t) {
  if (t >= 30) {
    return {
      color: "#ef4444",
      label: "Mucho calor",
      tag: "TEMP",
      msg: "La temperatura es muy alta. Riega fuera del mediodia y protege plantulas jovenes.",
    };
  }
  if (t >= 26) {
    return {
      color: "#f59e0b",
      label: "Calor moderado",
      tag: "TEMP",
      msg: "Hace calor. Vigila perdida de agua y evita riego en horas fuertes de sol.",
    };
  }
  if (t >= 22) {
    return {
      color: "#16a34a",
      label: "Temperatura ideal",
      tag: "TEMP",
      msg: "La temperatura esta en buen rango para el cultivo.",
    };
  }
  if (t >= 18) {
    return {
      color: "#f59e0b",
      label: "Fresco",
      tag: "TEMP",
      msg: "Hace fresco. Observa plantas jovenes y protege si baja mas en la noche.",
    };
  }
  return {
    color: "#ef4444",
    label: "Frio peligroso",
    tag: "TEMP",
    msg: "Hay riesgo de dano por frio. Protege el cultivo durante la noche.",
  };
}

function humidityStatus(h) {
  if (h >= 82) {
    return {
      color: "#ef4444",
      label: "Humedad muy alta",
      tag: "HUMEDAD",
      msg: "Demasiada humedad. Revisa si aparecen manchas o sintomas de hongos.",
    };
  }
  if (h >= 70) {
    return {
      color: "#16a34a",
      label: "Humedad normal",
      tag: "HUMEDAD",
      msg: "La humedad del aire se ve estable.",
    };
  }
  if (h >= 55) {
    return {
      color: "#f59e0b",
      label: "Humedad baja",
      tag: "HUMEDAD",
      msg: "El ambiente esta seco. Revisa humedad del suelo y frecuencia de riego.",
    };
  }
  return {
    color: "#ef4444",
    label: "Aire muy seco",
    tag: "HUMEDAD",
    msg: "Sequedad alta. Riega pronto y protege el suelo para evitar perdida de agua.",
  };
}

function phStatus(ph) {
  if (ph > 7.5) {
    return {
      color: "#ef4444",
      label: "Suelo alcalino",
      tag: "PH",
      msg: "El suelo esta muy alcalino. Revisa correccion del pH con apoyo tecnico.",
    };
  }
  if (ph > 7.0) {
    return {
      color: "#f59e0b",
      label: "Algo alcalino",
      tag: "PH",
      msg: "El pH esta algo alto. Conviene vigilar absorcion de nutrientes.",
    };
  }
  if (ph >= 6.0) {
    return {
      color: "#16a34a",
      label: "Suelo ideal",
      tag: "PH",
      msg: "El pH del suelo esta en un rango favorable.",
    };
  }
  if (ph >= 5.5) {
    return {
      color: "#f59e0b",
      label: "Algo acido",
      tag: "PH",
      msg: "El suelo esta algo acido. Evalua correccion si el cultivo lo necesita.",
    };
  }
  return {
    color: "#ef4444",
    label: "Suelo muy acido",
    tag: "PH",
    msg: "El suelo esta muy acido. Conviene revisar correccion con cal agricola.",
  };
}

const RISK_CONFIG = {
  high: {
    color: "#ef4444",
    bg: "rgba(239,68,68,0.08)",
    border: "rgba(239,68,68,0.2)",
    label: "Riesgo alto",
    msg: "Tu cultivo necesita atencion pronto.",
  },
  medium: {
    color: "#f59e0b",
    bg: "rgba(245,158,11,0.08)",
    border: "rgba(245,158,11,0.2)",
    label: "Riesgo medio",
    msg: "Hay algunas cosas que revisar esta semana.",
  },
  low: {
    color: "#16a34a",
    bg: "rgba(22,163,74,0.08)",
    border: "rgba(22,163,74,0.2)",
    label: "Todo bien",
    msg: "Tu cultivo esta en buenas condiciones.",
  },
};

const NIVEL_BADGE = {
  critica: { bg: "rgba(239,68,68,0.1)", color: "#ef4444", label: "Urgente" },
  advertencia: { bg: "rgba(245,158,11,0.1)", color: "#f59e0b", label: "Esta semana" },
  info: { bg: "rgba(22,163,74,0.08)", color: "#16a34a", label: "General" },
};

function effectiveRisk(predictionRisk, variables) {
  const redCount = variables.filter((v) => v.color === "#ef4444").length;
  const yellowCount = variables.filter((v) => v.color === "#f59e0b").length;
  if (predictionRisk.level === "low") {
    if (redCount >= 2) return { score: predictionRisk.score, level: "high" };
    if (redCount === 1 || yellowCount >= 2) return { score: predictionRisk.score, level: "medium" };
  }
  if (predictionRisk.level === "medium" && redCount >= 2) {
    return { score: predictionRisk.score, level: "high" };
  }
  return predictionRisk;
}

function farmerRiskCopy(level) {
  if (level === "high") {
    return {
      title: "Actua hoy",
      subtitle: "Hay condiciones que pueden danar el cultivo si no se corrigen pronto.",
    };
  }
  if (level === "medium") {
    return {
      title: "Revisa esta semana",
      subtitle: "Hay senales de alerta. Conviene corregir ahora antes de que empeoren.",
    };
  }
  return {
    title: "Condicion estable",
    subtitle: "El cultivo se mantiene en un rango manejable. Sigue observacion normal.",
  };
}

function buildPrioritySummary(variables, labels) {
  const red = [];
  const yellow = [];

  variables.forEach((item, index) => {
    const payload = { ...item, name: labels[index] };
    if (item.color === "#ef4444") red.push(payload);
    if (item.color === "#f59e0b") yellow.push(payload);
  });

  const main =
    red[0] ||
    yellow[0] || {
      color: "#16a34a",
      name: "Sin alertas fuertes",
      label: "En rango",
      msg: "Las metricas principales estan en un rango aceptable.",
    };

  return {
    main,
    reviewNow: red.length > 0 ? red : yellow,
    outOfRangeCount: red.length + yellow.length,
  };
}

export default function Reports({
  selectedEntry,
  predictionRisk,
  analysisReady,
  averageSoilPh,
  cropCoverage,
  riskCounts,
}) {
  const [steps, setSteps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);
  const [exportingPdf, setExportingPdf] = useState(false);
  const reportRef = useRef(null);

  useEffect(() => {
    const id = window.setTimeout(() => setPageLoading(false), 350);
    return () => window.clearTimeout(id);
  }, [selectedEntry]);

  const variables = [
    rainfallStatus(selectedEntry.rainfall),
    temperatureStatus(selectedEntry.temperature),
    humidityStatus(selectedEntry.humidity),
    phStatus(selectedEntry.soilPh),
  ];

  const varLabels = ["Lluvia", "Temperatura", "Humedad", "Suelo"];
  const varValues = [
    `${selectedEntry.rainfall} mm`,
    `${selectedEntry.temperature} C`,
    `${selectedEntry.humidity}%`,
    `pH ${selectedEntry.soilPh}`,
  ];

  const safeRiskCounts = riskCounts || { total: 0, highCount: 0, mediumCount: 0 };
  const risk = effectiveRisk(predictionRisk, variables);
  const rc = RISK_CONFIG[risk.level];
  const farmerRisk = farmerRiskCopy(risk.level);
  const prioritySummary = buildPrioritySummary(variables, varLabels);

  useEffect(() => {
    setLoading(true);
    getRecommendations(selectedEntry.crop, {
      temperatura: selectedEntry.temperature,
      precipitacion: selectedEntry.rainfall,
      humedad: selectedEntry.humidity,
      ph_suelo: selectedEntry.soilPh,
    })
      .then((data) => setSteps(data))
      .catch(() => setSteps([]))
      .finally(() => setLoading(false));
  }, [
    selectedEntry.crop,
    selectedEntry.temperature,
    selectedEntry.rainfall,
    selectedEntry.humidity,
    selectedEntry.soilPh,
  ]);

  if (pageLoading) {
    return (
      <div className="page-content">
        <div className="card">
          <div className="card-body skeleton-panel">
            <div className="skeleton-line wide" />
            <div className="skeleton-line" />
            <div className="skeleton-box" />
          </div>
        </div>
      </div>
    );
  }

  if (!analysisReady || selectedEntry?.pending) {
    return (
      <div className="page-content">
        <div className="card">
          <div className="card-body" style={{ padding: "1.4rem" }}>
            <h3 style={{ margin: "0 0 0.45rem", fontSize: "1.1rem", color: "var(--text-primary)" }}>Aun no hay resultados para mostrar</h3>
            <p style={{ margin: 0, color: "var(--text-secondary)", lineHeight: 1.6 }}>
              Vuelve a Inicio, ingresa las metricas del lote y ejecuta un nuevo analisis para generar el resumen de resultados.
            </p>
          </div>
        </div>
      </div>
    );
  }

  async function exportPdf() {
    if (!reportRef.current || exportingPdf) return;
    setExportingPdf(true);
    try {
      const canvas = await html2canvas(reportRef.current, {
        scale: 2,
        useCORS: true,
        backgroundColor: "#ffffff",
      });
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("p", "mm", "a4");
      const pageW = pdf.internal.pageSize.getWidth();
      const pageH = pdf.internal.pageSize.getHeight();
      const margin = 8;
      const contentW = pageW - margin * 2;
      const contentH = (canvas.height * contentW) / canvas.width;

      if (contentH <= pageH - margin * 2) {
        pdf.addImage(imgData, "PNG", margin, margin, contentW, contentH);
      } else {
        let remaining = contentH;
        let offsetY = 0;
        while (remaining > 0) {
          pdf.addImage(imgData, "PNG", margin, margin - offsetY, contentW, contentH);
          remaining -= pageH - margin * 2;
          offsetY += pageH - margin * 2;
          if (remaining > 0) pdf.addPage();
        }
      }

      const fname = `reporte_agroclima_${selectedEntry.crop}_${selectedEntry.municipality}.pdf`
        .toLowerCase()
        .replace(/\s+/g, "_");
      pdf.save(fname);
    } finally {
      setExportingPdf(false);
    }
  }

  return (
    <div className="page-content" ref={reportRef}>
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "0.2rem" }}>
        <button className="btn primary" onClick={exportPdf} disabled={exportingPdf}>
          {exportingPdf ? "Generando PDF..." : "Descargar reporte PDF"}
        </button>
      </div>

      <div
        style={{
          background: rc.bg,
          border: `1px solid ${rc.border}`,
          borderRadius: 14,
          padding: "1.5rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "1rem",
          flexWrap: "wrap",
        }}
      >
        <div>
          <p
            style={{
              fontSize: "0.78rem",
              fontWeight: 700,
              color: "var(--text-muted)",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              margin: "0 0 0.3rem",
            }}
          >
            Como esta tu cultivo
          </p>
          <h4
            style={{
              margin: "0 0 0.4rem",
              fontSize: "1.4rem",
              fontWeight: 800,
              color: "var(--text-primary)",
            }}
          >
            {selectedEntry.crop} - {selectedEntry.municipality}
          </h4>
          <p
            style={{
              margin: 0,
              fontSize: "0.95rem",
              color: "var(--text-secondary)",
              maxWidth: 520,
            }}
          >
            <strong style={{ color: rc.color }}>{rc.label}.</strong> {rc.msg}
          </p>
          <div style={{ display: "flex", gap: "0.55rem", flexWrap: "wrap", marginTop: "0.9rem" }}>
            <span
              style={{
                fontSize: "0.74rem",
                fontWeight: 800,
                padding: "0.35rem 0.7rem",
                borderRadius: 999,
                background: `${rc.color}12`,
                color: rc.color,
              }}
            >
              {farmerRisk.title}
            </span>
            <span
              style={{
                fontSize: "0.74rem",
                fontWeight: 700,
                padding: "0.35rem 0.7rem",
                borderRadius: 999,
                background: "rgba(15,23,42,0.05)",
                color: "var(--text-secondary)",
              }}
            >
              Problema principal: {prioritySummary.main.name}
            </span>
          </div>
          <p
            style={{
              margin: "0.8rem 0 0",
              fontSize: "0.84rem",
              color: "var(--text-secondary)",
              maxWidth: 560,
            }}
          >
            {farmerRisk.subtitle}
          </p>
        </div>
        <div
          style={{
            minWidth: 180,
            textAlign: "center",
            background: rc.bg,
            border: `2px solid ${rc.border}`,
            borderRadius: 12,
            padding: "0.75rem 1.2rem",
          }}
        >
          <div
            style={{
              fontSize: "0.7rem",
              color: "var(--text-muted)",
              fontWeight: 800,
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
          >
            Resumen rapido
          </div>
          <div style={{ fontSize: "1.55rem", fontWeight: 900, color: rc.color, lineHeight: 1.1, marginTop: "0.35rem" }}>
            {prioritySummary.outOfRangeCount}
          </div>
          <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)", fontWeight: 700, marginTop: 4 }}>
            variables fuera de rango
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Lo mas importante hoy</h3>
          <span className="chip">{prioritySummary.outOfRangeCount} variables a revisar</span>
        </div>
        <div
          className="card-body"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "0.75rem",
          }}
        >
          <div
            style={{
              padding: "0.9rem 1rem",
              borderRadius: 10,
              background: "var(--bg)",
              border: "1px solid var(--border)",
            }}
          >
            <div
              style={{
                fontSize: "0.72rem",
                color: "var(--text-muted)",
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                marginBottom: "0.3rem",
              }}
            >
              Estado del cultivo
            </div>
            <div style={{ fontSize: "1.1rem", fontWeight: 800, color: rc.color }}>{farmerRisk.title}</div>
            <p style={{ margin: "0.4rem 0 0", fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              {farmerRisk.subtitle}
            </p>
          </div>
          <div
            style={{
              padding: "0.9rem 1rem",
              borderRadius: 10,
              background: "var(--bg)",
              border: "1px solid var(--border)",
            }}
          >
            <div
              style={{
                fontSize: "0.72rem",
                color: "var(--text-muted)",
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                marginBottom: "0.3rem",
              }}
            >
              Problema principal
            </div>
            <div style={{ fontSize: "1.1rem", fontWeight: 800, color: prioritySummary.main.color }}>
              {prioritySummary.main.name}
            </div>
            <p style={{ margin: "0.4rem 0 0", fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              {prioritySummary.main.msg}
            </p>
          </div>
          <div
            style={{
              padding: "0.9rem 1rem",
              borderRadius: 10,
              background: "var(--bg)",
              border: "1px solid var(--border)",
            }}
          >
            <div
              style={{
                fontSize: "0.72rem",
                color: "var(--text-muted)",
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                marginBottom: "0.3rem",
              }}
            >
              Revisa primero
            </div>
            {prioritySummary.reviewNow.length > 0 ? (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.45rem" }}>
                {prioritySummary.reviewNow.slice(0, 3).map((item) => (
                  <span
                    key={item.name}
                    style={{
                      fontSize: "0.74rem",
                      fontWeight: 700,
                      padding: "0.32rem 0.6rem",
                      borderRadius: 999,
                      background: `${item.color}12`,
                      color: item.color,
                    }}
                  >
                    {item.name}
                  </span>
                ))}
              </div>
            ) : (
              <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "#16a34a" }}>Sin variables criticas</div>
            )}
            <p style={{ margin: "0.55rem 0 0", fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              Empieza por la variable mas comprometida antes de aplicar acciones generales.
            </p>
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "0.85rem" }}>
        {variables.map((v, i) => (
          <div
            key={varLabels[i]}
            style={{
              background: "var(--surface)",
              border: `1px solid ${v.color}30`,
              borderLeft: `4px solid ${v.color}`,
              borderRadius: 10,
              padding: "1rem",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
              <span
                style={{
                  fontSize: "0.7rem",
                  fontWeight: 800,
                  letterSpacing: "0.08em",
                  color: "var(--text-muted)",
                }}
              >
                {v.tag}
              </span>
              <span
                style={{
                  fontSize: "0.68rem",
                  fontWeight: 700,
                  padding: "0.2rem 0.55rem",
                  borderRadius: 20,
                  background: `${v.color}15`,
                  color: v.color,
                }}
              >
                {v.label}
              </span>
            </div>
            <div style={{ fontWeight: 800, fontSize: "1.25rem", color: "var(--text-primary)", marginBottom: "0.15rem" }}>
              {varValues[i]}
            </div>
            <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: 600, marginBottom: "0.5rem" }}>
              {varLabels[i]}
            </div>
            <p style={{ margin: 0, fontSize: "0.78rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>{v.msg}</p>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Que hacer esta semana</h3>
          <span className="chip">{loading ? "Cargando..." : `${steps.length} recomendaciones`}</span>
        </div>
        <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
          {loading && (
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", textAlign: "center", padding: "1rem 0" }}>
              Consultando base de conocimiento...
            </p>
          )}
          {!loading && steps.length === 0 && (
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", textAlign: "center", padding: "1rem 0" }}>
              No hay recomendaciones disponibles. Verifica que la API este activa.
            </p>
          )}
          {steps.map((step, i) => {
            const nb = NIVEL_BADGE[step.nivel] || NIVEL_BADGE.info;
            return (
              <div
                key={step.id || i}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "0.85rem",
                  padding: "0.85rem 1rem",
                  background: "var(--bg)",
                  border: "1px solid var(--border)",
                  borderLeft: `3px solid ${nb.color}`,
                  borderRadius: 10,
                }}
              >
                <span style={{ fontSize: "0.8rem", flexShrink: 0, marginTop: 4, color: nb.color, fontWeight: 800 }}>
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.3rem", flexWrap: "wrap" }}>
                    <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--text-primary)" }}>{step.titulo}</span>
                    <span
                      style={{
                        fontSize: "0.63rem",
                        fontWeight: 700,
                        padding: "0.15rem 0.45rem",
                        borderRadius: 20,
                        background: nb.bg,
                        color: nb.color,
                        flexShrink: 0,
                      }}
                    >
                      {nb.label}
                    </span>
                  </div>
                  <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                    {step.recomendacion}
                  </p>
                  {step.fuente && (
                    <span style={{ fontSize: "0.65rem", color: "var(--text-muted)", marginTop: "0.3rem", display: "block" }}>
                      Fuente: {step.fuente}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.85rem" }}>
        <div className="card">
          <div className="card-header" style={{ borderBottom: "1px solid var(--border)" }}>
            <h3>Decision de campo</h3>
          </div>
          <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
            {[
              { label: "Que hacer", value: farmerRisk.title },
              { label: "Revisar primero", value: prioritySummary.main.name },
              {
                label: "Prioridad",
                value: safeRiskCounts.highCount > 0
                  ? "Atender hoy"
                  : safeRiskCounts.mediumCount > 0
                    ? "Revisar esta semana"
                    : "Seguir observando",
              },
            ].map((row) => (
              <div
                key={row.label}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "0.55rem 0",
                  borderBottom: "1px solid var(--border)",
                  gap: "0.75rem",
                }}
              >
                <span style={{ fontSize: "0.83rem", color: "var(--text-secondary)" }}>{row.label}</span>
                <span style={{ fontWeight: 800, fontSize: "1rem", color: "var(--text-primary)", textAlign: "right" }}>
                  {row.value}
                </span>
              </div>
            ))}
            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.5, marginTop: "0.25rem" }}>
              {farmerRisk.subtitle}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header" style={{ borderBottom: "1px solid var(--border)" }}>
            <h3>Cuando llamar a un tecnico</h3>
          </div>
          <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: "0.65rem" }}>
            {[
              { texto: "Manchas nuevas en hojas o tallos", urgencia: "Hoy" },
              { texto: "Plantas marchitas aunque el suelo este humedo", urgencia: "Hoy" },
              { texto: "El cultivo no mejora despues de corregir riego o drenaje", urgencia: "Esta semana" },
            ].map((item, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.6rem",
                  fontSize: "0.82rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.4,
                }}
              >
                <span style={{ flexShrink: 0, color: "var(--text-muted)" }}>•</span>
                <span style={{ flex: 1 }}>{item.texto}</span>
                <span
                  style={{
                    fontSize: "0.65rem",
                    fontWeight: 700,
                    flexShrink: 0,
                    padding: "0.15rem 0.45rem",
                    borderRadius: 20,
                    background:
                      item.urgencia === "Hoy"
                        ? "rgba(239,68,68,0.1)"
                        : item.urgencia === "Esta semana"
                          ? "rgba(245,158,11,0.1)"
                          : "rgba(22,163,74,0.1)",
                    color:
                      item.urgencia === "Hoy"
                        ? "#ef4444"
                        : item.urgencia === "Esta semana"
                          ? "#f59e0b"
                          : "#16a34a",
                  }}
                >
                  {item.urgencia}
                </span>
              </div>
            ))}
            <div
              style={{
                marginTop: "0.5rem",
                padding: "0.65rem 0.85rem",
                background: "rgba(37,99,235,0.06)",
                border: "1px solid rgba(37,99,235,0.15)",
                borderRadius: 8,
                fontSize: "0.78rem",
                color: "#2563eb",
                fontWeight: 600,
              }}
            >
              MAGA 1548 - llamada gratis
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
