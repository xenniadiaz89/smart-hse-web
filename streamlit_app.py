import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta, date

st.set_page_config(
    page_title="Smart HSE Chile",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Estado ──────────────────────────────────────────────────
def init():
    for k,v in {"vista":"landing","auth":False,"contrato":"","actividad":"","lugar":"","ruta":"","incidentes":[]}.items():
        if k not in st.session_state: st.session_state[k]=v
init()

try:    APP_PW = st.secrets["APP_PASSWORD"]
except: APP_PW = "smarthse2025"

# ── CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;900&family=Inter:wght@300;400;600&display=swap');
#MainMenu,footer,header{visibility:hidden}
.block-container{padding:0!important;max-width:100%!important}
section[data-testid="stSidebar"]{display:none}
html,body,[class*="css"]{font-family:'Inter',sans-serif}
/* Landing */
.hero{background:#002B49;background-image:linear-gradient(rgba(0,43,73,.78),rgba(0,43,73,.78)),url('https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=2000&q=80');background-size:cover;background-position:center;padding:130px 20px;text-align:center;color:white;min-height:68vh;display:flex;flex-direction:column;justify-content:center;align-items:center}
.hero h1{font-family:'Montserrat',sans-serif;font-weight:900;font-size:48px;max-width:900px;margin:0 auto 20px;text-transform:uppercase;line-height:1.15;text-shadow:2px 2px 6px rgba(0,0,0,.4)}
.hero p{font-size:18px;max-width:720px;margin:0 auto 44px;font-weight:300;line-height:1.7}
.btn-hero{background:#55B4B0;color:white;padding:16px 36px;border-radius:30px;font-weight:700;font-size:14px;text-decoration:none;text-transform:uppercase;letter-spacing:1px;display:inline-block}
.cards{display:flex;justify-content:center;gap:24px;max-width:1200px;margin:-60px auto 60px;position:relative;z-index:10;padding:0 20px;flex-wrap:wrap}
.card{background:white;padding:40px 22px;border-radius:16px;width:22%;min-width:200px;text-align:center;box-shadow:0 12px 36px rgba(0,0,0,.09);border-bottom:4px solid transparent;transition:transform .3s,border-color .3s}
.card:hover{transform:translateY(-6px);border-bottom-color:#55B4B0}
.card-icon{font-size:40px;margin-bottom:8px}
.card h3{font-family:'Montserrat',sans-serif;font-weight:800;font-size:14px;color:#002B49;text-transform:uppercase;margin:14px 0 8px}
.card p{font-size:13px;color:#64748b;line-height:1.6}
.sh-footer{background:#002B49;color:#94A3B8;text-align:center;padding:48px 20px;font-size:13px;margin-top:40px}
.sh-footer a{color:#55B4B0;text-decoration:none}
.ftr-sep{border-top:1px solid #1a3a52;margin-top:20px;padding-top:16px;font-size:11px;color:#64748b}
/* Consola */
.kpi{background:linear-gradient(135deg,#002B49 0%,#1e3a5f 100%);border-radius:12px;padding:1.2rem 1.5rem;color:white;text-align:center;box-shadow:0 4px 14px rgba(0,43,73,.15);margin-bottom:8px}
.kpi .val{font-size:2.4rem;font-weight:300}
.kpi .lbl{font-size:.8rem;opacity:.8;margin-top:4px}
.ar{background:#fef2f2;border-left:4px solid #ef4444;padding:.8rem 1rem;border-radius:6px;margin:.4rem 0}
.ag{background:#f0fdf4;border-left:4px solid #8DC63F;padding:.8rem 1rem;border-radius:6px;margin:.4rem 0}
.aa{background:#fffbeb;border-left:4px solid #f59e0b;padding:.8rem 1rem;border-radius:6px;margin:.4rem 0}
.nota{background:#fff8e1;border-left:4px solid #FFA000;padding:12px 16px;border-radius:6px;font-size:.85rem}
@media(max-width:768px){.cards{flex-direction:column;margin:-30px 16px 30px}.card{width:100%}.hero h1{font-size:28px}}
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
    c1,c2,c3 = st.columns([2,4,2])
    with c1:
        st.markdown("<div style='padding:10px 0 0 8px'><span style='font-family:Montserrat,sans-serif;font-weight:900;font-size:22px;color:#002B49'>SMART HSE</span><br><span style='background:#55B4B0;color:white;font-size:9px;font-weight:700;padding:1px 7px;border-radius:3px;letter-spacing:2px'>CHILE</span></div>",unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='padding-top:14px;text-align:center'><span style='color:#4A5568;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin:0 14px'>Soluciones</span><span style='color:#4A5568;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin:0 14px'>Tecnología</span><span style='color:#4A5568;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin:0 14px'>Nosotros</span></div>",unsafe_allow_html=True)
    with c3:
        if st.button("🔒 Acceder a Consola",use_container_width=True,type="primary"):
            st.session_state["vista"]="login"; st.rerun()
    st.markdown("<hr style='margin:0;border:none;border-top:1px solid #e2e8f0'>",unsafe_allow_html=True)
    st.markdown("""
    <div class="hero">
        <h1>Revolucionando la gestión HSE transversal en Chile</h1>
        <p>Potenciamos la seguridad, el cumplimiento normativo DS.44 y el crecimiento sostenible en minería y contratistas de todo el territorio.</p>
        <a href="mailto:contacto@smarthse.cl" class="btn-hero">Descubra cómo simplificar el DS.44</a>
    </div>
    <div class="cards">
        <div class="card"><div class="card-icon">⚠️</div><h3>Gestión de Riesgos</h3><p>Identificación, evaluación y control de peligros según DS.44 y normativa SERNAGEOMIN.</p></div>
        <div class="card"><div class="card-icon">📋</div><h3>Cumplimiento Normativo</h3><p>Seguimiento en tiempo real de obligaciones legales mineras y vencimientos críticos.</p></div>
        <div class="card"><div class="card-icon">📊</div><h3>Análisis y Datos</h3><p>Dashboards con KPIs de seguridad operacional y reportes ejecutivos automatizados.</p></div>
        <div class="card"><div class="card-icon">🛡️</div><h3>Cultura de Seguridad</h3><p>Programas de capacitación y gestión del comportamiento seguro en terreno.</p></div>
    </div>
    <div class="sh-footer">
        <div style='font-family:Montserrat,sans-serif;font-weight:700;font-size:18px;color:white;letter-spacing:2px;margin-bottom:8px'>SMART HSE CHILE</div>
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
        st.markdown("<div style='text-align:center;margin-bottom:28px'><div style='font-family:Montserrat,sans-serif;font-weight:900;font-size:2.6rem;color:#002B49'>SMART HSE</div><div style='display:inline-block;background:#55B4B0;color:white;font-size:10px;font-weight:700;padding:2px 10px;border-radius:4px;letter-spacing:2px;margin-top:4px'>CHILE</div><p style='color:#64748b;margin-top:14px;font-weight:300;font-size:14px'>Consola de Gestión Operativa · DS.44</p></div>",unsafe_allow_html=True)
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
        st.markdown("<div style='text-align:center;padding:14px 0 6px'><div style='font-family:Montserrat,sans-serif;font-weight:900;font-size:20px;color:#002B49'>SMART HSE</div><div style='display:inline-block;background:#55B4B0;color:white;font-size:9px;font-weight:700;padding:1px 8px;border-radius:3px;letter-spacing:2px'>CHILE</div></div>",unsafe_allow_html=True)
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
        c1,c2,c3=st.columns(3)
        c1.markdown("<div class='kpi'><div class='val'>12</div><div class='lbl'>Documentos RESSO</div></div>",unsafe_allow_html=True)
        c2.markdown("<div class='kpi'><div class='val'>45</div><div class='lbl'>Registros FYS</div></div>",unsafe_allow_html=True)
        c3.markdown("<div class='kpi'><div class='val'>8</div><div class='lbl'>Ítems N/A detectados</div></div>",unsafe_allow_html=True)
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
