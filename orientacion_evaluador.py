"""Sugerencias para el evaluador — transcritas del manual oficial "Evaluación de Estándares,
Decreto N°44" de Mutual de Seguridad (Anexo: Orientación para el evaluador).

Dato puro (sin BD ni Flask), mismo estilo que riesgos_isp.py / roles_criticos.py. El manual
organiza su orientación por ESTÁNDAR (ej. 1.1.1, 2.2.1); el catálogo de fuf.py tiene 60 ítems
más granulares por ARTÍCULO del DS 44 (ej. los ítems 2 a 6 citan todos el Art. 7 — MIPER). El
enlace entre ambos catálogos es por artículo: cada bloque de orientación del manual se asocia a
todos los ítems FUF cuyo campo `art` cite el mismo artículo. Los bullets son transcripción
literal del manual (no un resumen propio): es contenido con peso de fiscalización, no se
reinterpreta. Los ítems FUF sin bloque equivalente en el manual no tienen entrada aquí — la
tarjeta simplemente no muestra la caja de sugerencia en vez de inventar contenido.

Estructura: {n_item_fuf: {'descripcion': str, 'requisitos_clave': [str, ...]}}
"""

_MIPER = {
    'descripcion': 'El evaluador verifica la existencia de la MIPER a nivel de Puestos de '
                    'Trabajo, mostrando claramente los peligros y la evaluación de los riesgos '
                    'asociados a los procesos y tareas del puesto de trabajo.',
    'requisitos_clave': [
        'Contiene los elementos mínimos: evaluación de riesgos, magnitud o nivel del riesgo, y '
        'medidas preventivas de control y de emergencia adicionales.',
        'Está disponible en los lugares de trabajo y ha sido informada a las personas '
        'trabajadoras, el Comité Paritario, el Delegado SST, líneas de mando y dirigentes sindicales.',
        'Considera la exposición a riesgos ergonómicos, psicosociales, violencia y acoso, '
        'accidentes y enfermedades profesionales, y programas de vigilancia ocupacional, con '
        'enfoque de género.',
        'La identificación de peligros considera cualquier fuente, situación o entorno con '
        'potencial de causar lesiones, según las características de las personas expuestas.',
        'La evaluación considera condiciones previsibles a futuro y si la persona que ocupa el '
        'puesto puede ser especialmente sensible a alguna de esas condiciones.',
        'El procedimiento de evaluación considera la Guía Técnica del ISP para identificación y '
        'evaluación primaria de riesgos en los ambientes de trabajo.',
        'Se adoptaron medidas preventivas y de emergencia adicionales cuando el riesgo evaluado '
        'sea elevado, alto o grave.',
        'Se revisa al menos anualmente, o cuando cambien las condiciones de trabajo, ocurra un '
        'accidente, se diagnostique una enfermedad profesional o exista riesgo grave e inminente.',
    ],
}

_PROGRAMA_PREVENTIVO = {
    'descripcion': 'El evaluador solicita el programa de trabajo preventivo, elaborado o '
                    'modificado en respuesta a la actualización de la MIPER dentro de 30 días '
                    'corridos.',
    'requisitos_clave': [
        'Medidas preventivas y correctivas, plazos de implementación y responsables de ejecución.',
        'Actividades de promoción para prevenir el consumo de alcohol y drogas, y difusión de '
        'estilos de vida saludables.',
        'Actividades para prevenir riesgos de la conducción de vehículos motorizados cuando corresponda.',
        'Orden de prelación en las medidas preventivas: eliminar, ingenieriles/técnicas, '
        'organizacionales, EPP.',
        'Firmado por el representante legal y difundido a las personas trabajadoras y al Comité Paritario.',
        'Evidencias de capacitación sobre el uso seguro de máquinas, equipos y elementos de '
        'trabajo (lista de asistencia, fechas, nombres, contenido específico).',
        'Evaluación anual del cumplimiento del programa, con eficacia de las acciones e '
        'implementación de mejora continua.',
    ],
}

_EPP = {
    'descripcion': 'El evaluador solicita actas o listas de entrega de EPP, y el procedimiento '
                    'de utilización, mantenimiento, reposición o recambio.',
    'requisitos_clave': [
        'Registros detallados de entrega de EPP: nombre del trabajador, tipo de EPP entregado, '
        'fecha de entrega y firma del trabajador que certifique la recepción.',
        'Procedimiento de utilización, mantenimiento, reposición o recambio, considerando tallas '
        'disponibles para la diversidad de aspectos fisiológicos.',
        'Los elementos y equipos de protección personal cumplen las normas de certificación de '
        'calidad o están registrados en el Instituto de Salud Pública.',
        'Programa de capacitación en uso y mantención de EPP, de al menos una hora cronológica: '
        'partes del elemento, colocación, limitaciones de uso, limpieza, almacenamiento y prueba '
        'de chequeo diario.',
        'Registro de capacitación con actividades teóricas y prácticas, resultados de '
        'evaluaciones de aprendizaje, asistentes, actividades de reforzamiento y relatores.',
    ],
}

