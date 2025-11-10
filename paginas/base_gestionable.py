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
import sys
import os
import utils as u
from io import BytesIO
from collections import Counter

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def mostrar():

    respuesta_propiedades = u.respuesta_propiedades

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
        (datetime(u.anio, u.mes, 1) - timedelta(days=7)).date()
        if u.dia <= 7
        else date(u.anio, u.mes, 1)
    )

    if "key_une_bg" not in st.session_state.keys():
        st.session_state.key_une_bg = "UCAL"

    if "key_rango_fechas_bg_llegada" not in st.session_state.keys():
        st.session_state.key_rango_fechas_bg_llegada = (fecha_corte_filtro, u.hoy)

    if "key_rango_fechas_bg_toque" not in st.session_state.keys():
        st.session_state.key_rango_fechas_bg_toque = (
            (u.hoy - timedelta(days=7)),
            date(u.anio, u.mes, u.dia - 1),
        )

    # --- Sidebar: Filtros ---
    with st.sidebar:

        st.markdown(f"# ⚙️ Filtros")
        # une
        une_seleccion = u.une(pagina="bg")

        # rango de fecha de llegada
        rango_fechas_llegada = u.rango_fechas(
            titulo="Fecha de llegada",
            fecha_min=date(u.anio, u.mes - 1, 1),
            fecha_max=u.hoy,
            pagina="bg_llegada",
        )
        if u.validar_rango_fecha(rango_fechas_llegada):
            val_fecha_llegada = True
            fecha_inicio_llegada, fecha_fin_llegada = rango_fechas_llegada
            cond_fecha_llegada = f" and DATE(fecha_llegada) BETWEEN '{fecha_inicio_llegada}' AND '{fecha_fin_llegada}' "

        # rango de fecha de toques
        rango_fechas_toque = u.rango_fechas(
            titulo="Fecha de accion",
            fecha_min=date(u.anio, 1, 1),
            fecha_max=u.hoy,
            pagina="bg_toque",
        )
        if u.validar_rango_fecha(rango_fechas_toque):
            val_fecha_accion = True
            fecha_inicio_accion, fecha_fin_accion = rango_fechas_toque
            cond_fecha_accion = f"DATE(fecha_accion) BETWEEN '{fecha_inicio_accion}' AND '{fecha_fin_accion}' "

        # programa
        programa = u.programa(une=une_seleccion, nombre_df="df_lead", pagina="bg")
        if programa:
            cond_programa = f" and programa in ({u.items_comas(programa)})"

        # respuesta
        respuesta_contacto = u.respuesta_contacto(
            pagina="bg", nom_columna="respuesta_contacto"
        )
        if respuesta_contacto:
            cond_respuesta_contacto = (
                f" and respuesta_ult_contacto in ({u.items_comas(respuesta_contacto)})"
            )

        # tipo contacto
        tipo_contacto = u.tipo_contacto(pagina="bg")
        if tipo_contacto:
            cond_tipo_contacto = (
                f" and tipo_contacto in ({u.items_comas(tipo_contacto)})"
            )

        # rango de toques
        rango_toques = st.multiselect(
            "Rango de conteo de toques",
            # ["sin toque", "entre 1 y 2", "mas de 2"],
            ["entre 1 y 2", "mas de 2"],
        )
        if rango_toques:
            cond_rango_toques = f" and rango_toques in ({u.items_comas(rango_toques)})"

    # VALIDAR QUE SE SELECCIONARON FECHA CORRECTAMENTE:
    if not val_fecha_llegada or not val_fecha_accion:
        st.warning(
            "⚠️ El rango de fechas seleccionado no es válido. Termine se leccionar tanto la fecha de Inicio como la fecha de Fin"
        )

    else:
        with st.sidebar:
            # asesor
            asesor = u.asesor(
                une=une_seleccion,
                nombre_df="df_lead",
                pagina="bg",
                nombre_fecha="fecha_llegada",
                fecha_inicio=fecha_inicio_llegada,
                fecha_fin=fecha_fin_llegada,
            )
        if asesor:
            cond_asesor = f" and asesor in ({u.items_comas(asesor)})"

        query = f"""
        With 
        cte_1 as (
        select 
        id_une,
        une,
        asesor,
        programa,
        respuesta_ult_contacto,
        tipo_contacto,
        fecha_llegada,
        conteo_toques,
        rango_toques,
        fecha_pri_accion,
        fecha_ult_accion
        
        from df_lead     
        where 
        une = '{une_seleccion}' 
        {cond_fecha_llegada}
        {cond_programa if programa else ""}
        {cond_respuesta_contacto if respuesta_contacto else ""}
        {cond_tipo_contacto if tipo_contacto else ""}
        {cond_rango_toques if rango_toques else ""}
        {cond_asesor if asesor else ""}        
        )
        
        select 
        c.*,
        cl.id_cliente,
        t.asesor as asesor_t,
        t.tipo_accion as tipo_accion_t,
        t.fecha_accion as fecha_accion_t,
        t.respuesta_contacto as respuesta_contacto_t
        
        from cte_1 c
        left join df_cliente cl on cl.id_une = c.id_une
        left join df_toque t on t.id_une = c.id_une 
        where {cond_fecha_accion} 
        """

        df = u.consultar_bd(query)
        df = df.rename(
            columns={
                "fecha_pri_accion": "primera_accion",
                "fecha_ult_accion": "ultima_accion",
            }
        )
        df["fecha_accion_t"] = pd.to_datetime(df["fecha_accion_t"])
        df["fecha_accion_date"] = df["fecha_accion_t"].dt.date

        # llenar con cadena vacia los que tienen valores vacios en respuesta_ult_contacto
        df["respuesta_contacto_t"] = df["respuesta_contacto_t"].fillna("").astype(str)
        df_group = (
            df.groupby(
                [
                    "id_cliente",
                    "asesor",
                    "programa",
                    "respuesta_ult_contacto",
                    "tipo_contacto",
                    "fecha_llegada",
                    "primera_accion",
                    "ultima_accion",
                    "conteo_toques",
                    "fecha_accion_date",
                ]
            )
            .agg(
                respuesta_contacto_list=("respuesta_contacto_t", list),
                asesor_t_list=("asesor_t", list),
            )
            .reset_index()
        )

        # Unir listas → string (más rápido que apply)
        df_group["respuestas_str"] = [
            " ".join(map(str, x)) for x in df_group["respuesta_contacto_list"]
        ]
        df_group["asesores_str"] = [
            " ".join(map(str, x)) for x in df_group["asesor_t_list"]
        ]

        # Máscaras vectorizadas
        mask_inscrito = df_group["respuestas_str"].str.contains(
            "Inscrito|Se Inscribio", regex=True
        )
        mask_asesor_en_lista = [
            a in lst for a, lst in zip(df_group["asesor"], df_group["asesor_t_list"])
        ]
        mask_varias = df_group["respuesta_contacto_list"].str.len() > 0

        df_group["color_celda"] = np.select(
            [mask_inscrito, mask_asesor_en_lista, mask_varias],
            # ["dorado", "azul", "celeste"],
            [
                u.colores["dorado"],
                u.colores["celeste_oscuro"],
                u.colores["celeste_claro"],
            ],
            default="",
        )

        # texto_valor optimizado
        get_icono = respuesta_propiedades.get

        def construir_texto_valor(lista):
            conteos = Counter(lista)
            partes = [
                f"{get_icono(k, {}).get('icono', '⚪️')} {v} {get_icono(k, {}).get('abreviatura', '')}"
                for k, v in conteos.items()
            ]
            return f"({len(lista)}): " + ", ".join(partes)

        df_group["texto_valor"] = [
            construir_texto_valor(x) for x in df_group["respuesta_contacto_list"]
        ]

        df_pivot = df_group.pivot(
            index=[
                "id_cliente",
                "asesor",
                "programa",
                "respuesta_ult_contacto",
                "tipo_contacto",
                "fecha_llegada",
                "primera_accion",
                "ultima_accion",
                "conteo_toques",
            ],
            columns="fecha_accion_date",
            values="texto_valor",
        ).fillna("")

        df_color = df_group.pivot(
            index=[
                "id_cliente",
                "asesor",
                "programa",
                "respuesta_ult_contacto",
                "tipo_contacto",
                "fecha_llegada",
                "primera_accion",
                "ultima_accion",
                "conteo_toques",
            ],
            columns="fecha_accion_date",
            values="color_celda",
        ).fillna("")

        # Alinear columnas
        df_pivot = df_pivot.reindex(sorted(df_pivot.columns), axis=1)
        df_color = df_color.reindex(sorted(df_color.columns), axis=1)

        # Formatear nombres de columnas
        df_pivot.columns = (
            pd.to_datetime(df_pivot.columns).strftime("%b %d").str.lower()
        )
        df_color.columns = (
            pd.to_datetime(df_color.columns).strftime("%b %d").str.lower()
        )

        # lista con las columnas a aplicar estilo
        columnas_fecha = df_pivot.columns.tolist()

        # --- Antes de aplicar el Styler ---
        df_pivot = df_pivot.reset_index()
        df_color = df_color.reset_index()

        # Establecemos solo las columnas deseadas como índice visible
        df_pivot = df_pivot.set_index(["id_cliente", "asesor"])
        df_color = df_color.set_index(["id_cliente", "asesor"])

        # ordenar por fecha_llegada descendente
        df_pivot = df_pivot.sort_values(by="fecha_llegada", ascending=False)
        df_color = df_color.sort_values(by="fecha_llegada", ascending=False)
        df_group = df_group.sort_values(by="fecha_llegada", ascending=False)

        # Crear DataFrame de estilos vacío
        styles = pd.DataFrame("", index=df_pivot.index, columns=df_pivot.columns)
        # Vectorizado: aplicar color solo a columnas de fechas
        styles[columnas_fecha] = df_color[columnas_fecha].applymap(
            lambda c: f"background-color: {c}" if c else ""
        )

        # Colorear "conteo_toques" con un gradiente de color
        toque_vals = df_pivot["conteo_toques"].astype(float)

        max_conteo_toque = u.ejecutar_query(
            "select max(conteo_toques) from df_lead"
        ).iloc[0, 0]
        norm = (toque_vals) / (max_conteo_toque)
        colors = [
            cm.Reds(norm_val) for norm_val in norm
        ]  # puedes usar otros colormaps de matplotlib
        colors_hex = [
            f"background-color: rgba({int(r*255)},{int(g*255)},{int(b*255)},{a})"
            for r, g, b, a in colors
        ]

        styles["conteo_toques"] = colors_hex

        # Definir colores por tipo_contacto
        colores_tipo_contacto = {
            "positivo": "#C8E6C9",
            "negativo": "#FFCDD2",
            "otros": "#E0E0E0",
            "venta": "#ffd54f",
        }

        # Función para asignar color según tipo_contacto
        def color_por_tipo_contacto(tipo):
            return f"background-color: {colores_tipo_contacto.get(tipo, '')}"

        # Aplicar estilo vectorizado a la columna 'respuesta_ult_contacto'
        styles["respuesta_ult_contacto"] = df_pivot["tipo_contacto"].map(
            color_por_tipo_contacto
        )

        # 4️⃣ Crear Styler
        styler = df_pivot.drop(columns=["tipo_contacto"]).style.apply(
            lambda _: styles.drop(columns=["tipo_contacto"]), axis=None
        )

        # 🔹 Cuadritos de info
        # ------------------
        leads = len(df_pivot)
        total_toques = df_pivot["conteo_toques"].sum()
        positivos = (df_pivot["tipo_contacto"] == "positivo").sum()
        negativos = (df_pivot["tipo_contacto"] == "negativo").sum()
        otros = (df_pivot["tipo_contacto"] == "otros").sum()
        venta = (df_pivot["tipo_contacto"] == "venta").sum()

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("🧑 Leads en cartera", f"{leads}")
        col2.metric("✅ Contactos positivos", f"{positivos}")
        col3.metric("❌ Contactos negativos", f"{negativos}")
        col4.metric("🏆 Contactos venta", f"{venta}")
        col5.metric("⚪ Contactos otros", f"{otros}")
        col6.metric("📊 Total toques", f"{total_toques}")

        col_1, _, col2 = st.columns([0.8, 0.005, 0.195])
        # --- Mostrar tabla estilizada en Streamlit ---
        with col_1:
            st.dataframe(styler, use_container_width=True, height=600)

        with col2:
            id_cliente = st.text_input(
                "Ingrese el id_cliente para buscar:", key="input_id_cliente_bg"
            )
            if id_cliente:
                st.write("Toques del 2025")
                df_toque = df[df.id_cliente == id_cliente][
                    [
                        "asesor_t",
                        "tipo_accion_t",
                        "fecha_accion_t",
                        "respuesta_contacto_t",
                    ]
                ].sort_values("fecha_accion_t", ascending=False)
                df_toque = df_toque.rename(
                    columns={
                        "asesor_t": "Asesor",
                        "tipo_accion_t": "Acción",
                        "fecha_accion_t": "Fecha",
                        "respuesta_contacto_t": "Respuesta",
                    }
                )

                st.dataframe(df_toque, hide_index=True)

        # Función para convertir el DataFrame a Excel en memoria
        def to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Sheet1")
            processed_data = output.getvalue()
            return processed_data

        # Botón de descarga
        excel_data = to_excel(df_pivot.reset_index())
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
                f"entre **{fecha_inicio_llegada}** y **{fecha_fin_llegada}**."
            )
            tab1, tab2 = st.tabs(["Ranking de asesores", "Programas por tipo"])

            # --- TAB 1: Ranking de asesores ---
            with tab1:
                st.markdown("### Ranking de asesores por cantidad de leads")

                query_asesores = f"""
                    SELECT 
                    asesor, 
                    COUNT(id_une) AS total_leads
                    FROM df_lead
                    WHERE une = '{une_seleccion}'
                    AND fecha_llegada BETWEEN '{fecha_inicio_llegada}' AND '{fecha_fin_llegada}'
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
                fig_asesores.update_layout(
                    yaxis_title="Leads únicos", xaxis_title="Asesor"
                )
                st.plotly_chart(fig_asesores, use_container_width=True)

            # --- TAB 2: Programas por tipo de contacto ---
            with tab2:
                st.markdown(
                    "### Programas con mayor cantidad de leads por tipo de contacto"
                )

                tipos = ["positivo", "negativo", "otros", "venta"]
                for t in tipos:
                    st.markdown(f"#### Tipo de contacto: {t.capitalize()}")

                    query_programas = f"""
                        SELECT 
                        programa, 
                        COUNT(id_une) AS total_leads
                        FROM df_lead
                        WHERE une = '{une_seleccion}'
                        AND fecha_llegada BETWEEN '{fecha_inicio_llegada}' AND '{fecha_fin_llegada}'
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
