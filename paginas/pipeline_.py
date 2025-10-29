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
    ### Reporte de Pipeline

    Este reporte proporciona una vista detallada de la actividad diaria de gestión comercial.  
    La tabla muestra dos métricas principales por día:

    - **Leads** 🎯: Número único de prospectos gestionados
    - **Toques** 📞: Total de interacciones realizadas

    #### Estructura de la tabla:

    - **Filas**: Cada asesor con sus respectivas respuestas de gestión
    - **Columnas**: Días del periodo seleccionado con las métricas Leads/Toques
    - **Colores**:
        - 🔵 Azul: Intensidad de leads gestionados
        - 🟢 Verde: Intensidad de toques realizados

    💡 **Tip**: Use los filtros laterales para segmentar por UNE, rango de fechas o asesores específicos.

    ✉️ Para solicitar modificaciones o nuevas funcionalidades, contactar a:

    **Melissa Rossel**  
    Gerente de Marketing Digital y Business Intelligence  
    📧 mrossel@ieduca.pe
    """,
            unsafe_allow_html=True,
        )

    if "key_une_p" not in st.session_state.keys():
        st.session_state.key_une_p = "UCAL"

    if "key_rango_fechas_t_toque" not in st.session_state.keys():
        st.session_state.key_rango_fechas_t_toque = (
            date(u.anio, u.mes, u.dia - 7),
            date(u.anio, u.mes, u.dia - 1),
        )

    condiciones = []
    # --- Sidebar: Filtros ---
    with st.sidebar:
        st.markdown(f"# ⚙️ Filtros")
        une_seleccion = u.une_seleccion(pagina="t")
        # rango de fechas
        rango_fechas_toque = u.rango_fechas(
            titulo="Fecha de accion",
            fecha_min=date(u.anio, 1, 1),
            fecha_max=u.hoy,
            pagina="t_toque",
        )
    if not u.validar_rango_fecha(rango_fechas_toque):
        st.warning(
            "⚠️ El rango de fechas seleccionado no es válido. Termine se leccionar tanto la fecha de Inicio como la fecha de Fin"
        )

    # FECHAS CORRECTAS ENTONCES SE RENDERIZA EL RESTO DE LA PAGINA**********************************************
    else:
        fecha_inicio_accion, fecha_fin_accion = rango_fechas_toque
        condiciones.append(
            f" and DATE(fecha_accion) BETWEEN '{fecha_inicio_accion}' AND '{fecha_fin_accion}' "
        )

        with st.sidebar:
            # asesor
            asesor = u.asesor(
                une=une_seleccion,
                nombre_df="df_toque",
                pagina="t",
                nombre_fecha="fecha_accion",
                fecha_inicio=fecha_inicio_accion,
                fecha_fin=fecha_fin_accion,
            )

        if asesor:
            condiciones.append(f" and t.asesor in ({u.items_comas(asesor)})")

        query = f"""
        SELECT 
    t.asesor, 
    equipo,
    respuesta_contacto,
    DATE(fecha_accion) as fecha,
    count(DISTINCT(id_une))  as leads,
    count(id_une) as toques
    
    from df_toque t
    left join df_asesor a on a.asesor = t.asesor
    where une = '{une_seleccion}' {' '.join(condiciones) if condiciones else ''}
    group by t.asesor,  equipo, respuesta_contacto, tipo_contacto, DATE(fecha_accion)
    """

        df = u.consultar_bd(query)

        # 1️⃣ Formatear la fecha (ejemplo: 01 nov)
        df["fecha_formato"] = (
            pd.to_datetime(df["fecha"]).dt.strftime("%d %b").str.lower()
        )

        # 2️⃣ Pivot: fechas arriba, métricas abajo
        tabla_pivot = df.pivot_table(
            index=["asesor", "respuesta_contacto"],
            columns="fecha_formato",
            values=["leads", "toques"],
        ).fillna(0)

        # 3️⃣ Intercambiar niveles para que quede: fecha → métrica
        tabla_pivot = tabla_pivot.swaplevel(0, 1, axis=1).sort_index(axis=1, level=0)

        # 4️⃣ Ordenar columnas cronológicamente (solo las fechas)
        tabla_pivot = tabla_pivot.reindex(
            sorted(
                tabla_pivot.columns.unique(level=0),
                key=lambda x: pd.to_datetime(x, format="%d %b"),
            ),
            axis=1,
            level=0,
        )

        # 6️⃣ (Opcional) ordenar asesores alfabéticamente
        tabla_pivot = tabla_pivot.sort_index()

        tabla_pivot = tabla_pivot.reset_index().set_index(
            ["asesor", "respuesta_contacto"]
        )

        def style_dataframe(df):
            # Convertir valores a enteros
            df = df.astype(int)

            # Aplicar colores para 'leads' (tonos azules)
            leads_cols = [col for col in df.columns if "leads" in col[1]]
            leads_subset = df[leads_cols]

            # Aplicar colores para 'toques' (tonos verdes)
            toques_cols = [col for col in df.columns if "toques" in col[1]]
            toques_subset = df[toques_cols]

            return (
                df.style.background_gradient(
                    cmap="Blues",
                    subset=leads_cols,
                    axis=None,
                    vmin=leads_subset.values.min(),
                    vmax=leads_subset.values.max(),
                )
                .background_gradient(
                    cmap="Greens",
                    subset=toques_cols,
                    axis=None,
                    vmin=toques_subset.values.min(),
                    vmax=toques_subset.values.max(),
                )
                .format("{:.0f}")
            )  # Formato para mostrar números enteros sin decimales

        # Función de estilo condicional para 'respuesta_ult_contacto'
        def estilo_respuesta(row, tipo_contacto_aux):
            color_map = {
                "positivo": "#C8E6C9",
                "negativo": "#FFCDD2",
                "otros": "#E0E0E0",
            }
            tipo = tipo_contacto_aux[row.name]  # usamos la Serie auxiliar
            color = color_map.get(tipo, "#FFFFFF")
            return [
                (f"background-color: {color}" if col == "respuesta_contacto" else "")
                for col in row.index
            ]

        # Aplicar el estilo y mostrar
        tabla_pivot = style_dataframe(tabla_pivot)
        st.dataframe(tabla_pivot, use_container_width=True, height=600)

        with st.expander("Ver Query"):
            st.code(query, language="sql")
