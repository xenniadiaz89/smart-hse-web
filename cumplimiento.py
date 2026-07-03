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
