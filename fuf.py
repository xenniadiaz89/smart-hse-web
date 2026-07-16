"""Catálogo del FUF — Formulario Único de Fiscalización del D.S. 44/2024.

Los 60 ítems con que se autoevalúa el cumplimiento legal de todo empleador (base Ley 16.744).
Dato puro, como cumplimiento.REQUISITOS_CORE: no es Blueprint ni toca la BD. Los estados por
empresa viven en la tabla fuf_estado (models.FufEstado); aquí solo está el enunciado.

FUENTE ÚNICA DE VERDAD: hasta la Ronda 24 este catálogo estaba duplicado —hardcodeado en el
JavaScript de templates/dashboard.html y como constante ciega FUF_TOTAL=60 en app.py—. Ahora
el dashboard lo recibe desde aquí vía `{{ fuf_catalogo | tojson }}` y el total se calcula.

Estructura de un ítem:  {'n': 1, 't': '<enunciado>', 'art': '<artículo del DS 44>'}
Los estados posibles por ítem son 'pendiente' | 'si' | 'no' | 'na' (ver app.api_fuf_guardar).
"""

SECCIONES = [
    {'seccion': 'Sistema de Gestión de Seguridad y Salud en el Trabajo (SGSST)',
     'organismo': 'SUSESO / Mutual',
     'items': [
         {'n': 1, 't': 'Cuenta con un SGSST que contiene al menos: a) Política de SST; b) estructura organizacional para la gestión preventiva; c) diagnóstico, planificación y programación; d) evaluación o auditoría periódica del desempeño; e) acción de mejora continua o correctiva.',
          'art': 'DS 44/2024 Art. 22 inc.1 y 64 inc.1'},
     ]},
    {'seccion': 'Identificación de peligros y evaluación de riesgos',
     'organismo': 'SUSESO / Mutual',
     'items': [
         {'n': 2, 't': 'Cuenta con Matriz de Identificación de Peligros y Evaluación de Riesgos (MIPER) que incorpore todos los procesos, tareas y puestos de trabajo.',
          'art': 'DS 44/2024 Art. 7 inc.1'},
         {'n': 3, 't': 'La MIPER considera la exposición a todos los agentes y factores de riesgo (ergonómicos, psicosociales, violencia y acoso, accidentes y EP, vigilancia ocupacional, con enfoque de género).',
          'art': 'DS 44/2024 Art. 7 inc.2'},
         {'n': 4, 't': 'La MIPER está disponible en los lugares de trabajo e informada a trabajadores, comité paritario, delegado SST, dirigentes sindicales y línea de mando.',
          'art': 'DS 44/2024 Art. 7 inc.9'},
         {'n': 5, 't': 'La MIPER contiene los elementos mínimos: a) identificación de peligros; b) evaluación de riesgos; c) magnitud o nivel de riesgo; d) medidas preventivas de control y de emergencia.',
          'art': 'DS 44/2024 Art. 7 inc.3'},
         {'n': 6, 't': 'La MIPER tiene fecha de elaboración y se revisa al menos anualmente o cuando cambian las condiciones, ocurre un accidente, se diagnostica una EP o hay riesgo grave e inminente.',
          'art': 'DS 44/2024 Art. 7 inc.9 y 64 inc.2'},
         {'n': 7, 't': 'La entidad de hasta 25 trabajadores identifica y evalúa condiciones ambientales, psicosociales y ergonómicas y el cumplimiento normativo con el instrumento de autoevaluación del Organismo Administrador Ley 16.744.',
          'art': 'DS 44/2024 Art. 64 inc.1'},
     ]},
    {'seccion': 'Programa de Trabajo en Prevención de Riesgos Laborales',
     'organismo': 'SUSESO / Mutual',
     'items': [
         {'n': 8, 't': 'Cuenta con el programa de trabajo preventivo confeccionado o actualizado a partir de la MIPER dentro de 30 días corridos.',
          'art': 'DS 44/2024 Art. 8 inc.1'},
         {'n': 9, 't': 'El programa de trabajo preventivo está por escrito y aprobado por el representante legal.',
          'art': 'DS 44/2024 Art. 8 inc.1'},
         {'n': 10, 't': 'El programa contiene: a) medidas preventivas y correctivas según MIPER; b) plazos; c) responsables; d) prevención de alcohol y drogas; e) vida y alimentación saludable; f) conducción de vehículos cuando corresponda; g) fechas de modificación y aprobación.',
          'art': 'DS 44/2024 Art. 8 inc.1, 2 y 3'},
         {'n': 11, 't': 'El programa de trabajo preventivo ha sido difundido en los lugares de trabajo y se remitió un ejemplar al Comité Paritario.',
          'art': 'DS 44/2024 Art. 8 inc.3'},
         {'n': 12, 't': 'Sobre máquinas, equipos y elementos de trabajo: a) informa riesgos y manejo seguro; b) informa manuales/fichas técnicas; c) cuenta con procedimiento de trabajo seguro; d) informa y capacita su uso correcto.',
          'art': 'DS 44/2024 Art. 10 inc.1 y 2'},
         {'n': 13, 't': 'Se adoptan medidas según la prelación, privilegiando la protección colectiva por sobre el uso de EPP.',
          'art': 'DS 44/2024 Art. 12'},
         {'n': 14, 't': 'Ante el riesgo residual, se proporcionan los EPP libres de costo a las personas trabajadoras.',
          'art': 'DS 44/2024 Art. 13 inc.1'},
         {'n': 15, 't': 'Los EPP son adecuados al riesgo a cubrir.',
          'art': 'DS 44/2024 Art. 13 inc.1'},
         {'n': 16, 't': 'Los EPP cumplen las normas de certificación de calidad o están registrados en el ISP.',
          'art': 'DS 44/2024 Art. 13 inc.2'},
         {'n': 17, 't': 'Cuenta con procedimiento de utilización, mantenimiento, reposición o recambio de los EPP.',
          'art': 'DS 44/2024 Art. 13 inc.2'},
         {'n': 18, 't': 'Las personas trabajadoras están capacitadas en el uso y mantención de los EPP (curso mínimo de 1 hora).',
          'art': 'DS 44/2024 Art. 13 inc.3'},
         {'n': 19, 't': 'Cuenta con registro de las capacitaciones en EPP (actividades teóricas y prácticas, asistentes, relatores, evaluaciones y reforzamiento).',
          'art': 'DS 44/2024 Art. 13 inc.4'},
         {'n': 20, 't': 'Se realiza al menos anualmente una evaluación del cumplimiento del programa de trabajo preventivo y se disponen medidas de mejora continua.',
          'art': 'DS 44/2024 Art. 14 y 52'},
     ]},
    {'seccion': 'Información y formación en seguridad y salud en el trabajo',
     'organismo': 'Dirección del Trabajo',
     'items': [
         {'n': 21, 't': 'Se informan los riesgos, las medidas preventivas y los procedimientos de trabajo correctos, de forma oportuna y previa al inicio de las labores y ante cambios de proceso, tecnología o materiales.',
          'art': 'DS 44/2024 Art. 15 inc.1'},
         {'n': 22, 't': 'La información considera al menos: a) características del lugar; b) riesgos y medidas, incl. emergencias; c) procedimientos de trabajo seguro; d) productos y sustancias; e) riesgos de emergencias/catástrofes del Plan de gestión.',
          'art': 'DS 44/2024 Art. 15 inc.3 y 19 inc.1'},
         {'n': 23, 't': 'Se efectuó capacitación teórica o práctica con la periodicidad del programa (máx. 2 años), con principales medidas de seguridad, enfoque de género, duración mínima de 8 horas y metodologías de aprendizaje.',
          'art': 'DS 44/2024 Art. 16 inc.1'},
         {'n': 24, 't': 'La capacitación aborda: factores de riesgo, efectos en la salud/EP, medidas preventivas, prestaciones, establecimiento asistencial del OAL, plan de emergencia, señalética y prevención de incendios.',
          'art': 'DS 44/2024 Art. 16 inc.1'},
     ]},
    {'seccion': 'Consulta y participación',
     'organismo': 'Dirección del Trabajo',
     'items': [
         {'n': 25, 't': 'Se promueve la consulta y participación de los representantes de las personas trabajadoras en la gestión preventiva (consulta al CPHS ante cambios y en la investigación de causas).',
          'art': 'DS 44/2024 Art. 17 inc.1, 37 inc.2 num.4 y 71 inc.1'},
     ]},
    {'seccion': 'Riesgo Grave e Inminente y Plan de Gestión de emergencias',
     'organismo': 'Seremi de Salud',
     'items': [
         {'n': 26, 't': 'Ante un riesgo grave e inminente: a) informa de inmediato a las personas trabajadoras afectadas y las medidas adoptadas; b) suspende y evacúa las faenas afectadas si el riesgo no se puede eliminar o atenuar.',
          'art': 'DS 44/2024 Art. 18 inc.1'},
         {'n': 27, 't': 'Cuenta con uno o más planes de gestión, reducción y respuesta ante emergencias, catástrofes o desastres, de origen interno o externo.',
          'art': 'DS 44/2024 Art. 19 inc.1'},
         {'n': 28, 't': 'Se realizan al menos una vez al año pruebas de ensayo de los planes de gestión, reducción y respuesta.',
          'art': 'DS 44/2024 Art. 19 inc.1'},
     ]},
    {'seccion': 'Coordinación y Cooperación de la actividad preventiva',
     'organismo': 'Dirección del Trabajo',
     'items': [
         {'n': 29, 't': 'Existe coordinación, cooperación e información mutua cuando prestan servicios más de una entidad empleadora (o trabajadores independientes) en el mismo lugar de trabajo.',
          'art': 'DS 44/2024 Art. 20 inc.1'},
     ]},
    {'seccion': 'Comités Paritarios de Higiene y Seguridad',
     'organismo': 'Dirección del Trabajo',
     'items': [
         {'n': 30, 't': 'El Comité Paritario de Higiene y Seguridad está constituido en la empresa, faena, sucursal o agencia con más de 25 personas.',
          'art': 'DS 44/2024 Art. 23 inc.1'},
         {'n': 31, 't': 'Los integrantes electos del CPHS sin curso de orientación lo realizan durante el primer semestre de su mandato.',
          'art': 'DS 44/2024 Art. 32 inc.1'},
         {'n': 32, 't': 'Se registró el acta de constitución del CPHS en el sitio web de la Dirección del Trabajo dentro de los 15 días hábiles siguientes a la elección.',
          'art': 'DS 44/2024 Art. 36'},
         {'n': 33, 't': 'La entidad otorga las facilidades y medidas para el adecuado funcionamiento del o los CPHS.',
          'art': 'DS 44/2024 Art. 37'},
         {'n': 34, 't': 'El CPHS efectúa reuniones mensuales ordinarias y extraordinarias (a petición, ante accidente fatal o grave, o riesgo grave e inminente).',
          'art': 'DS 44/2024 Art. 39 inc.1 y 2'},
         {'n': 35, 't': 'Cuenta con actas de las reuniones del CPHS, con materias tratadas, acuerdos, medidas preventivas y plazo de cumplimiento.',
          'art': 'DS 44/2024 Art. 39 inc.4 y 42 inc.1'},
         {'n': 36, 't': 'Los acuerdos del CPHS se comunican por escrito a la entidad empleadora.',
          'art': 'DS 44/2024 Art. 42 inc.2'},
         {'n': 37, 't': 'Se proporciona al CPHS toda la documentación de prevención de riesgos para cumplir su rol.',
          'art': 'DS 44/2024 Art. 46 inc.3'},
         {'n': 38, 't': 'El CPHS cumple las funciones mínimas (asesorar, vigilar, investigar causas, decidir negligencia, indicar medidas, promover cursos, informar riesgo grave e inminente y demás del OAL).',
          'art': 'DS 44/2024 Art. 47'},
         {'n': 39, 't': 'Donde laboren entre 10 y 25 personas, cuenta con Delegado de Seguridad y Salud en el Trabajo que participa en el sistema de gestión.',
          'art': 'DS 44/2024 Art. 66 inc.1, 64 y 37'},
         {'n': 40, 't': 'El Delegado SST es elegido cada 2 años mediante asamblea de las personas trabajadoras, dejando acta.',
          'art': 'DS 44/2024 Art. 66 inc.2'},
     ]},
    {'seccion': 'Departamentos de Prevención de Riesgos',
     'organismo': 'SUSESO / Mutual',
     'items': [
         {'n': 41, 't': 'Cuenta con Departamento de Prevención de Riesgos si tiene más de 100 trabajadores, dirigido por un experto inscrito en la Seremi de Salud.',
          'art': 'DS 44/2024 Art. 50 y 55 inc.2'},
         {'n': 42, 't': 'Se proporcionan al Departamento de Prevención de Riesgos los medios y el personal necesarios para sus funciones.',
          'art': 'DS 44/2024 Art. 51 inc.1'},
         {'n': 43, 't': 'El Departamento de Prevención de Riesgos cumple sus funciones.',
          'art': 'DS 44/2024 Art. 52'},
         {'n': 44, 't': 'La categoría y tiempo de dedicación del encargado del DPR se determinan según el N° de trabajadores y la cotización genérica.',
          'art': 'DS 44/2024 Art. 54 y 55 inc.1'},
         {'n': 45, 't': 'El encargado del DPR registra asistencia cumpliendo el tiempo de atención según N° de trabajadores y cotización.',
          'art': 'DS 44/2024 Art. 55 inc.1 y 3'},
         {'n': 46, 't': 'El DPR mantiene: a) registro de incidentes; b) registros de accidentes y EP; c) registro de trabajadores en vigilancia; d) estadísticas (accidentabilidad, frecuencia, gravedad) diferenciadas por sexo.',
          'art': 'DS 44/2024 Art. 73 y 74'},
         {'n': 47, 't': 'Si no está obligada a contar con DPR, registra: a) tasa anual de accidentabilidad; b) accidentes del trabajo y trayecto; c) enfermedades profesionales.',
          'art': 'DS 44/2024 Art. 75'},
         {'n': 48, 't': 'La entidad de hasta 100 trabajadores con encargado de Gestión del Riesgo: dicha persona fue capacitada por el Organismo Administrador Ley 16.744.',
          'art': 'DS 44/2024 Art. 65 inc.1'},
     ]},
    {'seccion': 'Reglamentos Internos',
     'organismo': 'Dirección del Trabajo',
     'items': [
         {'n': 49, 't': 'Cuenta y mantiene al día un Reglamento Interno de Higiene y Seguridad, entregado gratuitamente e ingresado a la página web de la Dirección del Trabajo.',
          'art': 'DS 44/2024 Art. 56 inc.1 y 57 inc.1'},
         {'n': 50, 't': 'El Reglamento Interno se envía 30 días antes de regir, para observaciones, a trabajadores, CPHS/Delegado SST y organizaciones sindicales.',
          'art': 'DS 44/2024 Art. 57 inc.2'},
         {'n': 51, 't': 'El Reglamento Interno se revisa con periodicidad no inferior a un año, con participación del DPR/CPHS/Delegado y organizaciones sindicales.',
          'art': 'DS 44/2024 Art. 57 inc.5'},
         {'n': 52, 't': 'El Reglamento Interno contiene al menos: preámbulo, disposiciones generales, obligaciones, prohibiciones y sanciones.',
          'art': 'DS 44/2024 Art. 58'},
     ]},
    {'seccion': 'Mapas de Riesgos',
     'organismo': 'Seremi de Salud',
     'items': [
         {'n': 53, 't': 'Mantiene mapas de riesgos en lugares visibles, con un esquema del lugar de trabajo e indicación de los principales riesgos existentes.',
          'art': 'DS 44/2024 Art. 62 inc.1 y 2'},
     ]},
    {'seccion': 'Vigilancia del ambiente y de la salud',
     'organismo': 'Seremi de Salud',
     'items': [
         {'n': 54, 't': 'Los lugares con exposición a agentes o factores de riesgo están en programa de vigilancia ambiental conforme a los protocolos del MINSAL y del OAL.',
          'art': 'DS 44/2024 Art. 67 inc.1 y 3'},
         {'n': 55, 't': 'Las personas trabajadoras expuestas están en programa de vigilancia de la salud conforme a los protocolos del MINSAL y del OAL.',
          'art': 'DS 44/2024 Art. 67 inc.1, 3 y 5'},
         {'n': 56, 't': 'Autoriza a las personas trabajadoras a asistir a los exámenes de control del OAL, considerando ese tiempo como trabajado.',
          'art': 'DS 44/2024 Art. 68'},
     ]},
    {'seccion': 'Traslado del puesto de trabajo y prescripción de medidas',
     'organismo': 'SUSESO / Mutual',
     'items': [
         {'n': 57, 't': 'La persona trabajadora con EP fue trasladada a un puesto sin exposición al riesgo de origen, sin detrimento de sus remuneraciones.',
          'art': 'DS 44/2024 Art. 69'},
         {'n': 58, 't': 'Implementa las medidas de SST que ordenen los fiscalizadores, el OAL, el DPR o el CPHS.',
          'art': 'DS 44/2024 Art. 70'},
     ]},
    {'seccion': 'Investigación de causas de accidentes del trabajo y EP',
     'organismo': 'SUSESO / Mutual',
     'items': [
         {'n': 59, 't': 'Investiga con enfoque de género las causas de los accidentes del trabajo y enfermedades profesionales, con la metodología del OAL.',
          'art': 'DS 44/2024 Art. 71'},
     ]},
    {'seccion': 'Registro de la actividad preventiva e indicadores de gestión',
     'organismo': 'SUSESO / Mutual',
     'items': [
         {'n': 60, 't': 'Registra y respalda documental y fidedignamente toda la información de la gestión de riesgos, a disposición de los fiscalizadores y del OAL.',
          'art': 'DS 44/2024 Art. 72 inc.1'},
     ]},
]


