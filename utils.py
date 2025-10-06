import sqlitecloud
import streamlit as st
from datetime import datetime, date

hoy = date.today()


def connection(db):
    return sqlitecloud.connect(
        f"sqlitecloud://cvixcqxfnz.g3.sqlite.cloud:8860/{db}?apikey=x6aRQxTUSHqNkU524H8AsCmutq7jnr0dX1AorzKszuw"
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
