import os
import json
import re
from datetime import date
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify, send_from_directory)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import db
import normativa
import resso
import ia

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), 'uploads')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'smarthse-dev-key-cambiar-en-render')

USERS_FILE = os.path.join(os.path.dirname(__file__), 'usuarios.json')

db.init_db()


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


def normalizar_id(valor):
    """Normaliza el N° SNS para usarlo como clave de cuenta (sin puntos/guion, mayúsculas)."""
    return re.sub(r'[^0-9A-Za-z]', '', valor or '').upper()


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
        sns_raw = request.form.get('sns', '')
        key = normalizar_id(sns_raw)
        usuarios = cargar_usuarios()
        u = usuarios.get(key)
        # Simulación: se ingresa solo con el N° SNS (sin exigir clave).
        # En producción, validar aquí: check_password_hash(u['pass_hash'], request.form.get('clave',''))
        if u:
            session['rut'] = key            # identificador interno = N° SNS normalizado
            session['sns'] = u['sns']
            session['nombre'] = u['nombre']
            session['rol'] = u.get('rol', '')
            return redirect(url_for('dashboard'))
        return render_template('login.html',
                               error='No existe una cuenta con ese N° SNS. Regístrate primero.',
                               sns=sns_raw)
    return render_template('login.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        f = request.form
        nombre = (f.get('nombre', '')).strip()
        sns = (f.get('sns', '')).strip()
        clave = f.get('clave', '')  # opcional en simulación (preparado para producción)
        datos = {'nombre': nombre, 'sns': sns}

        if not (nombre and sns):
            return render_template('registro.html', error='Completa nombre y N° SNS.', **datos)

        key = normalizar_id(sns)
        usuarios = cargar_usuarios()
        if key in usuarios:
            return render_template('registro.html', error='Ya existe una cuenta con ese N° SNS.', **datos)

        usuarios[key] = {
            'nombre': nombre, 'sns': sns, 'rol': 'asesor',
            'pass_hash': generate_password_hash(clave) if clave else None,
            'empresa': None,
        }
        guardar_usuarios(usuarios)
        session['rut'] = key            # identificador interno = N° SNS normalizado
        session['sns'] = sns
        session['nombre'] = nombre
        session['rol'] = 'asesor'
        # Tras crear la cuenta: ofrecer gestionar documentos (datos de empresa)
        return redirect(url_for('gestion_documentos'))
    return render_template('registro.html')


@app.route('/gestion-documentos', methods=['GET', 'POST'])
@login_required
def gestion_documentos():
    if request.method == 'POST':
        # "Omitir" / "No" → directo al panel
        if request.form.get('accion') == 'omitir':
            return redirect(url_for('dashboard'))
        f = request.form
        empresa = {
            'nombre': (f.get('empresa', '')).strip(),
            'rut': (f.get('rut_empresa', '')).strip(),
            'rubro': (f.get('rubro', '')).strip(),
            'mandante': (f.get('mandante', '')).strip(),
            'faena': (f.get('faena', '')).strip(),
        }
        if not empresa['nombre']:
            return render_template('gestion_documentos.html',
                                   error='Indica al menos el nombre de la empresa.', **empresa)
        usuarios = cargar_usuarios()
        if session.get('rut') in usuarios:
            usuarios[session['rut']]['empresa'] = empresa
            guardar_usuarios(usuarios)
        session['empresa'] = empresa['nombre']
        return redirect(url_for('dashboard'))
    return render_template('gestion_documentos.html')


@app.route('/prueba')
def prueba():
    """Acceso de PRUEBA momentáneo al panel de trabajo (sin pago).
    TEMPORAL: cuando se active el cobro, este acceso se reemplaza por el flujo de pago."""
    import secrets
    if not session.get('rut'):
        session['rut'] = 'PRUEBA-' + secrets.token_hex(4)
        session['sns'] = 'PRUEBA'
        session['nombre'] = 'Usuario de Prueba'
        session['rol'] = 'asesor'
    return redirect(url_for('dashboard'))


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


# ─────────────────── Motor de cumplimiento: contratos / matrices ────────────
def _consolidar(rut):
    """Devuelve los contratos del asesor con su estado de controles consolidado."""
    contratos = db.listar_contratos(rut)
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
                      'docs': [{'nombre': d['nombre'], 'tipo': d.get('tipo', 'evidencia')}
                               for d in docs.get(it['n'], [])]})
    aplicables = [i for i in items if i['estado'] != 'na']
    cumple = [i for i in aplicables if i['estado'] == 'cumple']
    pct = round(len(cumple) / len(aplicables) * 100) if aplicables else 0
    return {'items': items, 'cumplimiento_pct': pct}


