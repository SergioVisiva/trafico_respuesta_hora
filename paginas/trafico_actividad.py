import streamlit as st
import pandas as pd
import sqlitecloud
from datetime import date, datetime
import calendar
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import utils as u


def mostrar():
    # --- Expander descriptivo ---
    with st.expander("ℹ️ Descripción del reporte", expanded=False):
        st.markdown(
            f"""
        ### Reporte de Trafico de Actividad (00-23H)

        💡 Este reporte permite analizar:
        - Horas de mayor actividad de contactos.
        - Distribución de respuestas por hora.
        - Detectar patrones de atención.

        ✉️ Para solicitar cambios, mejoras en gráficos, filtros o métricas, coordinar con:

        **Melissa Rossel**  
        Gerente de Marketing Digital y Business Intelligence, Educación Continua  
        📧 mrossel@ieduca.pe
        """,
            unsafe_allow_html=True,
        )

    colores = u.respuesta_color()

    # --- Conexión a SQLite Cloud ---
    if "key_une_ta" not in st.session_state.keys():
        st.session_state.key_une_ta = "UCAL"

    if "key_rango_fechas_ta" not in st.session_state.keys():
        st.session_state.key_rango_fechas_ta = (date(2025, 1, 1), u.hoy)

    if "key_respuesta_ult_contacto_ta" not in st.session_state.keys():
        st.session_state.key_respuesta_ult_contacto_ta = ["Indeciso", "Interesado"]

    # --- Sidebar: Filtros ---
    with st.sidebar:
        st.markdown(f"# ⚙️ Filtros")

        # UNE
        une_seleccion = u.une_seleccion(pagina="ta")
        # rango de fechas
        rango_fechas = u.rango_fechas(
            titulo="Fecha de accion",
            fecha_min=date(2025, 1, 1),
            fecha_max=date(2025, 12, 31),
            pagina="ta",
        )
        # respuesta
        respuesta_seleccion = u.respuesta_ult_contacto(pagina="ta")

    if u.validar_rango_fecha(rango_fechas) and une_seleccion and respuesta_seleccion:
        fecha_inicio, fecha_fin = rango_fechas
        graficar = True

    else:
        graficar = False
        st.warning(
            "⚠️ Porfavor termine de seleccionar la fecha de incio y fin, o una filtro esta sin seleccionar"
        )

    if graficar:
        # --- Query con filtros ---
        query = f"""
        WITH cte_1 AS (
            SELECT
                une,
                strftime('%H', fecha_ult_accion) AS hora_accion,
                respuesta_ult_contacto,
                fecha_ult_accion
            FROM df_toque
            WHERE
                date(fecha_ult_accion) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
                AND une = '{une_seleccion}'
                AND respuesta_ult_contacto IN ({", ".join(f"'{i}'" for i in respuesta_seleccion)})
        )  
        SELECT
            hora_accion,
            respuesta_ult_contacto,
            COUNT(*) AS conteo
            
        FROM cte_1
        GROUP BY hora_accion, respuesta_ult_contacto"""

        # st.markdown(f"""```sql{query}```""")

        df = u.consultar_bd(query)

        # Crear DataFrame con todas las combinaciones de respuesta y hora
        respuestas = df["respuesta_ult_contacto"].unique()
        horas = [f"{i:02d}" for i in range(24)]

        base = pd.MultiIndex.from_product(
            [respuestas, horas], names=["respuesta_ult_contacto", "hora_accion"]
        ).to_frame(index=False)

        # Unir con los datos existentes
        df = base.merge(df, on=["respuesta_ult_contacto", "hora_accion"], how="left")

        # Reemplazar valores faltantes de conteo con 0
        df["conteo"] = df["conteo"].fillna(0).astype(int)

        st.markdown("### Mapa de Calor de Contactos por Hora y Respuesta")

        # MAPA DE CALOR********************************************
        df_pivot = df.pivot(
            index="respuesta_ult_contacto",
            columns="hora_accion",  # o 'respuesta' si está escrito correctamente
            values="conteo",
        )

        fig, ax = plt.subplots(figsize=(15, len(respuesta_seleccion) * 0.5))
        sns.heatmap(
            df_pivot,
            annot=True,
            fmt="g",
            cmap="YlOrRd",
            ax=ax,
            annot_kws={"size": 8},
        )
        ax.set_xlabel("Horas del dia")
        ax.set_ylabel("")
        st.pyplot(fig)

        # LINEA VISUAL DIVISORA*****************************************************
        st.markdown("### Distribución de Contactos por Hora y Respuesta")

        tab_lineas, tab_barras = st.tabs(["Lineas", "Barras"])

        def plot_base(df, colores, tipo, height=550):
            """
            Devuelve un gráfico de barras o líneas con diseño uniforme.
            """
            if tipo == "bar":
                fig = px.bar(
                    df,
                    x="hora_accion",
                    y="conteo",
                    color="respuesta_ult_contacto",
                    color_discrete_map=colores,
                    barmode="group",
                    text_auto=".0f",
                    hover_data={"respuesta_ult_contacto": True, "conteo": ":,.0f"},
                    labels={
                        "hora_accion": "Hora de acción",
                        "conteo": "Cantidad de contactos",
                        "respuesta_ult_contacto": "Respuesta",
                    },
                )
            else:  # line
                fig = px.line(
                    df,
                    x="hora_accion",
                    y="conteo",
                    color="respuesta_ult_contacto",
                    color_discrete_map=colores,
                    markers=True,
                    hover_data={
                        "hora_accion": True,
                        "respuesta_ult_contacto": True,
                        "conteo": ":,.0f",
                    },
                )
                fig.update_traces(
                    mode="lines+markers",
                    line=dict(width=3),
                    marker=dict(size=8, symbol="circle"),
                )

            # Diseño uniforme para ambos tipos
            fig.update_layout(
                template="plotly_white",
                height=height,
                yaxis_title="Cantidad de contactos",
                xaxis_title="Horas del dia",
                legend_title="Respuesta",
                xaxis=dict(
                    showgrid=True,
                    gridcolor="rgba(200,200,200,0.3)",
                    title_font=dict(size=16, color="#555"),
                    tickfont=dict(size=14, color="#555"),
                ),
                yaxis=dict(
                    rangemode="tozero",
                    showgrid=True,
                    gridcolor="rgba(200,200,200,0.3)",
                    title_font=dict(size=16, color="#555"),
                    tickfont=dict(size=14, color="#555"),
                ),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(245,245,245,1)",
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=0.95,
                    xanchor="right",
                    x=1.02,
                    font=dict(size=12),
                ),
            )

            fig.update_traces(
                hovertemplate="<b>Hora:</b> %{x}<br><b>Respuesta:</b> %{fullData.name}<br><b>Conteo:</b> %{y:,}<extra></extra>"
            )
            if tipo == "line":
                fig.update_xaxes(range=[-0.5, 23.5])

            return fig

        # --- Uso en tabs ---
        with tab_barras:
            st.plotly_chart(
                plot_base(df, colores, tipo="bar"), use_container_width=True
            )

        with tab_lineas:
            st.plotly_chart(
                plot_base(df, colores, tipo="line"), use_container_width=True
            )

    with st.expander("Ver Query"):
        st.code(query, language="sql")
