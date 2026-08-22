"""Envío de correo transaccional (Resend). Dato/servicio puro: no toca la BD ni Flask, solo
sabe armar y enviar un email.

Sin RESEND_API_KEY configurada (ej. desarrollo local), no falla: imprime el contenido a consola
para poder seguir probando el flujo de recuperación de clave sin cuenta real de Resend.
"""
import os

REMITENTE = os.environ.get('RESEND_FROM', 'Smart HSE <onboarding@resend.dev>')


def _enviar(destinatario, asunto, html):
    api_key = os.environ.get('RESEND_API_KEY')
    if not api_key:
        print(f'[correo] RESEND_API_KEY no configurada — envío simulado a {destinatario}:\n'
              f'  Asunto: {asunto}\n  {html}', flush=True)
        return
    try:
        import resend
        resend.api_key = api_key
        resend.Emails.send({
            'from': REMITENTE,
            'to': [destinatario],
            'subject': asunto,
            'html': html,
        })
    except Exception:
        # Nunca debe tumbar la ruta con un 500: el usuario final sigue viendo el mismo mensaje
        # genérico de siempre (anti-enumeración). El detalle real queda en los Logs de Render
        # para que se pueda diagnosticar (ej. remitente sandbox de Resend sin dominio verificado).
        import traceback
        traceback.print_exc()
        print(f'[correo] Falló el envío a {destinatario} — ver traza arriba.', flush=True)


def enviar_reset_clave(email, token, base_url):
    """base_url = request.host_url (con barra final), sin hardcodear el dominio."""
    link = f"{base_url.rstrip('/')}/reset-clave/{token}"
    html = f"""
    <p>Recibimos una solicitud para restablecer tu clave de Smart HSE.</p>
    <p><a href="{link}">Haz clic aquí para elegir una nueva clave</a> (válido por 1 hora).</p>
    <p>Si no fuiste tú, ignora este correo — tu clave actual sigue funcionando.</p>
    """
    _enviar(email, 'Smart HSE — Recuperar tu clave', html)
