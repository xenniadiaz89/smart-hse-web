"""Motor de Cumplimiento Inteligente — catálogo normativo y traducción legal→faena.

Módulo de responsabilidad única (Ronda 12). Contiene:
  - REGLAS_CUMPLIMIENTO: base legal + periodicidad + criticidad + ítem FUF por categoría.
  - DIALECTO_MANDANTE: estándar del mandante por categoría (Codelco Bow Tie/ECF, BHP IEC).
  - helpers de fecha (vencimiento/estado) puros, sin dependencia de la BD.

La siembra en tablas (`db.seed_reglas`) y la cascada viven en `db.py`/`app.py`; aquí solo
el conocimiento normativo y el cálculo, para poder escalar con nuevos módulos sin tocar el resto.
"""
from datetime import date


# ── Reglas de actualización + Cimiento Legal (DS 44 = base) ──
# categoria (llave común con resso.EQUIVALENCIAS) → regla.
REGLAS_CUMPLIMIENTO = {
    'programa_prp':     {'titulo': 'Programa de Trabajo Preventivo (Programa SSO)',
                         'base_legal': 'DS 44/2024 Art. 8 · Ley 16.744',
                         'periodicidad_meses': 12, 'es_critico': 1, 'fuf_item': 8},
    'iper':             {'titulo': 'Matriz IPER (MIPER)',
                         'base_legal': 'DS 44/2024 Art. 7 · Ley 16.744',
                         'periodicidad_meses': 12, 'es_critico': 1, 'fuf_item': 2},
    'reglamento':       {'titulo': 'Reglamento Interno (RIOHS)',
                         'base_legal': 'DS 44/2024 · Código del Trabajo Art. 153 · Ley 16.744',
                         'periodicidad_meses': 12, 'es_critico': 1, 'fuf_item': None},
    'irl':              {'titulo': 'Identificación de Requisitos Legales (IRL)',
                         'base_legal': 'DS 44/2024 Art. 64 · Ley 16.744',
                         'periodicidad_meses': 12, 'es_critico': 0, 'fuf_item': None},
    'odi':              {'titulo': 'ODI e inducciones',
                         'base_legal': 'DS 44/2024 Art. 15 · DS 40',
                         'periodicidad_meses': 12, 'es_critico': 0, 'fuf_item': 21},
    'epp':              {'titulo': 'Elementos de Protección Personal (EPP)',
                         'base_legal': 'DS 44/2024 Art. 13 · DS 594',
                         'periodicidad_meses': 12, 'es_critico': 0, 'fuf_item': 14},
    'plan_emergencia':  {'titulo': 'Plan de Emergencia',
                         'base_legal': 'DS 44/2024 Art. 19 · DS 594',
                         'periodicidad_meses': 12, 'es_critico': 0, 'fuf_item': 27},
    'riesgos_criticos': {'titulo': 'Listado RC, ECF y EST',
                         'base_legal': 'DS 44/2024 Art. 7 · Estándar mandante',
                         'periodicidad_meses': 12, 'es_critico': 1, 'fuf_item': None},
    'procedimientos':   {'titulo': 'Procedimientos e instructivos (PTS)',
                         'base_legal': 'DS 44/2024 Art. 10 · DS 594',
                         'periodicidad_meses': 24, 'es_critico': 0, 'fuf_item': 12},
}


