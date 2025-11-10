import sqlitecloud
import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
import calendar

hoy = date.today()
dia = hoy.day
mes = hoy.month
anio = hoy.year


def connection():
    return sqlitecloud.connect(
        f"sqlitecloud://cf1wheejhk.g4.sqlite.cloud:8860/dbBaseReporte.sqlite?apikey=O8ZthZ5mGnHzt1FZyfsnPrYLFPbOVeOzsVguyFR9efM"
    )


df_meses = pd.DataFrame(
    {
        "num_mes": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        "nom_mes": [
            "Ene",
            "Feb",
            "Mar",
            "Abr",
            "May",
            "Jun",
            "Jul",
            "Ago",
            "Sep",
            "Oct",
            "Nov",
            "Dic",
        ],
    }
)


def generar_df_dia_mes(anio, mes):
    inicio = date(anio, mes, 1)
    if mes == 12:
        fin = date(anio + 1, 1, 1)
    else:
        fin = date(anio, mes + 1, 1)

    dias = pd.date_range(start=inicio, end=fin - timedelta(days=1), freq="D")
    dias_semana = ["lun", "mar", "mie", "jue", "vie", "sab", "dom"]

    df = pd.DataFrame(
        {
            "fecha": dias,
            "num_dia": dias.day,
            "nom_dia": dias.weekday.map(lambda x: dias_semana[x]),
        }
    )
    df["num_nom"] = df["num_dia"].astype(str) + " " + df["nom_dia"]

    return df


mapa_dias = {
    "0": "dom",
    "1": "lun",
    "2": "mar",
    "3": "mie",
    "4": "jue",
    "5": "vie",
    "6": "sab",
}

mapeo = {
    "Indeciso": "positivo",
    "Interesado": "positivo",
    "Quiere Matricularse": "positivo",
    "Volver A Llamar": "positivo",
}

colores = {
    "verde_claro": "#C8E6C9",
    "rojo_claro": "#FFCDD2",
    "gris_claro": "#E0E0E0",
    "dorado": "#FFD700",
    "celeste_claro": "#D0EFF5",
    "celeste_oscuro": "#9AD3DE",
}


colores_tipo_contacto = {
    "positivo": "#C8E6C9",
    "negativo": "#FFCDD2",
    "otros": "#E0E0E0",
    "venta": "#ffd54f",
}


respuesta_propiedades = {
    # 🔴 NEGATIVOS IMPORTANTES
    "No Contesta": {
        "color": "#FF0000",  # rojo'
        "icono": "🔴",
        "tipo": "negativo",
        "color_tipo": colores["rojo_claro"],
        "abreviatura": "NC",
    },
    "Fuera De Servicio": {
        "color": "#FF8C00",  # naranja intenso
        "icono": "🔴",
        "tipo": "negativo",
        "color_tipo": colores["rojo_claro"],
        "abreviatura": "FS",
    },
    "Proxima Campaña": {
        "color": "#FF00FF",  # fucsia fuerte
        "icono": "🔴",
        "tipo": "negativo",
        "color_tipo": colores["rojo_claro"],
        "abreviatura": "PC",
    },
    "Prox Campaña": {
        "color": "#8A2BE2",  # violeta
        "icono": "🔴",
        "tipo": "negativo",
        "color_tipo": colores["rojo_claro"],
        "abreviatura": "PC",
    },
    "Proximas Campañas": {
        "color": "#00BFFF",  # azul brillante
        "icono": "🔴",
        "tipo": "negativo",
        "color_tipo": colores["rojo_claro"],
        "abreviatura": "PC",
    },
    "Sacar De La Base De Datos": {
        "color": "#006400",  # verde oscuro
        "icono": "🔴",
        "tipo": "negativo",
        "color_tipo": colores["rojo_claro"],
        "abreviatura": "SBD",
    },
    # 🟢 POSITIVOS IMPORTANTES
    "Interesado": {
        "color": "#32CD32",  # verde medio
        "icono": "🟢",
        "tipo": "positivo",
        "color_tipo": colores["verde_claro"],
        "abreviatura": "Int",
    },
    "Indeciso": {
        "color": "#00008B",  # azul intenso
        "icono": "🟢",
        "tipo": "positivo",
        "color_tipo": colores["verde_claro"],
        "abreviatura": "Ind",
    },
    "Volver A Llamar": {
        "color": "#FFD700",  # amarillo fuerte
        "icono": "🟢",
        "tipo": "positivo",
        "color_tipo": colores["verde_claro"],
        "abreviatura": "VLL",
    },
    "Quiere Matricularse": {
        "color": "#20B2AA",  # verde azulado
        "icono": "🟢",
        "tipo": "positivo",
        "color_tipo": colores["verde_claro"],
        "abreviatura": "QM",
    },
    # ⚪️ Otros
    "Solo Presencial": {
        "color": "#800080",  # púrpura
        "icono": "⚪️",
        "tipo": "otros",
        "color_tipo": colores["gris_claro"],
        "abreviatura": "SP",
    },
    "Proximo Inicio": {
        "color": "#808080",  # gris medio
        "icono": "⚪️",
        "tipo": "otros",
        "color_tipo": colores["gris_claro"],
        "abreviatura": "PI",
    },
    "Contacto Con Terceros": {
        "color": "#505050",  # gris oscuro
        "icono": "⚪️",
        "tipo": "otros",
        "color_tipo": colores["gris_claro"],
        "abreviatura": "CT",
    },
    "Recomendado": {
        "color": "#303030",  # gris fuerte
        "icono": "⚪️",
        "tipo": "otros",
        "color_tipo": colores["gris_claro"],
        "abreviatura": "Rec",
    },
    "Solo Mail": {
        "color": "#F5F5DC",  # beige apagado
        "icono": "⚪️",
        "tipo": "otros",
        "color_tipo": colores["gris_claro"],
        "abreviatura": "SM",
    },
    "De Certus": {
        "color": "#708090",  # gris azulado
        "icono": "⚪️",
        "tipo": "otros",
        "color_tipo": colores["gris_claro"],
        "abreviatura": "DC",
    },
    "Eventos Mkt": {
        "color": "#D3D3D3",  # gris claro
        "icono": "⚪️",
        "tipo": "otros",
        "color_tipo": colores["gris_claro"],
        "abreviatura": "EM",
    },
    "De Tls": {
        "color": "#B0C4DE",  # gris azulado claro
        "icono": "⚪️",
        "tipo": "otros",
        "color_tipo": colores["gris_claro"],
        "abreviatura": "DT",
    },
    "De Ucal": {
        "color": "#A9A9A9",  # gris plomo
        "icono": "⚪️",
        "tipo": "otros",
        "color_tipo": colores["gris_claro"],
        "abreviatura": "DU",
    },
    "Viene A Evento": {
        "color": "#F0F0F0",  # gris muy claro
        "icono": "⚪️",
        "tipo": "otros",
        "color_tipo": colores["gris_claro"],
        "abreviatura": "VE",
    },
    # VENTA
    "Se Inscribio": {
        "color": "#654321",  # marrón oscuro
        "icono": "🏆",
        "tipo": "venta",
        "color_tipo": colores["dorado"],
        "abreviatura": "SI",
    },
    "Inscrito": {
        "color": "#A0522D",  # marrón claro
        "icono": "🏆",
        "tipo": "venta",
        "color_tipo": colores["dorado"],
        "abreviatura": "Ins",
    },
}


