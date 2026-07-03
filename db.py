"""Capa de datos de Smart HSE sobre SQLAlchemy (PostgreSQL en prod, SQLite local).

Conserva la misma API pública que la versión sqlite3 previa (mismos nombres y
firmas de función) para que `app.py` no cambie. Las funciones devuelven `dict`
(vía `Model.to_dict()`), igual que antes con `sqlite3.Row`.
"""
from datetime import date, timedelta

from models import (sqla, Contrato, Documento, ControlEstado, CarpetaEstado,
                    FufEstado, MappingReq, Trabajador, AuditoriaEstado,
                    Aplicabilidad, DocumentoGenerado, Usuario)


def _hoy():
    return date.today().isoformat()


def _commit():
    sqla.session.commit()


# ─────────────────────────────── Inicialización ───────────────────────────
def init_db():
    """Crea las tablas (auto-migración al desplegar) y siembra el mapping."""
    sqla.create_all()
    seed_mapping()


def seed_mapping():
    """Siembra mapping_req desde el catálogo canónico (resso.EQUIVALENCIAS)."""
    import resso
    for categoria, m in resso.EQUIVALENCIAS.items():
        row = MappingReq.query.filter_by(categoria=categoria).first()
        if not row:
            row = MappingReq(categoria=categoria)
            sqla.session.add(row)
        row.arranque_item_n = m.get('carpeta')
        row.reso_codigo = m.get('reso')
    _commit()


# ───────────────────────────── Contratos ──────────────────────────────────
def listar_contratos(rut):
    return [c.to_dict() for c in
            Contrato.query.filter_by(rut_asesor=rut).order_by(Contrato.id).all()]


def crear_contrato(rut, empresa, faena, numero, mandante, datos_json=None):
    c = Contrato(rut_asesor=rut, empresa=empresa, faena=faena, numero=numero,
                 mandante=mandante, creado=_hoy(), datos_json=datos_json,
                 arranque_aprobado=0)
    sqla.session.add(c)
    _commit()
    return c.id


def actualizar_datos(contrato_id, datos_json):
    c = Contrato.query.get(contrato_id)
    if c:
        c.datos_json = datos_json
        _commit()


def eliminar_contrato(rut, contrato_id):
    c = Contrato.query.filter_by(id=contrato_id, rut_asesor=rut).first()
    if not c:
        return
    for M in (ControlEstado, CarpetaEstado, AuditoriaEstado, Aplicabilidad,
              Trabajador, Documento, DocumentoGenerado):
        M.query.filter_by(contrato_id=contrato_id).delete()
    Contrato.query.filter_by(id=contrato_id, rut_asesor=rut).delete()
    _commit()


def contrato_de(rut, contrato_id):
    c = Contrato.query.filter_by(id=contrato_id, rut_asesor=rut).first()
    return c.to_dict() if c else None


# ───────────────────────────── Documentos ─────────────────────────────────
def registrar_documento(contrato_id, nombre, flujo, tipo, item_n=None,
                        categoria=None, is_master=0, ref_doc_id=None,
                        version=None, fecha_aprobacion=None, firma=None,
                        vigencia_meses=None, fecha_vencimiento=None,
                        contenido=None, mimetype=None):
    """Inserta un documento (o una referencia si ref_doc_id) y devuelve su id.
    Si `contenido` viene, se guarda el archivo como BLOB en la base."""
    d = Documento(contrato_id=contrato_id, nombre=nombre, flujo=flujo, tipo=tipo,
                  fecha=_hoy(), item_n=item_n, categoria=categoria,
                  is_master=is_master, ref_doc_id=ref_doc_id, version=version,
                  fecha_aprobacion=fecha_aprobacion, firma=firma,
                  vigencia_meses=vigencia_meses, fecha_vencimiento=fecha_vencimiento,
                  contenido=contenido, mimetype=mimetype)
    sqla.session.add(d)
    _commit()
    return d.id


def documentos_de(contrato_id):
    return [d.to_dict() for d in
            Documento.query.filter_by(contrato_id=contrato_id)
            .order_by(Documento.id.desc()).all()]


def documento_por_id(rut, doc_id):
    """Documento + validación de pertenencia al asesor (join contrato por rut)."""
    d = (Documento.query.join(Contrato, Contrato.id == Documento.contrato_id)
         .filter(Documento.id == doc_id, Contrato.rut_asesor == rut).first())
    return d.to_dict() if d else None


