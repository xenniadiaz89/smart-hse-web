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


# ── Capa minera condicional: subpuntos ECF (Estándares de Control de Fatalidades) ──
ECF_PUNTOS = [
    {'codigo': '22.1', 'titulo': 'Gestión de Riesgos Críticos y Estándares de Control de Fatalidades'},
    {'codigo': '22.3', 'titulo': 'Verificación de controles críticos en terreno'},
    {'codigo': '22.4', 'titulo': 'Reporte y respuesta ante desviación de controles críticos'},
]
