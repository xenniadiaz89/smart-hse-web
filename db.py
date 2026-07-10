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
                    ReglaCumplimiento, DialectoMandante, RequisitoLegal,
                    FuenteLegal, ValidacionCumplimiento, MatrizRiesgo, RiesgoItem,
                    TareaIPER, EPP, PTS, TareaEPP, TareaPTS, TrabajadorTarea, IRLGenerado,
                    BibliotecaTarea, Vehiculo, ChecklistVehiculo)
import iper


def _hoy():
    return date.today().isoformat()


def _commit():
    sqla.session.commit()


# ─────────────────────────────── Inicialización ───────────────────────────
def init_db():
    """Crea las tablas y aplica SOLO migraciones ADITIVAS (cero pérdida de datos, Ronda 21).
    Ya no se ejecuta ninguna operación destructiva en el arranque: no se borran tablas ni datos
    de usuarios, empresas, avances ni documentos. Todo persiste en Postgres entre reinicios."""
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
    # Ronda 13 — Matriz Legal: fuente legal + detalle normativo + trazabilidad
    ('requisito_legal', 'fuente_legal_id', 'INTEGER'),
    ('requisito_legal', 'articulo', 'TEXT'),
    ('requisito_legal', 'obligacion', 'TEXT'),
    ('requisito_legal', 'frecuencia_actualizacion_meses', 'INTEGER'),
    ('requisito_legal', 'fecha_actualizacion', 'TEXT'),
    ('requisito_legal', 'validado_por', 'TEXT'),
    ('requisito_legal', 'validado_en', 'TEXT'),
    # Ronda 15 — Motor documental IRL
    ('riesgo_item', 'tarea_id', 'INTEGER'),
    ('trabajador', 'empresa_id', 'INTEGER'),
    ('trabajador', 'cargo', 'TEXT'),
    # Ronda 16 — Matriz Legal doble capa + logo por empresa
    ('requisito_legal', 'is_mandatory', 'INTEGER DEFAULT 0'),
    ('requisito_legal', 'evidencia_notas', 'TEXT'),
    ('requisito_legal', 'fecha_vencimiento', 'TEXT'),
    ('empresa', 'logo_doc_id', 'INTEGER'),
    # Ronda 17 — MIPER VEP + método + capa minera + re-firma IRL
    ('riesgo_item', 'vep', 'INTEGER'),
    ('riesgo_item', 'metodo_correcto', 'TEXT'),
    ('riesgo_item', 'contrato_id', 'INTEGER'),
    ('riesgo_item', 'ecf_punto', 'TEXT'),
    ('riesgo_item', 'mfl', 'TEXT'),
    ('riesgo_item', 'bowtie', 'TEXT'),
    ('irl_generado', 'requiere_refirma', 'INTEGER DEFAULT 0'),
    ('irl_generado', 'motivo_actualizacion', 'TEXT'),
    # Ronda 18 Fase 2 — capa legal por contrato/faena
    ('requisito_legal', 'contrato_id', 'INTEGER'),
]


def empresa_set_logo(empresa_id, doc_id):
    e = Empresa.query.get(empresa_id)
    if e:
        e.logo_doc_id = doc_id
        _commit()


def _reset_tablas_legacy():
    """DESACTIVADA (Ronda 21 — cero pérdida de datos).
    Antes eliminaba `fuf_estado` si le faltaba `empresa_id` (migración de la Ronda 12, ya aplicada
    en producción). Se conserva como no-op para no volver a introducir ninguna operación
    destructiva en el arranque. El arranque solo hace migraciones ADITIVAS."""
    return


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
    seed_fuentes_legales()


def seed_fuentes_legales():
    """Siembra las fuentes legales vigentes (Ronda 13). Idempotente."""
    for f in cumplimiento.FUENTES_LEGALES:
        row = FuenteLegal.query.filter_by(codigo=f['codigo']).first()
        if not row:
            row = FuenteLegal(codigo=f['codigo'])
            sqla.session.add(row)
        row.nombre = f['nombre']
        row.url = f.get('url')
        if row.vigente is None:
            row.vigente = 1
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
    seed_requisitos_core(e.id)          # Ronda 16: precarga la Capa Core (obligatoria)
    return e.id


def seed_requisitos_core(empresa_id):
    """Inyecta los requisitos legales transversales VIGENTES (is_mandatory=1) al crear la
    empresa. Idempotente: no duplica si ya existen."""
    for r in cumplimiento.REQUISITOS_CORE:
        if RequisitoLegal.query.filter_by(empresa_id=empresa_id, id_requisito=r['id_requisito']).first():
            continue
        sqla.session.add(RequisitoLegal(
            empresa_id=empresa_id, id_requisito=r['id_requisito'], capa='core',
            is_mandatory=1, origen=r.get('origen'), cuerpo_normativo=r.get('cuerpo_legal'),
            requisito_legal=r.get('requisito'), estado_avance='pendiente',
            frecuencia_actualizacion_meses=r.get('frecuencia_actualizacion_meses'),
            fecha=_hoy()))
    _commit()


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


def _empresa_datos_dict(empresa_id):
    import json as _json
    e = Empresa.query.get(empresa_id)
    if not e:
        return None, {}
    try:
        d = _json.loads(e.datos_json) if e.datos_json else {}
    except (TypeError, ValueError):
        d = {}
    return e, d


def seguimiento_get(empresa_id):
    """Dict {categoria: {comentario, fecha_compromiso}} de seguimiento de docs anuales."""
    _e, d = _empresa_datos_dict(empresa_id)
    return d.get('seguimiento', {}) if d else {}


