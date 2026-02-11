"""Página: Análisis Temporal - Demorados y Atascados."""

import streamlit as st
from visualizations.charts import delayed_ranges_bar, stuck_ranges_bar
from data_processing.analyzer import get_temporal_analysis


def render(df):
    """Renderiza la página de análisis temporal."""
    analysis = get_temporal_analysis(df)

    tab_dem, tab_atas = st.tabs(["Enviados Demorados", "Atascados en Pendiente"])

    with tab_dem:
        st.subheader("Envíos Demorados (>6 días en tránsito)")

        rangos = analysis["rangos_demorados"]
        detalle = analysis["detalle_demorados"]

        total_demorados = int(rangos["Cantidad"].sum()) if not rangos.empty else 0
        st.metric("Total Demorados", total_demorados)

        if not rangos.empty and total_demorados > 0:
            st.plotly_chart(delayed_ranges_bar(rangos), use_container_width=True)

            st.divider()

            # Alerta crítica
            criticos = rangos[rangos["Rango"] == "30+ días"]
            if not criticos.empty and criticos.iloc[0]["Cantidad"] > 0:
                st.error(
                    f"ALERTA: {criticos.iloc[0]['Cantidad']} envíos con más de 30 días en tránsito"
                )

            st.subheader("Detalle de Envíos Demorados")
            st.dataframe(
                detalle.reset_index(drop=True),
                use_container_width=True,
                height=400,
            )

            csv = detalle.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Descargar CSV - Demorados",
                csv,
                "envios_demorados.csv",
                "text/csv",
            )
        else:
            st.success("No hay envíos demorados.")

    with tab_atas:
        st.subheader("Pedidos Atascados en Pendiente (>3 días)")

        rangos = analysis["rangos_atascados"]
        detalle = analysis["detalle_atascados"]

        total_atascados = int(rangos["Cantidad"].sum()) if not rangos.empty else 0
        st.metric("Total Atascados", total_atascados)

        if not rangos.empty and total_atascados > 0:
            st.plotly_chart(stuck_ranges_bar(rangos), use_container_width=True)

            st.divider()

            # Alerta crítica
            criticos = rangos[rangos["Rango"] == "30+ días"]
            if not criticos.empty and criticos.iloc[0]["Cantidad"] > 0:
                st.error(
                    f"ALERTA: {criticos.iloc[0]['Cantidad']} pedidos con más de 30 días esperando"
                )

            st.subheader("Detalle de Pedidos Atascados")
            st.dataframe(
                detalle.reset_index(drop=True),
                use_container_width=True,
                height=400,
            )

            csv = detalle.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Descargar CSV - Atascados",
                csv,
                "pedidos_atascados.csv",
                "text/csv",
            )
        else:
            st.success("No hay pedidos atascados.")
