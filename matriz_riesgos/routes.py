"""Módulo 2 — Matriz de Riesgos Interactiva (IPER / Guía ISP, DS 44). Rutas aisladas en Blueprint.

Sin url_prefix a propósito: las URLs /api/miper* se conservan idénticas.

Ojo con el límite del módulo: /api/iper/tareas, /api/epp, /api/pts y /api/mutuales NO viven aquí
aunque el nombre lo sugiera — los consume la vista Trabajadores/IRL y la tarjeta de Mutual del
dashboard, que son del núcleo. Si estuvieran aquí, un fallo de este módulo las tumbaría.
"""
from flask import Blueprint, render_template, request, jsonify, session

import db
import docgen
import iper
import cumplimiento
from core_auth import empresa_required, onboarding_required, empresa_id
from formato import normalizar_control_operativo
from models import sqla, RiesgoItem, RequisitoLegal

from . import service

bp = Blueprint('matriz_riesgos', __name__, template_folder='templates')

# Campos cuyo texto se normaliza a lista numerada '1.\n2.\n' al guardarse.
_CAMPOS_LISTA = ('medida_control', 'metodo_correcto')


@bp.route('/matriz-riesgos')
@empresa_required
@onboarding_required
def panel():
    """Matriz de Riesgos: Proceso → Tarea → Puesto → riesgos, con GEMA, VEP y riesgo residual."""
    eid = empresa_id()
    datos = service.cargar(eid, session.get('nombre'))
    return render_template('matriz_riesgos/panel.html',
                           empresa=db.empresa_de(session.get('rut'), eid),
                           gema=iper.GEMA, tipos_control=iper.TIPOS_CONTROL,
                           escala_p=iper.PROBABILIDAD, escala_c=iper.CONSECUENCIA,
                           **datos)


@bp.route('/api/miper', methods=['GET'])
@empresa_required
@onboarding_required
def api_miper():
    """Matriz de riesgos vigente: tareas → riesgos (con VEP/magnitud/método) + contexto minero."""
    eid = empresa_id()
    m = db.matriz_riesgo_vigente(eid)
    if not m:
        db.crear_matriz_riesgo(eid, session.get('nombre'))
        m = db.matriz_riesgo_vigente(eid)
    tareas = db.tareas_de_matriz(m['id'])
    for t in tareas:
        t['riesgos'] = db.riesgos_de_tarea(t['id'])
        t['trabajadores'] = [x['id'] for x in db.trabajadores_de_tarea(t['id'])]
    return jsonify({'matriz': m, 'tareas': tareas,
                    'mineros': db.contratos_mineros_de(eid), 'ecf_puntos': iper.ECF_PUNTOS,
                    'gema': iper.GEMA, 'tipos_control': iper.TIPOS_CONTROL,
                    'escala': {'probabilidad': iper.PROBABILIDAD, 'consecuencia': iper.CONSECUENCIA}})


