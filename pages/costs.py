"""Página: Análisis de Costos e Impacto Económico."""

import streamlit as st
from data_processing.analyzer import get_cost_analysis
from visualizations.charts import cost_loss_bar


def _fmt(val):
    return f"${val:,}"


def render(df):
    """Renderiza la página de costos."""
    costs = get_cost_analysis(df)

    st.subheader("Impacto Económico")
    st.caption("Flete de envío se cobra en todos los pedidos enviados")

    # KPIs de costos
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Flete Envío (todos los envíos)", _fmt(costs["flete_envios"]))
    with col2:
        st.metric("Flete Perdido (envíos devueltos)", _fmt(costs["flete_devueltos"]))
    with col3:
        st.metric("Costo Producto (entregas)", _fmt(costs["costo_producto"]))

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Ingreso Perdido (ventas devueltas)", _fmt(costs["ingreso_perdido"]))
    with col2:
        st.metric("Valor Pedidos en Tránsito", _fmt(costs["valor_inventario"]))

    st.divider()

    # Top 10 pérdida por ciudad y producto
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Pérdida por Ciudad")
        top_cities = costs["top_cities"]
        if not top_cities.empty:
            st.plotly_chart(
                cost_loss_bar(top_cities, "Top 10 Pérdida Flete por Ciudad", "CIUDAD DESTINO"),
                use_container_width=True,
            )
            st.dataframe(
                top_cities[["CIUDAD DESTINO", "Devoluciones", "Pérdida Total"]].reset_index(drop=True),
                use_container_width=True,
            )

    with col2:
        st.subheader("Top 10 Pérdida por Producto")
        top_products = costs["top_products"]
        if not top_products.empty:
            st.plotly_chart(
                cost_loss_bar(top_products, "Top 10 Pérdida Flete por Producto", "PRODUCTO"),
                use_container_width=True,
            )
            st.dataframe(
                top_products[["PRODUCTO", "Devoluciones", "Pérdida Total"]].reset_index(drop=True),
                use_container_width=True,
            )
