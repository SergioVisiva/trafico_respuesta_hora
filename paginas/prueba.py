import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


def mostrar():
    # Datos de ejemplo
    df = pd.DataFrame(
        {
            "hora_accion": [f"{h:02d}:00" for h in range(8, 18)],
            "respuesta_ult_contacto": np.random.choice(
                ["Positiva", "Negativa", "Pendiente"], 10
            ),
            "conteo": np.random.randint(10, 200, 10),
        }
    )

    # --- Estilo visual ---
    st.markdown(
        """
    <div style="
        background-color:#f9f9f9;
        border:1px solid #ddd;
        padding:20px;
        border-radius:15px;
        box-shadow:0 2px 8px rgba(0,0,0,0.05);
        margin-bottom:25px;
    ">
    """,
        unsafe_allow_html=True,
    )

    # --- Contenido visual agrupado ---
    col1, col2 = st.columns([1, 3])

    with col1:
        tipo_grafico = st.radio(
            "📊 Tipo de gráfico:", ["Barras", "Líneas"], horizontal=True, index=0
        )

    with col2:
        st.write("")  # Solo para equilibrar el alto visualmente

    # --- Gráfico dinámico ---
    if tipo_grafico == "Barras":
        fig = px.bar(
            df,
            x="hora_accion",
            y="conteo",
            color="respuesta_ult_contacto",
            title="Distribución de contactos por hora",
            text_auto=True,
        )
    else:
        fig = px.line(
            df,
            x="hora_accion",
            y="conteo",
            color="respuesta_ult_contacto",
            markers=True,
            title="Evolución de contactos por hora",
        )

    fig.update_layout(
        template="plotly_white",
        title_font=dict(size=18, family="Arial Black", color="#333"),
        legend_title_text="Respuesta",
        xaxis_title="Hora de acción",
        yaxis_title="Cantidad de contactos",
        height=450,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Cierre del div (marco)
    st.markdown("</div>", unsafe_allow_html=True)