def seguimiento_set(empresa_id, categoria, comentario=None, fecha_compromiso=None):
    import json as _json
    e, d = _empresa_datos_dict(empresa_id)
    if not e:
        return None
    seg = d.get('seguimiento', {})
    seg[categoria] = {'comentario': comentario or '', 'fecha_compromiso': fecha_compromiso or '',
                      'fecha': _hoy()}
    d['seguimiento'] = seg
    e.datos_json = _json.dumps(d, ensure_ascii=False)
    _commit()
    return seg[categoria]


# ── Adhesión a Mutualidad (Ley 16.744) — Ronda 18 ──
_ADHESION_TIPOS = ('adhesion', 'siniestralidad', 'cotizaciones')


def adhesion_estado(rut, empresa_id):
    """Estado de la adhesión: mutual, N° adherente y los 3 certificados (doc_ids), + si CUMPLE."""
    emp = empresa_de(rut, empresa_id) or {}
    _e, d = _empresa_datos_dict(empresa_id)
    docs = (d or {}).get('adhesion_docs', {})
    completo = bool(emp.get('mutual')) and bool(emp.get('n_adherente')) and \
        all(docs.get(t) for t in _ADHESION_TIPOS)
    return {'mutual': emp.get('mutual'), 'n_adherente': emp.get('n_adherente'),
            'docs': {t: docs.get(t) for t in _ADHESION_TIPOS}, 'cumple': completo}


def adhesion_guardar(rut, empresa_id, mutual=None, n_adherente=None):
    e = Empresa.query.filter_by(id=empresa_id, rut_asesor=rut).first()
    if not e:
        return None
    if mutual is not None:
        e.mutual = mutual
    if n_adherente is not None:
        e.n_adherente = n_adherente
    _commit()
    _core01_auto_cumple(empresa_id)
    return adhesion_estado(rut, empresa_id)


def adhesion_set_doc(empresa_id, tipo, doc_id):
    import json as _json
    e, d = _empresa_datos_dict(empresa_id)
    if not e or tipo not in _ADHESION_TIPOS:
        return
    docs = d.get('adhesion_docs', {})
    docs[tipo] = doc_id
    d['adhesion_docs'] = docs
    e.datos_json = _json.dumps(d, ensure_ascii=False)
    _commit()
    _core01_auto_cumple(empresa_id)


def _core01_auto_cumple(empresa_id):
    """Si la adhesión está completa (mutual + N° adherente + 3 certificados), marca el ítem
    CORE-01 de la Matriz Legal como Cumple/Auditado con la evidencia correspondiente."""
    e = Empresa.query.get(empresa_id)
    if not e:
        return
    _e2, d = _empresa_datos_dict(empresa_id)
    docs = (d or {}).get('adhesion_docs', {})
    completo = bool(e.mutual) and bool(e.n_adherente) and all(docs.get(t) for t in _ADHESION_TIPOS)
    row = RequisitoLegal.query.filter_by(empresa_id=empresa_id, id_requisito='CORE-01').first()
    if not row:
        return
    if completo:
        row.estado_avance = 'auditado'
        row.evidencia_notas = (f'Adhesión a {e.mutual}, N° adherente {e.n_adherente}. '
                               'Certificados de Adhesión, Siniestralidad y Cotizaciones cargados.')
        row.fecha_actualizacion = _hoy()
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
    """Matriz Legal TRANSVERSAL de la empresa (requisitos sin contrato: Core + Operativa)."""
    return [r.to_dict() for r in
            RequisitoLegal.query.filter_by(empresa_id=empresa_id, contrato_id=None)
            .order_by(RequisitoLegal.capa, RequisitoLegal.id_requisito).all()]


def matriz_legal_contrato(empresa_id, contrato_id):
    """Requisitos legales de la capa mandante ligados a un contrato/faena."""
    return [r.to_dict() for r in
            RequisitoLegal.query.filter_by(empresa_id=empresa_id, contrato_id=contrato_id)
            .order_by(RequisitoLegal.id_requisito).all()]


# Campos siempre editables (también en filas Core); el resto queda bloqueado en Core.
_MATRIZ_CAMPOS_GESTION = ('estado_avance', 'evidencia_notas', 'responsable',
                          'fecha_vencimiento', 'fecha_actualizacion')
_MATRIZ_CAMPOS_DEF = ('capa', 'origen', 'cuerpo_normativo', 'requisito_legal', 'obligacion',
                      'riesgo_asociado', 'control_operativo', 'frecuencia', 'categoria',
                      'fuente_legal_id', 'articulo', 'frecuencia_actualizacion_meses', 'contrato_id')


def requisito_guardar(empresa_id, data):
    """Alta/edición de una fila de la Matriz Legal (por (empresa_id, id_requisito)).
    En filas Core (is_mandatory=1) solo se aceptan los campos de gestión; el Requisito y el
    Cuerpo_Legal quedan bloqueados."""
    idr = (data.get('id_requisito') or '').strip() or None
    row = None
    if idr:
        row = RequisitoLegal.query.filter_by(empresa_id=empresa_id, id_requisito=idr).first()
    nueva = row is None
    if nueva:
        row = RequisitoLegal(empresa_id=empresa_id, id_requisito=idr, is_mandatory=0)
        sqla.session.add(row)
    es_core = bool(row.is_mandatory) and not nueva
    campos = _MATRIZ_CAMPOS_GESTION if es_core else (_MATRIZ_CAMPOS_DEF + _MATRIZ_CAMPOS_GESTION)
    for k in campos:
        if k in data and data[k] is not None:
            setattr(row, k, data[k])
    row.fecha = _hoy()
    _commit()
    return row.to_dict()


