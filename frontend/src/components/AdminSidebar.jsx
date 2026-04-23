const adminNavIcons = {
  admin_dashboard: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
      <rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>
    </svg>
  ),
  admin_models: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
    </svg>
  ),
  admin_predictions: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
    </svg>
  ),
  admin_readings: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="7" width="20" height="14" rx="2"/>
      <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>
      <line x1="12" y1="12" x2="12" y2="16"/><line x1="10" y1="14" x2="14" y2="14"/>
    </svg>
  ),
  admin_dataset: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>
    </svg>
  ),
};

export const adminSections = {
  admin_dashboard:   { label: "Dashboard Admin",    title: "Panel de Administracion",   subtitle: "Estado del sistema, base de datos y actividad reciente." },
  admin_models:      { label: "Modelos ML",          title: "Modelos de Machine Learning", subtitle: "Metricas reales del modelo XGBoost entrenado con datos ERA5 y NASA POWER." },
  admin_predictions: { label: "Historial Predicciones", title: "Historial de Predicciones", subtitle: "Todas las predicciones registradas en la base de datos PostgreSQL." },
  admin_readings:    { label: "Lecturas Arduino",    title: "Lecturas de Sensores",      subtitle: "Registro historico de lecturas del dispositivo Arduino." },
  admin_dataset:     { label: "Datasets",            title: "Gestion de Datasets",       subtitle: "Archivos de entrenamiento, fuentes de datos y estadisticas del corpus." },
};

export default function AdminSidebar({ activeSection, onNavigate, onLogout, isOpen, onClose }) {
  return (
    <aside className={`sidebar ${isOpen ? "mobile-open" : ""}`} style={{ background: "#1a0a2e", borderRight: "1px solid rgba(124,58,237,0.2)" }}>
      <div className="brand">
        <div className="brand-icon">AD</div>
        <div className="brand-text">
          <h1 style={{ color: "#e9d5ff" }}>AgroClima GT</h1>
          <p style={{ color: "rgba(233,213,255,0.55)" }}>Panel Administrador</p>
        </div>
        <button className="sidebar-close" onClick={onClose} aria-label="Cerrar menú">✕</button>
      </div>

      <nav className="nav-section" aria-label="Navegacion admin">
        <p className="nav-label" style={{ color: "rgba(233,213,255,0.4)" }}>Administracion</p>
        <div className="menu">
          {Object.entries(adminSections).map(([key, section]) => (
            <button
              key={key}
              className={`menu-item ${activeSection === key ? "active" : ""}`}
              onClick={() => onNavigate(key)}
              style={activeSection === key ? {} : { color: "rgba(233,213,255,0.7)" }}
            >
              <span className="menu-icon">{adminNavIcons[key]}</span>
              {section.label}
            </button>
          ))}
        </div>
      </nav>

      <div className="sidebar-footer">
        <div style={{
          background: "rgba(124,58,237,0.12)",
          border: "1px solid rgba(124,58,237,0.25)",
          borderRadius: 8,
          padding: "0.6rem 0.8rem",
          marginBottom: "0.75rem",
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
        }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#a78bfa", flexShrink: 0 }} />
          <span style={{ fontSize: "0.75rem", color: "#c4b5fd", fontWeight: 600 }}>admin</span>
          <span style={{ fontSize: "0.7rem", color: "rgba(196,181,253,0.5)", marginLeft: "auto" }}>Sesion activa</span>
        </div>
        <button
          onClick={onLogout}
          style={{
            width: "100%",
            padding: "0.55rem",
            background: "rgba(239,68,68,0.1)",
            border: "1px solid rgba(239,68,68,0.25)",
            borderRadius: 8,
            color: "#fca5a5",
            fontSize: "0.78rem",
            fontWeight: 600,
            cursor: "pointer",
            fontFamily: "inherit",
          }}
        >
          Cerrar sesion
        </button>
      </div>
    </aside>
  );
}
