"""Regla de formato de los controles operativos. Helper puro: sin I/O, sin Flask, sin BD."""
import re

_NUM = re.compile(r'^\s*(\d+)[\.\)]\s*')


def normalizar_control_operativo(texto):
    """Normaliza a lista numerada, una acción por línea: '1. <acción>\\n2. <acción>\\n'.

    Acepta lo que escriba el asesor: '1. algo', '1) algo', viñetas ('- algo', '• algo'), líneas
    sueltas, o el formato viejo ('1.' con la acción en la línea siguiente), y renumera. Idempotente.
    Devuelve '' si no hay contenido.
    """
    if not texto:
        return ''
    crudo = [l.strip().strip('-•*').strip() for l in str(texto).splitlines()]
    acciones, i = [], 0
    while i < len(crudo):
        linea = crudo[i]
        if not linea:
            i += 1
            continue
        m = _NUM.match(linea)
        if m:
            resto = linea[m.end():].strip()
            if resto:                       # '1. acción' en una sola línea
                acciones.append(resto)
            else:                           # '1.' con la acción en la línea siguiente (ya normalizado)
                j = i + 1
                while j < len(crudo) and not crudo[j]:
                    j += 1
                if j < len(crudo):
                    acciones.append(crudo[j])
                    i = j
        else:
            acciones.append(linea)
        i += 1
    return ''.join(f'{k}. {a}\n' for k, a in enumerate(acciones, 1))
