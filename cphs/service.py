"""Lógica del seguimiento del Comité Paritario (cálculo del avance y de lo que falta).

Solo depende de db/cumplimiento — nunca de app.py ni de otro módulo (aislamiento por carpeta).
El % que sale de aquí es el mismo criterio que audita el FUF en sus ítems 30-38: no es un
indicador cosmético, cada componente apunta al ítem que lo exige.
"""
from datetime import date

import db

UMBRAL_CPHS = 26          # "más de 25 trabajadores" (Art. 66 Ley 16.744 / DS 54)


def aplica(empresa_id):
    """¿Le corresponde CPHS a esta empresa? Es la guarda real del módulo."""
    return db.dotacion_efectiva(empresa_id) >= UMBRAL_CPHS


def _mes_actual_del_mandato(fecha_constitucion, hoy=None):
    """Reuniones ordinarias esperadas = meses transcurridos desde la constitución (una al mes,
    ítem FUF 34). Sin fecha de constitución no se exige ninguna todavía."""
    hoy = hoy or date.today()
    try:
        d = date.fromisoformat(fecha_constitucion)
    except (TypeError, ValueError):
        return 0
    if d > hoy:
        return 0
    return max(1, (hoy.year - d.year) * 12 + (hoy.month - d.month) + 1)


def resumen(empresa_id, hoy=None):
    """Estado del comité: avance, desglose por obligación y lo que queda pendiente.

    Cada componente vale lo mismo (media simple): son todas obligaciones legales, no hay una que
    'pese menos' ante un fiscalizador.
    """
    comite = db.comite_de(empresa_id)
    if not comite:
        return {'constituido': False, 'pct': 0, 'componentes': [], 'pendientes': [
            {'texto': 'Constituir el Comité Paritario y levantar el acta.', 'item_fuf': 30}]}

    acts = db.actividades_de(comite['id'])
    reuniones = [a for a in acts if (a.get('tipo') or '').startswith('reunion')]
    con_acta = [a for a in reuniones if a.get('doc_id')]
    acuerdos = [a for a in acts if a.get('tipo') == 'acuerdo']
    comunicados = [a for a in acuerdos if a.get('acuerdo_comunicado')]
    total_m, con_curso = db.miembros_con_curso(empresa_id, comite['id'])
    esperadas = _mes_actual_del_mandato(comite.get('fecha_constitucion'), hoy)

    def pct(parte, total):
        return 100 if not total else min(100, round(parte * 100 / total))

    componentes = [
        {'clave': 'constitucion', 'nombre': 'Comité constituido', 'item_fuf': 30,
         'pct': 100 if comite.get('fecha_constitucion') else 0},
        {'clave': 'registro_dt', 'nombre': 'Acta registrada en la Dirección del Trabajo', 'item_fuf': 32,
         'pct': 100 if comite.get('fecha_registro_dt') else 0},
        {'clave': 'miembros', 'nombre': 'Miembros con curso de orientación', 'item_fuf': 31,
         'pct': pct(con_curso, total_m)},
        {'clave': 'reuniones', 'nombre': 'Reuniones mensuales al día', 'item_fuf': 34,
         'pct': pct(len(reuniones), esperadas)},
        {'clave': 'actas', 'nombre': 'Reuniones con acta levantada', 'item_fuf': 35,
         'pct': pct(len(con_acta), len(reuniones))},
        {'clave': 'acuerdos', 'nombre': 'Acuerdos comunicados por escrito', 'item_fuf': 36,
         'pct': pct(len(comunicados), len(acuerdos))},
    ]
    global_pct = round(sum(c['pct'] for c in componentes) / len(componentes))

    pendientes = []
    if not comite.get('fecha_constitucion'):
        pendientes.append({'texto': 'Registrar la fecha de constitución y generar el acta.', 'item_fuf': 30})
    if not comite.get('fecha_registro_dt'):
        pendientes.append({'texto': 'Registrar el acta en el sitio web de la Dirección del Trabajo '
                                    '(plazo: 15 días hábiles desde la constitución).', 'item_fuf': 32})
    if total_m == 0:
        pendientes.append({'texto': 'Ingresar los representantes titulares y suplentes del comité.', 'item_fuf': 30})
    elif con_curso < total_m:
        pendientes.append({'texto': f'{total_m - con_curso} miembro(s) sin el curso de orientación '
                                    'vigente (debe realizarse en el primer semestre del mandato).',
                           'item_fuf': 31})
    if len(reuniones) < esperadas:
        pendientes.append({'texto': f'Faltan {esperadas - len(reuniones)} reunión(es) ordinaria(s): '
                                    f'{len(reuniones)} registradas de {esperadas} esperadas.', 'item_fuf': 34})
    sin_acta = len(reuniones) - len(con_acta)
    if sin_acta > 0:
        pendientes.append({'texto': f'{sin_acta} reunión(es) sin acta adjunta.', 'item_fuf': 35})
    sin_comunicar = len(acuerdos) - len(comunicados)
    if sin_comunicar > 0:
        pendientes.append({'texto': f'{sin_comunicar} acuerdo(s) sin comunicar por escrito.', 'item_fuf': 36})

    return {
        'constituido': bool(comite.get('fecha_constitucion')),
        'pct': global_pct,
        'componentes': componentes,
        'pendientes': pendientes,
        'mandato_vence': comite.get('vigencia_hasta'),
        'reuniones': {'esperadas': esperadas, 'realizadas': len(reuniones), 'con_acta': len(con_acta)},
        'acuerdos': {'total': len(acuerdos), 'comunicados': len(comunicados)},
        'miembros': {'total': total_m, 'con_curso': con_curso},
    }


def cargar(empresa_id, rut):
    """Todo lo que el panel necesita para renderizar."""
    comite = db.comite_de(empresa_id, crear=True)
    return {
        'comite': comite,
        'miembros': db.miembros_de(comite['id']),
        'actividades': db.actividades_de(comite['id']),
        'trabajadores': db.trabajadores_de(empresa_id, solo_activos=True),
        'resumen': resumen(empresa_id),
        'dotacion': db.dotacion_efectiva(empresa_id),
    }
