import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ══════════════════════════════════════════════════════════════
#  CONFIGURACIÓN GENERAL
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Smart HSE Chile — Consola Operativa",
    page_icon="🛡️",
    layout="wide"
)

CONTRATOS  = ["405", "118", "109100077748"]
FECHA_HOY  = datetime.today().strftime("%Y-%m-%d")

# ══════════════════════════════════════════════════════════════
#  ESTADO DE SESIÓN E INICIO (LOGIN)
# ══════════════════════════════════════════════════════════════
def init_state():
    defaults = {
        "empresa": "", "contrato": "", "actividad": "",
        "lugar": "", "modo": "Enterprise",
        "na_items": [], "autenticado": False, "ruta_activa": ""
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── Contraseña desde Secrets (o valor por defecto si no está configurado) ──
APP_PASSWORD = st.secrets.get("APP_PASSWORD", "smarthse2025")

if not st.session_state["autenticado"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
            <h1 style='text-align:center; color:#002B49; font-size:3rem;
                       font-weight:300; font-family:Inter,sans-serif;'>
                SMART HSE
                <span style='color:#8DC63F; font-weight:700;'>CHILE</span>
            </h1>
            <p style='text-align:center; color:#64748b; margin-bottom:30px;
                      font-weight:300; font-family:Inter,sans-serif;'>
                Consola de Gestión Operativa · Cumplimiento DS.44
            </p>
        """, unsafe_allow_html=True)

        with st.form("form_login"):
            usuario = st.text_input("Correo Electrónico")
            clave   = st.text_input("Contraseña", type="password")
            submit  = st.form_submit_button("Iniciar Sesión", use_container_width=True)

            if submit:
                if clave == APP_PASSWORD:
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta. Intenta de nuevo.")
    st.stop()

# ══════════════════════════════════════════════════════════════
#  CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;700&display=swap');
html, body, [class*="css"], [class*="st-"] {
    font-family: 'Inter', sans-serif !important;
    font-weight: 300 !important;
}
h1, h2, h3, h4, h5, h6 { font-weight: 400 !important; color: #002B49 !important; }
b, strong { font-weight: 500 !important; }

.kpi-card {
    background: linear-gradient(135deg, #002B49 0%, #1e3a5f 100%);
    border-radius: 12px; padding: 1.2rem 1.5rem;
    color: white; text-align: center; margin-bottom: 0.5rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.08);
}
.kpi-card .valor { font-size: 2.2rem; font-weight: 300 !important; }
.kpi-card .label { font-size: 0.85rem; opacity: 0.85; margin-top: 0.2rem; }

.alerta-roja  { background:#fdf2f2; border-left:3px solid #ef4444; padding:.7rem 1rem; border-radius:6px; margin:.5rem 0; }
.alerta-verde { background:#f0fdf4; border-left:3px solid #8DC63F;  padding:.7rem 1rem; border-radius:6px; margin:.5rem 0; }
.alerta-ambar { background:#fffbeb; border-left:3px solid #f59e0b;  padding:.7rem 1rem; border-radius:6px; margin:.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  BARRA LATERAL
# ══════════════════════════════════════════════════════════════
st.sidebar.markdown("""
    <div style='text-align:center; padding:10px 0;'>
        <span style='font-family:Inter,sans-serif; font-weight:700;
                     font-size:1.4rem; color:#002B49;'>SMART HSE</span><br>
        <span style='background:#55B4B0; color:white; font-size:10px;
                     padding:2px 8px; border-radius:4px; letter-spacing:2px;'>CHILE</span>
    </div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.subheader("Selección de Faena")

ESTRUCTURA_MAESTRA = {
    "Minera Spence":   {"Faenas": ["Spence BHP"],
                        "Ruta": "Spence/Carpeta_Arranque"},
    "Codelco":         {"Faenas": ["Radomiro Tomic", "Chuquicamata", "Ministro Hales"],
                        "Ruta": "Codelco/Contratos_Estandar"},
    "Minera El Abra":  {"Faenas": ["Mina", "Planta"],
                        "Ruta": "El_Abra/Documentos"},
    "Centinela":       {"Faenas": ["Mina", "Planta SX-EW"],
                        "Ruta": "Centinela/Documentos"},
}

cliente      = st.sidebar.selectbox("Cliente:", list(ESTRUCTURA_MAESTRA.keys()))
faena        = st.sidebar.selectbox("Faena:", ESTRUCTURA_MAESTRA[cliente]["Faenas"])
ruta_activa  = ESTRUCTURA_MAESTRA[cliente]["Ruta"]
st.session_state["ruta_activa"] = ruta_activa

st.sidebar.success(f"Biblioteca activa: {ruta_activa}")
st.sidebar.markdown("---")
if st.sidebar.button("🔒 Cerrar Sesión"):
    st.session_state["autenticado"] = False
    st.rerun()

# ══════════════════════════════════════════════════════════════
#  DATOS MAESTROS
# ══════════════════════════════════════════════════════════════
CLIENTES_MINEROS = {
    "Minera Spence":  {"cliente_exige": [
        "Validación fotográfica ECF21",
        "Firma administrador en matriz base",
        "Acreditación vigente de equipos"]},
    "Codelco":        {"cliente_exige": [
        "LOD semanal enviado",
        "Reporte de observaciones conductuales",
        "Matriz de riesgos actualizada"]},
    "Minera El Abra": {"cliente_exige": [
        "Charla 5 minutos firmada",
        "Validación ingreso a planta"]},
    "Centinela":      {"cliente_exige": [
        "Registro All Scan diario",
        "Revisión EPP específico"]},
}

ACTIVIDADES_AGENDA = [
    {"actividad": "Registro FYS / ECF21 diario",      "frecuencia": "Diaria",   "dias": 1,  "modulo": "FYS",    "cliente": "Codelco"},
    {"actividad": "Actualización ECF21 Terreno",       "frecuencia": "Diaria",   "dias": 1,  "modulo": "Terreno","cliente": "Minera Spence"},
    {"actividad": "Revisión LOD semanal",              "frecuencia": "Semanal",  "dias": 7,  "modulo": "RESSO",  "cliente": "Codelco"},
    {"actividad": "Acreditación Equipos",              "frecuencia": "Semanal",  "dias": 5,  "modulo": "Legal",  "cliente": "Minera Spence"},
    {"actividad": "Reunión Comité Paritario (CPHS)",   "frecuencia": "Mensual",  "dias": 30, "modulo": "Legal",  "cliente": "Minera El Abra"},
    {"actividad": "Registro All Scan",                 "frecuencia": "Diaria",   "dias": 1,  "modulo": "Terreno","cliente": "Centinela"},
    {"actividad": "Revisión EPP específico",           "frecuencia": "Semanal",  "dias": 5,  "modulo": "Legal",  "cliente": "Centinela"},
]

# ══════════════════════════════════════════════════════════════
#  CABECERA PRINCIPAL Y TABS
# ══════════════════════════════════════════════════════════════
st.title(f"Gestión Operativa: {faena}")
st.caption(f"Smart HSE Chile · {datetime.today().strftime('%d/%m/%Y')} · Rol: Asesora Senior")

tab_dashboard, tab_inicio, tab_agenda, tab_cartas = st.tabs([
    "⚡ Acción Inmediata",
    "🚀 Onboarding",
    "📅 Agenda Inteligente",
    "📄 Cartas N/A",
])

# ══════════════════════════════════════════════════════════════
#  TAB 1: ACCIÓN INMEDIATA
# ══════════════════════════════════════════════════════════════
with tab_dashboard:
    c1, c2, c3 = st.columns(3)
    c1.markdown("<div class='kpi-card'><div class='valor'>12</div><div class='label'>Documentos RESSO</div></div>", unsafe_allow_html=True)
    c2.markdown("<div class='kpi-card'><div class='valor'>45</div><div class='label'>Registros FYS</div></div>", unsafe_allow_html=True)
    c3.markdown("<div class='kpi-card'><div class='valor'>8</div><div class='label'>Ítems N/A detectados</div></div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("<h3 style='font-size:1.2rem;'>⚡ Foco del Día — Top 3</h3>", unsafe_allow_html=True)

    acts_cliente = [a for a in ACTIVIDADES_AGENDA if a["cliente"] == cliente]
    top3 = sorted(acts_cliente, key=lambda a: a["dias"])[:3]

    if not top3:
        st.info("No hay tareas urgentes programadas para este cliente hoy.")
    else:
        for i, act in enumerate(top3, 1):
            proxima = (datetime.today() + timedelta(days=act["dias"])).strftime("%d/%m/%Y")
            if act["dias"] <= 1:
                clase, icono = "alerta-roja", "🔴"
            elif act["dias"] <= 7:
                clase, icono = "alerta-ambar", "⚠️"
            else:
                clase, icono = "alerta-verde", "✅"
            st.markdown(
                f'<div class="{clase}"><b>{i}. {icono} {act["actividad"]}</b><br>'
                f'<span style="font-size:.85rem">📅 Próxima ejecución: {proxima} · Módulo: {act["modulo"]}</span></div>',
                unsafe_allow_html=True
            )

    exige = CLIENTES_MINEROS.get(cliente, {}).get("cliente_exige", [])
    if exige:
        st.divider()
        st.markdown("<h3 style='font-size:1.2rem;'>📋 Requisitos Formales del Cliente</h3>", unsafe_allow_html=True)
        for i, req in enumerate(exige, 1):
            st.markdown(f"**{i}.** {req}")

# ══════════════════════════════════════════════════════════════
#  TAB 2: ONBOARDING
# ══════════════════════════════════════════════════════════════
with tab_inicio:
    st.info(f"Configurando estructura documental para: **{ruta_activa}**")
    with st.form("form_onboarding"):
        contrato  = st.text_input("N° de Contrato:", value=st.session_state["contrato"])
        actividad = st.text_input("Actividad (Macro Proceso):", value=st.session_state["actividad"])
        lugar     = st.text_input("Lugar / Faena:", value=st.session_state["lugar"])
        guardar   = st.form_submit_button("💾 Guardar en Sesión", type="primary")
        if guardar:
            st.session_state["contrato"]  = contrato
            st.session_state["actividad"] = actividad
            st.session_state["lugar"]     = lugar
            st.success("✅ Datos guardados en sesión activa.")

# ══════════════════════════════════════════════════════════════
#  TAB 3: AGENDA INTELIGENTE
# ══════════════════════════════════════════════════════════════
with tab_agenda:
    st.markdown("<h3 style='font-size:1.2rem;'>📅 Agenda de Actividades Recurrentes</h3>", unsafe_allow_html=True)
    df_agenda = pd.DataFrame(ACTIVIDADES_AGENDA)
    df_agenda.columns = ["Actividad", "Frecuencia", "Días", "Módulo", "Cliente"]
    st.dataframe(df_agenda, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
#  TAB 4: CARTAS N/A
# ══════════════════════════════════════════════════════════════
with tab_cartas:
    st.markdown("<h3 style='font-size:1.2rem;'>📄 Generador de Cartas de No Aplicabilidad</h3>", unsafe_allow_html=True)

    with st.form("form_carta_na"):
        col_a, col_b = st.columns(2)
        with col_a:
            empresa_dest = st.text_input("Empresa destinataria:", value=cliente)
            n_contrato   = st.text_input("N° Contrato:", value=st.session_state.get("contrato", ""))
            fecha_carta  = st.date_input("Fecha de emisión:", value=datetime.today())
        with col_b:
            norma_na     = st.text_input("Norma / Ítem N/A:", placeholder="Ej: DS44 Art. 23")
            justificacion = st.text_area("Justificación:", height=100,
                                         placeholder="Ej: La actividad no contempla uso de explosivos...")
        generar = st.form_submit_button("📄 Generar Vista Previa", type="primary", use_container_width=True)

    if generar and norma_na and justificacion:
        meses = {"January":"enero","February":"febrero","March":"marzo","April":"abril",
                 "May":"mayo","June":"junio","July":"julio","August":"agosto",
                 "September":"septiembre","October":"octubre","November":"noviembre","December":"diciembre"}
        fecha_es = fecha_carta.strftime("%d de %B de %Y")
        for en, es in meses.items():
            fecha_es = fecha_es.replace(en, es)

        st.divider()
        st.markdown("#### Vista Previa — Carta de No Aplicabilidad")
        st.markdown(f"""
---
**Ref.:** Carta N/A · {n_contrato or "Sin contrato"} · {fecha_es}

**Señores**
{empresa_dest}
Presente

**Asunto: Declaración de No Aplicabilidad — {norma_na}**

Por medio de la presente, **Smart HSE Chile** declara que el ítem **{norma_na}** no aplica
para las actividades desarrolladas en la faena **{faena}**, bajo contrato **{n_contrato or "—"}**.

**Justificación técnica:**
{justificacion}

Sin otro particular, saluda atentamente,

**Smart HSE Chile**
contacto@smarthse.cl · smarthse.cl

---
        """)
        st.caption("⚠️ Recuerde: Copie este texto a Word para agregar firma, timbre y logo corporativo antes de enviar.")
    elif generar:
        st.warning("Complete la Norma/Ítem N/A y la Justificación para generar la carta.")