def requisito_eliminar(empresa_id, requisito_id):
    """Elimina una fila operativa. Las filas Core (is_mandatory=1) NO se pueden borrar."""
    row = RequisitoLegal.query.filter_by(id=requisito_id, empresa_id=empresa_id).first()
    if not row:
        return {'error': 'Requisito no encontrado.'}
    if row.is_mandatory:
        return {'error': 'Los requisitos obligatorios (Core) no se pueden eliminar.'}
    sqla.session.delete(row)
    _commit()
    return {'ok': True}


# ══════════════ Ronda 13 — Pilares SGSST: Matriz Legal + Matriz de Riesgos ══════════════
from datetime import datetime as _dt


def fuentes_legales():
    return [f.to_dict() for f in FuenteLegal.query.order_by(FuenteLegal.codigo).all()]


def fuente_legal_de(codigo):
    f = FuenteLegal.query.filter_by(codigo=codigo).first()
    return f.to_dict() if f else None


def set_fuente_vigencia(codigo, vigente):
    """Marca una ley como vigente/derogada. Al derogarla, sus requisitos entran en alerta."""
    f = FuenteLegal.query.filter_by(codigo=codigo).first()
    if f:
        f.vigente = 1 if vigente else 0
        _commit()
    return f.to_dict() if f else None


# ── Trazabilidad auditable de la Matriz Legal ──
def validar_requisito(requisito_id, validado_por, estado='cumple', comentario=''):
    """Registra una validación auditable (quién/cuándo) y actualiza el snapshot del requisito."""
    req = RequisitoLegal.query.get(requisito_id)
    if not req:
        return None
    ahora = _dt.now().isoformat(timespec='seconds')
    sqla.session.add(ValidacionCumplimiento(
        requisito_id=requisito_id, validado_por=validado_por, validado_en=ahora,
        estado=estado, comentario=comentario))
    req.validado_por = validado_por
    req.validado_en = ahora
    req.estado_avance = 'auditado' if estado == 'cumple' else estado
    _commit()
    return req.to_dict()


def validaciones_de(requisito_id):
    return [v.to_dict() for v in
            ValidacionCumplimiento.query.filter_by(requisito_id=requisito_id)
            .order_by(ValidacionCumplimiento.id.desc()).all()]


def requisito_alerta(req):
    """True si el requisito está desactualizado: venció su frecuencia de actualización o su
    fuente legal dejó de estar vigente. `req` puede ser dict o id."""
    if isinstance(req, int):
        r = RequisitoLegal.query.get(req)
        req = r.to_dict() if r else {}
    # (a) fuente legal derogada/modificada
    fid = req.get('fuente_legal_id')
    if fid:
        f = FuenteLegal.query.get(fid)
        if f and not f.vigente:
            return True
    # (b) vencimiento por frecuencia de actualización
    venc = cumplimiento.calcular_vencimiento(req.get('fecha_actualizacion'),
                                             req.get('frecuencia_actualizacion_meses'))
    return cumplimiento.estado_cumplimiento(venc) == 'pendiente_actualizacion'


# ── Matriz de Riesgos (IPER) con versionado ──
def matriz_riesgo_vigente(empresa_id):
    m = MatrizRiesgo.query.filter_by(empresa_id=empresa_id, estado='vigente').first()
    return m.to_dict() if m else None


def crear_matriz_riesgo(empresa_id, creado_por=None):
    """Crea (o devuelve) la matriz de riesgos vigente de la empresa (versión 1). Al crearla,
    precarga el catálogo base transversal DS 44 (Ronda 17)."""
    existente = MatrizRiesgo.query.filter_by(empresa_id=empresa_id, estado='vigente').first()
    if existente:
        return existente.id
    m = MatrizRiesgo(empresa_id=empresa_id, version=1, estado='vigente',
                     creado_por=creado_por, creado_en=_hoy())
    sqla.session.add(m)
    _commit()
    seed_tareas_base(m.id, empresa_id)
    return m.id


def seed_tareas_base(matriz_id, empresa_id):
    """Precarga las tareas/riesgos transversales del catálogo base (iper.CATALOGO_TAREAS_BASE)."""
    if TareaIPER.query.filter_by(matriz_id=matriz_id).first():
        return                       # ya sembrada
    for t in iper.CATALOGO_TAREAS_BASE:
        tid = tarea_crear(matriz_id, t['tarea'], proceso=t.get('proceso'), rutinaria='rutinaria')
        for r in t.get('riesgos', []):
            rid = riesgo_agregar(matriz_id, r['peligro'], r['riesgo'], r['medida_control'],
                                 probabilidad=r.get('probabilidad'), consecuencia=r.get('consecuencia'),
                                 metodo_correcto=r.get('metodo_correcto'))
            it = RiesgoItem.query.get(rid)
            if it:
                it.tarea_id = tid
    _commit()


def _aplicar_vep(it, probabilidad, consecuencia):
    """Calcula VEP y magnitud (Guía ISP 3, 3×3) y los asigna al ítem."""
    if probabilidad is None or consecuencia is None:
        return
    ev = iper.calcular_vep(probabilidad, consecuencia)
    it.probabilidad = ev['probabilidad']
    it.consecuencia = ev['consecuencia']
    it.vep = ev['vep']
    it.nivel_riesgo = ev['magnitud']


