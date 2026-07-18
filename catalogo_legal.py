"""Catálogo de requisitos legales transversales SST — insertables en la Matriz Legal.

Igual que los presets de la matriz de riesgo: el usuario los inserta con un clic y quedan
editables. Complementan (no duplican) los CORE-01..08 que ya se precargan.

Alcance: seguridad y salud en el trabajo, alineado al D.S. 44 / FUF 44. Transversal a cualquier
empleador chileno. LIMPIO de minería y de estándares de mandante: se excluyen RESSO, SIGO,
estándares corporativos Codelco y el D.S. 72/132 (Reglamento de Seguridad Minera).

Fuente: consolidado real de requisitos legales (DS44/Matriz legal/) + marco DS 44/FUF 44. Cada
requisito está fundado en su norma; son REFERENCIA para que el prevencionista/abogado valide y
ajuste, no verdad cerrada (mismo criterio que los controles de la IPER).

control_operativo va como lista; se normaliza a '1. …\\n2. …' con formato.normalizar_control_operativo.
"""

CATALOGO = [
    # ── P1 · Gestión preventiva e información de riesgos (DS 44) ──
    {'codigo': 'LEG-PTP', 'cuerpo_legal': 'DS 44/2024', 'articulo': 'Art. 8', 'pilar': 'P1',
     'frecuencia_meses': 12,
     'requisito': 'Programa de Trabajo Preventivo escrito, aprobado por la gerencia y difundido, elaborado a partir de la MIPER.',
     'control_operativo': ['Confeccionar el programa preventivo a partir de la MIPER dentro de 30 días',
                           'Aprobarlo por el representante legal y difundirlo en los lugares de trabajo',
                           'Remitir un ejemplar al Comité Paritario / Delegado SST']},
    {'codigo': 'LEG-CAP', 'cuerpo_legal': 'DS 44/2024', 'articulo': 'Art. 16', 'pilar': 'P1',
     'frecuencia_meses': 24,
     'requisito': 'Capacitación teórica y práctica en prevención de riesgos, con enfoque de género (mín. 8 h, máx. cada 2 años).',
     'control_operativo': ['Capacitar según la periodicidad del programa (máximo 2 años)',
                           'Registrar asistentes, relatores, contenidos y evaluaciones',
                           'Incluir factores de riesgo, medidas preventivas y plan de emergencia']},
    {'codigo': 'LEG-MAPA', 'cuerpo_legal': 'DS 44/2024', 'articulo': 'Art. 62', 'pilar': 'P1',
     'frecuencia_meses': 12,
     'requisito': 'Mapa de riesgos publicado en lugares visibles, con esquema del lugar y los principales riesgos.',
     'control_operativo': ['Elaborar el mapa de riesgos del lugar de trabajo',
                           'Publicarlo en lugares visibles y mantenerlo actualizado']},
    {'codigo': 'LEG-INVACC', 'cuerpo_legal': 'DS 44/2024', 'articulo': 'Art. 71', 'pilar': 'P1',
     'frecuencia_meses': None,
     'requisito': 'Investigación de las causas de accidentes del trabajo y enfermedades profesionales con enfoque de género.',
     'control_operativo': ['Investigar todo accidente y enfermedad profesional con la metodología del OAL',
                           'Definir medidas correctivas y verificar su cierre',
                           'Registrar la investigación y comunicarla al CPHS']},
    {'codigo': 'LEG-ESTAD', 'cuerpo_legal': 'DS 44/2024', 'articulo': 'Art. 73-75', 'pilar': 'P1',
     'frecuencia_meses': 12,
     'requisito': 'Registro de accidentes, enfermedades profesionales y estadísticas (accidentabilidad, frecuencia, gravedad) diferenciadas por sexo.',
     'control_operativo': ['Mantener el registro de incidentes, accidentes y EP',
                           'Calcular las tasas de accidentabilidad, frecuencia y gravedad',
                           'Diferenciar las estadísticas por sexo']},
    {'codigo': 'LEG-DPR', 'cuerpo_legal': 'DS 44/2024', 'articulo': 'Art. 50-55', 'pilar': 'P1',
     'frecuencia_meses': None,
     'requisito': 'Departamento de Prevención de Riesgos dirigido por un experto, cuando hay más de 100 trabajadores.',
     'control_operativo': ['Constituir el DPR cuando la dotación supere 100 trabajadores',
                           'Designar un experto inscrito en la Seremi de Salud',
                           'Proporcionar los medios y el tiempo de dedicación según N° de trabajadores']},
    {'codigo': 'LEG-DELEG', 'cuerpo_legal': 'DS 44/2024', 'articulo': 'Art. 66', 'pilar': 'P1',
     'frecuencia_meses': 24,
     'requisito': 'Delegado de Seguridad y Salud en el Trabajo, elegido cada 2 años, donde laboran entre 10 y 25 personas.',
     'control_operativo': ['Elegir el Delegado SST por asamblea cuando haya entre 10 y 25 trabajadores',
                           'Dejar acta de la elección y renovarla cada 2 años']},

    # ── P2 · Condiciones sanitarias y ambientales (DS 594 y afines) ──
    {'codigo': 'LEG-EPP', 'cuerpo_legal': 'DS 44 Art. 13 / DS 18', 'articulo': 'Art. 13', 'pilar': 'P2',
     'frecuencia_meses': 12,
     'requisito': 'EPP certificado (registro ISP), entregado sin costo, con procedimiento de uso/reposición y registro por trabajador.',
     'control_operativo': ['Entregar EPP certificado (norma de calidad o registro ISP) sin costo',
                           'Registrar la entrega y la capacitación de uso por trabajador',
                           'Mantener procedimiento de mantención, reposición y recambio']},
    {'codigo': 'LEG-AGUA', 'cuerpo_legal': 'DS 594', 'articulo': 'Art. 12-15', 'pilar': 'P2',
     'frecuencia_meses': 12,
     'requisito': 'Agua potable para consumo humano y para higiene personal, suficiente y de calidad.',
     'control_operativo': ['Asegurar agua potable suficiente para consumo e higiene',
                           'Verificar la calidad del agua conforme al DS 594']},
    {'codigo': 'LEG-SSHH', 'cuerpo_legal': 'DS 594', 'articulo': 'Art. 21-27', 'pilar': 'P2',
     'frecuencia_meses': 12,
     'requisito': 'Servicios higiénicos, vestidores y comedores en número y condiciones según la dotación.',
     'control_operativo': ['Disponer de servicios higiénicos y duchas según el N° de trabajadores',
                           'Mantener vestidores y comedores en las condiciones exigidas',
                           'Asegurar limpieza y mantención periódica']},
    {'codigo': 'LEG-EXTINT', 'cuerpo_legal': 'DS 594 / DS 369', 'articulo': 'Art. 45-47', 'pilar': 'P2',
     'frecuencia_meses': 12,
     'requisito': 'Extintores adecuados al riesgo, en número suficiente, señalizados, con mantención y certificación vigente.',
     'control_operativo': ['Dotar extintores adecuados a la clase de fuego y al riesgo',
                           'Señalizarlos y mantenerlos accesibles',
                           'Mantención y certificación anual; capacitar en su uso']},
    {'codigo': 'LEG-SUSTQ', 'cuerpo_legal': 'DS 594 / DS 43', 'articulo': 'DS 43', 'pilar': 'P2',
     'frecuencia_meses': 12,
     'requisito': 'Almacenamiento y manejo seguro de sustancias peligrosas: HDS disponibles, rotulación y compatibilidad.',
     'control_operativo': ['Mantener las Hojas de Datos de Seguridad (HDS) accesibles',
                           'Rotular y almacenar por compatibilidad, con contención de derrames',
                           'Capacitar en manejo seguro y respuesta ante emergencia química']},
    {'codigo': 'LEG-LIMPERM', 'cuerpo_legal': 'DS 594', 'articulo': 'Art. 59-66', 'pilar': 'P2',
     'frecuencia_meses': 12,
     'requisito': 'Control de agentes ambientales (ruido, sílice, calor, químicos) contra los límites permisibles.',
     'control_operativo': ['Identificar los agentes presentes en el ambiente de trabajo',
                           'Evaluar la exposición contra los límites permisibles del DS 594',
                           'Aplicar medidas de control en la fuente, el medio y la persona']},
    {'codigo': 'LEG-VIGAMB', 'cuerpo_legal': 'DS 44 Art. 67 / Protocolos MINSAL', 'articulo': 'Art. 67', 'pilar': 'P2',
     'frecuencia_meses': 12,
     'requisito': 'Programas de vigilancia ambiental y de la salud según los protocolos MINSAL (PREXOR, PLANESI, TMERT, RUV, riesgo psicosocial).',
     'control_operativo': ['Incorporar a los expuestos a los programas de vigilancia del OAL',
                           'Aplicar los protocolos MINSAL que correspondan (ruido, sílice, TMERT, UV, psicosocial)',
                           'Autorizar la asistencia a los exámenes de control como tiempo trabajado']},
    {'codigo': 'LEG-UV', 'cuerpo_legal': 'Ley 20.096', 'articulo': 'Art. 19', 'pilar': 'P2',
     'frecuencia_meses': 12,
     'requisito': 'Medidas de protección contra la radiación UV para trabajadores expuestos a radiación solar.',
     'control_operativo': ['Informar el riesgo UV y difundir el índice de radiación',
                           'Proveer bloqueador, ropa con filtro UV, gorro legionario y lentes',
                           'Gestionar la exposición (sombra, horarios críticos)']},

    # ── OTROS · Marco laboral / administrativo transversal ──
    {'codigo': 'LEG-RIOHS', 'cuerpo_legal': 'DS 44 Art. 56 / Código del Trabajo', 'articulo': 'Art. 56-58', 'pilar': 'OTROS',
     'frecuencia_meses': 12,
     'requisito': 'Reglamento Interno de Higiene y Seguridad (RIOHS) vigente, entregado gratuitamente e ingresado a la Dirección del Trabajo.',
     'control_operativo': ['Mantener el RIOHS al día con preámbulo, obligaciones, prohibiciones y sanciones',
                           'Enviarlo 30 días antes de regir a trabajadores, CPHS y sindicatos para observaciones',
                           'Ingresarlo a la web de la Dirección del Trabajo y entregarlo gratuitamente']},
    {'codigo': 'LEG-PREOCUP', 'cuerpo_legal': 'DS 594 / Código Sanitario', 'articulo': 'Código Sanitario', 'pilar': 'OTROS',
     'frecuencia_meses': 12,
     'requisito': 'Exámenes preocupacionales y ocupacionales de aptitud según el cargo y los riesgos, en organismo autorizado.',
     'control_operativo': ['Realizar el examen preocupacional de aptitud antes del ingreso',
                           'Repetir los exámenes ocupacionales según el riesgo del cargo',
                           'Archivar los certificados vigentes por trabajador']},
    {'codigo': 'LEG-DROGAS', 'cuerpo_legal': 'Ley 20.000', 'articulo': 'Ley 20.000', 'pilar': 'OTROS',
     'frecuencia_meses': 12,
     'requisito': 'Política y control de alcohol y drogas, con procedimiento difundido incorporado al RIOHS.',
     'control_operativo': ['Definir y difundir la política de alcohol y drogas',
                           'Incorporar el procedimiento de control al RIOHS',
                           'Capacitar y registrar la difusión al personal']},
    {'codigo': 'LEG-TABACO', 'cuerpo_legal': 'Ley 20.105', 'articulo': 'Ley 20.105', 'pilar': 'OTROS',
     'frecuencia_meses': 12,
     'requisito': 'Ambientes libres de humo de tabaco: señalización y prohibición de fumar en recintos cerrados.',
     'control_operativo': ['Señalizar la prohibición de fumar en los recintos cerrados',
                           'Habilitar zonas de fumadores conforme a la normativa, cuando aplique']},
    {'codigo': 'LEG-SUBCON', 'cuerpo_legal': 'Ley 20.123 / DS 76', 'articulo': 'DS 76', 'pilar': 'OTROS',
     'frecuencia_meses': 12,
     'requisito': 'Gestión de subcontratación: coordinación de la actividad preventiva y registro de contratistas cuando corresponda.',
     'control_operativo': ['Coordinar, cooperar e informar mutuamente entre las empresas del lugar de trabajo',
                           'Mantener el registro de contratistas y subcontratistas',
                           'Verificar el cumplimiento SST de los contratistas']},
    {'codigo': 'LEG-COTIZ', 'cuerpo_legal': 'DS 67 / Ley 16.744', 'articulo': 'DS 67', 'pilar': 'OTROS',
     'frecuencia_meses': 12,
     'requisito': 'Cotización básica y adicional diferenciada por siniestralidad, al día ante el Organismo Administrador.',
     'control_operativo': ['Pagar la cotización básica y la adicional diferenciada por siniestralidad',
                           'Verificar la tasa asignada según el proceso de evaluación del DS 67']},
]

