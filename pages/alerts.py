"""Página: Alertas Operativas."""

import streamlit as st


def _fmt(val):
    return f"${val:,}"


def render(df):
    """Renderiza la página de alertas operativas."""
    from data_processing.analyzer import get_operational_alerts

    alerts = get_operational_alerts(df)

    st.subheader("Alertas Operativas")
    st.caption("Pedidos que requieren atención inmediata")

    flete = alerts["flete_sobrecosto"]
    guia = alerts["guia_demorada"]
    transito = alerts["transito_demorado"]

    n_flete = len(flete)
    n_guia = len(guia)
    n_transito = len(transito)

    # KPIs resumen
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Flete Sobrecosto (>$20K)", n_flete)
    with col2:
        st.metric("Guías Demoradas (>3d)", n_guia)
    with col3:
        st.metric("Tránsito Demorado (>6d)", n_transito)

    st.divider()

    # Flete sobrecosto
    with st.expander(f"Flete Sobrecosto — {n_flete} pedidos", expanded=n_flete > 0):
        if n_flete > 0:
            st.warning(f"{n_flete} pedidos con flete superior a $20,000")
            st.dataframe(flete.reset_index(drop=True), use_container_width=True)

            csv = flete.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Descargar CSV - Flete Sobrecosto",
                csv,
                "alerta_flete_sobrecosto.csv",
                "text/csv",
                key="dl_flete",
            )
        else:
            st.success("No hay pedidos con flete sobrecosto.")

    # Guías demoradas
    with st.expander(f"Guías Demoradas — {n_guia} pedidos", expanded=n_guia > 0):
        if n_guia > 0:
            st.warning(f"{n_guia} guías generadas hace más de 3 días sin despacho")
            st.dataframe(guia.reset_index(drop=True), use_container_width=True)

            csv = guia.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Descargar CSV - Guías Demoradas",
                csv,
                "alerta_guias_demoradas.csv",
                "text/csv",
                key="dl_guia",
            )
        else:
            st.success("No hay guías demoradas.")

    # Tránsito demorado
    with st.expander(f"Tránsito Demorado — {n_transito} pedidos", expanded=n_transito > 0):
        if n_transito > 0:
            st.warning(f"{n_transito} envíos con más de 6 días en tránsito")
            st.dataframe(transito.reset_index(drop=True), use_container_width=True)

            csv = transito.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Descargar CSV - Tránsito Demorado",
                csv,
                "alerta_transito_demorado.csv",
                "text/csv",
                key="dl_transito",
            )
        else:
            st.success("No hay envíos con tránsito demorado.")
