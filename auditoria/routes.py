"""Módulo 5 — Carpeta de auditoría. Rutas aisladas en Blueprint.

Sin url_prefix, igual que el resto de los módulos: las URLs son /api/auditoria*.

La vista vive dentro del dashboard (no es página propia), así que aquí solo hay API: el índice
que la pinta y la descarga del .zip.
"""
import zipfile
from datetime import datetime
from io import BytesIO

from flask import Blueprint, request, jsonify, session, send_file

import db
from core_auth import empresa_required, onboarding_required, empresa_id

from . import service

bp = Blueprint('auditoria', __name__)


def _esc(s):
    return ('' if s is None else str(s)).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


@bp.route('/api/auditoria', methods=['GET'])
@empresa_required
@onboarding_required
def api_indice():
    """Todo lo que la carpeta contiene y lo que le falta."""
    return jsonify(service.indice(empresa_id(), session.get('rut')))


def _indice_html(datos, incluidos, faltantes):
    """Portada del .zip: qué se entrega, dónde está cada cosa y qué brechas quedan.

    Se incluye SIEMPRE, también cuando hay brechas. Una carpeta que oculta lo que falta es peor
    que inútil ante un fiscalizador: el índice dice la verdad de lo que hay.
    """
    emp = datos['empresa']
    r = datos['resumen']
    hoy = datetime.now().strftime('%d-%m-%Y %H:%M')

    filas = []
    for bloque in datos['bloques']:
        if not bloque['n_docs']:
            continue
        filas.append(f'<tr class="sec"><td colspan="3">{_esc(bloque["nombre"])}'
                     f'<span class="n">{bloque["n_docs"]} documento(s)</span></td></tr>')
        for g in bloque['grupos']:
            for d in g['docs']:
                ruta = incluidos.get(d['id'])
                if not ruta:
                    continue
                extra = f' · {_esc(d["subtitulo"])}' if d.get('subtitulo') else ''
                filas.append(
                    f'<tr><td>{_esc(g["titulo"])}{extra}</td>'
                    f'<td>{_esc(d["nombre"])}</td>'
                    f'<td class="mono">{_esc(d.get("fecha") or "—")}</td></tr>')

    brechas = ''.join(
        f'<li class="{b["gravedad"]}"><b>{_esc(b["bloque"])}</b> — {_esc(b["texto"])}'
        + (f'<span class="det">{_esc(b["detalle"])}</span>' if b.get('detalle') else '')
        + '</li>' for b in datos['brechas'])

    aviso_falt = ''
    if faltantes:
        aviso_falt = (f'<p class="nota">{len(faltantes)} documento(s) del índice no pudieron '
                      'incluirse porque no tienen archivo adjunto (son registros de solo nombre o '
                      'referencias a un documento maestro).</p>')

    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Carpeta de auditoría — {_esc(emp.get('razon_social'))}</title><style>
 body{{font-family:Arial,Helvetica,sans-serif;color:#1a2b3c;max-width:900px;margin:24px auto;padding:0 24px;line-height:1.55}}
 .head{{border-bottom:3px solid #006a9b;padding-bottom:14px;margin-bottom:18px}}
 h1{{font-size:20px;margin:0;color:#006a9b}} .sub{{font-size:12px;color:#666;margin-top:4px}}
 .kpis{{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0}}
 .kpi{{border:1px solid #e0e6e9;border-radius:8px;padding:10px 14px;min-width:120px}}
 .kpi b{{display:block;font-size:22px;color:#006a9b}} .kpi span{{font-size:10px;text-transform:uppercase;color:#888;letter-spacing:.06em}}
 .kpi.warn b{{color:#b45309}}
 h2{{font-size:14px;color:#006a9b;margin:26px 0 8px;text-transform:uppercase;letter-spacing:.05em}}
 table{{width:100%;border-collapse:collapse;font-size:12.5px}}
 td{{padding:6px 8px;border-bottom:1px solid #eee;vertical-align:top}}
 tr.sec td{{background:#f1f5f7;font-weight:700;color:#0B3B60;font-size:12px}}
 tr.sec .n{{float:right;font-weight:400;color:#777}}
 .mono{{font-family:ui-monospace,Menlo,monospace;color:#777;white-space:nowrap}}
 ul{{margin:8px 0 8px 18px;font-size:12.5px}} li{{margin:5px 0}}
 li.alta{{color:#9E2F28}} li.media{{color:#9A5B0C}}
 .det{{display:block;color:#888;font-size:11px}}
 .nota{{font-size:11.5px;color:#888;background:#f7f9fa;border-left:3px solid #d5dee2;padding:8px 12px;margin-top:14px}}
 .pie{{margin-top:28px;font-size:11px;color:#999;border-top:1px solid #eee;padding-top:12px}}
</style></head><body>
<div class="head"><h1>Carpeta de auditoría</h1>
<div class="sub"><b>{_esc(emp.get('razon_social') or 'Empresa')}</b>
{f" · RUT {_esc(emp.get('rut'))}" if emp.get('rut') else ''}
{f" · {_esc(emp.get('mutual'))}" if emp.get('mutual') else ''} · generada el {hoy}</div></div>

<div class="kpis">
  <div class="kpi"><b>{len(incluidos)}</b><span>archivos incluidos</span></div>
  <div class="kpi"><b>{r['bloques_con_contenido']}</b><span>bloques con contenido</span></div>
  <div class="kpi {'warn' if r['brechas'] else ''}"><b>{r['brechas']}</b><span>brechas detectadas</span></div>
  <div class="kpi {'warn' if r['brechas_altas'] else ''}"><b>{r['brechas_altas']}</b><span>de atención prioritaria</span></div>
</div>

<h2>Contenido de la carpeta</h2>
<table>{''.join(filas) or '<tr><td colspan="3">Sin documentos.</td></tr>'}</table>
{aviso_falt}

<h2>Brechas pendientes</h2>
{f'<ul>{brechas}</ul>' if brechas else '<p style="font-size:12.5px;color:#4F7A1E">Sin brechas detectadas en los bloques revisados.</p>'}

<div class="pie">Smart HSE Chile · Índice generado automáticamente a partir de los documentos
registrados en la plataforma. Las brechas listadas son las que el sistema puede detectar; no
sustituyen la revisión del experto en prevención.</div>
</body></html>"""


@bp.route('/api/auditoria/export.zip', methods=['GET'])
@empresa_required
@onboarding_required
def api_export():
    """Descarga la carpeta completa como .zip, con subcarpetas por bloque y un índice de portada.

    Los documentos sin archivo adjunto (registros de solo nombre, o referencias cuyo maestro se
    borró) no se inventan: se omiten y el índice declara cuántos fueron.
    """
    eid, rut = empresa_id(), session.get('rut')
    datos = service.indice(eid, rut)
    solo_brechas = request.args.get('solo_indice') == '1'

    buffer = BytesIO()
    incluidos, faltantes, usados = {}, [], set()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
        if not solo_brechas:
            for bloque in datos['bloques']:
                for grupo in bloque['grupos']:
                    for doc in grupo['docs']:
                        blob = db.documento_contenido(rut, doc['id'])
                        if not blob:
                            faltantes.append(doc['id'])
                            continue
                        ruta = service.ruta_zip(bloque, grupo, doc, usados)
                        z.writestr(ruta, blob[0])
                        incluidos[doc['id']] = ruta
        z.writestr('00 INDICE.html', _indice_html(datos, incluidos, faltantes).encode('utf-8'))

    buffer.seek(0)
    empresa = (datos['empresa'].get('razon_social') or 'empresa')
    nombre = f"Carpeta de auditoria - {service._limpiar(empresa, 60)} - {datetime.now():%Y-%m-%d}.zip"
    return send_file(buffer, mimetype='application/zip', as_attachment=True, download_name=nombre)
