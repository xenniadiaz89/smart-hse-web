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
        'clave': 'silice',
        'nombre': 'SÍLICE — Autoevaluación Gestión de Factores de Riesgo/Agentes de Enfermedades Profesionales',
        'protocolo_match': 'PLANESI (Sílice)',
        'norma': 'MINSAL · Protocolo de Vigilancia del Ambiente y de la Salud de los Trabajadores con Exposición a Sílice',
        'tipo': 'autoevaluacion',
        'campos': [
            {'k': 'centro_trabajo', 'label': 'Nombre centro de trabajo a evaluar (CT)', 'tipo': 'text'},
            {'k': 'direccion_centro', 'label': 'Dirección centro de trabajo', 'tipo': 'text'},
            {'k': 'comuna_centro', 'label': 'Comuna centro de trabajo', 'tipo': 'text'},
            {'k': 'n_trabajadores_centro', 'label': 'N° trabajadores centro de trabajo', 'tipo': 'text'},
            {'k': 'responsable_centro', 'label': 'Nombre responsable centro de trabajo', 'tipo': 'text'},
            {'k': 'cargo_responsable', 'label': 'Cargo', 'tipo': 'text'},
            {'k': 'experto_prp', 'label': 'Nombre experto prevención de riesgos', 'tipo': 'text'},
            {'k': 'fecha', 'label': 'Fecha', 'tipo': 'date'},
        ],
        'secciones': [
            {'titulo': '1. Identificación, difusión y estrategia de gestión del riesgo',
             'items': [
                 'El agente de riesgo sílice libre cristalizada, ¿se incluye dentro de la Identificación de Peligros y Evaluación de Riesgos (IPER) y en el Reglamento Interno de Orden, Higiene y Seguridad (RIOHS) de la empresa/centro de trabajo?',
                 'Si la empresa tiene más de 50 trabajadores y se rige por la Ley N°20.123 de Subcontratación, ¿tiene un Sistema de Gestión de Seguridad y Salud en el Trabajo (SGSST) en el que se haya identificado el agente sílice e incorporado las Directrices Específicas sobre SGSST para empresas con Riesgo de Exposición a sílice, publicadas por la OIT, MINSAL y MINTRAB?',
                 '¿Se realiza la difusión del SGSST por exposición a sílice a todos los estamentos de la empresa?',
                 '¿Se realiza la difusión del Protocolo de Vigilancia del Ambiente y de la Salud de los trabajadores con exposición a sílice?',
                 '¿El Comité Paritario de Higiene y Seguridad (CPHS) incorpora en su cronograma de trabajo actividades relacionadas con la prevención de la silicosis?',
                 '¿Los trabajadores han sido informados acerca de los riesgos asociados a la inhalación de sustancias que contienen sílice libre cristalizada, de las medidas preventivas y de los métodos de trabajo correctos?',
                 'Si existen áreas con exposición a sílice cristalizada, ¿se informó de esta condición a empresas contratistas y subcontratistas que desarrollan labores en éstas, para que gestionen el riesgo?',
             ]},
            {'titulo': '2. Gestión de vigilancia ambiental y vigilancia de salud',
             'items': [
                 '¿Cuenta con Evaluación Cualitativa de exposición a sílice realizada por el organismo administrador?',
                 '¿Cuenta con Evaluación Cuantitativa de exposición a sílice realizada por el organismo administrador?',
                 '¿Se informaron los resultados de las Evaluaciones Cualitativas y/o Cuantitativas al CPHS, trabajadores y representantes, en el plazo de 7 días contados desde la recepción del informe?',
                 '¿Existe un Plan de Trabajo y Carta Gantt que considere la ejecución de cada una de las medidas de control prescritas en las Evaluaciones Cualitativas y/o Cuantitativas, o aquellas definidas por la empresa?',
                 '¿Los trabajadores calificados como expuestos, ya sea cualitativa o cuantitativamente, se encuentran en Programa de Vigilancia de Salud?',
                 '¿Se dispone de información histórica respecto de trabajadores detectados con silicosis y a qué Grupo de Exposición Similar (GES) pertenecían?',
                 '¿Se han efectuado reducciones de concentraciones de sílice en la(s) fuente(s) de emisión que tuvieron o tienen incidencia sobre los GES donde se han identificado enfermos ocupacionales con silicosis?',
             ]},
            {'titulo': '3. Aplicación de medidas de control ingenieriles',
             'items': [
                 '¿Se han implementado las prescripciones del organismo administrador en el informe de Evaluación Cualitativa, dentro de los plazos establecidos?',
                 '¿Se han implementado las prescripciones del organismo administrador en el informe de Evaluación Cuantitativa, dentro de los plazos establecidos?',
                 '¿Se ha efectuado la reevaluación Cuantitativa de sílice dentro del plazo legal?',
                 '¿Se redujo el número de expuestos a sílice?',
                 '¿Se han implementado las prescripciones del organismo administrador (Reevaluación Cuantitativa) para el control de sílice en las fuentes, dentro del plazo legal?',
                 '¿Se están actualizando los indicadores que muestren la mejora continua?',
             ]},
            {'titulo': '4. Aplicación de medidas de control administrativas',
             'items': [
                 '¿Se han implementado las prescripciones del organismo administrador en la Evaluación Cualitativa, para el control de la exposición a sílice con medidas administrativas?',
                 '¿Se han implementado las prescripciones del organismo administrador en la Evaluación Cuantitativa, para el control de la exposición a sílice con medidas administrativas?',
             ]},
            {'titulo': '5. Gestión de protección personal',
             'items': [
                 '¿Existe un Programa escrito de Selección y Control de Elementos de Protección Respiratoria (EPR), según lo establece la Guía del Instituto de Salud Pública (ISP)?',
                 '¿Se realizó difusión del Programa de Protección Respiratoria?',
                 '¿Se seleccionaron los EPR considerando los criterios establecidos en la Guía del Instituto de Salud Pública?',
                 '¿Existe orden técnica para la adquisición de EPR?',
                 '¿Existe stock en bodega coincidente con la orden técnica?',
                 '¿Se realiza capacitación a los distintos niveles de profesionales encargados de la selección, adquisición y entrega de estos Elementos de Protección Respiratoria?',
                 '¿Se realiza capacitación práctica a los trabajadores en el uso, cuidado y reconocimiento de necesidad de renovación de los EPR?',
             ]},
            {'titulo': '6. Plan de mejora contínua',
             'items': [
                 '¿Se evalúan permanentemente los avances en la reducción de concentraciones de sílice y de la exposición de los trabajadores?',
                 '¿Se ha profundizado en la identificación o cuantificación del riesgo por exposición a sílice, a través de mediciones de fuentes y realización de mapas de exposición?',
                 '¿Existe un documento de evaluación y cierre anual del Sistema de Gestión y Mejora Continua, revisado y firmado por jefaturas de la empresa/centro de trabajo?',
             ]},
        ],
    },
    {
        'clave': 'tmert',
        'nombre': 'TMERT-EESS — Autoevaluación Gestión de Factores de Riesgo/Agentes de Enfermedades Profesionales',
        'protocolo_match': 'TMERT-EESS',
        'norma': 'MINSAL · Protocolo de Vigilancia Ocupacional de Trabajadores Expuestos a Factores de Riesgo de Trastorno Musculoesquelético (Res. Exenta N°1660, 06.12.2024)',
        'tipo': 'autoevaluacion',
        'campos': [
            {'k': 'centro_trabajo', 'label': 'Nombre centro de trabajo a evaluar (CT)', 'tipo': 'text'},
            {'k': 'direccion_centro', 'label': 'Dirección centro de trabajo', 'tipo': 'text'},
            {'k': 'comuna_centro', 'label': 'Comuna centro de trabajo', 'tipo': 'text'},
            {'k': 'n_trabajadores_centro', 'label': 'N° trabajadores centro de trabajo', 'tipo': 'text'},
            {'k': 'responsable_centro', 'label': 'Nombre responsable centro de trabajo', 'tipo': 'text'},
            {'k': 'cargo_responsable', 'label': 'Cargo', 'tipo': 'text'},
            {'k': 'experto_prp', 'label': 'Nombre experto prevención de riesgos', 'tipo': 'text'},
            {'k': 'fecha', 'label': 'Fecha', 'tipo': 'date'},
        ],
        'secciones': [
            {'titulo': '1. Etapa inicial',
             'items': [
                 '¿Existe un Programa de Gestión del Riesgo de vigilancia ocupacional por exposición a factores de riesgo para Trastornos Musculoesqueléticos (TMERT)?',
                 '¿Existe una Carta Gantt con la planificación de la implementación de todas las etapas del protocolo TMERT?',
                 '¿Existe un comité de implementación del protocolo TMERT, que considere el modelo de ergonomía participativa integrando a las jefaturas, Departamento de Prevención de Riesgos (PRP), Comité Paritario de Higiene y Seguridad (CPHS) y trabajadores?',
                 '¿El CPHS ha incorporado en su cronograma de trabajo las actividades relacionadas con el control de la implementación del Protocolo TMERT?',
                 '¿Existe un programa de capacitación que considere formar competencias en las jefaturas, PRP, CPHS y trabajadores, según lo establecido en el protocolo TMERT?',
                 '¿Los profesionales Expertos en Prevención de Riesgos han participado y aprobado el curso de 20 horas del protocolo TMERT dictado por el Organismo Administrador (OAL)?',
                 '¿El centro de trabajo ha realizado la difusión del Protocolo TMERT a los trabajadores?',
             ]},
            {'titulo': '2. Caracterización del puesto de trabajo',
             'items': [
                 '¿Se efectúa el registro del Anexo I: Caracterización del puesto de trabajo, antecedentes de la empresa, centro de trabajo, puesto de trabajo, descripción de tareas e infraestructura y equipos, en el 100% de los puestos del centro de trabajo?',
             ]},
            {'titulo': '3. Identificación inicial y avanzada',
             'items': [
                 '¿Aplica la Tabla de Identificación Inicial en todos los puestos de trabajo?',
                 '¿Aplica la Tabla de Identificación Avanzada-Condición Aceptable en todos los puestos de trabajo que presentaron factores de riesgo en la Identificación Inicial?',
                 '¿Notifica al organismo administrador sobre los puestos de trabajo que presentaron Condición No Aceptable?',
                 '¿Envía al organismo administrador el listado de trabajadores que componen el Grupo de Exposición Similar (GES) de los puestos de trabajo que presentaron Condición No Aceptable?',
                 '¿Aplica la Tabla de Identificación Avanzada-Condición Crítica en todos los puestos de trabajo que presentaron Condiciones No Aceptables?',
                 '¿Notifica al organismo administrador los puestos de trabajo que presentaron Condiciones Críticas?',
                 '¿Comunica a los trabajadores el nivel de riesgo de los puestos de trabajo, después de aplicar las tablas de Condición Crítica?',
                 '¿Implementa medidas de control en puestos de trabajo con Condiciones Críticas en el plazo de 90 días?',
                 '¿Realiza la Re-Identificación con las Tablas de Identificación Avanzada-Condición Aceptable?',
             ]},
            {'titulo': '4. Evaluación inicial',
             'items': [
                 '¿Aplica las metodologías de evaluación inicial del riesgo TMERT en tareas de puestos de trabajo con Condición No Crítica (riesgo intermedio) y con Condición Crítica no subsanadas en la Re-Identificación del riesgo?',
                 '¿Comunica a los trabajadores el nivel de riesgo de las tareas donde se aplicó la Evaluación Inicial TMERT?',
                 '¿Realiza seguimiento de la implementación de medidas de control en tareas de puestos de trabajo con nivel de riesgo Medio, Alto y No Aceptable en un plazo de 90 días?',
                 '¿Se ha verificado el cumplimiento de las medidas de control prescritas en un plazo de 90 días?',
                 '¿Realiza la Re-Evaluación Inicial en tareas que en la Verificación de Cumplimiento obtuvieron resultados (1,2) según criterio SUSESO?',
             ]},
            {'titulo': '5. Evaluación avanzada',
             'items': [
                 '¿Aplica las metodologías de Evaluación Avanzada del riesgo en tareas con nivel de riesgo Medio/Alto/No Aceptable que no fueron subsanadas en la Re-Evaluación Inicial, y en tareas donde el resultado de la verificación de cumplimiento sea (3,4) según criterio SUSESO?',
                 '¿Comunica a los trabajadores el nivel de riesgo de las tareas donde se aplicó la Evaluación Avanzada TMERT?',
                 '¿Realiza seguimiento de la implementación de medidas de control en las tareas de los puestos de trabajo con nivel de riesgo Medio y Alto en un plazo de 90 días?',
                 '¿Se ha verificado el cumplimiento de las medidas de control prescritas en un plazo de 90 días para medidas de control administrativas y 180 días para medidas de control ingenieriles?',
                 '¿Realiza la Re-Evaluación Avanzada en tareas que en la Verificación de Cumplimiento obtuvieron resultados (1,2) según criterio SUSESO?',
             ]},
        ],
    },
    {
        'clave': 'mmc',
        'nombre': 'Manejo Manual de Cargas — Autoevaluación Gestión de Factores de Riesgo/Agentes de Enfermedades Profesionales',
        'protocolo_match': 'MMC (Manejo Manual de Cargas)',
        'norma': 'MINTRAB · Actualización Guía Técnica de Evaluación y Control de Riesgos Asociados al Manejo Manual de Carga (R.E. N°22, D.O. 10-02-2018)',
        'tipo': 'autoevaluacion',
        'campos': [
            {'k': 'centro_trabajo', 'label': 'Nombre centro de trabajo a evaluar (CT)', 'tipo': 'text'},
            {'k': 'direccion_centro', 'label': 'Dirección centro de trabajo', 'tipo': 'text'},
            {'k': 'comuna_centro', 'label': 'Comuna centro de trabajo', 'tipo': 'text'},
            {'k': 'n_trabajadores_centro', 'label': 'N° trabajadores centro de trabajo', 'tipo': 'text'},
            {'k': 'responsable_centro', 'label': 'Nombre responsable centro de trabajo', 'tipo': 'text'},
            {'k': 'cargo_responsable', 'label': 'Cargo', 'tipo': 'text'},
            {'k': 'experto_prp', 'label': 'Nombre experto prevención de riesgos', 'tipo': 'text'},
            {'k': 'fecha', 'label': 'Fecha', 'tipo': 'date'},
        ],
        'secciones': [
            {'titulo': '1. Etapa inicial',
             'items': [
                 '¿Se realiza la difusión asociada al Manejo Manual de Carga/Manejo Manual de Pacientes (MMC/MMP) que considere jefaturas, Comité Paritario de Higiene y Seguridad (CPHS) y trabajadores?',
                 '¿Las jefaturas y supervisores, Expertos en Prevención de Riesgos y CPHS cuentan con capacitación teórico-práctica, según lo establecido en la Guía Técnica?',
                 '¿Tiene un Programa de Gestión de Riesgos de MMC/MMP?',
                 '¿Tiene una Carta Gantt para la implementación de MMC/MMP?',
                 '¿El CPHS incorpora en su cronograma de trabajo actividades relacionadas con MMC/MMP?',
             ]},
            {'titulo': '2. Identificación inicial/avanzada',
             'items': [
                 '¿Existe identificación inicial para todos los puestos de trabajo con MMC/MMP (Tablas 1 y 2)?',
                 '¿Existe identificación avanzada de MMC en los puestos de trabajo con respuesta "Sí" en alguna de las preguntas de la Tabla 2?',
                 '¿Existe Plan de Acción correctivo para la eliminación y/o disminución del riesgo cuando existan condiciones críticas?',
                 '¿Se incluye la participación del CPHS, sindicatos y/o representantes de los trabajadores en la gestión del riesgo de MMC/MMP en las etapas de identificación y propuesta de medidas de control?',
             ]},
            {'titulo': '3. Tabla de identificación inicial y avance',
             'items': [
                 '¿Se cumplen los plazos para la aplicación de la Tabla de Identificación Inicial y Avance según lo señalado en la Guía Técnica? (30 días para micro/pequeña/mediana empresa <200 trabajadores; 90 días para grandes empresas ≥200 trabajadores)',
                 '¿Se realiza seguimiento en la implementación de medidas de control para las condiciones críticas, en el plazo de 60 días, o hasta 180 días si fue fundamentado por el OAL (tamaño de la empresa o característica de la condición crítica)?',
                 '¿Se realiza la Re-identificación del riesgo, si corresponde?',
             ]},
            {'titulo': '4. Evaluación inicial (MAC/VMAC/RAPP)',
             'items': [
                 '¿Existen evaluaciones de riesgo con la metodología correspondiente según árbol de decisión (MAC/VMAC/RAPP), en tareas críticas no subsanadas?',
                 '¿Se realiza seguimiento en la implementación de medidas de control para tareas con puntaje mayor a 5?',
                 '¿Se realiza la Re-evaluación del riesgo con método MAC/VMAC/RAPP, si corresponde?',
             ]},
            {'titulo': '5. Plan de acción',
             'items': [
                 '¿Se genera un Plan de Acción correctivo para tareas con puntaje mayor a 5 MAC/RAPP, específicamente en factores de riesgo rojo (obligatorio) y amarillo, que finaliza en el plazo de 60 días?',
             ]},
            {'titulo': '6. Evaluación avanzada (MAPO/IL NIOSH/Tablas Liberty Mutual/LT-ISO)',
             'items': [
                 '¿Existen evaluaciones de riesgo avanzadas con método (MAPO, IL NIOSH, Tablas Liberty Mutual, LT-ISO) en tareas no subsanadas en la re-evaluación del riesgo con métodos de evaluación inicial, realizadas por un profesional Ergónomo capacitado en un curso de 40 horas?',
                 '¿Se genera un Plan de Acción correctivo para tareas con nivel alto (MAPO) o nivel 3 (PTAI), que finaliza en el plazo de 90 días?',
             ]},
            {'titulo': '7. Seguimiento de implementación de medidas de control',
             'items': [
                 '¿Existe seguimiento de implementación de medidas de control en tareas con factores de riesgo rojo y amarillo para MAPO/LT-ISO/Tablas Liberty Mutual/IL NIOSH?',
                 '¿Se realiza la Re-evaluación del riesgo con método IL NIOSH/LT-ISO/Tablas Liberty Mutual/MAPO, según corresponda?',
             ]},
            {'titulo': '8. Asegurar',
             'items': [
                 '¿Se verifica el permanente uso seguro y eficiente de las nuevas medidas o soluciones, y la eficiencia y eficacia de las medidas de control implementadas?',
             ]},
        ],
    },
    {
        'clave': 'ruv_solar',
        'nombre': 'RUV Solar — Autoevaluación Gestión de Factores de Riesgo/Agentes de Enfermedades Profesionales',
        'protocolo_match': 'RUV (Radiación UV)',
        'norma': 'MINSAL · Guía Técnica de Radiación UV de Origen Solar (Ley N°20.096, Art. 109 b D.S. N°594)',
        'tipo': 'autoevaluacion',
        'campos': [
            {'k': 'centro_trabajo', 'label': 'Nombre centro de trabajo a evaluar (CT)', 'tipo': 'text'},
            {'k': 'direccion_centro', 'label': 'Dirección centro de trabajo', 'tipo': 'text'},
            {'k': 'comuna_centro', 'label': 'Comuna centro de trabajo', 'tipo': 'text'},
            {'k': 'n_trabajadores_centro', 'label': 'N° trabajadores centro de trabajo', 'tipo': 'text'},
            {'k': 'responsable_centro', 'label': 'Nombre responsable centro de trabajo', 'tipo': 'text'},
            {'k': 'cargo_responsable', 'label': 'Cargo', 'tipo': 'text'},
            {'k': 'experto_prp', 'label': 'Nombre experto prevención de riesgos', 'tipo': 'text'},
            {'k': 'fecha', 'label': 'Fecha', 'tipo': 'date'},
        ],
        'secciones': [
            {'titulo': '1. Identificación, difusión y estrategia de gestión del riesgo',
             'items': [
                 '¿El agente de riesgo RUV Solar se incluye dentro de la Identificación de Peligros y Evaluación de Riesgos (IPER) y en el Reglamento Interno de Orden, Higiene y Seguridad (RIOHS) de la empresa/centro de trabajo?',
                 '¿Se realiza difusión de la Guía Técnica de RUV Solar a personal de prevención, miembros del CPHS, sindicatos, trabajadores y empleadores?',
                 '¿Se cuenta con un Programa de Protección y Prevención contra la exposición a RUV Solar?',
                 '¿Se cuenta con un Programa de Capacitación teórico-práctico para los trabajadores expuestos a RUV Solar?',
                 '¿Se informa a los trabajadores del riesgo, las medidas de control y los métodos correctos de trabajo?',
                 '¿Se tiene incorporado en su Sistema de Gestión de Seguridad y Salud en el Trabajo (SGSST) el riesgo de exposición a RUV Solar?',
                 'Si existen áreas con exposición a RUV Solar, ¿se informó de esta condición a empresas contratistas y subcontratistas que desarrollan labores en éstas, para que gestionen el riesgo?',
             ]},
            {'titulo': '2. Documentación remitida a la autoridad',
             'items': [
                 '¿Se remitió el registro de la difusión de la Guía Técnica RUV Solar a la Seremi de Salud e Inspección del Trabajo correspondiente?',
             ]},
            {'titulo': '3. Gestión de vigilancia ambiental',
             'items': [
                 '¿Se cuenta con Evaluación Cualitativa de exposición a RUV Solar realizada por el organismo administrador?',
                 '¿Existe un Plan de Trabajo y Carta Gantt que considere la ejecución de cada una de las medidas de control prescritas por el organismo administrador y/o aquellas definidas por la empresa?',
                 '¿El personal se encuentra libre de signos evidentes de la exposición, tales como piel enrojecida, descamada o con ampollas producto de quemaduras solares?',
             ]},
            {'titulo': '4. Aplicación de medidas de control ingenieriles',
             'items': [
                 '¿Se han implementado las medidas prescritas por el organismo administrador para el control de la exposición a RUV Solar, dentro de los plazos establecidos?',
                 '¿Los lugares donde se realizan operaciones continuas cuentan con techos o láminas protectoras de RUV que efectivamente protejan de la RUV Solar?',
                 '¿Los vehículos o equipos operados al aire libre cuentan con cabinas, parabrisas y vidrios laterales con láminas reductoras de RUV-A?',
                 'En las faenas y/o tareas con exposición a RUV Solar, ¿se considera la implementación de medidas tendientes a disminuir los tiempos de exposición?',
             ]},
            {'titulo': '5. Aplicación de medidas de control administrativas',
             'items': [
                 '¿Se publica diariamente al personal que se expone al sol, en lugares visibles, información actualizada de los índices de RUV Solar, las medidas de control que se deben aplicar y los elementos de protección personal, por medio de letreros o semáforo calibrado según colores?',
             ]},
            {'titulo': '6. Gestión de protección personal',
             'items': [
                 '¿Se dispone y usan elementos de protección personal en la realización de operaciones con exposición directa a RUV Solar?',
                 '¿Se realizó difusión del Programa de Protección y Prevención contra la exposición a RUV Solar?',
                 '¿Existe stock de elementos de protección personal en bodega?',
                 '¿Se realiza capacitación a los distintos niveles de profesionales encargados de la selección, adquisición y entrega de estos elementos de protección RUV Solar?',
                 '¿Se realiza capacitación práctica de los trabajadores en el uso, cuidado y reconocimiento de necesidad de renovación?',
             ]},
            {'titulo': '7. Plan de mejora contínua',
             'items': [
                 '¿Se evalúan permanentemente los avances en el control de la exposición a RUV Solar?',
                 '¿Existe un documento de Evaluación del Sistema de Gestión y Mejora Continua, revisado y firmado por jefaturas del centro de trabajo?',
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
