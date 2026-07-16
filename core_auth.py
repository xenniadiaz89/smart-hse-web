"""Núcleo de control de acceso y utilidades de RUT.

Vive fuera de app.py para que los módulos aislados (onboarding/, matriz_legal/) puedan
importar los decoradores sin caer en un import circular (app.py importa los módulos y los
módulos importarían app.py). app.py re-importa estos nombres, así que sus rutas no cambian.
"""
import re
from functools import wraps

from flask import request, session, redirect, url_for, jsonify


# ─────────────────────────── Utilidades RUT ────────────────────────────────
def normalizar_rut(rut):
    """Quita puntos y guion, deja el dígito verificador en mayúscula."""
    r = re.sub(r'[^0-9kK]', '', rut or '').upper()
    if len(r) < 2:
        return r
    return r[:-1] + '-' + r[-1]


def rut_valido(rut):
    """Valida el dígito verificador chileno (módulo 11)."""
    r = re.sub(r'[^0-9kK]', '', rut or '').upper()
    if len(r) < 2:
        return False
    cuerpo, dv = r[:-1], r[-1]
    if not cuerpo.isdigit():
        return False
    suma, factor = 0, 2
    for d in reversed(cuerpo):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - (suma % 11)
    dv_calc = 'K' if resto == 10 else '0' if resto == 11 else str(resto)
    return dv == dv_calc


# ─────────────────────────── Control de acceso ─────────────────────────────
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('rut'):
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Sesión expirada. Reingresa a la consola.'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


def empresa_id():
    """Empresa en foco (Ronda 12). None si el asesor aún no seleccionó una."""
    return session.get('empresa_id')


def empresa_required(f):
    """Exige empresa activa. Para /api → 409 JSON; para vistas → redirige a Mis Empresas."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('rut'):
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Sesión expirada. Reingresa a la consola.'}), 401
            return redirect(url_for('login'))
        if not session.get('empresa_id'):
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Selecciona o registra una empresa primero.'}), 409
            return redirect(url_for('empresas'))
        return f(*args, **kwargs)
    return wrapper


# ─────────────────────────── Onboarding obligatorio ────────────────────────
# El módulo onboarding/ puede caer al importar (aislamiento por Blueprint). Si eso pasa,
# onboarding_required debe FAIL-OPEN: bloquear el acceso sin poder ofrecer el panel donde
# desbloquearlo dejaría al usuario encerrado. app.py fija este flag tras registrar los módulos.
_MODULO_ONBOARDING_OK = {'v': True}


def set_onboarding_disponible(ok):
    _MODULO_ONBOARDING_OK['v'] = bool(ok)


def onboarding_completo(emp):
    """emp = dict de db.empresa_de(). Completo = los 5 datos legales del alta presentes."""
    if not emp:
        return False
    campos = ('razon_social', 'rut_empresa', 'mutual', 'n_adherente')
    if not all(str(emp.get(k) or '').strip() for k in campos):
        return False
    try:
        return int(emp.get('dotacion') or 0) > 0
    except (TypeError, ValueError):
        return False


def onboarding_required(f):
    """Exige los datos legales de la empresa completos. Se apila DEBAJO de empresa_required
    (sesión → empresa activa → datos completos); no lo reemplaza. Mismo contrato: 409 JSON
    en /api, redirect en vistas."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not _MODULO_ONBOARDING_OK['v']:
            return f(*args, **kwargs)          # módulo caído: no encerrar al usuario
        import db
        emp = db.empresa_de(session.get('rut'), session.get('empresa_id'))
        if not onboarding_completo(emp):
            if request.path.startswith('/api/'):
                return jsonify({'error': 'onboarding_incompleto',
                                'mensaje': 'Completa los datos de tu empresa para habilitar este módulo.'}), 409
            return redirect(url_for('onboarding.panel'))
        return f(*args, **kwargs)
    return wrapper
