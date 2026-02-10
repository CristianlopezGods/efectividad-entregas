"""Cards de KPIs con st.metric()."""

import streamlit as st


def render_kpi_cards(metrics: dict):
    """Renderiza las cards de KPIs principales."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Órdenes", f"{metrics['total_ordenes']:,}")
        st.metric("Tasa Conversión", f"{metrics['tasa_conversion']:.1%}")
        st.metric("Flete Promedio", f"${metrics['flete_promedio']:,}")

    with col2:
        st.metric("Envíos Reales", f"{metrics['envios_reales']:,}")
        st.metric("Tasa Éxito", f"{metrics['tasa_exito']:.1%}")
        st.metric("Pérdida Total Fletes", f"${metrics['perdida_total']:,}")

    with col3:
        st.metric("Entregados", f"{metrics['entregados']:,}")
        st.metric(
            "Tasa Devolución",
            f"{metrics['tasa_devolucion']:.1%}",
        )
        st.metric("Devoluciones", f"{metrics['devoluciones']:,}")


def render_secondary_kpis(metrics: dict):
    """Renderiza KPIs secundarios: demorados y atascados."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Nunca Enviados", f"{metrics['nunca_enviados']:,}")
    with col2:
        st.metric("En Proceso", f"{metrics['en_proceso']:,}")
    with col3:
        st.metric(
            "Demorados (>7d)",
            f"{metrics['demorados']:,}",
        )
    with col4:
        st.metric(
            "Atascados (>3d)",
            f"{metrics['atascados']:,}",
        )
