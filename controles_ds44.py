"""Controles operacionales sugeridos por riesgo (código del Anexo 2), adaptados al D.S. 44.

QUÉ ES Y QUÉ NO ES ESTO
-----------------------
Son BORRADORES editables, no medidas cerradas. El sistema los propone; el prevencionista los
revisa, ajusta a su faena y firma. Mismo criterio que el Plan de Emergencias: la app propone, el
experto valida. La UI los marca como propuesta y obliga a revisarlos.

FUENTE
------
Adaptados y generalizados al D.S. 44 desde:
- El catálogo de Riesgos de Fatalidad + Controles Críticos aportado por el usuario (Codelco),
  DESPOJADO de lo minero exclusivo (roca, tronadura, piques, ferroviario, material fundido) y de
  su nomenclatura de marca (RC##, CCP#, CCM#).
- Estándares transversales: D.S. 594 (condiciones sanitarias/ambientales), D.S. 63 y Ley 20.001
  (manejo manual de cargas), protocolos MINSAL (PREXOR, PLANESI, TMERT, RUV, CEAL-SM/SUSESO),
  guías del ISP.

Cobertura parcial a propósito: solo los riesgos con base real. Un código ausente aquí devuelve
None → el control lo escribe el experto (campo vacío y obligatorio en el panel). NO se inventan
medidas donde no hay fuente.

Formato: lista de acciones. El panel/servidor las convierte a '1.\\n2.\\n' con
formato.normalizar_control_operativo. Aquí van como lista para mantenerlas legibles y editables.
"""

# Familias del Anexo 2 que comparten cuerpo de control (evita duplicar 4× eléctrico, 7× postural).
_ELECTRICO = [
    'Identificación y corte efectivo de todas las fuentes de energía antes de intervenir',
    'Aislación, bloqueo y señalización de elementos de maniobra (procedimiento de bloqueo)',
    'Verificación de ausencia de tensión e instalación de puesta a tierra',
    'Uso de herramientas y equipos portátiles conectados a tableros autorizados y protegidos',
    'Personal competente y autorizado para intervención eléctrica',
    'EPP dieléctrico según nivel de tensión y respuesta ante urgencia médica',
]
_POSTURAL = [
    'Evaluación del puesto con la metodología TMERT-EESS (Res. Exenta MINSAL)',
    'Rediseño ergonómico del puesto: alturas, alcances y apoyos adecuados a la tarea',
    'Pausas activas y rotación de tareas para limitar el tiempo en la postura forzada',
    'Capacitación en higiene postural y autocuidado musculoesquelético',
]
_AGENTE_QUIMICO = [
    'Identificación, clasificación y señalización de las sustancias (Hoja de Datos de Seguridad)',
    'Control en la fuente: encierro, ventilación/extracción localizada según el agente',
    'Monitoreo de la exposición contra los límites permisibles del D.S. 594',
    'EPP respiratorio/dérmico específico y programa de vigilancia de salud del OAL',
]

