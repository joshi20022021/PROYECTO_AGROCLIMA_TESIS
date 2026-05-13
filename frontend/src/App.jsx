import { useEffect, useMemo, useState } from "react";
import "./App.css";

// ── Paneles de usuario ─────────────────────────────────────────────────────
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Dataset from "./pages/Dataset";
import Alerts from "./pages/Alerts";
import Reports from "./pages/Reports";
import Arduino from "./pages/Arduino";
import Forecast from "./pages/Forecast";
import RiskMap from "./pages/RiskMap";

// ── Panel de administrador ─────────────────────────────────────────────────
import Login from "./pages/Login";
import AdminSidebar, { adminSections } from "./components/AdminSidebar";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminModels    from "./pages/Models";          // mismo componente
import AdminPredictions from "./pages/admin/AdminPredictions";
import AdminReadings    from "./pages/admin/AdminReadings";
import AdminDatasets    from "./pages/admin/AdminDatasets";

import { sections, initialDataset, initialTrendSeries, defaultForm, municipioOptions, TRAINED_CROPS } from "./data/constants";
import { calculateRisk, buildAlerts, clamp, getRecommendation, getAverageRiskByCrop } from "./utils/riskUtils";
import { predictYield, getForecast, getMetrics } from "./services/api";

const EMPTY_ANALYSIS = {
  municipality: defaultForm.municipality,
  crop: defaultForm.crop,
  rainfall: null,
  temperature: null,
  humidity: null,
  soilPh: null,
  pending: true,
};

function csvEscape(value) {
  if (value == null) return "";
  const text = String(value);
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, "\"\"")}"`;
  }
  return text;
}

function normalizeField(value, min, max, fallback) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return fallback;
  return clamp(numeric, min, max);
}

function SessionPopup({ mode, role, user }) {
  const isAdmin = role === "admin";
  const isLogin = mode === "login";
  const title = isLogin
    ? isAdmin ? "Bienvenido administrador" : "Bienvenido usuario"
    : isAdmin ? "Cerrando sesion de administrador" : "Cerrando sesion de usuario";
  const subtitle = isLogin
    ? isAdmin
      ? "Preparando el panel de administracion."
      : `Preparando tu dashboard${user?.nombre ? `, ${user.nombre}` : ""}.`
    : "Regresando al acceso principal.";
  const kicker = isLogin ? "Acceso concedido" : "Sesion finalizada";

  return (
    <div className="welcome-popup-backdrop" role="alertdialog" aria-modal="true" aria-label={title}>
      <div className={`welcome-popup-card ${isAdmin ? "admin" : "user"}`}>
        <div className="welcome-popup-orb" />
        <div className="welcome-popup-icon">{isLogin ? (isAdmin ? "AD" : "US") : "BY"}</div>
        <p className="welcome-popup-kicker">{kicker}</p>
        <h2>{title}</h2>
        <p>{subtitle}</p>
        <div className="welcome-popup-loader" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
      </div>
    </div>
  );
}

// ── Panel de usuario ───────────────────────────────────────────────────────

function ThemeToggle({ theme, onToggle }) {
  return (
    <button className="btn ghost icon-only" onClick={onToggle} aria-label="Cambiar modo claro u oscuro" title="Modo claro/oscuro">
      {theme === "dark" ? "☀" : "☾"}
    </button>
  );
}

