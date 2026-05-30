# Smart HSE Chile — Sitio Web

Sitio de marketing de **Smart HSE Chile**: gestión **HSE (Salud, Seguridad y Medio Ambiente)** para **todas las áreas laborales** de Chile. Acompañamos a empresas de cualquier sector a cumplir el **DS.44**, prevenir riesgos y construir cultura de seguridad.

## ✨ Secciones

- **Hero** transversal con propuesta de valor y CTA "Solicitar demo".
- **Sectores** que atendemos (minería, construcción, industria, logística, energía, agro, servicios, retail).
- **Soluciones** — gestión de riesgos, cumplimiento normativo, análisis de datos y cultura de seguridad.
- **Cómo funciona** — diagnóstico, implementación y mejora continua.
- **Por qué Smart HSE** — acompañamiento experto, tecnología y trazabilidad.
- **Contacto** — formulario de captura de leads (con fallback a correo).

Identidad visual alineada al logo de marca: cyan `#27AAE1`, azul `#16609E`, navy `#0E3A5F`, verde `#5BBA47`.

## 🛠️ Stack

- **Streamlit** (Python 3.11) — sitio de una sola página.
- Despliegue en **Render** (auto-deploy desde `main`).

## ▶️ Correr localmente

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Abre http://localhost:8501

## 🚀 Despliegue (Render)

El archivo [`render.yaml`](render.yaml) define el servicio. Cada push a `main` dispara un nuevo deploy automático.

## 🖼️ Assets

El logo vive en [`assets/`](assets/). Si reemplazas `assets/logo_smarthse.png` por el logo oficial (PNG con fondo transparente), la app lo usa automáticamente en nav, hero y footer.

---

© 2025 Smart HSE Chile · Todos los derechos reservados.