@bp.route('/api/miper/tareas', methods=['POST'])
@empresa_required
@onboarding_required
def api_miper_tarea():
    """Crea una tarea manual con sus riesgos. Si guardar_biblioteca=1, la persiste para reuso."""
    f = request.get_json(silent=True) or {}
    nombre = (f.get('nombre') or '').strip()
    if not nombre:
        return jsonify({'error': 'Indica el nombre de la tarea.'}), 400
    eid = empresa_id()
    m = db.matriz_riesgo_vigente(eid) or {'id': db.crear_matriz_riesgo(eid, session.get('nombre'))}
    mid = m['id'] if isinstance(m, dict) else m
    tid = db.tarea_crear(mid, nombre, proceso=(f.get('proceso') or '').strip() or None,
                         responsable=(f.get('responsable') or '').strip() or None,
                         rutinaria=(f.get('rutinaria') or '').strip() or None,
                         puesto=(f.get('puesto') or '').strip() or None)
    for r in (f.get('riesgos') or []):
        rid = db.riesgo_agregar(mid, r.get('peligro'), r.get('riesgo'),
                                normalizar_control_operativo(r.get('medida_control')),
                                probabilidad=r.get('probabilidad'), consecuencia=r.get('consecuencia'),
                                metodo_correcto=normalizar_control_operativo(r.get('metodo_correcto')),
                                tipo_control=r.get('tipo_control'), gema=r.get('gema'),
                                contrato_id=r.get('contrato_id') or None,
                                ecf_punto=r.get('ecf_punto'), mfl=r.get('mfl'), bowtie=r.get('bowtie'),
                                tarea_id=tid)
    sqla.session.commit()
    # auto-aprendizaje: guardar en biblioteca personalizada
    if f.get('guardar_biblioteca'):
        for r in (f.get('riesgos') or [{}]):
            db.biblioteca_crear(eid, nombre, peligro=r.get('peligro'), riesgo=r.get('riesgo'),
                                medida_control=r.get('medida_control'),
                                metodo_correcto=r.get('metodo_correcto'),
                                probabilidad=r.get('probabilidad'), consecuencia=r.get('consecuencia'))
    db.aplicar_herencia_controles(eid)
    return jsonify({'ok': True, 'tarea_id': tid})


@bp.route('/api/miper/sugerencia', methods=['GET'])
@empresa_required
@onboarding_required
def api_miper_sugerencia():
    """Sugiere el requisito legal aplicable a una actividad/peligro/riesgo (MIPER → Legal)."""
    return jsonify({'sugerencia': iper.sugerir_requisito(request.args.get('texto', ''))})


@bp.route('/api/miper/riesgo/<int:rid>/vincular-legal', methods=['POST'])
@empresa_required
@onboarding_required
def api_miper_vincular_legal(rid):
    """Vincula el riesgo con el requisito legal sugerido (creándolo en la Matriz Legal si falta).
    Tras vincular, aplica la herencia: si ese requisito ya está Cumple, el control se valida solo."""
    f = request.get_json(silent=True) or {}
    eid = empresa_id()
    s = f.get('sugerencia') or iper.sugerir_requisito(f.get('texto', ''))
    if not s:
        return jsonify({'error': 'Sin requisito sugerido.'}), 400
    req_row = db.asegurar_requisito_sugerido(eid, s)
    db.vincular_riesgo_requisito(rid, req_row)
    db.aplicar_herencia_controles(eid, requisito_id=req_row)
    return jsonify({'ok': True, 'requisito_row_id': req_row, 'cuerpo_legal': s.get('cuerpo_legal'),
                    'riesgo': (RiesgoItem.query.get(rid).to_dict() if RiesgoItem.query.get(rid) else None)})


@bp.route('/api/miper/desde-requisito', methods=['POST'])
@empresa_required
@onboarding_required
def api_miper_desde_requisito():
    """Legal → MIPER: crea una tarea/riesgo en la MIPER a partir de un requisito legal, ya vinculado."""
    f = request.get_json(silent=True) or {}
    eid = empresa_id()
    req = RequisitoLegal.query.filter_by(id=f.get('requisito_id'), empresa_id=eid).first()
    if not req:
        return jsonify({'error': 'Requisito no encontrado.'}), 404
    m = db.matriz_riesgo_vigente(eid) or {'id': db.crear_matriz_riesgo(eid, session.get('nombre'))}
    mid = m['id'] if isinstance(m, dict) else m
    nombre = (req.requisito_legal or req.cuerpo_normativo or 'Actividad legal')[:60]
    tid = db.tarea_crear(mid, nombre, proceso='Legal')
    rid = db.riesgo_agregar(mid, req.riesgo_asociado or '', req.requisito_legal or '',
                            req.control_operativo or '', probabilidad=2, consecuencia=2,
                            tipo_control='administrativo', requisito_legal_id=req.id, tarea_id=tid)
    db.aplicar_herencia_controles(eid, requisito_id=req.id)
    return jsonify({'ok': True, 'tarea_id': tid, 'riesgo_id': rid})