_INFORMACION_FORMACION = {
    'descripcion': 'El evaluador solicita el programa de inducción para nuevos trabajadores y el '
                    'programa de capacitación periódica en seguridad y salud en el trabajo.',
    'requisitos_clave': [
        'La inducción incluye: características mínimas del lugar de trabajo, riesgos y medidas '
        'preventivas (incluidas emergencias), procedimientos de trabajo seguro, y características '
        'de productos y sustancias manipuladas.',
        'Registros de asistencia a la inducción inicial: nombre, fecha y firma del trabajador.',
        'El procedimiento de inducción se ejecuta también ante cambio de puesto de trabajo o de '
        'procesos, tecnologías o materiales.',
        'Capacitación de al menos 8 horas cronológicas cada dos años, con enfoque de género, que '
        'incluya factores de riesgo, efectos en la salud, medidas preventivas, prestaciones de la '
        'Ley 16.744, plan de gestión de emergencias, señalética y prevención de incendios.',
    ],
}

_CONSULTA_PARTICIPACION = {
    'descripcion': 'El evaluador solicita el procedimiento que describa los mecanismos de '
                    'consulta y participación de los representantes de los trabajadores ante '
                    'cambios en los procesos o la estructura organizacional.',
    'requisitos_clave': [
        'Mecanismos de consulta previos a la implementación de cambios.',
        'Identificación de los representantes de los trabajadores que participan en la consulta.',
        'Pasos para garantizar la participación activa y la toma de decisiones conjunta.',
        'Actas del Comité Paritario donde se haya discutido la posibilidad de cambios en los '
        'procesos o la estructura organizacional.',
        'Evidencia de que los representantes de las personas trabajadoras promueven su '
        'participación en las actividades de seguridad y salud en el trabajo.',
    ],
}

_RIESGO_GRAVE_INMINENTE = {
    'descripcion': 'El evaluador solicita el procedimiento documentado que explique cómo la '
                    'entidad empleadora comunica de inmediato a los trabajadores un riesgo grave '
                    'e inminente.',
    'requisitos_clave': [
        'Identificación del riesgo, métodos de comunicación y responsables de comunicarlo.',
        'Acciones inmediatas a seguir y medidas adoptadas para eliminar o atenuar el riesgo.',
        'Medidas de suspensión inmediata de las faenas afectadas y evacuación si el riesgo no se '
        'puede eliminar o atenuar.',
        'Registros de las notificaciones entregadas a los trabajadores (escritas o digitales).',
        'Evidencia de medios inmediatos: alarmas, altavoces, carteles informativos, protocolos de '
        'activación de emergencias.',
    ],
}

_PLAN_EMERGENCIA = {
    'descripcion': 'El evaluador solicita el documento del plan de gestión, reducción y '
                    'respuesta de riesgos en caso de emergencias, catástrofes o desastres.',
    'requisitos_clave': [
        'Identificación de riesgos potenciales internos y externos (incendios, terremotos, '
        'derrames químicos, explosiones, etc.).',
        'Medidas de reducción de riesgos y acciones de respuesta, incluyendo evacuación y '
        'protección de los trabajadores.',
        'Asignación de responsabilidades y equipo de emergencia.',
        'Capacitación sobre los riesgos de emergencia y los procedimientos de evacuación y traslado.',
        'Elaborado conforme a la guía de reducción del riesgo de desastres de la autoridad competente.',
        'Evidencia de ensayo del plan al menos una vez al año, simulando una emergencia real.',
    ],
}

_COORDINACION = {
    'descripcion': 'El evaluador solicita registros que evidencien la coordinación y cooperación '
                    'entre entidades empleadoras que comparten un mismo lugar de trabajo.',
    'requisitos_clave': [
        'Descripción de los riesgos identificados y medidas preventivas adoptadas, con fecha de '
        'comunicación y firma de los destinatarios.',
        'Actas de las reuniones de coordinación en las que se discutieron los riesgos y las '
        'medidas preventivas adoptadas.',
        'Planes de emergencia, catástrofes o desastres compartidos entre todas las entidades '
        'empleadoras y trabajadores independientes presentes en el lugar de trabajo.',
    ],
}

