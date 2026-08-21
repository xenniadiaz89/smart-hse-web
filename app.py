import os
import json
import re
from io import BytesIO
from datetime import date
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify, send_file)
from werkzeug.security import generate_password_hash, check_password_hash

from models import sqla
import core_auth
from core_auth import (normalizar_rut, rut_valido, login_required,      # noqa: F401
                       empresa_required, onboarding_required,
                       empresa_id as _empresa_id)
import db
import fuf
import catalogo_documentos_ds44
import catalogo_protocolos
import normativa
import planes
import ia
import correccion
import cumplimiento
import alertas
import docgen
import iper
import vehiculos
import reportes
import formatos
import orientacion_evaluador
import correo

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'smarthse-dev-key-cambiar-en-render')

# ── Base de datos: PostgreSQL en producción (DATABASE_URL), SQLite en local ──
_db_url = os.environ.get('DATABASE_URL', '')
if _db_url.startswith('postgres://'):          # Render entrega 'postgres://'; SQLAlchemy pide 'postgresql://'
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url or 'sqlite:///' + os.path.join(
    os.path.dirname(__file__), 'smarthse.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Alarma anti-pérdida de datos: dejar claro en los logs qué backend de BD se usa. En Render (var RENDER)
# SIN DATABASE_URL, la app caería a SQLite en disco EFÍMERO → los datos se pierden en cada reinicio/dormida.
# Se avisa de forma inequívoca para detectarlo al instante (antes de que un usuario pierda su trabajo).
_en_render = bool(os.environ.get('RENDER'))
if _db_url:
    try:
        _host = _db_url.split('@', 1)[1].split('/', 1)[0]
    except Exception:
        _host = '(host?)'
    print(f'[Smart HSE] Base de datos: POSTGRES persistente @ {_host}', flush=True)
elif _en_render:
    print('\n' + '=' * 78 +
          '\n⚠️  [Smart HSE] SIN DATABASE_URL en Render: usando SQLite EFÍMERO.'
          '\n⚠️  LOS DATOS (registro, empresas, avances) SE PERDERÁN en cada reinicio/dormida.'
          '\n⚠️  Conecta un Postgres persistente (Neon/Supabase/Render) en Environment → DATABASE_URL.'
          '\n' + '=' * 78 + '\n', flush=True)
else:
    print('[Smart HSE] Base de datos: SQLite local (desarrollo).', flush=True)

# Hotfix deploy v3: SOLO en Postgres (prod), conexión que FALLA RÁPIDO. Si el Postgres de Render está
# suspendido/expirado y su host traga los paquetes, un connect sin timeout CUELGA el arranque → gunicorn
# mata el worker por timeout → "Exited with status 1" (un SIGKILL durante el cuelgue NO es una excepción,
# así que las guardas try/except no lo ven). Con connect_timeout el connect lanza OperationalError en ≤5s
# → lo atrapa la guarda de init_db → el servicio SUBE (Live, degradado) y el error real queda en Logs.
# No se aplica a SQLite (su DBAPI no acepta connect_timeout).
if _db_url:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,                  # descarta conexiones muertas del pool antes de usarlas
        'connect_args': {'connect_timeout': 5},  # psycopg2: falla en ≤5s en vez de colgarse indefinido
    }

# Arranque tolerante a fallos (Hotfix deploy v2). El crash de "Exited with status 1" ocurría en
# sqla.init_app(), que dentro llama create_engine e IMPORTA psycopg2 y parsea DATABASE_URL. Se hace en
# dos capas guardadas:
#   (1) init_app UNA sola vez al arrancar (Flask bloquea el setup tras la 1ª request, así que no se
#       reintenta): si el driver no está o la URL es inválida, NO se tumba el worker; se loguea la traza
#       y el servicio sube igual (queda Live, con el error visible en Logs).
#   (2) init_db (conexión + create_all + seeds) sí se reintenta en cada request hasta lograrlo, para
#       recuperarse de una caída/latencia transitoria del Postgres.
_db_app_bound = False
_db_ready = False

try:
    sqla.init_app(app)                          # importa psycopg2 + parsea URL (paso que reventaba)
    _db_app_bound = True
except Exception:
    import traceback
    traceback.print_exc()                       # driver ausente / URL inválida → visible en Logs de Render


def _try_init_db():
    global _db_ready
    if _db_ready or not _db_app_bound:
        return
    try:
        with app.app_context():
            db.init_db()                        # crea tablas (auto-migración) + siembra
        _db_ready = True
    except Exception:
        import traceback
        traceback.print_exc()                   # el error real queda visible en los logs de Render


_try_init_db()                                  # intento al arrancar (sin tumbar el worker)


@app.before_request
def _ensure_db_ready():
    if not _db_ready:
        _try_init_db()


# ──────────────────── Módulos aislados (Blueprints) ────────────────────────
# Cada submódulo vive en su carpeta y se registra por separado. Si uno revienta al importar,
# el error queda encapsulado ahí: se anota como caído, su ítem del sidebar sale deshabilitado
# y el resto de Smart HSE arranca normal. gunicorn importa app:app una vez por worker.
MODULOS_OK = {}


def _registrar(nombre, ruta_modulo, attr='bp'):
    try:
        mod = __import__(ruta_modulo, fromlist=[attr])
        app.register_blueprint(getattr(mod, attr))
        MODULOS_OK[nombre] = True
    except Exception:
        import traceback
        traceback.print_exc()                   # el error real queda visible en los logs de Render
        print(f'[Smart HSE] ⚠️  Módulo "{nombre}" NO disponible (ver traza arriba). '
              'El resto de la app sigue operativa.', flush=True)
        MODULOS_OK[nombre] = False


_registrar('onboarding', 'onboarding')
_registrar('matriz_legal', 'matriz_legal')
_registrar('matriz_riesgos', 'matriz_riesgos')
_registrar('nomina', 'nomina')
_registrar('cphs', 'cphs')
_registrar('auditoria', 'auditoria')
_registrar('grd', 'grd')
_registrar('protocolos_gantt', 'protocolos_gantt')
_registrar('siniestros', 'siniestros')

# Si el módulo de onboarding cayó, no se puede exigir onboarding: dejaría al usuario bloqueado
# sin la pantalla donde desbloquearse.
core_auth.set_onboarding_disponible(MODULOS_OK.get('onboarding', False))


@app.context_processor
def _inyectar_modulos():
    return {'MODULOS_OK': MODULOS_OK}


# ─────────────────────────── Utilidades RUT / clave ────────────────────────
# normalizar_rut, rut_valido, login_required, _empresa_id y empresa_required viven ahora en
# core_auth.py (los módulos aislados los necesitan sin importar app.py). Se re-importan con
# los mismos nombres, así que las rutas de este archivo no cambian.
def clave_valida(c):
    """Alfanumérica: mín. 6 caracteres con al menos una letra y un dígito."""
    return bool(c) and len(c) >= 6 and re.search(r'[A-Za-z]', c) and re.search(r'\d', c)


def normalizar_id(valor):
    """Normaliza el N° SNS para usarlo como clave de cuenta (sin puntos/guion, mayúsculas)."""
    return re.sub(r'[^0-9A-Za-z]', '', valor or '').upper()


# ─────────────────────────── Control de acceso ─────────────────────────────
# (definidos en core_auth.py — ver el re-import en la cabecera de imports)


# ─────────────────────────────── Rutas ─────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Acceso exclusivo con RUT + clave."""
    if request.method == 'POST':
        rut_raw = request.form.get('rut', '')
        clave = request.form.get('clave', '')
        key = normalizar_rut(rut_raw)
        u = db.usuario_get(key)
        if not u or not (u.get('pass_hash') and check_password_hash(u['pass_hash'], clave)):
            return render_template('login.html', error='RUT o clave incorrectos.', rut=rut_raw)
        session['rut'] = key                 # llave de cuenta = RUT normalizado
        session['sns'] = u.get('sns') or ''  # ID profesional visible
        session['nombre'] = u.get('nombre')
        session['rol'] = u.get('rol', 'asesor')
        return redirect(url_for('dashboard'))
    aviso = 'Tu clave fue actualizada. Ya puedes iniciar sesión.' if request.args.get('reset') == 'ok' else None
    return render_template('login.html', aviso=aviso)


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """Registro con RUT + clave + SNS (ID profesional) + nombre. El SNS se pide solo aquí."""
    if request.method == 'POST':
        f = request.form
        nombre = (f.get('nombre', '')).strip()
        rut_raw = (f.get('rut', '')).strip()
        sns = (f.get('sns', '')).strip()
        clave = f.get('clave', '')
        email = (f.get('email', '')).strip()
        datos = {'nombre': nombre, 'rut': rut_raw, 'sns': sns, 'email': email}

        if not (nombre and rut_raw and sns and email):
            return render_template('registro.html', error='Completa nombre, RUT, N° SNS y correo.', **datos)
        if not rut_valido(rut_raw):
            return render_template('registro.html', error='El RUT ingresado no es válido.', **datos)
        if '@' not in email or '.' not in email.split('@')[-1]:
            return render_template('registro.html', error='Indica un correo válido.', **datos)
        if not clave_valida(clave):
            return render_template('registro.html',
                                   error='La clave debe ser alfanumérica de al menos 6 caracteres (con letras y números).', **datos)

        key = normalizar_rut(rut_raw)
        if db.usuario_get(key):
            return render_template('registro.html', error='Ya existe una cuenta con ese RUT.', **datos)

        db.usuario_crear(key, rut_raw, sns, nombre, rol='asesor',
                         pass_hash=generate_password_hash(clave), email=email)
        session['rut'] = key
        session['sns'] = sns
        session['nombre'] = nombre
        session['rol'] = 'asesor'
        session.pop('empresa_id', None)
        # Ronda 18: entra directo a la consola; la empresa se registra dentro de "Mis Contratos".
        return redirect(url_for('dashboard'))
    return render_template('registro.html')