@bp.route('/api/miper/riesgo', methods=['POST'])
@empresa_required
@onboarding_required
def api_miper_riesgo_add():
    """Agrega un riesgo a una tarea existente."""
    f = request.get_json(silent=True) or {}
    tid, eid = f.get('tarea_id'), empresa_id()
    m = db.matriz_riesgo_vigente(eid)
    if not (m and tid):
        return jsonify({'error': 'Falta matriz o tarea.'}), 400
    rid = db.riesgo_agregar(m['id'], f.get('peligro'), f.get('riesgo'),
                            normalizar_control_operativo(f.get('medida_control')),
                            probabilidad=f.get('probabilidad'), consecuencia=f.get('consecuencia'),
                            metodo_correcto=normalizar_control_operativo(f.get('metodo_correcto')),
                            tipo_control=f.get('tipo_control'), gema=f.get('gema'),
                            contrato_id=f.get('contrato_id') or None, tarea_id=int(tid))
    db.aplicar_herencia_controles(eid)
    return jsonify({'ok': True, 'riesgo_id': rid,
                    'riesgo': RiesgoItem.query.get(rid).to_dict()})


@bp.route('/api/miper/riesgo/<int:rid>/campo', methods=['POST'])
@empresa_required
@onboarding_required
def api_miper_riesgo_campo(rid):
    """Edita en línea un campo del riesgo (recalcula VEP y residual). Si cambia una
    medida/método/peligro/riesgo, dispara la cascada al IRL (Art. 15 DS 44): regenera los IRL de
    los trabajadores afectados con aviso de que requieren nueva firma.

    Si lo que cambia es la medida de control de un riesgo amarrado a un requisito legal, se usa
    db.riesgo_editar_control: ese requisito queda 'en_revision' y se deja traza en la bitácora
    (el control cambió, la validación legal previa ya no vale)."""
    f = request.get_json(silent=True) or {}
    campo, valor = f.get('campo'), f.get('valor')
    if campo in _CAMPOS_LISTA:
        valor = normalizar_control_operativo(valor)

    it_row = RiesgoItem.query.get(rid)
    if campo == 'medida_control' and it_row and it_row.requisito_legal_id:
        it = db.riesgo_editar_control(rid, valor, quien=session.get('nombre') or session.get('rut'))
        afecta_irl = True
    else:
        it, afecta_irl = db.riesgo_editar(rid, campo, valor)
    if it is None:
        return jsonify({'error': 'Campo no editable o riesgo no encontrado.'}), 400

    resp = {'ok': True, 'riesgo': it, 'irls_actualizados': []}
    if afecta_irl and it.get('tarea_id'):
        rut, eid = session['rut'], empresa_id()
        empresa = db.empresa_de(rut, eid)
        afectados = docgen.regenerar_irls_de_tarea(
            db, empresa, it['tarea_id'], session.get('nombre') or rut,
            logo_data_uri=docgen.logo_empresa(db, rut, eid),
            motivo=f'Cambio en “{campo}” de la Matriz IPER')
        resp['irls_actualizados'] = afectados
    return jsonify(resp)


@bp.route('/api/miper/riesgo/<int:rid>/eliminar', methods=['POST'])
@empresa_required
@onboarding_required
def api_miper_riesgo_del(rid):
    it = RiesgoItem.query.get(rid)
    m = db.matriz_riesgo_vigente(empresa_id())
    if it and m and it.matriz_id == m['id']:
        sqla.session.delete(it)
        sqla.session.commit()
    return jsonify({'ok': True})


@bp.route('/api/miper/versionar', methods=['POST'])
@empresa_required
@onboarding_required
def api_miper_versionar():
    f = request.get_json(silent=True) or {}
    motivo = (f.get('motivo') or 'Revisión periódica').strip()
    nueva = db.bloquear_y_versionar(empresa_id(), motivo, session.get('nombre'))
    return jsonify({'ok': True, 'matriz': nueva})