# ── Dialecto de Prevención por mandante (traducción legal → faena) ──
DIALECTO_MANDANTE = {
    'codelco': {
        'programa_prp':     {'estandar': 'Programa SSO formalizado bajo SIGO-P004',
                             'metodologia': 'SIGO / Programa RESSO'},
        'iper':             {'estandar': 'MIPER con controles de RC vía Bow Tie (SIGO-P006)',
                             'metodologia': 'Bow Tie'},
        'riesgos_criticos': {'estandar': 'ECF y Estándares de Control de Fatalidades',
                             'metodologia': 'ECF / Riesgos Críticos Codelco'},
        'epp':              {'estandar': 'EPP según estándar Codelco de la División',
                             'metodologia': 'Estándar EPP Codelco'},
        'plan_emergencia':  {'estandar': 'Plan de Emergencia concordante con el de la División',
                             'metodologia': 'Plan concordante Codelco'},
        'procedimientos':   {'estandar': 'PTS aprobados según estándar SIGO',
                             'metodologia': 'SIGO-P'},
    },
    'bhp_spence': {
        'programa_prp':     {'estandar': 'Programa de Salud y Seguridad BHP',
                             'metodologia': 'BHP Operating System'},
        'iper':             {'estandar': 'Evaluación de Riesgos Materiales (IEC 31010)',
                             'metodologia': 'IEC 31010 · Riesgos Materiales'},
        'riesgos_criticos': {'estandar': 'Controles de Riesgos Materiales y de Fatalidad',
                             'metodologia': 'Material Risks / Critical Controls'},
        'epp':              {'estandar': 'EPP según estándar BHP',
                             'metodologia': 'Estándar EPP BHP'},
        'plan_emergencia':  {'estandar': 'Plan de respuesta a emergencias BHP',
                             'metodologia': 'Emergency Management BHP'},
        'procedimientos':   {'estandar': 'Procedimientos según estándar BHP',
                             'metodologia': 'BHP Standards'},
    },
}


# ── Fuentes legales vigentes (Ronda 13) — cuerpo normativo al que se amarra cada requisito ──
FUENTES_LEGALES = [
    {'codigo': 'L16744', 'nombre': 'Ley 16.744 — Accidentes del Trabajo y Enfermedades Profesionales',
     'url': 'https://www.bcn.cl/leychile/navegar?idNorma=28650'},
    {'codigo': 'DS44', 'nombre': 'DS 44/2024 — Nueva gestión preventiva de riesgos laborales',
     'url': 'https://www.bcn.cl/leychile/navegar?idNorma=1205298'},
    {'codigo': 'DS594', 'nombre': 'DS 594 — Condiciones sanitarias y ambientales básicas',
     'url': 'https://www.bcn.cl/leychile/navegar?idNorma=167766'},
    {'codigo': 'DS76', 'nombre': 'DS 76 — SST en obras/faenas subcontratadas',
     'url': 'https://www.bcn.cl/leychile/navegar?idNorma=257601'},
    {'codigo': 'DS54', 'nombre': 'DS 54 — Comités Paritarios de Higiene y Seguridad',
     'url': 'https://www.bcn.cl/leychile/navegar?idNorma=8336'},
    {'codigo': 'L20123', 'nombre': 'Ley 20.123 — Subcontratación y servicios transitorios',
     'url': 'https://www.bcn.cl/leychile/navegar?idNorma=254080'},
    {'codigo': 'L21643', 'nombre': 'Ley 21.643 — Ley Karin (acoso y violencia laboral)',
     'url': 'https://www.bcn.cl/leychile/navegar?idNorma=1200096'},
    {'codigo': 'L21015', 'nombre': 'Ley 21.015 — Inclusión laboral de personas con discapacidad',
     'url': 'https://www.bcn.cl/leychile/navegar?idNorma=1103997'},
]


# ── Pilares normativos de la Matriz Legal (agrupación de la capa Core) ──
# El orden de este dict es el orden de render en el panel. 'OTROS' es un valor explícito y no
# None: matriz_legal.service usa `pilar IS NULL` como centinela del backfill, así que un pilar
# nulo legítimo dispararía UPDATEs en cada request.
PILARES = {
    'P1': 'Pilar 1 · Gestión Preventiva e Información de Riesgos Laborales — D.S. 44 Art. 13-16',
    'P2': 'Pilar 2 · Condiciones Sanitarias y Ambientales Básicas — D.S. 594',
    'P3': 'Pilar 3 · Prevención del Acoso y Violencia Laboral — Ley 21.643 (Karin)',
    'OTROS': 'Otros requisitos Core',
}