function UserApp({ onLogout, userEmail, theme, onToggleTheme }) {
  const [activeSection, setActiveSection] = useState("dashboard");
  const [dataset, setDataset]             = useState(initialDataset);
  const [trendSeries, setTrendSeries]     = useState(initialTrendSeries);
  const [form, setForm]                   = useState(defaultForm);
  const [selectedEntry, setSelectedEntry] = useState(initialDataset[0]);
  const [toast, setToast]                 = useState("");
  const [yieldResult, setYieldResult]     = useState(null);
  const [analysisReady, setAnalysisReady] = useState(true);
  const [submitting, setSubmitting]       = useState(false);  // ← evita clicks múltiples
  const [apiOnline, setApiOnline]         = useState(false);
  const [menuOpen, setMenuOpen]           = useState(false);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [weatherSource, setWeatherSource] = useState("");

  useEffect(() => {
    getMetrics()
      .then((metrics) => {
        setApiOnline(true);
        const first = metrics.find((m) => municipioOptions.includes(m.municipio)) ?? metrics[0];
        if (first) {
          setForm((prev) => ({
            ...prev,
            municipality: municipioOptions.includes(first.municipio)
              ? first.municipio
              : municipioOptions[0],
            temperature:  Math.round(first.temperature * 10) / 10,
            rainfall:     Math.round(first.rainfall * 10) / 10,
            humidity:     Math.round(first.humidity * 10) / 10,
          }));
        }
        showToast("Datos ERA5-Land cargados desde el servidor.");
      })
      .catch(() => setApiOnline(false));
  }, []);

  useEffect(() => {
    if (!toast) return;
    const id = window.setTimeout(() => setToast(""), 2200);
    return () => window.clearTimeout(id);
  }, [toast]);

  useEffect(() => {
    let cancelled = false;

    async function syncDepartmentWeather() {
      if (!form.municipality) return;
      setWeatherLoading(true);

      try {
        const forecast = await getForecast(form.municipality);
        if (cancelled) return;

        const totalRain    = Math.round(normalizeField(forecast?.summary?.total_rain_mm ?? 0, 0, 600, 0) * 10) / 10;
        const avgTmax      = Number(forecast?.summary?.avg_tmax ?? 0);
        const avgTmin      = Number(forecast?.summary?.avg_tmin ?? 0);
        const avgTemp      = Math.round(normalizeField((avgTmax + avgTmin) / 2, 5, 45, 22) * 10) / 10;
        const firstHumidity = Math.round(normalizeField(forecast?.days?.[0]?.humidity ?? form.humidity, 5, 100, 70) * 10) / 10;

        setForm((prev) => {
          if (prev.municipality !== form.municipality) return prev;
          return {
            ...prev,
            rainfall: totalRain,
            temperature: avgTemp,
            humidity: firstHumidity,
          };
        });

        setWeatherSource(`Open-Meteo · ${form.municipality}`);
      } catch {
        if (!cancelled) setWeatherSource("");
      } finally {
        if (!cancelled) setWeatherLoading(false);
      }
    }

    syncDepartmentWeather();
    return () => {
      cancelled = true;
    };
  }, [form.municipality]);

  // Auto-ejecutar predicción al navegar a Resultados si aún no hay yieldResult
  useEffect(() => {
    if (activeSection !== "reports" || yieldResult || !apiOnline || submitting || !analysisReady) return;
    // Sincronizar selectedEntry con el formulario actual antes de predecir
    const entry = {
      municipality: form.municipality,
      crop:         form.crop,
      rainfall:     normalizeField(form.rainfall, 0, 600, 0),
      temperature:  normalizeField(form.temperature, 5, 45, 22),
      humidity:     normalizeField(form.humidity, 5, 100, 70),
      soilPh:       normalizeField(form.soilPh, 3.5, 9.5, 6),
      timestamp:    new Date().toISOString(),
    };
    setSelectedEntry(entry);
    setSubmitting(true);
    predictYield({
      municipio:    entry.municipality,
      crop:         entry.crop,
      month:        new Date().getMonth() + 1,
      temperature:  entry.temperature,
      rainfall:     entry.rainfall,
      humidity:     entry.humidity,
      soilPh:       entry.soilPh,
      greennessIdx: form.leafCondition ?? 65,
      cropKnown:    TRAINED_CROPS.includes(entry.crop),
    })
      .then((result) => {
        setYieldResult(result);
        setSelectedEntry((prev) => ({ ...prev, yieldPct: result.yield_pct, yieldLevel: result.yield_level }));
      })
      .catch(() => {})
      .finally(() => setSubmitting(false));
  }, [activeSection]); // eslint-disable-line react-hooks/exhaustive-deps

  const alerts         = useMemo(() => buildAlerts(dataset), [dataset]);
  const cropCoverage   = useMemo(() => new Set(dataset.map((e) => e.crop)).size, [dataset]);
  const avgRisk        = useMemo(() => getAverageRiskByCrop(dataset), [dataset]);
  const predictionRisk = useMemo(() => {
    if (!analysisReady || selectedEntry?.pending) {
      return {
        score: 0,
        level: "low",
        mlScore: null,
        formulaScore: 0,
        anomalyLabel: null,
        combination: "pending",
        source: "pending",
      };
    }

    const formulaRisk = calculateRisk(selectedEntry);

    if (yieldResult) {
      const mlScore = Math.round(clamp(100 - yieldResult.yield_pct, 0, 100));
      const hasHardAlert = yieldResult.anomaly?.is_anomaly || formulaRisk.level === "high";
      const weightedScore = Math.round((mlScore * 0.6) + (formulaRisk.score * 0.4));
      const score = hasHardAlert ? Math.max(mlScore, formulaRisk.score) : weightedScore;
      const level = score >= 55 ? "high" : score <= 18 ? "low" : "medium";
      return {
        score,
        level,
        mlScore,
        formulaScore: formulaRisk.score,
        anomalyLabel: yieldResult.anomaly?.label ?? null,
        combination: hasHardAlert ? "max_guardrail" : "weighted_60_40",
        source: "combined",
      };
    }

    return {
      ...formulaRisk,
      mlScore: null,
      formulaScore: formulaRisk.score,
      anomalyLabel: null,
      combination: "rules_only",
      source: "rules",
    };
  }, [analysisReady, selectedEntry, yieldResult]);
  const averageSoilPh  = useMemo(
    () => (dataset.reduce((s, e) => s + e.soilPh, 0) / dataset.length).toFixed(1),
    [dataset],
  );
  const riskCounts = useMemo(() => {
    const highCount   = alerts.filter((a) => a.level === "high").length;
    const mediumCount = alerts.filter((a) => a.level === "medium").length;
    return { total: highCount + mediumCount, highCount, mediumCount };
  }, [alerts]);

  function showToast(msg) { setToast(msg); }

  function updateForm(e) {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: ["rainfall","temperature","humidity","soilPh"].includes(name) ? Number(value) : value,
    }));
  }

  async function submitForm(e) {
    e.preventDefault();
    if (submitting) return;          // ← bloquea clicks repetidos
    setAnalysisReady(true);
    setSubmitting(true);
    const entry = {
      municipality: form.municipality,
      crop:         form.crop,
      rainfall:     normalizeField(form.rainfall, 0, 600, 0),
      temperature:  normalizeField(form.temperature, 5, 45, 22),
      humidity:     normalizeField(form.humidity, 5, 100, 70),
      soilPh:       normalizeField(form.soilPh, 3.5, 9.5, 6),
      timestamp:    new Date().toISOString(),
    };
    setDataset((prev) => [entry, ...prev].slice(0, 8));
    setTrendSeries((prev) => ({
      ...prev,
      rainfall:    [...prev.rainfall.slice(1),    entry.rainfall],
      temperature: [...prev.temperature.slice(1), entry.temperature],
      humidity:    [...prev.humidity.slice(1),     entry.humidity],
    }));
    setSelectedEntry(entry);

    if (apiOnline) {
      try {
        const result = await predictYield({
          municipio:    entry.municipality,
          crop:         entry.crop,
          month:        new Date().getMonth() + 1,
          temperature:  entry.temperature,
          rainfall:     entry.rainfall,
          humidity:     entry.humidity,
          soilPh:       entry.soilPh,
          greennessIdx: form.leafCondition ?? 65,
          cropKnown:    TRAINED_CROPS.includes(entry.crop),
        });
        setYieldResult(result);
        setDataset((prev) => prev.map((item, index) => (
          index === 0 && item.timestamp === entry.timestamp
            ? { ...item, yieldPct: result.yield_pct, yieldLevel: result.yield_level }
            : item
        )));
        showToast(`Rendimiento estimado: ${result.yield_pct}% — ${entry.crop} en ${entry.municipality}.`);
      } catch {
        setYieldResult(null);
        showToast(`Analisis actualizado — ${entry.crop} en ${entry.municipality}.`);
      }
    } else {
      setYieldResult(null);
      showToast(`Analisis actualizado — ${entry.crop} en ${entry.municipality}.`);
    }
    setSubmitting(false);
  }

  function resetAnalysis() {
    setForm(defaultForm);
    setSelectedEntry(EMPTY_ANALYSIS);
    setYieldResult(null);
    setAnalysisReady(false);
    setWeatherSource("");
    setActiveSection("dashboard");
    showToast("Nuevo analisis listo. Ingresa metricas para evaluar el cultivo.");
  }

  function exportDataset() {
    const exportedAt = new Date().toISOString();
    const headers = [
      "municipio",
      "cultivo",
      "temperatura_c",
      "lluvia_mm",
      "humedad_pct",
      "ph_suelo",
      "riesgo_score",
      "riesgo_nivel",
      "fuente_riesgo",
      "recomendacion",
      "fecha_exportacion",
    ];
    const rows = dataset.map((entry) => {
      const risk = calculateRisk(entry);
      return [
        entry.municipality,
        entry.crop,
        entry.temperature,
        entry.rainfall,
        entry.humidity,
        entry.soilPh,
        risk.score,
        risk.level,
        "reglas_agronomicas_locales",
        getRecommendation(entry, risk),
        exportedAt,
      ];
    });
    const csv  = [headers, ...rows].map((r) => r.map(csvEscape).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement("a"), { href: url, download: `agroclima_export_${new Date().toISOString().slice(0,10)}.csv` });
    a.click();
    URL.revokeObjectURL(url);
    showToast(`Dataset exportado: ${dataset.length} registros.`);
  }

  const pages = {
    dashboard: (
      <Dashboard
        form={form} selectedEntry={selectedEntry} predictionRisk={predictionRisk}
        trendSeries={trendSeries} avgRisk={avgRisk} yieldResult={yieldResult}
        analysisReady={analysisReady}
        apiOnline={apiOnline} updateForm={updateForm} submitForm={submitForm}
        submitting={submitting}
        weatherLoading={weatherLoading}
        weatherSource={weatherSource}
      />
    ),
    dataset: <Dataset dataset={dataset} />,
    risk_map: <RiskMap selectedCrop={form.crop} />,
    alerts:  <Alerts alerts={alerts} dataset={dataset} showToast={showToast} setActiveSection={setActiveSection} />,
    reports: (
      <Reports
        selectedEntry={selectedEntry} predictionRisk={predictionRisk}
        analysisReady={analysisReady}
        yieldResult={yieldResult}
        averageSoilPh={averageSoilPh} cropCoverage={cropCoverage} riskCounts={riskCounts}
      />
    ),
    forecast: <Forecast form={form} />,
    arduino: <Arduino />,
  };

  return (
    <>
      <div className={`sidebar-overlay ${menuOpen ? "show" : ""}`} onClick={() => setMenuOpen(false)} />
      <div className="app-shell">
        <Sidebar
          activeSection={activeSection}
          onNavigate={(s) => { setActiveSection(s); setMenuOpen(false); }}
          isOpen={menuOpen}
          onClose={() => setMenuOpen(false)}
          onLogout={onLogout}
        />
        <div className="main-content">
          <header className="topbar">
            <button className="hamburger" onClick={() => setMenuOpen(true)} aria-label="Abrir menú">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <line x1="3" y1="6"  x2="21" y2="6" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
            <div className="topbar-left">
              <h2>{sections[activeSection].title}</h2>
              <p>{sections[activeSection].subtitle}</p>
            </div>
            <div className="topbar-actions">
              <span className={`chip ${apiOnline ? "" : "orange"}`}>{apiOnline ? "API activa" : "Modo local"}</span>
              <ThemeToggle theme={theme} onToggle={onToggleTheme} />
              <button className="btn ghost" onClick={exportDataset}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                <span className="btn-label-hide">Exportar CSV</span>
              </button>
              <button className="btn primary" onClick={resetAnalysis}>Nuevo analisis</button>
            </div>
          </header>

          {pages[activeSection]}
        </div>
      </div>
      <div className={`toast ${toast ? "show" : ""}`} role="status" aria-live="polite">{toast}</div>
    </>
  );
}

