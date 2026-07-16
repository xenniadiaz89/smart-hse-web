"""Lógica del módulo Nómina. Solo depende de db/models/planes/resso — nunca de app.py ni de otro
módulo (aislamiento por carpeta)."""
import db
import planes


def semaforo(requisitos):
    """{vigentes, por_vencer, vencidos, pendientes, total} de un trabajador. Los del rol anterior
    no cuentan: ya no le aplican, solo se conservan como historial."""
    s = {'vigentes': 0, 'por_vencer': 0, 'vencidos': 0, 'pendientes': 0, 'total': 0}
    for r in requisitos or []:
        if r.get('origen') == 'rol_anterior':
            continue
        s['total'] += 1
        e = r.get('estado_cumplimiento')
        if e == 'vigente':
            s['vigentes'] += 1
        elif e == 'por_vencer':
            s['por_vencer'] += 1
        elif e == 'pendiente_actualizacion':
            s['vencidos'] += 1
        else:
            s['pendientes'] += 1
    return s


def dotacion_info(empresa_id):
    """La foto que encabeza el panel: declarada vs activos vs efectiva, más el cupo del tramo.

    `discrepancia` es el aviso: si los activos superan a la declarada, el número del Onboarding
    quedó corto y conviene corregirlo (la ley ya se está aplicando sobre la efectiva, así que
    nada se incumple mientras tanto)."""
    from models import Empresa
    e = Empresa.query.get(empresa_id)
    declarada = int((e.dotacion if e and e.dotacion else 0) or 0)
    activos = db.trabajadores_activos_count(empresa_id)
    efectiva = db.dotacion_efectiva(empresa_id)
    return {'declarada': declarada, 'activos': activos, 'efectiva': efectiva,
            'discrepancia': activos > declarada,
            'cupo': planes.cupo((e.plan if e else None), activos),
            'tramos': planes.PLANES}


def cargar(empresa_id, rut):
    """Todo lo que el panel necesita en un render."""
    trabajadores = []
    for t in db.trabajadores_de(empresa_id):
        t['requisitos'] = db.requisitos_de_trabajador(t['id'])
        t['semaforo'] = semaforo(t['requisitos'])
        trabajadores.append(t)
    contratos = db.listar_contratos(rut, empresa_id)
    faenas = {c['id']: (c.get('faena') or c.get('numero') or f"Contrato {c['id']}") for c in contratos}
    activos = [t for t in trabajadores if (t.get('estado') or 'activo') == 'activo']
    return {'trabajadores': trabajadores, 'contratos': contratos, 'faenas': faenas,
            'dotacion': dotacion_info(empresa_id),
            'resumen': {'activos': len(activos),
                        'inactivos': len(trabajadores) - len(activos),
                        'sin_faena': sum(1 for t in activos if not t.get('contrato_id')),
                        'con_brechas': sum(1 for t in activos
                                           if t['semaforo']['pendientes'] or t['semaforo']['vencidos'])}}
