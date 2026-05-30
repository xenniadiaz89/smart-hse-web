# Smart HSE Chile — Plataforma Web

Plataforma de gestión **HSE (Health, Safety & Environment)** para la minería y contratistas en Chile. Centraliza el cumplimiento **DS.44**, el estándar **RESSO V9 de Codelco** y la trazabilidad documental en una sola aplicación.

## ✨ Qué incluye

**Sitio público (landing)**
- Hero con propuesta de valor y captura de leads (formulario "Solicitar demo").
- Sección "Cómo funciona" y tarjetas de servicios.
- Identidad visual alineada al logo de marca (cyan `#27AAE1`, azul `#16609E`, verde `#5BBA47`).

**Consola operativa** (acceso con contraseña)
- ⚡ **Acción Inmediata** — KPIs dinámicos y foco del día por faena/cliente.
- 📥 **Motor Documental** — carga, clasificación y renombrado estándar de documentos.
- 📊 **GAP Analysis** — detección de brechas con gráfico de cumplimiento (donut).
- 📄 **Cartas N/A** — generador de cartas de No Aplicabilidad para Codelco DRT.
- 📅 **Agenda** — actividades recurrentes con visualizaciones.
- 🚨 **Incidentes** — registro con folio automático, gráficos y descarga Excel.

## 🛠️ Stack

- **Streamlit** (Python 3.11) · **pandas** · **openpyxl** · **Altair** (gráficos, incluido con Streamlit).
- Despliegue en **Render** (auto-deploy desde `main`).

## ▶️ Correr localmente

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Abre http://localhost:8501

## 🔐 Acceso a la consola

La contraseña se configura con la variable de entorno `APP_PASSWORD` (por defecto `smarthse2025`).

```bash
export APP_PASSWORD="tu_contraseña_segura"
```

## 🚀 Despliegue (Render)

El archivo [`render.yaml`](render.yaml) define el servicio. Cada push a `main` dispara un nuevo deploy automático.

---

© 2025 Smart HSE Chile · Todos los derechos reservados.
