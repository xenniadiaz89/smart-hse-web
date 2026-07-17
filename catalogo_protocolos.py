"""Plantillas Maestras de los Protocolos de Vigilancia MINSAL/SUSESO, enlazadas al Panel de
Protocolos de Salud. Extiende el motor documental del FUF (catalogo_documentos_ds44) a las
autoevaluaciones de vigilancia: el sistema toma los datos de la Empresa y la Nómina (Módulo 0),
precarga la carátula, el prevencionista responde la autoevaluación y el sistema genera el
documento con formato legal para firmar y subir a la carpeta del Módulo 5.

Alcance y criterio (acordado con el usuario):
  • MEZCLA — CEAL-SM (Riesgo Psicosocial) NO se reproduce (instrumento con derechos SUSESO): es
    de tipo 'carga', el usuario sube el cuestionario oficial y el sistema le adjunta la carátula
    auto-rellenada. PREXOR y TMERT se reproducen como LISTA DE AUTOEVALUACIÓN desde el estándar
    público (los requisitos que el empleador debe acreditar), marcada como REFERENCIA editable —
    el experto valida y ajusta antes de firmar. No es copia textual de ningún formulario.

Dato puro, como fuf.py / catalogo_documentos_ds44.py: no es Blueprint ni toca la BD.
Fase actual: PREXOR completo + CEAL-SM (carga). TMERT queda como entrada preparada para la
ronda siguiente (misma estructura: un dict + sus ítems).

Estructura de una Plantilla Maestra:
  {'clave': 'prexor', 'nombre': '<título>', 'protocolo_match': '<nombre del ProtocoloSalud>',
   'norma': '<referencia legal>', 'tipo': 'autoevaluacion' | 'carga',
   'campos': [{'k','label','tipo'}],            # datos que el usuario completa (responsable, fecha, dB…)
   'secciones': [{'titulo', 'items': ['<requisito a acreditar>', ...]}]}   # solo 'autoevaluacion'
"""

from catalogo_documentos_ds44 import _documento_html, _esc


# ─────────────────────────── Auto-llenado empresa + nómina ───────────────────────────
def prefill(empresa, nomina):
    """Carátula precargada desde la Empresa y la Nómina (Módulo 0). `nomina` = lista de
    trabajadores (dicts de db.trabajadores_de); se usa el conteo de activos."""
    empresa = empresa or {}
    activos = sum(1 for t in (nomina or []) if (t.get('estado') or 'activo') == 'activo')
    return {
        'razon_social': empresa.get('razon_social') or '',
        'rut_empresa': empresa.get('rut_empresa') or '',
        'mutual': empresa.get('mutual') or '',
        'n_adherente': empresa.get('n_adherente') or '',
        'rubro': empresa.get('rubro') or '',
        'dotacion': empresa.get('dotacion') or '',
        'trabajadores_activos': activos,
    }


def _tabla_caratula(pf, campos):
    filas = [
        ('Razón social', pf.get('razon_social')),
        ('RUT empresa', pf.get('rut_empresa')),
        ('Organismo Administrador (Mutual)', pf.get('mutual')),
        ('N° adherente', pf.get('n_adherente')),
        ('Rubro / actividad', pf.get('rubro')),
        ('Dotación declarada', pf.get('dotacion')),
        ('Trabajadores activos (nómina)', pf.get('trabajadores_activos')),
    ]
    valores = pf.get('_valores', {})
    for c in campos:
        filas.append((c['label'], valores.get(c['k'], '')))
    return filas


