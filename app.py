import os
import json
import re
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'smarthse-dev-key-cambiar-en-render')

USERS_FILE = os.path.join(os.path.dirname(__file__), 'usuarios.json')


# ─────────────────────────── Almacén de usuarios ───────────────────────────
def cargar_usuarios():
    try:
        with open(USERS_FILE, encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def guardar_usuarios(data):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─────────────────────────── Utilidades RUT / clave ────────────────────────
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


def clave_valida(c):
    """Alfanumérica: mín. 6 caracteres con al menos una letra y un dígito."""
    return bool(c) and len(c) >= 6 and re.search(r'[A-Za-z]', c) and re.search(r'\d', c)


# ─────────────────────────── Control de acceso ─────────────────────────────
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('rut'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


# ─────────────────────────────── Rutas ─────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        rut = normalizar_rut(request.form.get('rut', ''))
        clave = request.form.get('clave', '')
        usuarios = cargar_usuarios()
        u = usuarios.get(rut)
        if u and check_password_hash(u['pass_hash'], clave):
            session['rut'] = rut
            session['sns'] = u['sns']
            session['nombre'] = u['nombre']
            session['rol'] = u.get('rol', '')
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='RUT o clave incorrectos.', rut=request.form.get('rut', ''))
    return render_template('login.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        f = request.form
        nombre = (f.get('nombre', '')).strip()
        rut_raw = f.get('rut', '')
        sns = (f.get('sns', '')).strip()
        rol = f.get('rol', '')
        clave = f.get('clave', '')
        clave2 = f.get('clave2', '')
        datos = {'nombre': nombre, 'rut': rut_raw, 'sns': sns, 'rol': rol}

        if not (nombre and sns):
            return render_template('registro.html', error='Completa nombre y N° SNS.', **datos)
        if not rut_valido(rut_raw):
            return render_template('registro.html', error='El RUT ingresado no es válido.', **datos)
        if not clave_valida(clave):
            return render_template('registro.html', error='La clave debe ser alfanumérica, mínimo 6 caracteres con letras y números.', **datos)
        if clave != clave2:
            return render_template('registro.html', error='Las claves no coinciden.', **datos)

        rut = normalizar_rut(rut_raw)
        usuarios = cargar_usuarios()
        if rut in usuarios:
            return render_template('registro.html', error='Ya existe una cuenta con ese RUT.', **datos)

        usuarios[rut] = {
            'nombre': nombre, 'sns': sns, 'rol': rol,
            'pass_hash': generate_password_hash(clave),
        }
        guardar_usuarios(usuarios)
        session['rut'] = rut
        session['sns'] = sns
        session['nombre'] = nombre
        session['rol'] = rol
        return redirect(url_for('dashboard'))
    return render_template('registro.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', nombre=session.get('nombre'),
                           sns=session.get('sns'), rol=session.get('rol'))


@app.route('/contratistas')
def contratistas():
    return render_template('contratistas.html')


@app.route('/legislacion')
def legislacion():
    return render_template('legislacion.html')


if __name__ == '__main__':
    app.run(debug=True, port=5000)