# Etiqueta de cada pilar (para el menú del panel).
import cumplimiento
PILARES = cumplimiento.PILARES

INDEX = {r['codigo']: r for r in CATALOGO}


def agrupado():
    """[(pilar, nombre, [requisitos])] en el orden P1, P2, P3, OTROS — para el modal del catálogo."""
    orden = ['P1', 'P2', 'P3', 'OTROS']
    out = []
    for p in orden:
        reqs = [r for r in CATALOGO if r.get('pilar') == p]
        if reqs:
            out.append({'pilar': p, 'nombre': PILARES.get(p, p), 'requisitos': reqs})
    return out


def requisito(codigo):
    return INDEX.get((codigo or '').strip().upper())


# ── Puente FUF → Matriz Legal (principio transversal): qué requisito(s) satisface cada ítem del
#    FUF, para propagar el Cumple del FUF al estado del requisito legal. Por id_requisito. ──
FUF_A_CODIGO = {
    8: ['LEG-PTP'], 9: ['LEG-PTP'], 10: ['LEG-PTP'], 11: ['LEG-PTP'],
    14: ['LEG-EPP'], 15: ['LEG-EPP'], 16: ['LEG-EPP'], 17: ['LEG-EPP'],
    18: ['LEG-CAP'], 19: ['LEG-CAP'], 23: ['LEG-CAP'], 24: ['LEG-CAP'],
    # Comité Paritario: los ítems 30-38 satisfacen el requisito Core CORE-06 (DS 54 / Ley 16.744).
    # No hay un LEG-CPHS propio porque el CPHS ya vive en la Capa Core, que es la que el motor de
    # dotación enciende y apaga (cumplimiento.REGLAS_DOTACION).
    **{n: ['CORE-06'] for n in range(30, 39)},
    39: ['LEG-DELEG'], 40: ['LEG-DELEG'],
    41: ['LEG-DPR'], 42: ['LEG-DPR'], 43: ['LEG-DPR'],
    47: ['LEG-ESTAD'], 60: ['LEG-ESTAD'], 59: ['LEG-INVACC'],
    49: ['LEG-RIOHS'], 50: ['LEG-RIOHS'], 51: ['LEG-RIOHS'], 52: ['LEG-RIOHS'],
    53: ['LEG-MAPA'],
    54: ['LEG-VIGAMB'], 55: ['LEG-VIGAMB'],
}


def codigos_por_fuf(n):
    """Códigos de requisito legal (LEG-*) que satisface el ítem FUF n. [] si no hay mapeo."""
    try:
        return FUF_A_CODIGO.get(int(n), [])
    except (TypeError, ValueError):
        return []