# ─────────────────────── Render de una autoevaluación (checklist) ───────────────────────
def _plantilla_autoevaluacion(maestra, campos, respuestas, empresa, nomina):
    """campos: dict de valores de los campos del usuario. respuestas: {'<sec>-<idx>': {'estado','obs'}}."""
    pf = prefill(empresa, nomina)
    valores = {c['k']: (campos.get(c['k']) or '') for c in maestra.get('campos', [])}
    refs = [(k, v) for k, v in _tabla_caratula({**pf, '_valores': valores}, maestra.get('campos', []))]

    bloques = []
    n_cumple = n_no = n_na = 0
    for si, sec in enumerate(maestra.get('secciones', [])):
        filas = []
        for ii, item in enumerate(sec['items']):
            r = (respuestas or {}).get(f'{si}-{ii}') or {}
            est = (r.get('estado') or '').lower()
            obs = r.get('obs') or ''
            if est == 'si':
                badge, n_cumple = '<b style="color:#2e7d32">Cumple</b>', n_cumple + 1
            elif est == 'no':
                badge, n_no = '<b style="color:#c62828">No cumple</b>', n_no + 1
            elif est == 'na':
                badge, n_na = '<b style="color:#666">No aplica</b>', n_na + 1
            else:
                badge = '<span style="color:#999">—</span>'
            filas.append(
                f'<tr><td style="width:26px;color:#999">{ii + 1}</td><td>{_esc(item)}</td>'
                f'<td style="width:90px;text-align:center">{badge}</td>'
                f'<td style="width:200px;color:#555">{_esc(obs)}</td></tr>')
        bloques.append(
            f'<h2>{_esc(sec["titulo"])}</h2>'
            f'<table class="chk"><thead><tr><th>#</th><th>Requisito a acreditar</th>'
            f'<th>Estado</th><th>Observación / evidencia</th></tr></thead><tbody>{"".join(filas)}</tbody></table>')

    evaluables = n_cumple + n_no
    pct = round(100 * n_cumple / evaluables) if evaluables else 0
    responsable = valores.get('responsable') or '__________________'
    cuerpo = f"""
 <style>table.chk{{width:100%;border-collapse:collapse;margin:6px 0 14px;font-size:12px}}
  table.chk th{{background:#f0f6f9;text-align:left;padding:5px 7px;border-bottom:2px solid #cfe3ec;color:#006a9b}}
  table.chk td{{padding:5px 7px;border-bottom:1px solid #eee;vertical-align:top}}</style>
 <p><b>Resultado de la autoevaluación:</b> {n_cumple} cumple · {n_no} no cumple · {n_na} no aplica ·
    <b>{pct}% de cumplimiento</b> sobre los requisitos evaluables.</p>
 {''.join(bloques)}
 <p style="font-size:11px;color:#888">Documento de autoevaluación de referencia. Los ítems reproducen los
    requisitos del estándar MINSAL; revíselos y ajústelos a su realidad antes de firmar. No sustituye las
    mediciones ni la vigilancia de la salud del Organismo Administrador.</p>
 <div class="firma">{_esc(responsable)}<br><span class="sub">Responsable del programa — {_esc(pf.get('razon_social') or 'Empresa')}</span></div>"""
    return _documento_html(maestra['nombre'], maestra['norma'], empresa, cuerpo, refs=refs)


def generar_html(clave, campos, respuestas, empresa, nomina):
    m = INDEX.get(clave)
    if not m or m['tipo'] != 'autoevaluacion':
        return None
    return _plantilla_autoevaluacion(m, campos or {}, respuestas or {}, empresa or {}, nomina or [])


def caratula_carga_html(clave, campos, empresa, nomina):
    """Carátula auto-rellenada para las plantillas de tipo 'carga' (ej. CEAL-SM): acompaña al
    formulario oficial que sube el usuario."""
    m = INDEX.get(clave)
    if not m:
        return None
    pf = prefill(empresa, nomina)
    valores = {c['k']: (campos or {}).get(c['k'], '') for c in m.get('campos', [])}
    refs = _tabla_caratula({**pf, '_valores': valores}, m.get('campos', []))
    cuerpo = f"""
 <p>Carátula de aplicación del instrumento <b>{_esc(m['nombre'])}</b> ({_esc(m['norma'])}).</p>
 <p>El cuestionario oficial se aplica y se adjunta firmado. Esta carátula deja registro trazable de la
    empresa, el organismo administrador y la fecha de aplicación para la carpeta del Módulo 5.</p>"""
    return _documento_html(f'Carátula — {m["nombre"]}', m['norma'], empresa, cuerpo, refs=refs)


