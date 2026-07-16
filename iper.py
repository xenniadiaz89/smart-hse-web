"""Módulo IPER/MIPER (Ronda 17) — evaluación de riesgos estrictamente DS 44 / Guía ISP 3.

Responsabilidad única: el modelo de evaluación base (VEP = Probabilidad × Consecuencia, escala 3×3),
el catálogo transversal precargado y el catálogo de subpuntos ECF de la capa minera condicional.
No incluye MFL/Bowtie en la base: esos son campos opcionales de la capa minera (por faena).
"""

# ── Evaluación VEP = Probabilidad × Consecuencia (escala 3×3, Guía ISP 3) ──
PROBABILIDAD = {1: 'Baja', 2: 'Media', 3: 'Alta'}
CONSECUENCIA = {1: 'Ligeramente dañino', 2: 'Dañino', 3: 'Extremadamente dañino'}

# Magnitud del Riesgo según el producto VEP (1..9).
_MAGNITUD = [
    (1, 'Trivial',     'bg-gray-100 text-gray-600'),
    (2, 'Tolerable',   'bg-green-100 text-green-700'),
    (4, 'Moderado',    'bg-yellow-100 text-yellow-700'),
    (6, 'Importante',  'bg-amber-100 text-amber-700'),
    (9, 'Intolerable', 'bg-red-100 text-red-700'),
]


def calcular_vep(probabilidad, consecuencia):
    """Devuelve {vep, magnitud, color, probabilidad, consecuencia}. P y C se acotan a 1..3."""
    try:
        p = min(3, max(1, int(probabilidad)))
        c = min(3, max(1, int(consecuencia)))
    except (TypeError, ValueError):
        return {'vep': None, 'magnitud': None, 'color': '', 'probabilidad': None, 'consecuencia': None}
    vep = p * c
    magnitud, color = 'Trivial', _MAGNITUD[0][2]
    for umbral, nombre, col in _MAGNITUD:
        if vep <= umbral:
            magnitud, color = nombre, col
            break
    else:
        magnitud, color = _MAGNITUD[-1][1], _MAGNITUD[-1][2]
    return {'vep': vep, 'magnitud': magnitud, 'color': color, 'probabilidad': p, 'consecuencia': c}


# ── GEMA: categorización del peligro (columna H del SIGO-F-006) ──
GEMA = {'G': 'Gente', 'E': 'Equipos', 'M': 'Materiales', 'A': 'Ambiente'}


# ── Riesgo residual (Ronda 25) ──
# Cuánto baja la PROBABILIDAD un control validado, según su jerarquía. Honra la prelación del
# DS 44 (Art. 12) — la misma que exige el ítem 13 del FUF: privilegiar la protección colectiva
# por sobre el EPP. Un control de ingeniería vale más que un casco, y el residual debe reflejarlo.
REBAJA_POR_CONTROL = {
    'eliminacion': 2, 'sustitucion': 2, 'ingenieria': 2,
    'administrativo': 1, 'senaletica': 1, 'epp': 1,
}
# Etiquetas para la UI (el orden es el de la prelación, de mayor a menor eficacia).
TIPOS_CONTROL = {
    'eliminacion': 'Eliminación', 'sustitucion': 'Sustitución', 'ingenieria': 'Ingeniería',
    'administrativo': 'Administrativo', 'senaletica': 'Señalética / Advertencia', 'epp': 'EPP',
}