# Etiqueta breve del pilar, para la columna "Categoría" de la Matriz (el nombre largo no cabe).
PILARES_CORTOS = {
    'P1': 'Gestión Preventiva',
    'P2': 'Condiciones Sanitarias',
    'P3': 'Ley Karin',
    'OTROS': 'Otros',
}

# ── Matriz Legal — Capa Core (requisitos transversales VIGENTES, precarga obligatoria) ──
# Se inyectan al crear la empresa con is_mandatory=1 (bloqueados en Requisito/Cuerpo_Legal;
# editables en Estado_Avance, Evidencia_Notas, Responsable y Fecha_Vencimiento).
# control_operativo va en el formato estricto de lista numérica '1.\n<acción>\n2.\n<acción>\n'
# (ver matriz_legal.formato.normalizar_control_operativo). Los 8 deben tener pilar y control:
# un Core sin ellos reabriría el backfill en cada GET.
REQUISITOS_CORE = [
    {'id_requisito': 'CORE-01', 'origen': 'Legal Nacional', 'cuerpo_legal': 'Ley 16.744',
     'requisito': 'Adhesión a un Organismo Administrador del Seguro (mutualidad o ISL) y cotización vigente.',
     'frecuencia_actualizacion_meses': 12, 'pilar': 'OTROS', 'articulo': 'Art. 4 y 5',
     'control_operativo':
         '1.\nMantener vigente la adhesión al Organismo Administrador y su N° de adherente.\n'
         '2.\nArchivar el certificado de afiliación y las 3 constancias exigidas.\n'
         '3.\nVerificar el pago mensual de la cotización básica y adicional diferenciada.\n'},
    {'id_requisito': 'CORE-02', 'origen': 'Legal Nacional', 'cuerpo_legal': 'DS 44/2024',
     'requisito': 'Sistema de Gestión de SST implementado (política, MIPER, programa de trabajo y evaluación anual).',
     'frecuencia_actualizacion_meses': 12, 'pilar': 'P1', 'articulo': 'Art. 13',
     'control_operativo':
         '1.\nFormalizar la política de SST firmada por la gerencia y difundirla al personal.\n'
         '2.\nMantener el programa de trabajo anual con responsables y plazos.\n'
         '3.\nRealizar la evaluación anual del sistema y registrar sus conclusiones.\n'},
    {'id_requisito': 'CORE-03', 'origen': 'Legal Nacional', 'cuerpo_legal': 'DS 44/2024',
     'requisito': 'Matriz IPER elaborada, difundida y revisada al menos anualmente o ante cambios.',
     'frecuencia_actualizacion_meses': 12, 'pilar': 'P1', 'articulo': 'Art. 14 y 15',
     'control_operativo':
         '1.\nIdentificar peligros y evaluar riesgos por puesto de trabajo y tarea.\n'
         '2.\nDefinir medidas de control según la jerarquía (eliminación a EPP).\n'
         '3.\nRevisar la matriz al menos una vez al año o ante todo cambio de proceso.\n'
         '4.\nDifundir la matriz vigente a los trabajadores y dejar registro firmado.\n'},
    {'id_requisito': 'CORE-04', 'origen': 'Legal Nacional', 'cuerpo_legal': 'DS 44/2024',
     'requisito': 'Obligación de Informar los riesgos laborales (ODI) entregada y registrada a cada trabajador.',
     'frecuencia_actualizacion_meses': 12, 'pilar': 'P1', 'articulo': 'Art. 16',
     'control_operativo':
         '1.\nEntregar la ODI al ingreso y ante todo cambio de tarea o de riesgo.\n'
         '2.\nRegistrar la firma del trabajador y archivar el comprobante.\n'
         '3.\nRepetir la información al menos una vez al año.\n'},
    {'id_requisito': 'CORE-05', 'origen': 'Legal Nacional', 'cuerpo_legal': 'DS 594',
     'requisito': 'Condiciones sanitarias y ambientales básicas (agua potable, servicios higiénicos, EPP certificado).',
     'frecuencia_actualizacion_meses': 12, 'pilar': 'P2', 'articulo': 'Art. 12-27 y 53',
     'control_operativo':
         '1.\nAsegurar agua potable y servicios higiénicos suficientes según la dotación.\n'
         '2.\nMantener comedores y vestidores en las condiciones exigidas.\n'
         '3.\nEntregar EPP certificado y registrar su entrega por trabajador.\n'
         '4.\nControlar los agentes ambientales presentes contra los límites permisibles.\n'},
    {'id_requisito': 'CORE-06', 'origen': 'Legal Nacional', 'cuerpo_legal': 'DS 54 / Ley 16.744',
     'requisito': 'Comité Paritario de Higiene y Seguridad constituido cuando hay más de 25 trabajadores.',
     'frecuencia_actualizacion_meses': 24, 'pilar': 'OTROS', 'articulo': 'Art. 66 Ley 16.744',
     'control_operativo':
         '1.\nConstituir el CPHS por votación cuando la dotación llegue a 25 trabajadores.\n'
         '2.\nSesionar mensualmente y levantar acta de cada reunión.\n'
         '3.\nRenovar el comité cada 2 años.\n'},
    {'id_requisito': 'CORE-07', 'origen': 'Legal Nacional', 'cuerpo_legal': 'Ley 21.643 (Karin)',
     'requisito': 'Protocolo de prevención del acoso sexual, laboral y violencia en el trabajo, incorporado al RIOHS.',
     'frecuencia_actualizacion_meses': 12, 'pilar': 'P3', 'articulo': 'Art. 1 y 2',
     'control_operativo':
         '1.\nIncorporar el protocolo de prevención del acoso y la violencia al RIOHS.\n'
         '2.\nDifundir el protocolo y el canal de denuncia a toda la dotación.\n'
         '3.\nCapacitar a jefaturas en la aplicación del procedimiento de investigación.\n'
         '4.\nDerivar toda denuncia a la DT o investigar en plazo máximo de 30 días.\n'},
    {'id_requisito': 'CORE-08', 'origen': 'Legal Nacional', 'cuerpo_legal': 'Ley 21.015 / 21.690',
     'requisito': 'Cumplimiento de inclusión laboral: reserva del 1% de puestos en empresas de 100 o más trabajadores.',
     'frecuencia_actualizacion_meses': 12, 'pilar': 'OTROS', 'articulo': 'Art. 157 bis CdT',
     'control_operativo':
         '1.\nVerificar si la dotación alcanza 100 trabajadores y activa la reserva del 1%.\n'
         '2.\nRegistrar los contratos de personas con discapacidad en la DT.\n'
         '3.\nEnviar la comunicación electrónica anual a la Dirección del Trabajo.\n'},
]


