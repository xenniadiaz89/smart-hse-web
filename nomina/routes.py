"""Módulo 4 — Nómina y Smart Checker. Rutas aisladas en Blueprint.

Sin url_prefix: las URLs /api/trabajadores* y /api/irl/generar se conservan idénticas.

Límite del módulo: /api/iper/tareas, /api/epp y /api/pts SE QUEDAN en el núcleo — los consume
también la MIPER, y traerlos aquí haría que un fallo de este módulo las tumbara. Este panel las
consume como cliente.
"""
from flask import Blueprint, render_template, request, jsonify, session

import db
import docgen
import planes
import resso
from core_auth import empresa_required, onboarding_required, empresa_id

from . import service

bp = Blueprint('nomina', __name__, template_folder='templates')


@bp.route('/nomina')
@empresa_required
@onboarding_required
def panel():
    """Smart Checker: quién tiene qué vigente, qué vence y qué falta, por trabajador."""
    eid = empresa_id()
    db.refrescar_vencimientos_requisitos(eid)      # el tiempo pasa: lo de ayer puede estar vencido
    return render_template('nomina/panel.html',
                           empresa=db.empresa_de(session.get('rut'), eid),
                           roles=resso.ROLES_CRITICOS,
                           **service.cargar(eid, session.get('rut')))


@bp.route('/api/trabajadores', methods=['GET'])
@empresa_required
@onboarding_required
def api_trabajadores():
    eid = empresa_id()
    out = []
    for t in db.trabajadores_de(eid):
        t['tareas'] = [x['id'] for x in db.tareas_de_trabajador(t['id'])]
        t['irls'] = db.irls_de_trabajador(t['id'])
        t['requisitos'] = db.requisitos_de_trabajador(t['id'])
        t['semaforo'] = service.semaforo(t['requisitos'])
        out.append(t)
    return jsonify(out)


@bp.route('/api/trabajadores', methods=['POST'])
@empresa_required
@onboarding_required
def api_trabajador_crear():
    from core_auth import normalizar_rut, rut_valido
    f = request.get_json(silent=True) or request.form
    rut = (f.get('rut') or '').strip()
    nombre = (f.get('nombre') or '').strip()
    if not (rut and nombre):
        return jsonify({'error': 'Indica RUT y nombre del trabajador.'}), 400
    if not rut_valido(rut):
        return jsonify({'error': 'El RUT del trabajador no es válido.'}), 400
    eid = empresa_id()
    emp = db.empresa_de(session['rut'], eid) or {}
    # El tope es por tramo comercial y solo cuenta ACTIVOS: un desvinculado no consume cupo.
    activos = db.trabajadores_activos_count(eid)
    if not planes.cabe(emp.get('plan'), activos):
        info = planes.cupo(emp.get('plan'), activos)
        sug = planes.plan_de(info['sugerido'])
        return jsonify({'error': 'limite_trabajadores', 'cupo': info,
                        'mensaje': f"Tu {info['nombre']} contempla hasta {info['tope']} trabajadores "
                                   f"y ya tienes {activos} activos. Para agregar más necesitas el "
                                   f"{sug['nombre']}."}), 403
    resp = f.get('responsable_id')
    db.trabajador_crear(eid, normalizar_rut(rut), nombre,
                        cargo=(f.get('cargo') or '').strip() or None,
                        rol=(f.get('rol') or '').strip() or None,
                        contrato_id=f.get('contrato_id') or None,
                        responsable_id=int(resp) if resp else None,
                        conduce=str(f.get('conduce')) in ('1', 'true', 'True', 'on', 'si'))
    return jsonify(db.trabajadores_de(eid))


@bp.route('/api/trabajadores/<int:tid>/estado', methods=['POST'])
@empresa_required
@onboarding_required
def api_trabajador_estado(tid):
    """Desvincula ('Ya no labora en la empresa') o reactiva. No borra: el historial de requisitos
    y la trazabilidad de su RUT en checklists ya firmados se conservan."""
    f = request.get_json(silent=True) or {}
    t = db.trabajador_set_estado(tid, empresa_id(), (f.get('estado') or '').strip(),
                                 fecha_egreso=(f.get('fecha_egreso') or '').strip() or None,
                                 motivo=(f.get('motivo') or '').strip() or None)
    if not t:
        return jsonify({'error': 'Trabajador no encontrado o estado inválido.'}), 400
    return jsonify({'ok': True, 'trabajador': t,
                    'dotacion': service.dotacion_info(empresa_id())})


