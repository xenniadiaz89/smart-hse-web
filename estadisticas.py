"""Estadísticas de Prevención — cálculo puro de los índices de accidentabilidad (empresa
transversal). Sin BD ni Flask: recibe filas mensuales y devuelve los índices y las series para
el gráfico de la portada de Mis Contratos y para el documento FUF 47/60.

Fórmulas chilenas estándar (base 1.000.000 de horas-hombre):
  Índice/Tasa de Frecuencia (IF) = N° accidentes CTP · 1.000.000 / HH trabajadas
  Índice/Tasa de Gravedad   (IG) = días perdidos     · 1.000.000 / HH trabajadas
  Tasa de Accidentabilidad       = N° accidentes · 100 / N° trabajadores
Todo devuelve 0 cuando el divisor es 0 (mes sin horas / sin dotación).
"""

MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

_MILLON = 1_000_000


def _num(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def indice_frecuencia(n_accidentes, hh_trabajadas):
    hh = _num(hh_trabajadas)
    return round(_num(n_accidentes) * _MILLON / hh, 2) if hh else 0.0


def indice_gravedad(dias_perdidos, hh_trabajadas):
    hh = _num(hh_trabajadas)
    return round(_num(dias_perdidos) * _MILLON / hh, 2) if hh else 0.0


def indice_gravedad_con_cargo(dias_perdidos, dias_cargo, hh_trabajadas):
    """IG detallado (módulo /siniestros): suma días cargo (dias_cargo.py, tabla ISP) a los días
    perdidos reales. No reemplaza indice_gravedad(), que sigue alimentando /api/estadisticas y
    el FUF 47/60 sin cambios."""
    hh = _num(hh_trabajadas)
    return round((_num(dias_perdidos) + _num(dias_cargo)) * _MILLON / hh, 2) if hh else 0.0


def tasa_accidentabilidad(n_accidentes, n_trabajadores):
    nt = _num(n_trabajadores)
    return round(_num(n_accidentes) * 100 / nt, 2) if nt else 0.0


def indices_mes(fila):
    """Índices de una fila mensual (dict con n_accidentes, dias_perdidos, n_trabajadores, hh_trabajadas)."""
    return {
        'if': indice_frecuencia(fila.get('n_accidentes'), fila.get('hh_trabajadas')),
        'ig': indice_gravedad(fila.get('dias_perdidos'), fila.get('hh_trabajadas')),
        'ta': tasa_accidentabilidad(fila.get('n_accidentes'), fila.get('n_trabajadores')),
    }


def serie(filas):
    """`filas` = 12 dicts (mes 1..12). Devuelve etiquetas, series para el gráfico (IF, IG,
    accidentes) y los acumulados/promedios del año para los KPIs y el documento."""
    porm = {int(f.get('mes')): f for f in filas if f.get('mes')}
    labels, s_if, s_ig, s_acc, detalle = [], [], [], [], []
    tot_acc = tot_dias = tot_hh = tot_inc = 0.0
    max_trab = 0.0
    for m in range(1, 13):
        f = porm.get(m, {})
        ix = indices_mes(f)
        labels.append(MESES[m - 1])
        s_if.append(ix['if'])
        s_ig.append(ix['ig'])
        acc = _num(f.get('n_accidentes'))
        s_acc.append(acc)
        tot_acc += acc
        tot_inc += _num(f.get('n_incidentes'))
        tot_dias += _num(f.get('dias_perdidos'))
        tot_hh += _num(f.get('hh_trabajadas'))
        max_trab = max(max_trab, _num(f.get('n_trabajadores')))
        detalle.append({'mes': m, 'nombre': MESES[m - 1],
                        'n_accidentes': int(acc), 'n_incidentes': int(_num(f.get('n_incidentes'))),
                        'dias_perdidos': int(_num(f.get('dias_perdidos'))),
                        'n_trabajadores': int(_num(f.get('n_trabajadores'))),
                        'hh_trabajadas': int(_num(f.get('hh_trabajadas'))), **ix})
    acumulado = {
        'accidentes': int(tot_acc), 'incidentes': int(tot_inc),
        'dias_perdidos': int(tot_dias), 'hh_trabajadas': int(tot_hh),
        'if': indice_frecuencia(tot_acc, tot_hh),
        'ig': indice_gravedad(tot_dias, tot_hh),
        'ta': tasa_accidentabilidad(tot_acc, max_trab),
    }
    return {'labels': labels, 'if': s_if, 'ig': s_ig, 'accidentes': s_acc,
            'detalle': detalle, 'acumulado': acumulado}
