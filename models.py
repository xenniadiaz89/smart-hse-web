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


class Contrato(_DictMixin, sqla.Model):
    __tablename__ = 'contrato'
    id = sqla.Column(sqla.Integer, primary_key=True)
    rut_asesor = sqla.Column(sqla.Text, nullable=False, index=True)
    empresa = sqla.Column(sqla.Text, nullable=False)
    faena = sqla.Column(sqla.Text)
    numero = sqla.Column(sqla.Text, nullable=False)
    mandante = sqla.Column(sqla.Text)
    creado = sqla.Column(sqla.Text)
    datos_json = sqla.Column(sqla.Text)
    arranque_aprobado = sqla.Column(sqla.Integer, default=0)
    resso_estado = sqla.Column(sqla.Text)


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
    item_n = sqla.Column(sqla.Integer, nullable=False)
    estado = sqla.Column(sqla.Text, nullable=False, default='pendiente')
    observacion = sqla.Column(sqla.Text)
    fecha_compromiso = sqla.Column(sqla.Text)
    fecha = sqla.Column(sqla.Text)
    __table_args__ = (sqla.UniqueConstraint('rut_asesor', 'item_n'),)


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


class DocumentoGenerado(_DictMixin, sqla.Model):
    __tablename__ = 'documento_generado'
    id = sqla.Column(sqla.Integer, primary_key=True)
    contrato_id = sqla.Column(sqla.Integer, index=True, nullable=False)
    tipo_doc = sqla.Column(sqla.Text, nullable=False)
    nombre = sqla.Column(sqla.Text)
    estado = sqla.Column(sqla.Text, nullable=False, default='Creado')
    historial_json = sqla.Column(sqla.Text)
    fecha = sqla.Column(sqla.Text)
