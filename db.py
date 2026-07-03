"""Capa de datos de Smart HSE sobre SQLAlchemy (PostgreSQL en prod, SQLite local).

Conserva la misma API pública que la versión sqlite3 previa (mismos nombres y
firmas de función) para que `app.py` no cambie. Las funciones devuelven `dict`
(vía `Model.to_dict()`), igual que antes con `sqlite3.Row`.
"""
from datetime import date, timedelta

from sqlalchemy import inspect, text

import cumplimiento
from models import (sqla, Empresa, Contrato, Documento, ControlEstado, CarpetaEstado,
                    FufEstado, MappingReq, Trabajador, AuditoriaEstado,
                    Aplicabilidad, DocumentoGenerado, Usuario, Vocabulario,
                    ReglaCumplimiento, DialectoMandante, RequisitoLegal)


def _hoy():
    return date.today().isoformat()


def _commit():
    sqla.session.commit()


# ─────────────────────────────── Inicialización ───────────────────────────
def init_db():
    """Crea las tablas (auto-migración al desplegar) y siembra el mapping."""
    _reset_tablas_legacy()      # reestructuración destructiva (solo datos demo) antes de crear
    sqla.create_all()
    _migrar_columnas()
    seed_mapping()


# Columnas añadidas después del primer despliegue. create_all() NO altera tablas
# existentes, así que en Postgres de producción hay que agregarlas con ALTER.
# (tabla, columna, DDL de tipo). Idempotente y best-effort.
_COLUMNAS_NUEVAS = [
    ('contrato', 'es_contratista_minera', 'INTEGER DEFAULT 0'),  # Ronda 11 (Módulo Puente)
    ('usuario', 'rut', 'TEXT'),                                  # Ronda 11 (login por RUT)
    ('usuario', 'rut_raw', 'TEXT'),                              # Ronda 11
    ('contrato', 'empresa_id', 'INTEGER'),                       # Ronda 12 (contrato → empresa)
    ('documento', 'base_legal', 'TEXT'),                        # Ronda 12 (motor cumplimiento)
    ('documento', 'estado_cumplimiento', 'TEXT'),              # Ronda 12
]


def _reset_tablas_legacy():
    """Ronda 12: `fuf_estado` cambió su llave de (rut_asesor,item_n) a (empresa_id,item_n).
    create_all() no puede reescribir la restricción única de una tabla existente, así que si
    la tabla legada NO tiene `empresa_id`, se elimina para recrearla con el nuevo esquema.
    Es seguro: el avance FUF es dato demo que se re-responde por empresa (los datos se
    reinician, según lo acordado). Best-effort: nunca interrumpe el arranque."""
    try:
        insp = inspect(sqla.engine)
        if 'fuf_estado' not in set(insp.get_table_names()):
            return
        cols = {c['name'] for c in insp.get_columns('fuf_estado')}
        if 'empresa_id' not in cols:
            with sqla.engine.begin() as conn:
                conn.execute(text('DROP TABLE fuf_estado'))
    except Exception:
        pass


def _migrar_columnas():
    """Agrega columnas faltantes en tablas ya existentes (Postgres/SQLite).
    Best-effort: si la tabla no existe todavía (la crea create_all) o el motor
    rechaza el ALTER, no interrumpe el arranque."""
    insp = inspect(sqla.engine)
    try:
        tablas = set(insp.get_table_names())
    except Exception:
        return
    for tabla, col, ddl in _COLUMNAS_NUEVAS:
        if tabla not in tablas:
            continue
        try:
            existentes = {c['name'] for c in insp.get_columns(tabla)}
        except Exception:
            continue
        if col in existentes:
            continue
        try:
            with sqla.engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE {tabla} ADD COLUMN {col} {ddl}'))
        except Exception:
            pass  # otra instancia pudo haberla agregado; se ignora


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
    seed_vocabulario()
    seed_reglas()


