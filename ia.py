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


def inspeccionar_evidencia(minimos, contenido=None, mimetype=None):
    """Verifica que un documento subido contenga los elementos mínimos legales del ítem.
    Devuelve {'modo': 'ia'|'manual', 'items': [{'elemento','presente'|'estado'}], 'nota'} o None si
    no hay mínimos definidos. Best-effort: usa Claude si hay ANTHROPIC_API_KEY y texto extraíble;
    si no, entrega un checklist para verificación manual (no inventa cumplimiento)."""
    minimos = [m for m in (minimos or []) if m]
    if not minimos:
        return None
    texto = _texto_de(contenido, mimetype)
    if texto and os.environ.get('ANTHROPIC_API_KEY'):
        ia_res = _inspeccionar_claude(minimos, texto)
        if ia_res is not None:
            return ia_res
    return {'modo': 'manual',
            'items': [{'elemento': m, 'estado': 'por_verificar'} for m in minimos],
            'nota': 'Verifica manualmente que el documento contenga estos elementos mínimos que exige la ley.'}


def _inspeccionar_claude(minimos, texto):
    """Pregunta a Claude cuáles mínimos están presentes en el texto. Devuelve dict o None."""
    try:
        import anthropic
        import json as _json
    except ImportError:
        return None
    try:
        lista = "\n".join(f"- {m}" for m in minimos)
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=os.environ.get('SMARTHSE_IA_MODEL', 'claude-haiku-4-5'),
            max_tokens=400,
            system=("Eres un auditor SST chileno (DS 44). Te doy el texto de un documento y una lista "
                    "de elementos mínimos que la ley exige que contenga. Responde SOLO un JSON: "
                    '{"items":[{"elemento":"<texto>","presente":true|false}]} con un objeto por cada '
                    "elemento, en el mismo orden. No agregues nada fuera del JSON."),
            messages=[{'role': 'user',
                       'content': f"Elementos mínimos:\n{lista}\n\nTexto del documento:\n{texto[:6000]}"}],
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