@bp.route('/api/trabajadores/<int:tid>/rol', methods=['POST'])
@empresa_required
@onboarding_required
def api_trabajador_rol(tid):
    """Cambia el rol crítico y re-inyecta sus requisitos. Los del rol anterior no se borran."""
    f = request.get_json(silent=True) or {}
    t = db.trabajador_set_rol(tid, empresa_id(), (f.get('rol') or '').strip() or None,
                              cargo=f.get('cargo'))
    if not t:
        return jsonify({'error': 'Trabajador no encontrado.'}), 404
    return jsonify({'ok': True, 'trabajador': t, 'requisitos': db.requisitos_de_trabajador(tid)})


@bp.route('/api/trabajadores/<int:tid>/requisitos/<int:rid>', methods=['POST'])
@empresa_required
@onboarding_required
def api_requisito_guardar(tid, rid):
    """Fecha de emisión, responsable (de la nómina) y evidencia. Recalcula el vencimiento."""
    f = request.get_json(silent=True) or {}
    r = db.requisito_trab_guardar(rid, empresa_id(), f)
    if not r:
        return jsonify({'error': 'Requisito no encontrado.'}), 404
    return jsonify({'ok': True, 'requisito': r,
                    'semaforo': service.semaforo(db.requisitos_de_trabajador(tid))})


@bp.route('/api/nomina/asignar', methods=['POST'])
@empresa_required
@onboarding_required
def api_nomina_asignar():
    """Asignación masiva a una faena/contrato. Puebla contrato_id, que valía 0 en todos."""
    f = request.get_json(silent=True) or {}
    n = db.trabajadores_asignar_contrato(empresa_id(), f.get('trabajador_ids'), f.get('contrato_id'))
    return jsonify({'ok': True, 'asignados': n})


@bp.route('/api/nomina/plan', methods=['GET'])
@empresa_required
@onboarding_required
def api_nomina_plan():
    return jsonify(service.dotacion_info(empresa_id()))


@bp.route('/api/trabajadores/<int:tid>/eliminar', methods=['POST'])
@empresa_required
@onboarding_required
def api_trabajador_eliminar(tid):
    """Borrado real: solo para corregir un alta errónea. Para una baja usa /estado (desvincular),
    que conserva el historial."""
    db.trabajador_eliminar(empresa_id(), tid)
    return jsonify(db.trabajadores_de(empresa_id()))


@bp.route('/api/trabajadores/<int:tid>/tareas', methods=['POST'])
@empresa_required
@onboarding_required
def api_trabajador_tareas(tid):
    if not db.trabajador_de(empresa_id(), tid):
        return jsonify({'error': 'Trabajador no encontrado.'}), 404
    f = request.get_json(silent=True) or {}
    db.trabajador_set_tareas(tid, f.get('tarea_ids') or [])
    return jsonify({'ok': True, 'tareas': [x['id'] for x in db.tareas_de_trabajador(tid)]})


@bp.route('/api/trabajadores/<int:tid>/irl', methods=['GET'])
@empresa_required
@onboarding_required
def api_trabajador_irls(tid):
    return jsonify(db.irls_de_trabajador(tid))


@bp.route('/api/irl/generar', methods=['POST'])
@empresa_required
@onboarding_required
def api_irl_generar():
    f = request.get_json(silent=True) or request.form
    rut, eid = session['rut'], empresa_id()
    trab = db.trabajador_de(eid, int(f.get('trabajador_id')))
    if not trab:
        return jsonify({'error': 'Trabajador no encontrado.'}), 404
    res = docgen.generar_irl(db, db.empresa_de(rut, eid), trab, session.get('nombre') or rut,
                             logo_data_uri=docgen.logo_empresa(db, rut, eid))
    return jsonify({'ok': True, 'doc_id': res['doc_id'], 'audit_id': res['audit_id'],
                    'matriz_version': res['matriz_version'],
                    'preview_url': f"/api/doc/{res['doc_id']}"})