# ── Cruce automático dotación → aplicabilidad de requisitos Core ──
# La dotación declarada en el onboarding determina si CORE-06 y CORE-08 son exigibles.
# Los umbrales y su fundamento son datos; el writer vive en db.aplicar_reglas_dotacion().
REGLAS_DOTACION = [
    {'id_requisito': 'CORE-06', 'umbral': 25,
     'fundamento': 'Dotación declarada: {n} trabajadores (inferior a 25). La constitución del Comité '
                   'Paritario de Higiene y Seguridad es exigible desde 25 trabajadores '
                   '(Art. 66 Ley 16.744 / DS 54). No aplica.'},
    {'id_requisito': 'CORE-08', 'umbral': 100,
     'fundamento': 'Dotación declarada: {n} trabajadores (inferior a 100). La reserva del 1% de puestos '
                   'para personas con discapacidad rige desde 100 trabajadores (Ley 21.015). No aplica.'},
]


def dialecto_key(mandante):
    """Normaliza el mandante a su dialecto. None → solo base legal (sin traducción)."""
    m = (mandante or '').lower()
    if 'codelco' in m:
        return 'codelco'
    if 'spence' in m or 'bhp' in m:
        return 'bhp_spence'
    return None


# ── Cálculo de vencimiento / estado (puro) ──
def calcular_vencimiento(fecha_aprobacion, periodicidad_meses):
    """fecha_aprobacion (ISO) + N meses → ISO. None si no hay fecha."""
    if not fecha_aprobacion:
        return None
    try:
        d = date.fromisoformat(fecha_aprobacion[:10])
    except (TypeError, ValueError):
        return None
    meses = periodicidad_meses or 12
    y = d.year + (d.month - 1 + meses) // 12
    mth = (d.month - 1 + meses) % 12 + 1
    import calendar
    day = min(d.day, calendar.monthrange(y, mth)[1])
    return date(y, mth, day).isoformat()


