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
    city_profit = get_city_profitability(df)

    min_envios = st.slider("Mínimo de envíos para mostrar", 1, 50, 5, key="min_env_city_rent")
    filtered = city_profit[city_profit["Envíos"] >= min_envios]

    no_enviar = filtered[filtered["Veredicto"] == "NO ENVIAR"]
    precaucion = filtered[filtered["Veredicto"] == "PRECAUCIÓN"]
    ok = filtered[filtered["Veredicto"] == "OK"]

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ciudades Analizadas", len(filtered))
    with col2:
        st.metric("NO ENVIAR", len(no_enviar))
    with col3:
        st.metric("PRECAUCIÓN", len(precaucion))
    with col4:
        perdida_evitable = int(no_enviar["Pérdida"].sum()) if not no_enviar.empty else 0
        st.metric("Pérdida Evitable", f"${perdida_evitable:,}",
                  help="Flete perdido en devoluciones de ciudades NO ENVIAR")

    st.divider()

    # Sección principal: ciudades donde NO conviene enviar
    st.subheader("Ciudades Donde Conviene NO Enviar")
    st.caption(
        "Ciudades con rentabilidad negativa (5+ envíos): "
        "las devoluciones cuestan más de lo que generan las entregas"
    )

    if not no_enviar.empty:
        worst = no_enviar.head(20).copy()
        worst_sorted = worst.sort_values("Rent/Envío", ascending=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Ganancia Entregas",
            x=worst_sorted["CIUDAD DESTINO"],
            y=worst_sorted["Ganancia"],
            marker_color="#27ae60",
        ))
        fig.add_trace(go.Bar(
            name="Pérdida Devoluciones",
            x=worst_sorted["CIUDAD DESTINO"],
            y=-worst_sorted["Pérdida"],
            marker_color="#e74c3c",
        ))
        fig.update_layout(
            title="Ganancia vs Pérdida — Ciudades NO ENVIAR",
            barmode="group",
            yaxis_title="Valor ($)",
            height=450,
            margin=dict(t=40, b=80, l=40, r=20),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Tabla NO ENVIAR
        display = no_enviar.copy().reset_index(drop=True)
        st.dataframe(display, use_container_width=True, height=400)

        csv = no_enviar.to_csv(index=False).encode("utf-8")
        st.download_button("Descargar CSV - Ciudades NO ENVIAR", csv,
                           "ciudades_no_enviar.csv", "text/csv")
    else:
        st.success("No hay ciudades con rentabilidad negativa con el filtro actual.")

    st.divider()

    # Precaución
    if not precaucion.empty:
        st.subheader("Ciudades en PRECAUCIÓN")
        st.caption("Rentabilidad positiva pero >30% devolución — riesgo alto")
        st.dataframe(precaucion.reset_index(drop=True), use_container_width=True, height=300)

    st.divider()

    # Tabla completa
    st.subheader("Todas las Ciudades")
    st.dataframe(filtered.reset_index(drop=True), use_container_width=True, height=400)
