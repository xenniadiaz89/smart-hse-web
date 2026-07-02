---
name: preparar-testing-render
description: Consolida la web Smart HSE (Flask) y la deja lista para una ronda de testing abierto en Render. Úsala cuando se pida dejar la app "100% operativa en la nube", preparar pruebas con usuarios/evaluadores, consolidar rutas (landing, /login, /registro, dashboard de contratos asesorados), persistencia de cuentas, banner de modo testing, o verificar el deploy (requirements/render.yaml/start.sh) antes del commit a GitHub.
---

# Preparar Testing en Render — Smart HSE

Actúa como **desarrollador senior experto en Python, Flask y despliegue en Render**. El objetivo es consolidar la aplicación web de Smart HSE para que quede **100% operativa en la nube y lista para una ronda de pruebas (testing) con usuarios/evaluadores**.

Proyecto base: `Skill Smart HSE/skillwebsmarthse.cloude/` (repo `github.com/xenniadiaz89/smart-hse-web`, desplegado en Render). No regenerar el logo (`static/logo_smarthse.png`).

## 1. Consolidación de interfaces y rutas

- `app.py` debe servir correctamente la **Landing Page** con su marquee de leyes, cuadrícula de valor y el logo en `static/logo_smarthse.png` (sin regenerarlo).
- El flujo de **registro e inicio de sesión** (`/login`, `/registro`) debe procesar las validaciones de **RUT** y alfanuméricas, derivando limpiamente al **Dashboard**.
- El dashboard debe reflejar la interfaz **"Mis Contratos Asesorados"** con los campos: **Empresa Contratista, Faena** (ej. Radomiro Tomic), **Mandante, Gerencia, Superintendencia** y datos de **Administrador de Contrato**.

## 2. Preparación para testing abierto

- Persistencia simple o simulación robusta de sesiones usando **`usuarios.json` cifrado**, para que múltiples evaluadores creen cuentas, ingresen, testeen contratos y prueben la **Matriz de Cumplimiento DS 44** (pilares a–e, lógica Sí/No/N/A) sin que la plataforma se caiga.
- Banner visible **"Modo Testing — Demo Activa"** y **contadores de prueba** (ej. 5 días restantes) para dar contexto a quienes retroalimentan la plataforma.

## 3. Preparación de entorno (deploy)

- `requirements.txt` debe mantener exactamente: `Flask==3.0.2`, `Werkzeug==3.0.1`, `gunicorn==21.2.0`.
- `render.yaml` y `start.sh` deben invocar: `gunicorn app:app --bind 0.0.0.0:$PORT`.
- Entregar las instrucciones exactas para verificar la compilación localmente con `python app.py` en `http://localhost:5000/` antes del commit a GitHub.
  - Nota de entorno local (macOS): el puerto **5000 lo ocupa AirPlay Receiver**; para revisar usar otro puerto (ej. `gunicorn app:app --bind 127.0.0.1:5050`). En Render no afecta (usa `$PORT`).

## 4. Lanzamiento a evaluadores (pasos operativos)

1. **Subir a GitHub:** commit + push de la carpeta de trabajo al repo `smart-hse-web`, rama `main`.
2. **Revisar Render:** confirmar que el despliegue del último commit quede en verde (**Deployed**).
3. **Compartir el enlace:** entregar la URL pública `*.onrender.com` a evaluadores / early adopters.
4. **Recoger feedback:** dejar que interactúen con el simulador anti-fraude, la carga de evidencias (Drag & Drop) y la generación de cartas de no aplicabilidad, para medir la reducción de horas administrativas y validar la propuesta de valor.

## Verificación
- Levantar local y comprobar rutas (`/`, `/login`, `/registro`, dashboard) en 200.
- Validar el JS de las plantillas (parser) y el flujo de cuentas con `usuarios.json`.
- Confirmar `requirements.txt` / `render.yaml` / `start.sh` exactos antes del push.