def documento_contenido(rut, doc_id):
    """Devuelve (bytes, mimetype, nombre) del archivo, resolviendo referencias
    (ref_doc_id) al documento maestro. None si no existe o no pertenece al asesor."""
    d = (Documento.query.join(Contrato, Contrato.id == Documento.contrato_id)
         .filter(Documento.id == doc_id, Contrato.rut_asesor == rut).first())
    if not d:
        return None
    if d.contenido is None and d.ref_doc_id:
        base = Documento.query.get(d.ref_doc_id)
        if base and base.contenido is not None:
            return (base.contenido, base.mimetype, base.nombre)
    if d.contenido is None:
        return None
    return (d.contenido, d.mimetype, d.nombre)


def set_doc_maestro(doc_id, categoria=None):
    d = Documento.query.get(doc_id)
    if not d:
        return
    d.is_master = 1
    if categoria:
        d.categoria = categoria
    _commit()


def docs_por_categoria(contrato_id, categoria):
    return [d.to_dict() for d in
            Documento.query.filter_by(contrato_id=contrato_id, categoria=categoria)
            .order_by(Documento.id.desc()).all()]


def doc_maestro_de_categoria(rut, categoria):
    """Documento maestro (is_master=1) de una categoría para el asesor, o None."""
    row = (sqla.session.query(Documento, Contrato.numero)
           .join(Contrato, Contrato.id == Documento.contrato_id)
           .filter(Contrato.rut_asesor == rut, Documento.categoria == categoria,
                   Documento.is_master == 1)
           .order_by(Documento.id.desc()).first())
    if not row:
        return None
    d, numero = row
    return {**d.to_dict(), 'contrato_numero': numero}


def crear_doc_referencia(target_cid, master, tipo='matriz'):
    """Crea una referencia simbólica al doc maestro en el contrato destino (sin copiar archivo)."""
    return registrar_documento(
        target_cid, master['nombre'], master.get('flujo', ''), tipo,
        item_n=master.get('item_n'), categoria=master.get('categoria'),
        is_master=0, ref_doc_id=master['id'],
        version=master.get('version'), fecha_aprobacion=master.get('fecha_aprobacion'),
        firma=master.get('firma'))


def existe_referencia(target_cid, master_id):
    return Documento.query.filter_by(contrato_id=target_cid, ref_doc_id=master_id).first() is not None


def mapping_de(categoria):
    r = MappingReq.query.filter_by(categoria=categoria).first()
    return r.to_dict() if r else None


def maestros_vencidos(rut, dias_aviso=30):
    """Documentos maestros vencidos o próximos a vencer, del asesor."""
    limite = (date.today() + timedelta(days=dias_aviso)).isoformat()
    rows = (sqla.session.query(Documento, Contrato.numero)
            .join(Contrato, Contrato.id == Documento.contrato_id)
            .filter(Contrato.rut_asesor == rut, Documento.is_master == 1,
                    Documento.fecha_vencimiento.isnot(None),
                    Documento.fecha_vencimiento <= limite)
            .order_by(Documento.fecha_vencimiento).all())
    return [{**d.to_dict(), 'contrato_numero': numero} for d, numero in rows]


def referencias_de(master_id):
    """Docs hijos (auditorías vinculadas) que referencian a un maestro."""
    return [d.to_dict() for d in Documento.query.filter_by(ref_doc_id=master_id).all()]


# ── Contrato: hito de arranque / estado RESSO ──
def set_arranque_aprobado(contrato_id, resso_estado='en_progreso'):
    c = Contrato.query.get(contrato_id)
    if c:
        c.arranque_aprobado = 1
        c.resso_estado = resso_estado
        _commit()


def set_resso_estado(contrato_id, estado):
    c = Contrato.query.get(contrato_id)
    if c:
        c.resso_estado = estado
        _commit()


# ── Auditoría RESSO (estado por punto) ──
def set_auditoria_estado(contrato_id, punto_key, estado, observacion='', fecha_compromiso=None):
    row = AuditoriaEstado.query.filter_by(contrato_id=contrato_id, punto_key=punto_key).first()
    if not row:
        row = AuditoriaEstado(contrato_id=contrato_id, punto_key=punto_key)
        sqla.session.add(row)
    row.estado = estado
    row.observacion = observacion
    row.fecha_compromiso = fecha_compromiso
    row.fecha = _hoy()
    _commit()


def estados_auditoria(contrato_id):
    return {r.punto_key: r.to_dict()
            for r in AuditoriaEstado.query.filter_by(contrato_id=contrato_id).all()}


# ──────────────────────────── Carpeta de Arranque ─────────────────────────
def set_item_estado(contrato_id, item_n, estado, observacion='', fecha_compromiso=None):
    row = CarpetaEstado.query.filter_by(contrato_id=contrato_id, item_n=item_n).first()
    if not row:
        row = CarpetaEstado(contrato_id=contrato_id, item_n=item_n)
        sqla.session.add(row)
    row.estado = estado
    row.observacion = observacion
    row.fecha_compromiso = fecha_compromiso
    row.fecha = _hoy()
    _commit()


