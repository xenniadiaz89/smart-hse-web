"""Módulo 5 — Carpeta de auditoría: reúne en un solo índice todo lo que la empresa puede
presentar ante una fiscalización, y —esto es lo que la hace útil— también lo que NO puede.

Solo depende de db/fuf — nunca de app.py ni de otro módulo (aislamiento por carpeta).

Por qué existe: los documentos ya se venían guardando con su categoría (FUF, PROTOCOLO, CPHS) y
su ítem, pero repartidos entre las vistas que los produjeron. Un fiscalizador no pregunta por
módulos: pide la carpeta. Aquí se arma esa carpeta.

La pieza de valor no es el listado, es el bloque de BRECHAS. Un ítem del FUF marcado "Cumple"
sin ningún documento detrás es exactamente lo que se cae en una auditoría, y hasta ahora no
había forma de verlo.
"""
import re

import db
import fuf

# Los bloques de la carpeta, en el orden en que se presentan y se exportan. El `slug` es el
# nombre de la subcarpeta dentro del .zip, numerado para que el orden se conserve al descomprimir.
BLOQUES = [
    {'clave': 'fuf', 'nombre': 'FUF · D.S. 44', 'slug': '01 FUF DS 44',
     'desc': 'Evidencia y documentos generados por cada ítem del formulario único de fiscalización.'},
    {'clave': 'protocolos', 'nombre': 'Protocolos de Salud', 'slug': '02 Protocolos de Salud',
     'desc': 'Autoevaluaciones y formularios oficiales de los protocolos MINSAL.'},
    {'clave': 'cphs', 'nombre': 'Comité Paritario', 'slug': '03 Comite Paritario',
     'desc': 'Actas de constitución y de reuniones del comité.'},
    {'clave': 'irl', 'nombre': 'Nómina · IRL', 'slug': '04 Nomina IRL',
     'desc': 'Información de Riesgos Laborales entregada a cada persona trabajadora.'},
    {'clave': 'legal', 'nombre': 'Documentos legales', 'slug': '05 Documentos legales',
     'desc': 'Documentos con periodicidad legal y su vigencia.'},
]

_CATEGORIAS_PROPIAS = {'FUF', 'PROTOCOLO', 'CPHS'}


def _limpiar(nombre, largo=90):
    """Nombre seguro para una entrada de .zip: sin separadores de ruta ni caracteres de control."""
    n = re.sub(r'[\\/:*?"<>|\r\n\t]', '-', (nombre or '').strip()) or 'documento'
    return n[:largo]


def _doc(d, subtitulo=None):
    """Proyección uniforme de un documento para el índice (sin el blob)."""
    return {
        'id': d.get('id'), 'nombre': d.get('nombre') or f"documento_{d.get('id')}",
        'fecha': d.get('fecha'), 'flujo': d.get('flujo') or '', 'tipo': d.get('tipo') or '',
        'mimetype': d.get('mimetype') or '', 'item_n': d.get('item_n'),
        'es_referencia': bool(d.get('ref_doc_id')), 'subtitulo': subtitulo,
        'vencimiento': d.get('fecha_vencimiento'), 'estado': d.get('estado_cumplimiento'),
    }


# ─────────────────────────────── Bloques ───────────────────────────────
def _bloque_fuf(eid, rut, cid):
    """Documentos del FUF agrupados por ítem, con el enunciado y la norma de cada uno."""
    estados = db.estados_fuf(eid)
    por_item = {}
    for d in db.docs_por_categoria(cid, 'FUF'):
        por_item.setdefault(d.get('item_n'), []).append(d)

    grupos, brechas = [], []
    for n in range(1, fuf.TOTAL + 1):
        info = fuf.INDEX.get(n) or {}
        item = info.get('item') or {}
        estado = ((estados.get(n) or {}).get('estado')) or 'pendiente'
        docs = por_item.get(n, [])
        if docs:
            grupos.append({
                'ref': n, 'titulo': f'Ítem {n:02d}', 'detalle': item.get('t', ''),
                'norma': item.get('art', ''), 'seccion': info.get('seccion', ''),
                # Subcarpeta dentro del bloque: el .zip queda ordenado por sección del FUF, que es
                # como el fiscalizador recorre el formulario.
                'subcarpeta': info.get('seccion', ''),
                'estado': estado, 'docs': [_doc(d) for d in docs],
            })
        # La brecha que importa: dice cumplir y no hay nada que lo respalde.
        if estado == 'si' and not docs:
            brechas.append({'ref': n, 'gravedad': 'alta',
                            'texto': f'Ítem {n} marcado «Cumple» sin ningún documento de respaldo.',
                            'detalle': item.get('t', '')})
        elif estado == 'no':
            brechas.append({'ref': n, 'gravedad': 'media',
                            'texto': f'Ítem {n} declarado «No cumple».',
                            'detalle': item.get('t', '')})
    return grupos, brechas


