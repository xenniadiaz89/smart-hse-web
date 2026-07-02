"""Catálogo RESSO Anexo 2 — Reunión de Arranque (Carpeta de Arranque, 29 ítems)
y definición de los campos de Información General del contrato."""

# Información General del contrato (RESSO Anexo 2). (key, etiqueta)
INFO_GENERAL_CAMPOS = [
    ('gerencia',          'Gerencia Administradora del Contrato'),
    ('superintendencia',  'Superintendencia / Dirección'),
    ('empresa_contratista', 'Nombre Empresa Contratista'),
    ('nombre_servicio',   'Nombre del contrato / servicio'),
    ('admin_eecc',        'Administrador Contrato EE.CC.'),
    ('admin_eecc_tel',    'Teléfono Administrador EE.CC.'),
    ('admin_eecc_mail',   'Correo Administrador EE.CC.'),
    ('experto_eecc',      'Experto en Prevención EE.CC.'),
    ('experto_eecc_tel',  'Teléfono Experto EE.CC.'),
    ('experto_eecc_mail', 'Correo Experto EE.CC.'),
    ('fecha_inicio',      'Fecha de Inicio del Contrato'),
    ('fecha_termino',     'Fecha Término del Contrato'),
    ('n_trabajadores',    'N° de trabajadores'),
    ('n_trabajadores_bel', 'N° de trabajadores BEL'),
    ('n_riesgos_criticos', 'N° de Riesgos Críticos aplicables'),
    ('organismo_seguro',  'Organismo Administrador del Seguro'),
    ('n_subcontratistas', 'N° Empresas Subcontratistas'),
    ('admin_codelco',     'Administrador Contrato CODELCO'),
    ('experto_codelco',   'Experto en Prevención CODELCO'),
]