# Calculados, nunca a mano: si el catálogo cambia, el % de cumplimiento sigue cuadrando.
TOTAL = sum(len(s['items']) for s in SECCIONES)

# n° de ítem -> {'item', 'seccion', 'organismo'}. Espeja el ITEM_INDEX del JS del dashboard.
INDEX = {it['n']: {'item': it, 'seccion': s['seccion'], 'organismo': s['organismo']}
         for s in SECCIONES for it in s['items']}


def resumen(estados):
    """estados = dict {item_n: fila} de db.estados_fuf(). Devuelve el conteo y el % de
    cumplimiento con la MISMA fórmula que el dashboard DS 44 (app.py): (si + na) / TOTAL."""
    cnt = {'si': 0, 'no': 0, 'na': 0, 'pendiente': 0}
    for n in range(1, TOTAL + 1):
        fila = (estados or {}).get(n) or (estados or {}).get(str(n))
        e = (fila or {}).get('estado') or 'pendiente'
        cnt[e] = cnt.get(e, 0) + 1
    respondidos = cnt['si'] + cnt['no'] + cnt['na']
    pct = round(100 * (cnt['si'] + cnt['na']) / TOTAL) if TOTAL else 0
    return {**cnt, 'respondidos': respondidos, 'total': TOTAL, 'pct': pct}
