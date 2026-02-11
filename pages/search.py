"""Página: Buscador Interactivo de Productos."""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from data_processing.analyzer import get_product_search_metrics, get_product_profitability


def render(df):
    """Renderiza la página de búsqueda de productos."""
    st.subheader("Buscador de Productos")

    # Lista de productos únicos
    all_products = sorted(df["PRODUCTO"].unique().tolist())

    # Buscador
    search = st.text_input(
        "Busca un producto",
        placeholder="Ej: hidrolavadora, linterna, audifono...",
    )

    # Filtrar productos que coincidan
    if search:
        matches = [p for p in all_products if search.upper() in p.upper()]
    else:
        matches = all_products

    if not matches:
        st.warning(f"No se encontraron productos con '{search}'")
        return

    # Selector múltiple
    selected = st.multiselect(
        f"Selecciona productos ({len(matches)} encontrados)",
        options=matches,
        default=matches[:1] if search and len(matches) <= 5 else [],
    )

    if not selected:
        st.info("Selecciona uno o más productos para ver sus métricas.")

        # Mostrar lista de coincidencias como referencia
        if search:
            st.caption(f"Productos que coinciden con '{search}':")
            for p in matches[:20]:
                st.write(f"- {p}")
            if len(matches) > 20:
                st.caption(f"... y {len(matches) - 20} más")
        return

    st.divider()

    # Calcular métricas
    metrics = get_product_search_metrics(df, selected)

    # Header
    if len(selected) == 1:
        st.subheader(f"Métricas: {selected[0]}")
    else:
        st.subheader(f"Métricas combinadas ({len(selected)} productos)")

    # KPIs row 1
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Órdenes", f"{metrics['total_ordenes']:,}")
    with col2:
        st.metric("Envíos", f"{metrics['envios']:,}")
    with col3:
        st.metric("Entregas", f"{metrics['entregas']:,}")
    with col4:
        st.metric("Devoluciones", f"{metrics['devoluciones']:,}")

    # KPIs row 2
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Cancelados", f"{metrics['cancelados']:,}")
    with col2:
        st.metric("Tasa Éxito", f"{metrics['tasa_exito']:.1%}")
    with col3:
        st.metric("Tasa Devolución", f"{metrics['tasa_devolucion']:.1%}")
    with col4:
        st.metric("Ticket Promedio", f"${metrics['ticket_promedio']:,}")

    st.divider()

    # KPIs económicos
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Utilidad Entregas", f"${metrics['ganancia_entregas']:,}")
    with col2:
        st.metric("Pérdida Devoluciones", f"${metrics['perdida_devoluciones']:,}")
    with col3:
        rent = metrics["rentabilidad"]
        st.metric(
            "Rentabilidad",
            f"${rent:,}",
            delta="Ganando" if rent >= 0 else "Perdiendo",
            delta_color="normal" if rent >= 0 else "inverse",
        )

    st.divider()

    # Gráfico de distribución
    fig = go.Figure(go.Pie(
        labels=["Entregas", "Devoluciones", "Cancelados", "En Proceso"],
        values=[
            metrics["entregas"],
            metrics["devoluciones"],
            metrics["cancelados"],
            metrics["envios"] - metrics["entregas"] - metrics["devoluciones"],
        ],
        marker=dict(colors=["#27ae60", "#e74c3c", "#95a5a6", "#3498db"]),
        hole=0.4,
        textinfo="label+percent+value",
    ))
    fig.update_layout(
        title="Distribución de Resultados",
        height=400,
        margin=dict(t=40, b=20, l=20, r=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Publicidad por producto
    st.divider()
    st.subheader("Publicidad por Producto")

    gasto_prod = st.number_input(
        "Gasto en publicidad para este(os) producto(s) ($)",
        min_value=0,
        value=0,
        step=50000,
        format="%d",
        key="gasto_pub_producto",
    )

    if gasto_prod > 0:
        rent_con_pub = metrics["rentabilidad"] - gasto_prod
        roas = metrics["ingreso_bruto"] / gasto_prod if gasto_prod > 0 else 0
        cpa = gasto_prod / metrics["entregas"] if metrics["entregas"] > 0 else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Rentabilidad con Publicidad",
                f"${rent_con_pub:,}",
                delta="Ganando" if rent_con_pub >= 0 else "Perdiendo",
                delta_color="normal" if rent_con_pub >= 0 else "inverse",
            )
        with col2:
            st.metric("ROAS", f"{roas:.1f}x")
        with col3:
            st.metric("Costo por Entrega", f"${cpa:,.0f}")

    # Detalle si hay múltiples productos
    if len(selected) > 1:
        st.divider()
        st.subheader("Desglose por Producto")

        profit = get_product_profitability(df)
        detail = profit[profit["PRODUCTO"].isin(selected)].reset_index(drop=True)
        st.dataframe(detail, use_container_width=True)