# Carpeta de Arranque: 29 ítems del Anexo 2 (n, título corto de carpeta, evidencia, a quién).
CARPETA_ARRANQUE = [
    (1,  'Carta de inicio SERNAGEOMIN', 'Copia carta de inicio de actividades (Art. 21 D.S.72) y respaldo de ingreso a plataforma Sernageomin.', 'S. Acreditación'),
    (2,  'Contrato y resolución Jefe Prevención', 'Copia de contrato y resolución del Servicio de Salud/Sernageomin del Jefe de Depto. de Prevención.', 'Adm. Ctto.'),
    (3,  'Autorización jornada de trabajo', 'Resolución de autorización de jornada de trabajo (Dirección del Trabajo).', 'S. Acreditación'),
    (4,  'Toma de conocimiento RESSO', 'Registro reunión de inicio (Anexo 1) — Representante Legal y Administrador toman conocimiento del RESSO.', 'Adm. Ctto.'),
    (5,  'Contratos de trabajo', 'Contrato de trabajo vigente (Art. 10 Código del Trabajo) de cada trabajador, asociado al N° de contrato.', 'S. Acreditación'),
    (6,  'Cursos prevención supervisores', 'Certificados curso prevención de riesgos para supervisores (8 hrs), organismo certificado.', 'Adm. Ctto.'),
    (7,  'Exámenes preocupacionales', 'Exámenes preocupacionales de salud y aptitud de cada trabajador, organismo certificado y vigente.', 'S. Acreditación'),
    (8,  'Exámenes específicos (drogas)', 'Exámenes de drogas ilícitas por organismo certificado, sin observaciones (≤ 1 mes antes de la revisión).', 'Adm. Ctto.'),
    (9,  'Fatiga y somnolencia / Alcohol y drogas', 'Programa de gestión de fatiga y somnolencia / alcohol y drogas.', 'Adm. Ctto.'),
    (10, 'RIOHS autorizado SEREMI', 'RIOHS vigente autorizado por SEREMI (DS 40) y copia de recepción de cada trabajador.', 'Adm. Ctto.'),
    (11, 'Calificaciones y certificaciones', 'Certificaciones de competencias (rigger, altura física, operadores, soldadores, electricistas, etc.).', 'Adm. Ctto.'),
    (12, 'ODI e inducciones', 'Registro ODI trazable con matriz IPER + inducción Persona Nueva Divisional + inducción área específica.', 'S. Acreditación'),
    (13, 'Conductores acreditados', 'Listado conductores (Workmate), licencias internas/municipales y examen psicosensotécnico riguroso vigente.', 'S. Acreditación'),
    (14, 'Vehículos del contrato', 'Listado de vehículos y registro de validación por fiscalización de terceros (ingreso a faena).', 'S. Acreditación / Adm. Ctto.'),
    (15, 'Acta constitución CPHS', 'Acta de constitución del Comité Paritario (cuando aplique según DS 54).', 'Adm. Ctto.'),
    (16, 'Certificado de afiliación', 'Certificado de afiliación a organismo administrador (Ley 16.744): giro, tasa cotización y siniestralidad.', 'S. Acreditación'),
    (17, 'Libro de Obras (LOD)', 'Respaldo de apertura del Libro de Obras (papel o sistema de cartas contractuales).', 'Adm. Ctto.'),
    (18, 'Programa de Prevención de Riesgos', 'Programa PRP según los 12 elementos del SGSST corporativo, formalizado con firmas.', 'Adm. Ctto.'),
    (19, 'Mapa de procesos y Matriz IPER', 'Mapa de procesos trazable con matriz IPER (SIGO-P006), con controles de RC vía Bow Tie.', 'Adm. Ctto.'),
    (20, 'Requisitos legales', 'Registro de identificación de requisitos legales actualizado y aplicable al contrato.', 'Adm. Ctto.'),
    (21, 'Plan de Emergencia', 'Identificación de emergencias y Plan de Emergencia concordante con el de Codelco en el área.', 'Adm. Ctto.'),
    (22, 'Listado RC, ECF y EST', 'Registro de identificación de Riesgos Críticos, ECF y EST aplicables, formalizado con firmas.', 'Adm. Ctto.'),
    (23, 'Elementos de protección personal', 'Estudio de EPP según puesto de trabajo y certificados de calidad de los EPP.', 'Adm. Ctto.'),
    (24, 'Lavado de ropa de seguridad', 'Contrato con lavandería industrial y resolución sanitaria (si hay exposición a contaminantes).', 'Adm. Ctto.'),
    (25, 'Subcontratistas', 'Autorización del Administrador de Contrato y documentación (puntos 1–23) de cada subcontratista.', 'S. Acreditación'),
    (26, 'Documento de inicio de faena', 'Documento de inicio de faena: registro fotográfico y planos de la instalación de faena.', 'Adm. Ctto.'),
    (27, 'Plan de cierre de instalaciones', 'Plan de cierre de instalaciones (restitución de drenajes, retiro de residuos, etc.).', 'Adm. Ctto.'),
    (28, 'Procedimientos e instructivos', 'Procedimientos/instructivos de trabajo con difusión y evaluación de entendimiento por trabajador.', 'Adm. Ctto.'),
    (29, 'Otros documentos de la faena', 'Otros documentos específicos del centro de trabajo (especificar).', 'Adm. Ctto.'),
]

CARPETA_DICT = {n: {'n': n, 'titulo': t, 'evidencia': e, 'a_quien': q}
                for (n, t, e, q) in CARPETA_ARRANQUE}

