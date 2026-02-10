"""Página: Análisis por Producto."""

import streamlit as st
import pandas as pd
from data_processing.analyzer import get_product_analysis
from visualizations.charts import top_products_bar


def render(df):
    """Renderiza la página de análisis de productos."""
    products = get_product_analysis(df)

    st.subheader("Análisis de Productos")

    # Filtro mínimo de envíos
    min_envios = st.slider("Mínimo de envíos para mostrar", 1, 100, 5)
    filtered = products[products["Envíos"] >= min_envios]

    # Contadores
    total_productos = len(filtered)
    pausar = len(filtered[filtered["Acción"].str.contains("PAUSAR")])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Productos Analizados", total_productos)
    with col2:
        st.metric("Productos a PAUSAR (>30%)", pausar)
    with col3:
        st.metric("Productos OK", total_productos - pausar)

    st.divider()

    # Gráfico top 10
    if not filtered.empty:
        st.plotly_chart(top_products_bar(filtered), use_container_width=True)

    st.divider()

    # Tabla interactiva
    st.subheader("Detalle por Producto")

    # Highlight rows
    def highlight_action(row):
        if "PAUSAR" in str(row.get("Acción", "")):
            return ["background-color: #ffcccc"] * len(row)
        return [""] * len(row)

    display_df = filtered.reset_index(drop=True)
    st.dataframe(
        display_df.style.apply(highlight_action, axis=1),
        use_container_width=True,
        height=500,
    )

    # Exportar CSV
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Descargar CSV - Productos",
        csv,
        "productos_analisis.csv",
        "text/csv",
    )
