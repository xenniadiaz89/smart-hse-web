"""Catálogo de roles críticos y requisitos por rol (Módulo Trabajadores/Nómina).

Antes vivía dentro de resso.py junto al catálogo de auditoría RESSO (removido). Este archivo
conserva solo la parte que no depende de esa auditoría: qué exámenes/capacitaciones exige cada
rol de trabajador, motor usado por db.inyectar_requisitos_de_rol().
"""

# ── Requisitos por rol (Formulario de Trabajadores) ──
# Cada entrada tiene `codigo` (llave estable, no cambia aunque se edite el texto), `tipo` y
# `vigencia_meses` (None = no vence; el vencimiento se calcula con cumplimiento.calcular_vencimiento).
REQUISITOS_POR_ROL = {
    'todos': [
        {'codigo': 'DOC-CONTRATO', 'req': 'Contrato de trabajo vigente',
         'tipo': 'documento', 'vigencia_meses': None},
        {'codigo': 'EX-PREOCUP', 'req': 'Examen preocupacional',
         'tipo': 'examen', 'vigencia_meses': 12},
        {'codigo': 'EX-DROGAS', 'req': 'Examen de drogas y alcohol',
         'tipo': 'examen', 'vigencia_meses': 12},
        {'codigo': 'CAP-ODI', 'req': 'ODI e inducción',
         'tipo': 'capacitacion', 'vigencia_meses': 12},
        {'codigo': 'DOC-RIOHS', 'req': 'Recepción RIOHS',
         'tipo': 'documento', 'vigencia_meses': None},
    ],
    'supervisor': [
        {'codigo': 'CAP-SUP8H', 'req': 'Curso prevención de riesgos supervisores (8 h)',
         'tipo': 'capacitacion', 'vigencia_meses': 24},
    ],
    'conductor': [
        {'codigo': 'DOC-LICENCIA', 'req': 'Licencia interna/municipal vigente',
         'tipo': 'documento', 'vigencia_meses': 12},
        {'codigo': 'EX-PSICO', 'req': 'Examen psicosensotécnico riguroso vigente',
         'tipo': 'examen', 'vigencia_meses': 12},
    ],
    'operador': [
        {'codigo': 'CERT-EQUIPO', 'req': 'Certificación de competencias del equipo',
         'tipo': 'capacitacion', 'vigencia_meses': 24},
    ],
    # No es un rol del <select>: se gatilla por Trabajador.cphs_rol al ligar a la persona como
    # miembro del comité, igual que 'conduce' gatilla los requisitos de la Ley del Tránsito.
    'cphs': [
        {'codigo': 'CAP-CPHS-ORIENT',
         'req': 'Curso de orientación para miembros del CPHS (primer semestre del mandato)',
         'tipo': 'capacitacion', 'vigencia_meses': 24},
    ],
}

COD_CURSO_CPHS = 'CAP-CPHS-ORIENT'   # ítem FUF 31; lo lee db.miembros_con_curso()

# Roles críticos del <select> del alta. La llave debe coincidir con las de REQUISITOS_POR_ROL
# (el match de requisitos_de_rol() es por substring sobre el rol). 'trabajador' no añade extras:
# recibe solo los comunes de 'todos'.
ROLES_CRITICOS = {
    'trabajador': 'Trabajador',
    'supervisor': 'Supervisor',
    'conductor': 'Conductor',
    'operador': 'Operador de equipos',
}


def requisitos_de_rol(rol, conduce=False, cphs=False):
    """Requisitos aplicables a un rol = comunes ('todos') + los propios del rol.

    El match es por substring, así que 'Supervisor de Terreno' matchea 'supervisor'. Cada requisito
    sale con `origen` ('todos' o 'rol:<clave>') para poder distinguir, cuando alguien cambia de rol,
    cuáles dejaron de aplicarle (ver db.inyectar_requisitos_de_rol).
    """
    rol_key = (rol or '').strip().lower()
    reqs = [{**r, 'origen': 'todos'} for r in REQUISITOS_POR_ROL['todos']]
    for k, extra in REQUISITOS_POR_ROL.items():
        if k not in ('todos', 'cphs') and k in rol_key:   # 'cphs' no es un rol: se gatilla aparte
            reqs += [{**r, 'origen': f'rol:{k}'} for r in extra]
    # ¿Conduce? → requisitos de la Ley del Tránsito (18.290), aunque su rol no sea 'conductor'.
    if conduce and 'conductor' not in rol_key:
        reqs += [{**r, 'origen': 'conduce'} for r in REQUISITOS_POR_ROL['conductor']]
    # ¿Miembro del Comité Paritario? → curso de orientación (DS 44 Art. 32, ítem FUF 31).
    if cphs:
        reqs += [{**r, 'origen': 'cphs'} for r in REQUISITOS_POR_ROL['cphs']]
    return reqs
