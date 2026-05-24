import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Smart HSE Chile",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Estado de sesión ──
def init_state():
    for k, v in {"vista":"landing","autenticado":False,"contrato":"","actividad":"","lugar":"","ruta_activa":""}.items():
        if k not in st.session_state:
            st.session_state[k] = v
init_state()

# ── Contraseña ──
try:
    APP_PASSWORD = st.secrets["APP_PASSWORD"]
except Exception:
    APP_PASSWORD = "smarthse2025"

# ── CSS global ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;800;900&family=Inter:wght@300;400;500;600&display=swap');
#MainMenu,footer,header{visibility:hidden}
.block-container{padding:0!important;max-width:100%!important}
section[data-testid="stSidebar"]{display:none}
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.sh-hero{background-color:#002B49;background-image:linear-gradient(rgba(0,43,73,.78),rgba(0,43,73,.78)),url('https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=2000&q=80');background-size:cover;background-position:center;padding:130px 20px;text-align:center;color:white;min-height:68vh;display:flex;flex-direction:column;justify-content:center;align-items:center}
.sh-hero h1{font-family:'Montserrat',sans-serif;font-weight:900;font-size:48px;max-width:900px;margin:0 auto 20px;text-transform:uppercase;line-height:1.15;text-shadow:2px 2px 6px rgba(0,0,0,.4)}
.sh-hero p{font-size:18px;max-width:720px;margin:0 auto 44px;font-weight:300;line-height:1.7}
.sh-btn-hero{background:#55B4B0;color:white;padding:16px 36px;border-radius:30px;font-weight:700;font-size:14px;text-decoration:none;text-transform:uppercase;letter-spacing:1px;display:inline-block}
.sh-cards{display:flex;justify-content:center;gap:24px;max-width:1200px;margin:-60px auto 60px;position:relative;z-index:10;padding:0 20px;flex-wrap:wrap}
.sh-card{background:white;padding:44px 24px;border-radius:16px;width:22%;min-width:200px;text-align:center;box-shadow:0 12px 36px rgba(0,0,0,.09);border-bottom:4px solid transparent;transition:transform .3s,border-color .3s}
.sh-card:hover{transform:translateY(-6px);border-bottom-color:#55B4B0}
.sh-card-icon{font-size:40px;margin-bottom:8px}
.sh-card h3{font-family:'Montserrat',sans-serif;font-weight:800;font-size:14px;color:#002B49;text-transform:uppercase;margin:16px 0 10px;letter-spacing:.5px}
.sh-card p{font-size:13px;color:#64748b;line-height:1.6}
.sh-footer{background:#002B49;color:#94A3B8;text-align:center;padding:48px 20px;font-size:13px;margin-top:40px}
.sh-footer a{color:#55B4B0;text-decoration:none}
.sh-footer-sep{border-top:1px solid #1a3a52;margin-top:20px;padding-top:16px;font-size:11px;color:#64748b}
.kpi-card{background:linear-gradient(135deg,#002B49 0%,#1e3a5f 100%);border-radius:12px;padding:1.2rem 1.5rem;color:white;text-align:center;box-shadow:0 4px 14px rgba(0,43,73,.15);margin-bottom:8px}
.kpi-card .valor{font-size:2.4rem;font-weight:300}
.kpi-card .label{font-size:.8rem;opacity:.8;margin-top:4px}
.alerta-roja{background:#fef2f2;border-left:4px solid #ef4444;padding:.8rem 1rem;border-radius:6px;margin:.4rem 0}
.alerta-verde{background:#f0fdf4;border-left:4px solid #8DC63F;padding:.8rem 1rem;border-radius:6px;margin:.4rem 0}
.alerta-ambar{background:#fffbeb;border-left:4px solid #f59e0b;padding:.8rem 1rem;border-radius:6px;margin:.4rem 0}
@media(max-width:768px){.sh-cards{flex-direction:column;margin:-30px 16px 30px}.sh-card{width:100%}.sh-hero h1{font-size:28px}.sh-hero p{font-size:15px}}
</style>
""", unsafe_allow_html=True)

# ── Datos maestros ──
ESTRUCTURA = {
    "Minera Spence":  {"faenas":["Spence BHP"],"ruta":"Spence/Carpeta_Arranque"},
    "Codelco":        {"faenas":["Radomiro Tomic","Chuquicamata","Ministro Hales"],"ruta":"Codelco/Contratos_Estandar"},
    "Minera El Abra": {"faenas":["Mina","Planta"],"ruta":"El_Abra/Documentos"},
    "Centinela":      {"faenas":["Mina","Planta SX-EW"],"ruta":"Centinela/Documentos"},
}
REQUISITOS = {
    "Minera Spence":  ["Validación fotográfica ECF21","Firma administrador en matriz base","Acreditación vigente de equipos"],
    "Codelco":        ["LOD semanal enviado","Reporte de observaciones conductuales","Matriz de riesgos actualizada"],
    "Minera El Abra": ["Charla 5 minutos firmada","Validación ingreso a planta"],
    "Centinela":      ["Registro All Scan diario","Revisión EPP específico"],
}
ACTIVIDADES = [
    {"actividad":"Registro FYS / ECF21 diario","frecuencia":"Diaria","dias":1,"modulo":"FYS","cliente":"Codelco"},
    {"actividad":"Actualización ECF21 Terreno","frecuencia":"Diaria","dias":1,"modulo":"Terreno","cliente":"Minera Spence"},
    {"actividad":"Revisión LOD semanal","frecuencia":"Semanal","dias":7,"modulo":"RESSO","cliente":"Codelco"},
    {"actividad":"Acreditación Equipos","frecuencia":"Semanal","dias":5,"modulo":"Legal","cliente":"Minera Spence"},
    {"actividad":"Reunión CPHS","frecuencia":"Mensual","dias":30,"modulo":"Legal","cliente":"Minera El Abra"},
    {"actividad":"Registro All Scan","frecuencia":"Diaria","dias":1,"modulo":"Terreno","cliente":"Centinela"},
    {"actividad":"Revisión EPP específico","frecuencia":"Semanal","dias":5,"modulo":"Legal","cliente":"Centinela"},
]

# ══════════════════════════════════════════════════════════════
def vista_landing():
    # Barra superior
    col1, col2, col3 = st.columns([2,4,2])
    with col1:
        st.markdown("<div style='padding:10px 0 0 8px'><span style='font-family:Montserrat,sans-serif;font-weight:900;font-size:22px;color:#002B49'>SMART HSE</span><br><span style='background:#55B4B0;color:white;font-size:9px;font-weight:700;padding:1px 7px;border-radius:3px;letter-spacing:2px'>CHILE</span></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='padding-top:14px;text-align:center'><span style='color:#4A5568;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin:0 14px'>Soluciones</span><span style='color:#4A5568;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin:0 14px'>Tecnología</span><span style='color:#4A5568;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin:0 14px'>Nosotros</span></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div style='padding-top:6px'>", unsafe_allow_html=True)
        if st.button("🔒 Acceder a Consola", use_container_width=True, type="primary"):
            st.session_state["vista"] = "login"
            st.rerun()
    st.markdown("<hr style='margin:0;border:none;border-top:1px solid #e2e8f0'>", unsafe_allow_html=True)

    st.markdown("""
    <div class="sh-hero">
        <h1>Revolucionando la gestión HSE transversal en Chile</h1>
        <p>Potenciamos la seguridad, el cumplimiento normativo DS.44 y el crecimiento sostenible en minería y contratistas de todo el territorio.</p>
        <a href="mailto:contacto@smarthse.cl" class="sh-btn-hero">Descubra cómo simplificar el DS.44</a>
    </div>
    <div class="sh-cards">
        <div class="sh-card"><div class="sh-card-icon">⚠️</div><h3>Gestión de Riesgos</h3><p>Identificación, evaluación y control de peligros según DS.44 y normativa SERNAGEOMIN.</p></div>
        <div class="sh-card"><div class="sh-card-icon">📋</div><h3>Cumplimiento Normativo</h3><p>Seguimiento en tiempo real de obligaciones legales mineras y vencimientos críticos.</p></div>
        <div class="sh-card"><div class="sh-card-icon">📊</div><h3>Análisis y Datos</h3><p>Dashboards con KPIs de seguridad operacional y reportes ejecutivos automatizados.</p></div>
        <div class="sh-card"><div class="sh-card-icon">🛡️</div><h3>Cultura de Seguridad</h3><p>Programas de capacitación y gestión del comportamiento seguro en terreno.</p></div>
    </div>
    <div class="sh-footer">
        <div style='font-family:Montserrat,sans-serif;font-weight:700;font-size:18px;color:white;letter-spacing:2px;margin-bottom:8px'>SMART HSE CHILE</div>
        <p>Plataforma de gestión HSE para la minería y contratistas en Chile</p>
        <p style='margin-top:12px'><a href='mailto:contacto@smarthse.cl'>contacto@smarthse.cl</a> &nbsp;·&nbsp; <a href='https://smarthse.cl'>smarthse.cl</a></p>
        <div class='sh-footer-sep'>© 2025 Smart HSE Chile · Todos los derechos reservados.</div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
def vista_login():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1,1.2,1])
    with col:
        st.markdown("<div style='text-align:center;margin-bottom:28px'><div style='font-family:Montserrat,sans-serif;font-weight:900;font-size:2.6rem;color:#002B49'>SMART HSE</div><div style='display:inline-block;background:#55B4B0;color:white;font-size:10px;font-weight:700;padding:2px 10px;border-radius:4px;letter-spacing:2px;margin-top:4px'>CHILE</div><p style='color:#64748b;margin-top:14px;font-weight:300;font-size:14px'>Consola de Gestión Operativa · DS.44</p></div>", unsafe_allow_html=True)
        with st.form("login"):
            st.text_input("Correo electrónico", placeholder="correo@empresa.cl")
            clave = st.text_input("Contraseña", type="password")
            ca, cb = st.columns(2)
            volver   = ca.form_submit_button("← Volver", use_container_width=True)
            ingresar = cb.form_submit_button("Ingresar →", type="primary", use_container_width=True)
        if ingresar:
            if clave == APP_PASSWORD:
                st.session_state.update({"autenticado":True,"vista":"consola"})
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
        if volver:
            st.session_state["vista"] = "landing"
            st.rerun()

# ══════════════════════════════════════════════════════════════
def vista_consola():
    st.markdown("<style>section[data-testid='stSidebar']{display:flex!important}.block-container{padding:2rem!important;max-width:100%!important}</style>", unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("<div style='text-align:center;padding:14px 0 6px'><div style='font-family:Montserrat,sans-serif;font-weight:900;font-size:20px;color:#002B49'>SMART HSE</div><div style='display:inline-block;background:#55B4B0;color:white;font-size:9px;font-weight:700;padding:1px 8px;border-radius:3px;letter-spacing:2px'>CHILE</div></div>", unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("Selección de Faena")
        cliente = st.selectbox("Cliente:", list(ESTRUCTURA.keys()))
        faena   = st.selectbox("Faena:", ESTRUCTURA[cliente]["faenas"])
        st.session_state["ruta_activa"] = ESTRUCTURA[cliente]["ruta"]
        st.success(f"📁 {st.session_state['ruta_activa']}")
        st.markdown("---")
        if st.button("🔒 Cerrar Sesión", use_container_width=True):
            st.session_state.update({"autenticado":False,"vista":"landing"})
            st.rerun()

    st.title(f"Gestión Operativa: {faena}")
    st.caption(f"Smart HSE Chile · {datetime.today().strftime('%d/%m/%Y')} · Asesora Senior")

    tab1, tab2, tab3, tab4 = st.tabs(["⚡ Acción Inmediata","🚀 Onboarding","📅 Agenda","📄 Cartas N/A"])

    with tab1:
        c1,c2,c3 = st.columns(3)
        c1.markdown("<div class='kpi-card'><div class='valor'>12</div><div class='label'>Documentos RESSO</div></div>", unsafe_allow_html=True)
        c2.markdown("<div class='kpi-card'><div class='valor'>45</div><div class='label'>Registros FYS</div></div>", unsafe_allow_html=True)
        c3.markdown("<div class='kpi-card'><div class='valor'>8</div><div class='label'>Ítems N/A detectados</div></div>", unsafe_allow_html=True)
        st.divider()
        st.markdown("#### ⚡ Foco del Día — Top 3")
        acts = sorted([a for a in ACTIVIDADES if a["cliente"]==cliente], key=lambda x:x["dias"])[:3]
        if not acts:
            st.info("Sin tareas urgentes para este cliente.")
        for i,a in enumerate(acts,1):
            proxima=(datetime.today()+timedelta(days=a["dias"])).strftime("%d/%m/%Y")
            clase="alerta-roja" if a["dias"]<=1 else "alerta-ambar" if a["dias"]<=7 else "alerta-verde"
            icono="🔴" if a["dias"]<=1 else "⚠️" if a["dias"]<=7 else "✅"
            st.markdown(f'<div class="{clase}"><b>{i}. {icono} {a["actividad"]}</b><br><span style="font-size:.83rem">📅 Próxima: {proxima} · Módulo: {a["modulo"]}</span></div>', unsafe_allow_html=True)
        reqs=REQUISITOS.get(cliente,[])
        if reqs:
            st.divider()
            st.markdown("#### 📋 Requisitos Formales del Cliente")
            for i,r in enumerate(reqs,1): st.markdown(f"**{i}.** {r}")

    with tab2:
        st.info(f"Estructura activa: **{st.session_state['ruta_activa']}**")
        with st.form("onboarding"):
            c=st.text_input("N° Contrato:",value=st.session_state["contrato"])
            a=st.text_input("Actividad / Macro Proceso:",value=st.session_state["actividad"])
            l=st.text_input("Lugar / Faena:",value=st.session_state["lugar"])
            if st.form_submit_button("💾 Guardar",type="primary"):
                st.session_state.update({"contrato":c,"actividad":a,"lugar":l})
                st.success("✅ Guardado.")

    with tab3:
        df=pd.DataFrame(ACTIVIDADES)
        df.columns=["Actividad","Frecuencia","Días","Módulo","Cliente"]
        st.dataframe(df,use_container_width=True,hide_index=True)

    with tab4:
        st.markdown("#### 📄 Generador de Cartas de No Aplicabilidad")
        with st.form("carta"):
            ca,cb=st.columns(2)
            with ca:
                dest=st.text_input("Empresa destinataria:",value=cliente)
                nc=st.text_input("N° Contrato:",value=st.session_state.get("contrato",""))
                fecha=st.date_input("Fecha:",value=datetime.today())
            with cb:
                norma=st.text_input("Norma / Ítem N/A:",placeholder="Ej: DS44 Art. 23")
                justif=st.text_area("Justificación:",height=112,placeholder="Ej: La actividad no contempla uso de explosivos...")
            gen=st.form_submit_button("📄 Generar Vista Previa",type="primary",use_container_width=True)
        if gen:
            if not norma or not justif:
                st.warning("Completa la Norma/Ítem y la Justificación.")
            else:
                meses={"January":"enero","February":"febrero","March":"marzo","April":"abril","May":"mayo","June":"junio","July":"julio","August":"agosto","September":"septiembre","October":"octubre","November":"noviembre","December":"diciembre"}
                fe=fecha.strftime("%d de %B de %Y")
                for en,es in meses.items(): fe=fe.replace(en,es)
                st.divider()
                st.markdown(f"""**Vista Previa — Carta de No Aplicabilidad**
---
**Ref.:** Carta N/A · Contrato {nc or "—"} · {fe}

**Señores** {dest} — Presente

**Asunto: Declaración de No Aplicabilidad — {norma}**

Por medio de la presente, **Smart HSE Chile** declara formalmente que el ítem **{norma}** no aplica para las actividades desarrolladas en la faena **{faena}**, bajo contrato N° **{nc or "—"}**.

**Justificación técnica:** {justif}

Sin otro particular, saluda atentamente,
**Smart HSE Chile** · contacto@smarthse.cl · smarthse.cl

---""")
                st.caption("⚠️ Copie el texto a Word para agregar firma, timbre y logo antes de enviar.")

# ══════════════════════════════════════════════════════════════
#  ROUTER
# ══════════════════════════════════════════════════════════════
v = st.session_state["vista"]
if v == "landing":
    vista_landing()
elif v == "login":
    vista_login()
elif v == "consola":
    vista_consola() if st.session_state["autenticado"] else (st.session_state.update({"vista":"login"}), st.rerun())
