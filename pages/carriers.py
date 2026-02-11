"""Página: Análisis de Transportadoras."""

import streamlit as st
import plotly.graph_objects as go
from data_processing.analyzer import get_carrier_analysis


def _fmt(val):
    return f"${val:,}"


def render(df):
    """Renderiza la página de transportadoras."""
    carriers = get_carrier_analysis(df)

    st.subheader("Análisis por Transportadora")
    st.caption("Compara fletes, tasas de éxito y rentabilidad entre transportadoras")

    if carriers.empty:
        st.info("No hay datos suficientes de transportadoras.")
        return

    # KPIs por transportadora
    for _, row in carriers.iterrows():
        with st.expander(f"**{row['Transportadora']}** — {row['Envíos']:,} envíos", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Envíos", f"{row['Envíos']:,}")
                st.metric("Entregas", f"{row['Entregas']:,}")
            with col2:
                st.metric("% Éxito", f"{row['% Éxito']}%")
                st.metric("% Devolución", f"{row['% Devolución']}%")
            with col3:
                st.metric("Flete Envío Prom", _fmt(row["Flete Envío Prom"]))
                st.metric("Flete Dev Prom", _fmt(row["Flete Dev Prom"]))
            with col4:
                st.metric("Utilidad Entregas", _fmt(row["Ganancia"]))
                st.metric("Rentabilidad", _fmt(row["Rentabilidad"]),
                           delta="Positiva" if row["Rentabilidad"] >= 0 else "Negativa",
                           delta_color="normal" if row["Rentabilidad"] >= 0 else "inverse")

    st.divider()

    # Comparativo de fletes
    st.subheader("Comparativo de Fletes Promedio")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Flete Envío Prom",
        x=carriers["Transportadora"],
        y=carriers["Flete Envío Prom"],
        marker_color="#3498db",
        text=carriers["Flete Envío Prom"].apply(_fmt),
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="Flete Devolución Prom",
        x=carriers["Transportadora"],
        y=carriers["Flete Dev Prom"],
        marker_color="#e74c3c",
        text=carriers["Flete Dev Prom"].apply(_fmt),
        textposition="outside",
    ))
    fig.update_layout(
        barmode="group",
        title="Flete Promedio: Envío vs Devolución",
        yaxis_title="Valor ($)",
        height=400,
        margin=dict(t=40, b=40, l=40, r=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Comparativo de tasas
    st.subheader("Comparativo de Tasas")

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        name="% Éxito",
        x=carriers["Transportadora"],
        y=carriers["% Éxito"],
        marker_color="#27ae60",
        text=carriers["% Éxito"].apply(lambda x: f"{x}%"),
        textposition="outside",
    ))
    fig2.add_trace(go.Bar(
        name="% Devolución",
        x=carriers["Transportadora"],
        y=carriers["% Devolución"],
        marker_color="#e74c3c",
        text=carriers["% Devolución"].apply(lambda x: f"{x}%"),
        textposition="outside",
    ))
    fig2.update_layout(
        barmode="group",
        title="Tasa de Éxito vs Devolución",
        yaxis_title="%",
        height=400,
        margin=dict(t=40, b=40, l=40, r=20),
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # Tabla completa
    st.subheader("Tabla Resumen")

    display = carriers.copy()
    for col in ["Flete Envío Prom", "Flete Dev Prom", "Flete Envío Total", "Flete Dev Total", "Ganancia", "Rentabilidad"]:
        display[col] = display[col].apply(_fmt)

    st.dataframe(display.reset_index(drop=True), use_container_width=True)

    csv = carriers.to_csv(index=False).encode("utf-8")
    st.download_button("Descargar CSV - Transportadoras", csv,
                       "transportadoras_analisis.csv", "text/csv")