# Palabras clave por ítem para clasificar documentos por nombre/contenido.
KEYWORDS = {
    1:  ['carta inicio', 'inicio actividades', 'sernageomin', 'ds72', 'art 21'],
    2:  ['resolucion jefe', 'jefe departamento', 'jefe prevencion', 'resolucion prevencion'],
    3:  ['jornada', 'autorizacion jornada', 'direccion del trabajo', 'jornada excepcional'],
    4:  ['toma conocimiento', 'resso', 'reunion inicio', 'anexo 1'],
    5:  ['contrato de trabajo', 'contrato trabajo', 'contrato trabajador', 'articulo 10', 'contrato laboral'],
    6:  ['curso supervisor', 'curso prevencion', '8 horas', '8 hrs', 'curso supervisores'],
    7:  ['preocupacional', 'examen preocupacional', 'aptitud', 'examen salud', 'altura fisica'],
    8:  ['drogas', 'alcohol y drogas', 'examen drogas', 'toxicologico', 'narcotest'],
    9:  ['fatiga', 'somnolencia', 'programa fatiga', 'alcohol y drogas programa'],
    10: ['riohs', 'reglamento orden higiene', 'reglamento interno', 'ds 40', 'seremi'],
    11: ['rigger', 'certificacion', 'competencia', 'soldador', 'electricista', 'operador', 'calificacion'],
    12: ['odi', 'obligacion de informar', 'induccion', 'persona nueva', 'induccion area'],
    13: ['conductor', 'licencia', 'psicosensotecnico', 'licencia interna', 'workmate'],
    14: ['vehiculo', 'camioneta', 'patente', 'ingreso vehiculo', 'validacion vehiculo'],
    15: ['cphs', 'comite paritario', 'acta constitucion', 'paritario'],
    16: ['afiliacion', 'organismo administrador', 'mutual', 'achs', 'ist', 'cotizacion', 'siniestralidad'],
    17: ['libro de obras', 'lod', 'libro obra', 'apertura libro'],
    18: ['programa prevencion', 'programa de prevencion', 'prp', 'sgsst', '12 elementos'],
    19: ['matriz iper', 'iper', 'mapa de procesos', 'bow tie', 'identificacion de peligros'],
    20: ['requisitos legales', 'requisito legal', 'matriz legal', 'identificacion requisitos'],
    21: ['plan de emergencia', 'emergencia', 'plan emergencia'],
    22: ['riesgos criticos', 'controles criticos', 'ecf', 'est', 'rc ecf', 'control critico'],
    23: ['epp', 'proteccion personal', 'estudio epp', 'certificado epp'],
    24: ['lavanderia', 'lavado de ropa', 'resolucion sanitaria lavanderia'],
    25: ['subcontratista', 'subcontrato', 'autorizacion subcontratista'],
    26: ['inicio de faena', 'instalacion de faena', 'registro fotografico', 'planos faena'],
    27: ['plan de cierre', 'cierre de instalaciones', 'restitucion'],
    28: ['procedimiento', 'instructivo', 'pts', 'difusion', 'evaluacion entendimiento'],
    29: ['otros', 'varios', 'anexo', 'adicional'],
}


def carpeta_lista():
    return [dict(CARPETA_DICT[n]) for n in sorted(CARPETA_DICT)]


def es_codelco(mandante):
    return 'codelco' in (mandante or '').lower()


# ─────────────────────────────────────────────────────────────────────────
# RONDA 7 — Herencia Carpeta de Arranque ↔ Auditoría RESSO
# ─────────────────────────────────────────────────────────────────────────
# Mapa de equivalencias: cada categoría conecta un ítem de la Carpeta de
# Arranque con su punto equivalente en la Auditoría RESO (código tipo B.x.y).
EQUIVALENCIAS = {
    'reglamento':      {'carpeta': 10, 'reso': 'B.2.1', 'titulo': 'Reglamento Interno (RIOHS)'},
    'odi':             {'carpeta': 12, 'reso': 'B.2.5', 'titulo': 'ODI e inducciones'},
    'programa_prp':    {'carpeta': 18, 'reso': 'B.5.7', 'titulo': 'Programa de Prevención de Riesgos'},
    'iper':            {'carpeta': 19, 'reso': 'B.4.1', 'titulo': 'Mapa de procesos y Matriz IPER'},
    'irl':             {'carpeta': 20, 'reso': 'B.5.1', 'titulo': 'Identificación de Requisitos Legales (IRL)'},
    'plan_emergencia': {'carpeta': 21, 'reso': 'B.7.1', 'titulo': 'Plan de Emergencia'},
    'riesgos_criticos':{'carpeta': 22, 'reso': 'B.4.3', 'titulo': 'Listado RC, ECF y EST'},
    'epp':             {'carpeta': 23, 'reso': 'B.6.2', 'titulo': 'Elementos de Protección Personal'},
    'procedimientos':  {'carpeta': 28, 'reso': 'B.3.4', 'titulo': 'Procedimientos e instructivos'},
}