def seed_reglas():
    """Siembra las Reglas de Cumplimiento y el Dialecto por mandante (Ronda 12)."""
    for categoria, r in cumplimiento.REGLAS_CUMPLIMIENTO.items():
        row = ReglaCumplimiento.query.filter_by(categoria=categoria).first()
        if not row:
            row = ReglaCumplimiento(categoria=categoria)
            sqla.session.add(row)
        row.titulo = r.get('titulo')
        row.base_legal = r.get('base_legal')
        row.periodicidad_meses = r.get('periodicidad_meses', 12)
        row.es_critico = 1 if r.get('es_critico') else 0
        row.fuf_item = r.get('fuf_item')
        if row.activo is None:
            row.activo = 1
    for mkey, cats in cumplimiento.DIALECTO_MANDANTE.items():
        for categoria, d in cats.items():
            row = DialectoMandante.query.filter_by(mandante_key=mkey, categoria=categoria).first()
            if not row:
                row = DialectoMandante(mandante_key=mkey, categoria=categoria)
                sqla.session.add(row)
            row.estandar = d.get('estandar')
            row.metodologia = d.get('metodologia')
    _commit()


# ── Vocabulario técnico (siglas mineras / términos de faena) ──
_VOCAB_SEED = [
    ('ECF', 'sigla', 'Estándar de Control de Fatalidades'),
    ('RESSO', 'sigla', 'Reglamento Especial para Empresas Contratistas y Subcontratistas (Codelco)'),
    ('IPER', 'sigla', 'Identificación de Peligros y Evaluación de Riesgos'),
    ('MIPER', 'sigla', 'Matriz de Identificación de Peligros y Evaluación de Riesgos'),
    ('EPP', 'sigla', 'Elementos de Protección Personal'),
    ('DRT', 'sigla', 'División Radomiro Tomic (Codelco)'),
    ('CPHS', 'sigla', 'Comité Paritario de Higiene y Seguridad'),
    ('PREXOR', 'sigla', 'Protocolo de Vigilancia de Riesgos por Exposición a Ruido'),
    ('SERNAGEOMIN', 'sigla', 'Servicio Nacional de Geología y Minería'),
    ('LOD', 'sigla', 'Lista de Obreros y Dotación'),
    ('ODI', 'sigla', 'Obligación de Informar los riesgos laborales'),
    ('RIOHS', 'sigla', 'Reglamento Interno de Orden, Higiene y Seguridad'),
    ('ART', 'sigla', 'Análisis de Riesgo del Trabajo'),
    ('IRL', 'sigla', 'Identificación de Requisitos Legales'),
    ('RC', 'sigla', 'Riesgo Crítico'),
    ('EST', 'sigla', 'Estándar'),
    ('EECC', 'sigla', 'Empresa Contratista'),
]


def seed_vocabulario():
    if Vocabulario.query.first():
        return
    for termino, tipo, significado in _VOCAB_SEED:
        sqla.session.add(Vocabulario(termino=termino, tipo=tipo, significado=significado,
                                     activo=1, creado=_hoy()))
    _commit()


def vocabulario_listar(solo_activos=True):
    q = Vocabulario.query
    if solo_activos:
        q = q.filter_by(activo=1)
    return [v.to_dict() for v in q.order_by(Vocabulario.termino).all()]


def vocabulario_crear(termino, tipo='termino', significado=''):
    termino = (termino or '').strip()
    if not termino:
        return None
    existente = Vocabulario.query.filter(sqla.func.lower(Vocabulario.termino) == termino.lower()).first()
    if existente:
        existente.tipo = tipo
        existente.significado = significado
        existente.activo = 1
        _commit()
        return existente.id
    v = Vocabulario(termino=termino, tipo=tipo, significado=significado, activo=1, creado=_hoy())
    sqla.session.add(v)
    _commit()
    return v.id


def vocabulario_eliminar(vid):
    Vocabulario.query.filter_by(id=vid).delete()
    _commit()


# ───────────────────────────── Contratos ──────────────────────────────────
# ─────────────────────────────── Empresas (Ronda 12) ──────────────────────
def crear_empresa(rut, razon_social, rut_empresa=None, mutual=None,
                  n_adherente=None, rubro=None, datos_json=None):
    e = Empresa(rut_asesor=rut, razon_social=razon_social, rut_empresa=rut_empresa,
                mutual=mutual, n_adherente=n_adherente, rubro=rubro,
                creado=_hoy(), datos_json=datos_json)
    sqla.session.add(e)
    _commit()
    return e.id


def empresas_de(rut):
    return [e.to_dict() for e in
            Empresa.query.filter_by(rut_asesor=rut).order_by(Empresa.id).all()]


def empresa_de(rut, empresa_id):
    e = Empresa.query.filter_by(id=empresa_id, rut_asesor=rut).first()
    return e.to_dict() if e else None


