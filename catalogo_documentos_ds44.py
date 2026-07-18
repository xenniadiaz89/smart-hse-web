"""Catálogo de documentos del DS 44 enlazados a los ítems del FUF 44.

Cada ítem del FUF exige acreditar un documento. Este catálogo mapea, para los ítems que tienen
un formato conocido, el documento que corresponde: su evidencia requerida (referencia), los
campos que el usuario rellena y una plantilla HTML imprimible para GENERARLO cuando la empresa
no lo tiene. Si la empresa ya lo tiene, se sube (ver rutas /api/fuf/<n>/documento).

Dato puro, como fuf.py / catalogo_legal.py: no es Blueprint ni toca la BD. Las plantillas están
adaptadas de los formatos reales de la carpeta DS44/, LIMPIAS de datos de la empresa de muestra
(OmegaServicios) y de cualquier referencia a minería. Son REFERENCIA para que el prevencionista
valide y ajuste, no verdad cerrada (mismo criterio que los controles de la IPER).

Fase 1: motor completo + plantilla de la Política SST (ítem 1). Las demás plantillas del mapa
(Programa de trabajo, PTS EPP, Acta CPHS/Delegado, RIOHS, Investigación de accidentes, etc.) se
agregan como nuevos dicts en CATALOGO siguiendo el mismo patrón.

Estructura de un documento:
  {'tipo_doc': '<slug>', 'nombre': '<título>', 'items_fuf': [1, ...],
   'evidencia': '<qué acredita el ítem>', 'formato_origen': '<archivo de referencia>',
   'campos': [{'k': '<clave>', 'label': '<etiqueta>', 'tipo': 'text|textarea|date'}],
   'plantilla': <función(campos: dict, empresa: dict) -> str HTML imprimible>}
"""


def _esc(s):
    return ('' if s is None else str(s)).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


