import streamlit as st
import pandas as pd
import sqlitecloud
from datetime import date, datetime
import calendar
import matplotlib.pyplot as plt
import seaborn as sns


st.set_page_config(
    page_title="Trafico de Respuesta",
    page_icon="📊",
    layout="wide",  # que la layaut ocupe toda la pantalla
    initial_sidebar_state="expanded",
)

# --- Conexión a SQLite Cloud ---
hoy = date.today()

if "key_rango_fechas" not in st.session_state.keys():
    st.session_state.key_rango_fechas = (date(2025, 1, 1), hoy)
if "key_une" not in st.session_state.keys():
    st.session_state.key_une = ["TLS"]

if "key_respuesta_ult_accion" not in st.session_state.keys():
    st.session_state.key_respuesta_ult_accion = ["Indeciso", "Interesado"]


def connection(db):
    return sqlitecloud.connect(
        f"sqlitecloud://cvixcqxfnz.g3.sqlite.cloud:8860/{db}?apikey=x6aRQxTUSHqNkU524H8AsCmutq7jnr0dX1AorzKszuw"
    )


@st.cache_data
def get_programas(query):
    with connection(db="dbBase.sqlite") as con:
        cursor = con.execute(query)
        return [row[0] for row in cursor.fetchall()]


def consultar_bd(query, db="dbBase.sqlite"):
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

    # Rango de fechas
    rango_fechas = st.date_input(
        "Rango de fecha",
        key="key_rango_fechas",
        min_value=date(2025, 1, 1),
        max_value=date(2025, 12, 31),
        help="Seleccione primero la fecha inicial y luego la fecha final",
    )

    # UNE
    une_seleccion = st.sidebar.multiselect(
        "Seleccionar UNE",
        ["TLS", "UCAL", "CERTUS"],
        key="key_une",
    )

    # Respuesta
    resp_seleccion = st.sidebar.multiselect(
        "Seleccionar Respuesta",
        get_programas("SELECT DISTINCT respuesta_ult_contacto FROM df_hsm"),
        key="key_respuesta_ult_accion",
    )


if validar_rango_fecha(rango_fechas):
    fecha_inicio, fecha_fin = rango_fechas

else:
    # fecha_inicio = date(2025, 1, 1)
    # fecha_fin = date(2025, 12, 31)
    st.warning(
        "⚠️ El rango de fechas seleccionado no es válido. Se omite el filtro de fecha."
    )


# --- Query con filtros ---
query = f"""
WITH cte_1 AS (
    SELECT
        une,
        strftime('%H', fecha_ult_accion) AS hora_accion,
        respuesta_ult_contacto,
        fecha_ult_accion
    FROM df_hsm
    WHERE
        date(fecha_ult_accion) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
        AND une IN ({", ".join(f"'{i}'" for i in une_seleccion)})
        AND respuesta_ult_contacto IN ({", ".join(f"'{i}'" for i in resp_seleccion)})
)  
SELECT
    hora_accion,
    respuesta_ult_contacto,
    COUNT(*) AS conteo
FROM cte_1
GROUP BY hora_accion, respuesta_ult_contacto"""

# query = """SELECT * FROM df_hsm
# WHERE date(fecha_ult_accion) BETWEEN '2025-01-01' AND '2025-10-03'
# LIMIT 10;"""


# st.markdown(f"""```sql{query}```""")


df = consultar_bd(query)

st.markdown("### Frecuencia de Respuestas por Hora (00-23H)")

df_pivot = df.pivot(
    index="respuesta_ult_contacto",
    columns="hora_accion",  # o 'respuesta' si está escrito correctamente
    values="conteo",
).fillna(
    0
)  # reemplaza valores faltantes con 0
total_respustas = len(resp_seleccion)

fig, ax = plt.subplots(figsize=(15, total_respustas * 0.5))
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


# --- Histograma ---
if not df.empty:
    pivot = df.pivot(
        index="hora_accion", columns="respuesta_ult_contacto", values="conteo"
    ).fillna(0)

    fig, ax = plt.subplots(figsize=(10, 4))
    pivot.plot(kind="bar", ax=ax)

    # Etiquetas de los ejes
    ax.set_xlabel("")
    # ax.set_ylabel("Frecuencia")

    # Leyenda más pequeña
    ax.legend(title="Respuesta", fontsize=8, title_fontsize=10)

    # Más valores en el eje Y
    max_y = pivot.values.max()
    ax.set_yticks(
        range(0, int(max_y) + 1, max(1, int(max_y / 10)))
    )  # 10 divisiones aprox

    # Etiquetas del eje X sin rotación
    plt.xticks(rotation=0)

    st.pyplot(fig)
else:
    st.warning("No hay datos para los filtros seleccionados.")
