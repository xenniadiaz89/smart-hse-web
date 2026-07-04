"""Motor de Generación Documental (Ronda 15) — módulo de responsabilidad única.

Genera el IRL (Identificación de Riesgos Laborales) de un trabajador **inyectando** desde la
Matriz de Riesgos vigente: por cada Tarea asignada, sus riesgos, medidas de control, EPP y PTS.
Salida = HTML autocontenido con el logo embebido (previsualización + PDF por impresión), guardado
como blob en `documento`. Reutiliza el patrón de `carta_na_html`/`_logo_data_uri` de app.py.

No introduce dependencias nuevas: usa `flask.render_template` (Jinja) sobre `templates/irl.html`.
"""
from datetime import date

from flask import render_template


def recolectar_irl(db, empresa, trabajador):
    """Arma el contexto del IRL desde la matriz vigente: tareas del trabajador con sus riesgos,
    medidas de control, EPP y PTS. Devuelve (ctx, matriz_version)."""
    empresa_id = empresa['id']
    matriz = db.matriz_riesgo_vigente(empresa_id)
    version = (matriz or {}).get('version', 0)
    tareas = []
    for t in db.tareas_de_trabajador(trabajador['id']):
        tareas.append({
            'tarea': t,
            'riesgos': db.riesgos_de_tarea(t['id']),
            'epp': db.epp_de_tarea(t['id']),
            'pts': db.pts_de_tarea(t['id']),
        })
    return {'empresa': empresa, 'trabajador': trabajador, 'tareas': tareas}, version


def generar_irl(db, empresa, trabajador, quien, logo_data_uri=None):
    """Genera/actualiza el IRL del trabajador tomando la versión VIGENTE de la matriz.
    Guarda el HTML como blob en `documento` y registra la auditoría. Devuelve dict con
    {doc_id, audit_id, html, matriz_version}."""
    ctx, version = recolectar_irl(db, empresa, trabajador)
    hoy = date.today().isoformat()
    audit_id = f"IRL-E{empresa['id']}-T{trabajador['id']}-mv{version}-{hoy}"
    html = render_template(
        'irl.html', empresa=empresa, trabajador=trabajador, tareas=ctx['tareas'],
        logo=logo_data_uri, audit_id=audit_id, matriz_version=version,
        generado_por=quien, fecha=date.today().strftime('%d-%m-%Y'))

    # persistir el IRL como blob (contenedor: contrato base de la empresa)
    base_cid = db.contrato_base(empresa['id'], empresa.get('rut_asesor'), empresa.get('razon_social'))
    doc_id = db.registrar_documento(
        base_cid, f"IRL - {trabajador.get('nombre') or trabajador.get('rut')}.html",
        'IRL', 'irl', contenido=html.encode('utf-8'), mimetype='text/html')
    db.irl_registrar(trabajador['id'], empresa['id'], version, doc_id, audit_id, quien)
    return {'doc_id': doc_id, 'audit_id': audit_id, 'html': html, 'matriz_version': version}
