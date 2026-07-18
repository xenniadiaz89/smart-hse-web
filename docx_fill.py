"""Motor de relleno de plantillas .docx (Word) preservando el formato original.

La usuaria pidió que los documentos grandes (Programa/SGSST V8.2, RIOHS v4) se descarguen con el
formato Word idéntico al original. En vez de reconstruirlos en HTML, se rellena el .docx real:
- **Etiquetas de tabla**: donde el formato trae una tabla "Etiqueta | (vacío)" (Antecedentes de la
  Empresa), se escribe el valor en la celda contigua manteniendo su estilo.
- **Tokens** `{{clave}}`: reemplazo directo en párrafos y celdas, por si una plantilla los usa.

Las plantillas viven EN el repo (`plantillas_docx/`) para que funcione también en Render (el folder
DS44/ está fuera del repo). Devuelve los bytes del .docx para descargar/persistir.
"""
import io
import os
import unicodedata

PLANTILLAS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plantillas_docx')


def _norm(s):
    s = (s or '').lower().strip().rstrip(':').strip()
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def _set_cell_text(cell, valor):
    """Escribe `valor` en la celda conservando el estilo del primer run existente."""
    valor = '' if valor is None else str(valor)
    par = cell.paragraphs[0]
    if par.runs:
        par.runs[0].text = valor
        for r in par.runs[1:]:
            r.text = ''
    else:
        par.add_run(valor)


def _replace_tokens_paragraph(par, valores):
    """Reemplaza {{clave}} en un párrafo. Une los runs para no partir el token entre runs."""
    texto = par.text
    if '{{' not in texto:
        return
    nuevo = texto
    for k, v in valores.items():
        nuevo = nuevo.replace('{{' + k + '}}', '' if v is None else str(v))
    if nuevo != texto:
        if par.runs:
            par.runs[0].text = nuevo
            for r in par.runs[1:]:
                r.text = ''
        else:
            par.add_run(nuevo)


def rellenar(nombre_plantilla, valores=None, etiquetas=None):
    """Abre `plantillas_docx/<nombre_plantilla>`, rellena y devuelve (bytes, filename).
    - `valores`: dict para reemplazo de {{tokens}} (párrafos y tablas).
    - `etiquetas`: dict {texto_de_etiqueta_normalizado: valor} → rellena la celda contigua a la
      etiqueta en cualquier tabla (para tablas "Etiqueta | valor").
    Best-effort: si python-docx o la plantilla faltan, devuelve (None, None).
    """
    valores = valores or {}
    etiquetas_norm = {_norm(k): v for k, v in (etiquetas or {}).items()}
    ruta = os.path.join(PLANTILLAS_DIR, nombre_plantilla)
    if not os.path.exists(ruta):
        return None, None
    try:
        import docx
    except ImportError:
        return None, None
    try:
        d = docx.Document(ruta)
        for par in d.paragraphs:
            _replace_tokens_paragraph(par, valores)
        for tab in d.tables:
            for row in tab.rows:
                cells = row.cells
                for i, cell in enumerate(cells):
                    for par in cell.paragraphs:
                        _replace_tokens_paragraph(par, valores)
                    # tabla etiqueta|valor: si esta celda es una etiqueta conocida, rellena la siguiente
                    if etiquetas_norm and i + 1 < len(cells):
                        key = _norm(cell.text)
                        if key in etiquetas_norm and not cells[i + 1].text.strip():
                            _set_cell_text(cells[i + 1], etiquetas_norm[key])
        buf = io.BytesIO()
        d.save(buf)
        return buf.getvalue(), nombre_plantilla
    except Exception:      # noqa: BLE001 — best-effort; el pipeline degrada a HTML si falla
        return None, None


# ── Documentos .docx disponibles: mapea tipo_doc → plantilla + cómo auto-llenar desde la empresa ──
def _etiquetas_empresa(empresa):
    e = empresa or {}
    return {
        'razon social': e.get('razon_social'),
        'rut': e.get('rut_empresa'),
        'nombre representante legal': e.get('representante') or '',
        'domicilio comercial': e.get('direccion') or '',
        'organismo administrador ley': e.get('mutual') or '',
        'numero adherente mutual de seguridad': e.get('n_adherente') or '',
    }


DOCX = {
    'programa_sgsst': {
        'plantilla': 'programa_sgsst_v8.2.docx',
        'nombre': 'Programa Anual y SGSST',
        'items_fuf': [8, 9, 10, 11, 12, 13, 20],
        'campos': [{'k': 'periodo', 'label': 'Período (año)', 'tipo': 'text'}],
        'etiquetas': _etiquetas_empresa,
        'tokens': lambda empresa, campos: {
            'razon_social': (empresa or {}).get('razon_social') or '',
            'periodo': (campos or {}).get('periodo') or '',
        },
    },
}


def tipos_para_item(n):
    """Documentos .docx generables para el ítem FUF n (para el catálogo/UI del FUF)."""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return []
    return [{'tipo_doc': k, 'nombre': cfg['nombre'], 'campos': cfg.get('campos', []), 'formato': 'docx'}
            for k, cfg in DOCX.items() if n in cfg['items_fuf']]


def es_docx(tipo_doc):
    return tipo_doc in DOCX


def generar_docx(tipo_doc, empresa, campos=None):
    """Genera el .docx de `tipo_doc` auto-llenado desde la empresa. Devuelve (bytes, filename)."""
    cfg = DOCX.get(tipo_doc)
    if not cfg:
        return None, None
    etiquetas = cfg['etiquetas'](empresa) if callable(cfg.get('etiquetas')) else cfg.get('etiquetas')
    tokens = cfg['tokens'](empresa, campos) if callable(cfg.get('tokens')) else cfg.get('tokens')
    data, _ = rellenar(cfg['plantilla'], valores=tokens, etiquetas=etiquetas)
    if data is None:
        return None, None
    emp = (empresa or {}).get('razon_social') or 'empresa'
    return data, f"{cfg['nombre']} - {emp}.docx"
