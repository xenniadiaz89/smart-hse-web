"""Lógica del módulo GRD (Gestión de Riesgos de Desastres, ítem FUF 27).

Siembra las amenazas genéricas del estándar (grd/catalogo.py) para una empresa y calcula la
vulnerabilidad por amenaza y el nivel de cada medida de control (NA = NP × NC). Espeja la mecánica del
Excel oficial, pero de forma interactiva y persistida.
"""
from models import sqla, GRDAmenaza, GRDPregunta
from . import catalogo


def sembrar(empresa_id):
    """Inserta las amenazas genéricas + sus preguntas si la empresa aún no tiene GRD. Idempotente."""
    if GRDAmenaza.query.filter_by(empresa_id=empresa_id).first():
        return
    for i, a in enumerate(catalogo.AMENAZAS_BASE):
        am = GRDAmenaza(empresa_id=empresa_id, codigo=a['codigo'], nombre=a['nombre'],
                        descripcion=a['descripcion'], tipo='generica', identificada=0, orden=i)
        sqla.session.add(am)
        sqla.session.flush()
        for q in a['preguntas']:
            sqla.session.add(GRDPregunta(amenaza_id=am.id, empresa_id=empresa_id,
                                         codigo=q['codigo'], texto=q['texto']))
    sqla.session.commit()


def nivel_na(na):
    """Nivel de la medida a partir de NA = NP × NC (color para la UI)."""
    if not na:
        return {'txt': 'Sin valorar', 'color': 'gray'}
    if na <= 4:
        return {'txt': 'Bajo', 'color': 'green'}
    if na <= 8:
        return {'txt': 'Medio', 'color': 'amber'}
    return {'txt': 'Alto', 'color': 'red'}


def _vulnerabilidad(preguntas):
    """Vulnerabilidad de la amenaza: proporción de incumplimientos ('no') sobre las preguntas
    efectivamente respondidas (excluye 'na' y sin responder)."""
    aplicables = [p for p in preguntas if (p.cumplimiento or '') in ('si', 'no')]
    if not aplicables:
        return {'pct': None, 'txt': 'Sin evaluar', 'color': 'gray', 'brechas': 0, 'evaluadas': 0}
    brechas = sum(1 for p in aplicables if p.cumplimiento == 'no')
    pct = round(100 * brechas / len(aplicables))
    color = 'green' if pct < 30 else ('amber' if pct < 70 else 'red')
    txt = 'Baja' if pct < 30 else ('Media' if pct < 70 else 'Alta')
    return {'pct': pct, 'txt': txt, 'color': color, 'brechas': brechas, 'evaluadas': len(aplicables)}


def _pregunta_dict(p):
    na = (p.np or 0) * (p.nc or 0) if (p.np and p.nc) else None
    d = p.to_dict()
    d['na'] = na
    d['nivel'] = nivel_na(na)
    return d


def estado(empresa_id):
    """Estado completo del GRD de la empresa: amenazas + preguntas + métricas para la UI."""
    amenazas = (GRDAmenaza.query.filter_by(empresa_id=empresa_id)
                .order_by(GRDAmenaza.orden, GRDAmenaza.id).all())
    out = []
    for a in amenazas:
        preguntas = (GRDPregunta.query.filter_by(amenaza_id=a.id)
                     .order_by(GRDPregunta.id).all())
        d = a.to_dict()
        d['vulnerabilidad'] = _vulnerabilidad(preguntas)
        d['preguntas'] = [_pregunta_dict(p) for p in preguntas]
        out.append(d)
    resumen = {
        'amenazas': len(out),
        'identificadas': sum(1 for a in out if a['identificada']),
        'alto': sum(1 for a in out if a['vulnerabilidad']['color'] == 'red'),
    }
    return {'amenazas': out, 'resumen': resumen}