def calcular_residual(probabilidad, consecuencia, tipo_control=None, validado=False):
    """Riesgo residual = el que queda DESPUÉS del control, cuando ese control está validado.

    Devuelve {probabilidad, consecuencia, vep, magnitud, color} o vep=None si falta P o C.

    Tres reglas, en este orden:
    1. Si el control NO está validado, el residual es IGUAL al inherente. Sin excepción: un
       control que no se ha verificado no reduce nada.
    2. La rebaja se aplica solo sobre la Probabilidad. La Consecuencia no baja: un control
       reduce cuán probable es el accidente, no cuán grave sería si ocurre.
    3. La Probabilidad nunca baja de 1. No existe el riesgo cero.
    """
    base = calcular_vep(probabilidad, consecuencia)
    if base['vep'] is None:
        return {'probabilidad': None, 'consecuencia': None, 'vep': None, 'magnitud': None, 'color': ''}
    if not validado:
        return {'probabilidad': base['probabilidad'], 'consecuencia': base['consecuencia'],
                'vep': base['vep'], 'magnitud': base['magnitud'], 'color': base['color']}
    rebaja = REBAJA_POR_CONTROL.get((tipo_control or '').strip().lower(), 1)
    p_res = max(1, base['probabilidad'] - rebaja)
    res = calcular_vep(p_res, base['consecuencia'])
    return {'probabilidad': res['probabilidad'], 'consecuencia': res['consecuencia'],
            'vep': res['vep'], 'magnitud': res['magnitud'], 'color': res['color']}


# ── Catálogo base transversal (se precarga al inicializar la matriz de una empresa) ──
# Cada entrada: tarea + (peligro, riesgo, medida preventiva, método correcto, P, C).
CATALOGO_TAREAS_BASE = [
    {'tarea': 'Conducción de vehículos', 'proceso': 'Transversal', 'riesgos': [
        {'peligro': 'Tránsito vehicular', 'riesgo': 'Colisión / accidente de tránsito',
         'medida_control': 'Licencia vigente, revisión preuso, respeto de límites y descansos.',
         'metodo_correcto': 'Check-list preuso, cinturón de seguridad, velocidad segura, prohibición de uso de celular.',
         'probabilidad': 2, 'consecuencia': 3}]},
    {'tarea': 'Exposición a radiación UV', 'proceso': 'Transversal', 'riesgos': [
        {'peligro': 'Radiación ultravioleta solar', 'riesgo': 'Quemaduras / cáncer de piel',
         'medida_control': 'Protección solar, ropa de manga larga, sombra, gestión de la exposición.',
         'metodo_correcto': 'Aplicar bloqueador FPS 50+, usar gorro legionario y lentes UV, evitar exposición 11:00-15:00.',
         'probabilidad': 3, 'consecuencia': 2}]},
    {'tarea': 'Manejo manual de cargas', 'proceso': 'Transversal', 'riesgos': [
        {'peligro': 'Sobreesfuerzo / posturas forzadas', 'riesgo': 'Trastornos musculoesqueléticos (TMERT)',
         'medida_control': 'Evaluación MMC (Ley 20.001), ayudas mecánicas, límites de peso.',
         'metodo_correcto': 'Levantar con las piernas, no girar la columna, pedir ayuda sobre 25 kg, usar carros/ayudas.',
         'probabilidad': 2, 'consecuencia': 2}]},
    {'tarea': 'Digitación / trabajo en oficina', 'proceso': 'Transversal', 'riesgos': [
        {'peligro': 'Uso prolongado de pantalla y teclado', 'riesgo': 'Fatiga visual y TMERT extremidad superior',
         'medida_control': 'Puesto ergonómico, pausas activas, iluminación adecuada.',
         'metodo_correcto': 'Pantalla a la altura de los ojos, pausas cada 45 min, muñecas neutras, silla regulada.',
         'probabilidad': 2, 'consecuencia': 1}]},
    {'tarea': 'Orden y aseo', 'proceso': 'Transversal', 'riesgos': [
        {'peligro': 'Superficies resbaladizas / obstáculos', 'riesgo': 'Caída al mismo nivel',
         'medida_control': 'Programa de orden y limpieza (5S), señalización, vías despejadas.',
         'metodo_correcto': 'Mantener pasillos libres, limpiar derrames de inmediato, señalizar piso mojado.',
         'probabilidad': 2, 'consecuencia': 2}]},
]


# ── Organismos Administradores de la Ley 16.744 (Adhesión) ──
MUTUALES = [
    'Mutual de Seguridad CChC',
    'ACHS — Asociación Chilena de Seguridad',
    'IST — Instituto de Seguridad del Trabajo',
    'ISL — Instituto de Seguridad Laboral (estatal)',
]


