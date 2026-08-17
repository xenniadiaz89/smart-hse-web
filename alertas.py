"""Motor de alertas predictivas (Ronda 12) — módulo de responsabilidad única.

Consolida en un único Panel de Actividades Pendientes:
  (a) legales      → docs por vencer / vencidos (anualidad DS 44) vía db.pendientes_legales
  (b) operativas   → Matriz Legal con estado_avance='pendiente' → alerta al responsable
                     del Control_Operativo.

No envía correos aquí (hook desacoplado para una extensión futura); expone la lista priorizada
para la UI. Depende de `db` por inyección para no acoplar el import circularmente.
"""


def actividades_pendientes(db, empresa_id):
    """Lista unificada y priorizada. Cada item: {tipo, prioridad, titulo, detalle, ...}."""
    items = []

    # (a) Legales (anualidad)
    for p in db.pendientes_legales(empresa_id):
        if p['estado'] == 'vigente':
            continue
        items.append({
            'tipo': 'legal',
            'categoria': p['categoria'],
            'titulo': p['titulo'],
            'estado': p['estado'],
            'base_legal': p['base_legal'],
            'fecha_vencimiento': p.get('fecha_vencimiento'),
            'fuf_item': p.get('fuf_item'),
            'contratos': p.get('contratos', []),
            'mensaje': p['mensaje'],
            'prioridad': 0 if p['estado'] == 'pendiente_actualizacion' else 1,
        })

    # (b) Operativas (Matriz Legal — responsable del Control_Operativo)
    for r in db.matriz_legal(empresa_id):
        if (r.get('estado_avance') or '').lower() != 'pendiente':
            continue
        items.append({
            'tipo': 'operativa',
            'titulo': r.get('requisito_legal') or r.get('id_requisito') or 'Requisito legal',
            'estado': 'pendiente',
            'capa': r.get('capa'),
            'responsable': r.get('responsable') or '—',
            'control_operativo': r.get('control_operativo'),
            'cuerpo_normativo': r.get('cuerpo_normativo'),
            'frecuencia': r.get('frecuencia'),
            'prioridad': 1 if r.get('capa') == 'core' else 2,
        })

    # (c) Vehículos: checklists de terreno con no conformidad / fatiga (Ronda 22)
    try:
        for c in db.checklists_no_conformes(empresa_id):
            items.append({
                'tipo': 'vehiculo',
                'titulo': f"Checklist vehículo {c.get('patente','')} — no conforme",
                'estado': 'pendiente',
                'detalle': c.get('observacion') or 'Se detectaron no conformidades o indicios de fatiga.',
                'responsable': c.get('conductor_nombre') or '—',
                'fecha_compromiso': c.get('fecha'),
                'prioridad': 0,
            })
    except Exception:
        pass

    items.sort(key=lambda x: x.get('prioridad', 9))
    return items