def estado_cumplimiento(fecha_vencimiento, dias_aviso=30, hoy=None):
    """'pendiente_actualizacion' si venció, 'por_vencer' si ≤ dias_aviso, si no 'vigente'."""
    if not fecha_vencimiento:
        return 'vigente'
    try:
        v = date.fromisoformat(fecha_vencimiento[:10])
    except (TypeError, ValueError):
        return 'vigente'
    hoy = hoy or date.today()
    dias = (v - hoy).days
    if dias < 0:
        return 'pendiente_actualizacion'
    if dias <= dias_aviso:
        return 'por_vencer'
    return 'vigente'


# ── Catálogo normativo de Capacitaciones Legales (FUF 44 + SST Chile) — marca blanca SMART HSE ──
# Cada curso mapea (cuando aplica) a un requisito de la Matriz Legal: al completarse (evidencia de
# aprobación) el sistema marca ese ítem como 'Cumple' de forma cruzada. `req_idreq` = código CORE exacto;
# `req_kw` = palabra clave de respaldo para requisitos operativos/sectoriales.
CURSOS_LEGALES = [
    {'codigo': 'CAP-019', 'nombre': 'Capacitación teórica y práctica en EPP',
     'base_legal': 'D.S. 44 / FUF P.19', 'req_idreq': 'CORE-05', 'req_kw': 'epp'},
    {'codigo': 'CAP-018', 'nombre': 'Información de Riesgos Laborales / IRL (ODI)',
     'base_legal': 'D.S. 44 Art. 16', 'req_idreq': 'CORE-04', 'req_kw': 'informar'},
    {'codigo': 'CAP-023', 'nombre': 'Manejo Manual de Carga',
     'base_legal': 'Ley 20.001 / D.S. 63', 'req_idreq': None, 'req_kw': 'manejo manual'},
    {'codigo': 'CAP-024', 'nombre': 'Conducción a la defensiva y seguridad vial',
     'base_legal': 'Programa FYS / riesgos del IRL', 'req_idreq': None, 'req_kw': 'conduc'},
    {'codigo': 'CAP-025', 'nombre': 'Protocolo de Riesgo Psicosocial / CEAL-SM',
     'base_legal': 'SUSESO (cuando aplique)', 'req_idreq': None, 'req_kw': 'psicosocial'},
    {'codigo': 'CAP-021', 'nombre': 'Agentes físicos / PREXOR (Ruido)',
     'base_legal': 'D.S. 594 / PREXOR', 'req_idreq': None, 'req_kw': 'ruido'},
    {'codigo': 'CAP-022', 'nombre': 'Ley Karin (acoso y violencia laboral)',
     'base_legal': 'Ley 21.643', 'req_idreq': 'CORE-07', 'req_kw': 'karin'},
]


def curso_legal_match(texto):
    """Devuelve el curso del catálogo que corresponde al texto (por código o nombre), o None."""
    cl = (texto or '').lower()
    for c in CURSOS_LEGALES:
        if c['codigo'].lower() in cl or c['nombre'].lower() in cl:
            return c
    return None
