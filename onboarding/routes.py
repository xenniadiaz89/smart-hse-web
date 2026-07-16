"""Panel de Bienvenida — captura obligatoria de los datos legales de la empresa.

Bloquea el resto de la consola hasta estar completo (ver core_auth.onboarding_required).
"""
from flask import Blueprint, render_template, request, jsonify, session

import db
import iper
import planes
from core_auth import login_required, onboarding_completo

from . import service

bp = Blueprint('onboarding', __name__, template_folder='templates')


@bp.route('/onboarding')
@login_required
def panel():
    emp = db.empresa_de(session.get('rut'), session.get('empresa_id'))   # None si aún no hay empresa
    return render_template('onboarding/panel.html', empresa=emp, mutuales=iper.MUTUALES,
                           tramos=planes.PLANES, completo=onboarding_completo(emp))


@bp.route('/api/onboarding', methods=['POST'])
@login_required
def guardar():
    ok, datos, err = service.validar(request.get_json(silent=True) or {})
    if not ok:
        return jsonify({'error': err}), 400
    eid = service.persistir(session['rut'], session.get('empresa_id'), datos)
    session['empresa_id'] = eid
    # La dotación declarada define si CORE-06 (CPHS) y CORE-08 (1%) le aplican a esta empresa.
    tocados = db.aplicar_reglas_dotacion(eid)
    return jsonify({'ok': True, 'empresa_id': eid, 'requisitos_actualizados': tocados,
                    'redirect': '/dashboard'})
