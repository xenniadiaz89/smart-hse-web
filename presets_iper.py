"""Procesos preestablecidos para la Matriz de Riesgos (IPER) — insertables con un clic.

JERARQUÍA (DS 44 · Anexo 1 "Levantamiento de procesos" · verificada en las matrices reales):
    Proceso  →  Tarea(s) + Puesto(s)  →  Peligro → Riesgo → Evaluación
Un PROCESO agrupa varias TAREAS. Ejemplo: proceso "Traslado a punto de trabajo" → tarea
"Conducción de vehículo liviano". NO al revés: conducción es una tarea, no un proceso.

Ronda 30: corrección conceptual. Antes (Ronda 29) había tareas/riesgos (Conducción, UV, Ruido…)
mal rotulados como "procesos". Los transversales NO son procesos: se agregan como RIESGOS a una
tarea desde el selector del Anexo 2 (su contenido de control vive en controles_ds44 por código).

Cada preset es un PAQUETE editable: al insertarse son TareaIPER/RiesgoItem normales (la "ventana
abierta"). Los controles salen de las matrices reales (DS44/Matriz de riesgos/), limpios de
lenguaje minero. Son borradores: el sistema propone, el prevencionista valida y firma.

Los controles van como lista; el módulo los normaliza a '1.\\n2.\\n' antes de guardar.
"""

PRESETS = {
    'traslado': {
        'proceso': 'Traslado a punto de trabajo',
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
}

# Orden y etiqueta para el menú del panel.
LISTA = [('traslado', 'Traslado a punto de trabajo')]


def preset(pid):
    return PRESETS.get((pid or '').strip().lower())
