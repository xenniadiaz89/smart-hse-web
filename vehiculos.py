"""Módulo Vehículos + QR (Ronda 22) — checklist móvil de terreno.

Contiene los catálogos de los dos checklists que aparecen al escanear el QR de una patente:
- FYS (Fatiga y Somnolencia): preguntas de autochequeo del conductor (Sí = condición de riesgo).
- Vehículo (preuso): verificación de conformidad del vehículo antes de conducir.

La generación del QR (segno) y la persistencia viven en `app.py`/`db.py`. Aquí solo el conocimiento
del checklist, para poder renderizar la página móvil y evaluar conformidad/alertas.
"""

# Fatiga y Somnolencia — responder Sí/No. `riesgo_si=True`: un "Sí" indica condición de riesgo.
FYS_ITEMS = [
    {'k': 'horas_sueno', 'txt': '¿Dormiste menos de 6 horas anoche?', 'riesgo_si': True},
    {'k': 'cansancio', 'txt': '¿Te sientes cansado/a o con sueño en este momento?', 'riesgo_si': True},
    {'k': 'medicamentos', 'txt': '¿Tomaste medicamentos que provoquen somnolencia?', 'riesgo_si': True},
    {'k': 'alcohol_drogas', 'txt': '¿Consumiste alcohol o drogas en las últimas 12 horas?', 'riesgo_si': True},
    {'k': 'apto', 'txt': '¿Te sientes en condiciones físicas y mentales para conducir?', 'riesgo_si': False},
]

# Preuso del vehículo — responder Conforme / No conforme / N/A. `nc` = No conforme dispara alerta.
VEHICULO_ITEMS = [
    {'k': 'neumaticos', 'txt': 'Neumáticos (estado y presión) incluye rueda de repuesto'},
    {'k': 'luces', 'txt': 'Luces (altas, bajas, freno, intermitentes, baliza)'},
    {'k': 'frenos', 'txt': 'Frenos y freno de mano'},
    {'k': 'niveles', 'txt': 'Niveles (aceite, agua, refrigerante, líquido de frenos)'},
    {'k': 'cinturones', 'txt': 'Cinturones de seguridad operativos'},
    {'k': 'extintor', 'txt': 'Extintor vigente y accesible'},
    {'k': 'botiquin', 'txt': 'Botiquín y kit de emergencia (triángulos/conos, chaleco)'},
    {'k': 'documentos', 'txt': 'Documentación al día (permiso de circulación, SOAP, revisión técnica)'},
    {'k': 'parabrisas', 'txt': 'Parabrisas, espejos y limpiaparabrisas sin daños'},
    {'k': 'baliza_pertiga', 'txt': 'Baliza y pértiga (faena minera) operativas'},
]


def evaluar(fys, veh):
    """Devuelve (conforme:bool, alertas:list[str]) a partir de las respuestas."""
    alertas = []
    for it in FYS_ITEMS:
        r = (fys or {}).get(it['k'])
        if r is None:
            continue
        si = str(r).lower() in ('si', 'sí', 'true', '1')
        if (si and it['riesgo_si']) or ((not si) and not it['riesgo_si']):
            alertas.append('Fatiga/Somnolencia: ' + it['txt'])
    for it in VEHICULO_ITEMS:
        if str((veh or {}).get(it['k'], '')).lower() in ('nc', 'no_conforme', 'no conforme'):
            alertas.append('Vehículo NC: ' + it['txt'])
    return (len(alertas) == 0), alertas