def set_empresa_datos(rut, empresa_id, datos_json):
    e = Empresa.query.filter_by(id=empresa_id, rut_asesor=rut).first()
    if e:
        e.datos_json = datos_json
        _commit()


def listar_contratos(rut, empresa_id=None):
    q = Contrato.query.filter_by(rut_asesor=rut)
    if empresa_id is not None:
        q = q.filter_by(empresa_id=empresa_id)
    return [c.to_dict() for c in q.order_by(Contrato.id).all()]


def crear_contrato(rut, empresa, faena, numero, mandante, datos_json=None,
                   es_contratista_minera=0, empresa_id=None):
    c = Contrato(rut_asesor=rut, empresa_id=empresa_id, empresa=empresa, faena=faena,
                 numero=numero, mandante=mandante, creado=_hoy(), datos_json=datos_json,
                 arranque_aprobado=0,
                 es_contratista_minera=1 if es_contratista_minera else 0)
    sqla.session.add(c)
    _commit()
    return c.id


def upgrade_a_contratista_minera(rut, contrato_id, mandante):
    """Módulo Puente: eleva una empresa general (0) a contratista minera (1)
    SIN borrar nada. Reutiliza el mismo registro `contrato` (razón social, RUT,
    rubro, N° trabajadores) y conserva evidencias, carpeta, auditoría y el avance
    FUF (que es del asesor). Solo fija el flag + mandante y deja el RESSO bloqueado
    hasta aprobar la Carpeta de Arranque. Devuelve el contrato actualizado o None."""
    c = Contrato.query.filter_by(id=contrato_id, rut_asesor=rut).first()
    if not c:
        return None
    c.es_contratista_minera = 1
    c.mandante = mandante
    if not c.resso_estado:
        c.resso_estado = 'bloqueado'
    _commit()
    return c.to_dict()


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


# ──────────────────── Estado FUF (DS 44) — base por empresa (Ronda 12) ─────
def set_fuf_estado(empresa_id, item_n, estado, observacion='', fecha_compromiso=None, rut=None):
    row = FufEstado.query.filter_by(empresa_id=empresa_id, item_n=item_n).first()
    if not row:
        row = FufEstado(empresa_id=empresa_id, item_n=item_n, rut_asesor=rut or '')
        sqla.session.add(row)
    if rut:
        row.rut_asesor = rut
    row.estado = estado
    row.observacion = observacion
    row.fecha_compromiso = fecha_compromiso
    row.fecha = _hoy()
    _commit()


def estados_fuf(empresa_id):
    return {r.item_n: r.to_dict()
            for r in FufEstado.query.filter_by(empresa_id=empresa_id).all()}


def set_fuf_compromiso(empresa_id, item_n, fecha_compromiso):
    row = FufEstado.query.filter_by(empresa_id=empresa_id, item_n=item_n).first()
    if row:
        row.fecha_compromiso = fecha_compromiso
        _commit()


# ──────────────────────────── Brechas (Carpeta + FUF) ─────────────────────
def brechas_carpeta(rut, empresa_id=None):
    """Ítems de Carpeta en estado 'pendiente' de los contratos del asesor
    (opcionalmente acotado a una empresa)."""
    q = (sqla.session.query(CarpetaEstado, Contrato)
         .join(Contrato, Contrato.id == CarpetaEstado.contrato_id)
         .filter(Contrato.rut_asesor == rut, CarpetaEstado.estado == 'pendiente'))
    if empresa_id is not None:
        q = q.filter(Contrato.empresa_id == empresa_id)
    rows = q.order_by(Contrato.id, CarpetaEstado.item_n).all()
    return [{'item_n': ce.item_n, 'observacion': ce.observacion,
             'fecha_compromiso': ce.fecha_compromiso, 'contrato_id': ct.id,
             'numero': ct.numero, 'empresa': ct.empresa, 'faena': ct.faena}
            for ce, ct in rows]


