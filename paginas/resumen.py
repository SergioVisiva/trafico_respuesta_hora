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
import altair as alt

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
            df_catera = u.consultar_bd(
                f"""
                with df_ult_toque as (
                select 
                    id_une,
                    {categoria},
                    fecha_accion,
                    tipo_contacto,
                    row_number() over(
                        partition by id_une
                        order by fecha_accion desc
                    ) as rn
                from 
                    df_toque
                where 
                    une = '{une}'
                )
                
                select 
                    {categoria},
                    tipo_contacto,
                    COUNT(id_une) AS conteo_leads
                from 
                    df_ult_toque
                where
                    rn = 1 and
                    DATE(fecha_accion) >= '{date(2025,u.mes,1)}'
                GROUP BY 
                    {categoria}, 
                    tipo_contacto        
                """
            )
            top_15 = (
                df_catera.groupby(f"{categoria}")["conteo_leads"]
                .sum()
                .reset_index(name="leads")
                .sort_values("leads", ascending=False)
                .head(15)
            )
            orden_lista = top_15[f"{categoria}"].tolist()

            df_catera = df_catera[df_catera[f"{categoria}"].isin(orden_lista)]

            orden_tipos = ["negativo", "positivo", "otros", "venta"]
            df_catera["orden_stack"] = df_catera["tipo_contacto"].map(
                {"negativo": 0, "positivo": 1, "otros": 2, "venta": 3}
            )

            # ====== 3. Calcular totales para poner arriba ======
            totales = (
                df_catera.groupby(categoria)["conteo_leads"]
                .sum()
                .reset_index(name="total_leads")
            )

            # ====== 4. Gráfico principal ======
            chart_barras = (
                alt.Chart(df_catera)
                .mark_bar()
                .encode(
                    x=alt.X(
                        f"{categoria}:N",
                        sort=orden_lista,
                        title=categoria,
                        axis=alt.Axis(
                            labelAngle=-45,
                            labelFontSize=10,
                            labelLimit=400,
                            labelOverlap=False,
                        ),
                    ),
                    y=alt.Y(
                        "conteo_leads:Q",
                        stack="zero",
                        title="Cantidad de leads en cartera",
                    ),
                    color=alt.Color(
                        "tipo_contacto:N",
                        scale=alt.Scale(
                            domain=orden_tipos,
                            range=[colores_tipo_contacto[c] for c in orden_tipos],
                        ),
                        title="Tipo de contacto",
                    ),
                    order=alt.Order("orden_stack:Q", sort="ascending"),
                    tooltip=[
                        alt.Tooltip("tipo_contacto:N", title="Tipo de contacto"),
                        alt.Tooltip("conteo_leads:Q", title="Leads"),
                    ],
                )
                .properties(
                    width="container",
                    height=400,
                )
            )

            # ====== 5. Texto de totales encima de cada barra ======
            chart_text = (
                alt.Chart(totales)
                .mark_text(dy=-5, fontWeight="bold", size=12)
                .encode(
                    x=alt.X(f"{categoria}:N", sort=orden_lista),
                    y="total_leads:Q",
                    text="total_leads:Q",
                )
            )

            # ====== 6. Combinar ======
            grafico = (chart_barras + chart_text).properties(
                width="container",
            )
            st.altair_chart(grafico, use_container_width=True)

    def graficar_metricas(une, categoria, cat_seleccion, opcion_fecha):
        condicion_fecha = (
            f"DATE(fecha_accion) > '{date(2025,u.mes, 1)}' and"
            if opcion_fecha == "Este Mes"
            else ""
        )

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
            une = '{une}' and
            {condicion_fecha}
            {categoria} = '{cat_seleccion}'
            GROUP BY {categoria}
        """
        )
        if df_programa_historico.empty:
            st.warning(f"No se encontraron datos para este {categoria}.")
        else:
            leads_gestionados = df_programa_historico["leads"][0]
            ventas = df_programa_historico["venta"][0]
            conversion = ((ventas / leads_gestionados) * 100).round(2)

            cola, colb, colc = st.columns([0.3, 0.3, 0.4])
            with cola:
                st.metric("Clientes", leads_gestionados)
            with colb:
                st.metric("Ventas", ventas)
            with colc:
                st.metric("Conversion", f"{conversion} %")

    def graficar_tendencia_gestion_anual(une, categoria, cat_seleccion):
        # historico por mes
        df_historico_mes = u.consultar_bd(
            f"""
            SELECT
            strftime('%m', fecha_accion) AS num_mes,
            count(DISTINCT id_une) as Clientes,
            count(id_une) as Toques,
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

        if df_historico_mes.empty:
            st.warning(f"No se encontraron datos para este {categoria}.")
        else:
            df_meses = u.df_meses
            df_historico_mes["num_mes"] = df_historico_mes["num_mes"].astype(int)
            df_historico_mes = df_meses.merge(
                df_historico_mes, how="left", on="num_mes"
            )
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
                    tickvals=np.linspace(0, df_historico_mes["Venta"].max(), 5).astype(
                        int
                    ),
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

            st.plotly_chart(
                fig_hm,
                use_container_width=True,
                key=f"graf_tendencia_mensual_{categoria}",
            )

    def graficar_tendencia_gestion_diaria(une, categoria, cat_seleccion):
        # historico por mes
        df_historico_diario = u.consultar_bd(
            f"""
            SELECT
                CAST(strftime('%d', fecha_accion) AS INTEGER) AS num_dia,
                strftime('%w', fecha_accion) AS num_dia_semana,
                count(DISTINCT id_une) as Clientes,
                count(id_une) as Toques,
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
                DATE(fecha_accion) > '{date(2025,u.mes,1)}' and
                {categoria} = '{cat_seleccion}'
            GROUP by 
                DATE(fecha_accion)
            order by 
                DATE(fecha_accion) ASC
        """
        )
        if df_historico_diario.empty:
            st.warning(f"No se encontraron datos para este {categoria}.")
        else:
            df_historico_diario["dia_semana"] = df_historico_diario[
                "num_dia_semana"
            ].map(u.mapa_dias)
            df_historico_diario["num_nom"] = (
                df_historico_diario["num_dia"].astype(str)
                + " "
                + df_historico_diario["dia_semana"]
            )

            df_mes = u.generar_df_dia_mes(2025, u.mes)
            df_historico_diario = df_mes[["num_nom"]].merge(
                df_historico_diario[["num_nom", "Clientes", "Toques", "Venta"]],
                how="left",
                on="num_nom",
            )
            df_historico_diario.fillna(0)

            # Crear figura combinada
            fig_hm = go.Figure()

            # --- Barras (ventas) - se agregan primero para que queden atrás ---
            fig_hm.add_trace(
                go.Bar(
                    x=df_historico_diario["num_nom"],
                    y=df_historico_diario["Venta"],
                    name="Ventas",
                    marker_color="#FFD54F",
                    yaxis="y2",  # usa el segundo eje Y
                    opacity=0.5,  # leve transparencia para no tapar las líneas
                )
            )

            # --- Líneas (clientes y toques) - se agregan después para que estén al frente ---
            fig_hm.add_trace(
                go.Scatter(
                    x=df_historico_diario["num_nom"],
                    y=df_historico_diario["Clientes"],
                    name="Clientes",
                    mode="lines+markers",
                    line=dict(color="#42A5F5", width=2),
                )
            )
            fig_hm.add_trace(
                go.Scatter(
                    x=df_historico_diario["num_nom"],
                    y=df_historico_diario["Toques"],
                    name="Toques",
                    mode="lines+markers",
                    line=dict(color="#66BB6A", width=2),
                )
            )

            # --- Configurar diseño ---
            fig_hm.update_layout(
                title=dict(
                    text="Tendencia Diaria: Actividad (Clientes y Toques) vs Resultados (Ventas)",
                    x=0.5,
                    xanchor="center",
                ),
                xaxis=dict(title="Dia"),
                yaxis=dict(
                    tickvals=np.linspace(
                        0, df_historico_diario["Toques"].max(), 5
                    ).astype(int),
                    title="Clientes / Toques",
                    rangemode="tozero",
                ),
                yaxis2=dict(
                    tickvals=np.linspace(
                        0, df_historico_diario["Venta"].max(), 5
                    ).astype(int),
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

            st.plotly_chart(
                fig_hm,
                use_container_width=True,
                key=f"graf_tendencia_diario_{categoria}",
            )

    def graficar_cartera(une, categoria, cat_seleccion):
        st.subheader("Leads en Cartera")
        tab1, tab2 = st.tabs(["Tabla", "Grafico"])
        with tab1:
            query_cartera = f"""
                                with ult_toque as (
                                    select 
                                        *,
                                        row_number() over(
                                            partition by id_une
                                            order by fecha_accion desc
                                        ) as rn
                                    from df_toque
                                    where
                                        une = '{une}'
                                )
                                
                                SELECT
                                    tipo_contacto,
                                    respuesta_contacto,
                                    count(id_une) as conteo_leads
                                from ult_toque
                                where 
                                    rn = 1 and
                                    DATE(fecha_accion) >= '{date(2025,u.mes,1)}' and
                                    {categoria} = '{cat_seleccion}'
                                group by  
                                    tipo_contacto, 
                                    respuesta_contacto
                                order by 
                                    tipo_contacto
                                """
            # st.code(query_cartera, "sql")
            df_programa_cartera = u.consultar_bd(query_cartera)
            if df_programa_cartera.empty:
                st.warning(f"No se encontraron datos para este {categoria}.")
            else:
                total_leads_cartera = df_programa_cartera["conteo_leads"].sum()
                df_programa_cartera["Distribucion"] = (
                    (df_programa_cartera["conteo_leads"] / total_leads_cartera) * 100
                ).round(2)

                colores = df_programa_cartera["tipo_contacto"].map(
                    colores_tipo_contacto
                )
                df_mostrar = df_programa_cartera.drop(columns=["tipo_contacto"])
                # Aplicar los colores a la columna respuesta_ult_contacto
                styler = df_mostrar.style.apply(
                    lambda _: [f"background-color: {c}" for c in colores],
                    subset=["respuesta_contacto"],
                )
                alto = len(df_mostrar) * 43
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
                        text="Distribucion por tipo de contacto",
                        x=0.5,
                        xanchor="center",
                    )
                )

                st.plotly_chart(fig, use_container_width=True)

    with st.sidebar:
        une_seleccion = u.une(pagina="rs")

    tab_asesor, tab_programa = st.tabs(["Asesor", "Programa"])

    # **********************************************************
    with tab_programa:
        graficar_ranking(une_seleccion, "programa")
        programa = u.unico_programa(une_seleccion, "df_lead", "rs")
        # historico de leads getioado y ventas
        col1, col_, col2 = st.columns([0.7, 0.02, 0.28])

        # HISTORICO
        with col1:
            col_1a, col_1b = st.columns([0.7, 0.3])
            with col_1a:
                st.subheader("Leads Gestionados Historico")
            with col_1b:
                opcion_fecha = st.radio(
                    "",
                    ["Este Mes", "Todo el Año"],
                    key="radio_modo_programa",
                    horizontal=True,
                )

            graficar_metricas(une_seleccion, "programa", programa, opcion_fecha)
            if opcion_fecha == "Este Mes":
                graficar_tendencia_gestion_diaria(une_seleccion, "programa", programa)
            else:
                graficar_tendencia_gestion_anual(une_seleccion, "programa", programa)

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
            col_1a, col_1b = st.columns([0.7, 0.3])
            with col_1a:
                st.subheader("Leads Gestionados Historico")
            with col_1b:
                opcion_fecha = st.radio(
                    "",
                    ["Este Mes", "Todo el Año"],
                    key="radio_modo_asesor",
                    horizontal=True,
                )

            graficar_metricas(une_seleccion, "asesor", asesor, opcion_fecha)
            if opcion_fecha == "Este Mes":
                graficar_tendencia_gestion_diaria(une_seleccion, "asesor", asesor)
            else:
                graficar_tendencia_gestion_anual(une_seleccion, "asesor", asesor)

        # EN CARTERA
        with col2:
            graficar_cartera(une_seleccion, "asesor", asesor)

        # ************************************************    seguimiento cursos especificos
        st.divider()
        programas_seg = st.multiselect(
            "Seleccionar programa",
            u.get_items("SELECT DISTINCT programa FROM df_toque"),
            key="key_programas_seg",
        )

        def graficar_tabla(programas, asesor, condicion):
            if condicion == "mes actual":
                condicion_fecha = ">= '2025-11-01'"
            else:
                condicion_fecha = "< '2025-11-01'"

            query = f"""SELECT
                    asesor,
                    programa,
                    COUNT(DISTINCT id_une) AS leads_gestionados,
                    SUM(
                    CASE
                    when tipo_accion = 'Venta'
                    then 1 else 0
                    END
                    )  as venta

                    FROM df_toque
                    WHERE
                    asesor = '{asesor}' and
                    programa in ({u.items_comas(programas)}) and
                    DATE(fecha_accion) {condicion_fecha}
                    GROUP BY asesor, programa
                    """
            # with st.expander("Query"):
            #    st.code(query, language="sql")

            df_seg = u.consultar_bd(query)

            if df_seg.empty:
                st.warning("No se encontraron datos para este asesor.")
            else:
                # --- Cálculos adicionales ---
                total_leads = df_seg["leads_gestionados"].sum()
                df_seg["distribucion"] = (
                    df_seg["leads_gestionados"] / total_leads * 100
                ).round(2)
                df_seg["conversion"] = (
                    df_seg["venta"] / df_seg["leads_gestionados"] * 100
                ).round(2)

                # --- Tabla base ---
                # Mostrar tabla en Streamlit con formato visual
                alto_tb = len(df_seg) * 39
                st.dataframe(
                    df_seg[
                        [
                            "programa",
                            "leads_gestionados",
                            "distribucion",
                            "venta",
                            "conversion",
                        ]
                    ],
                    column_config={
                        "distribucion": st.column_config.ProgressColumn(
                            "Distribución",
                            format="%.2f%%",
                            min_value=0,
                            max_value=100,
                        ),
                        "conversion": st.column_config.ProgressColumn(
                            "Conversion",
                            format="%.2f%%",
                            min_value=0,
                            max_value=100,
                        ),
                    },
                    use_container_width=True,
                    hide_index=True,
                    height=alto_tb,
                )

                chart = (
                    alt.Chart(df_seg)
                    .mark_bar()
                    .encode(
                        x=alt.X(
                            "programa:N",
                            sort="-y",  # ✅ ordena de mayor a menor según el valor
                            axis=alt.Axis(
                                labelAngle=-60,
                                labelFontSize=10,
                                labelLimit=400,
                                labelOverlap=False,
                            ),  # ✅ inclina las etiquetas
                        ),
                        y=alt.Y("distribucion:Q", title="Distribución (%)"),
                        tooltip=[
                            alt.Tooltip("programa:N", title="Programa"),
                            alt.Tooltip("leads_gestionados:Q", title="Leads"),
                            alt.Tooltip("venta:Q", title="Ventas"),
                            alt.Tooltip("conversion:Q", title="Conversión (%)"),
                            alt.Tooltip("distribucion:Q", title="Distribución (%)"),
                        ],
                    )
                    .properties(
                        width="container",
                        height=600,
                        title="Distribución de Leads por Programa",
                    )
                )

                st.altair_chart(chart, use_container_width=True)

        col_actual, col_, col_anterior = st.columns([0.49, 0.02, 0.49])
        with col_actual:
            st.subheader("📊 Leads Gestionados en el actual mes")
            graficar_tabla(programas_seg, asesor, condicion="mes actual")

        with col_anterior:
            st.subheader("📊 Leads Gestionados en meses anteriores")
            graficar_tabla(programas_seg, asesor, condicion="meses anteriores")
