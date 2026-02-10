"""Página: Análisis de Clientes."""

import streamlit as st
from data_processing.analyzer import get_client_analysis


def render(df):
    """Renderiza la página de análisis de clientes."""
    analysis = get_client_analysis(df)
    bloquear = analysis["bloquear"]
    premiar = analysis["premiar"]

    st.subheader("Clientes a Bloquear")
    st.caption(f"Clientes con 3 o más devoluciones: **{len(bloquear)}**")

    if not bloquear.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Clientes a Bloquear", len(bloquear))
        with col2:
            st.metric("Total Devoluciones", int(bloquear["Devoluciones"].sum()))
        with col3:
            st.metric("Monto Perdido Total", f"${int(bloquear['Monto Perdido'].sum()):,}")

        st.dataframe(
            bloquear.reset_index(drop=True),
            use_container_width=True,
            height=400,
        )

        csv = bloquear.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Descargar CSV - Clientes a Bloquear",
            csv,
            "clientes_bloquear.csv",
            "text/csv",
        )
    else:
        st.info("No se encontraron clientes con 3+ devoluciones.")

    st.divider()

    st.subheader("Clientes a Premiar")
    st.caption("Top 20 clientes con más entregas exitosas")

    if not premiar.empty:
        st.dataframe(
            premiar.reset_index(drop=True),
            use_container_width=True,
            height=400,
        )

        csv = premiar.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Descargar CSV - Clientes a Premiar",
            csv,
            "clientes_premiar.csv",
            "text/csv",
        )
    else:
        st.info("No se encontraron clientes con entregas exitosas.")
