"""Página: Análisis por Producto (incluye buscador)."""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from data_processing.analyzer import (
    get_product_analysis,
    get_product_profitability,
    get_product_search_metrics,
)
from visualizations.charts import top_products_bar, profitability_bar


def render(df):
    """Renderiza la página de análisis de productos."""
    tab_dev, tab_rent, tab_buscar = st.tabs([
        "% Devolución", "Rentabilidad Real", "Buscador"
    ])

    with tab_dev:
        _render_devolucion(df)

    with tab_rent:
        _render_rentabilidad(df)

    with tab_buscar:
        _render_buscador(df)


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


def _render_buscador(df):
    """Buscador por palabra clave con métricas de rentabilidad."""
    st.subheader("Buscador de Productos")
    st.caption("Busca por palabra clave y selecciona para ver rentabilidad combinada")

    all_products = sorted(df["PRODUCTO"].unique().tolist())

    search = st.text_input(
        "Busca por palabra clave",
        placeholder="Ej: hidor, linterna, audifono, dron...",
        key="prod_search_keyword",
    )

    if search:
        matches = [p for p in all_products if search.upper() in p.upper()]
    else:
        matches = all_products

    if not matches:
        st.warning(f"No se encontraron productos con '{search}'")
        return

    selected = st.multiselect(
        f"Selecciona productos ({len(matches)} encontrados)",
        options=matches,
        default=matches if search and len(matches) <= 10 else [],
        key="prod_search_select",
    )

    if not selected:
        if search:
            st.info(f"Se encontraron **{len(matches)}** productos con '{search}'. Selecciona los que quieras analizar.")
            for p in matches[:20]:
                st.write(f"- {p}")
            if len(matches) > 20:
                st.caption(f"... y {len(matches) - 20} más")
        else:
            st.info("Escribe una palabra clave para buscar productos.")
        return

    st.divider()

    # Métricas combinadas
    metrics = get_product_search_metrics(df, selected)

    if len(selected) == 1:
        st.subheader(f"Métricas: {selected[0]}")
    else:
        st.subheader(f"Métricas combinadas ({len(selected)} productos)")

    # KPIs operativos
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Órdenes", f"{metrics['total_ordenes']:,}")
    with col2:
        st.metric("Envíos", f"{metrics['envios']:,}")
    with col3:
        st.metric("Entregas", f"{metrics['entregas']:,}")
    with col4:
        st.metric("Devoluciones", f"{metrics['devoluciones']:,}")

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

    # Gráfico pie
    fig = go.Figure(go.Pie(
        labels=["Entregas", "Devoluciones", "Cancelados", "En Proceso"],
        values=[
            metrics["entregas"],
            metrics["devoluciones"],
            metrics["cancelados"],
            max(0, metrics["envios"] - metrics["entregas"] - metrics["devoluciones"]),
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

    # Desglose individual si hay múltiples
    if len(selected) > 1:
        st.divider()
        st.subheader("Desglose por Producto")
        profit = get_product_profitability(df)
        detail = profit[profit["PRODUCTO"].isin(selected)].reset_index(drop=True)
        st.dataframe(detail, use_container_width=True)
