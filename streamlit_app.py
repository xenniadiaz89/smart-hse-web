import streamlit as st
import pandas as pd
import altair as alt
import io
import os
import base64
import pathlib
from datetime import datetime, timedelta, date

# Paleta de marca (logo Smart HSE)
BRAND = {"navy":"#0E3A5F","blue":"#16609E","cyan":"#27AAE1","green":"#5BBA47",
         "amber":"#F59E0B","red":"#EF4444"}

# ── Assets de marca (logo) ──────────────────────────────────
_BASE = os.path.dirname(os.path.abspath(__file__))
def _b64(rel):
    try: return base64.b64encode((pathlib.Path(_BASE)/rel).read_bytes()).decode()
    except Exception: return ""
_LOGO_B64 = _b64("assets/logo_mark.png")
LOGO_URI = f"data:image/png;base64,{_LOGO_B64}" if _LOGO_B64 else ""
_FAVICON = os.path.join(_BASE, "assets", "favicon.png")

st.set_page_config(
    page_title="Smart HSE Chile",
    page_icon=_FAVICON if os.path.exists(_FAVICON) else "🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def logo_img(height=46, cls=""):
    """Devuelve el <img> del emblema, o '' si no hay asset."""
    return f"<img src='{LOGO_URI}' class='{cls}' style='height:{height}px;width:auto;display:inline-block'/>" if LOGO_URI else ""

# ── Estado ──────────────────────────────────────────────────
def init():
    for k,v in {"vista":"landing","auth":False,"contrato":"","actividad":"","lugar":"","ruta":"","incidentes":[]}.items():
        if k not in st.session_state: st.session_state[k]=v
init()

APP_PW = os.environ.get("APP_PASSWORD", "smarthse2025")

# ── CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800;900&family=Inter:wght@300;400;500;600;700&display=swap');
:root{
  --navy:#0E3A5F; --blue:#16609E; --cyan:#27AAE1; --green:#5BBA47;
  --ink:#0E3A5F; --muted:#64748b; --line:#e2e8f0;
}
#MainMenu,footer,header{visibility:hidden}
.block-container{padding:0!important;max-width:100%!important}
section[data-testid="stSidebar"]{display:none}
html,body,[class*="css"]{font-family:'Inter',sans-serif}
@keyframes fadeUp{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:translateY(0)}}
.fu{animation:fadeUp .7s cubic-bezier(.2,.7,.2,1) both}
.fu2{animation:fadeUp .7s .12s cubic-bezier(.2,.7,.2,1) both}
.fu3{animation:fadeUp .7s .24s cubic-bezier(.2,.7,.2,1) both}
/* ── Hero ── */
.hero{position:relative;overflow:hidden;background:linear-gradient(125deg,var(--navy) 0%,var(--blue) 55%,#1f7fc0 100%);padding:120px 20px 150px;text-align:center;color:white;min-height:70vh;display:flex;flex-direction:column;justify-content:center;align-items:center}
.hero::before{content:"";position:absolute;inset:0;background:radial-gradient(circle at 78% 18%,rgba(91,186,71,.38),transparent 42%),radial-gradient(circle at 12% 88%,rgba(39,170,225,.45),transparent 45%);pointer-events:none}
.hero::after{content:"";position:absolute;top:-30%;right:-12%;width:520px;height:520px;border:2px solid rgba(255,255,255,.07);border-radius:50%;box-shadow:0 0 0 60px rgba(255,255,255,.04);pointer-events:none}
.hero>*{position:relative;z-index:2}
.hero-logo{width:122px;height:122px;margin:0 auto 20px;border-radius:50%;background:rgba(255,255,255,.96);display:flex;align-items:center;justify-content:center;box-shadow:0 16px 44px rgba(0,0,0,.28);border:1px solid rgba(255,255,255,.5)}
.hero .eyebrow{display:inline-block;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.25);color:#dff3ff;font-size:11px;font-weight:600;letter-spacing:2px;text-transform:uppercase;padding:7px 16px;border-radius:30px;margin-bottom:24px;backdrop-filter:blur(6px)}
.hero h1{font-family:'Montserrat',sans-serif;font-weight:900;font-size:50px;max-width:940px;margin:0 auto 22px;text-transform:uppercase;line-height:1.12;text-shadow:0 4px 18px rgba(0,0,0,.25)}
.hero h1 .hl{color:var(--green)}
.hero p{font-size:18px;max-width:720px;margin:0 auto 40px;font-weight:300;line-height:1.7;color:#e8f4fb}
.btn-hero{background:var(--cyan);color:white;padding:16px 38px;border-radius:30px;font-weight:700;font-size:14px;text-decoration:none;text-transform:uppercase;letter-spacing:1px;display:inline-block;box-shadow:0 10px 26px rgba(39,170,225,.45);transition:transform .25s,box-shadow .25s;margin:0 8px}
.btn-hero:hover{transform:translateY(-3px);box-shadow:0 16px 34px rgba(39,170,225,.55)}
.btn-ghost{background:transparent;color:white;padding:14px 34px;border-radius:30px;font-weight:700;font-size:14px;text-decoration:none;text-transform:uppercase;letter-spacing:1px;display:inline-block;border:2px solid rgba(255,255,255,.4);transition:background .25s;margin:0 8px}
.btn-ghost:hover{background:rgba(255,255,255,.12)}
/* ── Banda de claims ── */
.claims{display:flex;justify-content:center;flex-wrap:wrap;gap:14px;max-width:980px;margin:36px auto 0}
.claim{display:flex;align-items:center;gap:9px;background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.22);color:#eaf6ff;font-size:13px;font-weight:600;padding:10px 18px;border-radius:30px;backdrop-filter:blur(6px)}
.claim .dot{width:8px;height:8px;border-radius:50%;background:var(--green);box-shadow:0 0 10px var(--green)}
/* ── Cards servicios ── */
.cards{display:flex;justify-content:center;gap:22px;max-width:1180px;margin:-70px auto 70px;position:relative;z-index:10;padding:0 20px;flex-wrap:wrap}
.card{background:rgba(255,255,255,.92);backdrop-filter:blur(8px);padding:38px 22px;border-radius:18px;width:22%;min-width:210px;text-align:center;box-shadow:0 18px 44px rgba(14,58,95,.12);border:1px solid #eef3f8;border-top:4px solid transparent;transition:transform .3s,border-color .3s,box-shadow .3s}
.card:hover{transform:translateY(-8px);border-top-color:var(--cyan);box-shadow:0 26px 56px rgba(22,96,158,.20)}
.card-icon{font-size:30px;width:64px;height:64px;line-height:64px;margin:0 auto 6px;border-radius:16px;background:linear-gradient(135deg,var(--cyan),var(--blue));color:white;box-shadow:0 8px 20px rgba(39,170,225,.35)}
.card h3{font-family:'Montserrat',sans-serif;font-weight:800;font-size:14px;color:var(--ink);text-transform:uppercase;margin:16px 0 8px}
.card p{font-size:13px;color:var(--muted);line-height:1.6}
/* ── Secciones ── */
.sec{max-width:1080px;margin:0 auto;padding:30px 20px 10px}
.sec-tag{text-align:center;color:var(--cyan);font-weight:700;font-size:12px;letter-spacing:3px;text-transform:uppercase;margin-bottom:8px}
.sec-h{text-align:center;font-family:'Montserrat',sans-serif;font-weight:800;font-size:30px;color:var(--ink);margin:0 0 8px}
.sec-sub{text-align:center;color:var(--muted);font-size:15px;max-width:640px;margin:0 auto 38px;line-height:1.6}
.steps{display:flex;gap:22px;flex-wrap:wrap;justify-content:center}
.step{flex:1;min-width:240px;background:#fff;border:1px solid var(--line);border-radius:16px;padding:30px 24px;position:relative;transition:transform .3s,box-shadow .3s}
.step:hover{transform:translateY(-6px);box-shadow:0 18px 40px rgba(14,58,95,.10)}
.step .num{font-family:'Montserrat',sans-serif;font-weight:900;font-size:42px;line-height:1;background:linear-gradient(135deg,var(--cyan),var(--green));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:12px}
.step h4{font-family:'Montserrat',sans-serif;font-weight:800;font-size:16px;color:var(--ink);margin:0 0 8px}
.step p{font-size:13.5px;color:var(--muted);line-height:1.6;margin:0}
.step .arrow{position:absolute;right:-18px;top:50%;transform:translateY(-50%);color:var(--cyan);font-size:24px;font-weight:700}
/* ── CTA / contacto ── */
.ctaband{background:linear-gradient(120deg,var(--navy),var(--blue));border-radius:22px;max-width:1080px;margin:46px auto 10px;padding:8px;box-shadow:0 24px 60px rgba(14,58,95,.22)}
/* ── Footer ── */
.sh-footer{background:var(--navy);color:#9fb6c9;text-align:center;padding:52px 20px;font-size:13px;margin-top:46px}
.sh-footer a{color:var(--cyan);text-decoration:none}
.ftr-sep{border-top:1px solid rgba(255,255,255,.10);margin-top:22px;padding-top:16px;font-size:11px;color:#6f879b}
/* ── Logo wordmark ── */
.wm{font-family:'Montserrat',sans-serif;font-weight:900;letter-spacing:.5px}
.wm .smart{color:var(--blue)} .wm .hse{color:var(--cyan)}
.chip-chile{background:var(--cyan);color:white;font-weight:700;border-radius:4px;letter-spacing:3px;display:inline-block}
/* ── Consola ── */
.kpi{background:linear-gradient(135deg,var(--navy) 0%,var(--blue) 100%);border-radius:14px;padding:1.2rem 1.5rem;color:white;text-align:center;box-shadow:0 8px 22px rgba(22,96,158,.22);margin-bottom:8px;border:1px solid rgba(255,255,255,.06)}
.kpi.k-cyan{background:linear-gradient(135deg,var(--blue),var(--cyan))}
.kpi.k-green{background:linear-gradient(135deg,#3c9e7a,var(--green))}
.kpi .val{font-size:2.5rem;font-weight:300;line-height:1}
.kpi .lbl{font-size:.8rem;opacity:.9;margin-top:6px;letter-spacing:.5px}
.ar{background:#fef2f2;border-left:4px solid #ef4444;padding:.8rem 1rem;border-radius:6px;margin:.4rem 0}
.ag{background:#f0fdf4;border-left:4px solid var(--green);padding:.8rem 1rem;border-radius:6px;margin:.4rem 0}
.aa{background:#fffbeb;border-left:4px solid #f59e0b;padding:.8rem 1rem;border-radius:6px;margin:.4rem 0}
.nota{background:#fff8e1;border-left:4px solid #FFA000;padding:12px 16px;border-radius:6px;font-size:.85rem}
/* ── Botones nativos Streamlit → cyan ── */
.stButton>button[kind="primary"],.stForm button[kind="primaryFormSubmit"],.stDownloadButton>button{background:var(--cyan)!important;border-color:var(--cyan)!important}
.stButton>button[kind="primary"]:hover,.stDownloadButton>button:hover{background:var(--blue)!important;border-color:var(--blue)!important}
@media(max-width:768px){
  .cards{flex-direction:column;margin:-40px 16px 40px}.card{width:100%}
  .hero h1{font-size:30px}.hero{padding:90px 18px 120px}
  .btn-hero,.btn-ghost{display:block;margin:8px auto;max-width:300px}
  .steps{flex-direction:column}.step .arrow{display:none}
  .sec-h{font-size:24px}
}
</style>
""", unsafe_allow_html=True)

# ── Datos maestros ───────────────────────────────────────────
ESTRUCTURA = {
    "Minera Spence":  {"faenas":["Spence BHP"],"ruta":"Spence/Carpeta_Arranque"},
    "Codelco DRT":    {"faenas":["Radomiro Tomic","Chuquicamata","Ministro Hales"],"ruta":"Codelco/Contratos_Estandar"},
    "Minera El Abra": {"faenas":["Mina","Planta"],"ruta":"El_Abra/Documentos"},
    "Centinela":      {"faenas":["Mina","Planta SX-EW"],"ruta":"Centinela/Documentos"},
}
REQUISITOS = {
    "Minera Spence":  ["Validación fotográfica ECF21","Firma administrador en matriz base","Acreditación vigente de equipos"],
    "Codelco DRT":    ["LOD semanal enviado","Reporte de observaciones conductuales","Matriz de riesgos actualizada"],
    "Minera El Abra": ["Charla 5 minutos firmada","Validación ingreso a planta"],
    "Centinela":      ["Registro All Scan diario","Revisión EPP específico"],
}
ACTIVIDADES = [
    {"actividad":"Registro FYS / ECF21 diario","frecuencia":"Diaria","dias":1,"modulo":"FYS","cliente":"Codelco DRT"},
    {"actividad":"Actualización ECF21 Terreno","frecuencia":"Diaria","dias":1,"modulo":"Terreno","cliente":"Minera Spence"},
    {"actividad":"Revisión LOD semanal","frecuencia":"Semanal","dias":7,"modulo":"RESSO","cliente":"Codelco DRT"},
    {"actividad":"Acreditación Equipos","frecuencia":"Semanal","dias":5,"modulo":"Legal","cliente":"Minera Spence"},
    {"actividad":"Reunión CPHS","frecuencia":"Mensual","dias":30,"modulo":"Legal","cliente":"Minera El Abra"},
    {"actividad":"Registro All Scan","frecuencia":"Diaria","dias":1,"modulo":"Terreno","cliente":"Centinela"},
    {"actividad":"Revisión EPP específico","frecuencia":"Semanal","dias":5,"modulo":"Legal","cliente":"Centinela"},
]
NA_ITEMS = {
    "405":[
        ("CPHS - Comité Paritario de H&S","Empresa con menos de 25 trabajadores en faena. No aplica constitución de CPHS conforme Art. 66 Ley 16.744."),
        ("Maquinaria Autopropulsada (DS 44 §8.2)","El contrato 405 no contempla operación de equipos autopropulsados de minería. No aplica acreditación SERNAGEOMIN para esta categoría."),
        ("Buceo y Trabajo Subacuático","Las actividades del contrato no incluyen trabajos en medios acuáticos ni confinados bajo nivel de agua."),
        ("Exposición a Agentes Biológicos (DS 594)","Las tareas del alcance no generan exposición a agentes biológicos clasificados. No aplica vigilancia específica por este concepto."),
    ],
    "118":[
        ("CPHS - Comité Paritario de H&S","Dotación en faena inferior a 25 trabajadores de forma permanente. No aplica obligación de CPHS según Art. 66 Ley 16.744."),
        ("Trabajos en Caliente - Permiso Especial (RESSO V9 §4.3)","El contrato 118 no contempla soldadura, corte térmico ni operaciones con llama. No se emiten permisos de trabajo en caliente."),
        ("Plan de Gestión de Contratistas de Alto Riesgo","Las actividades del alcance están clasificadas como Riesgo Moderado según matriz de criticidad Codelco DRT. No aplica protocolo de alto riesgo."),
        ("Registro Dosimétrico PREXOR","Medición de ruido ocupacional indica niveles bajo 82 dB(A) TWA. No aplica programa de vigilancia audiométrica por este contrato."),
    ],
}
CONTRATOS = ["405","118","109100077748"]
FLUJOS    = ["FYS Diario","RESSO"]

def fecha_es(d=None):
    d = d or date.today()
    meses={"January":"enero","February":"febrero","March":"marzo","April":"abril","May":"mayo","June":"junio","July":"julio","August":"agosto","September":"septiembre","October":"octubre","November":"noviembre","December":"diciembre"}
    t=d.strftime("%d de %B de %Y")
    for en,es in meses.items(): t=t.replace(en,es)
    return t

# ════════════════════════════════════════════════════════════
# VISTA LANDING
# ════════════════════════════════════════════════════════════
def landing():
    # ── Navbar ──
    c1,c2,c3 = st.columns([2,4,2])
    with c1:
        st.markdown(f"<div style='display:flex;align-items:center;gap:10px;padding:6px 0 0 8px'>{logo_img(46)}<div class='wm'><span style='font-size:22px'><span class='smart'>SMART</span> <span class='hse'>HSE</span></span><br><span class='chip-chile' style='font-size:9px;padding:1px 8px'>CHILE</span></div></div>",unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='padding-top:16px;text-align:center'><span style='color:#4A5568;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin:0 14px'>Soluciones</span><span style='color:#4A5568;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin:0 14px'>Tecnología</span><span style='color:#4A5568;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin:0 14px'>Nosotros</span></div>",unsafe_allow_html=True)
    with c3:
        if st.button("🔒 Acceder a Consola",use_container_width=True,type="primary"):
            st.session_state["vista"]="login"; st.rerun()
    st.markdown("<hr style='margin:0;border:none;border-top:1px solid #e2e8f0'>",unsafe_allow_html=True)

    # ── Hero + claims verificables ──
    st.markdown(f"""
    <div class="hero">
        <div class="hero-logo fu">{logo_img(76)}</div>
        <div class="eyebrow fu">🛡️ Seguridad · Cumplimiento · Trazabilidad</div>
        <h1 class="fu">Gestión HSE inteligente para la <span class="hl">minería</span> y contratistas de Chile</h1>
        <p class="fu2">Centralizamos el cumplimiento DS.44, el estándar RESSO V9 de Codelco y la trazabilidad documental en una sola plataforma. Menos planillas, más control.</p>
        <div class="fu3">
            <a href="#contacto" class="btn-hero">Solicitar demo</a>
            <a href="#consola" class="btn-ghost">Conocer la plataforma</a>
        </div>
        <div class="claims fu3">
            <div class="claim"><span class="dot"></span>Cumplimiento DS.44</div>
            <div class="claim"><span class="dot"></span>Estándar RESSO V9 · Codelco</div>
            <div class="claim"><span class="dot"></span>Trazabilidad documental total</div>
            <div class="claim"><span class="dot"></span>Minería y contratistas en todo Chile</div>
        </div>
    </div>
    <div class="cards">
        <div class="card fu"><div class="card-icon">⚠️</div><h3>Gestión de Riesgos</h3><p>Identificación, evaluación y control de peligros según DS.44 y normativa SERNAGEOMIN.</p></div>
        <div class="card fu"><div class="card-icon">📋</div><h3>Cumplimiento Normativo</h3><p>Seguimiento en tiempo real de obligaciones legales mineras y vencimientos críticos.</p></div>
        <div class="card fu2"><div class="card-icon">📊</div><h3>Análisis y Datos</h3><p>Dashboards con KPIs de seguridad operacional y reportes ejecutivos automatizados.</p></div>
        <div class="card fu2"><div class="card-icon">🛡️</div><h3>Cultura de Seguridad</h3><p>Programas de capacitación y gestión del comportamiento seguro en terreno.</p></div>
    </div>
    """,unsafe_allow_html=True)

    # ── Cómo funciona ──
    st.markdown("""
    <div class="sec">
        <div class="sec-tag">Cómo funciona</div>
        <div class="sec-h">De la planilla al reporte, en tres pasos</div>
        <div class="sec-sub">Un flujo simple que ordena la documentación HSE de tus contratos sin perder trazabilidad.</div>
        <div class="steps">
            <div class="step"><div class="num">01</div><h4>Carga</h4><p>Sube matrices, registros FYS/ECF21 y documentos del contrato. El sistema los clasifica y renombra con el estándar correcto.</p><span class="arrow">→</span></div>
            <div class="step"><div class="num">02</div><h4>Analiza</h4><p>Detecta brechas en tu GAP Analysis, identifica ítems No Aplicables y prioriza el foco del día por faena y cliente.</p><span class="arrow">→</span></div>
            <div class="step"><div class="num">03</div><h4>Reporta</h4><p>Genera cartas de No Aplicabilidad, registros de incidentes y descargas en Excel listas para presentar al mandante.</p></div>
        </div>
    </div>
    <div id="consola"></div>
    """,unsafe_allow_html=True)

    # ── Contacto (captura de lead) ──
    st.markdown("<div id='contacto'></div>",unsafe_allow_html=True)
    st.markdown("""
    <div class="sec">
        <div class="sec-tag">Hablemos</div>
        <div class="sec-h">Solicita una demostración</div>
        <div class="sec-sub">Cuéntanos de tu operación y te mostramos cómo Smart HSE simplifica el cumplimiento DS.44 y RESSO en tus contratos.</div>
    </div>
    """,unsafe_allow_html=True)
    _,fc,_ = st.columns([1,2,1])
    with fc:
        with st.form("lead"):
            lc1,lc2 = st.columns(2)
            l_nombre  = lc1.text_input("Nombre",placeholder="Tu nombre")
            l_empresa = lc2.text_input("Empresa",placeholder="Empresa / contratista")
            l_correo  = st.text_input("Correo electrónico",placeholder="correo@empresa.cl")
            l_msg     = st.text_area("¿Qué necesitas resolver?",placeholder="Ej: ordenar la documentación RESSO de mi contrato con Codelco.",height=90)
            enviar = st.form_submit_button("Solicitar demo →",type="primary",use_container_width=True)
        if enviar:
            if not l_nombre.strip() or not l_correo.strip():
                st.error("Por favor completa al menos tu nombre y correo.")
            else:
                st.session_state.setdefault("leads",[]).append({
                    "nombre":l_nombre,"empresa":l_empresa,"correo":l_correo,
                    "mensaje":l_msg,"fecha":datetime.now().strftime("%Y-%m-%d %H:%M")})
                asunto=f"Solicitud de demo — {l_empresa or l_nombre}".replace(" ","%20")
                cuerpo=(f"Nombre: {l_nombre}%0D%0AEmpresa: {l_empresa}%0D%0ACorreo: {l_correo}"
                        f"%0D%0A%0D%0AMensaje:%0D%0A{l_msg}").replace(" ","%20")
                mailto=f"mailto:contacto@smarthse.cl?subject={asunto}&body={cuerpo}"
                st.success(f"✅ ¡Gracias, {l_nombre.split()[0]}! Recibimos tu solicitud. Te contactaremos a la brevedad.")
                st.markdown(f"<a href='{mailto}' class='btn-hero' style='margin-top:6px'>📧 Enviar también por correo</a>",unsafe_allow_html=True)

    # ── Footer ──
    st.markdown("""
    <div class="sh-footer">
        <div class="wm" style='font-size:20px;color:white;letter-spacing:1px;margin-bottom:8px'>SMART <span style='color:var(--cyan)'>HSE</span> CHILE</div>
        <p>Plataforma de gestión HSE para la minería y contratistas en Chile</p>
        <p style='margin-top:12px'><a href='mailto:contacto@smarthse.cl'>contacto@smarthse.cl</a> &nbsp;·&nbsp; <a href='https://smarthse.cl'>smarthse.cl</a></p>
        <div class='ftr-sep'>© 2025 Smart HSE Chile · Todos los derechos reservados.</div>
    </div>""",unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# VISTA LOGIN
# ════════════════════════════════════════════════════════════
def login():
    st.markdown("<br><br><br>",unsafe_allow_html=True)
    _,col,_ = st.columns([1,1.2,1])
    with col:
        st.markdown(f"<div style='text-align:center;margin-bottom:28px'><div style='margin-bottom:10px'>{logo_img(72)}</div><div class='wm' style='font-size:2.6rem'><span class='smart'>SMART</span> <span class='hse'>HSE</span></div><div class='chip-chile' style='font-size:10px;padding:2px 12px;margin-top:6px'>CHILE</div><p style='color:#64748b;margin-top:14px;font-weight:300;font-size:14px'>Consola de Gestión Operativa · DS.44</p></div>",unsafe_allow_html=True)
        with st.form("login"):
            st.text_input("Correo electrónico",placeholder="correo@empresa.cl")
            pw=st.text_input("Contraseña",type="password")
            ca,cb=st.columns(2)
            volver=ca.form_submit_button("← Volver",use_container_width=True)
            entrar=cb.form_submit_button("Ingresar →",type="primary",use_container_width=True)
        if entrar:
            if pw==APP_PW: st.session_state.update({"auth":True,"vista":"consola"}); st.rerun()
            else: st.error("Contraseña incorrecta.")
        if volver: st.session_state["vista"]="landing"; st.rerun()

# ════════════════════════════════════════════════════════════
# VISTA CONSOLA
# ════════════════════════════════════════════════════════════
def consola():
    st.markdown("<style>section[data-testid='stSidebar']{display:flex!important}.block-container{padding:2rem!important;max-width:100%!important}</style>",unsafe_allow_html=True)
    with st.sidebar:
        st.markdown(f"<div style='text-align:center;padding:14px 0 6px'><div style='margin-bottom:6px'>{logo_img(56)}</div><div class='wm' style='font-size:20px'><span class='smart'>SMART</span> <span class='hse'>HSE</span></div><div class='chip-chile' style='font-size:9px;padding:1px 9px'>CHILE</div></div>",unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("Selección de Faena")
        cliente=st.selectbox("Cliente:",list(ESTRUCTURA.keys()))
        faena=st.selectbox("Faena:",ESTRUCTURA[cliente]["faenas"])
        st.session_state["ruta"]=ESTRUCTURA[cliente]["ruta"]
        st.success(f"📁 {st.session_state['ruta']}")
        st.markdown("---")
        if st.button("🔒 Cerrar Sesión",use_container_width=True):
            st.session_state.update({"auth":False,"vista":"landing"}); st.rerun()

    st.title(f"Gestión Operativa: {faena}")
    st.caption(f"Smart HSE Chile · {datetime.today().strftime('%d/%m/%Y')} · Asesora Senior")

    t1,t2,t3,t4,t5,t6 = st.tabs([
        "⚡ Acción Inmediata",
        "📥 Motor Documental",
        "📊 GAP Analysis",
        "📄 Cartas N/A",
        "📅 Agenda",
        "🚨 Incidentes",
    ])

    # ── TAB 1: Dashboard ────────────────────────────────────
    with t1:
        n_tareas = len([a for a in ACTIVIDADES if a["cliente"]==cliente])
        n_na     = sum(len(v) for v in NA_ITEMS.values())
        n_inc    = len(st.session_state["incidentes"])
        c1,c2,c3=st.columns(3)
        c1.markdown(f"<div class='kpi'><div class='val'>{n_tareas}</div><div class='lbl'>Tareas activas · {cliente}</div></div>",unsafe_allow_html=True)
        c2.markdown(f"<div class='kpi k-cyan'><div class='val'>{n_na}</div><div class='lbl'>Ítems N/A en catálogo</div></div>",unsafe_allow_html=True)
        c3.markdown(f"<div class='kpi k-green'><div class='val'>{n_inc}</div><div class='lbl'>Incidentes en sesión</div></div>",unsafe_allow_html=True)
        st.divider()
        st.markdown("#### ⚡ Foco del Día — Top 3")
        acts=sorted([a for a in ACTIVIDADES if a["cliente"]==cliente],key=lambda x:x["dias"])[:3]
        if not acts: st.info("Sin tareas urgentes para este cliente.")
        for i,a in enumerate(acts,1):
            px=(datetime.today()+timedelta(days=a["dias"])).strftime("%d/%m/%Y")
            cl="ar" if a["dias"]<=1 else "aa" if a["dias"]<=7 else "ag"
            ic="🔴" if a["dias"]<=1 else "⚠️" if a["dias"]<=7 else "✅"
            st.markdown(f'<div class="{cl}"><b>{i}. {ic} {a["actividad"]}</b><br><span style="font-size:.83rem">📅 Próxima: {px} · Módulo: {a["modulo"]}</span></div>',unsafe_allow_html=True)
        reqs=REQUISITOS.get(cliente,[])
        if reqs:
            st.divider(); st.markdown("#### 📋 Requisitos Formales del Cliente")
            for i,r in enumerate(reqs,1): st.markdown(f"**{i}.** {r}")

    # ── TAB 2: Motor Documental ─────────────────────────────
    with t2:
        st.subheader("Motor Documental — Ingreso y Clasificación")
        st.caption("Sube el documento, selecciona contrato y flujo. El sistema genera el nombre correcto y te lo entrega listo para archivar.")
        archivo=st.file_uploader("Selecciona el documento",type=["pdf","docx","xlsx","csv"])
        if archivo:
            ext=archivo.name.rsplit(".",1)[-1].lower()
            if ext in ["xlsx","csv"]:
                try:
                    df_prev=pd.read_excel(archivo) if ext=="xlsx" else pd.read_csv(archivo)
                    st.dataframe(df_prev,use_container_width=True)
                    st.caption(f"{len(df_prev)} filas · {len(df_prev.columns)} columnas")
                except Exception as e: st.warning(f"Vista previa no disponible: {e}")
            else:
                st.info(f"📎 **{archivo.name}** · {round(archivo.size/1024,1)} KB")
            st.divider()
            ca,cb=st.columns(2)
            contrato_m=ca.selectbox("Contrato",CONTRATOS)
            flujo_m=cb.selectbox("Flujo documental",FLUJOS)
            codigo="FYS" if flujo_m=="FYS Diario" else "RESSO"
            nombre_nuevo=f"{date.today().isoformat()}_{codigo}_{contrato_m}.{ext}"
            st.markdown(f"**Nombre generado:** `{nombre_nuevo}`")
            st.markdown(f"**Carpeta destino:** `{'05_Salida_FYS/'+contrato_m if flujo_m=='FYS Diario' else '04_Salida_RESSO'}/`")
            archivo.seek(0)
            st.download_button(
                label="⬇️ Descargar archivo renombrado",
                data=archivo.read(),
                file_name=nombre_nuevo,
                mime=archivo.type,
                type="primary",
                use_container_width=True
            )
        else:
            st.info("Sube un documento para comenzar el proceso de clasificación.")

    # ── TAB 3: GAP Analysis ─────────────────────────────────
    with t3:
        st.subheader("Base Documental y GAP Analysis")
        st.caption("Sube tu matriz Excel o CSV con columnas de estado/brecha. El sistema detecta automáticamente los ítems con incumplimiento.")
        archivos_gap=st.file_uploader("Cargar matrices GAP/FYS",type=["xlsx","xls","csv"],accept_multiple_files=True)
        if archivos_gap:
            for f in archivos_gap:
                ext_g=f.name.rsplit(".",1)[-1].lower()
                st.markdown(f"---\n#### 📋 {f.name}")
                try:
                    df=pd.read_excel(f) if ext_g in ["xlsx","xls"] else pd.read_csv(f)
                    df=df.dropna(how="all")
                    total=len(df)
                    cm1,cm2,cm3=st.columns(3)
                    cm1.metric("Total ítems",total)
                    col_est=next((c for c in df.columns if any(k in str(c).upper() for k in ["ESTADO","BRECHA","CUMPLIMIENTO","STATUS"])),None)
                    if col_est:
                        brechas=df[col_est].astype(str).str.upper().str.contains("NO|BRECHA|INCUMPLE|PENDIENTE",na=False).sum()
                        cumplidos=df[col_est].astype(str).str.upper().str.contains("SI|CUMPLE|OK|COMPLETO",na=False).sum()
                        cm2.metric("Brechas",int(brechas),delta=f"-{int(brechas)}",delta_color="inverse")
                        cm3.metric("Cumplidos",int(cumplidos),delta=f"+{int(cumplidos)}")
                        otros=max(total-int(brechas)-int(cumplidos),0)
                        dona=pd.DataFrame({
                            "Estado":["Cumplidos","Brechas","Otros"],
                            "Cantidad":[int(cumplidos),int(brechas),otros]})
                        dona=dona[dona["Cantidad"]>0]
                        if not dona.empty:
                            ch=alt.Chart(dona).mark_arc(innerRadius=58,cornerRadius=4).encode(
                                theta=alt.Theta("Cantidad:Q",stack=True),
                                color=alt.Color("Estado:N",scale=alt.Scale(
                                    domain=["Cumplidos","Brechas","Otros"],
                                    range=[BRAND["green"],BRAND["red"],BRAND["cyan"]]),
                                    legend=alt.Legend(title=None,orient="bottom")),
                                tooltip=["Estado","Cantidad"]
                            ).properties(height=240,title="Cumplimiento normativo")
                            st.altair_chart(ch,use_container_width=True)
                    else:
                        cm2.metric("Columna estado","No detectada")
                        cm3.metric("Filas con datos",total)
                    st.dataframe(df.astype(str),use_container_width=True)
                except Exception as e: st.error(f"Error leyendo {f.name}: {e}")
        else:
            st.info("Sube archivos Excel/CSV con 'GAP', 'FYS' o 'RESSO' en el nombre para activar el análisis de brechas normativas.")

    # ── TAB 4: Cartas N/A ───────────────────────────────────
    with t4:
        st.subheader("Generador de Cartas de No Aplicabilidad")
        st.caption("Genera el borrador formal para presentación a Codelco DRT según requerimientos RESSO V9.")
        with st.form("carta_na"):
            cf1,cf2=st.columns(2)
            empresa=cf1.text_input("Nombre de la Empresa",value="Smart HSE Chile")
            ncontrato=cf2.text_input("N° de Contrato",value="405")
            generar=st.form_submit_button("📄 Generar Carta N/A",type="primary",use_container_width=True)
        if generar:
            if not empresa.strip() or not ncontrato.strip():
                st.error("Completa todos los campos.")
            else:
                items=NA_ITEMS.get(ncontrato.strip(), NA_ITEMS["405"])
                hoy=fecha_es(date.today()).upper()
                decl=""
                for i,(concepto,justif) in enumerate(items,1):
                    decl+=f"{i}.\n{concepto}: {justif}\n\n"
                carta=f"""CALAMA, {hoy}

SEÑORES
CODELCO CHILE — DIVISIÓN RADOMIRO TOMIC
Presente

REF.: DECLARACIÓN DE NO APLICABILIDAD — CONTRATO N° {ncontrato.strip()}

Estimados señores:

En virtud de los requerimientos de auditoría RESSO V9 establecidos por Codelco Chile para el contrato N° {ncontrato.strip()}, {empresa.strip()} procede a declarar formalmente los siguientes ítems normativos como NO APLICABLES al alcance específico del presente contrato, con sus respectivas justificaciones:

ÍTEMS DECLARADOS NO APLICABLES:

{decl.strip()}

Lo anterior se declara en el entendido que {empresa.strip()} mantendrá actualizada la presente declaración ante cualquier modificación del alcance contractual que pudiere hacer aplicables los ítems aquí señalados.

Sin otro particular, saluda atentamente,


___________________________________
[NOMBRE RESPONSABLE]
[CARGO]
{empresa.strip()}
RUT: XX.XXX.XXX-X
Contrato N° {ncontrato.strip()}"""
                st.markdown("#### Borrador — Carta de No Aplicabilidad")
                st.text_area("",value=carta,height=520,label_visibility="collapsed")
                st.download_button(
                    label="⬇️ Descargar borrador (.txt)",
                    data=carta.encode("utf-8"),
                    file_name=f"Carta_NA_{ncontrato.strip()}_{date.today().isoformat()}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                st.markdown('<div class="nota">⚠️ <strong>Nota:</strong> Inserte logos corporativos y firma manualmente en Word antes de la presentación oficial.</div>',unsafe_allow_html=True)

    # ── TAB 6: Registro de Incidentes ──────────────────────
    with t6:
        st.subheader("🚨 Registro de Incidentes y Eventos HSE")
        st.caption("Registra accidentes, incidentes de alto potencial, casi accidentes y condiciones inseguras. Genera folio automático y descarga el registro en Excel.")

        TIPOS_EVENTO = [
            "Accidente con Tiempo Perdido (ATP)",
            "Accidente sin Tiempo Perdido (ASTP)",
            "Incidente de Alto Potencial (IAP)",
            "Casi Accidente (CA)",
            "Condición Insegura (CI)",
            "Acto Inseguro (AI)",
            "Enfermedad Profesional (EP)",
        ]
        SEVERIDADES = ["Leve", "Moderado", "Grave", "Fatal"]
        PARTES_CUERPO = [
            "Cabeza","Cuello","Hombro derecho","Hombro izquierdo",
            "Brazo derecho","Brazo izquierdo","Mano derecha","Mano izquierda",
            "Tórax / Espalda","Abdomen","Cadera","Pierna derecha","Pierna izquierda",
            "Rodilla derecha","Rodilla izquierda","Pie derecho","Pie izquierdo",
            "Ojos","Sin lesión física",
        ]

        with st.form("form_incidente", clear_on_submit=True):
            st.markdown("#### 📋 Datos del Evento")
            ri1, ri2, ri3 = st.columns(3)
            fecha_inc  = ri1.date_input("Fecha del evento", value=date.today())
            hora_inc   = ri2.time_input("Hora del evento", value=datetime.now().time())
            tipo_ev    = ri3.selectbox("Tipo de evento", TIPOS_EVENTO)

            ri4, ri5 = st.columns(2)
            contrato_inc = ri4.selectbox("Contrato", CONTRATOS)
            lugar_inc    = ri5.text_input("Lugar / Área específica", placeholder="Ej: Patio norte, Nivel -120, Sector chancado")

            desc_inc = st.text_area("Descripción del evento", height=100,
                placeholder="Describa qué ocurrió, cómo ocurrió y las condiciones del entorno al momento del evento.")

            st.markdown("#### 👷 Personas Involucradas")
            ri6, ri7 = st.columns(2)
            trabajador = ri6.text_input("Nombre trabajador(es)", placeholder="Nombre completo o 'Sin lesionados'")
            testigos   = ri7.text_input("Testigo(s)", placeholder="Nombre(s) o 'Sin testigos'")

            ri8, ri9 = st.columns(2)
            parte_cuerpo = ri8.selectbox("Parte del cuerpo afectada", PARTES_CUERPO)
            severidad    = ri9.selectbox("Severidad", SEVERIDADES)

            st.markdown("#### ⚡ Respuesta Inmediata")
            acciones_imm = st.text_area("Acciones inmediatas tomadas", height=80,
                placeholder="Ej: Se aisló el área, se prestó primeros auxilios, se trasladó al policlínico...")
            requiere_inv = st.checkbox("¿Requiere investigación formal?", value=(tipo_ev in [
                "Accidente con Tiempo Perdido (ATP)",
                "Incidente de Alto Potencial (IAP)",
                "Accidente sin Tiempo Perdido (ASTP)",
            ]))

            registrar = st.form_submit_button("🚨 Registrar Evento", type="primary", use_container_width=True)

        if registrar:
            n = len(st.session_state["incidentes"]) + 1
            folio = f"INC-{fecha_inc.strftime('%Y%m%d')}-{n:03d}"
            nuevo = {
                "Folio":           folio,
                "Fecha":           fecha_inc.isoformat(),
                "Hora":            hora_inc.strftime("%H:%M"),
                "Tipo de Evento":  tipo_ev,
                "Contrato":        contrato_inc,
                "Lugar":           lugar_inc,
                "Descripción":     desc_inc,
                "Trabajador(es)":  trabajador,
                "Testigos":        testigos,
                "Parte Cuerpo":    parte_cuerpo,
                "Severidad":       severidad,
                "Acciones Inmediatas": acciones_imm,
                "Requiere Investigación": "Sí" if requiere_inv else "No",
                "Registrado":      datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Faena":           faena,
            }
            st.session_state["incidentes"].append(nuevo)
            if severidad in ["Grave","Fatal"] or "Alto Potencial" in tipo_ev:
                st.error(f"⚠️ **EVENTO CRÍTICO registrado** — Folio: `{folio}`. Notifique de inmediato a la supervisión y al cliente.")
            else:
                st.success(f"✅ Evento registrado con folio **{folio}**.")

        # ── Historial de incidentes ──
        st.divider()
        st.markdown("#### 📂 Historial de Eventos Registrados en Sesión")
        inc_list = st.session_state["incidentes"]

        if not inc_list:
            st.info("Aún no hay eventos registrados en esta sesión.")
        else:
            df_inc = pd.DataFrame(inc_list)

            # KPIs rápidos
            ki1,ki2,ki3,ki4 = st.columns(4)
            ki1.metric("Total eventos", len(df_inc))
            ki2.metric("ATP / ASTP", int(df_inc["Tipo de Evento"].str.contains("Accidente").sum()))
            ki3.metric("Alto Potencial", int(df_inc["Tipo de Evento"].str.contains("Alto Potencial").sum()))
            ki4.metric("Requieren investigación", int((df_inc["Requiere Investigación"]=="Sí").sum()))

            st.dataframe(df_inc, use_container_width=True, hide_index=True)

            # ── Gráficos ──
            gc1, gc2 = st.columns(2)
            by_tipo = df_inc["Tipo de Evento"].value_counts().reset_index()
            by_tipo.columns = ["Tipo", "Cantidad"]
            ch_tipo = alt.Chart(by_tipo).mark_bar(cornerRadiusEnd=4, color=BRAND["cyan"]).encode(
                x=alt.X("Cantidad:Q", title=None),
                y=alt.Y("Tipo:N", sort="-x", title=None),
                tooltip=["Tipo", "Cantidad"]
            ).properties(height=240, title="Eventos por tipo")
            gc1.altair_chart(ch_tipo, use_container_width=True)

            sev_order = ["Leve", "Moderado", "Grave", "Fatal"]
            by_sev = df_inc["Severidad"].value_counts().reset_index()
            by_sev.columns = ["Severidad", "Cantidad"]
            ch_sev = alt.Chart(by_sev).mark_bar(cornerRadiusEnd=4).encode(
                x=alt.X("Severidad:N", sort=sev_order, title=None),
                y=alt.Y("Cantidad:Q", title=None),
                color=alt.Color("Severidad:N", scale=alt.Scale(
                    domain=sev_order,
                    range=[BRAND["green"], BRAND["amber"], "#EA580C", BRAND["red"]]),
                    legend=None),
                tooltip=["Severidad", "Cantidad"]
            ).properties(height=240, title="Eventos por severidad")
            gc2.altair_chart(ch_sev, use_container_width=True)

            # ── Descarga Excel ──
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df_inc.to_excel(writer, index=False, sheet_name="Registro Incidentes")
                ws = writer.sheets["Registro Incidentes"]
                # Ancho de columnas automático
                for col in ws.columns:
                    max_len = max(len(str(cell.value or "")) for cell in col)
                    ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)
            buffer.seek(0)

            st.download_button(
                label="⬇️ Descargar Registro Excel",
                data=buffer,
                file_name=f"Registro_Incidentes_{faena}_{date.today().isoformat()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )

            if st.button("🗑️ Limpiar registro de sesión", use_container_width=True):
                st.session_state["incidentes"] = []
                st.rerun()

    # ── TAB 5: Agenda ───────────────────────────────────────
    with t5:
        st.markdown("#### 📅 Agenda de Actividades Recurrentes")
        df_ag=pd.DataFrame(ACTIVIDADES)
        df_ag.columns=["Actividad","Frecuencia","Días","Módulo","Cliente"]
        st.dataframe(df_ag,use_container_width=True,hide_index=True)

        ag1,ag2=st.columns(2)
        by_mod=df_ag["Módulo"].value_counts().reset_index()
        by_mod.columns=["Módulo","Cantidad"]
        ch_mod=alt.Chart(by_mod).mark_bar(cornerRadiusEnd=4,color=BRAND["blue"]).encode(
            x=alt.X("Cantidad:Q",title=None),y=alt.Y("Módulo:N",sort="-x",title=None),
            tooltip=["Módulo","Cantidad"]).properties(height=200,title="Actividades por módulo")
        ag1.altair_chart(ch_mod,use_container_width=True)
        by_frec=df_ag["Frecuencia"].value_counts().reset_index()
        by_frec.columns=["Frecuencia","Cantidad"]
        ch_frec=alt.Chart(by_frec).mark_arc(innerRadius=48,cornerRadius=4).encode(
            theta="Cantidad:Q",
            color=alt.Color("Frecuencia:N",scale=alt.Scale(range=[BRAND["cyan"],BRAND["green"],BRAND["amber"]]),
                legend=alt.Legend(title=None,orient="bottom")),
            tooltip=["Frecuencia","Cantidad"]).properties(height=200,title="Distribución por frecuencia")
        ag2.altair_chart(ch_frec,use_container_width=True)

        st.divider(); st.subheader("🚀 Onboarding — Datos del Contrato")
        st.info(f"Estructura activa: **{st.session_state['ruta']}**")
        with st.form("onboarding"):
            oc=st.text_input("N° Contrato:",value=st.session_state["contrato"])
            oa=st.text_input("Actividad / Macro Proceso:",value=st.session_state["actividad"])
            ol=st.text_input("Lugar / Faena:",value=st.session_state["lugar"])
            if st.form_submit_button("💾 Guardar",type="primary"):
                st.session_state.update({"contrato":oc,"actividad":oa,"lugar":ol})
                st.success("✅ Guardado en sesión.")

# ════════════════════════════════════════════════════════════
# ROUTER
# ════════════════════════════════════════════════════════════
v=st.session_state["vista"]
if   v=="landing": landing()
elif v=="login":   login()
elif v=="consola":
    if st.session_state["auth"]: consola()
    else: st.session_state["vista"]="login"; st.rerun()
