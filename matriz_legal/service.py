"""Lógica del módulo Matriz Legal. Solo depende de db/models/cumplimiento — nunca de app.py
ni del módulo onboarding (aislamiento por carpeta)."""
import cumplimiento
import db
from models import sqla, RequisitoLegal

from .formato import normalizar_control_operativo

_ORDEN_PILARES = ('P1', 'P2', 'P3', 'OTROS')


def asegurar_core(empresa_id):
    """Rescate lazy de la capa Core, en el patrón de db.protocolos_de().

    Hace falta porque seed_requisitos_core() solo corre dentro de crear_empresa(): las empresas
    creadas antes de esta versión no tienen los Core enriquecidos (pilar/artículo/control) y no
    hay backfill masivo en el repo.

    Escribe directo por ORM a propósito, saltándose db.requisito_guardar(): esa función bloquea
    los campos de definición en filas Core (is_mandatory=1), que es justo lo que hay que llenar.
    Enriquecer el catálogo no es una edición de usuario. Solo rellena lo vacío: nunca pisa dato
    escrito por el asesor.

    Centinela: `pilar IS NULL`. En régimen es un SELECT que devuelve 0 filas.
    """
    db.seed_requisitos_core(empresa_id)          # idempotente: crea los Core que falten
    pendientes = (RequisitoLegal.query
                  .filter(RequisitoLegal.empresa_id == empresa_id,
                          RequisitoLegal.is_mandatory == 1,
                          RequisitoLegal.pilar.is_(None))
                  .all())
    if not pendientes:
        return 0
    catalogo = {r['id_requisito']: r for r in cumplimiento.REQUISITOS_CORE}
    for row in pendientes:
        c = catalogo.get(row.id_requisito)
        if not c:
            row.pilar = 'OTROS'                  # Core ajeno al catálogo: no lo re-visites
            continue
        row.pilar = c.get('pilar') or 'OTROS'
        if not row.control_operativo and c.get('control_operativo'):
            row.control_operativo = normalizar_control_operativo(c['control_operativo'])
        if not row.articulo and c.get('articulo'):
            row.articulo = c['articulo']
    sqla.session.commit()
    return len(pendientes)


def agrupar_por_pilar(filas):
    """[fila] → [{'pilar', 'nombre', 'filas'}] en orden P1, P2, P3, OTROS y las operativas al
    final. Los grupos vacíos no se emiten."""
    grupos, operativas = [], []
    por_pilar = {}
    for f in filas:
        p = f.get('pilar')
        if p in _ORDEN_PILARES and f.get('is_mandatory'):
            por_pilar.setdefault(p, []).append(f)
        else:
            operativas.append(f)
    for p in _ORDEN_PILARES:
        if por_pilar.get(p):
            grupos.append({'pilar': p, 'nombre': cumplimiento.PILARES[p], 'filas': por_pilar[p]})
    if operativas:
        grupos.append({'pilar': 'OPERATIVA', 'nombre': 'Requisitos agregados manualmente',
                       'filas': operativas})
    return grupos
