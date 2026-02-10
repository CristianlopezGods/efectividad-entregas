"""Página: Análisis de Costos e Impacto Económico."""

import streamlit as st
from data_processing.analyzer import get_cost_analysis
from visualizations.charts import cost_loss_bar


def render(df):
    """Renderiza la página de costos."""
    costs = get_cost_analysis(df)

    st.subheader("Impacto Económico")

    # KPIs de costos
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Costo Total Fletes", f"${costs['costo_fletes']:,}")
        st.metric("Valor Productos Devueltos", f"${costs['valor_productos_devueltos']:,}")
    with col2:
        st.metric("Pérdida Flete Envío (dev)", f"${costs['perdida_flete_envio']:,}")
        st.metric("Inventario Atascado", f"${costs['valor_inventario_atascado']:,}")
    with col3:
        st.metric("Pérdida Flete Devolución", f"${costs['perdida_flete_devolucion']:,}")
        st.metric("Ingreso Perdido (ventas)", f"${costs['ingreso_perdido']:,}")

    st.divider()

    # Resumen
    st.error(
        f"**Pérdida Total por Devoluciones (fletes ida + vuelta):** "
        f"${costs['perdida_total_fletes']:,}"
    )

    st.divider()

    # Top 10 pérdida por ciudad
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Pérdida por Ciudad")
        top_cities = costs["top_cities"]
        if not top_cities.empty:
            st.plotly_chart(
                cost_loss_bar(top_cities, "Top 10 Pérdida por Ciudad", "CIUDAD DESTINO"),
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
                cost_loss_bar(top_products, "Top 10 Pérdida por Producto", "PRODUCTO"),
                use_container_width=True,
            )
            st.dataframe(
                top_products[["PRODUCTO", "Devoluciones", "Pérdida Total"]].reset_index(drop=True),
                use_container_width=True,
            )