@app.route('/olvide-clave', methods=['GET', 'POST'])
def olvide_clave():
    """Pide el RUT (mismo identificador del login) y, si la cuenta tiene un correo asociado,
    envía un link de recuperación de un solo uso (1 hora). El mensaje es siempre el mismo,
    exista o no la cuenta, para no permitir enumerar RUTs registrados."""
    enviado = False
    if request.method == 'POST':
        rut_raw = (request.form.get('rut') or '').strip()
        key = normalizar_rut(rut_raw)
        email, token = db.usuario_crear_reset_token(key)
        if email and token:
            correo.enviar_reset_clave(email, token, request.host_url)
        enviado = True
    return render_template('olvide_clave.html', enviado=enviado)


@app.route('/reset-clave/<token>', methods=['GET', 'POST'])
def reset_clave(token):
    u = db.usuario_validar_reset_token(token)
    if not u:
        return render_template('reset_clave.html', invalido=True)
    if request.method == 'POST':
        clave = request.form.get('clave', '')
        if not clave_valida(clave):
            return render_template('reset_clave.html', token=token,
                                   error='La clave debe ser alfanumérica de al menos 6 caracteres (con letras y números).')
        db.usuario_set_pass_hash(u['rut'], generate_password_hash(clave))
        return redirect(url_for('login', reset='ok'))
    return render_template('reset_clave.html', token=token)


@app.route('/prueba')
def prueba():
    """Acceso de PRUEBA momentáneo (sin pago). Identidad demo FIJA ('DEMO') y una
    empresa demo estable para que el workspace sobreviva reinicios/cookies perdidas.
    TEMPORAL: cuando se active el cobro, se reemplaza por el flujo de pago."""
    session['rut'] = 'DEMO'
    session['sns'] = 'DEMO'
    session['nombre'] = 'Usuario de Prueba'
    session['rol'] = 'asesor'
    emps = db.empresas_de('DEMO')
    if emps:
        session['empresa_id'] = emps[0]['id']
    else:
        # Marca blanca (Ronda 21): empresa demo neutra, sin datos corporativos de terceros.
        session['empresa_id'] = db.crear_empresa('DEMO', 'Empresa Demo (Smart HSE)', rubro='Servicios')
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ── Empresas (Ronda 18: gestión dentro de la consola, en "Mis Contratos") ──
@app.route('/empresas')
@login_required
def empresas():
    """Compatibilidad: la pantalla /empresas se retiró; ahora la empresa se gestiona en la
    consola ("Mis Contratos"). Redirige al dashboard."""
    return redirect(url_for('dashboard'))


