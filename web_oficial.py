import streamlit as st

st.set_page_config(page_title="Smart HSE Chile", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding: 0rem; max-width: 100%;}

        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;800;900&family=Inter:wght@400;600&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }

        /* HEADER */
        .header {
            background-color: #ffffff; padding: 15px 50px; display: flex;
            justify-content: space-between; align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05); position: sticky; top: 0; z-index: 100;
        }
        .logo-container { display: flex; align-items: center; gap: 10px; }
        .logo-text { font-family: 'Montserrat', sans-serif; font-weight: 900; font-size: 28px; color: #002B49; line-height: 0.9; }
        .logo-sub { background-color: #55B4B0; color: white; font-size: 11px; padding: 2px 8px; border-radius: 4px; letter-spacing: 2px; }

        .nav-links { display: flex; gap: 25px; font-weight: 700; font-size: 13px; color: #4A5568; text-transform: uppercase; }
        .nav-links a { text-decoration: none; color: inherit; transition: color 0.2s; }
        .nav-links a:hover { color: #55B4B0; }

        .btn-demo {
            background-color: #55B4B0; color: white; padding: 12px 24px; border-radius: 30px;
            font-weight: 700; font-size: 13px; text-decoration: none; text-transform: uppercase;
        }

        /* HERO */
        .hero {
            background-color: #002B49;
            background-image:
                linear-gradient(rgba(0, 43, 73, 0.75), rgba(0, 43, 73, 0.75)),
                url('https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80');
            background-size: cover; background-position: center;
            padding: 120px 20px; text-align: center; color: white; min-height: 70vh;
            display: flex; flex-direction: column; justify-content: center; align-items: center;
        }
        .hero h1 {
            font-family: 'Montserrat', sans-serif; font-weight: 900; font-size: 48px; max-width: 900px; margin: 0 auto 20px;
            text-transform: uppercase; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); line-height: 1.2;
        }
        .hero p { font-size: 18px; max-width: 800px; margin: 0 auto 40px; font-weight: 400; text-shadow: 1px 1px 3px rgba(0,0,0,0.5); }
        .btn-hero {
            background-color: #55B4B0; color: white; padding: 16px 32px; border-radius: 30px;
            font-weight: 700; font-size: 15px; text-decoration: none; text-transform: uppercase; border: none; cursor: pointer;
        }

        /* TARJETAS */
        .features-container {
            display: flex; justify-content: center; gap: 20px; max-width: 1200px; margin: -50px auto 50px; position: relative; z-index: 10; padding: 0 20px;
        }
        .feature-card {
            background: white; padding: 40px 20px; border-radius: 15px; width: 25%; text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1); border-bottom: 5px solid white; transition: border-color 0.3s, transform 0.3s;
        }
        .feature-card:hover { transform: translateY(-5px); border-bottom-color: #55B4B0; }
        .card-icon { font-size: 36px; margin-bottom: 10px; }
        .feature-card h3 { font-family: 'Montserrat', sans-serif; font-weight: 800; font-size: 16px; color: #002B49; text-transform: uppercase; margin-top: 15px; }
        .feature-card p { font-size: 13px; color: #4A5568; margin-top: 10px; line-height: 1.5; }

        /* RESPONSIVE MOBILE */
        @media (max-width: 768px) {
            .features-container { flex-direction: column; margin: -30px 15px 30px; }
            .feature-card { width: 100%; }
            .hero h1 { font-size: 30px; }
            .hero p { font-size: 15px; }
            .nav-links { display: none; }
            .header { padding: 15px 20px; }
        }
    </style>

    <header class="header">
        <div class="logo-container">
            <div>
                <div class="logo-text">SMART HSE</div>
                <div class="logo-sub">CHILE</div>
            </div>
        </div>
        <nav class="nav-links">
            <a href="#inicio">Inicio</a>
            <a href="#soluciones">Soluciones</a>
            <a href="#tecnologia">Tecnología</a>
            <a href="#nosotros">Nosotros</a>
        </nav>
        <a href="mailto:contacto@smarthse.cl" class="btn-demo">Acceso a Consola</a>
    </header>

    <section id="inicio" class="hero">
        <h1>REVOLUCIONANDO LA GESTIÓN HSE TRANSVERSAL EN CHILE.</h1>
        <p>Potenciando la seguridad, el cumplimiento normativo (especialmente el DS44) y el crecimiento sostenible en todo el territorio.</p>
        <a href="mailto:contacto@smarthse.cl" class="btn-hero">Descubra cómo desenredar el DS44</a>
    </section>

    <div id="soluciones" class="features-container">
        <div class="feature-card">
            <div class="card-icon">⚠️</div>
            <h3>Gestión de Riesgos</h3>
            <p>Identificación, evaluación y control de peligros según DS44 y normativa SERNAGEOMIN.</p>
        </div>
        <div class="feature-card">
            <div class="card-icon">📋</div>
            <h3>Cumplimiento Normativo</h3>
            <p>Seguimiento en tiempo real de obligaciones legales mineras y vencimientos críticos.</p>
        </div>
        <div class="feature-card">
            <div class="card-icon">📊</div>
            <h3>Análisis y Datos</h3>
            <p>Dashboards configurables con KPIs de seguridad operacional y reportes ejecutivos.</p>
        </div>
        <div class="feature-card">
            <div class="card-icon">🛡️</div>
            <h3>Cultura de Seguridad</h3>
            <p>Programas de capacitación y gestión del comportamiento seguro en terreno.</p>
        </div>
    </div>

    <footer style="background-color: #002B49; color: #A0AEC0; text-align: center; padding: 40px 20px; font-size: 13px; margin-top: 40px;">
        <p style="margin-bottom: 8px; color: white; font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 18px; letter-spacing: 2px;">SMART HSE CHILE</p>
        <p style="margin-bottom: 16px;">Plataforma de gestión HSE para la minería y contratistas en Chile</p>
        <p>
            <a href="mailto:contacto@smarthse.cl" style="color: #55B4B0; text-decoration: none;">contacto@smarthse.cl</a>
            &nbsp;&nbsp;|&nbsp;&nbsp;
            <a href="https://smarthse.cl" style="color: #55B4B0; text-decoration: none;">smarthse.cl</a>
        </p>
        <p style="margin-top: 20px; font-size: 11px; color: #718096; border-top: 1px solid #1a3a52; padding-top: 16px;">
            © 2025 Smart HSE Chile. Todos los derechos reservados.
        </p>
    </footer>
""", unsafe_allow_html=True)
