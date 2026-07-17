"""Procesos preestablecidos para la Matriz de Riesgos (IPER) — insertables con un clic.

Cada preset es un PAQUETE: proceso → tarea(s) → riesgo(s) con su código del Anexo 2, GEMA, tipo,
P/C en la escala oficial 1/2/4, y sus controles más habituales. Todo queda EDITABLE al insertarse
(la "ventana abierta" que pidió el usuario): son RiesgoItem normales.

FUENTE Y MÉTODO
---------------
Los controles se consolidaron de las 15 matrices reales de DS44/Matriz de riesgos/ (293 pares
peligro→control) — vocabulario real confirmado: licencia, cinturón, check-list preuso, encuesta de
fatiga, bloqueador FPS 50+, protector de cuello, protector auditivo, HDS, bloqueo/verificación de
energía cero, límites de la Ley 20.001, programa 5S, etc. Curados a mano y LIMPIOS de lenguaje
minero (Codelco / "Faena Minera" / EURO NCAP), como autorizó el usuario. Son BORRADORES: el
prevencionista los revisa, ajusta y firma. El sistema propone, el experto valida.

Los controles van como lista; el módulo los normaliza a '1.\\n2.\\n' con
formato.normalizar_control_operativo antes de guardar.
"""

PRESETS = {
    'conduccion': {
        'proceso': 'Conducción / traslado a faena',
        'tareas': [{
            'nombre': 'Conducción de vehículo liviano', 'puesto': 'Conductor',
            'riesgos': [{
                'riesgo_codigo': 'I2', 'tipo_riesgo': 'seguridad', 'gema': 'agentes_materiales',
                'peligro': 'Tránsito vehicular', 'riesgo': 'Choque, colisión o volcamiento',
                'tipo_control': 'administrativo', 'probabilidad': 2, 'consecuencia': 4,
                'medida_control': [
                    'Licencia de conducir municipal e interna vigente y conductor autorizado',
                    'Uso de cinturón de seguridad de 3 puntas',
                    'Check-list preuso diario del vehículo',
                    'Gestión de la fatiga: encuesta de fatiga y somnolencia antes de conducir',
                    'Capacitación en conducción a la defensiva y examen psicosensotécnico vigente',
                    'Respeto de rutas, límites de velocidad y señalización',
                    'Mantención preventiva del vehículo según fabricante'],
            }, {
                'riesgo_codigo': 'I1', 'tipo_riesgo': 'seguridad', 'gema': 'organizacion',
                'peligro': 'Interacción persona-vehículo', 'riesgo': 'Atropello o golpe con vehículo',
                'tipo_control': 'administrativo', 'probabilidad': 2, 'consecuencia': 4,
                'medida_control': [
                    'Segregación peatón-vehículo y tránsito por zonas demarcadas',
                    'Contacto visual, chaleco reflectante y alarma de retroceso',
                    'Control de puntos ciegos antes de mover el vehículo'],
            }],
        }],
    },
    'altura': {
        'proceso': 'Trabajo en altura',
        'tareas': [{
            'nombre': 'Trabajo en altura (sobre 1,8 m)', 'puesto': 'Trabajador de altura',
            'riesgos': [{
                'riesgo_codigo': 'A3', 'tipo_riesgo': 'seguridad', 'gema': 'agentes_materiales',
                'peligro': 'Trabajo sobre 1,8 m de altura', 'riesgo': 'Caída de altura',
                'tipo_control': 'ingenieria', 'probabilidad': 2, 'consecuencia': 4,
                'medida_control': [
                    'Capacitación y entrenamiento para trabajo en altura',
                    'Condición de salud física y mental compatible con trabajo en altura',
                    'Plataformas, andamios y puntos de anclaje certificados y mantenidos',
                    'Sistema personal de detención de caídas (arnés y línea de vida) inspeccionado',
                    'Control de acceso, segregación del área y plan de rescate en altura'],
            }],
        }],
    },
    'mmc': {
        'proceso': 'Manejo manual de cargas',
        'tareas': [{
            'nombre': 'Manejo manual de cargas', 'puesto': 'Operario',
            'riesgos': [{
                'riesgo_codigo': 'R1', 'tipo_riesgo': 'musculo', 'gema': 'organizacion',
                'peligro': 'Sobreesfuerzo / posturas forzadas',
                'riesgo': 'Trastorno musculoesquelético',
                'tipo_control': 'administrativo', 'probabilidad': 2, 'consecuencia': 2,
                'medida_control': [
                    'Evaluación del manejo manual de cargas (Ley 20.001 y su guía técnica)',
                    'Respetar los límites legales de carga (25 kg hombres; 20 kg mujeres y menores de 18)',
                    'Ayudas mecánicas y levantamiento en equipo cuando corresponda',
                    'Capacitación en técnica de levantamiento y manejo manual de cargas'],
            }],
        }],
    },
    'electrico': {
        'proceso': 'Trabajo eléctrico',
        'tareas': [{
            'nombre': 'Intervención de instalaciones y equipos eléctricos', 'puesto': 'Electricista',
            'riesgos': [{
                'riesgo_codigo': 'F2', 'tipo_riesgo': 'seguridad', 'gema': 'agentes_materiales',
                'peligro': 'Contacto con energía eléctrica', 'riesgo': 'Contacto eléctrico / arco eléctrico',
                'tipo_control': 'ingenieria', 'probabilidad': 2, 'consecuencia': 4,
                'medida_control': [
                    'Identificación y corte efectivo de todas las fuentes de energía',
                    'Aislación, bloqueo y verificación de energía cero (procedimiento de bloqueo)',
                    'Personal competente y autorizado para intervención eléctrica',
                    'EPP dieléctrico según el nivel de tensión',
                    'Revisión y mantención del sistema eléctrico'],
            }],
        }],
    },
    'cortes': {
        'proceso': 'Uso de herramientas cortopunzantes',
        'tareas': [{
            'nombre': 'Trabajo con herramientas cortantes/cortopunzantes', 'puesto': 'Operario',
            'riesgos': [{
                'riesgo_codigo': 'B3', 'tipo_riesgo': 'seguridad', 'gema': 'agentes_materiales',
                'peligro': 'Herramienta cortante / cortopunzante', 'riesgo': 'Corte o punción',
                'tipo_control': 'administrativo', 'probabilidad': 2, 'consecuencia': 2,
                'medida_control': [
                    'Herramienta adecuada a la tarea, en buen estado y con resguardo',
                    'Guantes anticorte y técnica de corte alejando el cuerpo',
                    'Descarte seguro de elementos cortopunzantes en contenedor rígido'],
            }],
        }],
    },
    'uv': {
        'proceso': 'Exposición a radiación UV',
        'tareas': [{
            'nombre': 'Trabajo a la intemperie con exposición solar', 'puesto': 'Trabajador de terreno',
            'riesgos': [{
                'riesgo_codigo': 'P4', 'tipo_riesgo': 'higienico', 'gema': 'entorno_ambiental',
                'peligro': 'Radiación ultravioleta de origen solar', 'riesgo': 'Quemaduras / cáncer de piel',
                'tipo_control': 'administrativo', 'probabilidad': 4, 'consecuencia': 2,
                'medida_control': [
                    'Capacitación y difusión del protocolo de radiación UV (MINSAL)',
                    'Bloqueador solar FPS 50+ y ropa de manga larga con filtro UV',
                    'Protector de cuello (legionario), gorro y lentes con filtro UV',
                    'Verificación y difusión del índice UV; sombra y agua potable disponibles'],
            }],
        }],
    },
    'ruido': {
        'proceso': 'Exposición a ruido',
        'tareas': [{
            'nombre': 'Trabajo con exposición a ruido', 'puesto': 'Operario',
            'riesgos': [{
                'riesgo_codigo': 'P1', 'tipo_riesgo': 'higienico', 'gema': 'entorno_ambiental',
                'peligro': 'Exposición a ruido', 'riesgo': 'Hipoacusia sensorioneural laboral',
                'tipo_control': 'administrativo', 'probabilidad': 4, 'consecuencia': 2,
                'medida_control': [
                    'Programa de protección auditiva (PREXOR / MINSAL)',
                    'Control del ruido en la fuente y en el medio cuando sea factible',
                    'Selección y uso de protector auditivo certificado',
                    'Vigilancia audiométrica de las personas expuestas'],
            }],
        }],
    },
    'quimicas': {
        'proceso': 'Manejo de sustancias químicas',
        'tareas': [{
            'nombre': 'Almacenamiento y manipulación de sustancias químicas', 'puesto': 'Operario',
            'riesgos': [{
                'riesgo_codigo': 'G2', 'tipo_riesgo': 'seguridad', 'gema': 'agentes_materiales',
                'peligro': 'Sustancias químicas peligrosas', 'riesgo': 'Contacto / intoxicación química',
                'tipo_control': 'administrativo', 'probabilidad': 2, 'consecuencia': 4,
                'medida_control': [
                    'Hojas de Datos de Seguridad (HDS) disponibles y capacitación en su uso',
                    'Almacenamiento por compatibilidad y contención de derrames',
                    'EPP/respirador específico con prueba de ajuste positiva y negativa',
                    'Respuesta ante emergencias químicas y urgencia médica'],
            }],
        }],
    },
    'orden_aseo': {
        'proceso': 'Orden y aseo',
        'tareas': [{
            'nombre': 'Orden y aseo del lugar de trabajo', 'puesto': 'Todos los puestos',
            'riesgos': [{
                'riesgo_codigo': 'A1', 'tipo_riesgo': 'seguridad', 'gema': 'entorno_ambiental',
                'peligro': 'Superficies resbaladizas u obstáculos', 'riesgo': 'Caída al mismo nivel',
                'tipo_control': 'administrativo', 'probabilidad': 2, 'consecuencia': 2,
                'medida_control': [
                    'Programa de orden y limpieza (5S) y vías de tránsito despejadas',
                    'Tránsito solo por lugares habilitados y demarcados',
                    'Limpieza inmediata de derrames y señalización de piso mojado',
                    'Calzado de seguridad antideslizante e iluminación adecuada'],
            }],
        }],
    },
}

# Orden y etiqueta para el menú del panel.
LISTA = [
    ('conduccion', 'Conducción / traslado a faena'),
    ('altura', 'Trabajo en altura'),
    ('mmc', 'Manejo manual de cargas'),
    ('electrico', 'Trabajo eléctrico'),
    ('cortes', 'Uso de herramientas cortopunzantes'),
    ('uv', 'Exposición a radiación UV'),
    ('ruido', 'Exposición a ruido'),
    ('quimicas', 'Manejo de sustancias químicas'),
    ('orden_aseo', 'Orden y aseo'),
]


def preset(pid):
    return PRESETS.get((pid or '').strip().lower())
