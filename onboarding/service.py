"""Validación y persistencia del Panel de Bienvenida. Solo depende de db/models/core_auth/iper
— nunca de app.py ni del módulo matriz_legal (aislamiento por carpeta)."""
import db
import iper
import planes
from core_auth import normalizar_rut, rut_valido
from models import sqla, Empresa


def validar(f):
    """(ok, datos, error). Valida server-side: el <select> del navegador no es garantía."""
    razon = (f.get('razon_social') or '').strip()
    if not razon:
        return False, None, 'Indica la Razón Social de la empresa.'

    rut_emp = (f.get('rut_empresa') or '').strip()
    if not rut_emp:
        return False, None, 'Indica el RUT de la empresa.'
    if not rut_valido(rut_emp):
        return False, None, 'El RUT de la empresa no es válido (revisa el dígito verificador).'

    try:
        dotacion = int(f.get('dotacion'))
    except (TypeError, ValueError):
        return False, None, 'Indica la dotación de trabajadores (número entero).'
    if dotacion < 1:
        return False, None, 'La dotación debe ser de al menos 1 trabajador.'

    mutual = (f.get('mutual') or '').strip()
    if mutual not in iper.MUTUALES:
        return False, None, 'Selecciona un Organismo Administrador válido de la lista.'

    n_adh = (f.get('n_adherente') or '').strip()
    if not n_adh:
        return False, None, 'Indica el N° de Adherente entregado por tu Organismo Administrador.'

    # El tramo topa la nómina, no las obligaciones legales. Si no viene, se deriva de la dotación.
    plan = (f.get('plan') or '').strip().lower()
    if plan and plan not in {p['codigo'] for p in planes.PLANES}:
        return False, None, 'Selecciona un plan válido de la lista.'
    plan = plan or planes.plan_sugerido(dotacion)['codigo']

    return True, {'razon_social': razon, 'rut_empresa': normalizar_rut(rut_emp),
                  'dotacion': dotacion, 'mutual': mutual, 'n_adherente': n_adh,
                  'plan': plan}, None


def persistir(rut_asesor, empresa_id, datos):
    """Crea la empresa o actualiza la que está en foco. Devuelve el empresa_id."""
    e = Empresa.query.filter_by(id=empresa_id, rut_asesor=rut_asesor).first() if empresa_id else None
    if e is None:
        eid = db.crear_empresa(rut_asesor, datos['razon_social'],
                               rut_empresa=datos['rut_empresa'], mutual=datos['mutual'],
                               n_adherente=datos['n_adherente'], dotacion=datos['dotacion'])
        e = Empresa.query.get(eid)
        e.plan = datos['plan']
        sqla.session.commit()
        return eid
    for k, v in datos.items():
        setattr(e, k, v)
    sqla.session.commit()
    db._core01_auto_cumple(e.id)      # mutual + adherente completos ⇒ reevaluar CORE-01
    return e.id