def _bloque_protocolos(eid, rut, cid):
    por_proto = {}
    for d in db.docs_por_categoria(cid, 'PROTOCOLO'):
        por_proto.setdefault(d.get('item_n'), []).append(d)
    grupos, brechas = [], []
    for p in db.protocolos_de(eid):
        docs = por_proto.get(p['id'], [])
        if docs:
            grupos.append({'ref': p['id'], 'titulo': p['nombre'], 'detalle': '',
                           'docs': [_doc(d) for d in docs]})
        else:
            brechas.append({'ref': p['id'], 'gravedad': 'media',
                            'texto': f"Protocolo «{p['nombre']}» sin ningún documento cargado.",
                            'detalle': ''})
    return grupos, brechas


def _bloque_cphs(eid, rut, cid):
    comite = db.comite_de(eid)
    if not comite:
        return [], []
    por_act = {}
    for d in db.docs_por_categoria(cid, 'CPHS'):
        por_act.setdefault(d.get('item_n'), []).append(d)
    grupos, brechas = [], []
    for a in db.actividades_de(comite['id']):
        docs = por_act.get(a['id'], [])
        etiqueta = (a.get('titulo') or a.get('tipo') or 'Actividad').replace('_', ' ')
        if docs:
            grupos.append({'ref': a['id'], 'titulo': f"{a.get('fecha') or ''} · {etiqueta}".strip(' ·'),
                           'detalle': '', 'docs': [_doc(d) for d in docs]})
        elif (a.get('tipo') or '').startswith('reunion'):
            brechas.append({'ref': a['id'], 'gravedad': 'media',
                            'texto': f"Reunión del {a.get('fecha') or 's/fecha'} sin acta adjunta.",
                            'detalle': etiqueta})
    return grupos, brechas


def _bloque_irl(eid, rut, cid):
    """Los IRL cuelgan del contrato base, pero su índice vive en IRLGenerado: sin él no se sabe
    de quién es cada uno ni cuál quedó obsoleto tras versionar la matriz."""
    grupos, brechas = [], []
    for t in db.trabajadores_de(eid, solo_activos=True):
        irls = db.irls_de_trabajador(t['id']) or []
        if not irls:
            brechas.append({'ref': t['id'], 'gravedad': 'media',
                            'texto': f"{t.get('nombre') or t.get('rut')} sin IRL generado.",
                            'detalle': t.get('cargo') or ''})
            continue
        docs = []
        for irl in irls:
            if not irl.get('doc_id'):
                continue
            marca = ' · requiere nueva firma' if irl.get('requiere_refirma') else ''
            docs.append({'id': irl['doc_id'],
                         'nombre': f"IRL {t.get('nombre') or t.get('rut')}.html",
                         'fecha': irl.get('fecha') or irl.get('creado'),
                         'flujo': 'generado', 'tipo': 'irl', 'mimetype': 'text/html',
                         'item_n': None, 'es_referencia': False,
                         'subtitulo': f"Matriz V{irl.get('matriz_version') or '—'}{marca}",
                         'vencimiento': None, 'estado': None})
            if irl.get('requiere_refirma'):
                brechas.append({'ref': t['id'], 'gravedad': 'alta',
                                'texto': f"IRL de {t.get('nombre') or t.get('rut')} requiere nueva "
                                         'firma: la matriz cambió después de emitirlo (Art. 15 DS 44).',
                                'detalle': ''})
        if docs:
            grupos.append({'ref': t['id'], 'titulo': t.get('nombre') or t.get('rut'),
                           'detalle': t.get('rut') or '', 'docs': docs})
    return grupos, brechas


