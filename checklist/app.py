import streamlit as st
from streamlit_drawable_canvas import st_canvas
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Registro de Entrega de EPP | Omega Servicios",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Registro Digital de Entrega de EPP")
st.caption("Documento: OMSERV-ADM-FORM-01 (Rev. 1.3) | Omega Servicios SpA")

# --- 1. IDENTIFICACIÓN Y TRAZABILIDAD ---
st.header("1. Identificación del Trabajador y Contexto")

col1, col2 = st.columns(2)
with col1:
    nombre = st.text_input("Nombre Completo del Trabajador", value="Xennia Díaz Díaz")
    rut = st.text_input("R.U.N.", value="17.433.846-9")
    cargo = st.text_input("Cargo", value="HSE")

with col2:
    area_trabajo = st.text_input("Área o Lugar de Trabajo", placeholder="Ej: Mantenimiento, Planta, Faena Central")
    turno = st.selectbox("Turno", ["Día", "Noche", "7x7", "4x3", "5x2", "Otro"])
    fecha = st.date_input("Fecha de Entrega", datetime.now())

st.divider()

# --- 2. FORMULARIO INTERACTIVO DE EPP ---
st.header("2. Detalle de Elementos de Protección Personal")

# Definición de ítems agrupados según el formato original
grupos_epp = {
    "Protección Personal (EPP)": [
        "Casco c/ barbiquejo Blanco",
        "Protector Auditivo Adosable al Casco",
        "Coipa (cubrenuca)",
        "Chaleco Geólogo",
        "Zapato de Seguridad",
        "Respirador Media Cara",
        "Filtro (Mixto ó Polvo)",
        "Lentes In-Out",
        "Guantes Instrumentista",
        "Bloqueador Solar",
        "Protector Labial",
        "Slack Anti-Ácido"
    ],
    "Ropa Corporativa": [
        "Camisa / Blusa / Polera",
        "Jeans / Pantalón",
        "Chaqueta 2 en 1",
        "Nombre geólogo"
    ],
    "Dispositivos de Bloqueo": [
        "Pinzas para candados",
        "Candados (indicar color)",
        "Tarjetas de Bloqueo"
    ],
    "Ropa Invierno / Turno Noche": [
        "Guantes Térmicos",
        "Chaqueta Térmica",
        "Pantalón Térmico",
        "Balaclava Zero",
        "Primera Capa Térmica",
        "Calcetines Térmicos"
    ],
    "Otros Elementos": [
        "Arnés de Seguridad",
        "Cuerda de Vida",
        "Botas de Goma (negra)",
        "Botas de ácido (amarilla)",
        "Full Face",
        "Botas PVC"
    ]
}

registros = []

for categoria, items in grupos_epp.items():
    with st.expander(f"📦 {categoria}", expanded=True):
        st.write("")
        for item in items:
            c1, c2, c3, c4 = st.columns([3, 1.5, 1.5, 3])
            
            with c1:
                st.markdown(f"**{item}**")
            
            with c2:
                entrega = st.radio(
                    f"¿Entrega?",
                    options=["No", "Sí"],
                    horizontal=True,
                    key=f"radio_{item}"
                )
            
            with c3:
                if entrega == "Sí":
                    cantidad = st.number_input(
                        "Cantidad",
                        min_value=1,
                        max_value=50,
                        value=1,
                        step=1,
                        key=f"cant_{item}"
                    )
                else:
                    cantidad = 0
                    st.write("-")
            
            with c4:
                obs = st.text_input(
                    "Obs. / Código / Color",
                    placeholder="Opcional",
                    key=f"obs_{item}"
                )
            
            registros.append({
                "Categoría": categoria,
                "Ítem": item,
                "Entregado": entrega,
                "Cantidad": cantidad,
                "Observaciones": obs
            })

st.divider()

# --- 3. DECLARACIÓN LEGAL Y COMPROMISO ---
st.header("3. Declaración de Recepción y Uso")
st.info(
    "**Declaración:**\n\n"
    "Omega Servicios por medio del presente documento, registra la entrega de elementos de protección personal "
    "debidamente certificados y entregados de manera gratuita al trabajador.\n\n"
    "Según las disposiciones legales vigentes, el trabajador está obligado a dar el uso debido a los "
    "elementos de protección personal (artículo 58° y siguientes del RIOHS de Omega Servicios y Art. 68 Ley 16.744)."
)

# --- 4. FIRMA EN LIENZO DIGITAL ---
st.header("4. Firma del Trabajador")
st.caption("Firme dentro del recuadro usando mouse o pantalla táctil:")

canvas_firma = st_canvas(
    stroke_width=2,
    stroke_color="#000000",
    background_color="#FFFFFF",
    height=150,
    width=500,
    drawing_mode="freedraw",
    key="canvas_firma"
)

col_btn1, col_btn2 = st.columns([1, 4])

# --- 5. GUARDADO Y EXPORTACIÓN ---
if st.button("💾 Guardar y Finalizar Registro", type="primary"):
    # Validación básica
    if not nombre or not rut or not area_trabajo or not cargo:
        st.error("⚠️ Debe completar todos los datos de identificación (Nombre, RUT, Cargo y Área de trabajo).")
    elif canvas_firma.image_data is None:
        st.warning("⚠️ Debe firmar en el recuadro antes de finalizar.")
    else:
        df_registro = pd.DataFrame(registros)
        df_entregados = df_registro[df_registro["Entregado"] == "Sí"]
        
        st.success(f"✅ Registro completado exitosamente para {nombre} ({cargo}). Total de ítems entregados: {len(df_entregados)}.")
        
        # Resumen de entrega
        st.subheader("Resumen de EPP Entregados")
        st.dataframe(df_entregados[["Categoría", "Ítem", "Cantidad", "Observaciones"]], use_container_width=True)
        
        # Descarga de evidencia en CSV para archivo/auditoría
        csv = df_registro.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Acta de Entrega (CSV / Auditoría)",
            data=csv,
            file_name=f"Entrega_EPP_{rut}_{fecha.strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )