"""Preset MIPER Codelco División Radomiro Tomic (DRT) — Ronda 23.

Curado a partir del archivo real SIGO-F-006-MIPER_V7_DRT (contrato 4600046405): procesos del
contrato (Conducción, AllScan, administrativo, transversales) con sus riesgos clave, códigos DRT
(RC10/RC27/RC03/RC01/RC04, A1, B3, B4, N…), evaluación P×C (VEP = Valor Esperado de la Pérdida) y
medidas preventivas. Se autoinyecta al precargar un contrato Codelco RT (ligado a Carpeta ítem 19 /
RESSO B.3). No es la matriz completa (que incluye todas las dimensiones psicosociales e higiénicas);
es el preset esencial, editable en la consola MIPER.
"""

# Cada proceso: nombre + lista de riesgos {peligro, riesgo, codigo, probabilidad, consecuencia,
# medida_control, es_critico}. probabilidad/consecuencia en escala 1-4 (DRT); si None → nivel de
# exposición higiénico (se rotula en nivel textual).
MIPER_DRT = [
    {'proceso': 'Conducción', 'riesgos': [
        {'peligro': 'Pérdida de control de vehículo liviano', 'riesgo': 'RC10 · Choque, colisión o volcamiento',
         'codigo': 'RC-10', 'probabilidad': 2, 'consecuencia': 4, 'es_critico': 1,
         'medida_control': 'CCP1: Conductor certificado y con licencia interna; CCP2: revisión preuso; respeto de límites, distancias y descansos.',
         'metodo_correcto': 'Check-list preuso, cinturón, velocidad segura según pista, prohibición de celular, gestión de fatiga.'},
        {'peligro': 'Interacción persona-vehículo', 'riesgo': 'RC27 · Atropello o golpe con vehículo',
         'codigo': 'RC-27', 'probabilidad': 2, 'consecuencia': 4, 'es_critico': 1,
         'medida_control': 'Segregación peatón-vehículo, contacto visual, chaleco reflectante, bocinazos reglamentarios.',
         'metodo_correcto': 'Circular por zonas peatonales, no cruzar tras equipos detenidos, verificar punto ciego.'},
        {'peligro': 'Objetos/estructuras en la vía', 'riesgo': 'B4 · Choque contra objetos',
         'codigo': 'B4', 'probabilidad': 2, 'consecuencia': 2, 'es_critico': 0,
         'medida_control': 'Ubicar el vehículo en lugar seguro (costado de la vía) para cambio de neumático; conos/triángulos.',
         'metodo_correcto': 'Estacionar en zona segura, señalizar, freno de mano y calzas.'},
    ]},
    {'proceso': 'Instalación AllScan', 'riesgos': [
        {'peligro': 'Pérdida de control de vehículo liviano', 'riesgo': 'RC10 · Choque, colisión o volcamiento',
         'codigo': 'RC-10', 'probabilidad': 2, 'consecuencia': 4, 'es_critico': 1,
         'medida_control': 'CCP1: certificación del conductor; segregación; respeto de reglas de tránsito de faena.'},
        {'peligro': 'Interacción persona-vehículo/equipo', 'riesgo': 'RC27 · Atropello o golpe con vehículo',
         'codigo': 'RC-27', 'probabilidad': 2, 'consecuencia': 4, 'es_critico': 1,
         'medida_control': 'CCP1: segregación y control de interacción persona-equipo; contacto visual.'},
        {'peligro': 'Maniobra de izaje / carga suspendida', 'riesgo': 'RC03 · Aplastamiento por carga suspendida',
         'codigo': 'RC-03', 'probabilidad': 2, 'consecuencia': 4, 'es_critico': 1,
         'medida_control': 'Plan de izaje, rigger certificado, prohibición de circular bajo carga, control de radio de giro.'},
        {'peligro': 'Superficie de trabajo', 'riesgo': 'A1 · Caídas al mismo nivel',
         'codigo': 'A1', 'probabilidad': 2, 'consecuencia': 1, 'es_critico': 0,
         'medida_control': 'Sectores de tránsito libres de obstáculos y sobretamaños; orden y aseo.'},
        {'peligro': 'Emergencia', 'riesgo': 'N1 · Accidente a personas (lesión/grave/fatal)',
         'codigo': 'N1', 'probabilidad': 2, 'consecuencia': 4, 'es_critico': 1,
         'medida_control': 'Dar alerta inmediata a CECO, activar plan de emergencia, primeros auxilios, evacuación.'},
    ]},
    {'proceso': 'Habilitación y mantención AllScan', 'riesgos': [
        {'peligro': 'Energía eléctrica', 'riesgo': 'RC01 · Contacto eléctrico indirecto',
         'codigo': 'RC-01', 'probabilidad': 2, 'consecuencia': 4, 'es_critico': 1,
         'medida_control': 'CCP1: identificación y corte de energía; bloqueo y señalización (LOTO); verificación de ausencia de tensión.'},
        {'peligro': 'Energías de alta intensidad', 'riesgo': 'RC04 · Liberación descontrolada de energía',
         'codigo': 'RC-04', 'probabilidad': 2, 'consecuencia': 2, 'es_critico': 1,
         'medida_control': 'CCP1: aislar y disipar energías; bloqueo; permiso de trabajo.'},
        {'peligro': 'Herramientas cortopunzantes', 'riesgo': 'B3 · Cortes por objetos/herramientas',
         'codigo': 'B3', 'probabilidad': 2, 'consecuencia': 2, 'es_critico': 0,
         'medida_control': 'Evaluar eliminación; herramientas en buen estado; guantes anticorte; técnica correcta.'},
        {'peligro': 'Superficie de trabajo', 'riesgo': 'A1 · Caídas al mismo nivel',
         'codigo': 'A1', 'probabilidad': 2, 'consecuencia': 1, 'es_critico': 0,
         'medida_control': 'Vías despejadas, orden y aseo, calzado de seguridad.'},
        {'peligro': 'Otros riesgos de la tarea', 'riesgo': 'N · Otros riesgos',
         'codigo': 'N', 'probabilidad': 2, 'consecuencia': 1, 'es_critico': 0,
         'medida_control': 'Uso de EPP según la actividad, atención al entorno, aplicar herramientas de gestión (ART/AST).'},
    ]},
    {'proceso': 'Trabajo administrativo', 'riesgos': [
        {'peligro': 'Uso prolongado de pantalla/teclado', 'riesgo': 'S1 · Sobrecarga física (TMERT)',
         'codigo': 'S1', 'probabilidad': 2, 'consecuencia': 1, 'es_critico': 0,
         'medida_control': 'Puesto ergonómico, pausas activas, evaluación TMERT-EESS (DS 594).',
         'metodo_correcto': 'Pantalla a la altura de los ojos, pausas cada 45 min, muñecas neutras.'},
    ]},
    {'proceso': 'Transversales (todas las actividades)', 'riesgos': [
        {'peligro': 'Exposición a ruido', 'riesgo': 'P1 · Exposición a ruido (PREXOR)',
         'codigo': 'P1', 'probabilidad': None, 'consecuencia': None, 'es_critico': 0,
         'nivel_texto': 'Nivel higiénico (VRE < 0,25 LP)',
         'medida_control': 'Protección auditiva, vigilancia PREXOR, controles de ingeniería.'},
        {'peligro': 'Aerosoles/sílice', 'riesgo': 'RC20/O1 · Exposición a aerosoles (sílice)',
         'codigo': 'RC-20', 'probabilidad': None, 'consecuencia': None, 'es_critico': 0,
         'nivel_texto': 'Nivel higiénico (PLANESI)',
         'medida_control': 'Humectación, protección respiratoria, vigilancia PLANESI.'},
        {'peligro': 'Radiación UV solar', 'riesgo': 'P5 · Radiación no ionizante (UV)',
         'codigo': 'P5', 'probabilidad': None, 'consecuencia': None, 'es_critico': 0,
         'nivel_texto': 'Nivel higiénico',
         'medida_control': 'Bloqueador FPS 50+, ropa manga larga, gorro legionario, gestión de exposición.'},
        {'peligro': 'Factores psicosociales', 'riesgo': 'Riesgo psicosocial (SUSESO/ISTAS 21)',
         'codigo': 'PSICO', 'probabilidad': None, 'consecuencia': None, 'es_critico': 0,
         'nivel_texto': 'Evaluación CEAL-SM/SUSESO',
         'medida_control': 'Aplicación del cuestionario, medidas por dimensión, seguimiento del comité.'},
    ]},
]
