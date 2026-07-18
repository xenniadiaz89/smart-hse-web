"""Módulo Comité Paritario de Higiene y Seguridad (FUF 30-40). Rutas aisladas en Blueprint.

Sin url_prefix, igual que el resto de los módulos: las URLs son /cphs y /api/cphs*.

El módulo solo existe cuando la ley lo exige (más de 25 trabajadores). Esa condición se comprueba
en la ruta —que es la guarda real— y no solo en el nav del dashboard, que es cosmético.
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for

import db
from core_auth import empresa_required, onboarding_required, empresa_id

from . import service

bp = Blueprint('cphs', __name__, template_folder='templates')


def _rut():
    return session.get('rut')


@bp.route('/cphs')
@empresa_required
@onboarding_required
def panel():
    eid = empresa_id()
    if not service.aplica(eid):
        return redirect(url_for('dashboard'))
    return render_template('cphs/panel.html',
                           empresa=db.empresa_de(_rut(), eid),
                           **service.cargar(eid, _rut()))


@bp.route('/api/cphs/resumen', methods=['GET'])
@empresa_required
@onboarding_required
def api_resumen():
    """Avance del comité para el gráfico del panel (6E)."""
    return jsonify(service.resumen(empresa_id()))


@bp.route('/api/cphs', methods=['GET'])
@empresa_required
@onboarding_required
def api_get():
    eid = empresa_id()
    return jsonify(service.cargar(eid, _rut()))


@bp.route('/api/cphs', methods=['POST'])
@empresa_required
@onboarding_required
def api_guardar():
    """Datos de constitución y registro en la DT. Al guardar, propaga al FUF y a la Matriz Legal."""
    eid = empresa_id()
    f = request.get_json(silent=True) or {}
    comite = db.comite_guardar(eid,
                               fecha_constitucion=f.get('fecha_constitucion'),
                               fecha_registro_dt=f.get('fecha_registro_dt'))
    return jsonify({'ok': True, 'comite': comite,
                    'fuf_actualizados': db.cphs_propagar_fuf(eid, rut=_rut()),
                    'resumen': service.resumen(eid)})


@bp.route('/api/cphs/miembros', methods=['POST'])
@empresa_required
@onboarding_required
def api_miembro_crear():
    eid = empresa_id()
    f = request.get_json(silent=True) or {}
    nombre = (f.get('nombre') or '').strip()
    if not nombre:
        return jsonify({'error': 'El nombre del representante es obligatorio.'}), 400
    comite = db.comite_de(eid, crear=True)
    try:
        tid = int(f.get('trabajador_id')) if f.get('trabajador_id') else None
    except (TypeError, ValueError):
        tid = None
    creado = db.miembro_crear(eid, comite['id'], nombre, rut=f.get('rut'),
                              representacion=f.get('representacion') or 'trabajadores',
                              calidad=f.get('calidad') or 'titular', trabajador_id=tid,
                              es_presidente=f.get('es_presidente'),
                              es_secretario=f.get('es_secretario'))
    if creado is None:
        return jsonify({'error': 'Ese RUT ya está registrado en el comité.'}), 400
    return jsonify({'ok': True, 'miembros': db.miembros_de(comite['id']),
                    'fuf_actualizados': db.cphs_propagar_fuf(eid, rut=_rut()),
                    'resumen': service.resumen(eid)})


@bp.route('/api/cphs/miembros/<int:mid>', methods=['DELETE'])
@empresa_required
@onboarding_required
def api_miembro_eliminar(mid):
    eid = empresa_id()
    if not db.miembro_eliminar(eid, mid):
        return jsonify({'error': 'Representante no encontrado.'}), 404
    comite = db.comite_de(eid, crear=True)
    return jsonify({'ok': True, 'miembros': db.miembros_de(comite['id']),
                    'resumen': service.resumen(eid)})


@bp.route('/api/cphs/actividades', methods=['POST'])
@empresa_required
@onboarding_required
def api_actividad_crear():
    eid = empresa_id()
    f = request.get_json(silent=True) or {}
    if not (f.get('fecha') or '').strip():
        return jsonify({'error': 'La fecha es obligatoria.'}), 400
    comite = db.comite_de(eid, crear=True)
    db.actividad_crear(eid, comite['id'], f.get('tipo') or 'reunion_ordinaria', f.get('fecha'),
                       titulo=f.get('titulo'), detalle=f.get('detalle'),
                       acuerdo_comunicado=f.get('acuerdo_comunicado'))
    return jsonify({'ok': True, 'actividades': db.actividades_de(comite['id']),
                    'fuf_actualizados': db.cphs_propagar_fuf(eid, rut=_rut()),
                    'resumen': service.resumen(eid)})


@bp.route('/api/cphs/actividades/<int:aid>', methods=['POST'])
@empresa_required
@onboarding_required
def api_actividad_guardar(aid):
    eid = empresa_id()
    f = request.get_json(silent=True) or {}
    if db.actividad_guardar(eid, aid, **f) is None:
        return jsonify({'error': 'Actividad no encontrada.'}), 404
    comite = db.comite_de(eid, crear=True)
    return jsonify({'ok': True, 'actividades': db.actividades_de(comite['id']),
                    'fuf_actualizados': db.cphs_propagar_fuf(eid, rut=_rut()),
                    'resumen': service.resumen(eid)})


@bp.route('/api/cphs/actividades/<int:aid>', methods=['DELETE'])
@empresa_required
@onboarding_required
def api_actividad_eliminar(aid):
    eid = empresa_id()
    if not db.actividad_eliminar(eid, aid):
        return jsonify({'error': 'Actividad no encontrada.'}), 404
    comite = db.comite_de(eid, crear=True)
    return jsonify({'ok': True, 'actividades': db.actividades_de(comite['id']),
                    'resumen': service.resumen(eid)})


@bp.route('/api/cphs/actividades/<int:aid>/acta', methods=['POST'])
@empresa_required
@onboarding_required
def api_actividad_acta(aid):
    """Sube el acta de una reunión. Queda en la carpeta de auditoría (Módulo 5) con
    categoria='CPHS' y marca el ítem FUF 35."""
    eid, rut = empresa_id(), _rut()
    archivo = request.files.get('archivo')
    if not archivo or not archivo.filename:
        return jsonify({'error': 'Adjunta el archivo del acta.'}), 400
    emp = db.empresa_de(rut, eid) or {}
    cid = db.contrato_base(eid, rut, emp.get('razon_social'))
    doc_id = db.registrar_documento(cid, archivo.filename, 'cargado', 'evidencia',
                                    item_n=aid, categoria='CPHS',
                                    contenido=archivo.read(), mimetype=archivo.mimetype)
    db.actividad_guardar(eid, aid, doc_id=doc_id)
    comite = db.comite_de(eid, crear=True)
    return jsonify({'ok': True, 'doc_id': doc_id,
                    'actividades': db.actividades_de(comite['id']),
                    'fuf_actualizados': db.cphs_propagar_fuf(eid, rut=rut),
                    'resumen': service.resumen(eid)})


@bp.route('/api/cphs/prefill-acta', methods=['GET'])
@empresa_required
@onboarding_required
def api_prefill_acta():
    """Campos del Acta de Constitución precargados con lo que ya está en el módulo.

    Evita re-teclear lo que el sistema ya sabe (principio P1): los miembros salen del comité y el
    N° de trabajadores de la dotación efectiva, no de un campo manual.
    """
    eid = empresa_id()
    comite = db.comite_de(eid, crear=True)
    miembros = db.miembros_de(comite['id'])

    def lista(representacion, calidad):
        return '\n'.join(f"{m['nombre']} — {m.get('rut') or 's/RUT'}" for m in miembros
                         if m.get('representacion') == representacion and m.get('calidad') == calidad)

    presi = next((m['nombre'] for m in miembros if m.get('es_presidente')), '')
    secre = next((m['nombre'] for m in miembros if m.get('es_secretario')), '')
    return jsonify({'tipo_doc': 'acta_cphs', 'campos': {
        'fecha': comite.get('fecha_constitucion') or '',
        'fecha_registro_dt': comite.get('fecha_registro_dt') or '',
        'n_trabajadores': str(db.dotacion_efectiva(eid)),
        'titulares_empresa': lista('empresa', 'titular'),
        'suplentes_empresa': lista('empresa', 'suplente'),
        'titulares_trabajadores': lista('trabajadores', 'titular'),
        'suplentes_trabajadores': lista('trabajadores', 'suplente'),
        'presidente': presi, 'secretario': secre,
    }})
