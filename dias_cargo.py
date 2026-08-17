"""Tabla de Días Cargo — Resolución Exenta ISP (equivalencias de días para lesiones con
incapacidad permanente parcial que no tuvieron días de reposo médico reales, o cuyo reposo real
es menor al que la ley reconoce por la secuela). Dato puro, mismo estilo que roles_criticos.py /
riesgos_isp.py: un dict a nivel de módulo, sin BD ni Flask.

Se usa para completar el numerador de la Tasa de Gravedad (DS44/ISP):
  Tasa de Gravedad = (días perdidos + días cargo) · 1.000.000 / HH trabajadas

TODO: esta tabla trae solo un subconjunto de valores conocidos como placeholder. La tabla
oficial completa (todas las lesiones tabuladas por la Resolución Exenta del ISP) debe
transcribirse fila por fila contra el documento fuente antes de usarla en producción — mismo
método que riesgos_isp.py ("no transcrito a mano" sin verificar). Mientras no esté completa,
una lesión no listada aquí devuelve 0 días cargo (nunca se inventa una cifra).
"""

TABLA_DIAS_CARGO = {
    'muerte': 6000,
    'perdida_mano': 3000,
    'perdida_pie': 2400,
    'perdida_dedo_pulgar': 600,
    'perdida_dedo_indice': 400,
    'perdida_dedo_medio': 300,
    'perdida_dedo_anular': 300,
    'perdida_dedo_menique': 300,
    'perdida_vision_un_ojo': 1800,
}

# Etiquetas legibles para el <select> del formulario de alta.
ETIQUETAS_TIPO_LESION = {
    'muerte': 'Muerte',
    'perdida_mano': 'Pérdida de mano',
    'perdida_pie': 'Pérdida de pie',
    'perdida_dedo_pulgar': 'Pérdida dedo pulgar',
    'perdida_dedo_indice': 'Pérdida dedo índice',
    'perdida_dedo_medio': 'Pérdida dedo medio',
    'perdida_dedo_anular': 'Pérdida dedo anular',
    'perdida_dedo_menique': 'Pérdida dedo meñique',
    'perdida_vision_un_ojo': 'Pérdida de visión de un ojo',
    'otra': 'Otra (sin días cargo tabulados)',
}


def dias_cargo_de(tipo_lesion, dias_cargo_manual=None):
    """Días cargo de un siniestro: el override manual gana; si no hay, se busca en la tabla;
    si el tipo de lesión no está tabulado, 0 (no se inventa un valor)."""
    if dias_cargo_manual is not None:
        return int(dias_cargo_manual)
    return TABLA_DIAS_CARGO.get((tipo_lesion or '').strip(), 0)