_SGSST = {
    'descripcion': 'El evaluador solicita el manual del Sistema de Gestión de Seguridad y Salud '
                    'en el Trabajo (SGSST).',
    'requisitos_clave': [
        'Política de seguridad y salud en el trabajo y objetivos del SGSST.',
        'Estructura organizacional y responsabilidades relacionadas con SST.',
        'Procedimientos documentados de identificación de riesgos, evaluación de peligros y '
        'planificación de medidas preventivas y de control.',
        'Programa aprobado y firmado por el representante legal, dado a conocer al Comité '
        'Paritario, al Departamento de Prevención y a las personas trabajadoras.',
        'Evaluaciones o auditorías periódicas del desempeño del SGSST y mecanismos de mejora continua.',
        'Evidencia de certificación (ISO 45001 u otra), cuando corresponda.',
    ],
}

_CPHS_CONSTITUCION = {
    'descripcion': 'El evaluador solicita el acta formal de constitución del Comité Paritario de '
                    'Higiene y Seguridad (CPHS).',
    'requisitos_clave': [
        'Fecha de constitución, nombres y firmas de los integrantes (representantes de los '
        'trabajadores y de la entidad empleadora).',
        'Los representantes de los trabajadores son mayores de edad, saben leer y escribir, y '
        'tienen antigüedad mínima de un año en la entidad.',
        'Los integrantes electos sin curso de orientación lo realizan durante el primer semestre '
        'de su mandato.',
        'Método de elección: voto escrito y secreto, con anticipación no inferior a 5 días a la '
        'fecha de cese del comité anterior.',
        'Registro del acta de constitución en el sitio web de la Dirección del Trabajo dentro de '
        'los 15 días hábiles siguientes a la elección.',
        'Actas de reuniones mensuales, con fechas, participantes, temas tratados y acuerdos alcanzados.',
    ],
}

_CPHS_FUNCIONES = {
    'descripcion': 'El evaluador verifica que el Comité Paritario de Higiene y Seguridad cumple '
                    'las funciones establecidas por el Decreto 44.',
    'requisitos_clave': [
        'Acompaña al experto en prevención o a los Inspectores del Trabajo en visitas y '
        'fiscalizaciones, con acceso libre a los lugares de trabajo.',
        'Asesora e instruye a las personas trabajadoras sobre el uso correcto de los elementos de protección.',
        'Vigila el cumplimiento de las medidas de prevención y seguridad, con revisión de '
        'maquinarias, equipos e instalaciones.',
        'Investiga, con resguardo de la información sensible, las causas de accidentes y '
        'enfermedades profesionales.',
        'Efectúa reuniones extraordinarias ante accidente fatal o grave, o riesgo grave e inminente.',
        'Informa por escrito a la entidad empleadora cuando detecte un riesgo grave e inminente.',
        'Los acuerdos del CPHS se comunican por escrito a la entidad empleadora.',
    ],
}

_DPR = {
    'descripcion': 'El evaluador solicita los informes elaborados por el Departamento de '
                    'Prevención de Riesgos y verifica el cumplimiento de sus funciones.',
    'requisitos_clave': [
        'Informes que demuestren la autonomía técnica del experto en la evaluación y gestión de riesgos.',
        'Evaluación de riesgos por área, recomendaciones técnicas, medidas implementadas y plan '
        'de prevención aprobado.',
        'Registro de todos los incidentes o sucesos peligrosos (lugar, fecha, hora, personas '
        'involucradas, causas, acciones correctivas).',
        'Registro de todos los accidentes del trabajo, de trayecto y enfermedades profesionales '
        '(fecha, nombre, sexo, lugar, descripción y relato de los hechos).',
        'Registro actualizado de las personas trabajadoras en vigilancia de la salud.',
        'El Departamento está dirigido por un experto de la categoría y dedicación que '
        'corresponde según el N° de trabajadores y la cotización genérica.',
        'CV del experto con al menos 12 meses de experiencia en los últimos tres años.',
    ],
}