def riesgo_agregar(matriz_id, peligro, riesgo, medida_control, probabilidad=None,
                   consecuencia=None, nivel_riesgo=None, tipo_control=None, mandante_key=None,
                   es_critico=0, requisito_legal_id=None, evidencia_doc_id=None,
                   metodo_correcto=None, contrato_id=None, ecf_punto=None, mfl=None, bowtie=None):
    it = RiesgoItem(matriz_id=matriz_id, peligro=peligro, riesgo=riesgo,
                    medida_control=medida_control, tipo_control=tipo_control,
                    metodo_correcto=metodo_correcto, mandante_key=mandante_key,
                    es_critico=1 if es_critico else 0, requisito_legal_id=requisito_legal_id,
                    evidencia_doc_id=evidencia_doc_id, contrato_id=contrato_id,
                    ecf_punto=ecf_punto, mfl=mfl, bowtie=bowtie,
                    estado_control='vigente', fecha=_hoy())
    _aplicar_vep(it, probabilidad, consecuencia)
    if nivel_riesgo and it.nivel_riesgo is None:
        it.nivel_riesgo = nivel_riesgo
    sqla.session.add(it)
    _commit()
    return it.id


def riesgo_items(matriz_id):
    return [i.to_dict() for i in
            RiesgoItem.query.filter_by(matriz_id=matriz_id).order_by(RiesgoItem.id).all()]


# Campos editables en línea del ítem de riesgo (recalcula VEP si cambian P/C).
_RIESGO_CAMPOS = ('peligro', 'riesgo', 'medida_control', 'metodo_correcto', 'tipo_control',
                  'probabilidad', 'consecuencia', 'es_critico', 'contrato_id',
                  'ecf_punto', 'mfl', 'bowtie')
# Cambios en estos campos disparan la cascada al IRL (Art. 15 DS 44).
_RIESGO_CAMPOS_IRL = ('medida_control', 'metodo_correcto', 'riesgo', 'peligro')


def riesgo_editar(item_id, campo, valor):
    """Edita un campo del ítem de riesgo. Devuelve (dict, afecta_irl:bool)."""
    it = RiesgoItem.query.get(item_id)
    if not it or campo not in _RIESGO_CAMPOS:
        return None, False
    if campo in ('probabilidad', 'consecuencia'):
        try:
            v = int(valor)
        except (TypeError, ValueError):
            return it.to_dict(), False
        p = v if campo == 'probabilidad' else it.probabilidad
        c = v if campo == 'consecuencia' else it.consecuencia
        _aplicar_vep(it, p if p is not None else v, c if c is not None else v)
    elif campo == 'es_critico':
        it.es_critico = 1 if str(valor) in ('1', 'true', 'True', 'si') else 0
    else:
        setattr(it, campo, valor)
    it.fecha = _hoy()
    _commit()
    return it.to_dict(), (campo in _RIESGO_CAMPOS_IRL)


def trabajadores_de_tarea(tarea_id):
    """Trabajadores asignados a una tarea (para la cascada IRL)."""
    rows = (sqla.session.query(Trabajador)
            .join(TrabajadorTarea, TrabajadorTarea.trabajador_id == Trabajador.id)
            .filter(TrabajadorTarea.tarea_id == tarea_id).all())
    return [t.to_dict() for t in rows]


def contrato_es_minero(contrato_id):
    if not contrato_id:
        return False
    c = Contrato.query.get(contrato_id)
    return bool(c and c.es_contratista_minera)


# ── Vínculo bidireccional Legal ↔ Riesgos (Ronda 18) ──
def requisito_por_idreq(empresa_id, id_requisito):
    r = RequisitoLegal.query.filter_by(empresa_id=empresa_id, id_requisito=id_requisito).first()
    return r.to_dict() if r else None


def asegurar_requisito_sugerido(empresa_id, sugerencia):
    """Crea (si no existe) el requisito legal sugerido (capa operativa) y devuelve su id de fila."""
    if not sugerencia:
        return None
    idr = sugerencia.get('id_requisito')
    row = RequisitoLegal.query.filter_by(empresa_id=empresa_id, id_requisito=idr).first()
    if not row:
        row = RequisitoLegal(empresa_id=empresa_id, id_requisito=idr, capa='operativa',
                             is_mandatory=0, origen='Legal Nacional',
                             cuerpo_normativo=sugerencia.get('cuerpo_legal'),
                             requisito_legal=sugerencia.get('requisito'),
                             estado_avance='pendiente', fecha=_hoy())
        sqla.session.add(row)
        _commit()
    return row.id


def vincular_riesgo_requisito(item_id, requisito_row_id):
    it = RiesgoItem.query.get(item_id)
    if it:
        it.requisito_legal_id = requisito_row_id
        _commit()
    return it.to_dict() if it else None


def riesgos_de_requisito(empresa_id, requisito_row_id):
    """Ítems de riesgo (MIPER) vinculados a un requisito legal, en la empresa."""
    rows = (sqla.session.query(RiesgoItem, TareaIPER.nombre)
            .join(MatrizRiesgo, MatrizRiesgo.id == RiesgoItem.matriz_id)
            .outerjoin(TareaIPER, TareaIPER.id == RiesgoItem.tarea_id)
            .filter(MatrizRiesgo.empresa_id == empresa_id,
                    RiesgoItem.requisito_legal_id == requisito_row_id).all())
    return [{**it.to_dict(), 'tarea': nombre} for it, nombre in rows]


def contratos_mineros_de(empresa_id):
    return [{'id': c.id, 'numero': c.numero, 'mandante': c.mandante}
            for c in Contrato.query.filter_by(empresa_id=empresa_id, es_contratista_minera=1).all()]


