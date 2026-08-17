"""Módulo Siniestros — Registro individual de accidentes/incidentes y KPIs de accidentabilidad
en tiempo real (Tasa de Frecuencia, Tasa de Gravedad con días cargo ISP, Tasa de Accidentabilidad).

Blueprint aislado. Complementa la Estadística de Prevención mensual existente (vista
'estadisticas' del dashboard, /api/estadisticas): esa sigue siendo la fuente oficial del FUF
47/60. Este panel registra el detalle por siniestro. Un fallo aquí no tumba el resto de la app.
"""
from datetime import date

from flask import Blueprint, render_template, request, jsonify, session

import db
import dias_cargo
from core_auth import empresa_required, onboarding_required, empresa_id

from . import service

bp = Blueprint('siniestros', __name__, template_folder='templates')


@bp.route('/siniestros')
@empresa_required
@onboarding_required
def panel():
    return render_template('siniestros/panel.html')


@bp.route('/api/siniestros', methods=['GET'])
@empresa_required
@onboarding_required
def api_siniestros():
    eid = empresa_id()
    anio = request.args.get('anio') or date.today().year
    return jsonify({
        'siniestros': service.listar(eid, anio),
        'kpis': service.kpis(eid, anio),
        'trabajadores': db.trabajadores_de(eid, solo_activos=True),
        'tipos_lesion': dias_cargo.ETIQUETAS_TIPO_LESION,
    })


@bp.route('/api/siniestros/kpis', methods=['GET'])
@empresa_required
@onboarding_required
def api_siniestros_kpis():
    anio = request.args.get('anio') or date.today().year
    return jsonify(service.kpis(empresa_id(), anio))


@bp.route('/api/siniestros', methods=['POST'])
@empresa_required
@onboarding_required
def api_siniestro_crear():
    f = request.get_json(silent=True) or request.form
    try:
        s = service.crear(empresa_id(), f, creado_por=session.get('rut'))
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    return jsonify({'ok': True, 'siniestro': s})


@bp.route('/api/siniestros/<int:sid>', methods=['POST'])
@empresa_required
@onboarding_required
def api_siniestro_editar(sid):
    f = request.get_json(silent=True) or request.form
    s = service.editar(empresa_id(), sid, f)
    if not s:
        return jsonify({'error': 'Siniestro no encontrado.'}), 404
    return jsonify({'ok': True, 'siniestro': s})


@bp.route('/api/siniestros/<int:sid>/eliminar', methods=['POST'])
@empresa_required
@onboarding_required
def api_siniestro_eliminar(sid):
    if not service.eliminar(empresa_id(), sid):
        return jsonify({'error': 'Siniestro no encontrado.'}), 404
    return jsonify({'ok': True})
