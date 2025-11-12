import streamlit as st
from streamlit_option_menu import option_menu
from paginas import pipeline, pipeline_, trafico_actividad, base_gestionable, resumen
import locale
import pandas as pd

pd.set_option("styler.render.max_elements", 1_000_000)

# 🔸 Configura el idioma (usa el que funcione en tu sistema operativo)
locale.setlocale(locale.LC_TIME, "C")

# --- Configuración de la interfaz ---
st.set_page_config(
    page_title="Reporte",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
.block-container {
    max-width: 100% !important;  /* ocupa todo el ancho */
    padding-left: 1rem;
    padding-right: 1rem;
    padding-top: 3rem;         /* 👈 reduce el espacio arriba (valor intermedio) */
}
[data-testid="stDataFrame"] div[role="grid"] {
    width: 100% !important;      /* tabla ancho completo */
}
div[data-testid="stHorizontalBlock"] {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;             /* evita que se corte el menú */
}
</style>
""",
    unsafe_allow_html=True,
)


# --- Menú horizontal ---
seleccion = option_menu(
    menu_title=None,
    options=["Pipeline", "Trafico Actividad (00-23H)", "Base Gestionable", "Resumen"],
    # icons=["collection", "bar-chart", "person-x"],
    menu_icon="cast",
    default_index=3,
    orientation="horizontal",
)

# --- Mostrar la página seleccionada ---
if seleccion == "Resumen":
    resumen.mostrar()
elif seleccion == "Pipeline":
    pipeline.mostrar()
elif seleccion == "Trafico Actividad (00-23H)":
    trafico_actividad.mostrar()
elif seleccion == "Base Gestionable":
    base_gestionable.mostrar()

st.markdown(
    """
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: #f8f9fa;
    color: #333;
    text-align: center;
    padding: 10px 0;
    font-size: 14px;
    border-top: 1px solid #ddd;
}
.footer a {
    color: #0073b1;
    text-decoration: none;
    margin: 0 5px;
}
</style>

<div class="footer">
    <b>Sergio Carbajal</b> — Analista de Datos y Automatización |
    <a href="https://www.linkedin.com/in/sergiocarbajal/" target="_blank">LinkedIn</a> |
    <a href="https://github.com/sergiocarbajal421-alt" target="_blank">GitHub</a> |
    📧 <a href="mailto:sergiocarbajal421@gmail.com">sergiocarbajal421@gmail.com</a> |
    📞 901 439 762
</div>
""",
    unsafe_allow_html=True,
)
