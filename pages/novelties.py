"""Página: Análisis de Novedades."""

import streamlit as st
import plotly.graph_objects as go
from data_processing.analyzer import get_novelty_analysis
from visualizations.charts import novelty_bar


def render(df):
    """Renderiza la página de novedades."""
    analysis = get_novelty_analysis(df)

    st.subheader("Análisis de Novedades")

    if analysis["total_novedades"] == 0:
        st.info("No se encontraron novedades en los datos.")
        return

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Novedades", f"{analysis['total_novedades']:,}")
    with col2:
        st.metric("Resueltas", f"{analysis['resueltas']:,}")
    with col3:
        st.metric("No Resueltas", f"{analysis['no_resueltas']:,}")
    with col4:
        st.metric("Tasa Resolución", f"{analysis['tasa_resolucion']:.1%}")

    st.divider()

    # Pie chart resolución
    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure(go.Pie(
            labels=["Resueltas", "No Resueltas"],
            values=[analysis["resueltas"], analysis["no_resueltas"]],
            marker=dict(colors=["#27ae60", "#e74c3c"]),
            hole=0.4,
            textinfo="label+percent",
        ))
        fig.update_layout(
            title="Tasa de Resolución de Novedades",
            height=350,
            margin=dict(t=40, b=20, l=20, r=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Top 5 soluciones
        st.subheader("Top 5 Soluciones Aplicadas")
        top_sol = analysis["top_soluciones"]
        if not top_sol.empty:
            st.dataframe(top_sol.reset_index(drop=True), use_container_width=True)
        else:
            st.info("No se encontraron soluciones registradas.")

    st.divider()

    # Top novedades gráfico
    top_nov = analysis["top_novedades"]
    if not top_nov.empty:
        st.plotly_chart(novelty_bar(top_nov), use_container_width=True)

        st.subheader("Detalle de Novedades")
        st.dataframe(top_nov.reset_index(drop=True), use_container_width=True, height=400)

    st.divider()

    # Novedades resueltas vs no resueltas por tipo
    nov_tipo = analysis["novedades_por_tipo"]
    if not nov_tipo.empty:
        st.subheader("Resolución por Tipo de Novedad")
        st.dataframe(
            nov_tipo.reset_index(drop=True),
            use_container_width=True,
            height=400,
        )

        csv = nov_tipo.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Descargar CSV - Novedades por Tipo",
            csv,
            "novedades_por_tipo.csv",
            "text/csv",
        )