def _bloque_legal(eid, rut, cid):
    """Documentos con periodicidad legal (registrar_documento_legal): categorías que no son las
    tres propias del sistema."""
    grupos = []
    vistos = {}
    for d in db.documentos_de(cid):
        cat = d.get('categoria')
        if not cat or cat in _CATEGORIAS_PROPIAS:
            continue
        vistos.setdefault(cat, []).append(d)
    brechas = []
    for cat, docs in sorted(vistos.items()):
        grupos.append({'ref': cat, 'titulo': cat, 'detalle': '',
                       'docs': [_doc(d) for d in docs]})
        for d in docs:
            if d.get('estado_cumplimiento') == 'pendiente_actualizacion':
                brechas.append({'ref': cat, 'gravedad': 'alta',
                                'texto': f'«{cat}» vencido: requiere actualización.',
                                'detalle': d.get('fecha_vencimiento') or ''})
    return grupos, brechas


_ARMADORES = {'fuf': _bloque_fuf, 'protocolos': _bloque_protocolos, 'cphs': _bloque_cphs,
              'irl': _bloque_irl, 'legal': _bloque_legal}


# ─────────────────────────────── Índice ───────────────────────────────
def indice(empresa_id, rut):
    """Todo lo que la carpeta contiene y todo lo que le falta. Es la fuente de la vista y del zip.

    Cada bloque se arma dentro de su propio try: si uno falla —porque un módulo del que depende
    está caído— la carpeta se entrega igual con el resto y el bloque queda marcado en error, en
    vez de dejar al usuario sin carpeta justo cuando la necesita.
    """
    cid = db.contrato_base(empresa_id, rut)
    bloques, brechas, total = [], [], 0
    for meta in BLOQUES:
        try:
            grupos, brechas_b = _ARMADORES[meta['clave']](empresa_id, rut, cid)
            error = None
        except Exception as e:      # noqa: BLE001 — un bloque roto no puede tumbar la carpeta
            grupos, brechas_b, error = [], [], str(e)[:160]
        n_docs = sum(len(g['docs']) for g in grupos)
        total += n_docs
        bloques.append({**meta, 'grupos': grupos, 'n_docs': n_docs,
                        'n_grupos': len(grupos), 'error': error})
        brechas.extend({**b, 'bloque': meta['nombre']} for b in brechas_b)

    emp = db.empresa_de(rut, empresa_id) or {}
    return {
        'empresa': {'razon_social': emp.get('razon_social'), 'rut': emp.get('rut_empresa'),
                    'mutual': emp.get('mutual')},
        'bloques': bloques,
        'brechas': brechas,
        'resumen': {
            'documentos': total,
            'brechas': len(brechas),
            'brechas_altas': sum(1 for b in brechas if b['gravedad'] == 'alta'),
            'bloques_con_contenido': sum(1 for b in bloques if b['n_docs']),
        },
    }


def ruta_zip(bloque, grupo, doc, usados):
    """Ruta de un documento dentro del .zip, sin colisiones de nombre.

    Si el grupo declara `subcarpeta` (las secciones del FUF), se interpone un nivel: el bloque
    queda ordenado igual que el formulario que recorre el fiscalizador.
    """
    tramos = [bloque['slug']]
    if grupo.get('subcarpeta'):
        tramos.append(_limpiar(grupo['subcarpeta'], 70))
    tramos.append(_limpiar(grupo['titulo'], 70))
    carpeta = '/'.join(tramos)
    base = _limpiar(doc['nombre'])
    ruta = f'{carpeta}/{base}'
    if ruta in usados:
        raiz, punto, ext = base.rpartition('.')
        i = 2
        while ruta in usados:
            alt = f'{raiz} ({i}){punto}{ext}' if punto else f'{base} ({i})'
            ruta = f'{carpeta}/{alt}'
            i += 1
    usados.add(ruta)
    return ruta
