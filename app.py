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
import db
import normativa
import resso
import ia
import correccion
import cumplimiento
import alertas

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'smarthse-dev-key-cambiar-en-render')

# ── Base de datos: PostgreSQL en producción (DATABASE_URL), SQLite en local ──
_db_url = os.environ.get('DATABASE_URL', '')
if _db_url.startswith('postgres://'):          # Render entrega 'postgres://'; SQLAlchemy pide 'postgresql://'
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url or 'sqlite:///' + os.path.join(
    os.path.dirname(__file__), 'smarthse.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
sqla.init_app(app)

with app.app_context():
    db.init_db()                                # crea tablas (auto-migración) + siembra mapping


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


def normalizar_id(valor):
    """Normaliza el N° SNS para usarlo como clave de cuenta (sin puntos/guion, mayúsculas)."""
    return re.sub(r'[^0-9A-Za-z]', '', valor or '').upper()


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


def _empresa_id():
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
    return render_template('login.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """Registro con RUT + clave + SNS (ID profesional) + nombre. El SNS se pide solo aquí."""
    if request.method == 'POST':
        f = request.form
        nombre = (f.get('nombre', '')).strip()
        rut_raw = (f.get('rut', '')).strip()
        sns = (f.get('sns', '')).strip()
        clave = f.get('clave', '')
        datos = {'nombre': nombre, 'rut': rut_raw, 'sns': sns}

        if not (nombre and rut_raw and sns):
            return render_template('registro.html', error='Completa nombre, RUT y N° SNS.', **datos)
        if not rut_valido(rut_raw):
            return render_template('registro.html', error='El RUT ingresado no es válido.', **datos)
        if not clave_valida(clave):
            return render_template('registro.html',
                                   error='La clave debe ser alfanumérica de al menos 6 caracteres (con letras y números).', **datos)

        key = normalizar_rut(rut_raw)
        if db.usuario_get(key):
            return render_template('registro.html', error='Ya existe una cuenta con ese RUT.', **datos)

        db.usuario_crear(key, rut_raw, sns, nombre, rol='asesor',
                         pass_hash=generate_password_hash(clave))
        session['rut'] = key
        session['sns'] = sns
        session['nombre'] = nombre
        session['rol'] = 'asesor'
        session.pop('empresa_id', None)
        # Tras crear la cuenta → registrar la primera empresa (base estructural).
        return redirect(url_for('empresas'))
    return render_template('registro.html')


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
        session['empresa_id'] = db.crear_empresa('DEMO', 'Empresa Demo SPA',
                                                 mutual='Mutual demo', rubro='Servicios')
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ─────────────────── Empresas (base estructural — Ronda 12) ────────────────
@app.route('/empresas', methods=['GET', 'POST'])
@login_required
def empresas():
    """Registrar empresa (base) o listar/seleccionar. Al crear → Consola Operativa."""
    if request.method == 'POST':
        f = request.form
        razon = (f.get('razon_social', '')).strip()
        if not razon:
            return render_template('empresas.html', error='Indica la Razón Social.',
                                   empresas=db.empresas_de(session['rut']), **_form_empresa(f))
        eid = db.crear_empresa(
            session['rut'], razon,
            rut_empresa=(f.get('rut_empresa', '')).strip() or None,
            mutual=(f.get('mutual', '')).strip() or None,
            n_adherente=(f.get('n_adherente', '')).strip() or None,
            rubro=(f.get('rubro', '')).strip() or None)
        session['empresa_id'] = eid
        return redirect(url_for('dashboard'))
    return render_template('empresas.html', empresas=db.empresas_de(session['rut']))


def _form_empresa(f):
    return {k: (f.get(k, '')).strip() for k in
            ('razon_social', 'rut_empresa', 'mutual', 'n_adherente', 'rubro')}


@app.route('/empresas/<int:eid>/seleccionar')
@login_required
def empresa_seleccionar(eid):
    if db.empresa_de(session['rut'], eid):
        session['empresa_id'] = eid
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
@login_required
def dashboard():
    # La Consola de Gestión Operativa vive sobre una empresa activa.
    if not session.get('empresa_id'):
        return redirect(url_for('empresas'))
    emp = db.empresa_de(session['rut'], session['empresa_id'])
    if not emp:                                   # empresa borrada / sesión vieja
        session.pop('empresa_id', None)
        return redirect(url_for('empresas'))
    return render_template('dashboard.html', nombre=session.get('nombre'),
                           sns=session.get('sns'), rol=session.get('rol'),
                           empresa=emp)


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
        es_codelco = resso.es_codelco(c['mandante'])
        carpeta = None
        if es_codelco:
            car = _carpeta(c['id'])
            cumple = sum(1 for i in car['items'] if i['estado'] == 'cumple')
            na = sum(1 for i in car['items'] if i['estado'] == 'na')
            total = len(car['items'])
            carpeta = {'pct': car['cumplimiento_pct'], 'total': total, 'cumple': cumple,
                       'na': na, 'pendientes': total - cumple - na}
        salida.append({**c, 'controles': controles,
                       'documentos': db.documentos_de(c['id']),
                       'datos': datos, 'es_codelco': es_codelco, 'carpeta': carpeta,
                       'cerradas': cerradas, 'pendientes': len(controles) - cerradas})
    return salida


def _carpeta(cid):
    """Estado de la Carpeta de Arranque (29 ítems) de un contrato."""
    estados = db.estados_carpeta(cid)
    docs = db.docs_por_item(cid)
    items = []
    for it in resso.carpeta_lista():
        e = estados.get(it['n'], {})
        items.append({**it,
                      'estado': e.get('estado', 'pendiente'),
                      'observacion': e.get('observacion', '') or '',
                      'fecha_compromiso': e.get('fecha_compromiso', '') or '',
                      'docs': [{'id': d['id'], 'nombre': d['nombre'], 'tipo': d.get('tipo', 'evidencia')}
                               for d in docs.get(it['n'], [])]})
    aplicables = [i for i in items if i['estado'] != 'na']
    cumple = [i for i in aplicables if i['estado'] == 'cumple']
    pct = round(len(cumple) / len(aplicables) * 100) if aplicables else 0
    return {'items': items, 'cumplimiento_pct': pct}


def _datos(contrato):
    if contrato and contrato.get('datos_json'):
        try:
            return json.loads(contrato['datos_json'])
        except (TypeError, ValueError):
            return {}
    return {}


def _logo_doc(cid):
    """Devuelve el documento-logo (tipo='logo') más reciente del contrato, o None."""
    logos = [d for d in db.documentos_de(cid) if d.get('tipo') == 'logo']
    return logos[0] if logos else None


def _logo_data_uri(rut, cid):
    """Data URI del logo de la empresa (leído desde la BD), o None."""
    doc = _logo_doc(cid)
    if not doc:
        return None
    blob = db.documento_contenido(rut, doc['id'])
    if not blob:
        return None
    import base64
    contenido, mimetype, _ = blob
    b64 = base64.b64encode(contenido).decode()
    return f"data:{mimetype or 'image/png'};base64,{b64}"


def carta_na_html(rut, contrato, datos, item, fundamento):
    """Genera una Carta de No Aplica (N/A) en HTML autocontenido (con logo si existe)."""
    hoy = date.today().strftime('%d-%m-%Y')
    empresa = (datos.get('empresa_contratista') or contrato.get('empresa') or '').strip()
    fund = (fundamento.strip() if fundamento and fundamento.strip() else '[Pendiente de fundamentar]')
    mandante = contrato.get('mandante', '') + (f" — {contrato.get('faena')}" if contrato.get('faena') else '')
    logo = _logo_data_uri(rut, contrato.get('id'))
    logo_html = f'<img src="{logo}" alt="Logo" style="max-height:80px;max-width:220px">' if logo else \
        f'<div style="font-weight:800;color:#006a9b;font-size:20px">{empresa or "Empresa Contratista"}</div>'
    def esc(s):
        return (str(s or '')).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Carta N/A · Ítem {item['n']} · Contrato {esc(contrato.get('numero',''))}</title>
<style>
 body{{font-family:Arial,Helvetica,sans-serif;color:#1a2b3c;max-width:820px;margin:24px auto;padding:0 24px;line-height:1.5}}
 .head{{display:flex;justify-content:space-between;align-items:center;border-bottom:3px solid #006a9b;padding-bottom:14px;margin-bottom:20px}}
 .titulo{{text-align:right}} h1{{font-size:18px;margin:0;color:#006a9b}} .sub{{font-size:12px;color:#666}}
 table{{width:100%;border-collapse:collapse;margin:14px 0;font-size:13px}}
 td{{padding:6px 8px;border-bottom:1px solid #eee}} td.k{{color:#666;width:230px;font-weight:600}}
 .item{{background:#f4f7f6;border-radius:8px;padding:12px 14px;margin:14px 0}}
 .decl{{margin:18px 0}} .fund{{background:#fffbe6;border:1px solid #ffe58f;border-radius:8px;padding:12px 14px;font-weight:600}}
 .firma{{margin-top:48px;border-top:1px solid #333;width:320px;padding-top:6px;font-size:13px}}
 .pie{{margin-top:24px;font-size:11px;color:#999}}
</style></head><body>
 <div class="head">{logo_html}<div class="titulo"><h1>CARTA DE NO APLICABILIDAD (N/A)</h1><div class="sub">Carpeta de Arranque · RESSO Anexo 2</div></div></div>
 <table>
  <tr><td class="k">Fecha</td><td>{esc(hoy)}</td></tr>
  <tr><td class="k">Empresa Contratista</td><td>{esc(empresa)}</td></tr>
  <tr><td class="k">N° de Contrato</td><td>{esc(contrato.get('numero',''))}</td></tr>
  <tr><td class="k">Mandante / División</td><td>{esc(mandante)}</td></tr>
  {f'<tr><td class="k">Administrador de Contrato CODELCO</td><td>{esc(datos.get("admin_codelco"))}</td></tr>' if datos.get('admin_codelco') else ''}
 </table>
 <div class="item"><b>Ítem N° {item['n']}: {esc(item['titulo'])}</b><br><span class="sub">Evidencia normalmente requerida: {esc(item['evidencia'])}</span></div>
 <div class="decl"><b>DECLARACIÓN DE NO APLICABILIDAD</b><br>
  Por medio de la presente, la Empresa Contratista declara que el requisito individualizado
  <b>NO APLICA</b> al presente contrato, por el siguiente fundamento:</div>
 <div class="fund">Fundamento: {esc(fund)}</div>
 <p>Esta declaración se incorpora a la Carpeta de Arranque para efectos de acreditación y auditoría.</p>
 <div class="firma">{esc(datos.get('experto_eecc') or 'Experto en Prevención de Riesgos EE.CC.')}<br>
  <span class="sub">Experto en Prevención de Riesgos — Empresa Contratista</span></div>
 <div class="pie">Smart HSE Chile · Documento generado automáticamente</div>
</body></html>"""


def generar_carta_na(rut, cid, contrato, n, fundamento):
    """Crea/actualiza la carta N/A (HTML con logo) del ítem n, guardándola en la BD."""
    item = resso.CARPETA_DICT.get(n)
    if not item:
        return
    datos = _datos(contrato)
    html = carta_na_html(rut, contrato, datos, item, fundamento)
    numero = re.sub(r'[^\w-]+', '_', contrato.get('numero', '') or '')
    nombre = f"Carta_NA_item{n:02d}_{numero}.html"
    db.eliminar_doc_tipo(cid, n, 'carta_na')          # evitar duplicados
    db.registrar_documento(cid, nombre, 'N/A', 'carta_na', item_n=n,
                           contenido=html.encode('utf-8'), mimetype='text/html')


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
MANDANTES_MINEROS = ['Codelco División RT', 'Minera Spence (BHP)', 'Minera El Abra',
                     'Minera Centinela', 'Otra minería']
FUF_TOTAL = 60          # ítems del FUF DS 44 (base legal Ley 16.744, común a todo empleador)
CARPETA_TOTAL = 29      # ítems de la Carpeta de Arranque (estándar minero)


def _gap_analysis(rut, cid):
    """Compara la base DS 44 (FUF del asesor, ya cumplida) contra el estándar minero
    pendiente (Carpeta de Arranque + RESSO). Devuelve el % de base ya lograda y qué
    falta para alcanzar el estándar minero. El FUF 'suma', no se re-hace."""
    _ce = db.contrato_de(rut, cid) or {}
    fuf = db.estados_fuf(_ce.get('empresa_id') or _empresa_id())
    fuf_ok = sum(1 for r in fuf.values() if r.get('estado') in ('si', 'na'))
    fuf_pct = round(100 * fuf_ok / FUF_TOTAL) if FUF_TOTAL else 0
    car = _carpeta(cid)
    cumple = sum(1 for i in car['items'] if i['estado'] == 'cumple')
    na = sum(1 for i in car['items'] if i['estado'] == 'na')
    pendientes = len(car['items']) - cumple - na
    return {
        'base_ds44': {'pct': fuf_pct, 'cumplidos': fuf_ok, 'total': FUF_TOTAL,
                      'titulo': 'Base legal DS 44 / FUF (Ley 16.744)'},
        'estandar_minero': {
            'carpeta_pct': car['cumplimiento_pct'], 'carpeta_cumple': cumple,
            'carpeta_na': na, 'carpeta_pendientes': pendientes,
            'carpeta_total': len(car['items']),
            'resso_estado': (db.contrato_de(rut, cid) or {}).get('resso_estado') or 'bloqueado'},
        'mensaje': (f'Ya tienes el {fuf_pct}% de la base legal (DS 44) lista. '
                    f'Para el estándar minero faltan {pendientes} ítem(es) de la '
                    f'Carpeta de Arranque y aprobar el RESSO.')
    }


@app.route('/api/contratos/<int:cid>/upgrade', methods=['POST'])
@login_required
def api_contrato_upgrade(cid):
    """Módulo Puente: convierte una empresa general en contratista minera SIN
    re-ingresar datos ni perder avance. Reutiliza el contrato + el FUF del asesor;
    solo fija el mandante y habilita el flujo Carpeta/RESSO. Deriva a la Carpeta."""
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
                    'gap': _gap_analysis(rut, cid),
                    'es_codelco': resso.es_codelco(mandante)})


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


def sync_to_resso(rut, cid):
    """Recorre los documentos aprobados de la Carpeta de Arranque y crea referencias
    simbólicas en los puntos equivalentes de la Auditoría RESSO (sin duplicar archivos)."""
    docs_item = db.docs_por_item(cid)          # {item_n: [docs...]}
    sincronizados = 0
    for categoria, m in resso.EQUIVALENCIAS.items():
        item_n = m['carpeta']
        base = next((d for d in docs_item.get(item_n, []) if d.get('tipo') == 'evidencia'), None)
        if not base:
            continue
        # el documento del arranque pasa a ser el maestro de su categoría
        db.set_doc_maestro(base['id'], categoria)
        if db.existe_referencia(cid, base['id']):
            continue
        master = db.documento_por_id(rut, base['id'])
        db.registrar_documento(
            cid, master['nombre'], 'RESO ' + m['reso'], 'auditoria_ref',
            item_n=item_n, categoria=categoria, ref_doc_id=base['id'],
            version=master.get('version') or 'v1',
            fecha_aprobacion=master.get('fecha_aprobacion') or date.today().isoformat(),
            firma=master.get('firma'))
        # el punto RESO queda 'cumple' heredado del arranque
        db.set_auditoria_estado(cid, m['reso'], 'cumple',
                                f'Heredado de Carpeta de Arranque (ítem {item_n}).')
        sincronizados += 1
    return sincronizados


@app.route('/api/contratos/<int:cid>/arranque/aprobar', methods=['POST'])
@login_required
def api_arranque_aprobar(cid):
    """Hito ARRANQUE_APROBADO: exige Carpeta al 100% + firmas; activa RESSO y sincroniza."""
    rut = session['rut']
    contrato = db.contrato_de(rut, cid)
    if not contrato:
        return jsonify({'error': 'Contrato no encontrado.'}), 404
    if not resso.es_codelco(contrato.get('mandante')):
        return jsonify({'error': 'El módulo RESSO aplica solo a contratos Codelco.'}), 400
    carp = _carpeta(cid)
    if carp['cumplimiento_pct'] < 100:
        return jsonify({'error': 'La Carpeta de Arranque debe estar al 100% (todos los ítems aprobados) para aprobar el arranque.'}), 400
    f = request.get_json(silent=True) or {}
    docs = db.documentos_de(cid)
    tiene_firmas = f.get('firmas_ok') is True or any(d.get('tipo') == 'firma' for d in docs)
    if not tiene_firmas:
        return jsonify({'error': 'Debe cargar las firmas oficiales (acta de aprobación / Anexo 1) antes de aprobar el arranque.'}), 400
    db.set_arranque_aprobado(cid)
    n = sync_to_resso(rut, cid)
    return jsonify({'ok': True, 'resso_estado': 'en_progreso', 'sincronizados': n,
                    'aviso': 'Se han pre-cargado documentos desde la Carpeta de Arranque aprobada para el RESO'})


def _auditoria(cid):
    """Estado del módulo Auditoría RESSO (puntos + docs heredados por categoría)."""
    estados = db.estados_auditoria(cid)
    por_cat = {}
    for d in db.documentos_de(cid):
        if d.get('tipo') == 'auditoria_ref' and d.get('categoria'):
            por_cat.setdefault(d['categoria'], []).append(d)
    puntos = []
    for p in resso.auditoria_lista():
        e = estados.get(p['punto_key'], {})
        refs = por_cat.get(p['categoria'], [])
        puntos.append({**p,
                       'estado': e.get('estado', 'pendiente'),
                       'observacion': e.get('observacion', '') or '',
                       'docs': [{'nombre': x['nombre'], 'ref_doc_id': x.get('ref_doc_id'),
                                 'version': x.get('version'), 'fecha_aprobacion': x.get('fecha_aprobacion'),
                                 'firma': x.get('firma')} for x in refs]})
    aplicables = [x for x in puntos if x['estado'] != 'na']
    cumple = [x for x in aplicables if x['estado'] == 'cumple']
    pct = round(len(cumple) / len(aplicables) * 100) if aplicables else 0
    return {'puntos': puntos, 'cumplimiento_pct': pct}


@app.route('/api/contratos/<int:cid>/auditoria', methods=['GET'])
@login_required
def api_auditoria(cid):
    c = db.contrato_de(session['rut'], cid)
    if not c:
        return jsonify({'error': 'Contrato no encontrado.'}), 404
    return jsonify({'resso_estado': c.get('resso_estado') or 'bloqueado',
                    'arranque_aprobado': bool(c.get('arranque_aprobado')),
                    **_auditoria(cid)})


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


# ─────────────────────── Carpeta de Arranque (RESSO Anexo 2) ───────────────
@app.route('/api/contratos/<int:cid>/carpeta', methods=['GET'])
@login_required
def api_carpeta(cid):
    c = db.contrato_de(session['rut'], cid)
    if not c:
        return jsonify({'error': 'Contrato no encontrado.'}), 404
    if not resso.es_codelco(c['mandante']):
        return jsonify({'error': 'La Carpeta de Arranque RESSO aplica solo a contratos Codelco.'}), 400
    return jsonify(_carpeta(cid))


@app.route('/api/contratos/<int:cid>/carpeta/<int:n>/estado', methods=['POST'])
@login_required
def api_carpeta_estado(cid, n):
    contrato = db.contrato_de(session['rut'], cid)
    if not contrato:
        return jsonify({'error': 'Contrato no encontrado.'}), 404
    f = request.get_json(silent=True) or request.form
    actual = db.estados_carpeta(cid).get(n, {})
    # conservar lo existente cuando el campo no viene en la petición
    estado = f.get('estado')
    if estado is None:
        estado = actual.get('estado', 'pendiente')
    estado = (estado or 'pendiente').strip()
    if estado not in ('pendiente', 'cumple', 'na'):
        estado = 'pendiente'
    obs = f.get('observacion')
    if obs is None:
        obs = actual.get('observacion', '') or ''
    obs = obs.strip()
    fecha_comp = f.get('fecha_compromiso')
    if fecha_comp is None:
        fecha_comp = actual.get('fecha_compromiso')
    fecha_comp = (fecha_comp or '').strip() or None
    # Una brecha (Pendiente) exige observación.
    if estado == 'pendiente' and not obs:
        return jsonify({'error': 'La observación es obligatoria para una brecha (Pendiente).'}), 400
    db.set_item_estado(cid, n, estado, obs, fecha_comp)
    # Carta de No Aplica: se genera/actualiza cuando el ítem queda en N/A; se retira si no.
    if estado == 'na':
        generar_carta_na(session['rut'], cid, contrato, n, obs)
    else:
        db.eliminar_doc_tipo(cid, n, 'carta_na')
    return jsonify(_carpeta(cid))


# ─────────────────────────── FUF DS 44 (persistencia) ──────────────────────
@app.route('/api/fuf', methods=['GET'])
@empresa_required
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
        db.set_fuf_estado(eid, n, estado, obs, fecha_comp, rut=rut)
    return jsonify(db.estados_fuf(eid))


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
def api_brechas():
    rut = session['rut']
    eid = _empresa_id()
    brechas = []
    for b in db.brechas_carpeta(rut, eid):
        item = resso.CARPETA_DICT.get(b['item_n'], {})
        brechas.append({
            'fuente': 'carpeta',
            'item_n': b['item_n'],
            'etiqueta': f"Carpeta N°{b['item_n']:02d}",
            'titulo': item.get('titulo', ''),
            'contrato_id': b['contrato_id'],
            'contrato': f"{b['empresa']} · N° {b['numero']}" + (f" · {b['faena']}" if b['faena'] else ''),
            'observacion': b['observacion'] or '',
            'fecha_compromiso': b['fecha_compromiso'] or '',
            'dias_restantes': _dias_restantes(b['fecha_compromiso']),
        })
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
    elif fuente == 'carpeta':
        cid = f.get('contrato_id')
        if not db.contrato_de(session['rut'], cid):
            return jsonify({'error': 'Contrato no encontrado.'}), 404
        db.set_carpeta_compromiso(cid, n, fecha)
    else:
        return jsonify({'error': 'fuente inválida.'}), 400
    return jsonify({'ok': True})


# ══════════════ Motor de Cumplimiento: pendientes / matriz / reglas ═════════
@app.route('/api/pendientes', methods=['GET'])
@empresa_required
def api_pendientes():
    """Panel de Actividades Pendientes unificado (legal + contractual + operativa)."""
    return jsonify(alertas.actividades_pendientes(db, _empresa_id()))


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


@app.route('/api/matriz-legal', methods=['GET'])
@empresa_required
def api_matriz_get():
    return jsonify(db.matriz_legal(_empresa_id()))


@app.route('/api/matriz-legal', methods=['POST'])
@empresa_required
def api_matriz_guardar():
    data = request.get_json(silent=True) or {}
    return jsonify(db.requisito_guardar(_empresa_id(), data))


@app.route('/api/matriz-legal/importar', methods=['POST'])
@empresa_required
def api_matriz_importar():
    """Importa la Matriz Legal desde un Excel normalizado (columnas ID_Requisito, Origen,
    Cuerpo_Normativo, Requisito_Legal, Riesgo_Asociado, Control_Operativo, Frecuencia,
    Estado_Avance). Reusa openpyxl."""
    archivo = request.files.get('archivo')
    if not archivo or not archivo.filename:
        return jsonify({'error': 'No se recibió archivo.'}), 400
    try:
        from openpyxl import load_workbook
        wb = load_workbook(BytesIO(archivo.read()), data_only=True)
        ws = wb.active
        filas = list(ws.iter_rows(values_only=True))
    except Exception as e:      # noqa: BLE001
        return jsonify({'error': f'No se pudo leer el Excel: {type(e).__name__}.'}), 400
    if not filas:
        return jsonify({'error': 'El archivo está vacío.'}), 400
    encabezados = [str(h or '').strip().lower().replace(' ', '_') for h in filas[0]]
    campo = {'id_requisito': 'id_requisito', 'origen': 'origen', 'cuerpo_normativo': 'cuerpo_normativo',
             'requisito_legal': 'requisito_legal', 'riesgo_asociado': 'riesgo_asociado',
             'control_operativo': 'control_operativo', 'frecuencia': 'frecuencia',
             'estado_avance': 'estado_avance', 'responsable': 'responsable', 'capa': 'capa',
             'categoria': 'categoria'}
    n = 0
    for fila in filas[1:]:
        data = {}
        for i, h in enumerate(encabezados):
            if h in campo and i < len(fila) and fila[i] is not None:
                data[campo[h]] = str(fila[i]).strip()
        if not data:
            continue
        db.requisito_guardar(_empresa_id(), data)
        n += 1
    return jsonify({'ok': True, 'importados': n, 'matriz': db.matriz_legal(_empresa_id())})


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


@app.route('/api/contratos/<int:cid>/carpeta/<int:n>/documento', methods=['POST'])
@login_required
def api_carpeta_doc(cid, n):
    c = db.contrato_de(session['rut'], cid)
    if not c:
        return jsonify({'error': 'Contrato no encontrado.'}), 404
    archivos = request.files.getlist('archivo') or []
    if not archivos:
        return jsonify({'error': 'No se recibió archivo.'}), 400
    for archivo in archivos:
        if not archivo or not archivo.filename:
            continue
        db.registrar_documento(cid, archivo.filename, '', 'evidencia', item_n=n,
                               contenido=archivo.read(),
                               mimetype=archivo.mimetype or 'application/octet-stream')
    return jsonify(_carpeta(cid))


@app.route('/api/contratos/<int:cid>/carpeta/bulk', methods=['POST'])
@login_required
def api_carpeta_bulk(cid):
    """Carga masiva: varios archivos / carpeta completa → se clasifican en los 29 ítems."""
    c = db.contrato_de(session['rut'], cid)
    if not c:
        return jsonify({'error': 'Contrato no encontrado.'}), 404
    archivos = request.files.getlist('archivos') or []
    if not archivos:
        return jsonify({'error': 'No se recibieron archivos.'}), 400
    reporte = []
    for archivo in archivos:
        if not archivo or not archivo.filename:
            continue
        # webkitdirectory envía rutas relativas; respetar numeración de carpeta si existe
        nombre = archivo.filename.replace('\\', '/').split('/')[-1]
        n, fuente = ia.clasificar_path(archivo.filename)
        db.registrar_documento(cid, nombre, '', 'evidencia', item_n=n,
                               contenido=archivo.read(),
                               mimetype=archivo.mimetype or 'application/octet-stream')
        reporte.append({'archivo': nombre, 'item': n,
                        'titulo': resso.CARPETA_DICT.get(n, {}).get('titulo', ''),
                        'fuente': fuente})
    return jsonify({'carpeta': _carpeta(cid), 'reporte': reporte})


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
    app.run(debug=True, port=5000)
