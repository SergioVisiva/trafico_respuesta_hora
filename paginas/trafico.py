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
from utils import connection, hoy, respuesta_color


def mostrar():

    colores = respuesta_color()

    # --- Conexión a SQLite Cloud ---

    if "key_rango_fechas" not in st.session_state.keys():
        st.session_state.key_rango_fechas = (date(2025, 1, 1), hoy)
    if "key_respuesta_ult_accion" not in st.session_state.keys():
        st.session_state.key_respuesta_ult_accion = ["Indeciso", "Interesado"]

    @st.cache_data
    def get_programas(query):
        with connection(db="base_reportes.sqlite") as con:
            cursor = con.execute(query)
            return [row[0] for row in cursor.fetchall()]

    @st.cache_data
    def consultar_bd(query, db="base_reportes.sqlite"):
        with connection(db) as con:
            cursor = con.execute(query)
            columnas = [desc[0] for desc in cursor.description]
            datos = cursor.fetchall()
            return pd.DataFrame(datos, columns=columnas)

    def validar_rango_fecha(rango_fechas):
        fechas_correcta = []
        # validamos que sean dos objetos
        if len(rango_fechas) == 2:
            # validamos que ambos objetos sean de instancia fecha
            if all(isinstance(f, date) for f in rango_fechas):
                # recorremos ambos objetos
                for f in rango_fechas:
                    año = f.year
                    mes = f.month
                    dia = f.day

                    # validamos que la fecha recorrida tenga valores validos de año, mes y dia
                    _, ultimo_dia = calendar.monthrange(año, mes)
                    if (
                        (2023 <= año <= hoy.year)
                        and (1 <= mes <= 12)
                        and (1 <= dia <= ultimo_dia)
                    ):
                        fechas_correcta.append(True)

                    else:
                        fechas_correcta.append(False)

            else:
                fechas_correcta = [False]
        else:
            fechas_correcta = [False]

        return all(fechas_correcta)

    # --- Sidebar: Filtros ---
    with st.sidebar:
        st.markdown(f"# ⚙️ Filtros")
        # Rango de fechas
        rango_fechas = st.date_input(
            "Rango de fecha",
            key="key_rango_fechas",
            min_value=date(2025, 1, 1),
            max_value=date(2025, 12, 31),
            help="Seleccione primero la fecha inicial y luego la fecha final",
        )

        # UNE
        une_seleccion = st.selectbox(
            "Seleccionar UNE",
            ["TLS", "UCAL", "CERTUS"],
            index=0,
            key="key_une",
        )

        # Respuesta
        respuesta_seleccion = st.multiselect(
            "Seleccionar Respuesta",
            get_programas(
                "SELECT DISTINCT respuesta_ult_contacto FROM tb_toque_compacto WHERE respuesta_ult_contacto IS NOT NULL"
            ),
            key="key_respuesta_ult_accion",
        )

    if validar_rango_fecha(rango_fechas) and une_seleccion and respuesta_seleccion:
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
            FROM tb_toque_compacto
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

        df = consultar_bd(query)

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

        st.write("b")