def _carpeta_dir(numero, n):
    item = resso.CARPETA_DICT.get(n)
    carpeta = f"{n:02d}_" + re.sub(r'[^\w]+', '_', item['titulo'])[:40] if item else f"{n:02d}"
    destino = os.path.join(UPLOADS_DIR, secure_filename(numero), carpeta)
    os.makedirs(destino, exist_ok=True)
    return destino


def _datos(contrato):
    if contrato and contrato.get('datos_json'):
        try:
            return json.loads(contrato['datos_json'])
        except (TypeError, ValueError):
            return {}
    return {}


def _logo_data_uri(numero, datos):
    """Devuelve un data URI del logo de la empresa, o None."""
    logo = datos.get('logo')
    if not logo:
        return None
    ruta = os.path.join(UPLOADS_DIR, secure_filename(numero), secure_filename(logo))
    if not os.path.exists(ruta):
        return None
    import base64
    ext = os.path.splitext(logo)[1].lstrip('.').lower() or 'png'
    mime = 'jpeg' if ext in ('jpg', 'jpeg') else ext
    with open(ruta, 'rb') as fh:
        b64 = base64.b64encode(fh.read()).decode()
    return f"data:image/{mime};base64,{b64}"


def carta_na_html(contrato, datos, item, fundamento):
    """Genera una Carta de No Aplica (N/A) en HTML autocontenido (con logo si existe)."""
    hoy = date.today().strftime('%d-%m-%Y')
    empresa = (datos.get('empresa_contratista') or contrato.get('empresa') or '').strip()
    fund = (fundamento.strip() if fundamento and fundamento.strip() else '[Pendiente de fundamentar]')
    mandante = contrato.get('mandante', '') + (f" — {contrato.get('faena')}" if contrato.get('faena') else '')
    logo = _logo_data_uri(contrato.get('numero', ''), datos)
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
    """Crea/actualiza la carta N/A (HTML con logo) del ítem n y la registra en su carpeta."""
    item = resso.CARPETA_DICT.get(n)
    if not item:
        return
    datos = _datos(contrato)
    html = carta_na_html(contrato, datos, item, fundamento)
    nombre = f"Carta_NA_item{n:02d}_{secure_filename(contrato.get('numero', ''))}.html"
    destino = _carpeta_dir(contrato.get('numero', ''), n)
    with open(os.path.join(destino, nombre), 'w', encoding='utf-8') as fh:
        fh.write(html)
    db.eliminar_doc_tipo(cid, n, 'carta_na')          # evitar duplicados
    db.registrar_documento(cid, nombre, 'N/A', 'carta_na', item_n=n)


def replicar_controles(rut, control_key, origen_contrato_id):
    """Hereda como 'acreditado' un control aprobado a los demás contratos del asesor."""
    for c in db.listar_contratos(rut):
        if c['id'] == origen_contrato_id:
            continue
        if db.estado_control(c['id'], control_key) == 'aprobado':
            continue  # no degradar una aprobación propia
        db.set_estado_control(rut, c['id'], control_key, 'acreditado', origen_contrato_id)


@app.route('/api/contratos', methods=['GET'])
@login_required
def api_contratos():
    return jsonify(_consolidar(session['rut']))


@app.route('/api/contratos', methods=['POST'])
@login_required
def api_contrato_crear():
    f = request.get_json(silent=True) or request.form
    empresa = (f.get('empresa') or '').strip()
    numero = (f.get('numero') or '').strip()
    if not empresa or not numero:
        return jsonify({'error': 'Empresa y N° de contrato son obligatorios.'}), 400
    datos = f.get('datos') or {}
    datos_json = json.dumps(datos, ensure_ascii=False) if datos else None
    db.crear_contrato(session['rut'], empresa, (f.get('faena') or '').strip(),
                      numero, (f.get('mandante') or '').strip(), datos_json)
    return jsonify(_consolidar(session['rut']))


