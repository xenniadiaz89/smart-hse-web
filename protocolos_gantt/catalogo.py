"""Catálogo de fases y actividades para la Carta Gantt de Protocolos MINSAL.

Dato puro, como fuf.py / catalogo_documentos_ds44.py: no es Blueprint ni toca la BD.
Cubre el ciclo completo de implementación de los protocolos de vigilancia MINSAL/SUSESO
(TMERT-EESS, Psicosocial, PREXOR, PLANESI, MMC y Radiación UV Solar), con una fase transversal
de arranque y una de cierre/auditoría anual — el registro de avance real vive en la tabla
`protocolo_etapa_estado` (una fila por empresa y `clave` de actividad).
"""

FASES = [
    {'fase': 1, 'titulo': 'Fase Transversal (Inicio del Sistema)', 'actividades': [
        {'clave': '1.1', 'actividad': 'Constitución de Comité de Salud Ocupacional o inclusión en CPHS',
         'responsable_sugerido': 'Gerencia / Experto', 'evidencia': 'Acta de constitución y firmas.'},
        {'clave': '1.2', 'actividad': 'Capacitación masiva sobre los protocolos obligatorios',
         'responsable_sugerido': 'Experto SST', 'evidencia': 'Registro de asistencia y material expuesto.'},
    ]},
    {'fase': 2, 'titulo': 'Protocolo TMERT-EESS (Trastornos Musculoesqueléticos)', 'actividades': [
        {'clave': '2.1', 'actividad': 'Difusión de la norma técnica TMERT a los trabajadores',
         'responsable_sugerido': 'Experto SST', 'evidencia': 'Lista de asistencia firmada por el personal.'},
        {'clave': '2.2', 'actividad': 'Aplicación de la lista de chequeo inicial (identificación de riesgos)',
         'responsable_sugerido': 'Experto / Supervisor', 'evidencia': 'Formulario de lista de chequeo completo.'},
        {'clave': '2.3', 'actividad': 'Confección de matriz de riesgo ergonómica interna',
         'responsable_sugerido': 'Experto SST', 'evidencia': 'Matriz TMERT digitalizada y firmada.'},
        {'clave': '2.4', 'actividad': 'Envío de puestos en riesgo alto a la mutualidad',
         'responsable_sugerido': 'Gerencia / Experto', 'evidencia': 'Comprobante de ingreso a plataforma de mutual.'},
        {'clave': '2.5', 'actividad': 'Implementación de medidas de control (pausas, rotación, rediseño)',
         'responsable_sugerido': 'Operaciones', 'evidencia': 'Registro de pausas activas e instructivos.'},
    ]},
    {'fase': 3, 'titulo': 'Protocolo Psicosocial (CEAL-SM / SUSESO)', 'actividades': [
        {'clave': '3.1', 'actividad': 'Constitución del Comité de Aplicación Psicosocial (Paritario)',
         'responsable_sugerido': 'Empresa / Trabajadores', 'evidencia': 'Acta de constitución oficial del comité.'},
        {'clave': '3.2', 'actividad': 'Campaña de difusión y sensibilización sobre riesgos psicosociales',
         'responsable_sugerido': 'Comité de Aplicación', 'evidencia': 'Afiches, correos o actas de charlas breves.'},
        {'clave': '3.3', 'actividad': 'Aplicación del cuestionario CEAL-SM (electrónico o papel)',
         'responsable_sugerido': 'Comité de Aplicación', 'evidencia': 'Reporte de participación o cuestionarios resguardados.'},
        {'clave': '3.4', 'actividad': 'Análisis de resultados y tabulación en plataforma de la mutual',
         'responsable_sugerido': 'Experto SST', 'evidencia': 'Informe de resultados oficial emitido por la mutual.'},
        {'clave': '3.5', 'actividad': 'Diseño y ejecución del plan de acción según dimensiones en riesgo',
         'responsable_sugerido': 'Comité / Gerencia', 'evidencia': 'Cronograma de medidas de mitigación internas.'},
    ]},
    {'fase': 4, 'titulo': 'Protocolo PREXOR (Exposición Ocupacional a Ruido)', 'actividades': [
        {'clave': '4.1', 'actividad': 'Catastro inicial de fuentes de ruido y herramientas ruidosas',
         'responsable_sugerido': 'Experto SST', 'evidencia': 'Inventario técnico de equipos y herramientas.'},
        {'clave': '4.2', 'actividad': 'Solicitud de evaluación ambiental cuantitativa (sonometría/dosimetría)',
         'responsable_sugerido': 'Experto SST', 'evidencia': 'Correo o requerimiento oficial formalizado a la mutual.'},
        {'clave': '4.3', 'actividad': 'Acompañamiento en terreno para la medición de ruido',
         'responsable_sugerido': 'Higienista Mutual', 'evidencia': 'Acta de visita del técnico de la mutualidad.'},
        {'clave': '4.4', 'actividad': 'Implementación del mapa de ruido y señalización de uso de EPP',
         'responsable_sugerido': 'Supervisor / SST', 'evidencia': 'Registro fotográfico y entrega de protectores auditivos.'},
        {'clave': '4.5', 'actividad': 'Ingreso de trabajadores expuestos al programa de vigilancia médica',
         'responsable_sugerido': 'Experto SST', 'evidencia': 'Nómina enviada y citaciones a audiometrías.'},
    ]},
    {'fase': 5, 'titulo': 'Protocolo PLANESI (Erradicación de la Silicosis)', 'actividades': [
        {'clave': '5.1', 'actividad': 'Identificación cualitativa de presencia de sílice en faenas o tareas',
         'responsable_sugerido': 'Experto SST', 'evidencia': 'Matriz de identificación de peligros.'},
        {'clave': '5.2', 'actividad': 'Solicitud de evaluación cuantitativa de polvo/sílice en el ambiente',
         'responsable_sugerido': 'Gerencia / Experto', 'evidencia': 'Solicitud formal ingresada al organismo administrador.'},
        {'clave': '5.3', 'actividad': 'Confección e implementación del sistema de gestión de sílice',
         'responsable_sugerido': 'Experto SST', 'evidencia': 'Documento del plan de gestión firmado.'},
        {'clave': '5.4', 'actividad': 'Capacitación específica sobre el riesgo del polvo de sílice',
         'responsable_sugerido': 'Experto SST', 'evidencia': 'Registro de asistencia y evaluaciones escritas.'},
        {'clave': '5.5', 'actividad': 'Control de ingeniería (humectación, extractores) y entrega de respiradores',
         'responsable_sugerido': 'Operaciones', 'evidencia': 'Registro de entrega de EPP (filtros P100) y mantenciones.'},
    ]},
    {'fase': 6, 'titulo': 'Protocolo MMC (Manejo Manual de Carga — Ley 20.949)', 'actividades': [
        {'clave': '6.1', 'actividad': 'Identificación de puestos con levantamiento o arrastre de carga > 25 kg',
         'responsable_sugerido': 'Experto SST', 'evidencia': 'Ficha de levantamiento de tareas con peso.'},
        {'clave': '6.2', 'actividad': 'Aplicación de las directrices de la Guía Técnica MMC del MINSAL',
         'responsable_sugerido': 'Experto SST', 'evidencia': 'Evaluación inicial mediante tablas de la guía técnica.'},
        {'clave': '6.3', 'actividad': 'Capacitación en técnicas correctas de levantamiento y ergonomía',
         'responsable_sugerido': 'Experto SST', 'evidencia': 'Registro de entrenamiento práctico y teórico.'},
        {'clave': '6.4', 'actividad': 'Adquisición de ayudas mecánicas (grúas, transpaletas, carros)',
         'responsable_sugerido': 'Gerencia', 'evidencia': 'Facturas de compra o bitácoras de uso de equipos.'},
    ]},
    {'fase': 7, 'titulo': 'Protocolo Radiación UV de Origen Solar (Ley 20.096)', 'actividades': [
        {'clave': '7.1', 'actividad': 'Publicación diaria del índice UV en un lugar visible',
         'responsable_sugerido': 'Supervisor / SST', 'evidencia': 'Registro en pizarra o panel del índice diario.'},
        {'clave': '7.2', 'actividad': 'Confección del programa de gestión teórico-práctico de radiación UV',
         'responsable_sugerido': 'Experto SST', 'evidencia': 'Documento del programa vigente y actualizado.'},
        {'clave': '7.3', 'actividad': 'Entrega de elementos de protección personal específicos (legionario, gafas)',
         'responsable_sugerido': 'Bodega / SST', 'evidencia': 'Formulario de entrega firmado (EPP con filtro UV).'},
        {'clave': '7.4', 'actividad': 'Disposición de puntos de hidratación y bloqueador solar FPS 30/50+',
         'responsable_sugerido': 'Operaciones', 'evidencia': 'Registro de consumo o verificación visual en terreno.'},
    ]},
    {'fase': 8, 'titulo': 'Fase de Cierre y Auditoría (Anual)', 'actividades': [
        {'clave': '8.1', 'actividad': 'Auditoría interna de cumplimiento de medidas correctivas',
         'responsable_sugerido': 'Experto SST', 'evidencia': 'Informe final con porcentajes de cumplimiento.'},
        {'clave': '8.2', 'actividad': 'Revisión del programa junto a la jefatura y la mutualidad',
         'responsable_sugerido': 'Gerencia / Mutual', 'evidencia': 'Acta de reunión de cierre de año e indicadores.'},
    ]},
]


def actividades_lista():
    """[{'clave','actividad','responsable_sugerido','evidencia','fase','fase_titulo'}, ...] aplanado."""
    out = []
    for f in FASES:
        for a in f['actividades']:
            out.append({**a, 'fase': f['fase'], 'fase_titulo': f['titulo']})
    return out
