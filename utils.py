import sqlitecloud
import streamlit as st
from datetime import datetime, date
import pandas as pd
import calendar

hoy = date.today()


def connection():
    return sqlitecloud.connect(
        f"sqlitecloud://cvixcqxfnz.g3.sqlite.cloud:8860/dbBase.sqlite?apikey=x6aRQxTUSHqNkU524H8AsCmutq7jnr0dX1AorzKszuw"
    )


def respuesta_color():
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
    return colores


def items_comas(items):
    result = ", ".join(f"'{i}'" for i in items)
    return result


@st.cache_data
def get_items(query):
    with connection() as con:
        cursor = con.execute(query)
        return [row[0] for row in cursor.fetchall()]


def programa(une, nombre_df):
    programas = st.multiselect(
        "Seleccionar programa",
        get_items(f"SELECT DISTINCT programa FROM {nombre_df} WHERE une ='{une}'"),
        key="key_programa",
    )
    return programas


def respuesta_ult_contacto(une, nombre_df):
    respuesta_ult_contacto = st.multiselect(
        "Seleccionar respuesta",
        get_items(
            f"SELECT DISTINCT respuesta_ult_contacto FROM {nombre_df} WHERE une ='{une}'"
        ),
        key="key_respuesta_ult_contacto",
    )
    return respuesta_ult_contacto


def asesor(une, nombre_df):
    asesor = st.multiselect(
        "Seleccionar asesor",
        get_items(f"SELECT DISTINCT asesor FROM {nombre_df} WHERE une ='{une}'"),
        key="key_asesor",
    )
    return asesor


@st.cache_data
def consultar_bd(query):
    with connection() as con:
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


def rango_fechas(titulo, fecha_min, fecha_max, pagina):
    rango_fechas = st.date_input(
        titulo,
        key=f"rango_fechas_{pagina}",
        min_value=fecha_min,
        max_value=fecha_max,
        help="Seleccione primero la fecha inicial y luego la fecha final",
    )
    return rango_fechas


def une_seleccion():
    # UNE
    une_seleccion = st.selectbox(
        "Seleccionar UNE",
        ["TLS", "UCAL", "CERTUS"],
        index=0,
        key="key_une",
    )
    return une_seleccion


def respuesta_seleccion():
    # Respuesta
    respuesta_seleccion = st.multiselect(
        "Seleccionar Respuesta",
        get_items(
            "SELECT DISTINCT respuesta_ult_contacto FROM df_base_25 WHERE respuesta_ult_contacto IS NOT NULL"
        ),
        key="key_respuesta_ult_accion",
    )
    return respuesta_seleccion
