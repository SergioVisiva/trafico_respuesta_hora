import streamlit as st
import pandas as pd
import numpy as np
import sqlitecloud
from datetime import date, datetime, timedelta
import calendar
import matplotlib.pyplot as plt
from matplotlib import cm
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

import sys
import os
import utils as u
from io import BytesIO
from collections import Counter

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def mostrar():
    if "key_programas_seg" not in st.session_state:
        st.session_state.key_programas_seg = [
            "Cajero Financiero Y Comercial",
            "Administracion De Negocios",
            "Como Importar Desde China",
            "Contabilidad Para Negocios",
            "Data Analytics",
            "Excel Experto",
            "Gestion De Logistica",
            "Ofimatica Pro",
            "Operador De Aduanas Y Comercio Exterior",
            "Planillas Y Legislacion Laboral",
            "Power Bi",
            "Seguridad Y Salud Ocupacional Y Medio Ambiente",
            "Marketing Digital",
            "Diseño Grafico Digital",
            "Ingles",
        ]

    respuesta_propiedades = u.respuesta_propiedades
    colores_tipo_contacto = u.colores_tipo_contacto

    def graficar_ranking(une, categoria):
        with st.expander(f"Top 15 {categoria} con mayor cantidad de leads en cartera"):
            orden_programas = u.consultar_bd(
                f"""                            
                SELECT {categoria}
                FROM df_lead
                WHERE une = '{une}'
                GROUP BY {categoria}
                ORDER BY COUNT(id_une) DESC
                LIMIT 15
                """
            )
            orden_lista = orden_programas[f"{categoria}"].tolist()

            df_programas = u.consultar_bd(
                f"""
                SELECT
                l.{categoria},
                l.tipo_contacto,
                COUNT(l.id_une) AS conteo
                FROM df_lead AS l
                WHERE 
                l.une = '{une}'
                AND l.{categoria} IN (
                    SELECT {categoria}
                    FROM df_lead
                    WHERE une = '{une}'
                    GROUP BY {categoria}
                    ORDER BY COUNT(id_une) DESC
                    LIMIT 15
                )
                GROUP BY l.{categoria}, l.tipo_contacto
                ORDER BY l.{categoria}, l.tipo_contacto
                """
            )
            df_programas[f"{categoria}"] = pd.Categorical(
                df_programas[f"{categoria}"], categories=orden_lista, ordered=True
            )
            df_programas["tipo_contacto"] = pd.Categorical(
                df_programas["tipo_contacto"],
                categories=["negativo", "positivo", "otros", "venta"],
                ordered=True,
            )
            df_programas = df_programas.sort_values(
                by=[f"{categoria}", "tipo_contacto"]
            )

            fig = px.bar(
                df_programas,
                x=f"{categoria}",
                y="conteo",
                color="tipo_contacto",
                color_discrete_map=colores_tipo_contacto,
                title=f"Distribución por tipo de contacto (Top 15 {categoria})",
            )

            fig.update_layout(
                xaxis_title=f"{categoria}",
                yaxis_title="Cantidad de contactos",
                legend_title="Tipo de contacto",
                bargap=0.15,
                template="plotly_white",
                title=dict(x=0.5, xanchor="center"),
            )

            grafico = st.plotly_chart(fig, use_container_width=True)

    def graficar_metricas(une, categoria, cat_seleccion):
        df_programa_historico = u.consultar_bd(
            f"""
                SELECT
                COUNT(DISTINCT id_une) AS leads,
                SUM(CASE 
                    WHEN tipo_accion = 'Venta' 
                    THEN 1
                    ELSE 0 
                END) AS venta
                FROM df_toque
                WHERE
                une = '{une}'
                AND {categoria} = '{cat_seleccion}'
                GROUP BY {categoria}
        """
        )
        leads_gestionados = df_programa_historico["leads"][0]
        ventas = df_programa_historico["venta"][0]
        conversion = ((ventas / leads_gestionados) * 100).round(2)

        st.subheader("Leads Gestionados Historico")
        cola, colb, colc = st.columns([0.3, 0.3, 0.4])
        with cola:
            st.metric("Clientes", leads_gestionados)
        with colb:
            st.metric("Ventas", ventas)
        with colc:
            st.metric("Conversion", f"{conversion} %")

    def graficar_tendencia_gestion(une, categoria, cat_seleccion):
        # historico por mes
        df_historico_mes = u.consultar_bd(
            f"""
            SELECT
            strftime('%m', fecha_accion) AS num_mes,
            count( DISTINCT id_une) as Clientes,
            count( id_une) as Toques,
            sum( CASE
            when tipo_accion = 'Venta'
            then 1
            else 0
            END
            )  as Venta
                
            from
            df_toque
            where 
            une = '{une}' and
            {categoria} = '{cat_seleccion}'
            GROUP by strftime('%m', fecha_accion)
            order by strftime('%m', fecha_accion) ASc
        """
        )
        df_meses = u.df_meses
        df_historico_mes["num_mes"] = df_historico_mes["num_mes"].astype(int)
        df_historico_mes = df_meses.merge(df_historico_mes, how="left", on="num_mes")
        df_historico_mes.fillna(0)

        # Crear figura combinada
        fig_hm = go.Figure()

        # --- Barras (ventas) - se agregan primero para que queden atrás ---
        fig_hm.add_trace(
            go.Bar(
                x=df_historico_mes["nom_mes"],
                y=df_historico_mes["Venta"],
                name="Ventas",
                marker_color="#FFD54F",
                yaxis="y2",  # usa el segundo eje Y
                opacity=0.5,  # leve transparencia para no tapar las líneas
            )
        )

        # --- Líneas (clientes y toques) - se agregan después para que estén al frente ---
        fig_hm.add_trace(
            go.Scatter(
                x=df_historico_mes["nom_mes"],
                y=df_historico_mes["Clientes"],
                name="Clientes",
                mode="lines+markers",
                line=dict(color="#42A5F5", width=2),
            )
        )
        fig_hm.add_trace(
            go.Scatter(
                x=df_historico_mes["nom_mes"],
                y=df_historico_mes["Toques"],
                name="Toques",
                mode="lines+markers",
                line=dict(color="#66BB6A", width=2),
            )
        )

        # --- Configurar diseño ---
        fig_hm.update_layout(
            title=dict(
                text="Tendencia Mensual: Actividad (Clientes y Toques) vs Resultados (Ventas)",
                x=0.5,
                xanchor="center",
            ),
            xaxis=dict(title="Mes"),
            yaxis=dict(
                tickvals=np.linspace(0, df_historico_mes["Toques"].max(), 5).astype(
                    int
                ),
                title="Clientes / Toques",
                rangemode="tozero",
            ),
            yaxis2=dict(
                tickvals=np.linspace(0, df_historico_mes["Venta"].max(), 5).astype(int),
                title="Ventas",
                overlaying="y",
                side="right",
                rangemode="tozero",
            ),
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5
            ),
            bargap=0.3,
            template="plotly_white",
        )

        st.plotly_chart(fig_hm, use_container_width=True)

    def graficar_cartera(une, categoria, cat_seleccion):
        st.subheader("Leads en Cartera")
        tab1, tab2 = st.tabs(["Tabla", "Grafico"])
        with tab1:
            df_programa_cartera = u.consultar_bd(
                f"""
                                SELECT
                                tipo_contacto,
                                respuesta_ult_contacto,
                                count(id_une) as conteo_leads
                                from df_lead
                                where 
                                une = '{une}' and
                                {categoria} = '{cat_seleccion}'
                                group by  tipo_contacto, respuesta_ult_contacto
                                order by tipo_contacto
                                """
            )
            total_leads_cartera = df_programa_cartera["conteo_leads"].sum()
            df_programa_cartera["Distribucion"] = (
                (df_programa_cartera["conteo_leads"] / total_leads_cartera) * 100
            ).round(2)

            colores = df_programa_cartera["tipo_contacto"].map(colores_tipo_contacto)
            df_mostrar = df_programa_cartera.drop(columns=["tipo_contacto"])
            # Aplicar los colores a la columna respuesta_ult_contacto
            styler = df_mostrar.style.apply(
                lambda _: [f"background-color: {c}" for c in colores],
                subset=["respuesta_ult_contacto"],
            )
            alto = len(df_mostrar) * 41
            st.dataframe(
                styler,
                column_config={
                    "Distribucion": st.column_config.ProgressColumn(
                        "Distribución",
                        format="%.2f%%",
                        min_value=0,
                        max_value=100,
                    )
                },
                hide_index=True,
                height=alto,
            )
        with tab2:
            fig = px.pie(
                df_programa_cartera,
                values="conteo_leads",
                names="tipo_contacto",
                color="tipo_contacto",
                color_discrete_map=colores_tipo_contacto,
                hole=0.3,
            )
            fig.update_layout(
                title=dict(
                    text="Distribucion por tipo de contacto", x=0.5, xanchor="center"
                )
            )

            st.plotly_chart(fig, use_container_width=True)

    with st.sidebar:
        une_seleccion = u.une(pagina="rs")

    tab_programa, tab_asesor = st.tabs(["Programa", "Asesor"])

    # **********************************************************
    with tab_programa:
        graficar_ranking(une_seleccion, "programa")
        programa = u.unico_programa(une_seleccion, "df_lead", "rs")
        # historico de leads getioado y ventas
        col1, col_, col2 = st.columns([0.7, 0.02, 0.28])

        # HISTORICO
        with col1:
            graficar_metricas(une_seleccion, "programa", programa)
            graficar_tendencia_gestion(une_seleccion, "programa", programa)

        # EN CARTERA
        with col2:
            graficar_cartera(une_seleccion, "programa", programa)

    # **********************************************************
    with tab_asesor:
        graficar_ranking(une_seleccion, "asesor")
        asesor = u.unico_asesor(
            une_seleccion,
            nombre_df="df_toque",
            pagina="rs",
            nombre_fecha="fecha_accion",
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 12, 31),
        )
        # historico de leads getioado y ventas
        col1, col_, col2 = st.columns([0.7, 0.02, 0.28])

        # HISTORICO
        with col1:
            graficar_metricas(une_seleccion, "asesor", asesor)
            graficar_tendencia_gestion(une_seleccion, "asesor", asesor)

        # EN CARTERA
        with col2:
            graficar_cartera(une_seleccion, "asesor", asesor)

        # ************************************************    seguimiento cursos especificos
        programas_seg = st.multiselect(
            "Seleccionar programa",
            u.get_items("SELECT DISTINCT programa FROM df_toque"),
            key="key_programas_seg",
        )

        # def graficar_tabla(programas, asesor, condicion_fecha):
        #     query = f"""
        #             SELECT
        #             asesor,
        #             programa,
        #             COUNT(DISTINCT id_une) AS leads_gestionados,
        #             SUM(
        #             CASE
        #             when tipo_accion = 'Venta'
        #             then 1 else 0
        #             END
        #             )  as Venta

        #             FROM df_toque
        #             WHERE
        #             asesor = '{asesor}' and
        #             programa in ({u.items_comas(programas)}) and
        #             DATE(fecha_accion) {condicion_fecha}
        #             GROUP BY asesor, programa;
        #             """
        #     st.code(query, language="sql")

        #     df_seg = u.consultar_bd(query)
        #     st.dataframe(df_seg)

        #     if df_seg.empty:
        #         st.warning("No se encontraron datos para este asesor.")
        #     else:
        #         # --- Cálculos adicionales ---
        #         total_leads = df_seg["leads_gestionados"].sum()
        #         df_seg["distribucion_%"] = (
        #             df_seg["leads_gestionados"] / total_leads * 100
        #         ).round(2)
        #         df_seg["conversion_%"] = (
        #             df_seg["venta"] / df_seg["leads_gestionados"] * 100
        #         ).round(2)

        #         # --- Tabla base ---
        #         st.subheader("📊 Métricas por Programa")

        #         # --- Mapa de calor para conversión ---
        #         fig = px.imshow(
        #             [df_seg["conversion_%"]],
        #             labels=dict(x="Programa", color="Conversión (%)"),
        #             x=df_seg["programa"],
        #             y=["Conversión"],
        #             color_continuous_scale="RdYlGn",
        #         )
        #         fig.update_layout(height=150)
        #         st.plotly_chart(fig, use_container_width=True)

        #         # --- Tabla con barras y porcentajes ---
        #         df_bar = df_seg.copy()
        #         df_bar["barra_distribucion"] = df_bar["distribucion_%"].apply(
        #             lambda x: "█" * int(x / 2)
        #         )

        #         # Mostrar tabla en Streamlit con formato visual
        #         st.dataframe(
        #             df_bar[
        #                 [
        #                     "programa",
        #                     "leads_gestionados",
        #                     "distribucion_%",
        #                     "venta",
        #                     "conversion_%",
        #                 ]
        #             ],
        #             use_container_width=True,
        #             hide_index=True,
        #         )

        #         # --- Barra visual extra (opcional) ---
        #         st.bar_chart(df_seg.set_index("programa")["distribucion_%"])

        # col_actual, col_anterior = st.columns([0.5, 0.5])
        # with col_actual:
        #     st.subheader("Leads Gestionados en el actual mes")
        #     graficar_tabla(programas_seg, asesor, condicion_fecha=">= '2025-11-01'")

        # with col_anterior:
        #     st.subheader("Leads Gestionados en meses anteriores")
        #     graficar_tabla(programas_seg, asesor, condicion_fecha="< '2025-11-01'")
