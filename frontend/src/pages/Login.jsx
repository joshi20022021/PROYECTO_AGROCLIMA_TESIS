import { useState } from "react";

const ADMIN_USER = "admin";
const ADMIN_PASS = "agroclima2024";

function ArrowIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
    </svg>
  );
}

export default function Login({ onLogin, theme = "light", onToggleTheme }) {
  const [user, setUser]       = useState("");
  const [pass, setPass]       = useState("");
  const [error, setError]     = useState("");
  const [loading, setLoading] = useState(false);
  const [focusUser, setFocusUser] = useState(false);
  const [focusPass, setFocusPass] = useState(false);

  const dk = theme === "dark";

  function handleAdmin(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    setTimeout(() => {
      if (user.trim() === ADMIN_USER && pass.trim() === ADMIN_PASS) {
        onLogin("admin");
      } else {
        setError("Credenciales incorrectas. Verifica usuario y contraseña.");
      }
      setLoading(false);
    }, 500);
  }

  /* ── paletas ── */
  const bg = dk
    ? "linear-gradient(135deg, #020814 0%, #061734 45%, #030e1e 100%)"
    : "linear-gradient(135deg, #f0f7ff 0%, #e8f4ff 45%, #f5fbff 100%)";

  const gridColor = dk
    ? "rgba(96,165,250,0.04)"
    : "rgba(37,99,235,0.05)";

  const cardUser = {
    background : dk ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.92)",
    border     : dk ? "1px solid rgba(76,175,114,0.22)" : "1px solid rgba(76,175,114,0.30)",
    boxShadow  : dk ? "none" : "0 2px 18px rgba(0,0,0,0.07)",
  };

  const cardAdmin = {
    background : dk ? "rgba(255,255,255,0.035)" : "rgba(255,255,255,0.92)",
    border     : dk ? "1px solid rgba(96,165,250,0.18)" : "1px solid rgba(37,99,235,0.20)",
    boxShadow  : dk ? "none" : "0 2px 18px rgba(0,0,0,0.07)",
  };

  const textSecondary = dk ? "rgba(255,255,255,0.55)" : "#475569";
  const textMuted     = dk ? "rgba(255,255,255,0.28)" : "#94a3b8";

  const inputBg      = (focus) => dk
    ? (focus ? "rgba(255,255,255,0.09)" : "rgba(255,255,255,0.06)")
    : (focus ? "#f0f7ff" : "#f8faff");
  const inputBorder  = (focus) => dk
    ? (focus ? "rgba(96,165,250,0.5)" : "rgba(255,255,255,0.12)")
    : (focus ? "#2563eb" : "#cbd5e1");
  const inputColor   = dk ? "#fff" : "#0f172a";
  const inputShadow  = (focus) => focus
    ? "0 0 0 3px rgba(37,99,235,0.14)"
    : "none";

  const toggleBtn = {
    border     : dk ? "1px solid rgba(255,255,255,0.16)" : "1px solid #cbd5e1",
    background : dk ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.85)",
    color      : dk ? "#fff" : "#334155",
    boxShadow  : dk ? "none" : "0 1px 4px rgba(0,0,0,0.08)",
  };

  const logoFilter = dk
    ? "brightness(1.08) contrast(1.12) saturate(1.18) drop-shadow(0 18px 42px rgba(0,0,0,0.55))"
    : "drop-shadow(0 6px 18px rgba(0,0,0,0.12))";

  const footerColor = dk ? "rgba(255,255,255,0.18)" : "#94a3b8";

  return (
    <div style={{
      minHeight: "100vh",
      background: bg,
      display: "flex", alignItems: "center", justifyContent: "center",
      fontFamily: '"Inter","DM Sans",system-ui,sans-serif',
      padding: "1.5rem", position: "relative", overflow: "hidden",
    }}>
      {/* Cuadrícula decorativa */}
      <div style={{
        position: "absolute", inset: 0,
        backgroundImage: `linear-gradient(${gridColor} 1px, transparent 1px), linear-gradient(90deg, ${gridColor} 1px, transparent 1px)`,
        backgroundSize: "48px 48px", pointerEvents: "none",
      }} />

      {/* Orbes suaves */}
      {[
        { top:"-18%", left:"-12%", size:"56vw", color: dk ? "rgba(34,197,94,0.10)" : "rgba(37,99,235,0.07)" },
        { bottom:"-18%", right:"-12%", size:"60vw", color: dk ? "rgba(59,130,246,0.09)" : "rgba(16,185,129,0.06)" },
      ].map((o, i) => (
        <div key={i} style={{
          position: "absolute", top: o.top, left: o.left, right: o.right, bottom: o.bottom,
          width: o.size, height: o.size, borderRadius: "50%",
          background: `radial-gradient(circle, ${o.color} 0%, transparent 65%)`,
          pointerEvents: "none",
        }} />
      ))}

      {/* Botón modo oscuro/claro */}
      <button
        onClick={onToggleTheme}
        aria-label="Cambiar modo claro u oscuro"
        title="Modo claro/oscuro"
        style={{
          position: "absolute", top: "1rem", right: "1rem", zIndex: 2,
          width: 40, height: 40, borderRadius: 10,
          cursor: "pointer", fontWeight: 800, fontSize: "1rem",
          transition: "all 180ms ease",
          ...toggleBtn,
        }}
      >
        {theme === "dark" ? "☀" : "☾"}
      </button>

      <style>{`
        @keyframes loginIn   { from{opacity:0;transform:translateY(24px) scale(0.96)} to{opacity:1;transform:translateY(0) scale(1)} }
        @keyframes welcomePulse { 0%,80%,100%{transform:translateY(0) scale(0.8);opacity:0.5} 40%{transform:translateY(-5px) scale(1);opacity:1} }
        .login-inp::placeholder { color:${dk ? "rgba(255,255,255,0.28)" : "#94a3b8"}; }
        .login-inp:focus { outline:none; }
        .btn-usr:hover { filter:brightness(1.07); transform:translateY(-2px)!important; box-shadow:0 8px 28px rgba(76,175,114,0.45)!important; }
        .btn-usr:active { transform:scale(0.97)!important; }
        .btn-adm:hover { filter:brightness(1.07); transform:translateY(-2px)!important; box-shadow:0 8px 28px rgba(37,99,235,0.40)!important; }
        .btn-adm:active { transform:scale(0.97)!important; }
      `}</style>

      <div style={{ width:"100%", maxWidth:440, animation:"loginIn 460ms cubic-bezier(0.2,0.9,0.2,1) both", position:"relative", zIndex:1 }}>

        {/* Logo */}
        <div style={{ display:"flex", justifyContent:"center", marginBottom:"1.6rem" }}>
          <div style={{
            background: "#fff",
            borderRadius: 16,
            padding: "0.6rem 1.25rem",
            boxShadow: dk ? "0 4px 24px rgba(0,0,0,0.32)" : "0 2px 16px rgba(37,99,235,0.10)",
          }}>
            <img
              src="/logo.png"
              alt="AgroClima GT"
              style={{ width: 260, height: "auto", objectFit: "contain", display: "block" }}
            />
          </div>
        </div>

        {/* Card usuario */}
        <div style={{
          backdropFilter:"blur(18px)", WebkitBackdropFilter:"blur(18px)",
          borderRadius:20, padding:"1.6rem", marginBottom:"0.9rem",
          position:"relative", overflow:"hidden",
          transition:"background 300ms, border 300ms",
          ...cardUser,
        }}>
          <div style={{ display:"flex", alignItems:"center", gap:"0.55rem", marginBottom:"1rem" }}>
            <div style={{ width:28, height:28, borderRadius:8, background:"rgba(76,175,114,0.14)", border:"1px solid rgba(76,175,114,0.28)", display:"flex", alignItems:"center", justifyContent:"center", color:"#22c55e" }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            </div>
            <p style={{ color: textSecondary, fontSize:"0.78rem", margin:0, fontWeight:700, textTransform:"uppercase", letterSpacing:"0.08em" }}>Acceso de usuario</p>
          </div>
          <button className="btn-usr" onClick={()=>onLogin("user")} style={{
            width:"100%", padding:"0.9rem",
            background:"#246222",
            border:"none", borderRadius:12, color:"#fff", fontWeight:700, fontSize:"0.9rem",
            cursor:"pointer", fontFamily:"inherit", letterSpacing:"0.01em",
            display:"flex", alignItems:"center", justifyContent:"center", gap:"0.6rem",
            boxShadow:"0 4px 18px rgba(38,99,36,0.35)",
            transition:"all 200ms ease",
          }}>
            <span>Ingresar al panel de usuario</span><ArrowIcon />
          </button>
          <p style={{ color: textMuted, fontSize:"0.7rem", textAlign:"center", margin:"0.75rem 0 0" }}>
            Acceso sin credenciales — visualizacion y analisis
          </p>
        </div>

        {/* Separador */}
        <div style={{ height:"0.9rem" }} />

        {/* Card admin */}
        <div style={{
          backdropFilter:"blur(18px)", WebkitBackdropFilter:"blur(18px)",
          borderRadius:20, padding:"1.6rem", position:"relative", overflow:"hidden",
          transition:"background 300ms, border 300ms",
          ...cardAdmin,
        }}>
          <div style={{ display:"flex", alignItems:"center", gap:"0.55rem", marginBottom:"1.1rem" }}>
            <div style={{ width:28, height:28, borderRadius:8, background:"rgba(37,99,235,0.12)", border:"1px solid rgba(37,99,235,0.28)", display:"flex", alignItems:"center", justifyContent:"center", color:"#2563eb" }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            </div>
            <p style={{ color: textSecondary, fontSize:"0.78rem", margin:0, fontWeight:700, textTransform:"uppercase", letterSpacing:"0.08em" }}>Acceso de administrador</p>
          </div>

          <form onSubmit={handleAdmin} style={{ display:"flex", flexDirection:"column", gap:"0.7rem" }}>
            {/* Input usuario */}
            <div style={{ position:"relative" }}>
              <div style={{ position:"absolute", left:"0.85rem", top:"50%", transform:"translateY(-50%)", color: focusUser ? "#2563eb" : (dk ? "rgba(255,255,255,0.28)" : "#94a3b8"), transition:"color 150ms", pointerEvents:"none" }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              </div>
              <input className="login-inp" type="text" placeholder="Usuario" value={user}
                onChange={e=>setUser(e.target.value)} onFocus={()=>setFocusUser(true)} onBlur={()=>setFocusUser(false)}
                autoComplete="off"
                style={{ width:"100%", padding:"0.78rem 0.9rem 0.78rem 2.6rem", background:inputBg(focusUser), border:`1.5px solid ${inputBorder(focusUser)}`, borderRadius:10, color:inputColor, fontSize:"0.88rem", fontFamily:"inherit", boxSizing:"border-box", transition:"border-color 160ms,background 160ms", boxShadow:inputShadow(focusUser) }}
              />
            </div>
            {/* Input contraseña */}
            <div style={{ position:"relative" }}>
              <div style={{ position:"absolute", left:"0.85rem", top:"50%", transform:"translateY(-50%)", color: focusPass ? "#2563eb" : (dk ? "rgba(255,255,255,0.28)" : "#94a3b8"), transition:"color 150ms", pointerEvents:"none" }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              </div>
              <input className="login-inp" type="password" placeholder="Contraseña" value={pass}
                onChange={e=>setPass(e.target.value)} onFocus={()=>setFocusPass(true)} onBlur={()=>setFocusPass(false)}
                autoComplete="new-password"
                style={{ width:"100%", padding:"0.78rem 0.9rem 0.78rem 2.6rem", background:inputBg(focusPass), border:`1.5px solid ${inputBorder(focusPass)}`, borderRadius:10, color:inputColor, fontSize:"0.88rem", fontFamily:"inherit", boxSizing:"border-box", transition:"border-color 160ms,background 160ms", boxShadow:inputShadow(focusPass) }}
              />
            </div>

            {error && (
              <div style={{ display:"flex", alignItems:"flex-start", gap:"0.5rem", padding:"0.62rem 0.8rem", background:"rgba(248,113,113,0.10)", border:"1px solid rgba(248,113,113,0.28)", borderRadius:8 }}>
                <span style={{ color:"#ef4444", fontSize:"0.9rem", lineHeight:1 }}>⚠</span>
                <p style={{ color: dk ? "#fca5a5" : "#b91c1c", fontSize:"0.76rem", margin:0, lineHeight:1.5 }}>{error}</p>
              </div>
            )}

            <button className="btn-adm" type="submit" disabled={loading} style={{
              width:"100%", padding:"0.88rem",
              background: loading ? (dk ? "rgba(255,255,255,0.08)" : "#e2e8f0") : "#2563eb",
              border:"none", borderRadius:12, color:"#fff", fontWeight:700, fontSize:"0.9rem",
              cursor:loading?"not-allowed":"pointer", fontFamily:"inherit", opacity:loading?0.65:1,
              display:"flex", alignItems:"center", justifyContent:"center", gap:"0.6rem",
              boxShadow:loading?"none":"0 4px 18px rgba(37,99,235,0.35)",
              transition:"all 200ms ease", marginTop:"0.1rem",
            }}>
              {loading
                ? <><span style={{opacity:0.7}}>Verificando</span><span style={{display:"inline-flex",gap:3}}>{[0,1,2].map(i=><span key={i} style={{width:4,height:4,borderRadius:"50%",background:"rgba(255,255,255,0.7)",animation:`welcomePulse 900ms ${i*120}ms ease-in-out infinite`,display:"inline-block"}}/>)}</span></>
                : <><span>Ingresar como administrador</span><ArrowIcon /></>
              }
            </button>
          </form>
        </div>

        <p style={{ color: footerColor, fontSize:"0.68rem", textAlign:"center", marginTop:"1.75rem" }}>
          AgroClima GT — Prototipo de tesis USAC 2025 · Guatemala
        </p>
      </div>
    </div>
  );
}
