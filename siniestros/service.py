"""Lógica del módulo Siniestros. Solo depende de db/models/estadisticas/dias_cargo — nunca de
app.py ni de otro módulo (aislamiento por carpeta, mismo criterio que nomina/service.py)."""
from datetime import date

import db
import dias_cargo
import estadisticas
from models import sqla, Siniestro


def _fila_con_dias_cargo(s):
    d = dict(s)
    d['dias_cargo'] = dias_cargo.dias_cargo_de(d.get('tipo_lesion'), d.get('dias_cargo_manual'))
    return d


def listar(empresa_id, anio=None):
    q = Siniestro.query.filter_by(empresa_id=empresa_id)
    if anio:
        anio = str(int(anio))
        q = q.filter(Siniestro.fecha.like(f'{anio}-%'))
    rows = q.order_by(Siniestro.fecha.desc(), Siniestro.id.desc()).all()
    return [_fila_con_dias_cargo(s.to_dict()) for s in rows]


def _siniestro_de(empresa_id, sid):
    return Siniestro.query.filter_by(id=sid, empresa_id=empresa_id).first()


def crear(empresa_id, datos, creado_por=None):
    fecha = (datos.get('fecha') or '').strip()
    if not fecha:
        raise ValueError('Indica la fecha del siniestro.')
    trab_id = datos.get('trabajador_id')
    s = Siniestro(
        empresa_id=empresa_id,
        trabajador_id=int(trab_id) if trab_id else None,
        fecha=fecha,
        faena=(datos.get('faena') or '').strip() or None,
        tipo_evento=(datos.get('tipo_evento') or 'accidente').strip(),
        tipo_lesion=(datos.get('tipo_lesion') or '').strip() or None,
        con_tiempo_perdido=1 if str(datos.get('con_tiempo_perdido')) in ('1', 'true', 'True', 'on', 'si') else 0,
        dias_perdidos=max(0, int(datos.get('dias_perdidos') or 0)),
        dias_cargo_manual=(int(datos['dias_cargo_manual']) if datos.get('dias_cargo_manual') not in (None, '') else None),
        descripcion=(datos.get('descripcion') or '').strip() or None,
        creado_por=creado_por,
        creado=date.today().isoformat(),
    )
    sqla.session.add(s)
    sqla.session.commit()
    return _fila_con_dias_cargo(s.to_dict())


def editar(empresa_id, sid, datos):
    s = _siniestro_de(empresa_id, sid)
    if not s:
        return None
    campos_texto = ('fecha', 'faena', 'tipo_evento', 'tipo_lesion', 'descripcion')
    for c in campos_texto:
        if c in datos:
            setattr(s, c, (datos[c] or '').strip() or None)
    if 'trabajador_id' in datos:
        s.trabajador_id = int(datos['trabajador_id']) if datos['trabajador_id'] else None
    if 'con_tiempo_perdido' in datos:
        s.con_tiempo_perdido = 1 if str(datos['con_tiempo_perdido']) in ('1', 'true', 'True', 'on', 'si') else 0
    if 'dias_perdidos' in datos:
        s.dias_perdidos = max(0, int(datos['dias_perdidos'] or 0))
    if 'dias_cargo_manual' in datos:
        s.dias_cargo_manual = int(datos['dias_cargo_manual']) if datos['dias_cargo_manual'] not in (None, '') else None
    sqla.session.commit()
    return _fila_con_dias_cargo(s.to_dict())


def eliminar(empresa_id, sid):
    s = _siniestro_de(empresa_id, sid)
    if not s:
        return False
    sqla.session.delete(s)
    sqla.session.commit()
    return True


def kpis(empresa_id, anio):
    """KPIs en tiempo real del año: Tasa de Frecuencia, Tasa de Gravedad (con días cargo) y Tasa
    de Accidentabilidad, calculados desde los siniestros individuales. Las HH trabajadas y la
    dotación se reutilizan del agregado mensual ya cargado en EstadisticaMensual (db.estadisticas_de)
    en vez de pedirlas de nuevo, para no duplicar esa entrada de datos."""
    anio = int(anio)
    filas = listar(empresa_id, anio)
    mensual = db.estadisticas_de(empresa_id, anio)
    hh_trabajadas = sum(f.get('hh_trabajadas') or 0 for f in mensual)
    n_trabajadores = max((f.get('n_trabajadores') or 0) for f in mensual) if mensual else 0

    n_accidentes = sum(1 for f in filas if f.get('tipo_evento') == 'accidente' and f.get('con_tiempo_perdido'))
    dias_perdidos_totales = sum(f.get('dias_perdidos') or 0 for f in filas)
    dias_cargo_totales = sum(f.get('dias_cargo') or 0 for f in filas)

    return {
        'anio': anio,
        'n_siniestros': len(filas),
        'n_accidentes': n_accidentes,
        'dias_perdidos_totales': dias_perdidos_totales,
        'dias_cargo_totales': dias_cargo_totales,
        'hh_trabajadas': int(hh_trabajadas),
        'if': estadisticas.indice_frecuencia(n_accidentes, hh_trabajadas),
        'ig': estadisticas.indice_gravedad_con_cargo(dias_perdidos_totales, dias_cargo_totales, hh_trabajadas),
        'ta': estadisticas.tasa_accidentabilidad(n_accidentes, n_trabajadores),
    }
