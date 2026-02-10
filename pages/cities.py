"""Página: Análisis por Ciudad."""

import streamlit as st
import plotly.graph_objects as go
from data_processing.analyzer import get_city_analysis, get_city_profitability
from visualizations.charts import top_cities_bar, top_cities_total_bar


def render(df):
    """Renderiza la página de análisis por ciudad."""
    analysis = get_city_analysis(df)

    tab_rate, tab_total, tab_profit = st.tabs([
        "Por Tasa %", "Por Cantidad Total", "Rentabilidad"
    ])

    with tab_rate:
        st.subheader("Ciudades por Tasa de Devolución")
        st.caption("Solo ciudades con 10+ envíos")

        by_rate = analysis["por_tasa"]
        if not by_rate.empty:
            st.plotly_chart(top_cities_bar(by_rate), use_container_width=True)
            st.divider()
            st.dataframe(by_rate.reset_index(drop=True), use_container_width=True, height=500)

            csv = by_rate.to_csv(index=False).encode("utf-8")
            st.download_button("Descargar CSV - Ciudades por Tasa", csv,
                               "ciudades_por_tasa.csv", "text/csv")
        else:
            st.info("No hay suficientes datos por ciudad.")

    with tab_total:
        st.subheader("Ciudades por Cantidad Total de Devoluciones")

        by_total = analysis["por_total"]
        if not by_total.empty:
            st.plotly_chart(top_cities_total_bar(by_total), use_container_width=True)
            st.divider()
            st.dataframe(by_total.reset_index(drop=True), use_container_width=True, height=500)

            csv = by_total.to_csv(index=False).encode("utf-8")
            st.download_button("Descargar CSV - Ciudades por Total", csv,
                               "ciudades_por_total.csv", "text/csv")
        else:
            st.info("No hay datos de ciudades.")

    with tab_profit:
        _render_profitability(df)


def _render_profitability(df):
    """Sub-tab de rentabilidad por ciudad."""
    st.subheader("Ciudades No Rentables")
    st.caption("Ciudades donde se pierde más en devoluciones de lo que se gana en entregas")

    city_profit = get_city_profitability(df)

    min_envios = st.slider("Mínimo de envíos para mostrar", 1, 50, 5, key="min_env_city_rent")
    filtered = city_profit[city_profit["Envíos"] >= min_envios]

    no_rentables = filtered[filtered["Rentabilidad"] < 0]
    rentables = filtered[filtered["Rentabilidad"] >= 0]

    # KPIs
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ciudades Analizadas", len(filtered))
    with col2:
        st.metric("No Rentables", len(no_rentables))
    with col3:
        st.metric("Rentables", len(rentables))

    st.divider()

    # Top 15 peores ciudades
    worst = no_rentables.head(15).copy()
    if not worst.empty:
        worst_sorted = worst.sort_values("Rentabilidad", ascending=True)

        fig = go.Figure(go.Bar(
            x=worst_sorted["Rentabilidad"],
            y=worst_sorted["CIUDAD DESTINO"],
            orientation="h",
            marker_color="#e74c3c",
            text=worst_sorted["Rentabilidad"].apply(lambda x: f"${x:,}"),
            textposition="outside",
        ))
        fig.update_layout(
            title="Top 15 Ciudades No Rentables",
            xaxis_title="Rentabilidad ($)",
            height=max(400, len(worst_sorted) * 35),
            margin=dict(t=40, b=40, l=150, r=80),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Tabla completa: no rentables
    st.subheader("Ciudades No Rentables (detalle)")

    def highlight_loss(row):
        if row.get("Rentabilidad", 0) < 0:
            return ["background-color: #ffcccc"] * len(row)
        return [""] * len(row)

    if not no_rentables.empty:
        display = no_rentables.copy().reset_index(drop=True)
        for col in ["Ganancia", "Pérdida", "Rentabilidad"]:
            display[col] = display[col].apply(lambda x: f"${x:,}")
        st.dataframe(
            display.style.apply(highlight_loss, axis=1),
            use_container_width=True,
            height=500,
        )

        csv = no_rentables.to_csv(index=False).encode("utf-8")
        st.download_button("Descargar CSV - Ciudades No Rentables", csv,
                           "ciudades_no_rentables.csv", "text/csv")
    else:
        st.success("Todas las ciudades son rentables con el filtro actual.")

    st.divider()

    # Tabla: todas las ciudades
    st.subheader("Todas las Ciudades")
    st.dataframe(filtered.reset_index(drop=True), use_container_width=True, height=400)