# Función de estilo condicional para 'respuesta_ult_contacto'
def estilo_respuesta(row, tipo_contacto_aux):
    color_map = {
        "positivo": "#C8E6C9",
        "negativo": "#FFCDD2",
        "otros": "#E0E0E0",
        "venta": "#ffd54f",
    }
    tipo = tipo_contacto_aux[row.name]  # usamos la Serie auxiliar
    color = color_map.get(tipo, "#FFFFFF")
    return [
        (f"background-color: {color}" if col == "respuesta_ult_contacto" else "")
        for col in row.index
    ]


def items_comas(items):
    result = ", ".join(f"'{i}'" for i in items)
    return result


@st.cache_data
def get_items(query):
    with connection() as con:
        cursor = con.execute(query)
        return [row[0] for row in cursor.fetchall()]


# funcion para ejecutar wuery a sqlite
def ejecutar_query(query):
    with connection() as con:
        resultado = pd.read_sql_query(query, con)
    return resultado


@st.cache_data
def consultar_bd(query):
    with connection() as con:
        cursor = con.execute(query)
        datos = cursor.fetchall()
        # Si no hay filas, devolvemos un DataFrame vacío con los nombres de columna
        if datos:
            columnas = [desc[0] for desc in cursor.description]
            return pd.DataFrame(datos, columns=columnas)
        else:
            columnas = [desc[0] for desc in cursor.description]
            return pd.DataFrame(columns=columnas)


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


# FILTROS ******************************************


def une(pagina):
    # UNE
    une = st.selectbox(
        "Seleccionar UNE",
        ["CERTUS", "UCAL", "TLS"],
        index=0,
        key=f"key_une_{pagina}",
    )
    return une


def programa(une, nombre_df, pagina):
    programas = st.multiselect(
        "Seleccionar programa",
        get_items(f"SELECT DISTINCT programa FROM {nombre_df} WHERE une ='{une}'"),
        key=f"key_programa_{pagina}",
    )
    return programas


def unico_programa(une, nombre_df, pagina):

    programas = st.selectbox(
        "Seleccionar programa",
        get_items(f"SELECT DISTINCT programa FROM {nombre_df} WHERE une ='{une}'"),
        key=f"key_programa_{pagina}",
    )
    return programas


def respuesta_contacto(pagina, nom_columna):
    respuesta_contacto = st.multiselect(
        "Seleccionar respuesta",
        get_items(f"SELECT DISTINCT {nom_columna} FROM df_toque"),
        key=f"key_respuesta_contacto_{pagina}",
    )
    return respuesta_contacto


def asesor(une, nombre_df, pagina, nombre_fecha, fecha_inicio, fecha_fin):

    asesor = st.multiselect(
        "Seleccionar asesor",
        get_items(
            f"SELECT DISTINCT asesor FROM {nombre_df} WHERE une ='{une}' AND DATE({nombre_fecha}) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'"
        ),
        key=f"key_asesor_{pagina}",
    )
    return asesor


def unico_asesor(une, nombre_df, pagina, nombre_fecha, fecha_inicio, fecha_fin):

    asesor = st.selectbox(
        "Seleccionar asesor",
        get_items(
            f"SELECT DISTINCT asesor FROM {nombre_df} WHERE une ='{une}' AND DATE({nombre_fecha}) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'"
        ),
        key=f"key_asesor_{pagina}",
    )
    return asesor


def rango_fechas(titulo, fecha_min, fecha_max, pagina):
    rango_fechas = st.date_input(
        titulo,
        key=f"key_rango_fechas_{pagina}",
        min_value=fecha_min,
        max_value=fecha_max,
        help="Seleccione primero la fecha inicial y luego la fecha final",
    )
    return rango_fechas


def tipo_contacto(pagina):
    tipo_contacto = st.multiselect(
        "Tipo de contacto",
        ["positivo", "negativo", "otros"],
        key=f"key_tipo_contacto_{pagina}",
    )

    return tipo_contacto
