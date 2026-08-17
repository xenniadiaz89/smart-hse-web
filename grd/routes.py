"""Módulo GRD — Plan de Gestión de Riesgos de Desastres (emergencias, ítem FUF 27).

Blueprint aislado. Vista /grd (las 3 etapas: identificar amenazas → evaluar → medidas de control).
Un fallo aquí no tumba el resto de la app.
"""
from flask import Blueprint, render_template, request, jsonify

from core_auth import empresa_required, onboarding_required, empresa_id
from models import sqla, GRDAmenaza, GRDPregunta

from . import service

bp = Blueprint('grd', __name__, template_folder='templates')


def _amenaza_de(eid, aid):
    return GRDAmenaza.query.filter_by(id=aid, empresa_id=eid).first()


@bp.route('/grd')
@empresa_required
@onboarding_required
def panel():
    service.sembrar(empresa_id())          # primera vez: carga las amenazas genéricas
    return render_template('grd/panel.html')


@bp.route('/api/grd', methods=['GET'])
@empresa_required
@onboarding_required
def api_grd():
    service.sembrar(empresa_id())
    return jsonify(service.estado(empresa_id()))


@bp.route('/api/grd/amenaza', methods=['POST'])
@empresa_required
@onboarding_required
def api_grd_amenaza_crear():
    """Agrega una amenaza específica de la empresa (con opción de preguntas propias)."""
    eid = empresa_id()
    f = request.get_json(silent=True) or {}
    nombre = (f.get('nombre') or '').strip()
    if not nombre:
        return jsonify({'error': 'Indica el nombre de la amenaza.'}), 400
    orden = (sqla.session.query(sqla.func.max(GRDAmenaza.orden))
             .filter_by(empresa_id=eid).scalar() or 0) + 1
    am = GRDAmenaza(empresa_id=eid, codigo=(f.get('codigo') or '').strip() or None, nombre=nombre,
                    descripcion=(f.get('descripcion') or '').strip() or None, tipo='especifica',
                    identificada=1, orden=orden)
    sqla.session.add(am)
    sqla.session.flush()
    for texto in (f.get('preguntas') or []):
        texto = (texto or '').strip()
        if texto:
            sqla.session.add(GRDPregunta(amenaza_id=am.id, empresa_id=eid, texto=texto))
    sqla.session.commit()
    return jsonify(service.estado(eid))


@bp.route('/api/grd/amenaza/<int:aid>', methods=['POST'])
@empresa_required
@onboarding_required
def api_grd_amenaza_actualizar(aid):
    """Marca/actualiza la amenaza (p. ej. 'identificada')."""
    eid = empresa_id()
    am = _amenaza_de(eid, aid)
    if not am:
        return jsonify({'error': 'Amenaza no encontrada.'}), 404
    f = request.get_json(silent=True) or {}
    if 'identificada' in f:
        am.identificada = 1 if f.get('identificada') else 0
    if f.get('nombre'):
        am.nombre = f['nombre'].strip()
    if 'descripcion' in f:
        am.descripcion = (f.get('descripcion') or '').strip() or None
    sqla.session.commit()
    return jsonify(service.estado(eid))


@bp.route('/api/grd/amenaza/<int:aid>/eliminar', methods=['POST'])
@empresa_required
@onboarding_required
def api_grd_amenaza_eliminar(aid):
    eid = empresa_id()
    am = _amenaza_de(eid, aid)
    if not am:
        return jsonify({'error': 'Amenaza no encontrada.'}), 404
    GRDPregunta.query.filter_by(amenaza_id=aid).delete()
    sqla.session.delete(am)
    sqla.session.commit()
    return jsonify(service.estado(eid))


@bp.route('/api/grd/pregunta/<int:pid>', methods=['POST'])
@empresa_required
@onboarding_required
def api_grd_pregunta_guardar(pid):
    """Guarda la evaluación y la medida de control de una pregunta."""
    eid = empresa_id()
    p = GRDPregunta.query.filter_by(id=pid, empresa_id=eid).first()
    if not p:
        return jsonify({'error': 'Pregunta no encontrada.'}), 404
    f = request.get_json(silent=True) or {}
    if 'cumplimiento' in f:
        p.cumplimiento = (f.get('cumplimiento') or '').strip()
    for k in ('accion', 'medida', 'evidencia'):
        if k in f:
            setattr(p, k, (f.get(k) or '').strip() or None)
    for k in ('np', 'nc'):
        if k in f:
            v = f.get(k)
            setattr(p, k, int(v) if str(v or '').isdigit() else None)
    sqla.session.commit()
    return jsonify(service.estado(eid))
