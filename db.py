"""Capa de datos local (SQLite) para contratos, documentos y estados de control."""
import os
import sqlite3
from datetime import date

DB_PATH = os.path.join(os.path.dirname(__file__), 'smarthse.db')


def conn():
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    # journal en memoria: evita el error "readonly database" en discos exFAT/NTFS
    # (locales). En Render (ext4) es inocuo.
    c.execute('PRAGMA journal_mode=MEMORY;')
    c.execute('PRAGMA synchronous=OFF;')
    return c


def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS contrato (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rut_asesor TEXT NOT NULL,
            empresa TEXT NOT NULL,
            faena TEXT,
            numero TEXT NOT NULL,
            mandante TEXT,
            creado TEXT
        );
        CREATE TABLE IF NOT EXISTS documento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contrato_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            flujo TEXT,
            tipo TEXT,
            fecha TEXT,
            FOREIGN KEY (contrato_id) REFERENCES contrato(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS control_estado (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rut_asesor TEXT NOT NULL,
            contrato_id INTEGER NOT NULL,
            control_key TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'pendiente',
            origen_contrato_id INTEGER,
            fecha TEXT,
            UNIQUE (contrato_id, control_key),
            FOREIGN KEY (contrato_id) REFERENCES contrato(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS carpeta_estado (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contrato_id INTEGER NOT NULL,
            item_n INTEGER NOT NULL,
            estado TEXT NOT NULL DEFAULT 'pendiente',
            observacion TEXT,
            fecha TEXT,
            UNIQUE (contrato_id, item_n),
            FOREIGN KEY (contrato_id) REFERENCES contrato(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS fuf_estado (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rut_asesor TEXT NOT NULL,
            item_n INTEGER NOT NULL,
            estado TEXT NOT NULL DEFAULT 'pendiente',
            observacion TEXT,
            fecha_compromiso TEXT,
            fecha TEXT,
            UNIQUE (rut_asesor, item_n)
        );
        -- ── Ronda 7: Fuente Única de Verdad + herencia Carpeta↔RESSO ──
        CREATE TABLE IF NOT EXISTS mapping_req (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            arranque_item_n INTEGER,
            reso_codigo TEXT,
            UNIQUE (categoria)
        );
        CREATE TABLE IF NOT EXISTS trabajador (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contrato_id INTEGER NOT NULL,
            rut TEXT NOT NULL,
            nombre TEXT,
            rol TEXT,
            fecha_ingreso TEXT,
            FOREIGN KEY (contrato_id) REFERENCES contrato(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS auditoria_estado (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contrato_id INTEGER NOT NULL,
            punto_key TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'pendiente',
            observacion TEXT,
            fecha_compromiso TEXT,
            fecha TEXT,
            UNIQUE (contrato_id, punto_key),
            FOREIGN KEY (contrato_id) REFERENCES contrato(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS aplicabilidad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contrato_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            codigo TEXT NOT NULL,
            aplica TEXT NOT NULL DEFAULT 'no',
            evidencia_doc_id INTEGER,
            fecha TEXT,
            UNIQUE (contrato_id, tipo, codigo),
            FOREIGN KEY (contrato_id) REFERENCES contrato(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS documento_generado (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contrato_id INTEGER NOT NULL,
            tipo_doc TEXT NOT NULL,
            nombre TEXT,
            estado TEXT NOT NULL DEFAULT 'Creado',
            historial_json TEXT,
            fecha TEXT,
            FOREIGN KEY (contrato_id) REFERENCES contrato(id) ON DELETE CASCADE
        );
        """)
        # Migraciones suaves (columnas nuevas en tablas existentes)
        _add_column(c, 'contrato', 'datos_json', 'TEXT')
        _add_column(c, 'contrato', 'arranque_aprobado', 'INTEGER')
        _add_column(c, 'contrato', 'resso_estado', 'TEXT')
        _add_column(c, 'documento', 'item_n', 'INTEGER')
        _add_column(c, 'carpeta_estado', 'fecha_compromiso', 'TEXT')
        # documento: herencia + trazabilidad legal
        _add_column(c, 'documento', 'categoria', 'TEXT')
        _add_column(c, 'documento', 'is_master', 'INTEGER')
        _add_column(c, 'documento', 'ref_doc_id', 'INTEGER')
        _add_column(c, 'documento', 'fecha_vencimiento', 'TEXT')
        _add_column(c, 'documento', 'vigencia_meses', 'INTEGER')
        _add_column(c, 'documento', 'version', 'TEXT')
        _add_column(c, 'documento', 'fecha_aprobacion', 'TEXT')
        _add_column(c, 'documento', 'firma', 'TEXT')
        _sembrar_mapping(c)


def _sembrar_mapping(c):
    """Siembra la tabla de mapping Arranque↔RESO desde el catálogo canónico (resso.EQUIVALENCIAS)."""
    import resso
    for categoria, m in resso.EQUIVALENCIAS.items():
        c.execute("""
            INSERT INTO mapping_req (categoria, arranque_item_n, reso_codigo)
            VALUES (?,?,?)
            ON CONFLICT(categoria) DO UPDATE SET
                arranque_item_n=excluded.arranque_item_n, reso_codigo=excluded.reso_codigo
        """, (categoria, m.get('carpeta'), m.get('reso')))


def _add_column(c, tabla, columna, tipo):
    cols = [r['name'] for r in c.execute(f'PRAGMA table_info({tabla})').fetchall()]
    if columna not in cols:
        c.execute(f'ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}')


# ───────────────────────────── Contratos ──────────────────────────────────
def listar_contratos(rut):
    with conn() as c:
        rows = c.execute(
            'SELECT * FROM contrato WHERE rut_asesor=? ORDER BY id', (rut,)).fetchall()
        return [dict(r) for r in rows]


def crear_contrato(rut, empresa, faena, numero, mandante, datos_json=None):
    with conn() as c:
        cur = c.execute(
            'INSERT INTO contrato (rut_asesor, empresa, faena, numero, mandante, creado, datos_json) '
            'VALUES (?,?,?,?,?,?,?)',
            (rut, empresa, faena, numero, mandante, date.today().isoformat(), datos_json))
        return cur.lastrowid


def actualizar_datos(contrato_id, datos_json):
    with conn() as c:
        c.execute('UPDATE contrato SET datos_json=? WHERE id=?', (datos_json, contrato_id))


def eliminar_contrato(rut, contrato_id):
    with conn() as c:
        c.execute('DELETE FROM control_estado WHERE contrato_id=? AND rut_asesor=?',
                  (contrato_id, rut))
        c.execute('DELETE FROM documento WHERE contrato_id=?', (contrato_id,))
        c.execute('DELETE FROM contrato WHERE id=? AND rut_asesor=?', (contrato_id, rut))


def contrato_de(rut, contrato_id):
    with conn() as c:
        r = c.execute('SELECT * FROM contrato WHERE id=? AND rut_asesor=?',
                      (contrato_id, rut)).fetchone()
        return dict(r) if r else None


# ───────────────────────────── Documentos ─────────────────────────────────
def registrar_documento(contrato_id, nombre, flujo, tipo, item_n=None,
                        categoria=None, is_master=0, ref_doc_id=None,
                        version=None, fecha_aprobacion=None, firma=None,
                        vigencia_meses=None, fecha_vencimiento=None):
    """Inserta un documento (o una referencia si ref_doc_id) y devuelve su id."""
    with conn() as c:
        cur = c.execute(
            'INSERT INTO documento (contrato_id, nombre, flujo, tipo, fecha, item_n, '
            'categoria, is_master, ref_doc_id, version, fecha_aprobacion, firma, '
            'vigencia_meses, fecha_vencimiento) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (contrato_id, nombre, flujo, tipo, date.today().isoformat(), item_n,
             categoria, is_master, ref_doc_id, version, fecha_aprobacion, firma,
             vigencia_meses, fecha_vencimiento))
        return cur.lastrowid


def documentos_de(contrato_id):
    with conn() as c:
        rows = c.execute('SELECT * FROM documento WHERE contrato_id=? ORDER BY id DESC',
                         (contrato_id,)).fetchall()
        return [dict(r) for r in rows]


def documento_por_id(rut, doc_id):
    """Documento + validación de pertenencia al asesor (join contrato por rut)."""
    with conn() as c:
        r = c.execute("""
            SELECT d.* FROM documento d JOIN contrato ct ON ct.id = d.contrato_id
            WHERE d.id=? AND ct.rut_asesor=?
        """, (doc_id, rut)).fetchone()
        return dict(r) if r else None


def set_doc_maestro(doc_id, categoria=None):
    with conn() as c:
        if categoria:
            c.execute('UPDATE documento SET is_master=1, categoria=? WHERE id=?', (categoria, doc_id))
        else:
            c.execute('UPDATE documento SET is_master=1 WHERE id=?', (doc_id,))


def docs_por_categoria(contrato_id, categoria):
    with conn() as c:
        rows = c.execute('SELECT * FROM documento WHERE contrato_id=? AND categoria=? ORDER BY id DESC',
                         (contrato_id, categoria)).fetchall()
        return [dict(r) for r in rows]


def doc_maestro_de_categoria(rut, categoria):
    """Documento maestro (is_master=1) de una categoría para el asesor, o None."""
    with conn() as c:
        r = c.execute("""
            SELECT d.*, ct.numero AS contrato_numero FROM documento d
            JOIN contrato ct ON ct.id = d.contrato_id
            WHERE ct.rut_asesor=? AND d.categoria=? AND d.is_master=1
            ORDER BY d.id DESC LIMIT 1
        """, (rut, categoria)).fetchone()
        return dict(r) if r else None


def crear_doc_referencia(target_cid, master, tipo='matriz'):
    """Crea una referencia simbólica al doc maestro en el contrato destino (sin copiar archivo)."""
    return registrar_documento(
        target_cid, master['nombre'], master.get('flujo', ''), tipo,
        item_n=master.get('item_n'), categoria=master.get('categoria'),
        is_master=0, ref_doc_id=master['id'],
        version=master.get('version'), fecha_aprobacion=master.get('fecha_aprobacion'),
        firma=master.get('firma'))


def existe_referencia(target_cid, master_id):
    with conn() as c:
        r = c.execute('SELECT 1 FROM documento WHERE contrato_id=? AND ref_doc_id=? LIMIT 1',
                      (target_cid, master_id)).fetchone()
        return r is not None


def mapping_de(categoria):
    with conn() as c:
        r = c.execute('SELECT * FROM mapping_req WHERE categoria=?', (categoria,)).fetchone()
        return dict(r) if r else None


def maestros_vencidos(rut, dias_aviso=30):
    """Documentos maestros vencidos o próximos a vencer, del asesor."""
    from datetime import timedelta
    limite = (date.today() + timedelta(days=dias_aviso)).isoformat()
    with conn() as c:
        rows = c.execute("""
            SELECT d.*, ct.numero AS contrato_numero FROM documento d
            JOIN contrato ct ON ct.id = d.contrato_id
            WHERE ct.rut_asesor=? AND d.is_master=1 AND d.fecha_vencimiento IS NOT NULL
              AND d.fecha_vencimiento <= ?
            ORDER BY d.fecha_vencimiento
        """, (rut, limite)).fetchall()
        return [dict(r) for r in rows]


def referencias_de(master_id):
    """Docs hijos (auditorías vinculadas) que referencian a un maestro."""
    with conn() as c:
        rows = c.execute('SELECT * FROM documento WHERE ref_doc_id=?', (master_id,)).fetchall()
        return [dict(r) for r in rows]


# ── Contrato: hito de arranque / estado RESSO ──
def set_arranque_aprobado(contrato_id, resso_estado='en_progreso'):
    with conn() as c:
        c.execute('UPDATE contrato SET arranque_aprobado=1, resso_estado=? WHERE id=?',
                  (resso_estado, contrato_id))


def set_resso_estado(contrato_id, estado):
    with conn() as c:
        c.execute('UPDATE contrato SET resso_estado=? WHERE id=?', (estado, contrato_id))


# ── Auditoría RESSO (estado por punto) ──
def set_auditoria_estado(contrato_id, punto_key, estado, observacion='', fecha_compromiso=None):
    with conn() as c:
        c.execute("""
            INSERT INTO auditoria_estado (contrato_id, punto_key, estado, observacion, fecha_compromiso, fecha)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(contrato_id, punto_key) DO UPDATE SET
                estado=excluded.estado, observacion=excluded.observacion,
                fecha_compromiso=excluded.fecha_compromiso, fecha=excluded.fecha
        """, (contrato_id, punto_key, estado, observacion, fecha_compromiso, date.today().isoformat()))


def estados_auditoria(contrato_id):
    with conn() as c:
        rows = c.execute('SELECT * FROM auditoria_estado WHERE contrato_id=?', (contrato_id,)).fetchall()
        return {r['punto_key']: dict(r) for r in rows}


# ──────────────────────────── Carpeta de Arranque ─────────────────────────
def set_item_estado(contrato_id, item_n, estado, observacion='', fecha_compromiso=None):
    with conn() as c:
        c.execute("""
            INSERT INTO carpeta_estado (contrato_id, item_n, estado, observacion, fecha_compromiso, fecha)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(contrato_id, item_n) DO UPDATE SET
                estado=excluded.estado, observacion=excluded.observacion,
                fecha_compromiso=excluded.fecha_compromiso, fecha=excluded.fecha
        """, (contrato_id, item_n, estado, observacion, fecha_compromiso, date.today().isoformat()))


def estados_carpeta(contrato_id):
    with conn() as c:
        rows = c.execute('SELECT * FROM carpeta_estado WHERE contrato_id=?', (contrato_id,)).fetchall()
        return {r['item_n']: dict(r) for r in rows}


def eliminar_doc_tipo(contrato_id, item_n, tipo):
    with conn() as c:
        c.execute('DELETE FROM documento WHERE contrato_id=? AND item_n=? AND tipo=?',
                  (contrato_id, item_n, tipo))


def docs_por_item(contrato_id):
    with conn() as c:
        rows = c.execute("SELECT * FROM documento WHERE contrato_id=? AND item_n IS NOT NULL "
                         "ORDER BY id DESC", (contrato_id,)).fetchall()
        out = {}
        for r in rows:
            out.setdefault(r['item_n'], []).append(dict(r))
        return out


def set_carpeta_compromiso(contrato_id, item_n, fecha_compromiso):
    """Actualiza solo la fecha de compromiso de un ítem de carpeta (si existe)."""
    with conn() as c:
        c.execute('UPDATE carpeta_estado SET fecha_compromiso=? WHERE contrato_id=? AND item_n=?',
                  (fecha_compromiso, contrato_id, item_n))


# ──────────────────────────── Estado FUF (DS 44) ──────────────────────────
def set_fuf_estado(rut, item_n, estado, observacion='', fecha_compromiso=None):
    with conn() as c:
        c.execute("""
            INSERT INTO fuf_estado (rut_asesor, item_n, estado, observacion, fecha_compromiso, fecha)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(rut_asesor, item_n) DO UPDATE SET
                estado=excluded.estado, observacion=excluded.observacion,
                fecha_compromiso=excluded.fecha_compromiso, fecha=excluded.fecha
        """, (rut, item_n, estado, observacion, fecha_compromiso, date.today().isoformat()))


def estados_fuf(rut):
    with conn() as c:
        rows = c.execute('SELECT * FROM fuf_estado WHERE rut_asesor=?', (rut,)).fetchall()
        return {r['item_n']: dict(r) for r in rows}


def set_fuf_compromiso(rut, item_n, fecha_compromiso):
    with conn() as c:
        c.execute('UPDATE fuf_estado SET fecha_compromiso=? WHERE rut_asesor=? AND item_n=?',
                  (fecha_compromiso, rut, item_n))


# ──────────────────────────── Brechas (Carpeta + FUF) ─────────────────────
def brechas_carpeta(rut):
    """Ítems de Carpeta en estado 'pendiente' de todos los contratos del asesor."""
    with conn() as c:
        rows = c.execute("""
            SELECT ce.item_n, ce.observacion, ce.fecha_compromiso,
                   ct.id AS contrato_id, ct.numero, ct.empresa, ct.faena
            FROM carpeta_estado ce
            JOIN contrato ct ON ct.id = ce.contrato_id
            WHERE ct.rut_asesor=? AND ce.estado='pendiente'
            ORDER BY ct.id, ce.item_n
        """, (rut,)).fetchall()
        return [dict(r) for r in rows]


def brechas_fuf(rut):
    """Ítems del FUF en estado 'no' (No Cumple) del asesor."""
    with conn() as c:
        rows = c.execute("""
            SELECT item_n, observacion, fecha_compromiso
            FROM fuf_estado WHERE rut_asesor=? AND estado='no'
            ORDER BY item_n
        """, (rut,)).fetchall()
        return [dict(r) for r in rows]


# ──────────────────────────── Estados de control ──────────────────────────
def set_estado_control(rut, contrato_id, control_key, estado, origen_contrato_id=None):
    """Inserta o actualiza el estado de un control para un contrato."""
    with conn() as c:
        c.execute("""
            INSERT INTO control_estado (rut_asesor, contrato_id, control_key, estado, origen_contrato_id, fecha)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(contrato_id, control_key) DO UPDATE SET
                estado=excluded.estado,
                origen_contrato_id=excluded.origen_contrato_id,
                fecha=excluded.fecha
        """, (rut, contrato_id, control_key, estado, origen_contrato_id, date.today().isoformat()))


def estado_control(contrato_id, control_key):
    with conn() as c:
        r = c.execute('SELECT estado FROM control_estado WHERE contrato_id=? AND control_key=?',
                      (contrato_id, control_key)).fetchone()
        return r['estado'] if r else None


def estados_de_contrato(contrato_id):
    with conn() as c:
        rows = c.execute('SELECT * FROM control_estado WHERE contrato_id=?',
                         (contrato_id,)).fetchall()
        return {r['control_key']: dict(r) for r in rows}