# ── Fase 2: Gestión de faena — precarga por contrato desde la Carpeta de Arranque ──
def riesgos_de_contrato(empresa_id, contrato_id):
    """Ítems de riesgo (MIPER) ligados a un contrato/faena, con el nombre de su tarea."""
    rows = (sqla.session.query(RiesgoItem, TareaIPER.nombre)
            .join(MatrizRiesgo, MatrizRiesgo.id == RiesgoItem.matriz_id)
            .outerjoin(TareaIPER, TareaIPER.id == RiesgoItem.tarea_id)
            .filter(MatrizRiesgo.empresa_id == empresa_id,
                    RiesgoItem.contrato_id == contrato_id)
            .order_by(RiesgoItem.id).all())
    return [{**it.to_dict(), 'tarea': nombre} for it, nombre in rows]


def precargar_faena(rut, contrato_id):
    """Precarga 'lo básico de la Carpeta de Arranque' para un contrato minero:
    (a) requisitos legales de la CAPA MANDANTE (RC/ECF del mandante) ligados al contrato;
    (b) actividades/riesgos críticos del mandante en la MIPER, tagueados con contrato_id.
    Idempotente. Devuelve {legales, riesgos} creados/existentes."""
    import resso
    c = Contrato.query.filter_by(id=contrato_id, rut_asesor=rut).first()
    if not c:
        return {'error': 'Contrato no encontrado.'}
    empresa_id = c.empresa_id
    mandante = c.mandante or 'Mandante'
    mid = matriz_riesgo_vigente(empresa_id)
    mid = mid['id'] if mid else crear_matriz_riesgo(empresa_id, rut)

    legales, riesgos = 0, 0
    # (a) Capa mandante (RESSO): Riesgos Críticos + ECF + SST (Estándares de Salud) como
    #     requisitos legales del contrato. NO toca la Matriz Legal transversal (DS 44 base).
    catalogo = (resso.ECF_RC_EST.get('RC', []) + resso.ECF_RC_EST.get('ECF', [])
                + resso.ECF_RC_EST.get('SST', []))
    for item in catalogo:
        idr = f"F{contrato_id}-{item['codigo']}"
        if RequisitoLegal.query.filter_by(empresa_id=empresa_id, id_requisito=idr).first():
            continue
        sqla.session.add(RequisitoLegal(
            empresa_id=empresa_id, contrato_id=contrato_id, id_requisito=idr, capa='mandante',
            is_mandatory=0, origen=mandante, cuerpo_normativo=f"Estándar {mandante} · {item['codigo']}",
            requisito_legal=item['titulo'], estado_avance='pendiente', fecha=_hoy()))
        legales += 1
    _commit()
    # (b) MIPER faena: Riesgos Críticos del mandante como tareas críticas (contrato_id)
    for item in resso.ECF_RC_EST.get('RC', []):
        nombre = f"{item['codigo']} · {item['titulo']}"
        existe = (sqla.session.query(TareaIPER)
                  .join(RiesgoItem, RiesgoItem.tarea_id == TareaIPER.id)
                  .filter(TareaIPER.matriz_id == mid, RiesgoItem.contrato_id == contrato_id,
                          TareaIPER.nombre == nombre).first())
        if existe:
            continue
        tid = tarea_crear(mid, nombre, proceso=f'Faena {mandante}')
        rid = riesgo_agregar(mid, item['titulo'], f"Riesgo crítico: {item['titulo']}",
                             'Control crítico según estándar del mandante (verificación en terreno).',
                             probabilidad=3, consecuencia=3, es_critico=1, contrato_id=contrato_id)
        it = RiesgoItem.query.get(rid)
        if it:
            it.tarea_id = tid
        riesgos += 1
    _commit()
    # (c) MIPER Codelco RT/DRT: preset real (SIGO-F-006 V7) por proceso, ligado a Carpeta 19 / RESSO B.3
    miper_drt_tareas = 0
    if resso.es_codelco(mandante) and any(k in (mandante or '').lower()
                                          for k in ('radomiro', 'drt', ' rt', 'rt ', 'división rt')):
        miper_drt_tareas = _inyectar_miper_drt(mid, contrato_id)
    return {'legales': legales, 'riesgos': riesgos, 'miper_drt': miper_drt_tareas, 'mandante': mandante}


def _inyectar_miper_drt(matriz_id, contrato_id):
    """Inyecta el preset MIPER de Codelco RT (miper_drt.MIPER_DRT): una Tarea por proceso y sus
    riesgos con contrato_id + categoria='iper' (Carpeta 19 / RESSO B.3). Idempotente. VEP=P×C."""
    import miper_drt
    creadas = 0
    for proc in miper_drt.MIPER_DRT:
        nombre = f"DRT · {proc['proceso']}"
        existe = TareaIPER.query.filter_by(matriz_id=matriz_id, nombre=nombre).first()
        if existe:
            tid = existe.id
            ya = {(r.peligro, r.riesgo) for r in RiesgoItem.query.filter_by(tarea_id=tid).all()}
        else:
            tid = tarea_crear(matriz_id, nombre, proceso='Codelco RT (SIGO-F-006)')
            ya = set()
            creadas += 1
        for r in proc['riesgos']:
            if (r['peligro'], r['riesgo']) in ya:
                continue
            rid = riesgo_agregar(matriz_id, r['peligro'], r['riesgo'], r.get('medida_control'),
                                 probabilidad=r.get('probabilidad'), consecuencia=r.get('consecuencia'),
                                 nivel_riesgo=r.get('nivel_texto'), metodo_correcto=r.get('metodo_correcto'),
                                 es_critico=r.get('es_critico', 0), contrato_id=contrato_id)
            it = RiesgoItem.query.get(rid)
            if it:
                it.tarea_id = tid
                it.ecf_punto = r.get('codigo')       # código DRT (RC-10, A1, …)
    _commit()
    return creadas