// ── Panel de administrador ─────────────────────────────────────────────────

function AdminApp({ onLogout, theme, onToggleTheme }) {
  const [activeSection, setActiveSection] = useState("admin_dashboard");
  const [menuOpen, setMenuOpen]           = useState(false);

  const adminPages = {
    admin_dashboard:   <AdminDashboard />,
    admin_models:      <AdminModels />,
    admin_predictions: <AdminPredictions />,
    admin_readings:    <AdminReadings />,
    admin_dataset:     <AdminDatasets />,
  };

  return (
    <div className="admin-theme">
      <div className={`sidebar-overlay ${menuOpen ? "show" : ""}`} onClick={() => setMenuOpen(false)} />
      <div className="app-shell">
        <AdminSidebar
          activeSection={activeSection}
          onNavigate={(s) => { setActiveSection(s); setMenuOpen(false); }}
          onLogout={onLogout}
          isOpen={menuOpen}
          onClose={() => setMenuOpen(false)}
        />
        <div className="main-content">
          <header className="topbar">
            <button className="hamburger" onClick={() => setMenuOpen(true)} aria-label="Abrir menú">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <line x1="3" y1="6"  x2="21" y2="6" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
            <div className="topbar-left">
              <h2>{adminSections[activeSection]?.title}</h2>
              <p>{adminSections[activeSection]?.subtitle}</p>
            </div>
            <div className="topbar-actions">
              <span className="chip green">Admin</span>
              <ThemeToggle theme={theme} onToggle={onToggleTheme} />
              <button className="btn ghost" onClick={onLogout} style={{ fontSize: "0.78rem" }}>
                Cerrar sesion
              </button>
            </div>
          </header>
          {adminPages[activeSection]}
        </div>
      </div>
    </div>
  );
}

