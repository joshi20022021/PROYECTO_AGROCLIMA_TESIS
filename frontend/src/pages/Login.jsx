import { useState } from "react";

// Credenciales admin hardcodeadas
const ADMIN_USER = "admin";
const ADMIN_PASS = "agroclima2024";

export default function Login({ onLogin }) {
  const [user, setUser]     = useState("");
  const [pass, setPass]     = useState("");
  const [error, setError]   = useState("");
  const [loading, setLoading] = useState(false);

  function handleAdmin(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    setTimeout(() => {
      if (user.trim() === ADMIN_USER && pass.trim() === ADMIN_PASS) {
        onLogin("admin");
      } else {
        setError("Credenciales incorrectas.");
      }
      setLoading(false);
    }, 400);
  }

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #0b1120 0%, #1a2540 60%, #0d2213 100%)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontFamily: "Manrope, Inter, sans-serif",
      padding: "1rem",
    }}>
      <div style={{ width: "100%", maxWidth: 420 }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <h1 style={{ color: "#fff", fontSize: "1.8rem", fontWeight: 800, margin: 0, letterSpacing: "-0.04em" }}>
            AgroClima GT
          </h1>
          <p style={{ color: "rgba(255,255,255,0.5)", fontSize: "0.85rem", margin: "0.3rem 0 0" }}>
            Sistema de monitoreo agroclimatico
          </p>
        </div>

        {/* User access card */}
        <div style={{
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.08)",
          borderRadius: 16,
          padding: "1.5rem",
          marginBottom: "1rem",
        }}>
          <p style={{ color: "rgba(255,255,255,0.7)", fontSize: "0.82rem", margin: "0 0 1rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Acceso de usuario
          </p>
          <button
            onClick={() => onLogin("user")}
            style={{
              width: "100%",
              padding: "0.85rem",
              background: "linear-gradient(135deg, #16a34a, #15803d)",
              border: "none",
              borderRadius: 10,
              color: "#fff",
              fontWeight: 700,
              fontSize: "0.95rem",
              cursor: "pointer",
              fontFamily: "inherit",
              letterSpacing: "0.01em",
            }}
          >
            Ingresar al panel de usuario
          </button>
          <p style={{ color: "rgba(255,255,255,0.35)", fontSize: "0.72rem", textAlign: "center", margin: "0.75rem 0 0" }}>
            Acceso sin credenciales — visualizacion y analisis
          </p>
        </div>

        {/* Admin access card */}
        <div style={{
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.08)",
          borderRadius: 16,
          padding: "1.5rem",
        }}>
          <p style={{ color: "rgba(255,255,255,0.7)", fontSize: "0.82rem", margin: "0 0 1rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Acceso de administrador
          </p>
          <form onSubmit={handleAdmin}>
            <div style={{ marginBottom: "0.75rem" }}>
              <input
                type="text"
                placeholder="Usuario"
                value={user}
                onChange={(e) => setUser(e.target.value)}
                autoComplete="off"
                style={{
                  width: "100%",
                  padding: "0.75rem 0.9rem",
                  background: "rgba(255,255,255,0.07)",
                  border: "1px solid rgba(255,255,255,0.12)",
                  borderRadius: 8,
                  color: "#fff",
                  fontSize: "0.9rem",
                  fontFamily: "inherit",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>
            <div style={{ marginBottom: "0.9rem" }}>
              <input
                type="password"
                placeholder="Contrasena"
                value={pass}
                onChange={(e) => setPass(e.target.value)}
                autoComplete="new-password"
                style={{
                  width: "100%",
                  padding: "0.75rem 0.9rem",
                  background: "rgba(255,255,255,0.07)",
                  border: "1px solid rgba(255,255,255,0.12)",
                  borderRadius: 8,
                  color: "#fff",
                  fontSize: "0.9rem",
                  fontFamily: "inherit",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>
            {error && (
              <p style={{ color: "#f87171", fontSize: "0.78rem", margin: "0 0 0.75rem", textAlign: "center" }}>
                {error}
              </p>
            )}
            <button
              type="submit"
              disabled={loading}
              style={{
                width: "100%",
                padding: "0.85rem",
                background: loading ? "rgba(255,255,255,0.1)" : "linear-gradient(135deg, #1d4ed8, #1e40af)",
                border: "none",
                borderRadius: 10,
                color: "#fff",
                fontWeight: 700,
                fontSize: "0.95rem",
                cursor: loading ? "not-allowed" : "pointer",
                fontFamily: "inherit",
                opacity: loading ? 0.7 : 1,
              }}
            >
              {loading ? "Verificando..." : "Ingresar como administrador"}
            </button>
          </form>
        </div>

        <p style={{ color: "rgba(255,255,255,0.2)", fontSize: "0.7rem", textAlign: "center", marginTop: "1.5rem" }}>
          AgroClima GT — Prototipo de tesis USAC 2025
        </p>
      </div>
    </div>
  );
}
