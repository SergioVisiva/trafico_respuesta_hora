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
import utils as u
from io import BytesIO


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def mostrar():
    with st.expander("ℹ️ Descripción del reporte", expanded=False):
        st.markdown(
            """
        ### Reporte de Base Gestionable

        Este reporte se basa en los leads que cada asesor tiene en cartera al día de hoy.  
        Cada fila de la tabla representa:

        - **Asesor**: el asesor que tiene ese lead en cartera y lo está gestionando.  
        - **ID Cliente**: el identificador del lead.  
        - **Programa**: el último programa en el que el cliente estuvo interesado.  
        - **Respuesta Último Contacto**: la última respuesta del cliente.  
        - **Fecha de llegada**: la fecha en que el lead ingresó a la cartera del asesor.  
        - **Cantidad de toques**: total de contactos que ha tenido el lead, tanto por el asesor actual como por otros que lo gestionaron previamente.

        En general, cada registro representa el **último estado del lead**, y esta información cambia diariamente debido al movimiento de leads entre asesores.

        💡 Este reporte se puede combinar con los gráficos de análisis para identificar patrones de desempeño por asesor o programa, detectar leads sin seguimiento y optimizar la gestión de la cartera.

        ✉️ Si desea solicitar algún cambio, mejora de gráficos, análisis, filtros o métricas, debe coordinarlo a través de:

        **Melissa Rossel**  
        Gerente de Marketing Digital y Business Intelligence, Educación Continua  
        📧 mrossel@ieduca.pe
        """,
            unsafe_allow_html=True,
        )

    fecha_corte_filtro = (
        (datetime(u.anio, u.mes, 1) - datetime.timedelta(days=7)).date()
        if u.dia <= 7
        else date(u.anio, u.mes, 1)
    )

    if "key_une_bg" not in st.session_state.keys():
        st.session_state.key_une_bg = "UCAL"

    if "key_rango_fechas_bg" not in st.session_state.keys():
        st.session_state.key_rango_fechas_bg = (fecha_corte_filtro, u.hoy)

    condiciones = []
    # --- Sidebar: Filtros ---
    with st.sidebar:

        st.markdown(f"# ⚙️ Filtros")
        # Rango de fechas
        une_seleccion = u.une_seleccion(pagina="bg")
        # rango de fechas
        rango_fechas = u.rango_fechas(
            titulo="Fecha de llegada",
            fecha_min=date(u.anio, u.mes - 1, 1),
            fecha_max=u.hoy,
            pagina="bg",
        )

        # programas
        programa = u.programa(une=une_seleccion, nombre_df="df_lead", pagina="bg")
        # respuesta
        respuesta_ult_contacto = u.respuesta_ult_contacto(pagina="bg")
        # asesor
        asesor = u.asesor(une=une_seleccion, nombre_df="df_lead", pagina="bg")
        # tipo contacto
        tipo_contacto = u.tipo_contacto(pagina="bg")

        rango_toques = st.multiselect(
            "Rango de conteo de toques", ["sin toque", "entre 1 y 2", "mas de 2"]
        )

    if tipo_contacto:
        condiciones.append(f" and tipo_contacto in ({u.items_comas(tipo_contacto)})")
    if rango_toques:
        condiciones.append(f" and rango_toques in ({u.items_comas(rango_toques)})")
    if programa:
        condiciones.append(f" and programa in ({u.items_comas(programa)})")
    if respuesta_ult_contacto:
        condiciones.append(
            f" and respuesta_ult_contacto in ({u.items_comas(respuesta_ult_contacto)})"
        )
    if asesor:
        condiciones.append(f" and asesor in ({u.items_comas(asesor)})")
    if u.validar_rango_fecha(rango_fechas):
        fecha_inicio, fecha_fin = rango_fechas
        condiciones.append(
            f" and fecha_llegada BETWEEN '{fecha_inicio}' AND '{fecha_fin}' "
        )

    query = f"""With cte_1 as (SELECT 
    une,
    asesor,
    id_cliente,
    programa,
    respuesta_ult_contacto,
    fecha_llegada,
    conteo_toques,
    tipo_contacto,
    CASE
        WHEN conteo_toques = 0 THEN 'sin toque'
        WHEN conteo_toques BETWEEN 1 AND 2 THEN 'entre 1 y 2'
        WHEN conteo_toques > 2 THEN 'mas de 2'
    END AS rango_toques
    
    FROM df_lead l
    left join df_cliente cl on cl.id_une = l.id_une 
    )
    select * from cte_1
    where une = '{une_seleccion}' {' '.join(condiciones) if condiciones else ''}
    """

    # st.code(query, language="sql")
    df = u.consultar_bd(query)
    df = df.sort_values("fecha_llegada", ascending=False)

    # 🔹 Cuadritos de info
    # ------------------
    leads = len(df)
    total_toques = df["conteo_toques"].sum()
    positivos = (df["tipo_contacto"] == "positivo").sum()
    negativos = (df["tipo_contacto"] == "negativo").sum()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🧑 Leads", f"{leads}")
    col2.metric("📊 Total toques", f"{total_toques}")
    col3.metric("✅ Contactos positivos", f"{positivos}")
    col4.metric("❌ Contactos negativos", f"{negativos}")

    # Copia para mostrar sin columnas auxiliares
    df_mostrar = df.drop(columns=["tipo_contacto", "rango_toques", "une"])

    # Serie auxiliar para colorear 'respuesta_ult_contacto'
    tipo_contacto_aux = df["tipo_contacto"]

    # Función de estilo condicional para 'respuesta_ult_contacto'
    def estilo_respuesta(row):
        color_map = {"positivo": "#C8E6C9", "negativo": "#FFCDD2", "otros": "#E0E0E0"}
        tipo = tipo_contacto_aux[row.name]  # usamos la Serie auxiliar
        color = color_map.get(tipo, "#FFFFFF")
        return [
            f"background-color: {color}" if col == "respuesta_ult_contacto" else ""
            for col in row.index
        ]

    # Aplicar estilos
    styled_df = df_mostrar.style.apply(
        estilo_respuesta, axis=1
    ).background_gradient(  # colores por tipo_contacto en 'respuesta_ult_contacto'
        subset=["conteo_toques"], cmap="YlOrRd"
    )  # mapa de calor en 'conteo_toques'

    # Mostrar en Streamlit
    st.dataframe(styled_df, use_container_width=True, hide_index=True, height=600)

    # Función para convertir el DataFrame a Excel en memoria
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Sheet1")
        processed_data = output.getvalue()
        return processed_data

    # Botón de descarga
    excel_data = to_excel(df)
    st.download_button(
        label="📥 Descargar Excel",
        data=excel_data,
        file_name="reporte.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    # 🔹 Expander con análisis gráficos************************************************
    with st.expander("📊 Análisis Gráficos", expanded=True):
        st.markdown(
            f"Análisis basado en **todos los leads** de **{une_seleccion}** "
            f"entre **{fecha_inicio}** y **{fecha_fin}**."
        )
        tab1, tab2 = st.tabs(["Ranking de asesores", "Programas por tipo"])

        # --- TAB 1: Ranking de asesores ---
        with tab1:
            st.markdown("### Ranking de asesores por cantidad de leads")

            query_asesores = f"""
                SELECT asesor, COUNT(id_une) AS total_leads
                FROM df_lead 
                WHERE une = '{une_seleccion}'
                AND fecha_llegada BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
                GROUP BY asesor
                ORDER BY total_leads DESC
            """
            df_asesores = u.consultar_bd(query_asesores)

            fig_asesores = px.bar(
                df_asesores,
                x="asesor",
                y="total_leads",
                text="total_leads",
                color="total_leads",
                color_continuous_scale="Blues",
            )
            fig_asesores.update_layout(yaxis_title="Leads únicos", xaxis_title="Asesor")
            st.plotly_chart(fig_asesores, use_container_width=True)

        # --- TAB 2: Programas por tipo de contacto ---
        with tab2:
            st.markdown(
                "### Programas con mayor cantidad de leads por tipo de contacto"
            )

            tipos = ["positivo", "negativo", "otros"]
            for t in tipos:
                st.markdown(f"#### Tipo de contacto: {t.capitalize()}")

                query_programas = f"""
                    SELECT programa, COUNT(id_une) AS total_leads
                    FROM df_lead
                    WHERE une = '{une_seleccion}'
                    AND fecha_llegada BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
                    AND tipo_contacto = '{t}'
                    GROUP BY programa
                    ORDER BY total_leads DESC
                """
                df_prog = u.consultar_bd(query_programas)

                if not df_prog.empty:
                    fig_prog = px.bar(
                        df_prog,
                        x="programa",
                        y="total_leads",
                        text="total_leads",
                        color="total_leads",
                        color_continuous_scale="Viridis",
                    )
                    fig_prog.update_layout(
                        yaxis_title="Leads únicos", xaxis_title="Programa"
                    )
                    st.plotly_chart(fig_prog, use_container_width=True)
                else:
                    st.info(
                        f"No hay datos para el tipo de contacto '{t}' en este rango de fechas."
                    )

    with st.expander("Ver Query"):
        st.code(query, language="sql")
