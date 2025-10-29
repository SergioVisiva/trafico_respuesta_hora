import streamlit as st
from streamlit_option_menu import option_menu
from paginas import pipeline, pipeline_, trafico_actividad, base_gestionable
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
    options=["Pipeline", "Trafico Actividad (00-23H)", "Base Gestionable"],
    # icons=["collection", "bar-chart", "person-x"],
    menu_icon="cast",
    default_index=2,
    orientation="horizontal",
)

# --- Mostrar la página seleccionada ---
if seleccion == "Pipeline":
    pipeline.mostrar()
if seleccion == "Trafico Actividad (00-23H)":
    trafico_actividad.mostrar()
elif seleccion == "Base Gestionable":
    base_gestionable.mostrar()
