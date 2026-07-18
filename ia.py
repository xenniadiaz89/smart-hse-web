"""Clasificación de documentos en los ítems de la Carpeta de Arranque RESSO.

Motor híbrido: heurística por palabras clave (siempre disponible) y, si existe
ANTHROPIC_API_KEY, refuerzo con Claude (gancho preparado)."""
import os
import re
import unicodedata

import resso


def _norm(s):
    s = str(s or '').lower()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[_\-.]+', ' ', s)


def clasificar_heuristico(nombre):
    """Devuelve (item_n, score) del mejor calce por palabras clave en el nombre."""
    t = _norm(nombre)
    mejor_n, mejor_score = None, 0
    for n, kws in resso.KEYWORDS.items():
        score = 0
        for kw in kws:
            kwn = _norm(kw)
            if kwn and kwn in t:
                score += len(kwn.split())  # frases pesan más que palabras sueltas
        if score > mejor_score:
            mejor_n, mejor_score = n, score
    return mejor_n, mejor_score


def clasificar_path(relpath):
    """Clasifica usando la ruta relativa (carga de carpeta ya conformada).
    Si algún segmento de carpeta empieza con un número 1–29, lo usa directo
    (la carpeta ya está ordenada conforme al listado); si no, clasifica por nombre."""
    partes = re.split(r'[\\/]+', relpath or '')
    nombre = partes[-1] if partes else relpath
    for seg in partes[:-1]:
        m = re.match(r'\s*0?(\d{1,2})(?:[\s._\-]|$)', seg)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 29:
                return n, 'carpeta'
    return clasificar(nombre)


def clasificar(nombre, texto=None):
    """Clasifica un documento → (item_n, fuente). Heurística; Claude si hay API key."""
    n, score = clasificar_heuristico(nombre)
    if score >= 1:
        return n, 'heuristica'
    # Sin calce claro: intentar con Claude si está configurado.
    if os.environ.get('ANTHROPIC_API_KEY'):
        n_ia = _clasificar_claude(nombre, texto)
        if n_ia:
            return n_ia, 'claude'
    return 29, 'sin_clasificar'  # 29 = "Otros documentos de la faena"


def _texto_de(contenido, mimetype):
    """Extrae texto plano si el documento es text/* o HTML (barato). PDF/DOCX → None (no se parsea
    aquí; la inspección degrada a checklist manual)."""
    if not contenido:
        return None
    mt = (mimetype or '').lower()
    if 'html' in mt or 'text/plain' in mt or mt == 'text':
        try:
            t = contenido.decode('utf-8', 'ignore')
            return re.sub(r'<[^>]+>', ' ', t)  # quita etiquetas si viene HTML
        except Exception:
            return None
    return None


# Límite del payload que se manda a la API. Por encima se degrada a checklist manual: mejor
# decir "revísalo tú" que fallar a mitad de una carga.
_MAX_VISION_BYTES = 4 * 1024 * 1024

_IMAGENES = ('image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp')


def _bloque_visual(contenido, mimetype):
    """Bloque de contenido para la API (imagen o PDF), o None si este documento no aplica.

    Existe porque _texto_de() no puede con PDF ni imágenes, y ahí es justo donde vive la evidencia
    que más pesa en una fiscalización: la FOTO de dónde está publicada la MIPER (ítem 4), el PDF
    del correo con que se envió el RIOHS (ítem 50) y todo documento escaneado.
    """
    import base64
    mt = (mimetype or '').lower().split(';')[0].strip()
    if mt in _IMAGENES:
        tipo, media = 'image', ('image/jpeg' if mt == 'image/jpg' else mt)
    elif mt == 'application/pdf':
        tipo, media = 'document', 'application/pdf'
    else:
        return None
    if not contenido or len(contenido) > _MAX_VISION_BYTES:
        return None
    return {'type': tipo,
            'source': {'type': 'base64', 'media_type': media,
                       'data': base64.standard_b64encode(contenido).decode('ascii')}}


def inspeccionar_evidencia(minimos, contenido=None, mimetype=None):
    """Verifica que un documento subido contenga los elementos mínimos legales del ítem.
    Devuelve {'modo': 'ia'|'manual', 'items': [{'elemento','presente'|'estado'}], 'nota'} o None si
    no hay mínimos definidos. Best-effort: usa Claude si hay ANTHROPIC_API_KEY y el documento es
    legible (texto, imagen o PDF); si no, entrega un checklist para verificación manual.

    Nunca decide el cumplimiento: informa qué mínimos encuentra y cuáles no. Marcar el ítem como
    Cumple sigue siendo del experto, porque es un estado con peso legal.
    """
    minimos = [m for m in (minimos or []) if m]
    if not minimos:
        return None
    nota_manual = ('Verifica manualmente que el documento contenga estos elementos mínimos '
                   'que exige la ley.')
    if os.environ.get('ANTHROPIC_API_KEY'):
        texto = _texto_de(contenido, mimetype)
        if texto:
            ia_res = _inspeccionar_claude(minimos, texto)
            if ia_res is not None:
                return ia_res
        else:
            bloque = _bloque_visual(contenido, mimetype)
            if bloque:
                ia_res = _inspeccionar_claude(minimos, None, bloque=bloque)
                if ia_res is not None:
                    return ia_res
            elif contenido and len(contenido) > _MAX_VISION_BYTES:
                nota_manual = ('El archivo supera los 4 MB, así que no se analizó automáticamente. '
                               'Verifica a mano que contenga estos elementos mínimos.')
    return {'modo': 'manual',
            'items': [{'elemento': m, 'estado': 'por_verificar'} for m in minimos],
            'nota': nota_manual}


