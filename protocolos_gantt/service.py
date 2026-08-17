"""Lógica del módulo Carta Gantt de Protocolos MINSAL. Solo depende de db/models/catalogo — nunca
de app.py ni de otro módulo (aislamiento por carpeta)."""
from models import sqla, ProtocoloEtapaEstado

from . import catalogo


def _estados_de(empresa_id):
    return {e.etapa_clave: e.to_dict()
            for e in ProtocoloEtapaEstado.query.filter_by(empresa_id=empresa_id).all()}


def cargar(empresa_id):
    """Fases con sus actividades fusionadas con el estado guardado de la empresa, más el %
    de avance por fase y global. 'cumple' cuenta completo, 'en_proceso' cuenta media."""
    estados = _estados_de(empresa_id)
    fases_out = []
    total_pts, total_max = 0, 0
    for f in catalogo.FASES:
        acts = []
        pts, max_pts = 0, 0
        for a in f['actividades']:
            e = estados.get(a['clave']) or {}
            estado = e.get('estado') or 'pendiente'
            max_pts += 1
            pts += 1 if estado == 'cumple' else (0.5 if estado == 'en_proceso' else 0)
            acts.append({**a, 'estado': estado, 'responsable': e.get('responsable') or '',
                        'fecha_inicio': e.get('fecha_inicio') or '',
                        'fecha_termino': e.get('fecha_termino') or '',
                        'observacion': e.get('observacion') or '',
                        'evidencia_doc_id': e.get('evidencia_doc_id')})
        pct = round(100 * pts / max_pts) if max_pts else 0
        fases_out.append({'fase': f['fase'], 'titulo': f['titulo'], 'actividades': acts, 'pct': pct})
        total_pts += pts
        total_max += max_pts
    pct_global = round(100 * total_pts / total_max) if total_max else 0
    return {'fases': fases_out, 'pct_global': pct_global}


def etapa_guardar(empresa_id, etapa_clave, estado=None, responsable=None,
                  fecha_inicio=None, fecha_termino=None, observacion=None):
    """Upsert del estado de una actividad. Los campos no enviados (None) no se pisan."""
    row = ProtocoloEtapaEstado.query.filter_by(empresa_id=empresa_id, etapa_clave=etapa_clave).first()
    if not row:
        row = ProtocoloEtapaEstado(empresa_id=empresa_id, etapa_clave=etapa_clave, estado='pendiente')
        sqla.session.add(row)
    if estado is not None:
        row.estado = estado
    if responsable is not None:
        row.responsable = responsable
    if fecha_inicio is not None:
        row.fecha_inicio = fecha_inicio
    if fecha_termino is not None:
        row.fecha_termino = fecha_termino
    if observacion is not None:
        row.observacion = observacion
    from datetime import date
    row.fecha = date.today().isoformat()
    sqla.session.commit()
    return row.to_dict()


def etapa_set_evidencia(empresa_id, etapa_clave, doc_id):
    row = ProtocoloEtapaEstado.query.filter_by(empresa_id=empresa_id, etapa_clave=etapa_clave).first()
    if not row:
        row = ProtocoloEtapaEstado(empresa_id=empresa_id, etapa_clave=etapa_clave, estado='en_proceso')
        sqla.session.add(row)
    row.evidencia_doc_id = doc_id
    if row.estado == 'pendiente':
        row.estado = 'en_proceso'
    sqla.session.commit()
    return row.to_dict()
