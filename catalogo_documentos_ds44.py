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