# Catálogo de puntos de la Auditoría RESSO (derivado de las equivalencias).
AUDITORIA_RESSO = [
    {'punto_key': m['reso'], 'titulo': m['titulo'], 'categoria': cat,
     'evidencia': CARPETA_DICT.get(m['carpeta'], {}).get('evidencia', '')}
    for cat, m in sorted(EQUIVALENCIAS.items(), key=lambda kv: kv[1]['reso'])
]

# Índices inversos categoria ↔ ítem/código.
_CAT_POR_ITEM = {m['carpeta']: cat for cat, m in EQUIVALENCIAS.items()}
_CAT_POR_RESO = {m['reso']: cat for cat, m in EQUIVALENCIAS.items()}


def categoria_de_carpeta(item_n):
    return _CAT_POR_ITEM.get(item_n)


def categoria_de_reso(codigo):
    return _CAT_POR_RESO.get(codigo)


def reso_de_categoria(categoria):
    m = EQUIVALENCIAS.get(categoria)
    return m['reso'] if m else None


def auditoria_lista():
    return [dict(p) for p in AUDITORIA_RESSO]


# ── Declaración de Aplicabilidad: ECF / RC / EST ──
ECF_RC_EST = {
    'RC': [
        {'codigo': 'RC-01', 'titulo': 'Caída de personas a distinto nivel'},
        {'codigo': 'RC-02', 'titulo': 'Contacto con energías peligrosas (eléctrica/mecánica)'},
        {'codigo': 'RC-03', 'titulo': 'Vehículos y equipos móviles'},
        {'codigo': 'RC-04', 'titulo': 'Izaje y operaciones de levante'},
        {'codigo': 'RC-05', 'titulo': 'Sustancias peligrosas'},
        {'codigo': 'RC-06', 'titulo': 'Espacios confinados'},
    ],
    'ECF': [
        {'codigo': 'ECF-01', 'titulo': 'Estándar de Control de Fatalidad — Caída de altura'},
        {'codigo': 'ECF-02', 'titulo': 'Estándar de Control de Fatalidad — Energías peligrosas'},
        {'codigo': 'ECF-03', 'titulo': 'Estándar de Control de Fatalidad — Vehículos y tránsito'},
    ],
    'EST': [
        {'codigo': 'EST-01', 'titulo': 'Estándar de trabajo en altura física'},
        {'codigo': 'EST-02', 'titulo': 'Estándar de bloqueo y señalización'},
    ],
}


def aplicabilidad_lista():
    """Devuelve el catálogo ECF/RC/EST aplanado con su tipo."""
    out = []
    for tipo, items in ECF_RC_EST.items():
        for it in items:
            out.append({'tipo': tipo, **it})
    return out


# ── Requisitos por rol (Formulario de Trabajadores) ──
# Cada rol exige capacitaciones/exámenes; se cruzan con ítems de la Carpeta.
REQUISITOS_POR_ROL = {
    'todos': [
        {'req': 'Contrato de trabajo vigente', 'carpeta': 5},
        {'req': 'Examen preocupacional', 'carpeta': 7},
        {'req': 'Examen de drogas y alcohol', 'carpeta': 8},
        {'req': 'ODI e inducción', 'carpeta': 12},
        {'req': 'Recepción RIOHS', 'carpeta': 10},
    ],
    'supervisor': [
        {'req': 'Curso prevención de riesgos supervisores (8 h)', 'carpeta': 6},
    ],
    'conductor': [
        {'req': 'Licencia interna/municipal vigente', 'carpeta': 13},
        {'req': 'Examen psicosensotécnico riguroso vigente', 'carpeta': 13},
    ],
    'operador': [
        {'req': 'Certificación de competencias del equipo', 'carpeta': 11},
    ],
}


def requisitos_de_rol(rol):
    """Requisitos aplicables a un rol = comunes ('todos') + los propios del rol."""
    rol_key = (rol or '').strip().lower()
    reqs = list(REQUISITOS_POR_ROL['todos'])
    for k, extra in REQUISITOS_POR_ROL.items():
        if k != 'todos' and k in rol_key:
            reqs += extra
    return reqs
