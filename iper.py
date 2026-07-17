"""Módulo IPER/MIPER (Ronda 17) — evaluación de riesgos estrictamente DS 44 / Guía ISP 3.

Responsabilidad única: el modelo de evaluación base (VEP = Probabilidad × Consecuencia, escala 3×3),
el catálogo transversal precargado y el catálogo de subpuntos ECF de la capa minera condicional.
No incluye MFL/Bowtie en la base: esos son campos opcionales de la capa minera (por faena).
"""

# ── Evaluación VEP = Probabilidad × Consecuencia ──
# Escala OFICIAL de la hoja 'Valoración Riesgo' del formato MATRIZ IPER (Guía ISP 3) V3.3 DS 44:
# Baja=1 · Media=2 · Alta=4. Ronda 27: antes usábamos Alta=3 (VEP máx 9), que no existe en la
# tabla oficial — un "VEP 9 Intolerable" no es un valor válido del DS 44.
ESCALA = [1, 2, 4]
PROBABILIDAD = {1: 'Baja', 2: 'Media', 4: 'Alta'}
CONSECUENCIA = {1: 'Baja', 2: 'Media', 4: 'Alta'}

# Magnitud según el producto VEP. Con escala 1/2/4 los únicos VEP posibles son estos cinco
# valores EXACTOS (no rangos): 1×1=1, 2×1=2, 2×2=4, 4×2=8, 4×4=16.
_MAGNITUD = {
    1:  ('Trivial',     'bg-gray-100 text-gray-600'),
    2:  ('Tolerable',   'bg-green-100 text-green-700'),
    4:  ('Moderado',    'bg-yellow-100 text-yellow-700'),
    8:  ('Importante',  'bg-amber-100 text-amber-700'),
    16: ('Intolerable', 'bg-red-100 text-red-700'),
}
VEP_VALIDOS = frozenset(_MAGNITUD)


def _al_peldano(v):
    """Acota un valor al peldaño válido más cercano hacia abajo (1, 2 o 4)."""
    for p in reversed(ESCALA):
        if v >= p:
            return p
    return ESCALA[0]


def calcular_vep(probabilidad, consecuencia):
    """Devuelve {vep, magnitud, color, probabilidad, consecuencia}. P y C se acotan a la escala."""
    try:
        p = _al_peldano(min(4, max(1, int(probabilidad))))
        c = _al_peldano(min(4, max(1, int(consecuencia))))
    except (TypeError, ValueError):
        return {'vep': None, 'magnitud': None, 'color': '', 'probabilidad': None, 'consecuencia': None}
    vep = p * c
    magnitud, color = _MAGNITUD[vep]
    return {'vep': vep, 'magnitud': magnitud, 'color': color, 'probabilidad': p, 'consecuencia': c}


# ── GEMA: factores de riesgo del Anexo 3 del formato oficial ──
# Ronda 27: corregido. Antes usábamos el GEMA clásico (Gente/Equipos/Materiales/Ambiente), que
# NO es lo que define el Anexo 3 de este formato.
GEMA = {
    'agentes_materiales': 'Agentes materiales',
    'entorno_ambiental': 'Entorno ambiental',
    'caracteristicas_personales': 'Características personales',
    'organizacion': 'Organización',
}


