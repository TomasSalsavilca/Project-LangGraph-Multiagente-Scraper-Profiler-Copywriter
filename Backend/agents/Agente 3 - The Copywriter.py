"""
Agente 3 - The Copywriter

Toma los "dolores" detectados por el Agente 2 y redacta un Cold Email
ofreciendo servicios, conectando específicamente con lo que hace la empresa.
Luego decide si enviar el email usando la tool send_email.

Misión: "La Conexión" — Unir punto A (Cliente) y punto B (Tu servicio).
"""

import os
import re
import sys
from typing import TypedDict

SALIDAS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Salidas de los Agentes")

# Agregar el directorio Backend al path para importar tools
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from tools.send_email import append_email_signature, send_email


# --- Tipos para el grafo ---
class CopywriterState(TypedDict, total=False):
    """Estado: profile_data del Agente 2 + config de tu servicio."""
    profile_data: str
    my_service_info: str
    company_tone: str
    final_email: str
    recipient_email: str
    email_sent_status: str


# --- LLM con tools bindeadas ---
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
tools = [send_email]

SYSTEM_PROMPT = """Eres un experto Copywriter de ventas B2B especializado en 'Cold Emailing'.
Tienes acceso a la herramienta send_email para enviar correos electrónicos.

Tu flujo de trabajo es:
1. Primero, genera el cold email basándote en la información del prospecto.
2. Luego, si se te proporciona un email de destinatario, usa la herramienta send_email para enviarlo.

Reglas para redactar el email:
- Empieza con un 'Icebreaker' genuino sobre algo específico que encontraste en su web.
- Menciona el problema (Punto de dolor) usando sus propias palabras si es posible.
- Presenta la solución de IA como el alivio natural a ese dolor.
- Call to Action (CTA) de bajo compromiso (ej: '¿Te envío un video de 3 min?').
- Adapta el tono al estilo indicado.
- Cierra con un saludo cordial (ej. 'Saludos cordiales,' o 'Atentamente,'). No escribas nombre, cargo ni datos de contacto después: el sistema los añade al enviar.
"""

copywriter_agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)


def _extract_pain_points(profile_data: str) -> str:
    """Extrae la sección 'Puntos de Dolor' del perfil del Agente 2."""
    if not profile_data:
        return "(No se detectaron puntos de dolor)"
    pattern = r"\*\*Puntos de Dolor[^*]*\*\*[:\s]*(.*?)(?=\n\n\d\.|\n\n\*\*|\n\n##|\Z)"
    match = re.search(pattern, profile_data, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return profile_data[:1500] if len(profile_data) > 1500 else profile_data


def copywriter_node(state: CopywriterState) -> dict[str, str]:
    """
    Nodo que genera el Cold Email y lo envía usando la tool send_email.
    El agente ReAct decide cuándo invocar la tool.
    """
    profile_data = state.get("profile_data", "")
    my_service_info = state.get("my_service_info", "Soluciones de IA para empresas")
    company_tone = state.get("company_tone", "profesional y cercano")
    recipient_email = state.get("recipient_email", "")

    pain_points = _extract_pain_points(profile_data)

    # Construir el mensaje para el agente
    user_message = f"""Genera un cold email con esta información:

Negocio del prospecto: {profile_data}
Puntos de dolor: {pain_points}
Nosotros vendemos: {my_service_info}
Tono deseado: {company_tone}

Primero redacta el email completo.
"""
    if recipient_email:
        user_message += f"""
Luego envíalo usando la herramienta send_email con estos datos:
- recipient_email: {recipient_email}
- subject: Propuesta de colaboración - Soluciones de IA
- body: el email que acabas de redactar
"""

    print("[Agente 3] Copywriter (ReAct) generando email...", flush=True)

    result = copywriter_agent.invoke(
        {"messages": [HumanMessage(content=user_message)]}
    )

    # Extraer el email generado y el estado de envío de los mensajes
    messages = result["messages"]
    final_email = ""
    email_sent_status = ""

    for msg in messages:
        # El primer AIMessage con content es el email generado
        if msg.type == "ai" and msg.content and not final_email:
            final_email = msg.content
        # Los ToolMessages contienen el resultado del envío
        if msg.type == "tool" and msg.name == "send_email":
            email_sent_status = msg.content

    if final_email:
        final_email = append_email_signature(final_email)

    print("[Agente 3] Copywriter completado", flush=True)
    if email_sent_status:
        print(f"[Agente 3] {email_sent_status}", flush=True)

    # Guardar salida en documento para revisión
    run_id = state.get("run_id")
    if run_id:
        run_dir = os.path.join(SALIDAS_DIR, run_id)
        os.makedirs(run_dir, exist_ok=True)
        out_path = os.path.join(run_dir, "agente3_email.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(final_email)
        print(f"[Agente 3] Guardado: {out_path}", flush=True)

    return {"final_email": final_email, "email_sent_status": email_sent_status}