def brechas_fuf(empresa_id):
    """Ítems del FUF en estado 'no' (No Cumple) de la empresa."""
    return [{'item_n': r.item_n, 'observacion': r.observacion,
             'fecha_compromiso': r.fecha_compromiso}
            for r in FufEstado.query.filter_by(empresa_id=empresa_id, estado='no')
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
def usuario_get(rut_key):
    """Devuelve el usuario cuya llave (RUT normalizado) coincide, o None."""
    u = Usuario.query.filter_by(rut=rut_key).first()
    return u.to_dict() if u else None


def usuario_crear(rut_key, rut_raw, sns, nombre, rol='asesor', pass_hash=None):
    u = Usuario(rut=rut_key, rut_raw=rut_raw, sns=sns, nombre=nombre, rol=rol, pass_hash=pass_hash)
    sqla.session.add(u)
    _commit()
    return u.id


# ══════════════ Motor de Cumplimiento Inteligente (Ronda 12) ══════════════
def contrato_base(empresa_id, rut, razon_social=None):
    """Devuelve (creando si hace falta) el 'contrato base' de la empresa: contenedor de los
    documentos de la Capa Legal (FUF/DS 44) que luego se replican a los contratos mineros.
    Es un contrato no-minero con numero='BASE-<empresa_id>'."""
    numero = f'BASE-{empresa_id}'
    c = Contrato.query.filter_by(empresa_id=empresa_id, numero=numero).first()
    if c:
        return c.id
    return crear_contrato(rut, razon_social or 'Base legal', '', numero, '',
                          es_contratista_minera=0, empresa_id=empresa_id)


def regla_de(categoria):
    r = ReglaCumplimiento.query.filter_by(categoria=categoria).first()
    return r.to_dict() if r else None


def reglas_listar():
    return [r.to_dict() for r in
            ReglaCumplimiento.query.order_by(ReglaCumplimiento.es_critico.desc(),
                                             ReglaCumplimiento.categoria).all()]


def regla_actualizar(regla_id, periodicidad_meses=None, es_critico=None):
    r = ReglaCumplimiento.query.get(regla_id)
    if not r:
        return None
    if periodicidad_meses is not None:
        r.periodicidad_meses = int(periodicidad_meses)
    if es_critico is not None:
        r.es_critico = 1 if es_critico else 0
    _commit()
    return r.to_dict()


def dialecto_de(mandante_key, categoria):
    if not mandante_key:
        return None
    d = DialectoMandante.query.filter_by(mandante_key=mandante_key, categoria=categoria).first()
    return d.to_dict() if d else None


def registrar_documento_legal(contrato_id, categoria, nombre, fecha_aprobacion,
                              contenido=None, mimetype=None, version=None, flujo='DS44'):
    """Registra un documento maestro aplicando su regla de cumplimiento: fija periodicidad,
    fecha de vencimiento (desde la fecha de aprobación), base legal y estado. Devuelve el id."""
    regla = cumplimiento.REGLAS_CUMPLIMIENTO.get(categoria, {})
    periodicidad = regla.get('periodicidad_meses', 12)
    fecha_venc = cumplimiento.calcular_vencimiento(fecha_aprobacion, periodicidad)
    estado = cumplimiento.estado_cumplimiento(fecha_venc)
    doc_id = registrar_documento(
        contrato_id, nombre, flujo, 'evidencia', categoria=categoria, is_master=1,
        version=version, fecha_aprobacion=fecha_aprobacion, vigencia_meses=periodicidad,
        fecha_vencimiento=fecha_venc, contenido=contenido, mimetype=mimetype)
    d = Documento.query.get(doc_id)
    if d:
        d.base_legal = regla.get('base_legal')
        d.estado_cumplimiento = estado
        _commit()
    return doc_id


def cascada_a_contratos(empresa_id, categoria, master_doc_id):
    """Cascada / transitividad (Capa Core → Capa Mandante): refleja por referencia el doc
    maestro de la base FUF en cada contrato minero de la empresa que exige esa categoría, y
    marca su RequisitoLegal de capa mandante como 'auditado'. Devuelve la lista de contratos
    afectados (numero/mandante). No copia el archivo (usa ref_doc_id)."""
    master = Documento.query.get(master_doc_id)
    if not master:
        return []
    afectados = []
    for c in Contrato.query.filter_by(empresa_id=empresa_id, es_contratista_minera=1).all():
        # referencia simbólica en el contrato (si no existe ya una a este maestro)
        if not existe_referencia(c.id, master_doc_id):
            crear_doc_referencia(c.id, master.to_dict(), tipo='evidencia')
        # RequisitoLegal de capa mandante → auditado
        rq = RequisitoLegal.query.filter_by(empresa_id=empresa_id, categoria=categoria,
                                            capa='mandante').first()
        if rq:
            rq.estado_avance = 'auditado'
            rq.evidencia_doc_id = master_doc_id
        afectados.append({'contrato_id': c.id, 'numero': c.numero, 'mandante': c.mandante})
    _commit()
    return afectados


def doc_maestro_por_categoria_empresa(empresa_id, categoria):
    """Doc maestro (is_master=1) de una categoría entre los contratos de la empresa, o None.
    El maestro puede vivir en cualquier contrato de la empresa (la base es compartida)."""
    row = (sqla.session.query(Documento)
           .join(Contrato, Contrato.id == Documento.contrato_id)
           .filter(Contrato.empresa_id == empresa_id, Documento.categoria == categoria,
                   Documento.is_master == 1)
           .order_by(Documento.id.desc()).first())
    return row.to_dict() if row else None


def pendientes_legales(empresa_id):
    """Núcleo del panel: por cada categoría con regla, su doc maestro + estado recalculado +
    contratos mineros afectados (con dialecto por mandante) + ítem FUF. Lista priorizada."""
    contratos = Contrato.query.filter_by(empresa_id=empresa_id, es_contratista_minera=1).all()
    salida = []
    for cat, regla in cumplimiento.REGLAS_CUMPLIMIENTO.items():
        doc = doc_maestro_por_categoria_empresa(empresa_id, cat)
        if doc:
            estado = cumplimiento.estado_cumplimiento(doc.get('fecha_vencimiento'))
        else:
            estado = 'sin_documento'
        # contratos afectados + su dialecto
        afectados = []
        for c in contratos:
            mkey = cumplimiento.dialecto_key(c.mandante)
            dial = dialecto_de(mkey, cat) if mkey else None
            afectados.append({'contrato_id': c.id, 'numero': c.numero, 'mandante': c.mandante,
                              'dialecto_key': mkey,
                              'estandar': (dial or {}).get('estandar'),
                              'metodologia': (dial or {}).get('metodologia')})
        # solo interesa mostrar lo crítico/por vencer/vencido/sin documento
        if estado == 'vigente' and not regla.get('es_critico'):
            continue
        nombres_mand = ', '.join(sorted({a['mandante'] for a in afectados if a['mandante']})) or 'tu contrato'
        mensaje = (f"{regla.get('titulo')} — base legal {regla.get('base_legal')}. "
                   f"Al actualizar el documento, cubres tu obligación legal (DS 44) y tu exigencia "
                   f"contractual con {nombres_mand} simultáneamente.")
        salida.append({
            'categoria': cat, 'titulo': regla.get('titulo'),
            'base_legal': regla.get('base_legal'), 'es_critico': bool(regla.get('es_critico')),
            'fuf_item': regla.get('fuf_item'), 'estado': estado,
            'fecha_vencimiento': (doc or {}).get('fecha_vencimiento'),
            'doc_id': (doc or {}).get('id'), 'doc_nombre': (doc or {}).get('nombre'),
            'contratos': afectados, 'mensaje': mensaje,
        })
    orden = {'pendiente_actualizacion': 0, 'por_vencer': 1, 'sin_documento': 2, 'vigente': 3}
    salida.sort(key=lambda x: (orden.get(x['estado'], 9), not x['es_critico']))
    return salida


# ── Matriz Legal por capas (RequisitoLegal) ──
def matriz_legal(empresa_id):
    return [r.to_dict() for r in
            RequisitoLegal.query.filter_by(empresa_id=empresa_id)
            .order_by(RequisitoLegal.capa, RequisitoLegal.id_requisito).all()]


def requisito_guardar(empresa_id, data):
    """Alta/edición de una fila de la Matriz Legal (por (empresa_id, id_requisito))."""
    idr = (data.get('id_requisito') or '').strip() or None
    row = None
    if idr:
        row = RequisitoLegal.query.filter_by(empresa_id=empresa_id, id_requisito=idr).first()
    if not row:
        row = RequisitoLegal(empresa_id=empresa_id, id_requisito=idr)
        sqla.session.add(row)
    for k in ('capa', 'origen', 'cuerpo_normativo', 'requisito_legal', 'riesgo_asociado',
              'control_operativo', 'responsable', 'frecuencia', 'estado_avance', 'categoria'):
        if k in data and data[k] is not None:
            setattr(row, k, data[k])
    row.fecha = _hoy()
    _commit()
    return row.to_dict()