# ── Mapa normativo bidireccional: actividad/peligro → cuerpo legal aplicable ──
# Cada entrada: palabras clave → {cuerpo_legal, id_requisito sugerido, requisito}.
MAPA_LEGAL_ACTIVIDAD = [
    {'kw': ['manejo manual', 'carga', 'levant', 'mmc'],
     'cuerpo_legal': 'Ley 20.001 / DS 63', 'id_requisito': 'LEY-MMC',
     'requisito': 'Evaluación y control del manejo manual de cargas (límites de peso, ayudas mecánicas).'},
    {'kw': ['radiación uv', 'radiacion uv', 'ultravioleta', 'exposición solar', 'sol'],
     'cuerpo_legal': 'Ley 20.096 / DS 594', 'id_requisito': 'LEY-UV',
     'requisito': 'Protección contra radiación UV de origen solar (Ley 20.096, DS 594 Art. 109).'},
    {'kw': ['ruido', 'prexor', 'acústic'],
     'cuerpo_legal': 'DS 594 (PREXOR)', 'id_requisito': 'LEY-RUIDO',
     'requisito': 'Protocolo de vigilancia de riesgos por exposición a ruido (PREXOR, DS 594).'},
    {'kw': ['conducción', 'conduccion', 'vehículo', 'vehiculo', 'tránsito', 'transito', 'manej'],
     'cuerpo_legal': 'Ley 18.290 / DS 44', 'id_requisito': 'LEY-CONDUC',
     'requisito': 'Gestión del riesgo de conducción y tránsito (Ley del Tránsito 18.290; DS 44).'},
    {'kw': ['digitación', 'digitacion', 'pantalla', 'oficina', 'tmert', 'ergonom'],
     'cuerpo_legal': 'DS 594 (TMERT-EESS)', 'id_requisito': 'LEY-TMERT',
     'requisito': 'Identificación y control de TMERT de extremidad superior (Norma Técnica TMERT, DS 594).'},
    {'kw': ['orden y aseo', 'resbal', 'caída mismo', 'caida mismo', 'piso'],
     'cuerpo_legal': 'DS 594', 'id_requisito': 'LEY-DS594-OA',
     'requisito': 'Condiciones de orden, aseo y superficies de trabajo seguras (DS 594).'},
    {'kw': ['altura', 'caída de altura', 'caida de altura', 'distinto nivel'],
     'cuerpo_legal': 'DS 594 / DS 44', 'id_requisito': 'LEY-ALTURA',
     'requisito': 'Control de trabajos en altura física y caídas a distinto nivel (DS 594, DS 44).'},
    {'kw': ['sustancia', 'químic', 'quimic', 'peligros'],
     'cuerpo_legal': 'DS 594 / DS 43', 'id_requisito': 'LEY-SUSTQUIM',
     'requisito': 'Almacenamiento y manejo de sustancias peligrosas (DS 43, DS 594).'},
]


def sugerir_requisito(texto):
    """Devuelve el requisito legal sugerido para una actividad/peligro/riesgo (por palabras
    clave), o None si no hay coincidencia."""
    t = (texto or '').lower()
    if not t.strip():
        return None
    for m in MAPA_LEGAL_ACTIVIDAD:
        if any(k in t for k in m['kw']):
            return {'cuerpo_legal': m['cuerpo_legal'], 'id_requisito': m['id_requisito'],
                    'requisito': m['requisito']}
    return None


# ── Capa minera condicional: subpuntos ECF (Estándares de Control de Fatalidades) ──
ECF_PUNTOS = [
    {'codigo': '22.1', 'titulo': 'Gestión de Riesgos Críticos y Estándares de Control de Fatalidades'},
    {'codigo': '22.3', 'titulo': 'Verificación de controles críticos en terreno'},
    {'codigo': '22.4', 'titulo': 'Reporte y respuesta ante desviación de controles críticos'},
]