CONTROLES = {
    # ── Caídas ──
    'A1': ['Programa de orden y limpieza (5S): vías despejadas y superficies libres de obstáculos',
           'Señalización de pisos mojados o desnivelados y limpieza inmediata de derrames',
           'Calzado de seguridad antideslizante e iluminación adecuada de tránsito'],
    'A2': ['Barandas, rodapiés y protección de aberturas y desniveles',
           'Escaleras y rampas normalizadas, con pasamanos y en buen estado',
           'Señalización y control de acceso a los desniveles'],
    'A3': ['Capacitación y entrenamiento para trabajo en altura (sobre 1,8 m)',
           'Condición de salud física y mental compatible con el trabajo en altura',
           'Plataformas de trabajo, andamios y puntos de anclaje certificados y mantenidos',
           'Sistema personal de detención de caídas (arnés, línea de vida) y su inspección',
           'Control de acceso, segregación del área y plan de rescate en altura'],
    'A4': ['Segregación y protección de bordes en trabajos sobre o junto al agua',
           'Chaleco salvavidas y elementos de flotación/rescate disponibles',
           'Trabajador acompañado y plan de rescate acuático'],
    # ── Contacto con objetos ──
    'B1': ['Guardas y protecciones fijas en las partes móviles de equipos y máquinas',
           'Bloqueo y verificación de energía cero (LOTO) antes de intervenir',
           'Competencias del personal que interactúa con equipos de partes móviles',
           'Parada de emergencia operativa y accesible'],
    'B2': ['Planificación y autorización de trabajos en la vertical (niveles superpuestos)',
           'Segregación y señalización de los niveles inferiores',
           'Sujeción y contención de herramientas y materiales en altura',
           'Casco de seguridad y control de acceso bajo la zona de trabajo'],
    'B3': ['Uso de herramientas cortopunzantes adecuadas, en buen estado y con resguardo',
           'Guantes anticorte y técnica de corte alejando el cuerpo',
           'Descarte seguro de elementos cortopunzantes en contenedores rígidos'],
    'B4': ['Ordenamiento y señalización de estructuras y objetos fijos en zonas de tránsito',
           'Iluminación y demarcación de pasillos y puntos de golpe',
           'EPP (casco) donde exista riesgo de choque contra estructuras'],
    # ── Térmicos ──
    'E1': ['Aislación y señalización de superficies y equipos calientes',
           'EPP para contacto con calor (guantes, ropa) y procedimiento de manipulación',
           'Respuesta ante quemaduras y urgencia médica'],
    'E2': ['Aislación y señalización de superficies y sustancias muy frías (criogénicas)',
           'EPP para contacto con frío y procedimiento de manipulación',
           'Respuesta ante lesiones por frío'],
    # ── Eléctrico (F1-F4 comparten cuerpo) ──
    'F1': _ELECTRICO, 'F2': _ELECTRICO, 'F3': _ELECTRICO, 'F4': _ELECTRICO,
    # ── Sustancias químicas (contacto) ──
    'G1': ['Identificación, clasificación y señalización de sustancias cáusticas/corrosivas (HDS)',
           'Contención, ventilación y control de acceso en el manejo',
           'EPP dérmico/ocular específico y duchas/lavaojos de emergencia',
           'Respuesta ante contacto y urgencia médica'],
    'G2': ['Identificación y HDS de las sustancias químicas manipuladas',
           'Almacenamiento por compatibilidad y contención de derrames',
           'EPP específico y respuesta ante emergencias químicas'],
    # ── Explosión / proyección (genéricas, sin la tronadura minera) ──
    'H1': ['Control de fuentes de ignición y de atmósferas explosivas',
           'Almacenamiento, separación y manipulación segura de inflamables y comburentes',
           'Segregación, control de acceso y respuesta ante emergencia'],
    'H2': ['Guardas y pantallas de contención de fragmentos y partículas',
           'EPP ocular y facial certificado según la energía de proyección',
           'Segregación del área de proyección'],
    # ── Vehículos ──
    'I1': ['Segregación peatón-vehículo y vías/zonas peatonales demarcadas',
           'Contacto visual, chaleco reflectante y reglas de circulación',
           'Alarmas de retroceso y control de puntos ciegos'],
    'I2': ['Vehículo certificado y mantenido, con sistemas de seguridad operativos',
           'Conductor competente, autorizado y con licencia vigente',
           'Gestión de tránsito, rutas, velocidad y distancias',
           'Check-list preuso, cinturón, prohibición de celular y gestión de la fatiga'],
    # ── Incendios ──
    'J': ['Identificación de áreas críticas (almacenamiento, zonas inflamables)',
          'Control de trabajos en caliente (soldadura, oxicorte) con permiso y vigía',
          'Detección de incendio y equipos de extinción operativos y señalizados',
          'Plan de respuesta y evacuación ante incendio'],
    # ── Atmósferas / tóxicos ──
    'K1': ['Identificación y clasificación de espacios confinados',
           'Medición y monitoreo de oxígeno, toxicidad y explosividad antes y durante',
           'Ventilación, bloqueo de energías/fluidos y permiso de trabajo',
           'Vigía externo, equipo de respiración y plan de rescate'],
    'K2': _AGENTE_QUIMICO,
    # ── Radiaciones ──
    'L1': ['Gestión de la exposición a radiación UV/no ionizante (sombra, horarios críticos)',
           'Bloqueador solar FPS 50+, ropa de manga larga, gorro legionario y lentes UV',
           'Difusión del protocolo RUV (radiación ultravioleta de origen solar) del MINSAL'],
    'L2': ['Blindaje, distancia y limitación del tiempo de exposición (protección radiológica)',
           'Dosimetría personal y control por autoridad competente',
           'Señalización y control de acceso a zonas con radiación ionizante'],
    # ── Higiénicos (agentes químicos O1-O3 comparten cuerpo) ──
    'O1': _AGENTE_QUIMICO, 'O2': _AGENTE_QUIMICO, 'O3': _AGENTE_QUIMICO,
    'P1': ['Evaluación de la exposición a ruido y programa PREXOR del MINSAL',
           'Control en la fuente (encierro, silenciadores) y en el medio',
           'Protección auditiva certificada y vigilancia audiométrica del OAL'],
    'P2': ['Evaluación de la exposición a vibración (mano-brazo o cuerpo completo)',
           'Mantención de equipos, asientos amortiguados y limitación del tiempo de exposición',
           'Vigilancia de salud de las personas expuestas'],
    'P4': ['Gestión de la exposición a radiación no ionizante (sombra, horarios críticos)',
           'Bloqueador FPS 50+, ropa de manga larga, gorro legionario y lentes UV',
           'Difusión del protocolo RUV del MINSAL'],
    'P5': ['Evaluación del estrés térmico por calor y aclimatación del personal',
           'Hidratación, sombra, pausas y ajuste de la jornada en horas críticas',
           'Vigilancia de signos de golpe de calor'],
    'P6': ['Evaluación de la exposición a frío y ropa térmica adecuada',
           'Pausas en zonas temperadas e hidratación con líquidos calientes',
           'Vigilancia de signos de hipotermia'],
    'Q1': ['Precauciones estándar frente a sangre y fluidos corporales',
           'EPP de barrera y manejo seguro de cortopunzantes',
           'Protocolo post-exposición y vacunación cuando corresponda'],
    'Q2': ['Ventilación, higiene de manos y protocolo frente a agentes de transmisión aérea/contacto',
           'EPP respiratorio según el agente y vigilancia de salud',
           'Aislamiento de casos y limpieza/desinfección de superficies'],
    # ── Músculo-esqueléticos ──
    'R1': ['Evaluación del manejo manual de cargas (Ley 20.001 / D.S. 63 / guía MINSAL)',
           'Ayudas mecánicas y reducción del peso y la frecuencia de manipulación',
           'Límites de carga y técnica correcta de levantamiento',
           'Capacitación en manejo manual de cargas'],
    'R2': ['Evaluación del manejo/movilización de personas y ayudas mecánicas (grúas, sábanas)',
           'Rediseño de la tarea y trabajo en pareja cuando corresponda',
           'Capacitación en movilización segura de pacientes'],
    'S1': ['Evaluación del trabajo repetitivo de extremidad superior (TMERT-EESS)',
           'Rediseño del ciclo de trabajo, herramientas y ritmo',
           'Pausas activas y rotación de tareas'],
    'T1': _POSTURAL, 'T2': _POSTURAL, 'T3': _POSTURAL, 'T4': _POSTURAL,
    'T5': _POSTURAL, 'T6': _POSTURAL, 'T7': _POSTURAL,
    # ── Psicosociales (Anexo 2 D1-D5; controles del protocolo CEAL-SM/SUSESO + Ley Karin) ──
    'D1': ['Evaluación del riesgo psicosocial con el cuestionario CEAL-SM/SUSESO',
           'Ajuste de cargas de trabajo, plazos y exigencias emocionales',
           'Plan de intervención sobre las dimensiones en riesgo y su seguimiento'],
    'D2': ['Promover autonomía, desarrollo de habilidades y participación en las decisiones del trabajo',
           'Definición clara de roles y sentido de la tarea',
           'Planes de capacitación y desarrollo'],
    'D3': ['Fortalecer el apoyo social, el compañerismo y la calidad del liderazgo',
           'Canales de comunicación y de resolución de conflictos',
           'Formación de jefaturas en habilidades de liderazgo y buen trato'],
    'D4': ['Revisión de compensaciones, estabilidad y reconocimiento del trabajo',
           'Claridad y respeto de las condiciones contractuales',
           'Reconocimiento del desempeño'],
    'D5': ['Medidas de conciliación trabajo-vida (doble presencia): horarios y permisos',
           'Respeto de jornadas, descansos y períodos de vacaciones',
           'Corresponsabilidad y flexibilidad según la normativa vigente'],
    # Ausentes a propósito (sin fuente transversal clara): A-N residuales C1/C2/M/N,
    # radiaciones P3, presiones P7/P8, aerosoles vs O ya cubiertos. Devuelven None → los escribe el experto.
}


def controles(codigo):
    """Lista de controles sugeridos para un riesgo del Anexo 2, o None si no hay base.
    None significa 'que lo escriba el experto', nunca 'invéntalo'."""
    return CONTROLES.get((codigo or '').strip().upper())