@app.route('/empresas/<int:eid>/seleccionar')
@login_required
def empresa_seleccionar(eid):
    if db.empresa_de(session['rut'], eid):
        session['empresa_id'] = eid
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Consola de Gestión Operativa. Si aún no hay empresa activa, entra igual: 'Mis Contratos'
    muestra el alta de empresa (Ronda 18). Si hay empresas pero ninguna activa, toma la primera."""
    emp = None
    eid = session.get('empresa_id')
    if eid:
        emp = db.empresa_de(session['rut'], eid)
        if not emp:
            session.pop('empresa_id', None)
    if not emp:
        emps = db.empresas_de(session['rut'])
        if emps:
            session['empresa_id'] = emps[0]['id']
            emp = emps[0]
    # Aplicabilidad por dotación de los ítems FUF del CPHS/Delegado. Se recalcula al entrar para
    # que las empresas ya creadas se regularicen sin esperar un alta de trabajador.
    dotacion = 0
    if emp:
        try:
            db.aplicar_reglas_dotacion_fuf(emp['id'], rut=session['rut'])
            db.aplicar_regla_miper_fuf(emp['id'], rut=session['rut'])
            dotacion = db.dotacion_efectiva(emp['id'])
        except Exception:      # noqa: BLE001 — el dashboard entra igual
            pass
    # Enriquecer con el flag de "formato Word descargable" por ítem (sin ensuciar el catálogo).
    fuf_catalogo = catalogo_documentos_ds44.enriquecer_fuf(fuf.SECCIONES)
    for s in fuf_catalogo:
        for it in s['items']:
            it['formato'] = formatos.tiene_formato(it['n'])
            it['sugerencia'] = orientacion_evaluador.ORIENTACION.get(it['n'])
    # Trazabilidad del FUF 44 (solo lectura, tarjeta "Panel FUF 44" en Cumplimiento DS 44) —
    # vivía en Matriz Legal; se trasladó aquí porque "Cumplimiento Legal" ahora es solo la matriz.
    fuf_estados = db.estados_fuf(emp['id']) if emp else {}
    return render_template('dashboard.html', nombre=session.get('nombre'),
                           sns=session.get('sns'), rol=session.get('rol'), empresa=emp,
                           onboarding_ok=core_auth.onboarding_completo(emp),
                           dotacion_efectiva=dotacion,       # gatea el nav del Comité Paritario
                           fuf_catalogo=fuf_catalogo,   # el modal FUF lo recibe por tojson
                           fuf_secciones=fuf.SECCIONES, fuf_estados=fuf_estados,
                           fuf_resumen=fuf.resumen(fuf_estados))


# ── API de empresas (gestión desde la consola) ──
@app.route('/api/empresas', methods=['GET'])
@login_required
def api_empresas_get():
    return jsonify({'empresas': db.empresas_de(session['rut']),
                    'activa': session.get('empresa_id')})


# ── Límites del Plan del Asesor (Ronda 20; tramos por empresa en planes.py desde la Ronda 26) ──
MAX_EMPRESAS_BASICO = 30


@app.route('/api/plan', methods=['GET'])
@login_required
def api_plan():
    """Uso del plan: empresas de la cuenta y cupo de nómina de la empresa activa (por tramo)."""
    empresas = db.empresas_de(session['rut'])
    eid = session.get('empresa_id')
    emp = db.empresa_de(session['rut'], eid) if eid else None
    activos = db.trabajadores_activos_count(eid) if eid else 0
    cupo = planes.cupo((emp or {}).get('plan'), activos)
    return jsonify({'empresas': len(empresas), 'max_empresas': MAX_EMPRESAS_BASICO,
                    'cupo': cupo, 'tramos': planes.PLANES,
                    'dotacion_declarada': (emp or {}).get('dotacion'),
                    'dotacion_efectiva': db.dotacion_efectiva(eid) if eid else 0})


# ── Protocolos de Salud (MINSAL) — motor de datos de la Tarjeta 3 del Dashboard DS44 ──
@app.route('/api/protocolos', methods=['GET'])
@empresa_required
@onboarding_required
def api_protocolos_get():
    protos = db.protocolos_de(_empresa_id())
    for p in protos:                      # marca los que tienen Plantilla Maestra (autoeval o carga)
        m = catalogo_protocolos.por_protocolo(p.get('nombre'))
        p['plantilla_tipo'] = m['tipo'] if m else None
    return jsonify(protos)


@app.route('/api/protocolos', methods=['POST'])
@empresa_required
def api_protocolo_crear():
    f = request.get_json(silent=True) or {}
    nombre = (f.get('nombre') or '').strip()
    if not nombre:
        return jsonify({'error': 'Indica el nombre del protocolo.'}), 400
    db.protocolo_crear(_empresa_id(), nombre, f.get('puestos_totales') or 0)
    return jsonify(db.protocolos_de(_empresa_id()))


@app.route('/api/protocolos/<int:pid>', methods=['POST'])
@empresa_required
def api_protocolo_actualizar(pid):
    f = request.get_json(silent=True) or {}
    db.protocolo_actualizar(_empresa_id(), pid, evaluados=f.get('puestos_evaluados'),
                            totales=f.get('puestos_totales'))
    return jsonify(db.protocolos_de(_empresa_id()))


@app.route('/api/protocolos/<int:pid>/eliminar', methods=['POST'])
@empresa_required
def api_protocolo_eliminar(pid):
    db.protocolo_eliminar(_empresa_id(), pid)
    return jsonify(db.protocolos_de(_empresa_id()))


# ── Plantillas Maestras de Protocolos (autoevaluación MINSAL/SUSESO) → Módulo 5 ──
def _protocolo_maestra(pid):
    """(protocolo, plantilla maestra) para un id de ProtocoloSalud, o (proto, None) si no tiene."""
    proto = db.protocolo_por_id(_empresa_id(), pid)
    if not proto:
        return None, None
    return proto, catalogo_protocolos.por_protocolo(proto.get('nombre'))


@app.route('/api/protocolos/<int:pid>/plantilla', methods=['GET'])
@empresa_required
@onboarding_required
def api_protocolo_plantilla(pid):
    """Plantilla Maestra del protocolo (autoevaluación + campos) con la carátula precargada desde
    Empresa y Nómina, más los documentos ya generados/subidos (carpeta del Módulo 5)."""
    rut, eid = session['rut'], _empresa_id()
    proto, maestra = _protocolo_maestra(pid)
    if not proto:
        return jsonify({'error': 'Protocolo no encontrado.'}), 404
    emp = db.empresa_de(rut, eid) or {}
    nomina = db.trabajadores_de(eid)
    return jsonify({
        'protocolo': proto.get('nombre'),
        'maestra': catalogo_protocolos.resumen(maestra),
        'prefill': catalogo_protocolos.prefill(emp, nomina),
        'documentos': db.documentos_protocolo(eid, rut, pid),
    })


@app.route('/api/protocolos/<int:pid>/generar', methods=['POST'])
@empresa_required
@onboarding_required
def api_protocolo_generar(pid):
    """Genera la autoevaluación (PREXOR/TMERT) con auto-llenado + respuestas, la persiste trazable
    al protocolo (categoria='PROTOCOLO') y la devuelve para abrir/imprimir/firmar."""
    rut, eid = session['rut'], _empresa_id()
    proto, maestra = _protocolo_maestra(pid)
    if not proto:
        return jsonify({'error': 'Protocolo no encontrado.'}), 404
    if not maestra or maestra['tipo'] != 'autoevaluacion':
        return jsonify({'error': 'Este protocolo no tiene autoevaluación generable.'}), 400
    f = request.get_json(silent=True) or {}
    emp = db.empresa_de(rut, eid) or {}
    nomina = db.trabajadores_de(eid)
    html = catalogo_protocolos.generar_html(maestra['clave'], f.get('campos') or {},
                                            f.get('respuestas') or {}, emp, nomina)
    cid = db.contrato_base(eid, rut, emp.get('razon_social'))
    nombre = f"{maestra['nombre']}.html"
    doc_id = db.registrar_documento(cid, nombre, 'generado', 'evidencia', item_n=pid,
                                    categoria='PROTOCOLO', contenido=html.encode('utf-8'),
                                    mimetype='text/html; charset=utf-8')
    return jsonify({'ok': True, 'doc_id': doc_id, 'html': html,
                    'documentos': db.documentos_protocolo(eid, rut, pid)})


@app.route('/api/protocolos/<int:pid>/documento', methods=['POST'])
@empresa_required
@onboarding_required
def api_protocolo_subir(pid):
    """Sube el formulario oficial ya aplicado (ej. CEAL-SM) y lo cuelga trazable al protocolo."""
    rut, eid = session['rut'], _empresa_id()
    proto, _ = _protocolo_maestra(pid)
    if not proto:
        return jsonify({'error': 'Protocolo no encontrado.'}), 404
    emp = db.empresa_de(rut, eid) or {}
    cid = db.contrato_base(eid, rut, emp.get('razon_social'))
    archivos = request.files.getlist('archivo') or []
    if not archivos or not any(a and a.filename for a in archivos):
        return jsonify({'error': 'No se recibió archivo.'}), 400
    for archivo in archivos:
        if not archivo or not archivo.filename:
            continue
        db.registrar_documento(cid, archivo.filename, 'oficial', 'evidencia', item_n=pid,
                               categoria='PROTOCOLO', contenido=archivo.read(),
                               mimetype=archivo.mimetype or 'application/octet-stream')
    return jsonify({'ok': True, 'documentos': db.documentos_protocolo(eid, rut, pid)})


# ── Estadísticas de Prevención (empresa transversal) — portada Mis Contratos + FUF 47/60 ──
def _anio_actual():
    return date.today().year


@app.route('/api/estadisticas', methods=['GET'])
@empresa_required
@onboarding_required
def api_estadisticas_get():
    anio = request.args.get('anio', type=int) or _anio_actual()
    eid = _empresa_id()
    return jsonify({'anio': anio, 'filas': db.estadisticas_de(eid, anio),
                    'resumen': db.estadisticas_resumen(eid, anio)})


@app.route('/api/estadisticas', methods=['POST'])
@empresa_required
@onboarding_required
def api_estadisticas_set():
    f = request.get_json(silent=True) or {}
    anio = int(f.get('anio') or _anio_actual())
    mes = int(f.get('mes') or 0)
    if not 1 <= mes <= 12:
        return jsonify({'error': 'Mes inválido.'}), 400
    rut, eid = session['rut'], _empresa_id()
    db.estadistica_set(eid, anio, mes, f.get('datos') or {})
    # Principio transversal: al haber registro de estadísticas, los ítems FUF 47 y 60 quedan Cumple
    # y se propaga al requisito legal de estadísticas (LEG-ESTAD). Best-effort.
    try:
        for it in (47, 60):
            db.fuf_marcar_cumple(eid, it, rut=rut)
            db.sincronizar_fuf_matriz(eid, it)
    except Exception:      # noqa: BLE001
        pass
    return jsonify({'anio': anio, 'filas': db.estadisticas_de(eid, anio),
                    'resumen': db.estadisticas_resumen(eid, anio)})


# ── Capacitaciones Legales por cargo — motor de datos de la Tarjeta 5 ──
@app.route('/api/cargos', methods=['GET'])
@empresa_required
def api_cargos_get():
    return jsonify(db.cargos_de(_empresa_id()))


@app.route('/api/capacitaciones', methods=['GET'])
@empresa_required
@onboarding_required
def api_capacitaciones_get():
    return jsonify({'registros': db.capacitaciones_de(_empresa_id()),
                    'resumen': db.capacitaciones_resumen(_empresa_id()),
                    'cargos': db.cargos_de(_empresa_id()),
                    'catalogo': cumplimiento.CURSOS_LEGALES})


@app.route('/api/capacitaciones', methods=['POST'])
@empresa_required
def api_capacitacion_crear():
    f = request.get_json(silent=True) or {}
    curso = (f.get('curso') or '').strip()
    cargo = (f.get('cargo') or '').strip()
    if not curso or not cargo:
        return jsonify({'error': 'Indica el curso y el cargo.'}), 400
    eid = _empresa_id()
    db.capacitacion_crear(eid, curso, cargo, f.get('n_capacitados') or 0, f.get('n_requeridos') or 0)
    # Sincronización cruzada: si el curso legal se completó (capacitados ≥ requeridos > 0), marca su
    # requisito de la Matriz Legal como 'Cumple' de inmediato.
    matriz_actualizada = None
    try:
        ncap, nreq = int(f.get('n_capacitados') or 0), int(f.get('n_requeridos') or 0)
        if nreq > 0 and ncap >= nreq:
            matriz_actualizada = db.sincronizar_capacitacion_matriz(eid, curso)
    except (TypeError, ValueError):
        pass
    return jsonify({'resumen': db.capacitaciones_resumen(eid), 'matriz_actualizada': matriz_actualizada})


@app.route('/api/capacitaciones/<int:cid>/eliminar', methods=['POST'])
@empresa_required
def api_capacitacion_eliminar(cid):
    db.capacitacion_eliminar(_empresa_id(), cid)
    return jsonify(db.capacitaciones_resumen(_empresa_id()))


# ── Agregado del Dashboard Gerencial DS44 (todo en un JSON, sin hardcode) ──
@app.route('/api/ds44/dashboard', methods=['GET'])
@empresa_required
@onboarding_required
def api_ds44_dashboard():
    eid = _empresa_id()
    # 1-2) FUF: conteos Cumple/No Cumple/N-A + % global de cumplimiento.
    fuf = db.estados_fuf(eid)
    cnt = {'si': 0, 'no': 0, 'na': 0}
    for v in fuf.values():
        e = (v.get('estado') or '').lower()
        if e in cnt:
            cnt[e] += 1
    respondidos = cnt['si'] + cnt['no'] + cnt['na']
    pct_global = round(100 * (cnt['si'] + cnt['na']) / FUF_TOTAL) if FUF_TOTAL else 0
    # 4) Matriz Legal agrupada por área (capa) con % y lista de pendientes.
    capa_label = {'core': 'Legal Core (DS 44 / Nacional)', 'mandante': 'Capa Mandante',
                  'operativa': 'Capa Operativa'}
    cumplido = ('auditado', 'cumple', 'cumplido', 'ok')
    areas = {}
    for r in db.matriz_legal(eid):
        area = capa_label.get((r.get('capa') or 'operativa').lower(), (r.get('capa') or 'General').title())
        a = areas.setdefault(area, {'total': 0, 'ok': 0, 'pendientes': []})
        a['total'] += 1
        if (r.get('estado_avance') or '').lower() in cumplido:
            a['ok'] += 1
        else:
            a['pendientes'].append(r.get('requisito_legal') or r.get('id_requisito') or 'Ítem')
    matriz_areas = [{'area': k, 'total': v['total'], 'ok': v['ok'],
                     'pct': round(100 * v['ok'] / v['total']) if v['total'] else 0,
                     'pendientes': v['pendientes'][:25]}
                    for k, v in sorted(areas.items())]
    return jsonify({
        'fuf': {'si': cnt['si'], 'no': cnt['no'], 'na': cnt['na'],
                'respondidos': respondidos, 'total': FUF_TOTAL, 'pct': pct_global},
        'protocolos': db.protocolos_de(eid),
        'matriz_areas': matriz_areas,
        'capacitaciones': db.capacitaciones_resumen(eid),
    })


@app.route('/api/empresas', methods=['POST'])
@login_required
def api_empresa_crear():
    f = request.get_json(silent=True) or request.form
    razon = (f.get('razon_social') or '').strip()
    if not razon:
        return jsonify({'error': 'Indica la Razón Social.'}), 400
    if len(db.empresas_de(session['rut'])) >= MAX_EMPRESAS_BASICO:
        return jsonify({'error': 'limite_empresas',
                        'mensaje': f'Alcanzaste el límite del Plan Básico ({MAX_EMPRESAS_BASICO} '
                                   'empresas). Migra a un pack corporativo superior para gestionar más.'}), 403
    try:
        dotacion = int(f.get('dotacion') or 0) or None
    except (TypeError, ValueError):
        dotacion = None
    eid = db.crear_empresa(
        session['rut'], razon,
        rut_empresa=(f.get('rut_empresa') or '').strip() or None,
        mutual=(f.get('mutual') or '').strip() or None,
        n_adherente=(f.get('n_adherente') or '').strip() or None,
        rubro=(f.get('rubro') or '').strip() or None,
        dotacion=dotacion)
    session['empresa_id'] = eid
    if dotacion:
        db.aplicar_reglas_dotacion(eid)
    return jsonify({'ok': True, 'empresa_id': eid, 'empresas': db.empresas_de(session['rut'])})


@app.route('/api/empresas/<int:eid>/seleccionar', methods=['POST'])
@login_required
def api_empresa_seleccionar(eid):
    if not db.empresa_de(session['rut'], eid):
        return jsonify({'error': 'Empresa no encontrada.'}), 404
    session['empresa_id'] = eid
    return jsonify({'ok': True, 'empresa_id': eid})


# ── Adhesión a Mutualidad (Ley 16.744) — nivel empresa, una vez por RUT ──
@app.route('/api/empresa/adhesion', methods=['GET'])
@empresa_required
def api_adhesion_get():
    return jsonify(db.adhesion_estado(session['rut'], _empresa_id()))


@app.route('/api/empresa/adhesion', methods=['POST'])
@empresa_required
def api_adhesion_set():
    f = request.get_json(silent=True) or request.form
    db.adhesion_guardar(session['rut'], _empresa_id(),
                        mutual=(f.get('mutual') or '').strip() or None,
                        n_adherente=(f.get('n_adherente') or '').strip() or None)
    return jsonify(db.adhesion_estado(session['rut'], _empresa_id()))


@app.route('/api/empresa/adhesion/<tipo>', methods=['POST'])
@empresa_required
def api_adhesion_cert(tipo):
    if tipo not in ('adhesion', 'siniestralidad', 'cotizaciones'):
        return jsonify({'error': 'Tipo de certificado inválido.'}), 400
    archivo = request.files.get('archivo')
    if not archivo or not archivo.filename:
        return jsonify({'error': 'No se recibió archivo.'}), 400
    rut, eid = session['rut'], _empresa_id()
    emp = db.empresa_de(rut, eid)
    base_cid = db.contrato_base(eid, rut, emp.get('razon_social'))
    doc_id = db.registrar_documento(base_cid, f'cert_{tipo}_{archivo.filename}', 'Adhesión',
                                    f'cert_{tipo}', contenido=archivo.read(),
                                    mimetype=archivo.mimetype or 'application/pdf')
    db.adhesion_set_doc(eid, tipo, doc_id)
    return jsonify(db.adhesion_estado(rut, eid))


@app.route('/contratistas')
def contratistas():
    return render_template('contratistas.html')


@app.route('/legislacion')
def legislacion():
    return render_template('legislacion.html')


# ─────────────────── Motor de cumplimiento: contratos / matrices ────────────
def _consolidar(rut, empresa_id=None):
    """Contratos de la empresa activa del asesor, con su estado consolidado.
    Excluye el 'contrato base' (BASE-*), contenedor interno de docs de la Capa Legal."""
    contratos = [c for c in db.listar_contratos(rut, empresa_id if empresa_id is not None else _empresa_id())
                 if not str(c.get('numero', '')).startswith('BASE-')]
    por_num = {c['id']: c['numero'] for c in contratos}
    salida = []
    for c in contratos:
        estados = db.estados_de_contrato(c['id'])
        controles = []
        for ctrl in normativa.CONTROLES:
            e = estados.get(ctrl['key'])
            estado = e['estado'] if e else 'pendiente'
            origen = por_num.get(e['origen_contrato_id']) if e and e.get('origen_contrato_id') else None
            controles.append({'key': ctrl['key'], 'label': ctrl['label'],
                              'estado': estado, 'origen': origen})
        cerradas = sum(1 for x in controles if x['estado'] in ('aprobado', 'acreditado'))
        try:
            datos = json.loads(c['datos_json']) if c.get('datos_json') else {}
        except (TypeError, ValueError):
            datos = {}
        salida.append({**c, 'controles': controles,
                       'documentos': db.documentos_de(c['id']),
                       'datos': datos,
                       'cerradas': cerradas, 'pendientes': len(controles) - cerradas})
    return salida


def _datos(contrato):
    if contrato and contrato.get('datos_json'):
        try:
            return json.loads(contrato['datos_json'])
        except (TypeError, ValueError):
            return {}
    return {}


# Los helpers de logo viven en docgen.py (Ronda 25) para que los módulos aislados generen
# documentos con logo sin importar app.py. Aquí quedan como envoltorios con la firma de siempre.
def _logo_doc(cid):
    return docgen.logo_doc(db, cid)


def _logo_data_uri(rut, cid):
    return docgen.logo_data_uri(db, rut, cid)


def _replicar_lista(rut):
    return db.listar_contratos(rut, _empresa_id())


def replicar_controles(rut, control_key, origen_contrato_id):
    """Hereda como 'acreditado' un control aprobado a los demás contratos de la empresa."""
    for c in _replicar_lista(rut):
        if c['id'] == origen_contrato_id:
            continue
        if db.estado_control(c['id'], control_key) == 'aprobado':
            continue  # no degradar una aprobación propia
        db.set_estado_control(rut, c['id'], control_key, 'acreditado', origen_contrato_id)


@app.route('/api/contratos', methods=['GET'])
@empresa_required
def api_contratos():
    return jsonify(_consolidar(session['rut']))


@app.route('/api/contratos', methods=['POST'])
@empresa_required
def api_contrato_crear():
    """'Ingresar contrato' — Escenario A (Contratista Minero). El contrato cuelga de la
    empresa activa y hereda su razón social si no se envía otra."""
    f = request.get_json(silent=True) or request.form
    emp = db.empresa_de(session['rut'], _empresa_id()) or {}
    empresa = (f.get('empresa') or '').strip() or emp.get('razon_social') or ''
    numero = (f.get('numero') or '').strip()
    if not empresa or not numero:
        return jsonify({'error': 'Empresa y N° de contrato son obligatorios.'}), 400
    datos = f.get('datos') or {}
    datos_json = json.dumps(datos, ensure_ascii=False) if datos else None
    es_minera = 1 if str(f.get('es_contratista_minera') or '').lower() in ('1', 'si', 'sí', 'true') else 0
    mandante = (f.get('mandante') or '').strip() if es_minera else ''
    cid = db.crear_contrato(session['rut'], empresa, (f.get('faena') or '').strip(),
                            numero, mandante, datos_json, es_contratista_minera=es_minera,
                            empresa_id=_empresa_id())
    return jsonify({'contratos': _consolidar(session['rut']), 'id': cid,
                    'es_contratista_minera': es_minera})


@app.route('/api/contratos/eliminar', methods=['POST'])
@empresa_required
def api_contrato_eliminar():
    f = request.get_json(silent=True) or request.form
    db.eliminar_contrato(session['rut'], int(f.get('id')))
    return jsonify(_consolidar(session['rut']))


# Mandantes mineros parametrizados (selector de derivación / Módulo Puente).
MANDANTES_MINEROS = ['Minera Spence (BHP)', 'Minera El Abra',
                     'Minera Centinela', 'Otra minería']
FUF_TOTAL = fuf.TOTAL   # 60 ítems del FUF DS 44, contados del catálogo (fuf.py) y no a mano


def _gap_analysis(rut, cid):
    """Estado de la base legal DS 44 (FUF del asesor, ya cumplida) tras convertir un contrato
    a contratista minero. El FUF 'suma', no se re-hace."""
    _ce = db.contrato_de(rut, cid) or {}
    fuf = db.estados_fuf(_ce.get('empresa_id') or _empresa_id())
    fuf_ok = sum(1 for r in fuf.values() if r.get('estado') in ('si', 'na'))
    fuf_pct = round(100 * fuf_ok / FUF_TOTAL) if FUF_TOTAL else 0
    return {
        'base_ds44': {'pct': fuf_pct, 'cumplidos': fuf_ok, 'total': FUF_TOTAL,
                      'titulo': 'Base legal DS 44 / FUF (Ley 16.744)'},
        'mensaje': (f'Ya tienes el {fuf_pct}% de la base legal (DS 44) lista. '
                    f'Ve a Gestión de Faena para precargar la Matriz de Riesgos de este contrato.')
    }


@app.route('/api/contratos/<int:cid>/upgrade', methods=['POST'])
@login_required
def api_contrato_upgrade(cid):
    """Módulo Puente: convierte una empresa general en contratista minera SIN
    re-ingresar datos ni perder avance. Reutiliza el contrato + el FUF del asesor;
    solo fija el mandante."""
    rut = session['rut']
    if not db.contrato_de(rut, cid):
        return jsonify({'error': 'Contrato no encontrado.'}), 404
    f = request.get_json(silent=True) or request.form
    mandante = (f.get('mandante') or '').strip()
    if not mandante:
        return jsonify({'error': 'Selecciona el mandante (minería).'}), 400
    actualizado = db.upgrade_a_contratista_minera(rut, cid, mandante)
    if not actualizado:
        return jsonify({'error': 'No se pudo convertir el contrato.'}), 400
    return jsonify({'contratos': _consolidar(rut), 'id': cid,
                    'gap': _gap_analysis(rut, cid)})


@app.route('/api/contratos/<int:cid>/gap', methods=['GET'])
@login_required
def api_contrato_gap(cid):
    rut = session['rut']
    if not db.contrato_de(rut, cid):
        return jsonify({'error': 'Contrato no encontrado.'}), 404
    return jsonify(_gap_analysis(rut, cid))


@app.route('/api/contratos/<int:cid>/matriz', methods=['POST'])
@login_required
def api_subir_matriz(cid):
    rut = session['rut']
    if not db.contrato_de(rut, cid):
        return jsonify({'error': 'Contrato no encontrado.'}), 404
    archivo = request.files.get('archivo')
    if not archivo or not archivo.filename:
        return jsonify({'error': 'No se recibió archivo.'}), 400
    detectados = normativa.parsear_matriz(archivo)
    db.registrar_documento(cid, archivo.filename, request.form.get('flujo', ''), 'matriz')
    aplicados = []
    for d in detectados:
        if d['conforme']:
            db.set_estado_control(rut, cid, d['control_key'], 'aprobado', cid)
            replicar_controles(rut, d['control_key'], cid)
            aplicados.append(normativa.CONTROL_LABEL[d['control_key']])
    return jsonify({'contratos': _consolidar(rut), 'aplicados': aplicados})


# ────────────── Herencia de documentos (Fuente Única de Verdad) ─────────────
def link_document(doc_id, target_contract_id, rut=None):
    """Crea una referencia simbólica (sin copiar archivo) al documento maestro
    `doc_id` dentro del contrato destino. Conserva metadatos de trazabilidad."""
    rut = rut or session['rut']
    master = db.documento_por_id(rut, doc_id)
    if not master:
        return None
    if not db.contrato_de(rut, target_contract_id):
        return None
    if db.existe_referencia(target_contract_id, doc_id):
        return None
    return db.crear_doc_referencia(target_contract_id, master, tipo='matriz')


# ─────────────── Motor lingüístico: vocabulario técnico + corrección ───────
@app.route('/api/vocabulario', methods=['GET'])
@login_required
def api_vocabulario_listar():
    return jsonify(db.vocabulario_listar(solo_activos=False))


@app.route('/api/vocabulario', methods=['POST'])
@login_required
def api_vocabulario_crear():
    f = request.get_json(silent=True) or {}
    termino = (f.get('termino') or '').strip()
    if not termino:
        return jsonify({'error': 'Indica el término o sigla.'}), 400
    db.vocabulario_crear(termino, (f.get('tipo') or 'termino').strip(),
                         (f.get('significado') or '').strip())
    return jsonify(db.vocabulario_listar(solo_activos=False))


@app.route('/api/vocabulario/<int:vid>/eliminar', methods=['POST'])
@login_required
def api_vocabulario_eliminar(vid):
    db.vocabulario_eliminar(vid)
    return jsonify(db.vocabulario_listar(solo_activos=False))


@app.route('/api/corregir', methods=['POST'])
@login_required
def api_corregir():
    """Corrige ortografía/gramática priorizando el vocabulario técnico. Best-effort:
    nunca lanza 500; ante cualquier fallo devuelve el texto original con un flag."""
    f = request.get_json(silent=True) or {}
    texto = f.get('texto') or ''
    try:
        vocab = db.vocabulario_listar(solo_activos=True)
        return jsonify(correccion.corregir_texto(texto, vocab))
    except Exception:                            # noqa: BLE001 — estabilidad ante todo
        return jsonify({'ok': False, 'original': texto, 'corregido': texto,
                        'cambios': [], 'error': 'No se pudo corregir el texto.'})


@app.route('/api/contratos/<int:cid>/documento', methods=['POST'])
@login_required
def api_registrar_doc(cid):
    rut = session['rut']
    if not db.contrato_de(rut, cid):
        return jsonify({'error': 'Contrato no encontrado.'}), 404
    f = request.get_json(silent=True) or request.form
    nombre = (f.get('nombre') or '').strip()
    if not nombre:
        return jsonify({'error': 'Falta el nombre del documento.'}), 400
    db.registrar_documento(cid, nombre, (f.get('flujo') or '').strip(), 'evidencia')
    return jsonify(_consolidar(rut))


# ─────────────────────────── FUF DS 44 (persistencia) ──────────────────────
@app.route('/api/fuf', methods=['GET'])
@empresa_required
@onboarding_required
def api_fuf_get():
    return jsonify(db.estados_fuf(_empresa_id()))


@app.route('/api/fuf', methods=['POST'])
@empresa_required
def api_fuf_guardar():
    """Guarda en bloque los ítems del FUF de la empresa. Exige observación si es 'No Cumple'."""
    f = request.get_json(silent=True) or {}
    items = f.get('items') or []
    rut = session['rut']
    eid = _empresa_id()
    for it in items:
        try:
            n = int(it.get('item_n'))
        except (TypeError, ValueError):
            continue
        estado = (it.get('estado') or 'pendiente').strip()
        if estado not in ('si', 'no', 'na', 'pendiente'):
            estado = 'pendiente'
        obs = (it.get('observacion') or '').strip()
        if estado == 'no' and not obs:
            return jsonify({'error': f'La observación es obligatoria en el ítem {n} (No Cumple).'}), 400
        fecha_comp = (it.get('fecha_compromiso') or '').strip() or None
        responsable = (it.get('responsable') or '').strip()
        db.set_fuf_estado(eid, n, estado, obs, fecha_comp, rut=rut, responsable=responsable)
    return jsonify(db.estados_fuf(eid))


# ───────────── FUF con documentos: cargar el que se tiene o generar el que falta ─────────────
@app.route('/api/fuf/<int:n>/documentos', methods=['GET'])
@empresa_required
@onboarding_required
def api_fuf_documentos(n):
    """Tipos de documento generables/cargables del ítem FUF n + documentos ya cargados/generados."""
    rut, eid = session['rut'], _empresa_id()
    return jsonify({**catalogo_documentos_ds44.resumen_para_item(n),
                    'documentos': db.documentos_fuf(eid, rut, item_n=n)})


def _fuf_propagar(eid, rut, n, doc_id=None):
    """Principio transversal: propaga el Cumple del ítem n. (1.4) marca el requisito de la Matriz
    Legal ligado (fuf_item); (1.3) si el ítem pertenece a un grupo de evidencia compartida, marca
    Cumple los demás ítems del grupo compartiendo el mismo documento (ref_doc_id)."""
    legal, propagados = [], []
    try:
        legal = db.sincronizar_fuf_matriz(eid, n)
        grupo = catalogo_documentos_ds44.grupo_de(n)
        if grupo and doc_id:
            cid = db.contrato_base(eid, rut)
            for m in catalogo_documentos_ds44.items_del_grupo(grupo):
                if m == n or db.documentos_fuf(eid, rut, item_n=m):
                    continue
                db.registrar_documento(cid, f'Evidencia compartida (ítem {n})', 'compartido',
                                       'evidencia', item_n=m, categoria='FUF', ref_doc_id=doc_id)
                db.fuf_marcar_cumple(eid, m, rut=rut)
                db.sincronizar_fuf_matriz(eid, m)
                propagados.append(m)
    except Exception:      # noqa: BLE001 — la propagación es un extra; nunca debe romper la carga
        pass
    return {'legal_actualizados': legal, 'items_propagados': propagados}


@app.route('/api/fuf/<int:n>/documento', methods=['POST'])
@empresa_required
@onboarding_required
def api_fuf_subir(n):
    """Sube el documento real que la empresa ya tiene y lo cuelga del contrato base con item_n=n."""
    rut, eid = session['rut'], _empresa_id()
    emp = db.empresa_de(rut, eid) or {}
    cid = db.contrato_base(eid, rut, emp.get('razon_social'))
    archivos = request.files.getlist('archivo') or []
    if not archivos or not any(a and a.filename for a in archivos):
        return jsonify({'error': 'No se recibió archivo.'}), 400
    doc_id = None
    for archivo in archivos:
        if not archivo or not archivo.filename:
            continue
        contenido = archivo.read()
        doc_id = db.registrar_documento(cid, archivo.filename, '', 'evidencia', item_n=n,
                                        categoria='FUF', contenido=contenido,
                                        mimetype=archivo.mimetype or 'application/octet-stream')
    db.fuf_marcar_cumple(eid, n, rut=rut)
    prop = _fuf_propagar(eid, rut, n, doc_id)
    # Análisis IA best-effort del documento subido contra los mínimos legales del ítem.
    mime = archivos[0].mimetype if archivos else ''
    analisis = ia.inspeccionar_evidencia(catalogo_documentos_ds44.minimos_item(n),
                                         contenido=contenido, mimetype=mime)
    return jsonify({'ok': True, 'documentos': db.documentos_fuf(eid, rut, item_n=n),
                    'analisis': analisis, **prop})


@app.route('/api/fuf/<int:n>/formato', methods=['GET'])
@empresa_required
@onboarding_required
def api_fuf_formato(n):
    """Descarga el formato Word ya hecho del ítem (con el logo de Smart HSE), para rellenar."""
    par = formatos.formato_de(n)
    if not par:
        return ('No hay formato disponible para este ítem.', 404)
    ruta, nombre = par
    data = formatos.brandear_docx(ruta)
    return send_file(BytesIO(data), mimetype=formatos.DOCX_MIME, as_attachment=True,
                     download_name=f'{nombre} - Smart HSE.docx')


@app.route('/api/fuf/<int:n>/generar', methods=['POST'])
@empresa_required
@onboarding_required
def api_fuf_generar(n):
    """Genera el documento desde la plantilla del catálogo con los campos rellenados, lo persiste
    (HTML) trazable al ítem, y lo devuelve para abrir/imprimir."""
    rut, eid = session['rut'], _empresa_id()
    f = request.get_json(silent=True) or {}
    tipo_doc = (f.get('tipo_doc') or '').strip()
    campos = f.get('campos') or {}
    emp = db.empresa_de(rut, eid) or {}

    # Documento Word fiel (Programa/SGSST V8.2, RIOHS…): rellena el .docx real y lo deja para descargar.
    import docx_fill
    if docx_fill.es_docx(tipo_doc):
        # El Programa lleva las medidas de la matriz vigente (ítem 10 del FUF: «medidas
        # preventivas y correctivas según MIPER»). Best-effort: sin matriz, el documento igual sale.
        try:
            medidas = db.medidas_para_programa(eid)
        except Exception:      # noqa: BLE001
            medidas = None
        data, fname = docx_fill.generar_docx(tipo_doc, emp, campos, medidas_miper=medidas)
        if data is None:
            return jsonify({'error': 'No se pudo generar el documento Word.'}), 500
        cid = db.contrato_base(eid, rut, emp.get('razon_social'))
        doc_id = db.registrar_documento(
            cid, fname, 'generado', 'evidencia', item_n=n, categoria='FUF', contenido=data,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        db.fuf_marcar_cumple(eid, n, rut=rut)
        prop = _fuf_propagar(eid, rut, n, doc_id)
        return jsonify({'ok': True, 'doc_id': doc_id, 'descargar': True,
                        'documentos': db.documentos_fuf(eid, rut, item_n=n), **prop})

    doc = catalogo_documentos_ds44.documento(tipo_doc)
    if not doc or n not in doc['items_fuf']:
        return jsonify({'error': 'Tipo de documento no válido para este ítem.'}), 400
    if tipo_doc == 'estadisticas':       # documento data-driven: inyecta la serie de la empresa
        anio = int((campos.get('anio') or 0)) or date.today().year
        campos = {**campos, 'anio': anio, '_resumen': db.estadisticas_resumen(eid, anio)}
    html = catalogo_documentos_ds44.generar_html(tipo_doc, campos, emp)
    cid = db.contrato_base(eid, rut, emp.get('razon_social'))
    nombre = f"{doc['nombre']}.html"
    # Los campos crudos (incluye listas como roles_extra) se guardan para poder reabrir/Editar.
    campos_json = json.dumps({k: v for k, v in campos.items() if not k.startswith('_')}, ensure_ascii=False)
    edit_id = f.get('doc_id')
    if edit_id and db.actualizar_documento_generado(rut, int(edit_id), html.encode('utf-8'),
                                                     mimetype='text/html; charset=utf-8',
                                                     campos_json=campos_json):
        doc_id = int(edit_id)            # Editar: reemplaza el mismo documento (sin duplicar).
    else:
        doc_id = db.registrar_documento(cid, nombre, 'generado', 'evidencia', item_n=n, categoria='FUF',
                                        contenido=html.encode('utf-8'), mimetype='text/html; charset=utf-8',
                                        tipo_doc=tipo_doc, campos_json=campos_json)
    db.fuf_marcar_cumple(eid, n, rut=rut)
    prop = _fuf_propagar(eid, rut, n, doc_id)
    return jsonify({'ok': True, 'doc_id': doc_id, 'html': html,
                    'documentos': db.documentos_fuf(eid, rut, item_n=n), **prop})


# ─────────────────────────── Panel de Brechas (unificado) ──────────────────
def _dias_restantes(fecha_iso):
    if not fecha_iso:
        return None
    try:
        d = date.fromisoformat(fecha_iso)
    except (TypeError, ValueError):
        return None
    return (d - date.today()).days


@app.route('/api/brechas', methods=['GET'])
@empresa_required
@onboarding_required
def api_brechas():
    eid = _empresa_id()
    brechas = []
    for b in db.brechas_fuf(eid):
        brechas.append({
            'fuente': 'fuf',
            'item_n': b['item_n'],
            'etiqueta': f"FUF DS44 N°{b['item_n']}",
            'titulo': '',
            'contrato_id': None,
            'contrato': '—',
            'observacion': b['observacion'] or '',
            'fecha_compromiso': b['fecha_compromiso'] or '',
            'dias_restantes': _dias_restantes(b['fecha_compromiso']),
        })
    return jsonify(brechas)


@app.route('/api/brechas/compromiso', methods=['POST'])
@login_required
def api_brecha_compromiso():
    f = request.get_json(silent=True) or {}
    fuente = f.get('fuente')
    try:
        n = int(f.get('item_n'))
    except (TypeError, ValueError):
        return jsonify({'error': 'item_n inválido.'}), 400
    fecha = (f.get('fecha_compromiso') or '').strip() or None
    if fuente == 'fuf':
        db.set_fuf_compromiso(_empresa_id(), n, fecha)
    else:
        return jsonify({'error': 'fuente inválida.'}), 400
    return jsonify({'ok': True})


# ══════════════ Motor de Cumplimiento: pendientes / matriz / reglas ═════════
@app.route('/api/pendientes', methods=['GET'])
@empresa_required
@onboarding_required
def api_pendientes():
    """Panel de Actividades Pendientes unificado (legal + contractual + operativa),
    con el seguimiento de actualización anual adjunto a cada ítem legal."""
    eid = _empresa_id()
    items = alertas.actividades_pendientes(db, eid)
    seg = db.seguimiento_get(eid)
    for it in items:
        if it.get('tipo') == 'legal' and it.get('categoria') in seg:
            it['seguimiento'] = seg[it['categoria']]
    return jsonify(items)


@app.route('/api/pendientes/<categoria>/seguimiento', methods=['POST'])
@empresa_required
def api_pendiente_seguimiento(categoria):
    """Guarda el comentario y la fecha de compromiso de seguimiento de un documento anual."""
    f = request.get_json(silent=True) or {}
    res = db.seguimiento_set(_empresa_id(), categoria,
                             comentario=(f.get('comentario') or '').strip(),
                             fecha_compromiso=(f.get('fecha_compromiso') or '').strip() or None)
    return jsonify({'ok': True, 'seguimiento': res})


@app.route('/api/pendientes/<categoria>/subir', methods=['POST'])
@empresa_required
def api_pendiente_subir(categoria):
    """Sube la nueva versión de un documento de la Capa Legal, aplica su regla (vencimiento),
    dispara la CASCADA a los contratos mineros y marca el ítem FUF. Doble cobertura."""
    if categoria not in cumplimiento.REGLAS_CUMPLIMIENTO:
        return jsonify({'error': 'Categoría no reconocida.'}), 400
    rut, eid = session['rut'], _empresa_id()
    emp = db.empresa_de(rut, eid) or {}
    fecha_aprob = (request.form.get('fecha_aprobacion') or '').strip()
    if not fecha_aprob:
        return jsonify({'error': 'Indica la fecha de aprobación/emisión del documento.'}), 400
    archivo = request.files.get('archivo')
    contenido = archivo.read() if archivo and archivo.filename else None
    nombre = (archivo.filename if archivo and archivo.filename else
              f"{cumplimiento.REGLAS_CUMPLIMIENTO[categoria]['titulo']} {fecha_aprob[:4]}")
    base_cid = db.contrato_base(eid, rut, emp.get('razon_social'))
    doc_id = db.registrar_documento_legal(
        base_cid, categoria, nombre, fecha_aprob,
        contenido=contenido, mimetype=(archivo.mimetype if archivo else None))
    # Cascada Capa Core → Capa Mandante (referencias a contratos mineros)
    afectados = db.cascada_a_contratos(eid, categoria, doc_id)
    # Nutre el FUF (marca el ítem como cumplido) si la regla lo mapea
    fuf_item = cumplimiento.REGLAS_CUMPLIMIENTO[categoria].get('fuf_item')
    if fuf_item:
        db.set_fuf_estado(eid, fuf_item, 'si', rut=rut)
    mand = ', '.join(sorted({a['mandante'] for a in afectados if a['mandante']})) or 'tus contratos'
    mensaje = (f"Documento actualizado. Cubres tu obligación legal (DS 44) y tu exigencia "
               f"contractual con {mand} simultáneamente"
               + (f"; ítem FUF N°{fuf_item} marcado como cumplido." if fuf_item else "."))
    return jsonify({'ok': True, 'doc_id': doc_id, 'afectados': afectados,
                    'mensaje': mensaje, 'pendientes': alertas.actividades_pendientes(db, eid)})


# Las rutas /api/matriz-legal* y la vista /matriz-legal viven ahora en el módulo aislado
# matriz_legal/ (Blueprint, mismas URLs).


@app.route('/api/reglas', methods=['GET'])
@login_required
def api_reglas_get():
    return jsonify(db.reglas_listar())


@app.route('/api/reglas/<int:rid>', methods=['POST'])
@login_required
def api_regla_editar(rid):
    f = request.get_json(silent=True) or {}
    r = db.regla_actualizar(rid, periodicidad_meses=f.get('periodicidad_meses'),
                            es_critico=f.get('es_critico'))
    if not r:
        return jsonify({'error': 'Regla no encontrada.'}), 404
    return jsonify(r)


# ══════════════ Ronda 15 — Motor Documental: Trabajadores / Tareas / EPP / PTS / IRL ═════════
def _logo_empresa(rut, empresa_id):
    return docgen.logo_empresa(db, rut, empresa_id)


@app.route('/api/empresa/logo', methods=['POST'])
@empresa_required
def api_empresa_logo():
    """Carga/reemplaza el logo corporativo de la empresa activa (blob en la BD)."""
    rut, eid = session['rut'], _empresa_id()
    emp = db.empresa_de(rut, eid)
    if not emp:
        return jsonify({'error': 'Empresa no encontrada.'}), 404
    archivo = request.files.get('logo')
    if not archivo or not archivo.filename:
        return jsonify({'error': 'No se recibió imagen.'}), 400
    ext = os.path.splitext(archivo.filename)[1].lower() or '.png'
    base_cid = db.contrato_base(eid, rut, emp.get('razon_social'))
    db.eliminar_doc_tipo(base_cid, None, 'logo_empresa')      # reemplazar anterior
    doc_id = db.registrar_documento(base_cid, 'logo_empresa' + ext, '', 'logo_empresa',
                                    contenido=archivo.read(), mimetype=archivo.mimetype or 'image/png')
    db.empresa_set_logo(eid, doc_id)
    return jsonify({'ok': True, 'logo_doc_id': doc_id, 'url': f'/api/doc/{doc_id}'})


@app.route('/api/empresa/logo', methods=['GET'])
@empresa_required
def api_empresa_logo_get():
    emp = db.empresa_de(session['rut'], _empresa_id()) or {}
    return jsonify({'logo_doc_id': emp.get('logo_doc_id'),
                    'url': f"/api/doc/{emp['logo_doc_id']}" if emp.get('logo_doc_id') else None,
                    'razon_social': emp.get('razon_social')})


# Las rutas /api/trabajadores*, /api/irl/generar y la vista /nomina viven en el módulo
# aislado nomina/ (Blueprint, mismas URLs).
@app.route('/api/iper/tareas', methods=['GET'])
@empresa_required
@onboarding_required
def api_tareas_get():
    tareas = db.tareas_de_empresa(_empresa_id())
    for t in tareas:
        t['riesgos'] = db.riesgos_de_tarea(t['id'])
        t['epp'] = db.epp_de_tarea(t['id'])
        t['pts'] = db.pts_de_tarea(t['id'])
    return jsonify(tareas)


@app.route('/api/iper/tareas', methods=['POST'])
@empresa_required
def api_tarea_crear():
    f = request.get_json(silent=True) or request.form
    nombre = (f.get('nombre') or '').strip()
    if not nombre:
        return jsonify({'error': 'Indica el nombre de la Tarea.'}), 400
    eid = _empresa_id()
    m = db.matriz_riesgo_vigente(eid) or {'id': db.crear_matriz_riesgo(eid, session.get('nombre'))}
    tid = db.tarea_crear(m['id'], nombre, proceso=(f.get('proceso') or '').strip() or None,
                         rutinaria=(f.get('rutinaria') or '').strip() or None,
                         responsable=(f.get('responsable') or '').strip() or None)
    # riesgos opcionales en el alta → se amarran a la tarea recién creada
    from models import RiesgoItem
    for r in (f.get('riesgos') or []):
        rid = db.riesgo_agregar(m['id'], r.get('peligro'), r.get('riesgo'), r.get('medida_control'),
                                nivel_riesgo=r.get('nivel_riesgo'), es_critico=r.get('es_critico', 0))
        it = RiesgoItem.query.get(rid)
        if it:
            it.tarea_id = tid
    sqla.session.commit()
    return jsonify({'ok': True, 'tarea_id': tid})


@app.route('/api/iper/tareas/<int:tid>/riesgo', methods=['POST'])
@empresa_required
def api_tarea_riesgo(tid):
    f = request.get_json(silent=True) or {}
    eid = _empresa_id()
    m = db.matriz_riesgo_vigente(eid)
    if not m:
        return jsonify({'error': 'No hay matriz vigente.'}), 400
    rid = db.riesgo_agregar(m['id'], f.get('peligro'), f.get('riesgo'), f.get('medida_control'),
                            nivel_riesgo=f.get('nivel_riesgo'), es_critico=f.get('es_critico', 0))
    # amarrar el riesgo a la tarea
    from models import RiesgoItem
    it = RiesgoItem.query.get(rid)
    if it:
        it.tarea_id = tid
        sqla.session.commit()
    return jsonify({'ok': True, 'riesgo_id': rid})


@app.route('/api/epp', methods=['GET'])
@empresa_required
def api_epp_get():
    return jsonify(db.epp_listar(_empresa_id()))


@app.route('/api/epp', methods=['POST'])
@empresa_required
def api_epp_crear():
    f = request.get_json(silent=True) or request.form
    nombre = (f.get('nombre') or '').strip()
    if not nombre:
        return jsonify({'error': 'Indica el nombre del EPP.'}), 400
    db.epp_crear(_empresa_id(), nombre, codigo=(f.get('codigo') or '').strip() or None,
                 norma=(f.get('norma') or '').strip() or None)
    return jsonify(db.epp_listar(_empresa_id()))


@app.route('/api/pts', methods=['GET'])
@empresa_required
def api_pts_get():
    return jsonify(db.pts_listar(_empresa_id()))


@app.route('/api/pts', methods=['POST'])
@empresa_required
def api_pts_crear():
    f = request.get_json(silent=True) or request.form
    nombre = (f.get('nombre') or '').strip()
    if not nombre:
        return jsonify({'error': 'Indica el nombre del PTS.'}), 400
    db.pts_crear(_empresa_id(), nombre, codigo=(f.get('codigo') or '').strip() or None,
                 version=(f.get('version') or '').strip() or None)
    return jsonify(db.pts_listar(_empresa_id()))


@app.route('/api/iper/tareas/<int:tid>/epp', methods=['POST'])
@empresa_required
def api_tarea_link_epp(tid):
    f = request.get_json(silent=True) or {}
    db.tarea_link_epp(tid, int(f.get('epp_id')))
    return jsonify({'ok': True, 'epp': db.epp_de_tarea(tid)})


@app.route('/api/iper/tareas/<int:tid>/pts', methods=['POST'])
@empresa_required
def api_tarea_link_pts(tid):
    f = request.get_json(silent=True) or {}
    db.tarea_link_pts(tid, int(f.get('pts_id')))
    return jsonify({'ok': True, 'pts': db.pts_de_tarea(tid)})


# ── IRL: generar / actualizar / listar ──
@app.route('/api/mutuales', methods=['GET'])
@login_required
def api_mutuales():
    return jsonify(iper.MUTUALES)


@app.route('/api/faena/<int:cid>', methods=['GET'])
@empresa_required
def api_faena_get(cid):
    """Capa legal (mandante) + riesgos de la faena de un contrato + catálogo de actividades."""
    rut, eid = session['rut'], _empresa_id()
    c = db.contrato_de(rut, cid)
    if not c:
        return jsonify({'error': 'Contrato no encontrado.'}), 404
    actividades = [t['tarea'] for t in iper.CATALOGO_TAREAS_BASE] + \
                  [b['nombre'] for b in db.biblioteca_listar(eid)]
    return jsonify({'contrato': c,
                    'legal': db.matriz_legal_contrato(eid, cid),
                    'riesgos': db.riesgos_de_contrato(eid, cid),
                    'actividades': sorted(set(actividades))})


@app.route('/api/faena/<int:cid>/precargar', methods=['POST'])
@empresa_required
def api_faena_precargar(cid):
    res = db.precargar_faena(session['rut'], cid)
    if res.get('error'):
        return jsonify(res), 400
    return jsonify({'ok': True, **res,
                    'legal': db.matriz_legal_contrato(_empresa_id(), cid),
                    'riesgos': db.riesgos_de_contrato(_empresa_id(), cid)})


@app.route('/api/faena/<int:cid>/miper.xlsx', methods=['GET'])
@empresa_required
def api_faena_miper_xlsx(cid):
    """Descarga la Matriz de Riesgos (MIPER) en Excel, con la cabecera autocompletada desde el
    contrato, lista para subir a la nube del mandante."""
    import docgen_xlsx
    eid = _empresa_id()
    c = db.contrato_de(session['rut'], cid)
    if not c:
        return jsonify({'error': 'Contrato no encontrado.'}), 404
    data = docgen_xlsx.build_miper_xlsx(c, db.riesgos_de_contrato(eid, cid))
    nombre = f"MIPER_{re.sub(r'[^A-Za-z0-9_-]+', '_', c.get('numero') or str(cid))}.xlsx"
    return send_file(BytesIO(data), as_attachment=True, download_name=nombre,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/api/faena/<int:cid>/mapa.xlsx', methods=['GET'])
@empresa_required
def api_faena_mapa_xlsx(cid):
    """Descarga el Mapa de Proceso en Excel, con Antecedentes autocompletados y la tabla
    Procesos → Actividades → Tareas del contrato, en el formato del mandante."""
    import docgen_xlsx
    eid = _empresa_id()
    c = db.contrato_de(session['rut'], cid)
    if not c:
        return jsonify({'error': 'Contrato no encontrado.'}), 404
    data = docgen_xlsx.build_mapa_xlsx(c, db.tareas_de_contrato(eid, cid))
    nombre = f"MapaProceso_{re.sub(r'[^A-Za-z0-9_-]+', '_', c.get('numero') or str(cid))}.xlsx"
    return send_file(BytesIO(data), as_attachment=True, download_name=nombre,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/api/faena/<int:cid>/legal', methods=['POST'])
@empresa_required
def api_faena_legal(cid):
    """Agrega un requisito legal de mandante ligado a la faena (CRUD capa mandante)."""
    eid = _empresa_id()
    if not db.contrato_de(session['rut'], cid):
        return jsonify({'error': 'Contrato no encontrado.'}), 404
    f = request.get_json(silent=True) or {}
    existentes = db.matriz_legal_contrato(eid, cid)
    n = 1 + len(existentes)
    data = {'id_requisito': f"F{cid}-OP-{n:02d}", 'capa': 'mandante', 'contrato_id': cid,
            'origen': (f.get('origen') or '').strip(), 'cuerpo_normativo': (f.get('cuerpo_normativo') or '').strip(),
            'requisito_legal': (f.get('requisito_legal') or '').strip(),
            'responsable': (f.get('responsable') or '').strip()}
    db.requisito_guardar(eid, data)
    return jsonify(db.matriz_legal_contrato(eid, cid))


@app.route('/api/faena/<int:cid>/inyectar', methods=['POST'])
@empresa_required
def api_faena_inyectar(cid):
    """Inyecta actividades/procesos (del catálogo base o biblioteca) a la MIPER de la faena."""
    f = request.get_json(silent=True) or {}
    res = db.inyectar_actividades_faena(session['rut'], cid, f.get('actividades') or [])
    if res.get('error'):
        return jsonify(res), 400
    return jsonify({'ok': True, **res, 'riesgos': db.riesgos_de_contrato(_empresa_id(), cid)})


@app.route('/api/biblioteca', methods=['GET'])
@empresa_required
def api_biblioteca_get():
    return jsonify(db.biblioteca_listar(_empresa_id()))


@app.route('/api/biblioteca', methods=['POST'])
@empresa_required
def api_biblioteca_add():
    f = request.get_json(silent=True) or {}
    nombre = (f.get('nombre') or '').strip()
    if not nombre:
        return jsonify({'error': 'Indica el nombre.'}), 400
    db.biblioteca_crear(_empresa_id(), nombre, peligro=f.get('peligro'), riesgo=f.get('riesgo'),
                        medida_control=f.get('medida_control'), metodo_correcto=f.get('metodo_correcto'),
                        probabilidad=f.get('probabilidad'), consecuencia=f.get('consecuencia'))
    return jsonify(db.biblioteca_listar(_empresa_id()))


# ══════════════ Ronda 22 — Vehículos + QR + checklist móvil ══════════════
@app.route('/api/vehiculos', methods=['GET'])
@empresa_required
@onboarding_required
def api_vehiculos_get():
    return jsonify(db.vehiculos_de(_empresa_id()))


@app.route('/api/vehiculos', methods=['POST'])
@empresa_required
def api_vehiculo_crear():
    f = request.get_json(silent=True) or request.form
    patente = (f.get('patente') or '').strip()
    if not patente:
        return jsonify({'error': 'Indica la patente.'}), 400
    km = f.get('km_actual')
    db.vehiculo_crear(_empresa_id(), patente, tipo=(f.get('tipo') or '').strip() or None,
                      marca_modelo=(f.get('marca_modelo') or '').strip() or None,
                      km_actual=int(km) if str(km or '').isdigit() else None)
    return jsonify(db.vehiculos_de(_empresa_id()))


@app.route('/api/vehiculos/<int:vid>/eliminar', methods=['POST'])
@empresa_required
def api_vehiculo_eliminar(vid):
    db.vehiculo_eliminar(_empresa_id(), vid)
    return jsonify(db.vehiculos_de(_empresa_id()))


@app.route('/api/vehiculos/<int:vid>/qr', methods=['GET'])
@empresa_required
def api_vehiculo_qr(vid):
    """QR (PNG) que apunta a la ruta móvil pública del vehículo (/v/<token>)."""
    v = db.vehiculo_de(_empresa_id(), vid)
    if not v or not v.get('token'):
        return ('Vehículo no encontrado', 404)
    import segno
    url = url_for('checklist_movil', token=v['token'], _external=True)
    buf = BytesIO()
    segno.make(url, error='m').save(buf, kind='png', scale=6, border=2)
    buf.seek(0)
    return send_file(buf, mimetype='image/png', as_attachment=False,
                     download_name=f"QR_{v.get('patente','vehiculo')}.png")


@app.route('/api/vehiculos/checklists-alerta', methods=['GET'])
@empresa_required
def api_vehiculo_alertas():
    return jsonify(db.checklists_no_conformes(_empresa_id()))


# ── Ruta MÓVIL PÚBLICA (se abre al escanear el QR; sin login) ──
@app.route('/v/<token>', methods=['GET'])
def checklist_movil(token):
    v = db.vehiculo_por_token(token)
    if not v:
        return ('Vehículo no encontrado o QR inválido.', 404)
    return render_template('mobile_checklist.html', v=v, token=token,
                           fys=vehiculos.FYS_ITEMS, veh=vehiculos.VEHICULO_ITEMS,
                           ya_hoy=None)


@app.route('/v/<token>', methods=['POST'])
def checklist_movil_guardar(token):
    v = db.vehiculo_por_token(token)
    if not v:
        return jsonify({'error': 'QR inválido.'}), 404
    f = request.get_json(silent=True) or request.form
    nombre = (f.get('conductor_nombre') or '').strip()
    rut = (f.get('conductor_rut') or '').strip()
    if not (nombre and rut):
        return jsonify({'error': 'Indica tu nombre y RUT.'}), 400
    fys = {it['k']: (f.get('fys_' + it['k']) or '') for it in vehiculos.FYS_ITEMS}
    veh = {it['k']: (f.get('veh_' + it['k']) or '') for it in vehiculos.VEHICULO_ITEMS}
    km = f.get('km')
    km = int(km) if str(km or '').isdigit() else None
    conforme, alertas = vehiculos.evaluar(fys, veh)
    db.checklist_vehiculo_guardar(v['id'], v['empresa_id'], nombre, normalizar_rut(rut) if rut_valido(rut) else rut,
                                  km, fys, veh, conforme, alertas)
    return jsonify({'ok': True, 'conforme': conforme, 'alertas': alertas})


# ── Tarjeta de Reporte de Actos y Condiciones Subestándar (participación — FUF 25) ──
def _reporte_serializer():
    """Firma/verifica el token del QR por empresa (sin almacenar columna nueva)."""
    from itsdangerous import URLSafeSerializer
    return URLSafeSerializer(app.secret_key, salt='reporte-subestandar')


@app.route('/api/reportes', methods=['GET'])
@empresa_required
@onboarding_required
def api_reportes_get():
    return jsonify(db.reportes_de(_empresa_id(),
                                  faena=request.args.get('faena') or None,
                                  nivel=request.args.get('nivel') or None,
                                  estado=request.args.get('estado') or None))


@app.route('/api/reportes/resumen', methods=['GET'])
@empresa_required
@onboarding_required
def api_reportes_resumen():
    return jsonify(db.reportes_resumen(_empresa_id()))


@app.route('/api/reportes/qr', methods=['GET'])
@empresa_required
def api_reportes_qr():
    """QR (PNG) que abre la tarjeta móvil pública de la empresa (/r/<token>)."""
    import segno
    token = _reporte_serializer().dumps(_empresa_id())
    url = url_for('reporte_movil', token=token, _external=True)
    buf = BytesIO()
    segno.make(url, error='m').save(buf, kind='png', scale=6, border=2)
    buf.seek(0)
    return send_file(buf, mimetype='image/png', as_attachment=False,
                     download_name='QR_reporte_subestandar.png')


@app.route('/api/reportes/<int:rid>/foto', methods=['GET'])
@empresa_required
def api_reporte_foto(rid):
    data, mime = db.reporte_foto(_empresa_id(), rid)
    if not data:
        return ('Sin evidencia fotográfica', 404)
    return send_file(BytesIO(data), mimetype=mime, as_attachment=False)


@app.route('/api/reportes/<int:rid>/cerrar', methods=['POST'])
@empresa_required
def api_reporte_cerrar(rid):
    if not db.reporte_cerrar(_empresa_id(), rid):
        return jsonify({'error': 'Reporte no encontrado.'}), 404
    return jsonify({'ok': True})


# ── Ruta MÓVIL PÚBLICA (se abre al escanear el QR de la faena; sin login) ──
@app.route('/r/<token>', methods=['GET'])
def reporte_movil(token):
    try:
        eid = _reporte_serializer().loads(token)
    except Exception:
        return ('QR inválido.', 404)
    emp = db.empresa_basica(eid)
    if not emp:
        return ('Empresa no encontrada o QR inválido.', 404)
    return render_template('mobile_reporte.html', empresa=emp, token=token,
                           clasificacion=reportes.CLASIFICACION, peligros=reportes.PELIGROS,
                           niveles=reportes.NIVELES, hoy=date.today().isoformat())


@app.route('/r/<token>', methods=['POST'])
def reporte_movil_guardar(token):
    try:
        eid = _reporte_serializer().loads(token)
    except Exception:
        return jsonify({'error': 'QR inválido.'}), 404
    if not db.empresa_basica(eid):
        return jsonify({'error': 'QR inválido.'}), 404
    f = request.form
    if not (f.get('descripcion') or '').strip():
        return jsonify({'error': 'Describe lo que detectaste.'}), 400
    data = {k: f.get(k) for k in ('faena', 'area', 'fecha', 'hora', 'reporta_nombre',
                                  'reporta_cargo', 'clasificacion', 'descripcion',
                                  'accion_inmediata', 'nivel_riesgo')}
    data['peligros'] = f.getlist('peligros')
    foto_bytes, foto_mime = None, None
    foto = request.files.get('foto')
    if foto and foto.filename:
        foto_bytes = foto.read()
        foto_mime = foto.mimetype or 'image/jpeg'
    rid = db.reporte_registrar(eid, data, foto=foto_bytes, foto_mime=foto_mime)
    urgente, etiqueta = reportes.evaluar(data.get('nivel_riesgo'))
    return jsonify({'ok': True, 'id': rid, 'urgente': urgente, 'nivel': etiqueta})


@app.route('/api/doc/<int:doc_id>', methods=['GET'])
@login_required
def api_doc(doc_id):
    """Sirve un documento (evidencia, carta o logo) desde la BD, resolviendo referencias."""
    blob = db.documento_contenido(session['rut'], doc_id)
    if not blob:
        return ('Documento no encontrado', 404)
    contenido, mimetype, nombre = blob
    inline = (mimetype or '').startswith(('image/', 'text/html')) or \
        (nombre or '').lower().endswith(('.html', '.htm'))
    return send_file(BytesIO(contenido), mimetype=mimetype or 'application/octet-stream',
                     as_attachment=not inline, download_name=nombre or f'doc_{doc_id}')


@app.route('/api/doc/<int:doc_id>/word', methods=['GET'])
@login_required
def api_doc_word(doc_id):
    """Descarga un documento como .docx. Los documentos generados son HTML → se convierten con
    python-docx (doc_word.html_a_docx). Si ya es un .docx (ruta docx_fill), se sirve tal cual."""
    blob = db.documento_contenido(session['rut'], doc_id)
    if not blob:
        return ('Documento no encontrado', 404)
    contenido, mimetype, nombre = blob
    base = os.path.splitext(nombre or f'doc_{doc_id}')[0]
    docx_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    if (mimetype or '').startswith('text/html') or (nombre or '').lower().endswith(('.html', '.htm')):
        import doc_word
        data = doc_word.html_a_docx(contenido.decode('utf-8', 'ignore'), titulo=base)
        return send_file(BytesIO(data), mimetype=docx_mime, as_attachment=True,
                         download_name=f'{base}.docx')
    # Ya es un archivo (probablemente .docx): entregarlo directo.
    return send_file(BytesIO(contenido), mimetype=mimetype or docx_mime, as_attachment=True,
                     download_name=nombre or f'{base}.docx')


@app.route('/api/contratos/<int:cid>/logo', methods=['POST'])
@login_required
def api_subir_logo(cid):
    c = db.contrato_de(session['rut'], cid)
    if not c:
        return jsonify({'error': 'Contrato no encontrado.'}), 404
    archivo = request.files.get('logo')
    if not archivo or not archivo.filename:
        return jsonify({'error': 'No se recibió imagen.'}), 400
    ext = os.path.splitext(archivo.filename)[1].lower() or '.png'
    # reemplazar logo anterior
    for d in db.documentos_de(cid):
        if d.get('tipo') == 'logo':
            db.eliminar_doc_tipo(cid, None, 'logo')
            break
    doc_id = db.registrar_documento(cid, 'empresa_logo' + ext, '', 'logo',
                                    contenido=archivo.read(),
                                    mimetype=archivo.mimetype or 'image/png')
    datos = _datos(c)
    datos['logo_doc_id'] = doc_id                 # referencia al blob en la BD
    datos.pop('logo', None)                       # limpiar esquema antiguo (filesystem)
    db.actualizar_datos(cid, json.dumps(datos, ensure_ascii=False))
    return jsonify(_consolidar(session['rut']))


@app.route('/api/contratos/<int:cid>/logo', methods=['GET'])
@login_required
def api_ver_logo(cid):
    c = db.contrato_de(session['rut'], cid)
    if not c:
        return ('', 404)
    doc = _logo_doc(cid)
    if not doc:
        return ('', 404)
    blob = db.documento_contenido(session['rut'], doc['id'])
    if not blob:
        return ('', 404)
    contenido, mimetype, _ = blob
    return send_file(BytesIO(contenido), mimetype=mimetype or 'image/png')


if __name__ == '__main__':
    # Solo desarrollo local (en Render arranca gunicorn, no este bloque).
    # Puerto 5001 por defecto: en macOS el 5000 lo ocupa AirPlay Receiver (responde 403).
    app.run(debug=True, port=int(os.environ.get('PORT', 5001)))
