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

export default function Login({ onLogin }) {
  const [user, setUser]       = useState("");
  const [pass, setPass]       = useState("");
  const [error, setError]     = useState("");
  const [loading, setLoading] = useState(false);
  const [focusUser, setFocusUser] = useState(false);
  const [focusPass, setFocusPass] = useState(false);

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

  const orb = (top, left, right, bottom, w, h, color, delay) => (
    <div style={{
      position: "absolute", top, left, right, bottom,
      width: w, height: h, borderRadius: "50%",
      background: `radial-gradient(circle, ${color} 0%, transparent 65%)`,
      filter: "blur(2px)", pointerEvents: "none",
      animation: `loginOrb${delay} ${12 + delay * 3}s ease-in-out infinite`,
    }} />
  );

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #060d0a 0%, #0c1f10 30%, #081525 70%, #040d06 100%)",
      display: "flex", alignItems: "center", justifyContent: "center",
      fontFamily: '"Inter","DM Sans",system-ui,sans-serif',
      padding: "1.5rem", position: "relative", overflow: "hidden",
    }}>
      {/* Orbes de fondo */}
      {orb("-15%", "-10%", undefined, undefined, "55vw", "55vw", "rgba(76,175,114,0.12)", 1)}
      {orb(undefined, undefined, "-10%", "-20%", "60vw", "60vw", "rgba(3,105,161,0.10)", 2)}
      {orb("40%", undefined, "15%", undefined, "25vw", "25vw", "rgba(139,94,25,0.08)", 3)}

      {/* Cuadrícula decorativa */}
      <div style={{
        position: "absolute", inset: 0,
        backgroundImage: "linear-gradient(rgba(76,175,114,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(76,175,114,0.04) 1px, transparent 1px)",
        backgroundSize: "48px 48px", pointerEvents: "none",
      }} />

      <style>{`
        @keyframes loginOrb1 { 0%,100%{transform:translate(0,0) scale(1)} 33%{transform:translate(3%,5%) scale(1.04)} 66%{transform:translate(-2%,3%) scale(0.97)} }
        @keyframes loginOrb2 { 0%,100%{transform:translate(0,0) scale(1)} 40%{transform:translate(-4%,-3%) scale(1.06)} 70%{transform:translate(2%,-5%) scale(0.96)} }
        @keyframes loginOrb3 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-6%,4%)} }
        @keyframes loginIn   { from{opacity:0;transform:translateY(24px) scale(0.96)} to{opacity:1;transform:translateY(0) scale(1)} }
        @keyframes tagIn     { from{opacity:0;transform:translateX(-10px)} to{opacity:1;transform:translateX(0)} }
        @keyframes welcomePulse { 0%,80%,100%{transform:translateY(0) scale(0.8);opacity:0.5} 40%{transform:translateY(-5px) scale(1);opacity:1} }
        .login-inp::placeholder { color:rgba(255,255,255,0.28); }
        .login-inp:focus { outline:none; }
        .btn-usr:hover { filter:brightness(1.08); transform:translateY(-2px)!important; box-shadow:0 8px 28px rgba(76,175,114,0.45)!important; }
        .btn-usr:active { transform:scale(0.97)!important; }
        .btn-adm:hover { filter:brightness(1.08); transform:translateY(-2px)!important; box-shadow:0 8px 28px rgba(37,99,235,0.40)!important; }
        .btn-adm:active { transform:scale(0.97)!important; }
      `}</style>

      <div style={{ width:"100%", maxWidth:440, animation:"loginIn 460ms cubic-bezier(0.2,0.9,0.2,1) both", position:"relative", zIndex:1 }}>

        {/* Logo */}
        <div style={{ textAlign:"center", marginBottom:"2rem" }}>
          <div style={{
            display:"inline-flex", alignItems:"center", justifyContent:"center",
            width:68, height:68, borderRadius:22,
            background:"linear-gradient(145deg,#4caf72 0%,#246222 55%,#163915 100%)",
            marginBottom:"1.1rem",
            boxShadow:"0 0 0 1px rgba(76,175,114,0.38),0 8px 32px rgba(38,99,36,0.55),0 0 48px rgba(76,175,114,0.20)",
            color:"#e8f5e2", position:"relative",
          }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10z"/>
              <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
            </svg>
            <div style={{ position:"absolute", inset:0, borderRadius:"inherit", background:"linear-gradient(145deg,rgba(255,255,255,0.16),transparent 60%)", pointerEvents:"none" }} />
          </div>

          <div style={{ display:"flex", justifyContent:"center", gap:"0.45rem", marginBottom:"1.1rem", flexWrap:"wrap" }}>
            {["XGBoost ML","Open-Meteo","37 cultivos"].map((t,i)=>(
              <span key={t} style={{
                fontSize:"0.6rem", fontWeight:700, letterSpacing:"0.07em", textTransform:"uppercase",
                padding:"0.22rem 0.65rem", borderRadius:999,
                background:"rgba(76,175,114,0.12)", border:"1px solid rgba(76,175,114,0.22)",
                color:"rgba(140,232,164,0.85)", animation:`tagIn 360ms ${i*80}ms ease both`,
              }}>{t}</span>
            ))}
          </div>

          <h1 style={{ color:"#f0f8ec", fontSize:"1.95rem", fontWeight:900, margin:0, letterSpacing:"-0.045em", lineHeight:1.15 }}>
            AgroClima <span style={{ color:"#4caf72" }}>GT</span>
          </h1>
          <p style={{ color:"rgba(255,255,255,0.42)", fontSize:"0.84rem", margin:"0.38rem 0 0" }}>
            Sistema de monitoreo agroclimatico · USAC 2025
          </p>
        </div>

        {/* Card usuario */}
        <div style={{
          background:"rgba(255,255,255,0.04)", backdropFilter:"blur(18px)", WebkitBackdropFilter:"blur(18px)",
          border:"1px solid rgba(76,175,114,0.18)", borderRadius:20, padding:"1.6rem", marginBottom:"0.9rem", position:"relative", overflow:"hidden",
        }}>
          <div style={{ position:"absolute", top:0, left:0, right:0, height:1, background:"linear-gradient(90deg,transparent,rgba(76,175,114,0.45),transparent)", pointerEvents:"none" }} />
          <div style={{ display:"flex", alignItems:"center", gap:"0.55rem", marginBottom:"1rem" }}>
            <div style={{ width:28, height:28, borderRadius:8, background:"rgba(76,175,114,0.14)", border:"1px solid rgba(76,175,114,0.26)", display:"flex", alignItems:"center", justifyContent:"center", color:"#4caf72" }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            </div>
            <p style={{ color:"rgba(255,255,255,0.65)", fontSize:"0.78rem", margin:0, fontWeight:700, textTransform:"uppercase", letterSpacing:"0.08em" }}>Acceso de usuario</p>
          </div>
          <button className="btn-usr" onClick={()=>onLogin("user")} style={{
            width:"100%", padding:"0.9rem",
            background:"linear-gradient(135deg,#4caf72 0%,#246222 60%,#163915 100%)",
            border:"none", borderRadius:12, color:"#fff", fontWeight:700, fontSize:"0.9rem",
            cursor:"pointer", fontFamily:"inherit", letterSpacing:"0.01em",
            display:"flex", alignItems:"center", justifyContent:"center", gap:"0.6rem",
            boxShadow:"0 4px 18px rgba(38,99,36,0.42),0 0 0 1px rgba(76,175,114,0.22) inset",
            transition:"all 200ms ease", position:"relative", overflow:"hidden",
          }}>
            <div style={{ position:"absolute", inset:0, background:"linear-gradient(180deg,rgba(255,255,255,0.12),transparent 55%)", pointerEvents:"none" }} />
            <span>Ingresar al panel de usuario</span><ArrowIcon />
          </button>
          <p style={{ color:"rgba(255,255,255,0.28)", fontSize:"0.7rem", textAlign:"center", margin:"0.75rem 0 0" }}>
            Acceso sin credenciales — visualizacion y analisis
          </p>
        </div>

        {/* Divider */}
        <div style={{ display:"flex", alignItems:"center", gap:"0.75rem", margin:"0 0 0.9rem" }}>
          <div style={{ flex:1, height:1, background:"rgba(255,255,255,0.08)" }} />
          <span style={{ fontSize:"0.68rem", color:"rgba(255,255,255,0.25)", fontWeight:600, letterSpacing:"0.06em" }}>O</span>
          <div style={{ flex:1, height:1, background:"rgba(255,255,255,0.08)" }} />
        </div>

        {/* Card admin */}
        <div style={{
          background:"rgba(255,255,255,0.035)", backdropFilter:"blur(18px)", WebkitBackdropFilter:"blur(18px)",
          border:"1px solid rgba(255,255,255,0.10)", borderRadius:20, padding:"1.6rem", position:"relative", overflow:"hidden",
        }}>
          <div style={{ position:"absolute", top:0, left:0, right:0, height:1, background:"linear-gradient(90deg,transparent,rgba(255,255,255,0.15),transparent)", pointerEvents:"none" }} />
          <div style={{ display:"flex", alignItems:"center", gap:"0.55rem", marginBottom:"1.1rem" }}>
            <div style={{ width:28, height:28, borderRadius:8, background:"rgba(37,99,235,0.14)", border:"1px solid rgba(37,99,235,0.28)", display:"flex", alignItems:"center", justifyContent:"center", color:"#60a5fa" }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            </div>
            <p style={{ color:"rgba(255,255,255,0.60)", fontSize:"0.78rem", margin:0, fontWeight:700, textTransform:"uppercase", letterSpacing:"0.08em" }}>Acceso de administrador</p>
          </div>

          <form onSubmit={handleAdmin} style={{ display:"flex", flexDirection:"column", gap:"0.7rem" }}>
            <div style={{ position:"relative" }}>
              <div style={{ position:"absolute", left:"0.85rem", top:"50%", transform:"translateY(-50%)", color:focusUser?"rgba(96,165,250,0.8)":"rgba(255,255,255,0.28)", transition:"color 150ms", pointerEvents:"none" }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              </div>
              <input className="login-inp" type="text" placeholder="Usuario" value={user}
                onChange={e=>setUser(e.target.value)} onFocus={()=>setFocusUser(true)} onBlur={()=>setFocusUser(false)}
                autoComplete="off"
                style={{ width:"100%", padding:"0.78rem 0.9rem 0.78rem 2.6rem", background:focusUser?"rgba(255,255,255,0.09)":"rgba(255,255,255,0.06)", border:`1.5px solid ${focusUser?"rgba(96,165,250,0.5)":"rgba(255,255,255,0.12)"}`, borderRadius:10, color:"#fff", fontSize:"0.88rem", fontFamily:"inherit", boxSizing:"border-box", transition:"border-color 160ms,background 160ms", boxShadow:focusUser?"0 0 0 3px rgba(37,99,235,0.14)":"none" }}
              />
            </div>
            <div style={{ position:"relative" }}>
              <div style={{ position:"absolute", left:"0.85rem", top:"50%", transform:"translateY(-50%)", color:focusPass?"rgba(96,165,250,0.8)":"rgba(255,255,255,0.28)", transition:"color 150ms", pointerEvents:"none" }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              </div>
              <input className="login-inp" type="password" placeholder="Contraseña" value={pass}
                onChange={e=>setPass(e.target.value)} onFocus={()=>setFocusPass(true)} onBlur={()=>setFocusPass(false)}
                autoComplete="new-password"
                style={{ width:"100%", padding:"0.78rem 0.9rem 0.78rem 2.6rem", background:focusPass?"rgba(255,255,255,0.09)":"rgba(255,255,255,0.06)", border:`1.5px solid ${focusPass?"rgba(96,165,250,0.5)":"rgba(255,255,255,0.12)"}`, borderRadius:10, color:"#fff", fontSize:"0.88rem", fontFamily:"inherit", boxSizing:"border-box", transition:"border-color 160ms,background 160ms", boxShadow:focusPass?"0 0 0 3px rgba(37,99,235,0.14)":"none" }}
              />
            </div>

            {error && (
              <div style={{ display:"flex", alignItems:"flex-start", gap:"0.5rem", padding:"0.62rem 0.8rem", background:"rgba(248,113,113,0.10)", border:"1px solid rgba(248,113,113,0.24)", borderRadius:8 }}>
                <span style={{ color:"#f87171", fontSize:"0.9rem", lineHeight:1 }}>⚠</span>
                <p style={{ color:"#fca5a5", fontSize:"0.76rem", margin:0, lineHeight:1.5 }}>{error}</p>
              </div>
            )}

            <button className="btn-adm" type="submit" disabled={loading} style={{
              width:"100%", padding:"0.88rem",
              background:loading?"rgba(255,255,255,0.08)":"linear-gradient(135deg,#2563eb 0%,#1d4ed8 55%,#1e3a8a 100%)",
              border:"none", borderRadius:12, color:"#fff", fontWeight:700, fontSize:"0.9rem",
              cursor:loading?"not-allowed":"pointer", fontFamily:"inherit", opacity:loading?0.65:1,
              display:"flex", alignItems:"center", justifyContent:"center", gap:"0.6rem",
              boxShadow:loading?"none":"0 4px 18px rgba(37,99,235,0.40),0 0 0 1px rgba(96,165,250,0.18) inset",
              transition:"all 200ms ease", position:"relative", overflow:"hidden", marginTop:"0.1rem",
            }}>
              {!loading && <div style={{ position:"absolute", inset:0, background:"linear-gradient(180deg,rgba(255,255,255,0.12),transparent 55%)", pointerEvents:"none" }} />}
              {loading
                ? <><span style={{opacity:0.7}}>Verificando</span><span style={{display:"inline-flex",gap:3}}>{[0,1,2].map(i=><span key={i} style={{width:4,height:4,borderRadius:"50%",background:"rgba(255,255,255,0.7)",animation:`welcomePulse 900ms ${i*120}ms ease-in-out infinite`,display:"inline-block"}}/>)}</span></>
                : <><span>Ingresar como administrador</span><ArrowIcon /></>
              }
            </button>
          </form>
        </div>

        <p style={{ color:"rgba(255,255,255,0.18)", fontSize:"0.68rem", textAlign:"center", marginTop:"1.75rem" }}>
          AgroClima GT — Prototipo de tesis USAC 2025 · Guatemala
        </p>
      </div>
    </div>
  );
}