# ─────────────────────────────────── Catálogo ───────────────────────────────────
CATALOGO = [
    {
        'clave': 'prexor',
        'nombre': 'PREXOR — Autoevaluación de cumplimiento (Ruido)',
        'protocolo_match': 'PREXOR (Ruido)',
        'norma': 'MINSAL · Protocolo PREXOR (Exposición Ocupacional a Ruido)',
        'tipo': 'autoevaluacion',
        'campos': [
            {'k': 'responsable', 'label': 'Responsable del programa', 'tipo': 'text'},
            {'k': 'fecha', 'label': 'Fecha de la autoevaluación', 'tipo': 'date'},
            {'k': 'centro', 'label': 'Centro de trabajo / faena', 'tipo': 'text'},
        ],
        'secciones': [
            {'titulo': 'A. Gestión del programa',
             'items': [
                 'Se designó formalmente al responsable de la implementación del PREXOR en la empresa.',
                 'Se identificaron los puestos y trabajadores con exposición ocupacional a ruido.',
                 'Se cuenta con evaluación cuantitativa de la exposición a ruido (NPSeq / peak) del OAL o de higiene ocupacional.',
                 'Se elaboró e implementó el programa de vigilancia ambiental con mediciones periódicas según el nivel de acción.',
                 'Se aplicaron medidas de control según jerarquía (ingenieriles y administrativas antes que EPP).',
             ]},
            {'titulo': 'B. Vigilancia de la salud',
             'items': [
                 'Los trabajadores expuestos están incorporados al programa de vigilancia de la salud auditiva del OAL.',
                 'Se dispone del registro de audiometrías de base y de seguimiento de los trabajadores expuestos.',
                 'Se derivan al OAL los casos con hallazgos audiométricos (DTS / hipoacusia) para su evaluación.',
             ]},
            {'titulo': 'C. Protección personal, capacitación y registro',
             'items': [
                 'Se entrega protección auditiva certificada, adecuada al nivel de atenuación requerido.',
                 'Se capacita y difunde el PREXOR y el uso correcto de la protección auditiva a los trabajadores.',
                 'Se señalizan las zonas con nivel de presión sonora que exige uso obligatorio de protección auditiva.',
                 'Se archiva y mantiene disponible la documentación del programa para efectos de fiscalización.',
             ]},
        ],
    },
    {
        'clave': 'psicosocial',
        'nombre': 'CEAL-SM / SUSESO — Riesgo Psicosocial (carga del formulario oficial)',
        'protocolo_match': 'Riesgo Psicosocial (CEAL-SM/SUSESO)',
        'norma': 'SUSESO · Protocolo de Vigilancia de Riesgos Psicosociales (CEAL-SM)',
        'tipo': 'carga',
        'campos': [
            {'k': 'responsable', 'label': 'Responsable de la aplicación', 'tipo': 'text'},
            {'k': 'fecha', 'label': 'Fecha de aplicación', 'tipo': 'date'},
            {'k': 'comite', 'label': 'Comité de aplicación', 'tipo': 'text'},
        ],
    },
]

INDEX = {m['clave']: m for m in CATALOGO}
_POR_NOMBRE = {m['protocolo_match']: m for m in CATALOGO}


def por_protocolo(nombre):
    """Plantilla Maestra que corresponde al nombre de un ProtocoloSalud, o None."""
    return _POR_NOMBRE.get(nombre)


def resumen(maestra):
    """Lo que el front necesita para pintar la plantilla en la tarjeta del protocolo."""
    if not maestra:
        return None
    return {
        'clave': maestra['clave'], 'nombre': maestra['nombre'], 'norma': maestra['norma'],
        'tipo': maestra['tipo'], 'campos': maestra.get('campos', []),
        'secciones': [{'titulo': s['titulo'], 'items': s['items']}
                      for s in maestra.get('secciones', [])],
    }
