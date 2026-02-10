"""Página: Análisis por Producto."""

import streamlit as st
import pandas as pd
from data_processing.analyzer import get_product_analysis, get_product_profitability
from visualizations.charts import top_products_bar, profitability_bar


def render(df):
    """Renderiza la página de análisis de productos."""
    tab_dev, tab_rent = st.tabs(["% Devolución", "Rentabilidad Real"])

    with tab_dev:
        _render_devolucion(df)

    with tab_rent:
        _render_rentabilidad(df)


def _render_devolucion(df):
    products = get_product_analysis(df)

    st.subheader("Productos por Tasa de Devolución")

    min_envios = st.slider("Mínimo de envíos para mostrar", 1, 100, 5, key="min_env_dev")
    filtered = products[products["Envíos"] >= min_envios]

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

    if not filtered.empty:
        st.plotly_chart(top_products_bar(filtered), use_container_width=True)

    st.divider()

    st.subheader("Detalle por Producto")

    def highlight_action(row):
        if "PAUSAR" in str(row.get("Acción", "")):
            return ["background-color: #ffcccc"] * len(row)
        return [""] * len(row)

    st.dataframe(
        filtered.reset_index(drop=True).style.apply(highlight_action, axis=1),
        use_container_width=True,
        height=500,
    )

    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Descargar CSV - Productos Devolución",
        csv,
        "productos_devolucion.csv",
        "text/csv",
    )


def _render_rentabilidad(df):
    profit = get_product_profitability(df)

    st.subheader("Rentabilidad Real por Producto")
    st.caption(
        "Ganancia de entregas exitosas - Flete perdido en envíos devueltos"
    )

    min_envios = st.slider("Mínimo de envíos para mostrar", 1, 100, 5, key="min_env_rent")
    filtered = profit[profit["Envíos"] >= min_envios]

    # KPIs
    perdiendo = filtered[filtered["Rentabilidad Real"] < 0]
    ganando = filtered[filtered["Rentabilidad Real"] >= 0]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Productos Analizados", len(filtered))
    with col2:
        st.metric("Dando Pérdida", len(perdiendo))
    with col3:
        st.metric("Dando Ganancia", len(ganando))
    with col4:
        total_rent = int(filtered["Rentabilidad Real"].sum())
        st.metric("Rentabilidad Total", f"${total_rent:,}")

    st.divider()

    # Gráfico
    if not filtered.empty:
        st.plotly_chart(profitability_bar(filtered), use_container_width=True)

    st.divider()

    # Tabla
    st.subheader("Detalle de Rentabilidad")

    def highlight_profit(row):
        if row.get("Rentabilidad Real", 0) < 0:
            return ["background-color: #ffcccc"] * len(row)
        return [""] * len(row)

    # Formatear columnas monetarias
    display = filtered.copy().reset_index(drop=True)
    for col in ["Ganancia Entregas", "Pérdida Devoluciones", "Rentabilidad Real", "Rent/Envío"]:
        display[col] = display[col].apply(lambda x: f"${x:,}")

    st.dataframe(
        display.style.apply(highlight_profit, axis=1),
        use_container_width=True,
        height=500,
    )

    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Descargar CSV - Rentabilidad Productos",
        csv,
        "productos_rentabilidad.csv",
        "text/csv",
    )