def inyectar_actividades_faena(rut, contrato_id, nombres):
    """Inyecta actividades base/personalizadas (por nombre) a la MIPER de una faena (contrato_id),
    tomándolas del catálogo base transversal o de la biblioteca. Sincroniza con IRL vía tareas."""
    import iper as _iper
    c = Contrato.query.filter_by(id=contrato_id, rut_asesor=rut).first()
    if not c:
        return {'error': 'Contrato no encontrado.'}
    empresa_id = c.empresa_id
    mid = matriz_riesgo_vigente(empresa_id)
    mid = mid['id'] if mid else crear_matriz_riesgo(empresa_id, rut)
    catalogo = {t['tarea']: t for t in _iper.CATALOGO_TAREAS_BASE}
    biblio = {b['nombre']: b for b in biblioteca_listar(empresa_id)}
    n = 0
    for nombre in (nombres or []):
        base = catalogo.get(nombre)
        tid = tarea_crear(mid, nombre, proceso=f'Faena {c.mandante or ""}'.strip())
        if base:
            for r in base.get('riesgos', []):
                rid = riesgo_agregar(mid, r['peligro'], r['riesgo'], r['medida_control'],
                                     probabilidad=r.get('probabilidad'), consecuencia=r.get('consecuencia'),
                                     metodo_correcto=r.get('metodo_correcto'), contrato_id=contrato_id)
                it = RiesgoItem.query.get(rid)
                if it:
                    it.tarea_id = tid
        elif nombre in biblio:
            b = biblio[nombre]
            rid = riesgo_agregar(mid, b.get('peligro'), b.get('riesgo'), b.get('medida_control'),
                                 probabilidad=b.get('probabilidad'), consecuencia=b.get('consecuencia'),
                                 metodo_correcto=b.get('metodo_correcto'), contrato_id=contrato_id)
            it = RiesgoItem.query.get(rid)
            if it:
                it.tarea_id = tid
        n += 1
    _commit()
    return {'inyectadas': n}


# ── Biblioteca personalizada (auto-aprendizaje) ──
def biblioteca_crear(empresa_id, nombre, peligro=None, riesgo=None, medida_control=None,
                     metodo_correcto=None, probabilidad=None, consecuencia=None):
    b = BibliotecaTarea(empresa_id=empresa_id, nombre=nombre, peligro=peligro, riesgo=riesgo,
                        medida_control=medida_control, metodo_correcto=metodo_correcto,
                        probabilidad=probabilidad, consecuencia=consecuencia, creado=_hoy())
    sqla.session.add(b)
    _commit()
    return b.id


def biblioteca_listar(empresa_id):
    return [b.to_dict() for b in
            BibliotecaTarea.query.filter_by(empresa_id=empresa_id).order_by(BibliotecaTarea.nombre).all()]


def biblioteca_eliminar(empresa_id, bid):
    BibliotecaTarea.query.filter_by(id=bid, empresa_id=empresa_id).delete()
    _commit()


def bloquear_y_versionar(empresa_id, motivo, creado_por=None):
    """Genera una Revisión V2: bloquea la matriz vigente y crea una nueva versión (N+1) vigente,
    clonando sus ítems y conservando el histórico (version_previa_id). Devuelve la nueva matriz."""
    actual = MatrizRiesgo.query.filter_by(empresa_id=empresa_id, estado='vigente').first()
    if not actual:
        nueva_id = crear_matriz_riesgo(empresa_id, creado_por)
        return MatrizRiesgo.query.get(nueva_id).to_dict()
    actual.estado = 'bloqueada'
    nueva = MatrizRiesgo(empresa_id=empresa_id, version=(actual.version or 1) + 1,
                         estado='vigente', motivo_revision=motivo, version_previa_id=actual.id,
                         creado_por=creado_por, creado_en=_hoy())
    sqla.session.add(nueva)
    sqla.session.flush()          # asigna nueva.id antes de clonar
    for it in RiesgoItem.query.filter_by(matriz_id=actual.id).all():
        sqla.session.add(RiesgoItem(
            matriz_id=nueva.id, tarea_id=it.tarea_id, peligro=it.peligro, riesgo=it.riesgo,
            probabilidad=it.probabilidad, consecuencia=it.consecuencia, vep=it.vep,
            nivel_riesgo=it.nivel_riesgo, medida_control=it.medida_control,
            metodo_correcto=it.metodo_correcto, tipo_control=it.tipo_control,
            mandante_key=it.mandante_key, es_critico=it.es_critico,
            requisito_legal_id=it.requisito_legal_id, estado_control=it.estado_control,
            evidencia_doc_id=it.evidencia_doc_id, contrato_id=it.contrato_id,
            ecf_punto=it.ecf_punto, mfl=it.mfl, bowtie=it.bowtie, fecha=_hoy()))
    _commit()
    return nueva.to_dict()


# ── Motor de integridad automática ──
def riesgo_editar_control(item_id, medida_control, quien=None):
    """Edita la medida de control de un riesgo. Si el ítem está amarrado a un requisito legal
    (requisito_legal_id), ese requisito queda 'en_revision' y se deja traza — evita trabajo doble."""
    it = RiesgoItem.query.get(item_id)
    if not it:
        return None
    it.medida_control = medida_control
    it.estado_control = 'vigente'
    it.fecha = _hoy()
    if it.requisito_legal_id:
        req = RequisitoLegal.query.get(it.requisito_legal_id)
        if req:
            req.estado_avance = 'en_revision'
            ahora = _dt.now().isoformat(timespec='seconds')
            sqla.session.add(ValidacionCumplimiento(
                requisito_id=req.id, validado_por=quien or 'sistema', validado_en=ahora,
                estado='en_revision',
                comentario='Cambió el control operativo en la Matriz de Riesgos; requiere re-validación legal.'))
    _commit()
    return it.to_dict()


