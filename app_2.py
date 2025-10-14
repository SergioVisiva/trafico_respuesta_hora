import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

st.set_page_config(page_title="Ejemplo Profesional con AgGrid", layout="wide")

# --- Datos de prueba ---
data = {
    "id": [1, 2, 3, 4, 5],
    "nombre": ["Ana", "Luis", "Carla", "Pedro", "Sofía"],
    "ventas": [1200, 800, 1500, 400, 2300],
    "estado": ["Activo", "Inactivo", "Activo", "Pendiente", "Activo"],
    "fecha_ingreso": pd.to_datetime(
        ["2024-01-10", "2023-09-20", "2024-02-14", "2022-12-01", "2023-05-18"]
    ),
}
df = pd.DataFrame(data)

st.title("💼 Dashboard de Ventas - Ejemplo con AgGrid")

# --- Códigos JS para formato dinámico ---
cellstyle_estado = JsCode(
    """
function(params) {
    if (params.value == 'Activo') {
        return {'color': 'white', 'backgroundColor': '#2E7D32', 'fontWeight': 'bold'};
    } else if (params.value == 'Inactivo') {
        return {'color': 'white', 'backgroundColor': '#C62828', 'fontWeight': 'bold'};
    } else if (params.value == 'Pendiente') {
        return {'color': 'black', 'backgroundColor': '#FFF176', 'fontWeight': 'bold'};
    }
}
"""
)

cellRenderer_progress = JsCode(
    """
function(params) {
    const value = params.value;
    const percentage = Math.min(value / 25, 100);  // escala simple
    const color = value > 1500 ? '#2E7D32' : (value > 800 ? '#FFB300' : '#C62828');
    return `
        <div style="background-color: #eee; border-radius: 10px; padding: 2px;">
            <div style="width: ${percentage}%; background-color: ${color}; 
                height: 12px; border-radius: 10px;">
            </div>
        </div>
    `;
}
"""
)

# --- Configuración avanzada del grid ---
gb = GridOptionsBuilder.from_dataframe(df)

gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=5)
gb.configure_side_bar()  # permite filtros, columnas, etc.
gb.configure_selection("multiple", use_checkbox=True)
gb.configure_default_column(
    resizable=True, filter=True, sortable=True, wrapText=True, autoHeight=True
)

# --- Columnas con formato personalizado ---
gb.configure_column("estado", cellStyle=cellstyle_estado)
gb.configure_column(
    "ventas", cellRenderer=cellRenderer_progress, headerName="Ventas (con barra)"
)
gb.configure_column(
    "fecha_ingreso",
    type=["dateColumnFilter", "customDateTimeFormat"],
    custom_format_string="dd/MM/yyyy",
)

# --- Columna editable ---
gb.configure_column("nombre", editable=True)

# --- Construir gridOptions ---
gridOptions = gb.build()

# --- Mostrar tabla interactiva ---
grid_response = AgGrid(
    df,
    gridOptions=gridOptions,
    enable_enterprise_modules=True,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    fit_columns_on_grid_load=True,
    allow_unsafe_jscode=True,  # importante para usar JsCode
    theme="material",
    height=400,
)

# --- Respuesta a selección ---
selected_rows = grid_response["selected_rows"]

st.markdown("### 🧩 Fila seleccionada:")
st.dataframe(pd.DataFrame(selected_rows))

# --- Ejemplo adicional: exportar ---
if st.button("📤 Exportar selección a CSV"):
    if selected_rows:
        export_df = pd.DataFrame(selected_rows)
        export_df.to_csv("seleccion.csv", index=False)
        st.success("✅ Archivo exportado como 'seleccion.csv'")
    else:
        st.warning("Selecciona al menos una fila.")
