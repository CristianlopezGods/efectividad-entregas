"""Página: Análisis por Ciudad."""

import streamlit as st
from data_processing.analyzer import get_city_analysis
from visualizations.charts import top_cities_bar, top_cities_total_bar


def render(df):
    """Renderiza la página de análisis por ciudad."""
    analysis = get_city_analysis(df)

    tab_rate, tab_total = st.tabs(["Por Tasa %", "Por Cantidad Total"])

    with tab_rate:
        st.subheader("Ciudades por Tasa de Devolución")
        st.caption("Solo ciudades con 10+ envíos")

        by_rate = analysis["por_tasa"]
        if not by_rate.empty:
            st.plotly_chart(top_cities_bar(by_rate), use_container_width=True)

            st.divider()

            st.dataframe(
                by_rate.reset_index(drop=True),
                use_container_width=True,
                height=500,
            )

            csv = by_rate.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Descargar CSV - Ciudades por Tasa",
                csv,
                "ciudades_por_tasa.csv",
                "text/csv",
            )
        else:
            st.info("No hay suficientes datos por ciudad.")

    with tab_total:
        st.subheader("Ciudades por Cantidad Total de Devoluciones")

        by_total = analysis["por_total"]
        if not by_total.empty:
            st.plotly_chart(top_cities_total_bar(by_total), use_container_width=True)

            st.divider()

            st.dataframe(
                by_total.reset_index(drop=True),
                use_container_width=True,
                height=500,
            )

            csv = by_total.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Descargar CSV - Ciudades por Total",
                csv,
                "ciudades_por_total.csv",
                "text/csv",
            )
        else:
            st.info("No hay datos de ciudades.")
