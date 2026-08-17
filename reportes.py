"""Tarjeta de Reporte de Actos y Condiciones Subestándar — checklist móvil de participación.

Digitaliza la "Tarjeta Reporte de Actos y Condiciones Subestándar" (formulario HSE de 6 secciones).
Es un mecanismo de PARTICIPACIÓN de las personas trabajadoras (ítem FUF 25): cualquier trabajador
escanea el QR de la faena y reporta desde su teléfono, sin login.

No es un checklist de conformidad (no hay conforme/NC por ítem): es un reporte de un evento. Espejo
funcional de `vehiculos.py` — aquí solo el conocimiento del formulario (catálogos + evaluación); el QR
(segno), la ruta móvil y la persistencia viven en `app.py`/`db.py`.
"""

# Sección 2 — Clasificación del reporte.
CLASIFICACION = [
    {'k': 'condicion', 'txt': 'Condición subestándar',
     'desc': 'Fallo en el entorno, terreno, equipos o herramientas'},
    {'k': 'acto', 'txt': 'Acto subestándar',
     'desc': 'Conducta o incumplimiento de un procedimiento'},
]

# Sección 3 — Peligros asociados en topografía / minería (multiselección).
PELIGROS = [
    {'k': 'maquinaria_pesada', 'txt': 'Tránsito de maquinaria pesada / camiones'},
    {'k': 'taludes', 'txt': 'Taludes / Zanjas / Terreno inestable'},
    {'k': 'segregacion', 'txt': 'Falta de segregación / Barreras'},
    {'k': 'interferencia', 'txt': 'Interferencia con otros contratistas'},
    {'k': 'desniveles', 'txt': 'Desniveles / Riesgo de caída del personal'},
    {'k': 'clima', 'txt': 'Clima adverso / Poca visibilidad'},
    {'k': 'uv_temperatura', 'txt': 'Radiación UV / Temperaturas extremas'},
    {'k': 'equipos_defectuosos', 'txt': 'Equipos de medición / Herramientas defectuosas'},
    {'k': 'comunicacion', 'txt': 'Falta de comunicación en el área'},
    {'k': 'polvo_gases', 'txt': 'Exposición a polvo / Gases'},
    {'k': 'energias_peatonal', 'txt': 'Bloqueo de energías / Tránsito peatonal'},
    {'k': 'otro', 'txt': 'Otro'},
]

# Sección 5 — Nivel de riesgo operativo. `urgente=True` ⇒ detiene el trabajo (panel de pendientes).
NIVELES = [
    {'k': 'bajo', 'txt': 'Bajo', 'accion': 'Monitorear', 'color': 'green', 'urgente': False},
    {'k': 'medio', 'txt': 'Medio', 'accion': 'Corregir en el turno', 'color': 'amber', 'urgente': False},
    {'k': 'alto', 'txt': 'Alto', 'accion': 'Detener el trabajo', 'color': 'red', 'urgente': True},
]

_PELIGROS_TXT = {p['k']: p['txt'] for p in PELIGROS}
_NIVELES = {n['k']: n for n in NIVELES}
_CLASIF_TXT = {c['k']: c['txt'] for c in CLASIFICACION}


def nivel_meta(k):
    """Metadatos del nivel de riesgo (txt, acción, color, urgente) o el nivel bajo por defecto."""
    return _NIVELES.get((k or '').lower(), NIVELES[0])


def clasificacion_txt(k):
    return _CLASIF_TXT.get((k or '').lower(), k or '')


def peligros_txt(keys):
    """Lista de etiquetas legibles a partir de las claves de peligros marcadas."""
    return [_PELIGROS_TXT.get(k, k) for k in (keys or [])]


def evaluar(nivel):
    """Devuelve (urgente:bool, etiqueta:str) según el nivel de riesgo operativo del reporte."""
    m = nivel_meta(nivel)
    return bool(m['urgente']), f"{m['txt']} — {m['accion']}"