# ── Riesgo residual (Ronda 25 · escala corregida en la 27) ──
# Cuántos PELDAÑOS de la escala baja la Probabilidad un control validado, según su jerarquía.
# Honra la prelación del DS 44 (Art. 12) — la misma que exige el ítem 13 del FUF: privilegiar la
# protección colectiva por sobre el EPP.
#
# PELDAÑOS y no resta: la escala [1, 2, 4] no es lineal. Restar 1 a Alta(4) daría 3, un valor que
# no existe en la tabla de valoración oficial. Se baja por la escalera: 4 → 2 → 1.
PELDANOS_POR_CONTROL = {
    'eliminacion': 2, 'sustitucion': 2, 'ingenieria': 2,      # Alta(4) → Baja(1)
    'administrativo': 1, 'senaletica': 1, 'epp': 1,           # Alta(4) → Media(2)
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
    3. La Probabilidad nunca baja del primer peldaño (1). No existe el riesgo cero.
    """
    base = calcular_vep(probabilidad, consecuencia)
    if base['vep'] is None:
        return {'probabilidad': None, 'consecuencia': None, 'vep': None, 'magnitud': None, 'color': ''}
    if not validado:
        return {'probabilidad': base['probabilidad'], 'consecuencia': base['consecuencia'],
                'vep': base['vep'], 'magnitud': base['magnitud'], 'color': base['color']}
    # Se baja por la escalera [1,2,4]; restar produciría valores fuera de la escala oficial.
    peldanos = PELDANOS_POR_CONTROL.get((tipo_control or '').strip().lower(), 1)
    i = max(0, ESCALA.index(base['probabilidad']) - peldanos)
    res = calcular_vep(ESCALA[i], base['consecuencia'])
    return {'probabilidad': res['probabilidad'], 'consecuencia': res['consecuencia'],
            'vep': res['vep'], 'magnitud': res['magnitud'], 'color': res['color']}


# ── Riesgos del Anexo 2 que SÍ tienen medida de control validada ──
# Solo estos cinco: son los del catálogo transversal, cuyo contenido preventivo está escrito y
# revisado. Para los otros 52 riesgos del Anexo 2 el sistema NO propone control: son medidas con
# peso legal y su autoría es del prevencionista, no de la aplicación (ver matriz_riesgos/routes).
CONTROLES_VALIDADOS = {
    'I2': 'Conducción de vehículos',          # Choque, colisión o volcamiento
    'P4': 'Exposición a radiación UV',        # Exposición a radiaciones no ionizantes
    'R1': 'Manejo manual de cargas',          # Sobrecarga física por manipulación manual de carga
    'S1': 'Digitación / trabajo en oficina',  # Sobrecarga física por trabajo repetitivo
    'A1': 'Orden y aseo',                     # Caídas al mismo nivel
}


def codigos_con_control():
    """Todos los códigos del Anexo 2 que traen control sugerido (de cualquiera de las 2 fuentes).
    Lo usa el panel para marcar con ✓ los riesgos que se autocargan."""
    import controles_ds44
    return sorted(set(CONTROLES_VALIDADOS) | set(controles_ds44.CONTROLES))


def control_validado(codigo):
    """Control sugerido para un riesgo del Anexo 2, de dos fuentes, o None si no hay base.

    1º CONTROLES_VALIDADOS (5 riesgos del catálogo transversal): traen peligro, método y P/C, así
       que se prefieren — son la propuesta más completa.
    2º controles_ds44.CONTROLES: el resto de los riesgos con base DS 44, solo con la medida.

    None significa 'que lo escriba el experto', nunca 'invéntalo'. La UI marca lo autocargado como
    propuesta editable, no como medida cerrada.
    """
    from formato import normalizar_control_operativo
    cod = (codigo or '').strip().upper()
    tarea = CONTROLES_VALIDADOS.get(cod)
    if tarea:
        for t in CATALOGO_TAREAS_BASE:
            if t['tarea'] == tarea and t.get('riesgos'):
                r = t['riesgos'][0]
                # Numerado ya, para que en el textarea se vea ordenado (1. 2. 3.).
                return {'fuente': 'catalogo_transversal', 'peligro': r.get('peligro'),
                        'medida_control': normalizar_control_operativo(r.get('medida_control')),
                        'metodo_correcto': r.get('metodo_correcto'),
                        'probabilidad': r.get('probabilidad'), 'consecuencia': r.get('consecuencia')}
    import controles_ds44
    lista = controles_ds44.controles(cod)
    if lista:
        return {'fuente': 'ds44', 'peligro': None,
                'medida_control': normalizar_control_operativo('\n'.join(lista)),
                'metodo_correcto': None, 'probabilidad': None, 'consecuencia': None}
    return None


# ── Catálogo base transversal (se precarga al inicializar la matriz de una empresa) ──
# Cada entrada: tarea + (peligro, riesgo, medida preventiva, método correcto, P, C).
# P/C en la escala oficial 1/2/4 (Ronda 27: los 'Alta' pasaron de 3 a 4).
CATALOGO_TAREAS_BASE = [
    {'tarea': 'Conducción de vehículos', 'proceso': 'Transversal', 'riesgos': [
        {'peligro': 'Tránsito vehicular', 'riesgo': 'Colisión / accidente de tránsito',
         'medida_control': 'Licencia vigente, revisión preuso, respeto de límites y descansos.',
         'metodo_correcto': 'Check-list preuso, cinturón de seguridad, velocidad segura, prohibición de uso de celular.',
         'probabilidad': 2, 'consecuencia': 4}]},
    {'tarea': 'Exposición a radiación UV', 'proceso': 'Transversal', 'riesgos': [
        {'peligro': 'Radiación ultravioleta solar', 'riesgo': 'Quemaduras / cáncer de piel',
         'medida_control': 'Protección solar, ropa de manga larga, sombra, gestión de la exposición.',
         'metodo_correcto': 'Aplicar bloqueador FPS 50+, usar gorro legionario y lentes UV, evitar exposición 11:00-15:00.',
         'probabilidad': 4, 'consecuencia': 2}]},
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