@app.route('/api/contratos/eliminar', methods=['POST'])
@login_required
def api_contrato_eliminar():
    f = request.get_json(silent=True) or request.form
    db.eliminar_contrato(session['rut'], int(f.get('id')))
    return jsonify(_consolidar(session['rut']))


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
@login_required
def api_fuf_get():
    return jsonify(db.estados_fuf(session['rut']))


@app.route('/api/fuf', methods=['POST'])
@login_required
def api_fuf_guardar():
    """Guarda en bloque los ítems del FUF enviados. Exige observación si es 'No Cumple'."""
    f = request.get_json(silent=True) or {}
    items = f.get('items') or []
    rut = session['rut']
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
        db.set_fuf_estado(rut, n, estado, obs, fecha_comp)
    return jsonify(db.estados_fuf(rut))


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
@login_required
def api_brechas():
    rut = session['rut']
    brechas = []
    for b in db.brechas_carpeta(rut):
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
    for b in db.brechas_fuf(rut):
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
        db.set_fuf_compromiso(session['rut'], n, fecha)
    elif fuente == 'carpeta':
        cid = f.get('contrato_id')
        if not db.contrato_de(session['rut'], cid):
            return jsonify({'error': 'Contrato no encontrado.'}), 404
        db.set_carpeta_compromiso(cid, n, fecha)
    else:
        return jsonify({'error': 'fuente inválida.'}), 400
    return jsonify({'ok': True})


@app.route('/api/contratos/<int:cid>/carpeta/<int:n>/documento', methods=['POST'])
@login_required
def api_carpeta_doc(cid, n):
    c = db.contrato_de(session['rut'], cid)
    if not c:
        return jsonify({'error': 'Contrato no encontrado.'}), 404
    archivos = request.files.getlist('archivo') or []
    if not archivos:
        return jsonify({'error': 'No se recibió archivo.'}), 400
    destino = _carpeta_dir(c['numero'], n)
    for archivo in archivos:
        if not archivo or not archivo.filename:
            continue
        archivo.save(os.path.join(destino, secure_filename(archivo.filename)))
        db.registrar_documento(cid, archivo.filename, '', 'evidencia', item_n=n)
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
        destino = _carpeta_dir(c['numero'], n)
        archivo.save(os.path.join(destino, secure_filename(nombre)))
        db.registrar_documento(cid, nombre, '', 'evidencia', item_n=n)
        reporte.append({'archivo': nombre, 'item': n,
                        'titulo': resso.CARPETA_DICT.get(n, {}).get('titulo', ''),
                        'fuente': fuente})
    return jsonify({'carpeta': _carpeta(cid), 'reporte': reporte})


@app.route('/api/contratos/<int:cid>/carpeta/<int:n>/archivo/<path:nombre>', methods=['GET'])
@login_required
def api_carpeta_descargar(cid, n, nombre):
    c = db.contrato_de(session['rut'], cid)
    if not c:
        return ('Contrato no encontrado', 404)
    carpeta = _carpeta_dir(c['numero'], n)
    # HTML (cartas) se abre en el navegador; el resto se descarga
    inline = nombre.lower().endswith(('.html', '.htm'))
    return send_from_directory(carpeta, secure_filename(nombre), as_attachment=not inline)


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
    nombre = 'empresa_logo' + ext  # sin guion bajo inicial (secure_filename lo eliminaría)
    destino = os.path.join(UPLOADS_DIR, secure_filename(c['numero']))
    os.makedirs(destino, exist_ok=True)
    archivo.save(os.path.join(destino, nombre))
    datos = _datos(c)
    datos['logo'] = nombre
    db.actualizar_datos(cid, json.dumps(datos, ensure_ascii=False))
    return jsonify(_consolidar(session['rut']))


@app.route('/api/contratos/<int:cid>/logo', methods=['GET'])
@login_required
def api_ver_logo(cid):
    c = db.contrato_de(session['rut'], cid)
    if not c:
        return ('', 404)
    datos = _datos(c)
    if not datos.get('logo'):
        return ('', 404)
    return send_from_directory(os.path.join(UPLOADS_DIR, secure_filename(c['numero'])),
                               secure_filename(datos['logo']))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
