"""
Tool de envío de email por SMTP (Gmail).
Usa APP_PASSWORD_GMAIL para autenticación.
"""

import os
import smtplib
import socket # nuevo
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from langchain_core.tools import tool


def append_email_signature(body: str) -> str:
    """Añade EMAIL_FIRMA (.env) al final del cuerpo si está definida."""
    sig = (os.getenv("EMAIL_FIRMA") or "").strip()
    if not sig:
        return body
    return body.rstrip() + "\n\n" + sig


@tool
def send_email(recipient_email: str, subject: str, body: str) -> str:
    """Envia un email via SMTP de Gmail al destinatario indicado.

    Args:
        recipient_email: Direccion de correo del destinatario.
        subject: Asunto del email.
        body: Cuerpo del email en texto plano.
    """
    sender_email = os.getenv("EMAIL_REMITENTE")
    app_password = os.getenv("APP_PASSWORD_GMAIL")

    if not sender_email or not app_password:
        return "Error: Variables EMAIL_REMITENTE o APP_PASSWORD_GMAIL no configuradas en .env"

    body = append_email_signature(body)

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        # ✅ Forzar IPv4
        smtp_host = socket.gethostbyname("smtp.gmail.com")

        with smtplib.SMTP(smtp_host, 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())

        return f"Email enviado exitosamente a {recipient_email}"

    except Exception as e:
        return f"Error al enviar email: {str(e)}"

    '''
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        return f"Email enviado exitosamente a {recipient_email}"
    except Exception as e:
        return f"Error al enviar email: {str(e)}"
    '''
