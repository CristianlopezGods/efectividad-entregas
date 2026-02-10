"""Página: Resumen General."""

import streamlit as st
from data_processing.analyzer import get_general_metrics, get_status_distribution, get_temporal_evolution
from visualizations.kpis import render_kpi_cards, render_secondary_kpis
from visualizations.charts import funnel_chart, status_pie_chart, temporal_line_chart, carrier_pie


def render(df):
    """Renderiza la página de resumen general."""
    metrics = get_general_metrics(df)

    # KPIs principales
    st.subheader("KPIs Principales")
    render_kpi_cards(metrics)

    st.divider()

    # KPIs secundarios
    render_secondary_kpis(metrics)

    st.divider()

    # Funnel + Distribución de estatus
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(funnel_chart(metrics), use_container_width=True)
    with col2:
        st.plotly_chart(status_pie_chart(df), use_container_width=True)

    st.divider()

    # Evolución temporal
    evolution = get_temporal_evolution(df)
    if not evolution.empty:
        st.plotly_chart(temporal_line_chart(evolution), use_container_width=True)

    # Distribución por transportadora
    st.plotly_chart(carrier_pie(df), use_container_width=True)
