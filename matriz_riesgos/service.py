"""Lógica del módulo Matriz de Riesgos. Solo depende de db/models/iper/cumplimiento — nunca de
app.py ni de otro módulo (aislamiento por carpeta)."""
import cumplimiento
import db
import iper


def cargar(empresa_id, quien=None):
    """Matriz vigente + tareas agrupadas por proceso, listo para el panel."""
    m = db.matriz_riesgo_vigente(empresa_id)
    if not m:
        db.crear_matriz_riesgo(empresa_id, quien)
        m = db.matriz_riesgo_vigente(empresa_id)
    tareas = db.tareas_de_matriz(m['id'])
    for t in tareas:
        t['riesgos'] = db.riesgos_de_tarea(t['id'])
    procesos = db.procesos_de_matriz(m['id'])
    return {'matriz': m, 'procesos': agrupar_por_proceso(tareas, procesos),
            'resumen': resumen(tareas), 'mineros': db.contratos_mineros_de(empresa_id)}


def agrupar_por_proceso(tareas, procesos=None):
    """[tarea] → [{'proceso', 'tareas': [...]}]. El eje de la IPER es Proceso → Tarea → Puesto.

    Parte de los procesos reales (ProcesoIPER) para que uno recién incorporado se vea aunque
    todavía no tenga tareas; las tareas legacy cuyo texto libre no calza con ningún proceso real
    arman su propio grupo igual que antes (compatibilidad hacia atrás)."""
    grupos, orden = {}, []
    for p in (procesos or []):
        nombre = (p.get('nombre') or '').strip()
        if nombre and nombre not in grupos:
            grupos[nombre] = []
            orden.append(nombre)
    for t in tareas:
        p = (t.get('proceso') or '').strip() or 'Sin proceso asignado'
        if p not in grupos:
            grupos[p] = []
            orden.append(p)
        grupos[p].append(t)
    orden.sort(key=lambda p: (p == 'Sin proceso asignado', p.lower()))
    return [{'proceso': p, 'tareas': grupos[p]} for p in orden]


def resumen(tareas):
    """Conteo de riesgos por magnitud RESIDUAL (la que queda tras los controles), más cuántos
    controles están validados por el sistema. Es el titular del panel."""
    r = {'total': 0, 'validados': 0, 'por_magnitud': {}, 'criticos': 0}
    for t in tareas:
        for x in t.get('riesgos') or []:
            r['total'] += 1
            if x.get('estado_control') == 'validado_sistema':
                r['validados'] += 1
            mag = x.get('nivel_riesgo_residual') or x.get('nivel_riesgo') or '—'
            r['por_magnitud'][mag] = r['por_magnitud'].get(mag, 0) + 1
            if mag in ('Importante', 'Intolerable'):
                r['criticos'] += 1
    return r
