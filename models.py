"""Modelos SQLAlchemy (flask-sqlalchemy) — Fuente Única de Verdad de Smart HSE.

Reemplaza la capa sqlite3 cruda por ORM, de modo que la misma app corra sobre
PostgreSQL (Render, vía DATABASE_URL) o SQLite (local, fallback). Los archivos
(evidencias, logos, cartas) se guardan como BLOB en `Documento.contenido` para
persistir en la base y no depender del disco efímero.
"""
import sqlite3

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

sqla = SQLAlchemy()


@event.listens_for(Engine, "connect")
def _sqlite_pragmas(dbapi_connection, connection_record):
    """Solo para SQLite local: journal en memoria evita 'readonly database' en
    discos exFAT/NTFS. En PostgreSQL (Render) este listener no aplica."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA journal_mode=MEMORY")
        cur.execute("PRAGMA synchronous=OFF")
        cur.close()


class _DictMixin:
    """to_dict() para devolver filas como dicts (compatibilidad con la API previa).
    Excluye `contenido` (el blob) para no cargar binarios en operaciones de lista."""
    def to_dict(self):
        return {c.name: getattr(self, c.name)
                for c in self.__table__.columns if c.name != 'contenido'}


class Empresa(_DictMixin, sqla.Model):
    """Base estructural (Ronda 12): unidad que posee la Consola de Gestión
    Operativa (FUF DS 44 / Ley 16.744 / DS 594). Un asesor gestiona varias
    empresas; los contratos y el FUF cuelgan de la empresa."""
    __tablename__ = 'empresa'
    id = sqla.Column(sqla.Integer, primary_key=True)
    rut_asesor = sqla.Column(sqla.Text, nullable=False, index=True)
    rut_empresa = sqla.Column(sqla.Text)
    razon_social = sqla.Column(sqla.Text, nullable=False)
    mutual = sqla.Column(sqla.Text)
    n_adherente = sqla.Column(sqla.Text)
    rubro = sqla.Column(sqla.Text)
    creado = sqla.Column(sqla.Text)
    datos_json = sqla.Column(sqla.Text)


class Contrato(_DictMixin, sqla.Model):
    __tablename__ = 'contrato'
    id = sqla.Column(sqla.Integer, primary_key=True)
    rut_asesor = sqla.Column(sqla.Text, nullable=False, index=True)
    empresa_id = sqla.Column(sqla.Integer, index=True)   # Ronda 12: contrato cuelga de una Empresa
    empresa = sqla.Column(sqla.Text, nullable=False)
    faena = sqla.Column(sqla.Text)
    numero = sqla.Column(sqla.Text, nullable=False)
    mandante = sqla.Column(sqla.Text)
    creado = sqla.Column(sqla.Text)
    datos_json = sqla.Column(sqla.Text)
    arranque_aprobado = sqla.Column(sqla.Integer, default=0)
    resso_estado = sqla.Column(sqla.Text)
    # 1 = presta servicios como contratista a una minería (flujo Carpeta/RESSO);
    # 0 = empresa general (flujo educativo DS 44 / FUF). Un contrato evoluciona 0→1
    # sin perder evidencias (Módulo Puente).
    es_contratista_minera = sqla.Column(sqla.Integer, default=0)


class Documento(_DictMixin, sqla.Model):
    __tablename__ = 'documento'
    id = sqla.Column(sqla.Integer, primary_key=True)
    contrato_id = sqla.Column(sqla.Integer, index=True, nullable=False)
    nombre = sqla.Column(sqla.Text, nullable=False)
    flujo = sqla.Column(sqla.Text)
    tipo = sqla.Column(sqla.Text)
    fecha = sqla.Column(sqla.Text)
    item_n = sqla.Column(sqla.Integer)
    categoria = sqla.Column(sqla.Text)
    is_master = sqla.Column(sqla.Integer, default=0)
    ref_doc_id = sqla.Column(sqla.Integer)
    version = sqla.Column(sqla.Text)
    fecha_aprobacion = sqla.Column(sqla.Text)
    firma = sqla.Column(sqla.Text)
    vigencia_meses = sqla.Column(sqla.Integer)
    fecha_vencimiento = sqla.Column(sqla.Text)
    # Archivo persistido en la BD (no en disco efímero)
    contenido = sqla.Column(sqla.LargeBinary)
    mimetype = sqla.Column(sqla.Text)
    base_legal = sqla.Column(sqla.Text)             # Ronda 12: cimiento legal (snapshot de la regla)
    estado_cumplimiento = sqla.Column(sqla.Text)    # 'vigente'|'por_vencer'|'pendiente_actualizacion'


class ControlEstado(_DictMixin, sqla.Model):
    __tablename__ = 'control_estado'
    id = sqla.Column(sqla.Integer, primary_key=True)
    rut_asesor = sqla.Column(sqla.Text, nullable=False)
    contrato_id = sqla.Column(sqla.Integer, index=True, nullable=False)
    control_key = sqla.Column(sqla.Text, nullable=False)
    estado = sqla.Column(sqla.Text, nullable=False, default='pendiente')
    origen_contrato_id = sqla.Column(sqla.Integer)
    fecha = sqla.Column(sqla.Text)
    __table_args__ = (sqla.UniqueConstraint('contrato_id', 'control_key'),)


class CarpetaEstado(_DictMixin, sqla.Model):
    __tablename__ = 'carpeta_estado'
    id = sqla.Column(sqla.Integer, primary_key=True)
    contrato_id = sqla.Column(sqla.Integer, index=True, nullable=False)
    item_n = sqla.Column(sqla.Integer, nullable=False)
    estado = sqla.Column(sqla.Text, nullable=False, default='pendiente')
    observacion = sqla.Column(sqla.Text)
    fecha_compromiso = sqla.Column(sqla.Text)
    fecha = sqla.Column(sqla.Text)
    __table_args__ = (sqla.UniqueConstraint('contrato_id', 'item_n'),)


class FufEstado(_DictMixin, sqla.Model):
    __tablename__ = 'fuf_estado'
    id = sqla.Column(sqla.Integer, primary_key=True)
    rut_asesor = sqla.Column(sqla.Text, nullable=False, index=True)
    empresa_id = sqla.Column(sqla.Integer, index=True)   # Ronda 12: FUF base por empresa
    item_n = sqla.Column(sqla.Integer, nullable=False)
    estado = sqla.Column(sqla.Text, nullable=False, default='pendiente')
    observacion = sqla.Column(sqla.Text)
    fecha_compromiso = sqla.Column(sqla.Text)
    fecha = sqla.Column(sqla.Text)
    __table_args__ = (sqla.UniqueConstraint('empresa_id', 'item_n'),)


class MappingReq(_DictMixin, sqla.Model):
    __tablename__ = 'mapping_req'
    id = sqla.Column(sqla.Integer, primary_key=True)
    categoria = sqla.Column(sqla.Text, nullable=False, unique=True)
    arranque_item_n = sqla.Column(sqla.Integer)
    reso_codigo = sqla.Column(sqla.Text)


class Trabajador(_DictMixin, sqla.Model):
    __tablename__ = 'trabajador'
    id = sqla.Column(sqla.Integer, primary_key=True)
    contrato_id = sqla.Column(sqla.Integer, index=True, nullable=False)
    rut = sqla.Column(sqla.Text, nullable=False)
    nombre = sqla.Column(sqla.Text)
    rol = sqla.Column(sqla.Text)
    fecha_ingreso = sqla.Column(sqla.Text)


class AuditoriaEstado(_DictMixin, sqla.Model):
    __tablename__ = 'auditoria_estado'
    id = sqla.Column(sqla.Integer, primary_key=True)
    contrato_id = sqla.Column(sqla.Integer, index=True, nullable=False)
    punto_key = sqla.Column(sqla.Text, nullable=False)
    estado = sqla.Column(sqla.Text, nullable=False, default='pendiente')
    observacion = sqla.Column(sqla.Text)
    fecha_compromiso = sqla.Column(sqla.Text)
    fecha = sqla.Column(sqla.Text)
    __table_args__ = (sqla.UniqueConstraint('contrato_id', 'punto_key'),)


class Aplicabilidad(_DictMixin, sqla.Model):
    __tablename__ = 'aplicabilidad'
    id = sqla.Column(sqla.Integer, primary_key=True)
    contrato_id = sqla.Column(sqla.Integer, index=True, nullable=False)
    tipo = sqla.Column(sqla.Text, nullable=False)
    codigo = sqla.Column(sqla.Text, nullable=False)
    aplica = sqla.Column(sqla.Text, nullable=False, default='no')
    evidencia_doc_id = sqla.Column(sqla.Integer)
    fecha = sqla.Column(sqla.Text)
    __table_args__ = (sqla.UniqueConstraint('contrato_id', 'tipo', 'codigo'),)


class Usuario(_DictMixin, sqla.Model):
    __tablename__ = 'usuario'
    id = sqla.Column(sqla.Integer, primary_key=True)
    rut = sqla.Column(sqla.Text, nullable=False, unique=True)   # llave de acceso (RUT normalizado)
    rut_raw = sqla.Column(sqla.Text)                            # RUT como lo tecleó el usuario
    sns = sqla.Column(sqla.Text)                                # N° SNS: ID profesional visible
    nombre = sqla.Column(sqla.Text)
    rol = sqla.Column(sqla.Text, default='asesor')
    pass_hash = sqla.Column(sqla.Text)
    empresa_json = sqla.Column(sqla.Text)


class Vocabulario(_DictMixin, sqla.Model):
    __tablename__ = 'vocabulario'
    id = sqla.Column(sqla.Integer, primary_key=True)
    termino = sqla.Column(sqla.Text, nullable=False, unique=True)
    tipo = sqla.Column(sqla.Text, default='termino')          # 'termino' | 'sigla'
    significado = sqla.Column(sqla.Text)
    activo = sqla.Column(sqla.Integer, default=1)
    creado = sqla.Column(sqla.Text)


class ReglaCumplimiento(_DictMixin, sqla.Model):
    """Regla de actualización + base legal por categoría documental (Ronda 12)."""
    __tablename__ = 'regla_cumplimiento'
    id = sqla.Column(sqla.Integer, primary_key=True)
    categoria = sqla.Column(sqla.Text, nullable=False, unique=True)
    titulo = sqla.Column(sqla.Text)
    base_legal = sqla.Column(sqla.Text)             # 'DS 44/2024 · Ley 16.744'
    periodicidad_meses = sqla.Column(sqla.Integer, default=12)
    es_critico = sqla.Column(sqla.Integer, default=0)
    fuf_item = sqla.Column(sqla.Integer)            # ítem del FUF que satisface (alerta cruzada)
    activo = sqla.Column(sqla.Integer, default=1)


class DialectoMandante(_DictMixin, sqla.Model):
    """Traducción legal→faena: estándar del mandante por categoría (Ronda 12)."""
    __tablename__ = 'dialecto_mandante'
    id = sqla.Column(sqla.Integer, primary_key=True)
    mandante_key = sqla.Column(sqla.Text, nullable=False)   # 'codelco' | 'bhp_spence'
    categoria = sqla.Column(sqla.Text, nullable=False)
    estandar = sqla.Column(sqla.Text)               # 'Formalización Bow Tie / ECF (SIGO-P006)'
    metodologia = sqla.Column(sqla.Text)            # 'Bow Tie' | 'IEC 31010 · Riesgos Materiales'
    __table_args__ = (sqla.UniqueConstraint('mandante_key', 'categoria'),)


class RequisitoLegal(_DictMixin, sqla.Model):
    """Matriz Legal por capas (Ronda 12): Core Legal (DS 44) + Capa Mandante (RT/Spence)
    + Capa Operativa (PTS/Tareas). Normaliza la matriz aportada por el usuario."""
    __tablename__ = 'requisito_legal'
    id = sqla.Column(sqla.Integer, primary_key=True)
    empresa_id = sqla.Column(sqla.Integer, index=True, nullable=False)
    id_requisito = sqla.Column(sqla.Text)
    capa = sqla.Column(sqla.Text, default='core')          # 'core'|'mandante'|'operativa'
    origen = sqla.Column(sqla.Text)
    cuerpo_normativo = sqla.Column(sqla.Text)               # = base legal
    requisito_legal = sqla.Column(sqla.Text)
    riesgo_asociado = sqla.Column(sqla.Text)
    control_operativo = sqla.Column(sqla.Text)             # '1.\nAcción.\n2.\nResponsable.'
    responsable = sqla.Column(sqla.Text)
    frecuencia = sqla.Column(sqla.Text)
    estado_avance = sqla.Column(sqla.Text, default='pendiente')  # 'auditado'|'pendiente'|'en_revision'
    evidencia_doc_id = sqla.Column(sqla.Integer)
    categoria = sqla.Column(sqla.Text)                     # enlaza con EQUIVALENCIAS/reglas
    fecha = sqla.Column(sqla.Text)
    # Ronda 13 — Matriz Legal: fuente legal + detalle normativo + trazabilidad
    fuente_legal_id = sqla.Column(sqla.Integer)            # FK lógico a fuente_legal.id (tabla existente)
    articulo = sqla.Column(sqla.Text)
    obligacion = sqla.Column(sqla.Text)
    frecuencia_actualizacion_meses = sqla.Column(sqla.Integer)
    fecha_actualizacion = sqla.Column(sqla.Text)          # última actualización del requisito
    validado_por = sqla.Column(sqla.Text)                 # snapshot de la última validación
    validado_en = sqla.Column(sqla.Text)
    __table_args__ = (sqla.UniqueConstraint('empresa_id', 'id_requisito'),)


# ══════════ Ronda 13 — Dos pilares del SGSST (FK reales) ══════════
class FuenteLegal(_DictMixin, sqla.Model):
    """Cuerpo normativo vigente al que se amarra cada requisito (Ley 16.744, DS 44, DS 594…).
    Si `vigente=0` (ley derogada/modificada), sus requisitos entran en alerta."""
    __tablename__ = 'fuente_legal'
    id = sqla.Column(sqla.Integer, primary_key=True)
    codigo = sqla.Column(sqla.Text, nullable=False, unique=True)   # 'DS44','DS594','L16744'…
    nombre = sqla.Column(sqla.Text, nullable=False)
    vigente = sqla.Column(sqla.Integer, default=1)
    fecha_vigencia = sqla.Column(sqla.Text)
    url = sqla.Column(sqla.Text)


class ValidacionCumplimiento(_DictMixin, sqla.Model):
    """Bitácora auditable append-only: quién y cuándo validó un requisito legal."""
    __tablename__ = 'validacion_cumplimiento'
    id = sqla.Column(sqla.Integer, primary_key=True)
    requisito_id = sqla.Column(sqla.Integer, sqla.ForeignKey('requisito_legal.id'),
                               index=True, nullable=False)
    validado_por = sqla.Column(sqla.Text)
    validado_en = sqla.Column(sqla.Text)                  # ISO timestamp
    estado = sqla.Column(sqla.Text)                        # 'cumple'|'no_cumple'|'en_revision'
    comentario = sqla.Column(sqla.Text)


class MatrizRiesgo(_DictMixin, sqla.Model):
    """Encabezado versionable de la Matriz de Riesgos (IPER) por empresa. Una 'Revisión V2'
    bloquea la versión previa y crea una nueva vigente, conservando el histórico."""
    __tablename__ = 'matriz_riesgo'
    id = sqla.Column(sqla.Integer, primary_key=True)
    empresa_id = sqla.Column(sqla.Integer, sqla.ForeignKey('empresa.id'), index=True, nullable=False)
    version = sqla.Column(sqla.Integer, default=1)
    estado = sqla.Column(sqla.Text, default='vigente')     # 'vigente'|'bloqueada'|'borrador'
    motivo_revision = sqla.Column(sqla.Text)
    version_previa_id = sqla.Column(sqla.Integer, sqla.ForeignKey('matriz_riesgo.id'))
    creado_por = sqla.Column(sqla.Text)
    creado_en = sqla.Column(sqla.Text)
    __table_args__ = (sqla.UniqueConstraint('empresa_id', 'version'),)


class RiesgoItem(_DictMixin, sqla.Model):
    """Ítem IPER: Peligro / Riesgo / Evaluación (P×C) / Medida de Control, con dialecto por
    mandante y lazo a la Matriz Legal (requisito_legal_id) + evidencia en terreno."""
    __tablename__ = 'riesgo_item'
    id = sqla.Column(sqla.Integer, primary_key=True)
    matriz_id = sqla.Column(sqla.Integer, sqla.ForeignKey('matriz_riesgo.id'),
                            index=True, nullable=False)
    peligro = sqla.Column(sqla.Text)
    riesgo = sqla.Column(sqla.Text)
    probabilidad = sqla.Column(sqla.Integer)
    consecuencia = sqla.Column(sqla.Integer)
    nivel_riesgo = sqla.Column(sqla.Text)                  # evaluación P×C (bajo/medio/alto/crítico)
    medida_control = sqla.Column(sqla.Text)
    tipo_control = sqla.Column(sqla.Text)                  # jerarquía de control
    mandante_key = sqla.Column(sqla.Text)                  # dialecto: 'codelco'|'bhp_spence'|None
    es_critico = sqla.Column(sqla.Integer, default=0)
    # Lazo Riesgos → Legal: si el control es una norma legal, verifica su cumplimiento.
    requisito_legal_id = sqla.Column(sqla.Integer, sqla.ForeignKey('requisito_legal.id'))
    estado_control = sqla.Column(sqla.Text, default='vigente')  # 'vigente'|'en_revision'
    evidencia_doc_id = sqla.Column(sqla.Integer, sqla.ForeignKey('documento.id'))  # control en terreno
    fecha = sqla.Column(sqla.Text)


class DocumentoGenerado(_DictMixin, sqla.Model):
    __tablename__ = 'documento_generado'
    id = sqla.Column(sqla.Integer, primary_key=True)
    contrato_id = sqla.Column(sqla.Integer, index=True, nullable=False)
    tipo_doc = sqla.Column(sqla.Text, nullable=False)
    nombre = sqla.Column(sqla.Text)
    estado = sqla.Column(sqla.Text, nullable=False, default='Creado')
    historial_json = sqla.Column(sqla.Text)
    fecha = sqla.Column(sqla.Text)
