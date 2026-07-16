"""Tramos comerciales de Smart HSE — dato puro, como cumplimiento.py o fuf.py.

El tramo topa cuántos trabajadores se pueden registrar en la NÓMINA (registro nominal). NO topa
la dotación declarada ni las obligaciones legales: la exigibilidad del CPHS (25) y de la reserva
del 1% (100) se calcula sobre la dotación efectiva, sin importar el tramo contratado
(ver db.dotacion_efectiva y cumplimiento.REGLAS_DOTACION).

Reemplaza la constante suelta MAX_TRABAJADORES_BASICO = 20 que vivía en app.py.
"""

PLANES = [
    {'codigo': 'basico', 'nombre': 'Plan Básico',
     'desde': 1, 'max_trabajadores': 20},
    {'codigo': 'empresa', 'nombre': 'Plan Empresa',
     'desde': 21, 'max_trabajadores': 100},
    {'codigo': 'corporativo', 'nombre': 'Plan Corporativo / Minería',
     'desde': 101, 'max_trabajadores': None},      # None = sin tope
]

POR_DEFECTO = 'basico'

_INDEX = {p['codigo']: p for p in PLANES}


def plan_de(codigo):
    """Tramo por código. Cae al Plan Básico si el código es desconocido o nulo: nunca devuelve
    None, para que un dato sucio no deje pasar trabajadores sin tope."""
    return _INDEX.get((codigo or '').strip().lower(), _INDEX[POR_DEFECTO])


def plan_sugerido(dotacion):
    """El tramo que le corresponde a esa dotación. Se usa para sugerir el upgrade."""
    try:
        n = int(dotacion or 0)
    except (TypeError, ValueError):
        n = 0
    for p in reversed(PLANES):
        if n >= p['desde']:
            return p
    return _INDEX[POR_DEFECTO]


def cabe(codigo, n_actual):
    """¿Cabe un trabajador más en la nómina con este tramo? n_actual = ACTIVOS (un desvinculado
    no consume cupo)."""
    tope = plan_de(codigo)['max_trabajadores']
    return tope is None or int(n_actual or 0) < tope


def cupo(codigo, n_actual):
    """{plan, usados, tope, disponible, sugerido} para pintar el badge y armar el 403."""
    p = plan_de(codigo)
    usados = int(n_actual or 0)
    tope = p['max_trabajadores']
    return {'plan': p['codigo'], 'nombre': p['nombre'], 'usados': usados, 'tope': tope,
            'disponible': None if tope is None else max(0, tope - usados),
            'sugerido': plan_sugerido(usados + 1)['codigo']}
