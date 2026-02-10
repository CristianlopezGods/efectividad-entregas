"""Página: Ganancias y Pérdidas Generales."""

import streamlit as st
import plotly.graph_objects as go
from data_processing.analyzer import get_pnl_general


def render(df):
    """Renderiza la página de P&L general."""
    pnl = get_pnl_general(df)

    st.subheader("Resumen de Ganancias y Pérdidas")

    # KPIs principales en grande
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ganancia por Entregas", f"${pnl['ganancia_entregas']:,}")
    with col2:
        st.metric("Pérdida por Devoluciones", f"${pnl['perdida_devoluciones']:,}")
    with col3:
        color = "normal" if pnl["rentabilidad_neta"] >= 0 else "inverse"
        st.metric(
            "Rentabilidad Neta",
            f"${pnl['rentabilidad_neta']:,}",
            delta=f"{'Ganando' if pnl['rentabilidad_neta'] >= 0 else 'Perdiendo'}",
            delta_color=color,
        )

    st.divider()

    # Detalle
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Ingresos")
        st.metric("Ingreso Bruto (ventas entregadas)", f"${pnl['ingreso_bruto']:,}")
        st.metric("Total Entregas Exitosas", f"{pnl['total_entregas']:,}")
        st.metric("Ganancia Neta Entregas", f"${pnl['ganancia_entregas']:,}")
        st.caption("Ganancia = Ingreso - Costo Producto - Flete - Comisión")

    with col2:
        st.subheader("Pérdidas")
        st.metric("Pérdida Fletes Devolución", f"${pnl['perdida_devoluciones']:,}")
        st.metric("Total Devoluciones", f"{pnl['total_devoluciones']:,}")
        st.metric("Costo Total Fletes (todos)", f"${pnl['costo_fletes_envio']:,}")

    st.divider()

    # Gráfico waterfall
    fig = go.Figure(go.Waterfall(
        name="P&L",
        orientation="v",
        measure=["absolute", "relative", "total"],
        x=["Ganancia Entregas", "Pérdida Devoluciones", "Rentabilidad Neta"],
        y=[pnl["ganancia_entregas"], -pnl["perdida_devoluciones"], pnl["rentabilidad_neta"]],
        text=[f"${pnl['ganancia_entregas']:,}", f"-${pnl['perdida_devoluciones']:,}", f"${pnl['rentabilidad_neta']:,}"],
        textposition="outside",
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "#27ae60"}},
        decreasing={"marker": {"color": "#e74c3c"}},
        totals={"marker": {"color": "#3498db"}},
    ))
    fig.update_layout(
        title="Flujo de Rentabilidad",
        height=450,
        margin=dict(t=40, b=40, l=40, r=40),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Sección de publicidad
    st.subheader("Análisis de Publicidad")
    st.caption("Ingresa tu gasto en publicidad para ver el impacto en rentabilidad")

    gasto_pub = st.number_input(
        "Gasto total en publicidad ($)",
        min_value=0,
        value=0,
        step=100000,
        format="%d",
        key="gasto_pub_general",
    )

    if gasto_pub > 0:
        rent_con_pub = pnl["rentabilidad_neta"] - gasto_pub
        roas = pnl["ingreso_bruto"] / gasto_pub if gasto_pub > 0 else 0
        cpa = gasto_pub / pnl["total_entregas"] if pnl["total_entregas"] > 0 else 0
        cpa_envio = gasto_pub / pnl["total_envios"] if pnl["total_envios"] > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            color = "normal" if rent_con_pub >= 0 else "inverse"
            st.metric(
                "Rentabilidad con Publicidad",
                f"${rent_con_pub:,}",
                delta=f"-${gasto_pub:,} publicidad",
                delta_color="inverse",
            )
        with col2:
            st.metric("ROAS", f"{roas:.1f}x",
                       help="Return On Ad Spend: por cada $1 en publicidad, cuánto ingresó en ventas")
        with col3:
            st.metric("Costo por Entrega", f"${cpa:,.0f}",
                       help="Cuánto costó en publicidad cada entrega exitosa")
        with col4:
            st.metric("Costo por Envío", f"${cpa_envio:,.0f}",
                       help="Cuánto costó en publicidad cada envío")

        # Waterfall con publicidad
        fig2 = go.Figure(go.Waterfall(
            name="P&L con Publicidad",
            orientation="v",
            measure=["absolute", "relative", "relative", "total"],
            x=["Ganancia Entregas", "Pérdida Devoluciones", "Publicidad", "Rentabilidad Final"],
            y=[pnl["ganancia_entregas"], -pnl["perdida_devoluciones"], -gasto_pub, rent_con_pub],
            text=[
                f"${pnl['ganancia_entregas']:,}",
                f"-${pnl['perdida_devoluciones']:,}",
                f"-${gasto_pub:,}",
                f"${rent_con_pub:,}",
            ],
            textposition="outside",
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            increasing={"marker": {"color": "#27ae60"}},
            decreasing={"marker": {"color": "#e74c3c"}},
            totals={"marker": {"color": "#3498db" if rent_con_pub >= 0 else "#e74c3c"}},
        ))
        fig2.update_layout(
            title="Flujo de Rentabilidad (con Publicidad)",
            height=450,
            margin=dict(t=40, b=40, l=40, r=40),
        )
        st.plotly_chart(fig2, use_container_width=True)