# ─────────────────────── Envoltorio HTML imprimible común ───────────────────────
# Mismo estilo que cartaNAHtml del dashboard: se abre en ventana e imprime a PDF.
def _documento_html(titulo, subtitulo, empresa, cuerpo_html, refs=None):
    refs = refs or []
    filas = ''.join(f'<tr><td class="k">{_esc(k)}</td><td>{_esc(v)}</td></tr>' for k, v in refs)
    nombre_emp = _esc((empresa or {}).get('razon_social') or (empresa or {}).get('nombre') or 'Empresa')
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>{_esc(titulo)}</title><style>
 body{{font-family:Arial,Helvetica,sans-serif;color:#1a2b3c;max-width:820px;margin:24px auto;padding:0 24px;line-height:1.55}}
 .head{{display:flex;justify-content:space-between;align-items:center;border-bottom:3px solid #006a9b;padding-bottom:14px;margin-bottom:20px}}
 .titulo{{text-align:right}} h1{{font-size:18px;margin:0;color:#006a9b}} .sub{{font-size:12px;color:#666}}
 table.meta{{width:100%;border-collapse:collapse;margin:14px 0;font-size:13px}} table.meta td{{padding:6px 8px;border-bottom:1px solid #eee}} td.k{{color:#666;width:230px;font-weight:600}}
 h2{{font-size:14px;color:#006a9b;margin:20px 0 6px}} p{{margin:8px 0}} ul{{margin:8px 0 8px 18px}} li{{margin:4px 0}}
 .firma{{margin-top:48px;border-top:1px solid #333;width:340px;padding-top:6px;font-size:13px}}
 .pie{{margin-top:24px;font-size:11px;color:#999}} @media print{{.noprint{{display:none}}}}</style></head><body>
 <div class="head"><div style="font-weight:800;color:#006a9b;font-size:20px">{nombre_emp}</div>
 <div class="titulo"><h1>{_esc(titulo)}</h1><div class="sub">{_esc(subtitulo)}</div></div></div>
 <table class="meta"><tr><td class="k">Empresa</td><td>{nombre_emp}</td></tr>{filas}</table>
 {cuerpo_html}
 <div class="pie">Smart HSE Chile · Documento de referencia generado automáticamente · revíselo y ajústelo antes de su aprobación · <button class="noprint" onclick="window.print()">Imprimir / Guardar PDF</button></div>
</body></html>"""


# ───────────────────────────── Plantilla: Política SST ─────────────────────────────
def _plantilla_politica_sst(c, empresa):
    nombre_emp = (empresa or {}).get('razon_social') or (empresa or {}).get('nombre') or 'la empresa'
    giro = c.get('giro') or 'sus actividades'
    representante = c.get('representante') or '__________________'
    ciudad = c.get('ciudad') or ''
    region = c.get('region') or ''
    fecha = c.get('fecha') or ''
    lugar = ', '.join(x for x in [ciudad, region] if x)
    cuerpo = f"""
 <p><b>{_esc(nombre_emp)}</b>, dedicada a {_esc(giro)}, consciente de los riesgos inherentes a
 sus actividades, establece la presente Política de Seguridad y Salud en el Trabajo como marco de
 su Sistema de Gestión (D.S. 44/2024), orientada a proteger la integridad física y la salud de
 todas las personas trabajadoras y de terceros. Esta política es conocida por todos los miembros
 de la organización y su cumplimiento es responsabilidad de quienes la integran.</p>
 <h2>Compromisos</h2>
 <ul>
   <li>Proporcionar condiciones de trabajo seguras y saludables para prevenir lesiones y el
       deterioro de la salud, con enfoque de género.</li>
   <li>Cumplir los requisitos legales aplicables en materia de prevención de riesgos laborales y
       otros compromisos que la organización suscriba.</li>
   <li>Identificar los peligros y evaluar los riesgos de todos los procesos, tareas y puestos de
       trabajo, y aplicar medidas de control según el orden de prelación (protección colectiva
       antes que EPP).</li>
   <li>Informar, capacitar y consultar a las personas trabajadoras y a sus representantes en las
       materias de seguridad y salud.</li>
   <li>Eliminar los peligros y reducir los riesgos, y mejorar continuamente el desempeño del
       Sistema de Gestión de la SST.</li>
 </ul>
 <p>La presente política se revisa periódicamente para mantener su vigencia y adecuación.</p>
 <div class="firma">{_esc(representante)}<br><span class="sub">Representante legal — {_esc(nombre_emp)}</span></div>
 {f'<p class="sub" style="margin-top:18px">{_esc(lugar)}{", " if lugar and fecha else ""}{_esc(fecha)}</p>' if (lugar or fecha) else ''}"""
    return _documento_html(
        'POLÍTICA DE SEGURIDAD Y SALUD EN EL TRABAJO',
        'D.S. 44/2024 · Art. 9 · Sistema de Gestión de la SST',
        empresa, cuerpo,
        refs=[('Norma', 'D.S. 44/2024 Art. 9'), ('Fecha', fecha or '—'),
              ('Representante legal', representante)])


# ────────────────────────────────── Catálogo ──────────────────────────────────
def _firmas(elabora='', revisa='', aprueba=''):
    """Bloque ELABORA / REVISA / APRUEBA de los formatos DS 44."""
    def col(rol, quien):
        return (f'<td style="width:33%;text-align:center;padding:10px 6px">'
                f'<div style="height:34px"></div><div style="border-top:1px solid #333;padding-top:4px">'
                f'<b>{_esc(rol)}</b><br><span class="sub">{_esc(quien) or "&nbsp;"}</span></div></td>')
    return (f'<table style="width:100%;border-collapse:collapse;margin-top:28px">'
            f'<tr>{col("Elabora", elabora)}{col("Revisa", revisa)}{col("Aprueba", aprueba)}</tr></table>')


def _plantilla_programa_trabajo(c, empresa):
    nombre_emp = (empresa or {}).get('razon_social') or (empresa or {}).get('nombre') or 'la empresa'
    periodo = c.get('periodo') or ''
    responsable = c.get('responsable') or ''
    cuerpo = f"""
 <h2>1. Objetivo y base</h2>
 <p>Establecer el Programa de Trabajo Preventivo de <b>{_esc(nombre_emp)}</b>, confeccionado a partir de la
 Matriz de Identificación de Peligros y Evaluación de Riesgos (MIPER), con las medidas preventivas y
 correctivas, sus plazos y responsables (D.S. 44/2024 Art. 8).</p>
 <h2>2. Contenido mínimo (Art. 8)</h2>
 <ul>
   <li>Medidas preventivas y correctivas priorizadas según la MIPER.</li>
   <li>Plazos de ejecución y responsables de cada medida.</li>
   <li>Actividades de prevención del consumo de alcohol y drogas.</li>
   <li>Promoción de vida y alimentación saludable.</li>
   <li>Conducción segura de vehículos cuando corresponda.</li>
   <li>Fechas de elaboración, modificación y aprobación.</li>
 </ul>
 <h2>3. Cronograma (referencia — completar desde la MIPER)</h2>
 <table style="width:100%;border-collapse:collapse;font-size:12px"><thead><tr>
   <th style="text-align:left;border-bottom:2px solid #cfe3ec;padding:5px">Medida / actividad</th>
   <th style="text-align:left;border-bottom:2px solid #cfe3ec;padding:5px">Responsable</th>
   <th style="text-align:left;border-bottom:2px solid #cfe3ec;padding:5px">Plazo</th>
   <th style="text-align:left;border-bottom:2px solid #cfe3ec;padding:5px">Estado</th></tr></thead>
   <tbody>{''.join('<tr><td style="border-bottom:1px solid #eee;padding:6px 5px;height:22px"></td><td style="border-bottom:1px solid #eee"></td><td style="border-bottom:1px solid #eee"></td><td style="border-bottom:1px solid #eee"></td></tr>' for _ in range(6))}</tbody></table>
 <p class="sub">Programa por escrito y aprobado por el representante legal; difundido en los lugares de trabajo y
 remitido un ejemplar al Comité Paritario.</p>
 {_firmas(elabora=responsable, aprueba='Representante legal')}"""
    return _documento_html('PROGRAMA DE TRABAJO PREVENTIVO', f'D.S. 44/2024 · Art. 8 · Período {_esc(periodo)}',
                           empresa, cuerpo, refs=[('Norma', 'D.S. 44/2024 Art. 8'),
                                                  ('Período', periodo or '—'), ('Responsable', responsable or '—')])


def _plantilla_pts_epp(c, empresa):
    nombre_emp = (empresa or {}).get('razon_social') or (empresa or {}).get('nombre') or 'la empresa'
    cuerpo = f"""
 <h2>1. Propósito y alcance</h2>
 <p>Regular la adquisición, selección, entrega, uso, mantención, reposición y disposición final de los
 Equipos de Protección Personal (EPP) en <b>{_esc(nombre_emp)}</b>, asegurando que toda persona trabajadora
 cuente con el EPP requerido para su puesto y esté capacitada en su uso (D.S. 44/2024 Art. 12 y 13).</p>
 <h2>2. Criterios</h2>
 <ul>
   <li>Los EPP se entregan solo ante el riesgo residual, tras privilegiar la protección colectiva (prelación).</li>
   <li>Adecuados al riesgo a cubrir y a las características de la persona.</li>
   <li>Certificados según norma de calidad o registrados en el ISP.</li>
   <li>Entregados libres de costo para la persona trabajadora.</li>
   <li>Con procedimiento de utilización, mantención, reposición o recambio.</li>
 </ul>
 <h2>3. Matriz de EPP por puesto (referencia — completar)</h2>
 <table style="width:100%;border-collapse:collapse;font-size:12px"><thead><tr>
   <th style="text-align:left;border-bottom:2px solid #cfe3ec;padding:5px">Puesto de trabajo</th>
   <th style="text-align:left;border-bottom:2px solid #cfe3ec;padding:5px">Riesgo</th>
   <th style="text-align:left;border-bottom:2px solid #cfe3ec;padding:5px">EPP requerido</th>
   <th style="text-align:left;border-bottom:2px solid #cfe3ec;padding:5px">Certificación / ISP</th></tr></thead>
   <tbody>{''.join('<tr><td style="border-bottom:1px solid #eee;padding:6px 5px;height:22px"></td><td style="border-bottom:1px solid #eee"></td><td style="border-bottom:1px solid #eee"></td><td style="border-bottom:1px solid #eee"></td></tr>' for _ in range(5))}</tbody></table>
 <h2>4. Registro de entrega</h2>
 <p>Toda entrega de EPP se registra por trabajador (fecha, EPP, cantidad, firma de recepción), constituyendo
 evidencia auditable.</p>
 {_firmas(elabora=c.get('elabora'), revisa=c.get('revisa'), aprueba=c.get('aprueba'))}"""
    return _documento_html('PROCEDIMIENTO DE EQUIPOS DE PROTECCIÓN PERSONAL (EPP)',
                           'D.S. 44/2024 · Art. 12 y 13 · DS 18 (certificación)', empresa, cuerpo,
                           refs=[('Norma', 'D.S. 44/2024 Art. 13 / DS 18')])


def _plantilla_acta_delegado(c, empresa):
    nombre_emp = (empresa or {}).get('razon_social') or (empresa or {}).get('nombre') or 'la empresa'
    fecha = c.get('fecha') or ''
    lugar = c.get('lugar') or ''
    n_trab = c.get('n_trabajadores') or ''
    delegado = c.get('delegado') or '__________________'
    rut_del = c.get('rut_delegado') or ''
    cuerpo = f"""
 <p>En {_esc(lugar)}, con fecha {_esc(fecha)}, reunida la asamblea de las personas trabajadoras de
 <b>{_esc(nombre_emp)}</b> (dotación declarada: {_esc(n_trab)}), se procede a la elección del
 <b>Delegado de Seguridad y Salud en el Trabajo</b>, conforme al D.S. 44/2024 Art. 66, aplicable a las
 entidades donde laboran entre 10 y 25 personas, por un período de dos años.</p>
 <h2>Resultado de la elección</h2>
 <table class="meta"><tr><td class="k">Delegado electo</td><td>{_esc(delegado)}</td></tr>
 <tr><td class="k">RUT</td><td>{_esc(rut_del)}</td></tr>
 <tr><td class="k">Fecha de elección</td><td>{_esc(fecha)}</td></tr>
 <tr><td class="k">Vigencia</td><td>2 años</td></tr></table>
 <p>La asamblea deja constancia del acto eleccionario. Copia de la presente acta se conserva como evidencia
 y queda a disposición de la fiscalización.</p>
 <div class="firma">{_esc(delegado)}<br><span class="sub">Delegado de SST electo</span></div>"""
    return _documento_html('ACTA DE ELECCIÓN — DELEGADO DE SEGURIDAD Y SALUD EN EL TRABAJO',
                           'D.S. 44/2024 · Art. 66', empresa, cuerpo,
                           refs=[('Norma', 'D.S. 44/2024 Art. 66'), ('Fecha', fecha or '—')])


def _plantilla_riohs(c, empresa):
    nombre_emp = (empresa or {}).get('razon_social') or (empresa or {}).get('nombre') or 'la empresa'
    vigencia = c.get('vigencia') or ''
    cuerpo = f"""
 <p>Reglamento Interno de Higiene y Seguridad de <b>{_esc(nombre_emp)}</b>, dictado conforme a la Ley 16.744
 y al D.S. 44/2024, de conocimiento y cumplimiento obligatorio para todas las personas trabajadoras.</p>
 <h2>Estructura (contenido mínimo)</h2>
 <ul>
   <li><b>Preámbulo</b> y ámbito de aplicación.</li>
   <li><b>Disposiciones generales</b> del sistema de gestión preventiva.</li>
   <li><b>Obligaciones</b> de las personas trabajadoras en materia de SST.</li>
   <li><b>Prohibiciones</b> en materia de seguridad y salud.</li>
   <li><b>Obligación de informar</b> los riesgos laborales (derecho a saber).</li>
   <li><b>Procedimiento de reclamos</b> conforme a la Ley 16.744.</li>
   <li><b>Sanciones</b> y su procedimiento de aplicación.</li>
   <li><b>Vigencia y actualización</b> (revisión no inferior a un año).</li>
 </ul>
 <p class="sub">Se entrega gratuitamente a cada persona trabajadora y se envía, 30 días antes de su entrada
 en vigencia, para observaciones, a las personas trabajadoras, al Comité Paritario y al Departamento de
 Prevención de Riesgos cuando corresponda.</p>
 {_firmas(elabora='Prevención de Riesgos', aprueba='Representante legal')}"""
    return _documento_html('REGLAMENTO INTERNO DE HIGIENE Y SEGURIDAD (RIOHS)',
                           f'Ley 16.744 · D.S. 44/2024 · Vigencia {_esc(vigencia)}', empresa, cuerpo,
                           refs=[('Norma', 'Ley 16.744 / D.S. 44/2024'), ('Vigencia', vigencia or '—')])


def _plantilla_programa_capacitaciones(c, empresa):
    nombre_emp = (empresa or {}).get('razon_social') or (empresa or {}).get('nombre') or 'la empresa'
    anio = c.get('anio') or ''
    responsable = c.get('responsable') or ''
    cuerpo = f"""
 <h2>Objetivo</h2>
 <p>Programa Anual de Capacitación en prevención de riesgos de <b>{_esc(nombre_emp)}</b> ({_esc(anio)}), con
 enfoque de género, incluyendo la información de los riesgos laborales (IRL), el uso de EPP y la respuesta
 ante emergencias (D.S. 44/2024 Art. 16 y 21).</p>
 <h2>Plan anual (referencia — completar)</h2>
 <table style="width:100%;border-collapse:collapse;font-size:12px"><thead><tr>
   <th style="text-align:left;border-bottom:2px solid #cfe3ec;padding:5px">Actividad / curso</th>
   <th style="text-align:left;border-bottom:2px solid #cfe3ec;padding:5px">Destinatarios (cargo)</th>
   <th style="text-align:left;border-bottom:2px solid #cfe3ec;padding:5px">Horas</th>
   <th style="text-align:left;border-bottom:2px solid #cfe3ec;padding:5px">Trimestre</th>
   <th style="text-align:left;border-bottom:2px solid #cfe3ec;padding:5px">Relator / OAL</th></tr></thead>
   <tbody>{''.join('<tr><td style="border-bottom:1px solid #eee;padding:6px 5px;height:22px"></td><td style="border-bottom:1px solid #eee"></td><td style="border-bottom:1px solid #eee"></td><td style="border-bottom:1px solid #eee"></td><td style="border-bottom:1px solid #eee"></td></tr>' for _ in range(6))}</tbody></table>
 <p class="sub">Cada actividad deja registro (asistentes, contenidos, relator, evaluación) como evidencia.</p>
 {_firmas(elabora=responsable, aprueba='Representante legal')}"""
    return _documento_html('PROGRAMA ANUAL DE CAPACITACIONES', f'D.S. 44/2024 · Art. 16 y 21 · Año {_esc(anio)}',
                           empresa, cuerpo, refs=[('Norma', 'D.S. 44/2024 Art. 16'), ('Año', anio or '—'),
                                                  ('Responsable', responsable or '—')])


def _plantilla_investigacion(c, empresa):
    nombre_emp = (empresa or {}).get('razon_social') or (empresa or {}).get('nombre') or 'la empresa'
    fecha = c.get('fecha_evento') or ''
    lugar = c.get('lugar') or ''
    tipo = c.get('tipo') or ''
    afectado = c.get('afectado') or ''
    cargo = c.get('cargo') or ''
    cuerpo = f"""
 <table class="meta">
   <tr><td class="k">Tipo de evento</td><td>{_esc(tipo)}</td></tr>
   <tr><td class="k">Fecha y hora</td><td>{_esc(fecha)}</td></tr>
   <tr><td class="k">Lugar</td><td>{_esc(lugar)}</td></tr>
   <tr><td class="k">Persona afectada</td><td>{_esc(afectado)}</td></tr>
   <tr><td class="k">Cargo</td><td>{_esc(cargo)}</td></tr></table>
 <h2>1. Descripción del evento</h2>
 <p style="min-height:40px;border:1px solid #eee;border-radius:6px;padding:8px">&nbsp;</p>
 <h2>2. Análisis de causas</h2>
 <p><b>Causas inmediatas</b> (actos y condiciones):</p>
 <p style="min-height:34px;border:1px solid #eee;border-radius:6px;padding:8px">&nbsp;</p>
 <p><b>Causas básicas / raíz</b> (factores personales y del trabajo):</p>
 <p style="min-height:34px;border:1px solid #eee;border-radius:6px;padding:8px">&nbsp;</p>
 <h2>3. Medidas correctivas</h2>
 <table style="width:100%;border-collapse:collapse;font-size:12px"><thead><tr>
   <th style="text-align:left;border-bottom:2px solid #cfe3ec;padding:5px">Medida</th>
   <th style="text-align:left;border-bottom:2px solid #cfe3ec;padding:5px">Responsable</th>
   <th style="text-align:left;border-bottom:2px solid #cfe3ec;padding:5px">Plazo</th></tr></thead>
   <tbody>{''.join('<tr><td style="border-bottom:1px solid #eee;padding:6px 5px;height:22px"></td><td style="border-bottom:1px solid #eee"></td><td style="border-bottom:1px solid #eee"></td></tr>' for _ in range(4))}</tbody></table>
 <p class="sub">Investigación con enfoque de género. Se actualiza la MIPER si el evento revela nuevos riesgos
 (D.S. 44/2024 Art. 71-75).</p>
 {_firmas(elabora='Investigador', revisa='Comité Paritario', aprueba='Prevención de Riesgos')}"""
    return _documento_html('INFORME DE INVESTIGACIÓN DE ACCIDENTES / INCIDENTES',
                           'D.S. 44/2024 · Art. 71 a 75', empresa, cuerpo,
                           refs=[('Norma', 'D.S. 44/2024 Art. 71-75'), ('Fecha del evento', fecha or '—')])


def _plantilla_estadisticas(c, empresa):
    """Data-driven: la ruta api_fuf_generar inyecta c['_resumen'] = db.estadisticas_resumen(...)."""
    anio = c.get('anio') or ''
    r = c.get('_resumen') or {'detalle': [], 'acumulado': {}}
    ac = r.get('acumulado') or {}
    filas = ''.join(
        f'<tr><td>{_esc(d["nombre"])}</td><td style="text-align:right">{d["n_accidentes"]}</td>'
        f'<td style="text-align:right">{d["dias_perdidos"]}</td><td style="text-align:right">{d["n_trabajadores"]}</td>'
        f'<td style="text-align:right">{d["hh_trabajadas"]}</td><td style="text-align:right">{d["if"]}</td>'
        f'<td style="text-align:right">{d["ig"]}</td><td style="text-align:right">{d["ta"]}</td></tr>'
        for d in r.get('detalle', []))
    cuerpo = f"""
 <style>table.est{{width:100%;border-collapse:collapse;font-size:11px;margin:8px 0}}
  table.est th{{background:#f0f6f9;text-align:right;padding:5px;border-bottom:2px solid #cfe3ec;color:#006a9b}}
  table.est th:first-child,table.est td:first-child{{text-align:left}}
  table.est td{{padding:4px 5px;border-bottom:1px solid #eee}}
  table.est tfoot td{{font-weight:bold;border-top:2px solid #cfe3ec;background:#fafcfd}}</style>
 <h2>Indicadores acumulados {_esc(anio)}</h2>
 <p>N° accidentes: <b>{ac.get('accidentes', 0)}</b> · Días perdidos: <b>{ac.get('dias_perdidos', 0)}</b> ·
    HH trabajadas: <b>{ac.get('hh_trabajadas', 0)}</b> · Índice de Frecuencia: <b>{ac.get('if', 0)}</b> ·
    Índice de Gravedad: <b>{ac.get('ig', 0)}</b> · Tasa de accidentabilidad: <b>{ac.get('ta', 0)}</b>.</p>
 <h2>Detalle mensual</h2>
 <table class="est"><thead><tr><th>Mes</th><th>Accid.</th><th>Días perd.</th><th>Trabaj.</th><th>HH</th>
   <th>I. Frec.</th><th>I. Grav.</th><th>Tasa acc.</th></tr></thead>
   <tbody>{filas}</tbody>
   <tfoot><tr><td>Acumulado</td><td style="text-align:right">{ac.get('accidentes', 0)}</td>
     <td style="text-align:right">{ac.get('dias_perdidos', 0)}</td><td></td>
     <td style="text-align:right">{ac.get('hh_trabajadas', 0)}</td>
     <td style="text-align:right">{ac.get('if', 0)}</td><td style="text-align:right">{ac.get('ig', 0)}</td>
     <td style="text-align:right">{ac.get('ta', 0)}</td></tr></tfoot></table>
 <p class="sub">IF = accidentes·1.000.000 / HH · IG = días perdidos·1.000.000 / HH ·
    Tasa de accidentabilidad = accidentes·100 / N° trabajadores. Registro de la gestión preventiva de la
    empresa (D.S. 44/2024 Art. 73-75).</p>
 {_firmas(elabora='Prevención de Riesgos', aprueba='Representante legal')}"""
    return _documento_html('REGISTRO DE ESTADÍSTICAS E INDICADORES DE PREVENCIÓN',
                           f'D.S. 44/2024 · Art. 73-75 · Año {_esc(anio)}', empresa, cuerpo,
                           refs=[('Norma', 'D.S. 44/2024 Art. 73-75'), ('Año', anio or '—')])


CATALOGO = [
    {'tipo_doc': 'politica_sst',
     'nombre': 'Política de Seguridad y Salud en el Trabajo',
     'items_fuf': [1],
     'evidencia': 'Política SST por escrito, firmada por el representante legal y difundida a la organización.',
     'formato_origen': 'DS44/Política de Seguridad Salud y Medio Ambiente.docx',
     'campos': [
         {'k': 'representante', 'label': 'Representante legal', 'tipo': 'text'},
         {'k': 'giro', 'label': 'Giro / actividad de la empresa', 'tipo': 'text'},
         {'k': 'ciudad', 'label': 'Ciudad', 'tipo': 'text'},
         {'k': 'region', 'label': 'Región', 'tipo': 'text'},
         {'k': 'fecha', 'label': 'Fecha', 'tipo': 'date'},
     ],
     'plantilla': _plantilla_politica_sst},

    {'tipo_doc': 'programa_trabajo',
     'nombre': 'Programa de Trabajo Preventivo',
     'items_fuf': [8, 9, 10, 11],
     'evidencia': 'Programa de trabajo preventivo por escrito, elaborado desde la MIPER, aprobado por el representante legal y difundido.',
     'formato_origen': 'DS44/CARTA GANTT PROGRAMA DE IMPLEMENTACION DS 44.xlsx',
     'campos': [
         {'k': 'periodo', 'label': 'Período (año)', 'tipo': 'text'},
         {'k': 'responsable', 'label': 'Responsable de elaboración', 'tipo': 'text'},
     ],
     'plantilla': _plantilla_programa_trabajo},

    {'tipo_doc': 'pts_epp',
     'nombre': 'Procedimiento de EPP (selección, entrega, uso y reposición)',
     'items_fuf': [14, 15, 16, 17],
     'evidencia': 'Procedimiento de EPP + matriz por puesto + registro de entrega por trabajador (EPP certificado ISP, sin costo).',
     'formato_origen': 'DS44/PTS procedimiento Estandar de Seleccion, reposicion y entrega de epp DS44.docx',
     'campos': [
         {'k': 'elabora', 'label': 'Elabora', 'tipo': 'text'},
         {'k': 'revisa', 'label': 'Revisa', 'tipo': 'text'},
         {'k': 'aprueba', 'label': 'Aprueba', 'tipo': 'text'},
     ],
     'plantilla': _plantilla_pts_epp},

    {'tipo_doc': 'acta_delegado',
     'nombre': 'Acta de Elección del Delegado de SST',
     'items_fuf': [39, 40],
     'evidencia': 'Acta de asamblea de elección del Delegado de SST (entre 10 y 25 personas, cada 2 años).',
     'formato_origen': 'DS44/Formatos ACTA elección Delegado de Seguridad y Salud en el Trabajo.xls',
     'campos': [
         {'k': 'fecha', 'label': 'Fecha de elección', 'tipo': 'date'},
         {'k': 'lugar', 'label': 'Lugar', 'tipo': 'text'},
         {'k': 'n_trabajadores', 'label': 'N° de trabajadores', 'tipo': 'text'},
         {'k': 'delegado', 'label': 'Delegado electo', 'tipo': 'text'},
         {'k': 'rut_delegado', 'label': 'RUT del delegado', 'tipo': 'text'},
     ],
     'plantilla': _plantilla_acta_delegado},

    {'tipo_doc': 'riohs',
     'nombre': 'Reglamento Interno de Higiene y Seguridad (RIOHS)',
     'items_fuf': [49, 50, 51, 52],
     'evidencia': 'RIOHS al día, entregado gratuitamente, con obligación de informar, procedimiento de reclamos y vigencia.',
     'formato_origen': 'Ley 16.744 / D.S. 44/2024',
     'campos': [
         {'k': 'vigencia', 'label': 'Fecha de entrada en vigencia', 'tipo': 'date'},
     ],
     'plantilla': _plantilla_riohs},

    {'tipo_doc': 'programa_capacitaciones',
     'nombre': 'Programa Anual de Capacitaciones',
     'items_fuf': [18, 19, 23, 24],
     'evidencia': 'Programa anual de capacitación (IRL, EPP, emergencias) con registro de asistentes y evaluación.',
     'formato_origen': 'DS44/FORMATO PROGRAMA ANUAL DE CAPACITACIONES  DS44.xlsx',
     'campos': [
         {'k': 'anio', 'label': 'Año', 'tipo': 'text'},
         {'k': 'responsable', 'label': 'Responsable', 'tipo': 'text'},
     ],
     'plantilla': _plantilla_programa_capacitaciones},

    {'tipo_doc': 'investigacion_accidentes',
     'nombre': 'Informe de Investigación de Accidentes / Incidentes',
     'items_fuf': [59],
     'evidencia': 'Investigación de causas con enfoque de género, medidas correctivas con responsable y plazo.',
     'formato_origen': 'DS44/FORMATO INVESTIGACIÓN DE ACCIDENTES E INCIDENTES DS 44.xlsx',
     'campos': [
         {'k': 'tipo', 'label': 'Tipo (accidente / incidente / EP)', 'tipo': 'text'},
         {'k': 'fecha_evento', 'label': 'Fecha y hora del evento', 'tipo': 'text'},
         {'k': 'lugar', 'label': 'Lugar', 'tipo': 'text'},
         {'k': 'afectado', 'label': 'Persona afectada', 'tipo': 'text'},
         {'k': 'cargo', 'label': 'Cargo', 'tipo': 'text'},
     ],
     'plantilla': _plantilla_investigacion},

    {'tipo_doc': 'estadisticas',
     'nombre': 'Registro de Estadísticas e Indicadores de Prevención',
     'items_fuf': [47, 60],
     'evidencia': 'Registro mensual de accidentes, días perdidos e indicadores (frecuencia, gravedad, accidentabilidad) de la empresa.',
     'formato_origen': 'DS44/FORMATO COMPLETO ESTADISTICAS MENSUALES DS44.xlsx',
     'campos': [
         {'k': 'anio', 'label': 'Año del registro', 'tipo': 'text'},
     ],
     'plantilla': _plantilla_estadisticas},
]


# ───────────────────────────────── Helpers ─────────────────────────────────
INDEX = {d['tipo_doc']: d for d in CATALOGO}


def por_item(n):
    """Documentos generables/cargables aplicables al ítem FUF n (puede haber más de uno)."""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return []
    return [d for d in CATALOGO if n in d['items_fuf']]


def evidencia_de(n):
    """Texto de evidencia requerida para el ítem FUF n. '' si el ítem no tiene formato mapeado."""
    docs = por_item(n)
    return docs[0]['evidencia'] if docs else ''


def documento(tipo_doc):
    return INDEX.get(tipo_doc)


def generar_html(tipo_doc, campos, empresa):
    """Devuelve el HTML del documento, o None si el tipo no existe."""
    d = INDEX.get(tipo_doc)
    if not d:
        return None
    return d['plantilla'](campos or {}, empresa or {})


def resumen_para_item(n):
    """Lo que el front necesita para pintar el ítem: tipos generables + sus campos + evidencia."""
    return {
        'evidencia': evidencia_de(n),
        'tipos': [{'tipo_doc': d['tipo_doc'], 'nombre': d['nombre'], 'campos': d['campos']}
                  for d in por_item(n)],
    }


def enriquecer_fuf(secciones):
    """Copia de las SECCIONES del FUF con, por ítem, su evidencia de referencia ('ev') y los
    documentos generables ('docs'). No muta el original (fuf.SECCIONES es dato compartido)."""
    out = []
    for s in secciones:
        items = []
        for it in s['items']:
            r = resumen_para_item(it['n'])
            items.append({**it, 'ev': r['evidencia'], 'docs': r['tipos']})
        out.append({**s, 'items': items})
    return out