// ── Raiz ───────────────────────────────────────────────────────────────────

export default function App() {
  const [role, setRole] = useState(() => sessionStorage.getItem("role") || null);
  const [email, setEmail] = useState(() => sessionStorage.getItem("email") || null);
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "light");
  const [sessionTransition, setSessionTransition] = useState(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("theme", theme);
  }, [theme]);

  function toggleTheme() {
    setTheme((prev) => prev === "dark" ? "light" : "dark");
  }

  useEffect(() => {
    if (!sessionTransition) return undefined;

    const timer = window.setTimeout(() => {
      if (sessionTransition.mode === "login") {
        const { role: nextRole, user } = sessionTransition;
        sessionStorage.setItem("role", nextRole);
        if (user?.email) {
          sessionStorage.setItem("email", user.email);
          setEmail(user.email);
        }
        setRole(nextRole);
      } else {
        sessionStorage.removeItem("role");
        sessionStorage.removeItem("email");
        setRole(null);
        setEmail(null);
      }
      setSessionTransition(null);
    }, 1900);

    return () => window.clearTimeout(timer);
  }, [sessionTransition]);

  function handleLogin(r, userObject) {
    setSessionTransition({ mode: "login", role: r, user: userObject });
  }

  function handleLogout() {
    setSessionTransition({
      mode: "logout",
      role,
      user: email ? { email } : null,
    });
  }

  if (!role) {
    return (
      <>
        <Login onLogin={handleLogin} theme={theme} onToggleTheme={toggleTheme} />
        {sessionTransition && (
          <SessionPopup
            mode={sessionTransition.mode}
            role={sessionTransition.role}
            user={sessionTransition.user}
          />
        )}
      </>
    );
  }

  return (
    <>
      {role === "admin" ? (
        <AdminApp onLogout={handleLogout} theme={theme} onToggleTheme={toggleTheme} />
      ) : (
        <UserApp onLogout={handleLogout} userEmail={email} theme={theme} onToggleTheme={toggleTheme} />
      )}
      {sessionTransition && (
        <SessionPopup
          mode={sessionTransition.mode}
          role={sessionTransition.role}
          user={sessionTransition.user}
        />
      )}
    </>
  );
}
