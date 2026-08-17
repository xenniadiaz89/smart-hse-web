"""Catálogo semilla del GRD (Gestión de Riesgos de Desastres) — extraído del Excel oficial
"Identificación, evaluación y medidas de control GRD v2.0". Amenazas genéricas del estándar SUSESO
y sus preguntas de evaluación. Versionado aquí para no depender del Excel externo en runtime."""

AMENAZAS_BASE = [
    {
        'codigo': 'AG_01',
        'nombre': 'Sismos',
        'descripcion': 'Movimiento de la superficie terrestre, debido principalmente al roce de placas tectónicas, fallas geológicas o volcanismo.',
        'preguntas': [
            {'codigo': 'AG_01.1', 'texto': '¿Se verifica periódicamente el estado estructural de las instalaciones ante la ocurrencia de sismos (por ejemplo: que no hayan grietas o fisuras en las partes estructurales de la edificación como cornisas, pilares - materiales de construcción susceptibles a sismos como adobe, vidrios, otros)?'},
            {'codigo': 'AG_01.2', 'texto': '¿Se encuentran asegurados ante posibles caídas todos los elementos (por ejemplo: repisas, casilleros, insumos, luminarias, adornos, entre otros) que podrían caer en caso de sismos?'},
            {'codigo': 'AG_01.3', 'texto': '¿Se encuentran definidas e identificadas las vías de evacuación, salidas de emergencia y zonas de seguridad (por ejemplo: con señalización, demarcaciones en pisos y muros) y la identificación de estas zonas, es conocida y comprendida por todas las personas trabajadoras?'},
            {'codigo': 'AG_01.4', 'texto': '¿Se encuentran disponibles planos o croquis de evacuación y de recursos para la respuesta a emergencias y estos están en lugares visibles y comprensibles por todas las personas trabajadoras en cada área?'},
            {'codigo': 'AG_01.5', 'texto': '¿El centro de trabajo cuenta con salidas de emergencias con puertas de apertura en sentido de la evacuación y con sistema de cierre que facilita su apertura (solo entornadas)?'},
            {'codigo': 'AG_01.6', 'texto': '¿Tienen identificadas a las personas trabajadoras con movilidad reducida, se designaron a los responsables de apoyarlos en caso de una evacuación y se implementaron los dispositivos que facilitan esta tarea?'},
            {'codigo': 'AG_01.7', 'texto': '¿Se ejecutan en los plazos establecidos los simulacros o prácticas de evacuación en caso de sismos?'},
            {'codigo': 'AG_01.8', 'texto': '¿Las zonas de seguridad del centro de trabajo se ubican fuera de áreas de riesgos inminentes (por ej. caída de vidrios o materiales cercanos al tendido eléctrico, árboles con ramas que puedan desprenderse o panderetas que pudiesen colapsar, entre otros)?'},
            {'codigo': 'AG_01.9', 'texto': '¿Las zonas de seguridad del centro de trabajo se encuentran siempre despejadas, libres de obstáculos y elementos que podrían afectar a las personas trabajadoras durante un proceso de evacuación o al encontrarse en ellas?'},
            {'codigo': 'AG_01.10', 'texto': '¿Se cuenta con un programa de mantenimiento de los equipos y dispositivos de respuesta a emergencias del centro de trabajo?'},
            {'codigo': 'AG_01.11', 'texto': '¿El centro de trabajo cuenta con un sistema de iluminación de emergencia en las vías de evacuación, puertas de salidas de emergencia, sectores de escaleras, cambio de dirección de la vía de evacuación y en las zonas de seguridad?'},
            {'codigo': 'AG_01.12', 'texto': '¿Se realizan mantenciones preventivas al sistema de iluminación de emergencia?'},
            {'codigo': 'AG_01.13', 'texto': '¿Todas las personas trabajadoras (tanto directos como indirectos) que laboran en el centro de trabajo han sido capacitados respecto al plan de respuesta del centro de trabajo?'},
        ],
    },
    {
        'codigo': 'AG_02',
        'nombre': 'Incendio estructural',
        'descripcion': 'Fuego de grandes proporciones que afecta a la infraestructura, equipos, maquinarias, entre otros en el centro de trabajo.',
        'preguntas': [
            {'codigo': 'AG_02.1', 'texto': '¿Se cuenta con un procedimiento de orden y aseo de las instalaciones del centro de trabajo, que regule la forma de almacenar desechos y materiales inflamables o combustibles cerca de fuentes de calor?'},
            {'codigo': 'AG_02.2', 'texto': '¿Se encuentra señalizada la prohibición de fumar en las áreas de trabajo?, y en aquellas debidamente autorizadas para fumadores ¿Se cuenta con recipientes para apagar y disponer las colillas de los cigarrillos?'},
            {'codigo': 'AG_02.3', 'texto': '¿El centro de trabajo cuenta con las instalaciones eléctricas certificadas ante la Superintendencia de Electricidad y Combustibles (SEC)?'},
            {'codigo': 'AG_02.4', 'texto': '¿El centro de trabajo cuenta con extintores portátiles de incendio del tipo adecuado a los materiales combustibles o inflamables que se manipulen? Y ¿estos se encuentran certificados, ubicados en sitios de fácil acceso, claramente identificados y libres de cualquier obstáculo?'},
            {'codigo': 'AG_02.5', 'texto': '¿Todas las personas trabajadoras del centro de trabajo, se encuentran instruidos y entrenados en el uso de extintores portátiles en caso de emergencias?'},
            {'codigo': 'AG_02.6', 'texto': 'Si el centro de trabajo tiene 5 o más pisos, con carga de ocupación superior a 200 personas, ¿cuenta con un sistema automático para detectar oportunamente cualquier principio de incendio y un sistema de alarma que permita alertar a las personas?'},
            {'codigo': 'AG_02.7', 'texto': 'Si el centro de trabajo corresponde a un hospital, comercio, escuela, industria, edificio público, deportivo, entre otros para mismo efecto, o bien, tiene 3 o más pisos, ¿cuenta con un sistema de red húmeda contra fuegos incipientes?'},
            {'codigo': 'AG_02.8', 'texto': 'Si el centro de trabajo tiene 5 o más pisos, ¿cuenta con la instalación de una red seca para agua independiente de la red de distribución de agua de consumo, de uso exclusivo de bomberos y con salida en todos los pisos?'},
            {'codigo': 'AG_02.9', 'texto': 'Si el centro de trabajo cuenta con 16 o más pisos de altura, ¿dispone de un sistema de alimentación eléctrica sin tensión (red inerte), para uso exclusivo de bomberos, que cuenta con una entrada en la fachada exterior del edificio y con salidas en cada piso?'},
            {'codigo': 'AG_02.10', 'texto': '¿Las redes húmedas, redes secas y extintores se encuentran señalizados en cada piso del centro de trabajo?'},
            {'codigo': 'AG_02.11', 'texto': '¿Se cuenta con un procedimiento para la autorización y control de los trabajos en caliente (por ej. soldadura, corte y desbaste, oxicorte, equipos con llama abierta, entre otros)?'},
            {'codigo': 'AG_02.12', 'texto': '¿Las instalaciones eléctricas del centro de trabajo se encuentran en buenas condiciones respecto a canalización, protecciones, enchufes, otros?'},
            {'codigo': 'AG_02.13', 'texto': '¿Se verifica la ausencia de sobrecargas del sistema eléctrico?'},
            {'codigo': 'AG_02.14', 'texto': '¿Se encuentran certificadas por SEC (Superintendencia de Electricidad y Combustible) las extensiones eléctricas utilizadas en el lugar de trabajo?'},
            {'codigo': 'AG_02.15', 'texto': '¿Se verifica que las extensiones eléctricas se utilizan sin sobrecargar la potencia máxima para la que se encuentra diseñada?'},
            {'codigo': 'AG_02.16', 'texto': '¿Se realizan mantenciones preventivas al grupo electrógeno del centro de trabajo?'},
            {'codigo': 'AG_02.17', 'texto': '¿Se realizan mantenciones preventivas a las instalaciones de gas por un instalador autorizado por SEC (Superintendencia de Electricidad y Combustible)?'},
            {'codigo': 'AG_02.18', 'texto': '¿Se cuenta con un programa de inspección para el control de cargas combustibles y fuentes de ignición en las áreas de trabajo?'},
            {'codigo': 'AG_02.19', 'texto': '¿Se realizan mantenciones preventivas a la red húmeda y red seca contra incendios por un profesional competente en la materia?'},
        ],
    },
    {
        'codigo': 'AG_03',
        'nombre': 'Corte de agua',
        'descripcion': 'Interrupción temporal del agua potable, por circunstancias externas al centro de trabajo.',
        'preguntas': [
            {'codigo': 'AG_03.1', 'texto': '¿Se mantienen disponibles los planos de las instalaciones de agua potable (planos guías cañerías) del centro de trabajo?'},
            {'codigo': 'AG_03.2', 'texto': '¿El centro de trabajo cuenta con un plan para mantener el suministro de agua en caso de cortes programados y no programados?'},
        ],
    },
    {
        'codigo': 'AG_04',
        'nombre': 'Corte de energía eléctrica',
        'descripcion': 'Interrupción temporal del suministro de energía eléctrica, por circunstancias externas al centro de trabajo.',
        'preguntas': [
            {'codigo': 'AG_04.1', 'texto': '¿Se mantienen disponibles los planos de las instalaciones eléctricas (planos guías) del centro de trabajo?'},
            {'codigo': 'AG_04.2', 'texto': '¿Las zonas de seguridad y vías de evacuación del centro de trabajo, cuentan con sistema de iluminación de emergencias, en caso de corte del suministro eléctrico?'},
            {'codigo': 'AG_04.3', 'texto': '¿El centro de trabajo cuenta con un plan para mantener el suministro eléctrico en caso de cortes programados y no programados?'},
            {'codigo': 'AG_04.4', 'texto': '¿Se encuentra conectado el sistema de bombas de agua del centro de trabajo al sistema de energía eléctrico de emergencia?'},
        ],
    },
    {
        'codigo': 'AG_05',
        'nombre': 'Asalto/robo',
        'descripcion': 'Intimidación o agresión que ejercen personas externas, con la finalidad de apoderarse de bienes que posee el centro de trabajo o los trabajadores.',
        'preguntas': [
            {'codigo': 'AG_05.1', 'texto': '¿Existe un procedimiento conocido por todas las personas trabajadoras para actuar de manera no temeraria en caso de asaltos o robos en el centro de trabajo?'},
            {'codigo': 'AG_05.2', 'texto': 'En caso de contar con servicio de guardias de seguridad o vigilantes, ¿estos conocen el procedimiento en caso de asaltos y robos?'},
            {'codigo': 'AG_05.3', 'texto': '¿Se cuenta con un programa de retiro de valores del centro de trabajo?'},
        ],
    },
    {
        'codigo': 'AG_06',
        'nombre': 'Accidentes graves/situaciones médicas extremas',
        'descripcion': 'Accidentes o situaciones médicas que ponen en riesgo la vida de los trabajadores del centro de trabajo.',
        'preguntas': [
            {'codigo': 'AG_06.1', 'texto': '¿Se cuenta con un procedimiento de rescate, inmovilización y/o reanimación en caso de accidentes o situaciones médicas extremas?'},
            {'codigo': 'AG_06.2', 'texto': '¿Se cuenta con equipos para rescate, reanimación e inmovilización ante accidentes graves o situaciones médicas extremas de las personas trabajadoras?'},
            {'codigo': 'AG_06.3', 'texto': '¿El centro de trabajo cuenta con personal capacitado y entrenado  para ejecutar maniobras de reanimación e inmovilización?'},
            {'codigo': 'AG_06.4', 'texto': 'Si el centro de trabajo es del rubro de alimentación y/o poseen casino, ¿cuentan con personal entrenado en maniobra de Heimlich (compresión abdominal)?'},
        ],
    },
]

INDEX = {a['codigo']: a for a in AMENAZAS_BASE}