def _inspeccionar_claude(minimos, texto, bloque=None):
    """Pregunta a Claude cuáles mínimos están presentes. `texto` para documentos de texto,
    `bloque` para imagen o PDF (una sola llamada por documento). Devuelve dict o None."""
    try:
        import anthropic
        import json as _json
    except ImportError:
        return None
    try:
        lista = "\n".join(f"- {m}" for m in minimos)
        client = anthropic.Anthropic()
        if bloque:
            contenido = [bloque, {'type': 'text',
                                  'text': f"Elementos mínimos:\n{lista}\n\n"
                                          'Analiza el documento adjunto (puede ser una fotografía, '
                                          'un escaneo o un PDF) e indica cuáles de estos elementos '
                                          'aparecen efectivamente en él.'}]
        else:
            contenido = f"Elementos mínimos:\n{lista}\n\nTexto del documento:\n{texto[:6000]}"
        msg = client.messages.create(
            model=os.environ.get('SMARTHSE_IA_MODEL', 'claude-haiku-4-5'),
            max_tokens=400,
            system=("Eres un auditor SST chileno (DS 44). Te doy un documento y una lista "
                    "de elementos mínimos que la ley exige que contenga. Responde SOLO un JSON: "
                    '{"items":[{"elemento":"<texto>","presente":true|false}]} con un objeto por cada '
                    "elemento, en el mismo orden. Marca presente=true solo si lo ves en el documento; "
                    "ante la duda, false. No agregues nada fuera del JSON."),
            messages=[{'role': 'user', 'content': contenido}],
        )
        raw = msg.content[0].text
        m = re.search(r'\{.*\}', raw, re.S)
        data = _json.loads(m.group() if m else raw)
        items = [{'elemento': it.get('elemento'), 'presente': bool(it.get('presente'))}
                 for it in data.get('items', [])]
        if not items:
            return None
        faltan = [it['elemento'] for it in items if not it['presente']]
        nota = ('El documento contiene todos los elementos mínimos.' if not faltan
                else 'Faltan elementos mínimos: ' + '; '.join(faltan))
        return {'modo': 'ia', 'items': items, 'nota': nota}
    except Exception:
        return None


def analizar_ley(texto_o_link):
    """Analiza una ley (link BCN o texto pegado) y sugiere los campos de un Requisito Legal
    (OBS-3B). Devuelve {'ok':bool, 'sugerencia':{cuerpo_legal,articulo,requisito,obligacion,
    control}, 'nota'}. Best-effort: requiere ANTHROPIC_API_KEY; si no, pide captura manual."""
    txt = (texto_o_link or '').strip()
    if not txt:
        return {'ok': False, 'nota': 'Pega el texto o el link de la ley.'}
    if not os.environ.get('ANTHROPIC_API_KEY'):
        return {'ok': False, 'nota': ('Análisis con IA no disponible (falta ANTHROPIC_API_KEY). '
                                      'Completa los campos manualmente.'), 'sugerencia': {}}
    try:
        import anthropic
        import json as _json
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=os.environ.get('SMARTHSE_IA_MODEL', 'claude-haiku-4-5'),
            max_tokens=600,
            system=("Eres un abogado experto en SST chilena (DS 44, Ley 16.744). Te doy el texto o el "
                    "link BCN de una norma. Responde SOLO un JSON con los campos de un requisito legal "
                    'para una matriz de cumplimiento: {"cuerpo_legal":"","articulo":"","requisito":"",'
                    '"obligacion":"","control":"","pilar":"P1|P2|P3|OTROS"}. Sé conciso y fiel a la norma; '
                    "no inventes artículos. Si es un link que no puedes leer, deduce por el nombre."),
            messages=[{'role': 'user', 'content': txt[:4000]}],
        )
        raw = msg.content[0].text
        m = re.search(r'\{.*\}', raw, re.S)
        data = _json.loads(m.group() if m else raw)
        return {'ok': True, 'sugerencia': data,
                'nota': 'Sugerencia de la IA — revísala y ajústala antes de guardar.'}
    except Exception:
        return {'ok': False, 'nota': 'No se pudo analizar la norma. Completa los campos manualmente.',
                'sugerencia': {}}


def _clasificar_claude(nombre, texto=None):
    """Refuerzo opcional con Claude. Devuelve item_n o None.
    Requiere ANTHROPIC_API_KEY y el paquete `anthropic` (se activa en producción)."""
    try:
        import anthropic
    except ImportError:
        return None
    try:
        catalogo = "\n".join(f"{i['n']}. {i['titulo']} — {i['evidencia']}"
                             for i in resso.carpeta_lista())
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=os.environ.get('SMARTHSE_IA_MODEL', 'claude-haiku-4-5'),
            max_tokens=10,
            system=("Eres un clasificador documental de la Carpeta de Arranque RESSO (minería "
                    "Codelco). Dada la información de un documento, responde SOLO con el número "
                    "de ítem (1-29) que mejor le corresponde, según este catálogo:\n" + catalogo),
            messages=[{'role': 'user',
                       'content': f"Documento: {nombre}\n{(texto or '')[:1500]}"}],
        )
        m = re.search(r'\d+', msg.content[0].text)
        if m:
            n = int(m.group())
            if 1 <= n <= 29:
                return n
    except Exception:
        return None
    return None
