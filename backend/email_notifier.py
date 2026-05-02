"""
Notificador de alertas críticas por correo electrónico — AgroClima GT.

Envía un email HTML cuando el Arduino detecta condiciones severas.
Incluye cooldown por variable para evitar spam (mínimo 30 min entre
correos del mismo tipo de alerta para el mismo cultivo).

Configuración (archivo .env en el directorio del backend):
    SMTP_HOST       = smtp.gmail.com
    SMTP_PORT       = 587
    SMTP_USER       = tucorreo@gmail.com
    SMTP_PASSWORD   = xxxx xxxx xxxx xxxx   (contraseña de aplicación Gmail)
    ALERT_EMAIL_FROM= tucorreo@gmail.com
    ALERT_EMAIL_TO  = destinatario@gmail.com,otro@gmail.com

Para Gmail necesitas una "Contraseña de aplicación":
    Mi cuenta Google → Seguridad → Verificación en 2 pasos → Contraseñas de app
"""

import os
import smtplib
import ssl
import threading
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ── Cargar .env si existe ──────────────────────────────────────────────────

def _load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

_load_env()

# ── Configuración ──────────────────────────────────────────────────────────

SMTP_HOST     = os.getenv("SMTP_HOST",        "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT",    "587"))
SMTP_USER     = os.getenv("SMTP_USER",        "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD",    "")
EMAIL_FROM    = os.getenv("ALERT_EMAIL_FROM", SMTP_USER)
EMAIL_TO_RAW  = os.getenv("ALERT_EMAIL_TO",   "")

# Mínimo de minutos entre correos del mismo tipo de alerta + cultivo
COOLDOWN_MINUTES = int(os.getenv("ALERT_COOLDOWN_MIN", "30"))

# Solo se envía correo para alertas de severidad en este conjunto
NOTIFY_SEVERITIES = {"severo"}

# ── Estado interno (cooldown) ──────────────────────────────────────────────

_lock          = threading.Lock()
_last_sent: dict[tuple, datetime] = {}   # (crop, variable, condition) → timestamp


def is_configured() -> bool:
    return bool(SMTP_USER and SMTP_PASSWORD and EMAIL_TO_RAW)


def _get_recipients() -> list[str]:
    return [e.strip() for e in EMAIL_TO_RAW.split(",") if e.strip()]


def _in_cooldown(crop: str, variable: str, condition: str) -> bool:
    key = (crop, variable, condition)
    with _lock:
        last = _last_sent.get(key)
        if last and datetime.now() - last < timedelta(minutes=COOLDOWN_MINUTES):
            return True
        return False


def _mark_sent(crop: str, variable: str, condition: str):
    key = (crop, variable, condition)
    with _lock:
        _last_sent[key] = datetime.now()


# ── Plantilla HTML del correo ──────────────────────────────────────────────

_SEVERITY_COLOR = {"severo": "#dc2626", "moderado": "#d97706", "leve": "#16a34a"}
_SEVERITY_LABEL = {"severo": "CRÍTICO",  "moderado": "MODERADO", "leve": "LEVE"}

_VAR_ES = {
    "temperature":   "Temperatura",
    "humidity":      "Humedad",
    "rainfall":      "Precipitación",
    "soil_ph":       "pH del suelo",
    "soil_moisture": "Humedad del suelo",
    "light_lux":     "Luz (lux)",
    "greenness_idx": "Índice de verdor",
}


