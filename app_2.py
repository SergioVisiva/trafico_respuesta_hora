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

from utils import connection, hoy


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

    colores = {
        # 🔴 NEGATIVOS IMPORTANTES
        "No Contesta": "#d32f2f",  # rojo fuerte
        "Fuera De Servicio": "#ff6f00",  # naranja intenso
        "Proxima Campaña": "#c2185b",  # fucsia fuerte
        "Prox Campaña": "#7b1fa2",  # violeta
        "Proximas Campañas": "#0288d1",  # azul brillante
        "Sacar De La Base De Datos": "#2e7d32",  # verde oscuro
        # 🟢 POSITIVOS IMPORTANTES
        "Interesado": "#388e3c",  # verde medio
        "Indeciso": "#1976d2",  # azul intenso
        "Volver A Llamar": "#fbc02d",  # amarillo fuerte
        "Quiere Matricularse": "#00897b",  # verde azulado
        "Se Inscribio": "#5d4037",  # marrón oscuro
        "Solo Presencial": "#512da8",  # púrpura
        # ⚪️ NO IMPORTANTES (colores apagados / neutros)
        "Proximo Inicio": "#bdbdbd",  # gris medio
        "Contacto Con Terceros": "#9e9e9e",  # gris oscuro
        "Recomendado": "#757575",  # gris fuerte
        "Solo Mail": "#a1887f",  # beige apagado
        "De Certus": "#90a4ae",  # gris azulado
        "Eventos Mkt": "#cfd8dc",  # gris claro
        "Inscrito": "#8d6e63",  # marrón claro
        "De Tls": "#b0bec5",  # gris azulado claro
        "De Ucal": "#78909c",  # gris plomo
        "Viene A Evento": "#e0e0e0",  # gris muy claro
    }
    df = consultar_bd(query)

    st.markdown("### Frecuencia de Respuestas por Hora (00-23H)")

    # MAPA
    df_pivot = df.pivot(
        index="respuesta_ult_contacto",
        columns="hora_accion",  # o 'respuesta' si está escrito correctamente
        values="conteo",
    ).fillna(
        0
    )  # reemplaza valores faltantes con 0

    fig, ax = plt.subplots(figsize=(15, len(respuesta_seleccion) * 0.5))
    sns.heatmap(
        df_pivot,
        annot=True,
        fmt="g",
        cmap="YlOrRd",
        ax=ax,
        annot_kws={"size": 8},
    )
    ax.set_xlabel("")
    ax.set_ylabel("")
    st.pyplot(fig)

    st.markdown(
        "<hr style='border:1px solid #ccc; margin:20px 0;'>", unsafe_allow_html=True
    )

    tab_lineas, tab_barras = st.tabs(["Lineas", "Barras"])

    with tab_barras:
        fig = px.bar(
            df,
            x="hora_accion",
            y="conteo",
            color="respuesta_ult_contacto",
            color_discrete_map=colores,
            barmode="group",
            text_auto=".0f",
            labels={
                "hora_accion": "Hora de acción",
                "conteo": "Cantidad de contactos",
                "respuesta_ult_contacto": "Respuesta",
            },
            title="Distribución de contactos por hora y tipo de respuesta",
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab_lineas:
        fig = px.line(
            df,
            x="hora_accion",
            y="conteo",
            color="respuesta_ult_contacto",
            color_discrete_map=colores,
            markers=True,
            hover_data=["respuesta_ult_contacto", "conteo"],
        )
        st.plotly_chart(fig, use_container_width=True)
