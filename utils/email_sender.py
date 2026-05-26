"""
Utilidad para enviar emails de notificación a técnicos.
Requiere variables de entorno SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS.
Si no están configuradas, solo registra un log y retorna False sin romper el flujo.

Configuración de ejemplo (.env o variables del sistema):
    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USER=hotel@example.com
    SMTP_PASS=tu_app_password_de_google
    SMTP_FROM=Hotel Mantenimiento <hotel@example.com>
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


def enviar_email_tecnico(
    destinatario_email: str,
    nombre_tecnico: str,
    habitacion: str,
    tipo_equipo: str,
    fecha_sugerida: str,
    prioridad: str,
) -> bool:
    """
    Envía notificación al técnico cuando se aprueba una orden preventiva.
    Retorna True si se envió, False si SMTP no está configurado o falló.
    """
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)

    if not all([smtp_host, smtp_user, smtp_pass]):
        logger.info(
            "SMTP no configurado — email no enviado a %s (%s). "
            "Orden: Hab #%s / %s / %s",
            nombre_tecnico, destinatario_email, habitacion, tipo_equipo, fecha_sugerida,
        )
        return False

    asunto = f"[Hotel] Nueva orden asignada: Hab #{habitacion} — {tipo_equipo}"
    cuerpo = (
        f"Estimado/a {nombre_tecnico},\n\n"
        f"Se te ha asignado una nueva orden de mantenimiento preventivo:\n\n"
        f"  Habitación:     #{habitacion}\n"
        f"  Equipo:         {tipo_equipo}\n"
        f"  Fecha sugerida: {fecha_sugerida}\n"
        f"  Prioridad:      {prioridad}\n\n"
        f"Por favor ingresa al sistema para confirmar y coordinar la intervención.\n\n"
        f"Hotel Mantenimiento — Sistema Automatizado\n"
    )

    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_from
        msg["To"] = destinatario_email
        msg["Subject"] = asunto
        msg.attach(MIMEText(cuerpo, "plain", "utf-8"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_from, [destinatario_email], msg.as_string())

        logger.info("Email enviado a %s (%s)", nombre_tecnico, destinatario_email)
        return True

    except Exception as e:
        logger.error("Fallo al enviar email a %s (%s): %s", nombre_tecnico, destinatario_email, e)
        return False
