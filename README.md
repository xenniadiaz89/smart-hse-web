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

- **Flask 3** + **gunicorn** (Python 3.11.9, fijado en `.python-version`).
- Plantillas Jinja2 + Tailwind (CDN) + iconos Lucide. Sin build step.
- **PostgreSQL** (Neon) en producción vía `DATABASE_URL`; **SQLite** local automático si esa variable no existe.
- Despliegue en **Render** (auto-deploy desde `main`).

> `streamlit_app.py` quedó **obsoleto** tras la migración a Flask (jun-2026). Se conserva solo como referencia.

## 🧱 Arquitectura — módulos aislados

El núcleo (`app.py`) registra cada submódulo como Blueprint dentro de un `try/except` y anota el resultado en `MODULOS_OK`. **Un módulo que falle al importar queda encapsulado**: su ítem del sidebar sale deshabilitado, la traza va a los Logs y el resto de la app sigue en pie.

```
app.py            núcleo + registro de módulos
core_auth.py      decoradores (login/empresa/onboarding) + helpers de RUT
onboarding/       Panel de Bienvenida  → /onboarding
matriz_legal/     Matriz Legal D.S. 44 → /matriz-legal
db.py models.py   capa de datos compartida
```

Reglas al crear un módulo nuevo: va en su carpeta con `__init__.py`, `routes.py`, `service.py` y `templates/<modulo>/`; **nunca** importa `app.py` (import circular) ni a otro módulo. Se engancha con una línea: `_registrar('x', 'x')`.

## ▶️ Correr localmente

```bash
python3 -m venv venv && venv/bin/pip install -r requirements.txt   # solo la 1ª vez
./dev.sh              # http://localhost:5001 con recarga automática
./dev.sh --reset      # además, recrea la BD local limpia
```

Entrada directa sin clave: **http://localhost:5001/prueba**

- Usa **SQLite** (`smarthse.db`, ignorado por git). `dev.sh` hace `unset DATABASE_URL`, así que **trabajar en local nunca toca la base de producción**.
- Puerto **5001** y no 5000: en macOS el 5000 lo ocupa AirPlay Receiver (responde `403`).

## 🚀 Despliegue (Render)

El archivo [`render.yaml`](render.yaml) define el servicio: `gunicorn app:app`. **Cada push a `main` dispara un deploy automático** — trabaja y commitea local; pushea solo cuando quieras publicar.

Antes de pushear, validar la sintaxis contra el Python 3.11 de Render (el local es más nuevo y no detecta incompatibilidades hacia atrás):

```bash
venv/bin/python -c "
import ast, pathlib
for f in list(pathlib.Path('.').glob('*.py')) + list(pathlib.Path('.').glob('*/*.py')):
    if f.name.startswith('._') or 'venv' in f.parts: continue
    try: ast.parse(f.read_text(encoding='utf-8'), filename=str(f), feature_version=(3, 11))
    except SyntaxError as e: print('✘', f, e.lineno, e.msg)
print('listo')"
```

## 🖼️ Assets

El logo vive en [`assets/`](assets/). Si reemplazas `assets/logo_smarthse.png` por el logo oficial (PNG con fondo transparente), la app lo usa automáticamente en nav, hero y footer.

---

© 2025 Smart HSE Chile · Todos los derechos reservados.
