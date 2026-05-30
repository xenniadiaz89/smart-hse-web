import streamlit as st
import os
import base64
import pathlib
from datetime import datetime

# ── Paleta de marca (logo Smart HSE) ─────────────────────────
BRAND = {"navy": "#0E3A5F", "blue": "#16609E", "cyan": "#27AAE1", "green": "#5BBA47"}

# ── Assets de marca ──────────────────────────────────────────
_BASE = os.path.dirname(os.path.abspath(__file__))
def _b64(rel):
    try:
        return base64.b64encode((pathlib.Path(_BASE) / rel).read_bytes()).decode()
    except Exception:
        return ""

# Usa el logo oficial si existe; si no, cae al emblema.
_LOGO_REL = "assets/logo_smarthse.png" if (pathlib.Path(_BASE) / "assets/logo_smarthse.png").exists() else "assets/logo_mark.png"
_LOGO_B64 = _b64(_LOGO_REL)
LOGO_URI = f"data:image/png;base64,{_LOGO_B64}" if _LOGO_B64 else ""
_HAS_FULL_LOGO = _LOGO_REL.endswith("logo_smarthse.png")
_FAVICON = os.path.join(_BASE, "assets", "favicon.png")

st.set_page_config(
    page_title="Smart HSE Chile — Gestión HSE para todas las áreas laborales",
    page_icon=_FAVICON if os.path.exists(_FAVICON) else "🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def logo_img(height=46):
    return f"<img src='{LOGO_URI}' style='height:{height}px;width:auto;display:inline-block'/>" if LOGO_URI else ""

# ── Estado ───────────────────────────────────────────────────
if "leads" not in st.session_state:
    st.session_state["leads"] = []

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800;900&family=Inter:wght@300;400;500;600;700&display=swap');
:root{--navy:#0E3A5F;--blue:#16609E;--cyan:#27AAE1;--green:#5BBA47;--ink:#0E3A5F;--muted:#5b7184;--line:#e2e8f0;}
#MainMenu,footer,header{visibility:hidden}
.block-container{padding:0!important;max-width:100%!important}
section[data-testid="stSidebar"]{display:none}
html,body,[class*="css"]{font-family:'Inter',sans-serif}
a{text-decoration:none}
@keyframes fadeUp{from{opacity:0;transform:translateY(26px)}to{opacity:1;transform:translateY(0)}}
.fu{animation:fadeUp .7s cubic-bezier(.2,.7,.2,1) both}
.fu2{animation:fadeUp .7s .12s cubic-bezier(.2,.7,.2,1) both}
.fu3{animation:fadeUp .7s .24s cubic-bezier(.2,.7,.2,1) both}

/* ── Nav ── */
.nav{display:flex;align-items:center;justify-content:space-between;padding:14px 46px;background:#fff;box-shadow:0 2px 18px rgba(14,58,95,.07);position:sticky;top:0;z-index:999;flex-wrap:wrap;gap:12px}
.nav-logo{display:flex;align-items:center;gap:11px}
.wm{font-family:'Montserrat',sans-serif;font-weight:900;letter-spacing:.5px;line-height:1}
.wm .smart{color:var(--blue)} .wm .hse{color:var(--cyan)}
.chip-chile{background:var(--cyan);color:#fff;font-weight:700;border-radius:4px;letter-spacing:3px;display:inline-block}
.nav-links{display:flex;gap:26px;align-items:center;flex-wrap:wrap}
.nav-links a{color:#42566a;font-size:12.5px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;transition:color .2s}
.nav-links a:hover,.nav-links a.active{color:var(--cyan)}
.btn-demo{background:var(--green);color:#fff!important;padding:11px 24px;border-radius:30px;font-size:12.5px;font-weight:800;text-transform:uppercase;letter-spacing:.8px;box-shadow:0 8px 20px rgba(91,186,71,.35);transition:transform .2s,box-shadow .2s}
.btn-demo:hover{transform:translateY(-2px);box-shadow:0 12px 26px rgba(91,186,71,.45)}

/* ── Hero ── */
.hero{position:relative;overflow:hidden;background:linear-gradient(125deg,var(--navy) 0%,var(--blue) 55%,#1f7fc0 100%);padding:104px 20px 150px;text-align:center;color:#fff}
.hero::before{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(14,58,95,.82),rgba(22,96,158,.78)),url('https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?auto=format&fit=crop&w=2000&q=80');background-size:cover;background-position:center;opacity:.5}
.hero::after{content:"";position:absolute;top:-28%;right:-10%;width:520px;height:520px;background:radial-gradient(circle,rgba(91,186,71,.35),transparent 60%);pointer-events:none}
.hero>*{position:relative;z-index:2}
.hero-logo{width:122px;height:122px;margin:0 auto 22px;border-radius:50%;background:rgba(255,255,255,.96);display:flex;align-items:center;justify-content:center;box-shadow:0 16px 44px rgba(0,0,0,.30);border:1px solid rgba(255,255,255,.5)}
.eyebrow{display:inline-block;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.28);color:#dff3ff;font-size:11px;font-weight:600;letter-spacing:2px;text-transform:uppercase;padding:7px 16px;border-radius:30px;margin-bottom:22px;backdrop-filter:blur(6px)}
.hero h1{font-family:'Montserrat',sans-serif;font-weight:900;font-size:50px;max-width:960px;margin:0 auto 22px;text-transform:uppercase;line-height:1.12;text-shadow:0 4px 18px rgba(0,0,0,.3)}
.hero h1 .hl{color:var(--green)}
.hero p{font-size:18px;max-width:730px;margin:0 auto 38px;font-weight:300;line-height:1.7;color:#eaf4fb}
.btn-hero{background:var(--green);color:#fff;padding:16px 38px;border-radius:30px;font-weight:800;font-size:14px;text-transform:uppercase;letter-spacing:1px;display:inline-block;box-shadow:0 12px 28px rgba(91,186,71,.45);transition:transform .25s,box-shadow .25s;margin:0 8px}
.btn-hero:hover{transform:translateY(-3px);box-shadow:0 18px 36px rgba(91,186,71,.55)}
.btn-ghost{background:transparent;color:#fff;padding:14px 34px;border-radius:30px;font-weight:700;font-size:14px;text-transform:uppercase;letter-spacing:1px;display:inline-block;border:2px solid rgba(255,255,255,.45);transition:background .25s;margin:0 8px}
.btn-ghost:hover{background:rgba(255,255,255,.14)}
.claims{display:flex;justify-content:center;flex-wrap:wrap;gap:13px;max-width:920px;margin:38px auto 0}
.claim{display:flex;align-items:center;gap:9px;background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.22);color:#eaf6ff;font-size:13px;font-weight:600;padding:10px 18px;border-radius:30px;backdrop-filter:blur(6px)}
.claim .dot{width:8px;height:8px;border-radius:50%;background:var(--green);box-shadow:0 0 10px var(--green)}

/* ── Secciones ── */
.sec{max-width:1140px;margin:0 auto;padding:64px 22px 12px}
.sec-tag{text-align:center;color:var(--cyan);font-weight:800;font-size:12px;letter-spacing:3px;text-transform:uppercase;margin-bottom:8px}
.sec-h{text-align:center;font-family:'Montserrat',sans-serif;font-weight:800;font-size:32px;color:var(--ink);margin:0 0 10px}
.sec-sub{text-align:center;color:var(--muted);font-size:15.5px;max-width:660px;margin:0 auto 42px;line-height:1.6}

/* ── Sectores ── */
.sectores{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.sector{background:#fff;border:1px solid var(--line);border-radius:14px;padding:24px 16px;text-align:center;transition:transform .28s,box-shadow .28s,border-color .28s}
.sector:hover{transform:translateY(-6px);box-shadow:0 18px 38px rgba(14,58,95,.12);border-color:var(--cyan)}
.sector .si{font-size:30px;display:block;margin-bottom:10px}
.sector b{display:block;font-size:13.5px;color:var(--ink);font-weight:700}

/* ── Cards servicios ── */
.cards{display:flex;justify-content:center;gap:22px;flex-wrap:wrap}
.card{background:#fff;padding:36px 24px;border-radius:18px;width:23%;min-width:230px;text-align:center;box-shadow:0 14px 40px rgba(14,58,95,.10);border:1px solid #eef3f8;border-top:4px solid transparent;transition:transform .3s,border-color .3s,box-shadow .3s}
.card:hover{transform:translateY(-8px);border-top-color:var(--cyan);box-shadow:0 26px 56px rgba(22,96,158,.20)}
.card-icon{font-size:28px;width:62px;height:62px;line-height:62px;margin:0 auto 6px;border-radius:16px;background:linear-gradient(135deg,var(--cyan),var(--blue));color:#fff;box-shadow:0 8px 20px rgba(39,170,225,.35)}
.card h3{font-family:'Montserrat',sans-serif;font-weight:800;font-size:14px;color:var(--ink);text-transform:uppercase;margin:16px 0 8px}
.card p{font-size:13px;color:var(--muted);line-height:1.6}

/* ── Cómo funciona ── */
.steps{display:flex;gap:22px;flex-wrap:wrap;justify-content:center}
.step{flex:1;min-width:240px;background:#fff;border:1px solid var(--line);border-radius:16px;padding:30px 24px;position:relative;transition:transform .3s,box-shadow .3s}
.step:hover{transform:translateY(-6px);box-shadow:0 18px 40px rgba(14,58,95,.10)}
.step .num{font-family:'Montserrat',sans-serif;font-weight:900;font-size:42px;line-height:1;background:linear-gradient(135deg,var(--cyan),var(--green));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:12px}
.step h4{font-family:'Montserrat',sans-serif;font-weight:800;font-size:16px;color:var(--ink);margin:0 0 8px}
.step p{font-size:13.5px;color:var(--muted);line-height:1.6;margin:0}

/* ── Beneficios ── */
.why{background:linear-gradient(120deg,var(--navy),var(--blue));border-radius:24px;max-width:1140px;margin:64px auto 0;padding:48px 40px;color:#fff;display:grid;grid-template-columns:repeat(3,1fr);gap:30px}
.why .b .bi{font-size:26px;margin-bottom:8px}
.why .b h4{font-family:'Montserrat',sans-serif;font-size:16px;margin:0 0 6px;font-weight:800}
.why .b p{font-size:13.5px;color:#cfe4f3;line-height:1.6;margin:0}

/* ── Footer ── */
.sh-footer{background:var(--navy);color:#9fb6c9;text-align:center;padding:54px 20px;font-size:13px;margin-top:64px}
.sh-footer a{color:var(--cyan)}
.ftr-sep{border-top:1px solid rgba(255,255,255,.10);margin-top:22px;padding-top:16px;font-size:11px;color:#6f879b}

/* ── Botones nativos Streamlit (form) → verde ── */
.stForm button[kind="primaryFormSubmit"]{background:var(--green)!important;border-color:var(--green)!important}
.stForm button[kind="primaryFormSubmit"]:hover{background:#4ea23b!important;border-color:#4ea23b!important}
.stDownloadButton>button{background:var(--cyan)!important;border-color:var(--cyan)!important}

@media(max-width:900px){.sectores{grid-template-columns:repeat(2,1fr)}.why{grid-template-columns:1fr}}
@media(max-width:768px){
  .nav{padding:12px 18px;justify-content:center}.nav-links{gap:14px;justify-content:center}
  .card{width:100%}.cards{flex-direction:column}
  .hero h1{font-size:30px}.hero{padding:80px 18px 120px}
  .btn-hero,.btn-ghost{display:block;margin:8px auto;max-width:320px}
  .steps{flex-direction:column}.sec-h{font-size:25px}
}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# NAV
# ════════════════════════════════════════════════════════════
_logo_block = logo_img(48) if _HAS_FULL_LOGO else (
    f"{logo_img(46)}<div class='wm'><span style='font-size:21px'><span class='smart'>SMART</span> <span class='hse'>HSE</span></span>"
    f"<br><span class='chip-chile' style='font-size:9px;padding:1px 8px'>CHILE</span></div>"
)
st.markdown(f"""
<div class="nav">
  <div class="nav-logo">{_logo_block}</div>
  <div class="nav-links">
    <a href="#inicio" class="active">Inicio</a>
    <a href="#soluciones">Soluciones</a>
    <a href="#tecnologia">Tecnología</a>
    <a href="#nosotros">Nosotros</a>
    <a href="#sectores">Sectores</a>
    <a href="#contacto">Contacto</a>
    <a href="#contacto" class="btn-demo">Solicitar demo</a>
  </div>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# HERO
# ════════════════════════════════════════════════════════════
st.markdown(f"""
<div id="inicio"></div>
<div class="hero">
  <div class="hero-logo fu">{logo_img(78)}</div>
  <div class="eyebrow fu">🛡️ Seguridad · Salud Ocupacional · Medio Ambiente</div>
  <h1 class="fu">Gestión HSE inteligente para <span class="hl">todas las áreas laborales</span> de Chile</h1>
  <p class="fu2">Acompañamos a empresas de cualquier sector a cumplir el DS.44, prevenir riesgos y construir cultura de seguridad — con tecnología, trazabilidad total y asesoría experta.</p>
  <div class="fu3">
    <a href="#contacto" class="btn-hero">Solicitar demo</a>
    <a href="#soluciones" class="btn-ghost">Conocer soluciones</a>
  </div>
  <div class="claims fu3">
    <div class="claim"><span class="dot"></span>Cumplimiento DS.44</div>
    <div class="claim"><span class="dot"></span>Multisector · Transversal</div>
    <div class="claim"><span class="dot"></span>Trazabilidad documental total</div>
    <div class="claim"><span class="dot"></span>Asesoría experta en terreno</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# SECTORES
# ════════════════════════════════════════════════════════════
st.markdown("""
<div id="sectores"></div>
<div class="sec">
  <div class="sec-tag">Transversal</div>
  <div class="sec-h">Una solución para todos los sectores</div>
  <div class="sec-sub">El DS.44 aplica a toda empresa con trabajadores. Sin importar tu rubro, Smart HSE adapta la gestión de seguridad y salud ocupacional a tu realidad.</div>
  <div class="sectores">
    <div class="sector"><span class="si">⛏️</span><b>Minería</b></div>
    <div class="sector"><span class="si">🏗️</span><b>Construcción</b></div>
    <div class="sector"><span class="si">🏭</span><b>Industria y Manufactura</b></div>
    <div class="sector"><span class="si">🚚</span><b>Logística y Transporte</b></div>
    <div class="sector"><span class="si">⚡</span><b>Energía</b></div>
    <div class="sector"><span class="si">🌾</span><b>Agro y Alimentos</b></div>
    <div class="sector"><span class="si">🏢</span><b>Servicios y Oficinas</b></div>
    <div class="sector"><span class="si">🛒</span><b>Retail y Comercio</b></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# SOLUCIONES / SERVICIOS
# ════════════════════════════════════════════════════════════
st.markdown("""
<div id="soluciones"></div>
<div class="sec">
  <div class="sec-tag">Soluciones</div>
  <div class="sec-h">Lo que hacemos por tu empresa</div>
  <div class="sec-sub">Un sistema completo de gestión HSE que cubre desde la identificación de riesgos hasta la cultura preventiva.</div>
  <div class="cards">
    <div class="card"><div class="card-icon">⚠️</div><h3>Gestión de Riesgos</h3><p>Identificación, evaluación y control de peligros con matrices y planes de acción según DS.44.</p></div>
    <div class="card"><div class="card-icon">📋</div><h3>Cumplimiento Normativo</h3><p>Seguimiento en tiempo real de obligaciones legales, plazos y vencimientos críticos.</p></div>
    <div class="card"><div class="card-icon">📊</div><h3>Análisis y Datos</h3><p>Indicadores de seguridad, reportes ejecutivos y trazabilidad documental completa.</p></div>
    <div class="card"><div class="card-icon">🛡️</div><h3>Cultura de Seguridad</h3><p>Capacitación, observaciones conductuales y gestión del comportamiento seguro.</p></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# CÓMO FUNCIONA / TECNOLOGÍA
# ════════════════════════════════════════════════════════════
st.markdown("""
<div id="tecnologia"></div>
<div class="sec">
  <div class="sec-tag">Cómo funciona</div>
  <div class="sec-h">Tecnología que ordena tu gestión HSE</div>
  <div class="sec-sub">Un proceso simple y acompañado, de principio a fin.</div>
  <div class="steps">
    <div class="step"><div class="num">01</div><h4>Diagnóstico</h4><p>Evaluamos tu cumplimiento DS.44 actual, detectamos brechas y priorizamos lo urgente para tu sector.</p></div>
    <div class="step"><div class="num">02</div><h4>Implementación</h4><p>Centralizamos documentos, matrices y registros en la plataforma, con clasificación y trazabilidad automática.</p></div>
    <div class="step"><div class="num">03</div><h4>Mejora continua</h4><p>Monitoreas indicadores, generas reportes y mantienes la cultura preventiva viva en el tiempo.</p></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# POR QUÉ / NOSOTROS
# ════════════════════════════════════════════════════════════
st.markdown("""
<div id="nosotros"></div>
<div class="sec" style="padding-bottom:0">
  <div class="sec-tag">Por qué Smart HSE</div>
  <div class="sec-h">Experiencia + tecnología, a tu lado</div>
</div>
<div class="why">
  <div class="b"><div class="bi">🤝</div><h4>Acompañamiento experto</h4><p>Asesores especialistas en seguridad y salud ocupacional que conocen el terreno y la normativa chilena.</p></div>
  <div class="b"><div class="bi">⚙️</div><h4>Tecnología a tu favor</h4><p>Plataforma que automatiza la documentación, reduce planillas y te da control en tiempo real.</p></div>
  <div class="b"><div class="bi">🔒</div><h4>Trazabilidad total</h4><p>Cada registro queda respaldado y disponible, listo para auditorías y fiscalizaciones.</p></div>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# CONTACTO
# ════════════════════════════════════════════════════════════
st.markdown("""
<div id="contacto"></div>
<div class="sec">
  <div class="sec-tag">Hablemos</div>
  <div class="sec-h">Solicita una demostración</div>
  <div class="sec-sub">Cuéntanos de tu empresa y te mostramos cómo Smart HSE simplifica el cumplimiento DS.44 y la prevención en tu sector.</div>
</div>
""", unsafe_allow_html=True)

SECTORES = ["Minería", "Construcción", "Industria y Manufactura", "Logística y Transporte",
            "Energía", "Agro y Alimentos", "Servicios y Oficinas", "Retail y Comercio", "Otro"]

_, fc, _ = st.columns([1, 2, 1])
with fc:
    with st.form("lead"):
        a, b = st.columns(2)
        nombre = a.text_input("Nombre", placeholder="Tu nombre")
        empresa = b.text_input("Empresa", placeholder="Nombre de tu empresa")
        c, d = st.columns(2)
        correo = c.text_input("Correo electrónico", placeholder="correo@empresa.cl")
        sector = d.selectbox("Sector", SECTORES)
        msg = st.text_area("¿Qué necesitas resolver?",
                           placeholder="Ej: ordenar el cumplimiento DS.44 de mi empresa y reducir el papeleo.",
                           height=90)
        enviar = st.form_submit_button("Solicitar demo →", type="primary", use_container_width=True)
    if enviar:
        if not nombre.strip() or not correo.strip():
            st.error("Por favor completa al menos tu nombre y correo.")
        else:
            st.session_state["leads"].append({
                "nombre": nombre, "empresa": empresa, "correo": correo,
                "sector": sector, "mensaje": msg,
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")})
            asunto = f"Solicitud de demo — {empresa or nombre}".replace(" ", "%20")
            cuerpo = (f"Nombre: {nombre}%0D%0AEmpresa: {empresa}%0D%0ASector: {sector}"
                      f"%0D%0ACorreo: {correo}%0D%0A%0D%0AMensaje:%0D%0A{msg}").replace(" ", "%20")
            mailto = f"mailto:contacto@smarthse.cl?subject={asunto}&body={cuerpo}"
            st.success(f"✅ ¡Gracias, {nombre.split()[0]}! Recibimos tu solicitud. Te contactaremos a la brevedad.")
            st.markdown(f"<a href='{mailto}' class='btn-hero' style='margin-top:6px'>📧 Enviar también por correo</a>",
                        unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="sh-footer">
  <div style="margin-bottom:12px">{logo_img(54)}</div>
  <div class="wm" style="font-size:20px;color:#fff;letter-spacing:1px;margin-bottom:8px">SMART <span style="color:var(--cyan)">HSE</span> CHILE</div>
  <p>Gestión HSE para todas las áreas laborales de Chile · Cumplimiento DS.44</p>
  <p style="margin-top:12px"><a href="mailto:contacto@smarthse.cl">contacto@smarthse.cl</a> &nbsp;·&nbsp; <a href="https://smarthse.cl">smarthse.cl</a></p>
  <div class="ftr-sep">© 2025 Smart HSE Chile · Todos los derechos reservados.</div>
</div>
""", unsafe_allow_html=True)