def registrar_requerimiento(afecta, empresa_id, datos, creado_por=None):
    """Motor de integridad: '¿afecta a la Matriz Legal, a la de Riesgos, o a ambas?'.
    afecta ∈ {'legal','riesgo','ambas'}. Crea el/los registro(s) y los vincula (requisito_legal_id
    en el RiesgoItem cuando es 'ambas'). Devuelve {requisito, riesgo_item_id}."""
    out = {'requisito': None, 'riesgo_item_id': None}
    req_id = None
    if afecta in ('legal', 'ambas'):
        req = requisito_guardar(empresa_id, datos.get('legal', datos))
        out['requisito'] = req
        req_id = req.get('id')
    if afecta in ('riesgo', 'ambas'):
        r = datos.get('riesgo', datos)
        matriz_id = matriz_riesgo_vigente(empresa_id)
        matriz_id = matriz_id['id'] if matriz_id else crear_matriz_riesgo(empresa_id, creado_por)
        out['riesgo_item_id'] = riesgo_agregar(
            matriz_id, r.get('peligro'), r.get('riesgo'), r.get('medida_control'),
            probabilidad=r.get('probabilidad'), consecuencia=r.get('consecuencia'),
            nivel_riesgo=r.get('nivel_riesgo'), tipo_control=r.get('tipo_control'),
            mandante_key=r.get('mandante_key'), es_critico=r.get('es_critico', 0),
            requisito_legal_id=req_id, evidencia_doc_id=r.get('evidencia_doc_id'))
    return out


# ══════════════ Ronda 15 — Motor Documental: Tareas / EPP / PTS / Trabajadores / IRL ══════════
# ── Tareas de la Matriz IPER (agrupan riesgos) ──
def tarea_crear(matriz_id, nombre, proceso=None, rutinaria=None, responsable=None,
                fecha_evaluacion=None, estado_avance='Pendiente'):
    t = TareaIPER(matriz_id=matriz_id, nombre=nombre, proceso=proceso, rutinaria=rutinaria,
                  responsable=responsable, fecha_evaluacion=fecha_evaluacion,
                  estado_avance=estado_avance)
    sqla.session.add(t)
    _commit()
    return t.id


def tareas_de_matriz(matriz_id):
    return [t.to_dict() for t in
            TareaIPER.query.filter_by(matriz_id=matriz_id).order_by(TareaIPER.id).all()]


def tareas_de_empresa(empresa_id):
    """Tareas de la matriz de riesgos vigente de la empresa."""
    m = matriz_riesgo_vigente(empresa_id)
    return tareas_de_matriz(m['id']) if m else []


def riesgos_de_tarea(tarea_id):
    return [i.to_dict() for i in
            RiesgoItem.query.filter_by(tarea_id=tarea_id).order_by(RiesgoItem.id).all()]


# ── Catálogos EPP / PTS y su vínculo N-a-N con la Tarea ──
def epp_crear(empresa_id, nombre, codigo=None, norma=None):
    e = EPP(empresa_id=empresa_id, nombre=nombre, codigo=codigo, norma=norma)
    sqla.session.add(e)
    _commit()
    return e.id


def epp_listar(empresa_id):
    return [e.to_dict() for e in EPP.query.filter_by(empresa_id=empresa_id).order_by(EPP.nombre).all()]


def pts_crear(empresa_id, nombre, codigo=None, version=None, doc_id=None):
    p = PTS(empresa_id=empresa_id, nombre=nombre, codigo=codigo, version=version, doc_id=doc_id)
    sqla.session.add(p)
    _commit()
    return p.id


def pts_listar(empresa_id):
    return [p.to_dict() for p in PTS.query.filter_by(empresa_id=empresa_id).order_by(PTS.nombre).all()]


def tarea_link_epp(tarea_id, epp_id):
    if not TareaEPP.query.filter_by(tarea_id=tarea_id, epp_id=epp_id).first():
        sqla.session.add(TareaEPP(tarea_id=tarea_id, epp_id=epp_id))
        _commit()


def tarea_link_pts(tarea_id, pts_id):
    if not TareaPTS.query.filter_by(tarea_id=tarea_id, pts_id=pts_id).first():
        sqla.session.add(TareaPTS(tarea_id=tarea_id, pts_id=pts_id))
        _commit()


def epp_de_tarea(tarea_id):
    rows = (sqla.session.query(EPP).join(TareaEPP, TareaEPP.epp_id == EPP.id)
            .filter(TareaEPP.tarea_id == tarea_id).all())
    return [e.to_dict() for e in rows]


def pts_de_tarea(tarea_id):
    rows = (sqla.session.query(PTS).join(TareaPTS, TareaPTS.pts_id == PTS.id)
            .filter(TareaPTS.tarea_id == tarea_id).all())
    return [p.to_dict() for p in rows]


# ── Trabajadores y sus Tareas asignadas ──
def trabajador_crear(empresa_id, rut, nombre, cargo=None, rol=None, contrato_id=None):
    t = Trabajador(empresa_id=empresa_id, contrato_id=contrato_id or 0, rut=rut, nombre=nombre,
                   cargo=cargo, rol=rol, fecha_ingreso=_hoy())
    sqla.session.add(t)
    _commit()
    return t.id


def trabajadores_de(empresa_id):
    return [t.to_dict() for t in
            Trabajador.query.filter_by(empresa_id=empresa_id).order_by(Trabajador.nombre).all()]


def trabajador_de(empresa_id, trabajador_id):
    t = Trabajador.query.filter_by(id=trabajador_id, empresa_id=empresa_id).first()
    return t.to_dict() if t else None