_REGLAMENTO_INTERNO = {
    'descripcion': 'El evaluador solicita el Reglamento Interno de Higiene y Seguridad, '
                    'actualizado y vigente, y verifica su contenido mínimo según el artículo 58 '
                    'del Decreto 44.',
    'requisitos_clave': [
        'Normas y procedimientos de higiene y seguridad, y derechos/obligaciones de trabajadores '
        'y entidad empleadora.',
        'Registro de entrega gratuita del Reglamento a cada trabajador, con fecha y firma.',
        'Constancia de ingreso del Reglamento (o sus modificaciones) a la SEREMI de Salud y la '
        'Dirección del Trabajo.',
        'Acta de reunión con el Comité Paritario/Delegado y organizaciones sindicales donde se '
        'sometió a consideración el Reglamento.',
        'Revisiones anuales del Reglamento Interno.',
        'Contenido mínimo: preámbulo, disposiciones generales, procedimientos de exámenes '
        'médicos, notificación de accidentes, EPP, riesgo grave e inminente, plan de emergencia, '
        'reclamos, obligaciones, prohibiciones, sanciones y protocolos de prevención del acoso '
        'sexual/laboral y violencia en el trabajo.',
    ],
}

_MAPAS_RIESGO = {
    'descripcion': 'El evaluador solicita copia de los mapas de riesgos de las distintas '
                    'dependencias de la entidad empleadora.',
    'requisitos_clave': [
        'Ubicación en lugar visible y descripción de los riesgos identificados en las distintas áreas.',
        'Leyendas y símbolos que permitan identificar claramente el tipo de riesgo.',
        'Fecha de actualización coherente con la MIPER y las condiciones actuales.',
    ],
}

_GESTION_MENOR_TAMANO = {
    'descripcion': 'El evaluador solicita la política de seguridad y salud en el trabajo y '
                    'verifica la identificación y evaluación de condiciones ambientales, '
                    'psicosociales y ergonómicas de la entidad de hasta 25 trabajadores.',
    'requisitos_clave': [
        'Política firmada por el representante legal, con compromiso de protección de la vida y '
        'salud, cumplimiento normativo y mejora continua.',
        'Informe de la herramienta de autoevaluación de riesgos críticos de Mutual de Seguridad.',
        'MIPER con el formato del organismo administrador, revisada anualmente o ante cambios/accidentes.',
        'Programa Preventivo basado en la MIPER, con acciones y medidas preventivas/correctivas.',
    ],
}

_ENCARGADO_HASTA_100 = {
    'descripcion': 'El evaluador solicita el certificado de capacitación en gestión de riesgos '
                    'del representante legal o de la persona designada, para entidades de hasta '
                    '100 trabajadores.',
    'requisitos_clave': [
        'Certificado de capacitación emitido por la Mutual de Seguridad (nombre, fecha, curso y '
        'firma de la entidad capacitadora).',
        'Registro de las actividades de colaboración de la persona capacitada (fecha, '
        'descripción, resultado y firma del responsable).',
    ],
}

_DELEGADO_SST = {
    'descripcion': 'El evaluador solicita copia del acta de elección del Delegado de Seguridad y '
                    'Salud en el Trabajo, en faenas de 10 a 25 trabajadores sin Comité Paritario.',
    'requisitos_clave': [
        'Acta con fecha de elección, nombres de participantes, nombre del delegado elegido, '
        'método de elección y firmas.',
        'Registro de las actividades del Delegado en la implementación del instrumento '
        'preventivo (fecha, actividades, resultados y firma).',
    ],
}

_VIGILANCIA_SALUD = {
    'descripcion': 'El evaluador solicita el listado de trabajadores en programa de vigilancia '
                    'ambiental y de salud, según las evaluaciones realizadas.',
    'requisitos_clave': [
        'Registro por tipo de agente, fecha de recepción, nombre completo, RUT y fecha de reevaluación.',
        'Resoluciones de Calificación (RECA) de los casos identificados como enfermedad profesional.',
        'Autorización a las personas trabajadoras para asistir a citaciones de exámenes de '
        'control del organismo administrador.',
    ],
}

_TRASLADO_PRESCRIPCION = {
    'descripcion': 'El evaluador solicita el documento con las medidas prescritas por el '
                    'organismo administrador o los fiscalizadores para el control del riesgo.',
    'requisitos_clave': [
        'Documento de Mutual de Seguridad con las medidas necesarias, justificación técnica y '
        'firma del profesional responsable.',
        'Documento del organismo fiscalizador que ordena la implementación de las medidas.',
        'Informe de verificación de cumplimiento, con fecha de implementación y evaluación de efectividad.',
        'Evidencias fotográficas o documentales de la implementación de las medidas sugeridas.',
    ],
}

_INVESTIGACION_CAUSAS = {
    'descripcion': 'El evaluador solicita el procedimiento de investigación de accidentes '
                    'laborales, incidentes peligrosos y enfermedades profesionales.',
    'requisitos_clave': [
        'Criterios de investigación con enfoque de género y metodología indicada por Mutual de Seguridad.',
        'Instancias de participación de los trabajadores y sus representantes durante la investigación.',
        'Listado de accidentes/incidentes peligrosos y sus informes de investigación: descripción, '
        'fecha, lugar, causas, acciones preventivas/correctivas y participación de los trabajadores.',
    ],
}