def estados_carpeta(contrato_id):
    return {r.item_n: r.to_dict()
            for r in CarpetaEstado.query.filter_by(contrato_id=contrato_id).all()}


def eliminar_doc_tipo(contrato_id, item_n, tipo):
    Documento.query.filter_by(contrato_id=contrato_id, item_n=item_n, tipo=tipo).delete()
    _commit()


def docs_por_item(contrato_id):
    out = {}
    for d in (Documento.query.filter(Documento.contrato_id == contrato_id,
                                     Documento.item_n.isnot(None))
              .order_by(Documento.id.desc()).all()):
        out.setdefault(d.item_n, []).append(d.to_dict())
    return out


def set_carpeta_compromiso(contrato_id, item_n, fecha_compromiso):
    row = CarpetaEstado.query.filter_by(contrato_id=contrato_id, item_n=item_n).first()
    if row:
        row.fecha_compromiso = fecha_compromiso
        _commit()


# ──────────────────────────── Estado FUF (DS 44) ──────────────────────────
def set_fuf_estado(rut, item_n, estado, observacion='', fecha_compromiso=None):
    row = FufEstado.query.filter_by(rut_asesor=rut, item_n=item_n).first()
    if not row:
        row = FufEstado(rut_asesor=rut, item_n=item_n)
        sqla.session.add(row)
    row.estado = estado
    row.observacion = observacion
    row.fecha_compromiso = fecha_compromiso
    row.fecha = _hoy()
    _commit()


def estados_fuf(rut):
    return {r.item_n: r.to_dict()
            for r in FufEstado.query.filter_by(rut_asesor=rut).all()}


def set_fuf_compromiso(rut, item_n, fecha_compromiso):
    row = FufEstado.query.filter_by(rut_asesor=rut, item_n=item_n).first()
    if row:
        row.fecha_compromiso = fecha_compromiso
        _commit()


# ──────────────────────────── Brechas (Carpeta + FUF) ─────────────────────
def brechas_carpeta(rut):
    """Ítems de Carpeta en estado 'pendiente' de todos los contratos del asesor."""
    rows = (sqla.session.query(CarpetaEstado, Contrato)
            .join(Contrato, Contrato.id == CarpetaEstado.contrato_id)
            .filter(Contrato.rut_asesor == rut, CarpetaEstado.estado == 'pendiente')
            .order_by(Contrato.id, CarpetaEstado.item_n).all())
    return [{'item_n': ce.item_n, 'observacion': ce.observacion,
             'fecha_compromiso': ce.fecha_compromiso, 'contrato_id': ct.id,
             'numero': ct.numero, 'empresa': ct.empresa, 'faena': ct.faena}
            for ce, ct in rows]


def brechas_fuf(rut):
    """Ítems del FUF en estado 'no' (No Cumple) del asesor."""
    return [{'item_n': r.item_n, 'observacion': r.observacion,
             'fecha_compromiso': r.fecha_compromiso}
            for r in FufEstado.query.filter_by(rut_asesor=rut, estado='no')
            .order_by(FufEstado.item_n).all()]


# ──────────────────────────── Estados de control ──────────────────────────
def set_estado_control(rut, contrato_id, control_key, estado, origen_contrato_id=None):
    """Inserta o actualiza el estado de un control para un contrato."""
    row = ControlEstado.query.filter_by(contrato_id=contrato_id, control_key=control_key).first()
    if not row:
        row = ControlEstado(contrato_id=contrato_id, control_key=control_key, rut_asesor=rut)
        sqla.session.add(row)
    row.rut_asesor = rut
    row.estado = estado
    row.origen_contrato_id = origen_contrato_id
    row.fecha = _hoy()
    _commit()


def estado_control(contrato_id, control_key):
    r = ControlEstado.query.filter_by(contrato_id=contrato_id, control_key=control_key).first()
    return r.estado if r else None


def estados_de_contrato(contrato_id):
    return {r.control_key: r.to_dict()
            for r in ControlEstado.query.filter_by(contrato_id=contrato_id).all()}


# ─────────────────────────────── Usuarios (Postgres) ──────────────────────
def usuario_get(sns_key):
    u = Usuario.query.filter_by(sns=sns_key).first()
    return u.to_dict() if u else None


def usuario_crear(sns_key, sns_raw, nombre, rol='asesor', pass_hash=None):
    u = Usuario(sns=sns_key, sns_raw=sns_raw, nombre=nombre, rol=rol, pass_hash=pass_hash)
    sqla.session.add(u)
    _commit()
    return u.id


def usuario_set_empresa(sns_key, empresa_json):
    u = Usuario.query.filter_by(sns=sns_key).first()
    if u:
        u.empresa_json = empresa_json
        _commit()
