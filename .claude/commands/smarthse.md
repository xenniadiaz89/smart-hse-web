# Smart HSE Chile — Contexto de Proyecto

Eres el asistente de desarrollo de **Smart HSE Chile**, una plataforma de gestión HSE para minería en Chile. Tienes todo el contexto del proyecto cargado.

## Stack técnico
- **Framework:** Streamlit 1.35.0
- **Python:** 3.11.9 (fijado en `.python-version`)
- **Deploy:** Render.com (plan free) → https://smart-hse.onrender.com
- **Dominio:** smarthse.cl (DNS via Cloudflare, CNAME DNS-only)
- **Repo:** github.com/xenniadiaz89/smart-hse-web
- **Archivo principal:** `streamlit_app.py`
- **Dependencias:** `requirements.txt` → streamlit, pandas, openpyxl

## Arquitectura de la app
App de página única con router por `st.session_state["vista"]`:
- `"landing"` → Página pública de marketing
- `"login"` → Formulario de contraseña
- `"consola"` → App operativa (requiere auth)

**Contraseña:** `smarthse2025` (o variable de entorno `APP_PASSWORD` en Render)

## Módulos actuales (5 tabs en consola)
1. **⚡ Acción Inmediata** — KPIs + Top 3 tareas urgentes + requisitos del cliente
2. **📥 Motor Documental** — Upload → renombrar con nomenclatura `FECHA_FLUJO_CONTRATO.ext` → download
3. **📊 GAP Analysis** — Upload Excel/CSV → detecta columnas ESTADO/BRECHA → métricas de cumplimiento
4. **📄 Cartas N/A** — Genera carta formal RESSO V9 para Codelco DRT → descarga .txt
5. **📅 Agenda** — Tabla actividades recurrentes + onboarding datos de contrato

## Datos maestros clave
- **Contratos activos:** 405, 118, 109100077748
- **Flujos documentales:** FYS Diario, RESSO
- **Clientes:** Minera Spence, Codelco DRT, Minera El Abra, Centinela
- **NA_ITEMS:** Ítems N/A con justificación RESSO V9 para contratos 405 y 118

## Reglas de negocio / normativa chilena
- **DS.44:** Decreto Supremo 44, Reglamento de Seguridad Minera SERNAGEOMIN
- **RESSO V9:** Reglamento Especial para Empresas Contratistas y Subcontratistas de Codelco
- **FYS:** Fiscalización y Seguimiento — reporte diario de actividades
- **ECF21:** Estándar de Control de Fatalidades N°21 (observación conductual)
- **LOD:** Lista de Obreros y Dotación — registro semanal
- **CPHS:** Comité Paritario de Higiene y Seguridad (obligatorio +25 trabajadores, Ley 16.744)
- **PREXOR:** Programa de Vigilancia del Ambiente Laboral y de la Salud de los Trabajadores expuestos a Ruido
- **Art. 66 Ley 16.744:** Obligación de CPHS sobre 25 trabajadores

## Estilo visual
- **Colores:** Azul oscuro `#002B49`, verde agua `#55B4B0`, verde lima `#8DC63F`
- **Tipografía:** Montserrat (títulos, bold/black) + Inter (texto, light/regular)
- **Alertas:** roja `.ar`, ámbar `.aa`, verde `.ag`
- **KPI cards:** `.kpi` con gradiente azul oscuro

## Rutas locales (solo desarrollo)
```
/Volumes/Elements/SMART HSE/Motor_Smart_HSE/
├── 01_Motor_App/app_smarthse.py     ← versión local con rutas hardcoded
├── 02_Bases_Datos/                  ← matrices GAP y FYS
├── 03_Entrada_Documentos/
├── 04_Salida_RESSO/
├── 05_Salida_FYS/
└── smart-hse-web/                   ← VERSIÓN PRODUCCIÓN (Render)
    ├── streamlit_app.py             ← archivo principal
    ├── requirements.txt
    ├── .python-version              ← 3.11.9
    ├── start.sh
    ├── render.yaml
    └── .streamlit/config.toml
```

## Errores conocidos / soluciones
- **Render usa Python 3.14 por defecto** → siempre mantener `.python-version` con `3.11.9`
- **No usar rutas locales** → todo upload/download via `st.file_uploader` + `st.download_button`
- **`st.secrets` puede fallar** → siempre usar `try: st.secrets["X"] except: X = "default"`
- **Cloudflare debe estar en DNS-only** (gris) → no Proxied para que Render verifique SSL

## Próximos módulos planificados
- 🚨 Registro de Incidentes (folio automático + descarga Excel)
- 👷 Gestión de Trabajadores (dotación, acreditaciones, vencimientos)
- ⏰ Semáforo de vencimientos documentales
- 📸 ECF21 Digital (formulario observación conductual)
- 🤖 IA generativa (Claude API) para cartas N/A y asesor normativo DS.44

## Tu tarea
Cuando se invoca este skill, el usuario quiere trabajar en Smart HSE Chile.
- Pregunta qué módulo o mejora quiere trabajar hoy
- Sugiere siempre el enfoque más simple que funcione en Render free tier
- El código va en `streamlit_app.py` y debe ser compatible con la arquitectura actual
- Al terminar, recuerda hacer `git add . && git commit -m "..." && git push` para que Render redesplegue

$ARGUMENTS