def _build_html(alerts: list[dict], crop: str, municipio: str,
                sensors: dict, timestamp: str) -> str:
    rows = ""
    for a in alerts:
        color = _SEVERITY_COLOR.get(a["severity"], "#6b7280")
        label = _SEVERITY_LABEL.get(a["severity"], a["severity"].upper())
        var   = _VAR_ES.get(a["variable"], a["variable"])
        rows += f"""
        <tr>
          <td style="padding:10px 14px;border-bottom:1px solid #e5e7eb;">
            <span style="background:{color};color:#fff;font-size:11px;font-weight:700;
                         padding:2px 8px;border-radius:12px;">{label}</span>
          </td>
          <td style="padding:10px 14px;border-bottom:1px solid #e5e7eb;font-weight:600;">{var}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #e5e7eb;color:{color};font-weight:700;">
            {a['value']} (óptimo: {a['optimal_min']}–{a['optimal_max']})
          </td>
          <td style="padding:10px 14px;border-bottom:1px solid #e5e7eb;color:#374151;">
            {a.get('action','Revisar condiciones del cultivo')}
          </td>
        </tr>"""

    sensor_summary = " · ".join(
        f"<b>{_VAR_ES.get(k, k)}</b>: {round(v, 2)}"
        for k, v in sensors.items()
        if k not in ("timestamp", "color_r", "color_g", "color_b")
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Segoe UI,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0"
         style="max-width:640px;margin:32px auto;background:#fff;
                border-radius:12px;overflow:hidden;
                box-shadow:0 2px 12px rgba(0,0,0,0.08);">
    <!-- Header -->
    <tr>
      <td style="background:linear-gradient(135deg,#1e4d2b,#15803d);
                 padding:28px 32px;text-align:center;">
        <p style="margin:0 0 4px;font-size:22px;font-weight:800;color:#fff;
                  letter-spacing:-0.03em;">🌱 AgroClima GT</p>
        <p style="margin:0;font-size:13px;color:rgba(255,255,255,0.75);">
          Sistema de monitoreo agroclimatológico — Alerta automática
        </p>
      </td>
    </tr>
    <!-- Alerta banner -->
    <tr>
      <td style="background:#fef2f2;border-left:4px solid #dc2626;
                 padding:16px 32px;">
        <p style="margin:0;font-size:15px;font-weight:700;color:#991b1b;">
          ⚠️ Se detectaron condiciones críticas en el cultivo
        </p>
        <p style="margin:6px 0 0;font-size:13px;color:#6b7280;">
          <b>Cultivo:</b> {crop} &nbsp;·&nbsp;
          <b>Municipio:</b> {municipio} &nbsp;·&nbsp;
          <b>Hora:</b> {timestamp}
        </p>
      </td>
    </tr>
    <!-- Lecturas actuales -->
    <tr>
      <td style="padding:20px 32px 8px;">
        <p style="margin:0 0 8px;font-size:12px;font-weight:700;
                  text-transform:uppercase;letter-spacing:.06em;color:#6b7280;">
          Lecturas del Arduino
        </p>
        <p style="margin:0;font-size:13px;color:#374151;line-height:1.6;">
          {sensor_summary}
        </p>
      </td>
    </tr>
    <!-- Tabla de alertas -->
    <tr>
      <td style="padding:16px 32px 8px;">
        <p style="margin:0 0 10px;font-size:12px;font-weight:700;
                  text-transform:uppercase;letter-spacing:.06em;color:#6b7280;">
          Alertas generadas ({len(alerts)})
        </p>
        <table width="100%" cellpadding="0" cellspacing="0"
               style="border-collapse:collapse;font-size:13px;">
          <thead>
            <tr style="background:#f9fafb;">
              <th style="padding:8px 14px;text-align:left;font-size:11px;
                         text-transform:uppercase;color:#6b7280;font-weight:700;
                         border-bottom:2px solid #e5e7eb;">Nivel</th>
              <th style="padding:8px 14px;text-align:left;font-size:11px;
                         text-transform:uppercase;color:#6b7280;font-weight:700;
                         border-bottom:2px solid #e5e7eb;">Variable</th>
              <th style="padding:8px 14px;text-align:left;font-size:11px;
                         text-transform:uppercase;color:#6b7280;font-weight:700;
                         border-bottom:2px solid #e5e7eb;">Valor medido</th>
              <th style="padding:8px 14px;text-align:left;font-size:11px;
                         text-transform:uppercase;color:#6b7280;font-weight:700;
                         border-bottom:2px solid #e5e7eb;">Acción recomendada</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
      </td>
    </tr>
    <!-- Footer -->
    <tr>
      <td style="padding:20px 32px 28px;border-top:1px solid #e5e7eb;margin-top:12px;">
        <p style="margin:0;font-size:12px;color:#9ca3af;text-align:center;">
          Este correo fue generado automáticamente por AgroClima GT.<br>
          Extensionistas MAGA: <b>1548</b> (llamada gratis) para apoyo técnico.
        </p>
      </td>
    </tr>
  </table>
</body>
</html>"""


# ── Función principal de envío ─────────────────────────────────────────────

def notify_critical_alerts(alerts: list[dict], crop: str, municipio: str,
                            sensors: dict, timestamp: str = None) -> list[str]:
    """
    Envía correos para las alertas severas que no estén en cooldown.

    Returns:
        Lista de variables para las que se envió correo.
    """
    if not is_configured():
        return []

    # Filtrar solo las alertas severas fuera de cooldown
    to_send = [
        a for a in alerts
        if a["severity"] in NOTIFY_SEVERITIES
        and not _in_cooldown(crop, a["variable"], a["condition"])
    ]

    if not to_send:
        return []

    ts = timestamp or datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    try:
        html = _build_html(to_send, crop, municipio, sensors, ts)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = (
            f"🚨 AgroClima GT — Alerta crítica en {crop} ({municipio}) · {ts}"
        )
        msg["From"]    = EMAIL_FROM
        msg["To"]      = ", ".join(_get_recipients())
        msg.attach(MIMEText(html, "html", "utf-8"))

        ctx = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls(context=ctx)
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, _get_recipients(), msg.as_string())

        sent_vars = []
        for a in to_send:
            _mark_sent(crop, a["variable"], a["condition"])
            sent_vars.append(a["variable"])

        print(f"[email] Alerta crítica enviada → {crop} en {municipio} | vars: {sent_vars}")
        return sent_vars

    except Exception as e:
        print(f"[email] ERROR al enviar correo: {e}")
        return []