_REGISTRO_ESTADISTICAS = {
    'descripcion': 'El evaluador solicita ejemplos de registros electrónicos de la gestión de '
                    'riesgos laborales y las estadísticas de seguridad y salud.',
    'requisitos_clave': [
        'Registros electrónicos: MIPER, auditorías de seguridad, informes de investigación, '
        'capacitaciones con listas de asistencia, medidas preventivas y correctivas implementadas.',
        'Tasa de accidentabilidad: N° de accidentados por cada cien trabajadores en el período, x100.',
        'Tasa mensual de frecuencia: N° de lesionados por millón de horas-hombre trabajadas.',
        'Tasa semestral de gravedad: N° de días de ausencia laboral de los lesionados por millón '
        'de horas-hombre, sumando los días cargo de las tablas del ISP para incapacidades '
        'permanentes y muertes.',
        'Registros diferenciados por sexo: exposición a agentes/factores de riesgo, accidentes y '
        'enfermedades profesionales, y personas en vigilancia de la salud.',
    ],
}

_ESTADISTICAS_SIN_DPR = {
    'descripcion': 'Para entidades no obligadas a contar con Departamento de Prevención de '
                    'Riesgos, el evaluador solicita el registro de la tasa anual de '
                    'accidentabilidad y de todos los accidentes/enfermedades profesionales.',
    'requisitos_clave': [
        'Tasa anual de accidentabilidad por accidentes del trabajo.',
        'Registro de todos los accidentes del trabajo, de trayecto y enfermedades profesionales, '
        'indicando nombre, sexo, lugar y descripción del accidente y el relato de los hechos.',
    ],
}

# n° de ítem FUF (fuf.py) -> bloque de orientación. Varios ítems comparten bloque cuando el
# manual cubre, bajo un mismo estándar, todo lo que en fuf.py está desglosado en más ítems.
ORIENTACION = {
    1: _SGSST,
    2: _MIPER, 3: _MIPER, 4: _MIPER, 5: _MIPER, 6: _MIPER,
    7: _GESTION_MENOR_TAMANO,
    8: _PROGRAMA_PREVENTIVO, 9: _PROGRAMA_PREVENTIVO, 10: _PROGRAMA_PREVENTIVO,
    11: _PROGRAMA_PREVENTIVO, 12: _PROGRAMA_PREVENTIVO, 13: _PROGRAMA_PREVENTIVO,
    14: _EPP, 15: _EPP, 16: _EPP, 17: _EPP, 18: _EPP, 19: _EPP,
    20: _PROGRAMA_PREVENTIVO,
    21: _INFORMACION_FORMACION, 22: _INFORMACION_FORMACION,
    23: _INFORMACION_FORMACION, 24: _INFORMACION_FORMACION,
    25: _CONSULTA_PARTICIPACION,
    26: _RIESGO_GRAVE_INMINENTE,
    27: _PLAN_EMERGENCIA, 28: _PLAN_EMERGENCIA,
    29: _COORDINACION,
    30: _CPHS_CONSTITUCION, 31: _CPHS_CONSTITUCION, 32: _CPHS_CONSTITUCION, 33: _CPHS_CONSTITUCION,
    34: _CPHS_FUNCIONES, 35: _CPHS_FUNCIONES, 36: _CPHS_FUNCIONES,
    37: _CPHS_FUNCIONES, 38: _CPHS_FUNCIONES,
    39: _DELEGADO_SST, 40: _DELEGADO_SST,
    41: _DPR, 42: _DPR, 43: _DPR, 44: _DPR, 45: _DPR, 46: _DPR,
    47: _ESTADISTICAS_SIN_DPR,
    48: _ENCARGADO_HASTA_100,
    49: _REGLAMENTO_INTERNO, 50: _REGLAMENTO_INTERNO,
    51: _REGLAMENTO_INTERNO, 52: _REGLAMENTO_INTERNO,
    53: _MAPAS_RIESGO,
    54: _VIGILANCIA_SALUD, 55: _VIGILANCIA_SALUD, 56: _VIGILANCIA_SALUD,
    57: _TRASLADO_PRESCRIPCION, 58: _TRASLADO_PRESCRIPCION,
    59: _INVESTIGACION_CAUSAS,
    60: _REGISTRO_ESTADISTICAS,
}
