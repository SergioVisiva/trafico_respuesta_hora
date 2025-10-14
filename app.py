import streamlit as st
from streamlit_option_menu import option_menu
from paginas import pipeline, trafico_actividad, base_gestionable

# --- Configuración de la interfaz ---
st.set_page_config(
    page_title="Reporte",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
# --- CSS para estilo general ---
st.markdown(
    """
    <style>
        html, body, [class*="css"] {
            font-size: 14px !important;
        }
        .block-container {
            padding-top: 0.5rem;
            margin-top: 30px;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 1300px;
            margin-left: auto;
            margin-right: auto;
        }
        .stButton > button {
            padding: 0.25rem 0.75rem;
            font-size: 14px;
        }
        .stDownloadButton > button {
            padding: 0.4rem 0.8rem;
            font-size: 14px;
        }
        h1, h2, h3, h4 {
            margin-bottom: 0.3rem;
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
    default_index=1,
    orientation="horizontal",
)

# --- Mostrar la página seleccionada ---
if seleccion == "Pipeline":
    pipeline.mostrar()
if seleccion == "Trafico Actividad (00-23H)":
    trafico_actividad.mostrar()
elif seleccion == "Base Gestionable":
    base_gestionable.mostrar()