def trabajador_eliminar(empresa_id, trabajador_id):
    TrabajadorTarea.query.filter_by(trabajador_id=trabajador_id).delete()
    Trabajador.query.filter_by(id=trabajador_id, empresa_id=empresa_id).delete()
    _commit()


def trabajador_set_tareas(trabajador_id, tarea_ids):
    TrabajadorTarea.query.filter_by(trabajador_id=trabajador_id).delete()
    for tid in tarea_ids or []:
        sqla.session.add(TrabajadorTarea(trabajador_id=trabajador_id, tarea_id=int(tid)))
    _commit()


def tareas_de_trabajador(trabajador_id):
    rows = (sqla.session.query(TareaIPER).join(TrabajadorTarea, TrabajadorTarea.tarea_id == TareaIPER.id)
            .filter(TrabajadorTarea.trabajador_id == trabajador_id).all())
    return [t.to_dict() for t in rows]


# ── Registro de auditoría de IRLs generados ──
def irl_registrar(trabajador_id, empresa_id, matriz_version, doc_id, audit_id, generado_por,
                  requiere_refirma=False, motivo=None):
    r = IRLGenerado(trabajador_id=trabajador_id, empresa_id=empresa_id, matriz_version=matriz_version,
                    doc_id=doc_id, audit_id=audit_id, generado_por=generado_por,
                    generado_en=_dt.now().isoformat(timespec='seconds'),
                    estado='Actualizado' if requiere_refirma else 'Generado',
                    requiere_refirma=1 if requiere_refirma else 0, motivo_actualizacion=motivo)
    sqla.session.add(r)
    _commit()
    return r.id


def irls_de_trabajador(trabajador_id):
    return [r.to_dict() for r in
            IRLGenerado.query.filter_by(trabajador_id=trabajador_id)
            .order_by(IRLGenerado.id.desc()).all()]


# ══════════════ Ronda 22 — Vehículos + QR (checklist móvil) ══════════════
import secrets as _secrets, json as _json2


def vehiculo_crear(empresa_id, patente, tipo=None, marca_modelo=None, km_actual=None):
    patente = (patente or '').strip().upper()
    v = Vehiculo(empresa_id=empresa_id, patente=patente, tipo=tipo, marca_modelo=marca_modelo,
                 km_actual=km_actual, token=_secrets.token_urlsafe(9), creado=_hoy())
    sqla.session.add(v)
    _commit()
    return v.id


def vehiculos_de(empresa_id):
    out = []
    for v in Vehiculo.query.filter_by(empresa_id=empresa_id).order_by(Vehiculo.patente).all():
        d = v.to_dict()
        ult = (ChecklistVehiculo.query.filter_by(vehiculo_id=v.id)
               .order_by(ChecklistVehiculo.id.desc()).first())
        d['ultimo_checklist'] = ult.to_dict() if ult else None
        out.append(d)
    return out


def vehiculo_de(empresa_id, vehiculo_id):
    v = Vehiculo.query.filter_by(id=vehiculo_id, empresa_id=empresa_id).first()
    return v.to_dict() if v else None


def vehiculo_por_token(token):
    v = Vehiculo.query.filter_by(token=token).first()
    return v.to_dict() if v else None


def vehiculo_eliminar(empresa_id, vehiculo_id):
    ChecklistVehiculo.query.filter_by(vehiculo_id=vehiculo_id).delete()
    Vehiculo.query.filter_by(id=vehiculo_id, empresa_id=empresa_id).delete()
    _commit()


def checklist_hoy(vehiculo_id, conductor_rut):
    """¿Ya se hizo hoy el checklist de este vehículo para este conductor? (primer viaje del día)."""
    if not conductor_rut:
        return None
    row = (ChecklistVehiculo.query
           .filter_by(vehiculo_id=vehiculo_id, conductor_rut=conductor_rut, fecha=_hoy()).first())
    return row.to_dict() if row else None


def checklist_vehiculo_guardar(vehiculo_id, empresa_id, conductor_nombre, conductor_rut, km,
                               fys, veh, conforme, alertas):
    from datetime import datetime as _dt2
    row = ChecklistVehiculo(
        vehiculo_id=vehiculo_id, empresa_id=empresa_id, conductor_nombre=conductor_nombre,
        conductor_rut=conductor_rut, fecha=_hoy(), km=km,
        fys_json=_json2.dumps(fys, ensure_ascii=False), vehiculo_json=_json2.dumps(veh, ensure_ascii=False),
        conforme=1 if conforme else 0, observacion=' · '.join(alertas) if alertas else None,
        creado_ts=_dt2.now().isoformat(timespec='seconds'))
    sqla.session.add(row)
    # actualizar km del vehículo
    v = Vehiculo.query.get(vehiculo_id)
    if v and km is not None:
        v.km_actual = km
    _commit()
    return row.id


def checklists_de_vehiculo(vehiculo_id, limite=30):
    return [c.to_dict() for c in
            ChecklistVehiculo.query.filter_by(vehiculo_id=vehiculo_id)
            .order_by(ChecklistVehiculo.id.desc()).limit(limite).all()]


def checklists_no_conformes(empresa_id):
    """Checklists con alerta (fatiga o vehículo NC) — para el panel de pendientes."""
    rows = (sqla.session.query(ChecklistVehiculo, Vehiculo.patente)
            .join(Vehiculo, Vehiculo.id == ChecklistVehiculo.vehiculo_id)
            .filter(ChecklistVehiculo.empresa_id == empresa_id, ChecklistVehiculo.conforme == 0)
            .order_by(ChecklistVehiculo.id.desc()).limit(20).all())
    return [{**c.to_dict(), 'patente': p} for c, p in rows]
