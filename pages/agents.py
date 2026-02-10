"""Página: Cancelaciones por Agente/Vendedor."""

import streamlit as st
import plotly.graph_objects as go
from data_processing.analyzer import get_agent_cancellations


def render(df):
    """Renderiza la página de agentes."""
    agents = get_agent_cancellations(df)

    st.subheader("Rendimiento por Agente / Vendedor")
    st.caption("Datos de la columna VENDEDOR del Excel")

    if agents.empty:
        st.info("No se encontraron datos de vendedores/agentes en el archivo.")
        return

    # KPIs
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Agentes Registrados", len(agents))
    with col2:
        st.metric("Total Pedidos Gestionados", int(agents["Total_Pedidos"].sum()))
    with col3:
        st.metric("Total Cancelados", int(agents["Cancelados"].sum()))

    st.divider()

    # Gráfico comparativo
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Entregados",
        x=agents["Agente"],
        y=agents["Entregados"],
        marker_color="#27ae60",
    ))
    fig.add_trace(go.Bar(
        name="Devoluciones",
        x=agents["Agente"],
        y=agents["Devoluciones"],
        marker_color="#e74c3c",
    ))
    fig.add_trace(go.Bar(
        name="Cancelados",
        x=agents["Agente"],
        y=agents["Cancelados"],
        marker_color="#95a5a6",
    ))
    fig.update_layout(
        title="Resultados por Agente",
        barmode="group",
        height=400,
        margin=dict(t=40, b=40, l=40, r=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Tabla detallada
    st.subheader("Detalle por Agente")
    st.dataframe(
        agents.reset_index(drop=True),
        use_container_width=True,
    )

    csv = agents.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Descargar CSV - Agentes",
        csv,
        "agentes_rendimiento.csv",
        "text/csv",
    )

    st.divider()

    # Nota sobre cobertura
    total_ordenes = len(df)
    con_agente = df["VENDEDOR"].notna().sum() if "VENDEDOR" in df.columns else 0
    st.info(
        f"**Nota:** Solo {con_agente:,} de {total_ordenes:,} órdenes "
        f"({con_agente/total_ordenes*100:.1f}%) tienen agente asignado. "
        f"Las demás fueron procesadas sin vendedor registrado."
    )
