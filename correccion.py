"""Motor de corrección ortográfica y gramatical (Claude API).

Corrige el texto en español de Chile para documentos HSE/minería, priorizando el
vocabulario técnico del proyecto (no "corrige" siglas ni términos de faena).

Es **best-effort**: si falta ANTHROPIC_API_KEY o la API falla/expira, devuelve el
texto original con un flag; nunca lanza una excepción hacia arriba. Así la corrección
es opcional y no afecta la estabilidad del resto de la aplicación.
"""
import os
import json

MODELO = 'claude-haiku-4-5'   # económico y rápido para corrección


def corregir_texto(texto, vocabulario=None):
    """Devuelve dict {ok, original, corregido, cambios, error?}."""
    texto = (texto or '').strip()
    if not texto:
        return {'ok': False, 'original': texto, 'corregido': texto,
                'cambios': [], 'error': 'Texto vacío.'}

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return {'ok': False, 'original': texto, 'corregido': texto, 'cambios': [],
                'no_configurado': True,
                'error': 'Corrección no configurada: falta ANTHROPIC_API_KEY en el entorno.'}

    terminos = [v['termino'] for v in (vocabulario or [])]
    lista_vocab = ', '.join(terminos) if terminos else '(sin términos personalizados)'

    system = (
        "Eres un corrector de estilo experto en documentos de Seguridad y Salud en el "
        "Trabajo (HSE) y minería en Chile. Corrige ortografía, tildes, puntuación y "
        "gramática en español de Chile, manteniendo el sentido y el tono técnico-formal. "
        "NO alteres, traduzcas ni marques como error los siguientes términos técnicos y "
        "siglas de faena (respétalos exactamente, incluida su mayúscula): "
        f"{lista_vocab}. "
        "Responde SÓLO con un objeto JSON válido, sin texto adicional, con la forma: "
        '{"texto_corregido": "...", "cambios": ["desc1", "desc2"]}. '
        "Si el texto ya está correcto, devuelve el mismo texto y cambios: []."
    )

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=MODELO,
            max_tokens=2000,
            system=system,
            messages=[{'role': 'user', 'content': texto}],
        )
        raw = ''.join(b.text for b in msg.content if getattr(b, 'type', '') == 'text').strip()
        # el modelo puede envolver el JSON; extraer el primer objeto {...}
        ini, fin = raw.find('{'), raw.rfind('}')
        data = json.loads(raw[ini:fin + 1]) if ini >= 0 and fin > ini else {}
        corregido = (data.get('texto_corregido') or texto).strip()
        cambios = data.get('cambios') or []
        return {'ok': True, 'original': texto, 'corregido': corregido, 'cambios': cambios}
    except Exception as e:                      # noqa: BLE001 — best-effort, nunca propaga
        return {'ok': False, 'original': texto, 'corregido': texto, 'cambios': [],
                'error': f'No se pudo corregir (motor no disponible): {type(e).__name__}.'}
