"""Módulo — Carta Gantt de Protocolos MINSAL. Rutas aisladas en Blueprint.

Registro de avance por actividad (fase → actividad → responsable → estado → evidencia) de los
protocolos de vigilancia MINSAL (TMERT-EESS, Psicosocial, PREXOR, PLANESI, MMC, Radiación UV
Solar), independiente del contador simple de ProtocoloSalud (Panel de Protocolos existente).
"""
from io import BytesIO

from flask import Blueprint, render_template, request, jsonify, session, send_file

import db
from core_auth import empresa_required, onboarding_required, empresa_id

from . import service

bp = Blueprint('protocolos_gantt', __name__, template_folder='templates')

_ESTADOS_VALIDOS = ('pendiente', 'en_proceso', 'cumple')


@bp.route('/protocolos-gantt')
@empresa_required
@onboarding_required
def panel():
    """Carta Gantt de Protocolos MINSAL: fases, actividades y su avance real."""
    eid = empresa_id()
    return render_template('protocolos_gantt/panel.html',
                           empresa=db.empresa_de(session.get('rut'), eid),
                           **service.cargar(eid))


@bp.route('/api/protocolos-gantt', methods=['GET'])
@empresa_required
@onboarding_required
def api_cargar():
    return jsonify(service.cargar(empresa_id()))


@bp.route('/api/protocolos-gantt/etapa', methods=['POST'])
@empresa_required
@onboarding_required
def api_etapa_guardar():
    f = request.get_json(silent=True) or {}
    clave = (f.get('clave') or '').strip()
    if not clave:
        return jsonify({'error': 'Falta la clave de la actividad.'}), 400
    estado = f.get('estado')
    if estado is not None and estado not in _ESTADOS_VALIDOS:
        return jsonify({'error': 'Estado inválido.'}), 400
    row = service.etapa_guardar(
        empresa_id(), clave, estado=estado,
        responsable=f.get('responsable'), fecha_inicio=f.get('fecha_inicio'),
        fecha_termino=f.get('fecha_termino'), observacion=f.get('observacion'))
    return jsonify({'ok': True, 'etapa': row})


@bp.route('/api/protocolos-gantt/etapa/<clave>/documento', methods=['POST'])
@empresa_required
@onboarding_required
def api_etapa_documento(clave):
    archivo = request.files.get('archivo')
    if not archivo or not archivo.filename:
        return jsonify({'error': 'No se recibió archivo.'}), 400
    rut, eid = session['rut'], empresa_id()
    emp = db.empresa_de(rut, eid) or {}
    cid = db.contrato_base(eid, rut, emp.get('razon_social'))
    doc_id = db.registrar_documento(
        cid, archivo.filename, '', 'evidencia', categoria='PROTOCOLO_GANTT',
        contenido=archivo.read(), mimetype=archivo.mimetype or 'application/octet-stream')
    row = service.etapa_set_evidencia(eid, clave, doc_id)
    return jsonify({'ok': True, 'etapa': row, 'doc_id': doc_id})


@bp.route('/api/protocolos-gantt/documento/<int:doc_id>', methods=['GET'])
@empresa_required
def api_documento_descargar(doc_id):
    blob = db.documento_contenido(session['rut'], doc_id)
    if not blob:
        return ('Documento no encontrado', 404)
    contenido, mimetype, nombre = blob
    return send_file(BytesIO(contenido), mimetype=mimetype or 'application/octet-stream',
                     as_attachment=False, download_name=nombre or f'doc_{doc_id}')
