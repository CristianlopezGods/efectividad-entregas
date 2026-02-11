"""Dashboard de Efectividad de Entregas - Veynori Store."""

import streamlit as st
import sys
import os

# Agregar directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_processing.loader import load_and_clean
from data_processing.classifier import classify_dataframe, apply_ai_classifications
from pages import overview, products, clients, cities, temporal, costs, novelties, ai_status, pnl, search, carriers, alerts

# --- Configuración de la página ---
st.set_page_config(
    page_title="Dashboard Efectividad de Entregas",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Sidebar ---
with st.sidebar:
    st.title("📦 Efectividad de Entregas")
    st.caption("Dashboard de análisis para Veynori Store")

    st.divider()

    uploaded_file = st.file_uploader(
        "Sube tu archivo de órdenes (.xlsx)",
        type=["xlsx"],
        help="Archivo Excel exportado de Dropi con todas las órdenes",
    )

    if uploaded_file:
        st.success(f"Archivo: {uploaded_file.name}")
        file_size = uploaded_file.size / (1024 * 1024)
        st.caption(f"Tamaño: {file_size:.1f} MB")

    st.divider()
    st.caption("Desarrollado para Veynori Store")

# --- Contenido principal ---
if not uploaded_file:
    st.title("📦 Dashboard de Efectividad de Entregas")
    st.markdown("""
    ### Bienvenido

    Este dashboard te permite analizar la efectividad de tus entregas e identificar:

    - **Productos no rentables** con alta tasa de devolución
    - **Clientes problemáticos** que generan muchas devoluciones
    - **Ciudades** con alta tasa de devolución
    - **Pedidos demorados** y atascados
    - **Impacto económico** de las devoluciones
    - **Novedades** y su tasa de resolución
    - **Alertas operativas** (flete sobrecosto, guías demoradas, tránsito lento)

    **Para comenzar**, sube tu archivo Excel de órdenes en la barra lateral.
    """)
    st.stop()

# Cargar y procesar datos
file_content = uploaded_file.getvalue()
df = load_and_clean(file_content, uploaded_file.name)

# Clasificar estatus
df = classify_dataframe(df)

# Aplicar clasificaciones IA si existen
if st.session_state.get("apply_ai") and st.session_state.get("ai_classifications"):
    df = apply_ai_classifications(df, st.session_state["ai_classifications"])
    st.session_state["apply_ai"] = False

# --- Tabs de navegación ---
tabs = st.tabs([
    "📊 Resumen",           # 0
    "💵 P&L General",       # 1
    "🔍 Buscador",          # 2
    "📦 Productos",         # 3
    "👤 Clientes",          # 4
    "🏙️ Ciudades",         # 5
    "🚚 Transportadoras",   # 6
    "⏱️ Tiempos",           # 7
    "💰 Costos",            # 8
    "🚨 Alertas",           # 9
    "⚠️ Novedades",         # 10
    "🤖 IA - Estatus",      # 11
])

with tabs[0]:
    overview.render(df)

with tabs[1]:
    pnl.render(df)

with tabs[2]:
    search.render(df)

with tabs[3]:
    products.render(df)

with tabs[4]:
    clients.render(df)

with tabs[5]:
    cities.render(df)

with tabs[6]:
    carriers.render(df)

with tabs[7]:
    temporal.render(df)

with tabs[8]:
    costs.render(df)

with tabs[9]:
    alerts.render(df)

with tabs[10]:
    novelties.render(df)

with tabs[11]:
    ai_status.render(df)
