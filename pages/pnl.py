"""Página: Ganancias y Pérdidas Generales."""

import streamlit as st
import plotly.graph_objects as go
from data_processing.analyzer import get_pnl_general


def _fmt(val):
    """Formato moneda sin decimales."""
    return f"${val:,}"


def render(df):
    """Renderiza la página de P&L general."""
    pnl = get_pnl_general(df)

    st.subheader("Estado de Resultados (P&L)")

    # KPIs principales
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ventas Brutas (entregas)", _fmt(pnl["ventas_brutas"]))
    with col2:
        st.metric("Costos Totales", _fmt(pnl["costo_producto"] + pnl["fletes_total"] + pnl["comisiones"]))
    with col3:
        st.metric(
            "Venta Neta (sin publicidad)",
            _fmt(pnl["venta_neta"]),
            delta="Ganando" if pnl["venta_neta"] >= 0 else "Perdiendo",
            delta_color="normal" if pnl["venta_neta"] >= 0 else "inverse",
        )

    st.divider()

    # Desglose detallado
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Ingresos")
        st.metric("Ventas Brutas", _fmt(pnl["ventas_brutas"]))
        st.caption(f"{pnl['total_entregas']:,} entregas exitosas")

    with col2:
        st.subheader("Costos")
        st.metric("Costo Producto (solo entregas)", _fmt(pnl["costo_producto"]))
        st.metric("Flete Envío (solo entregas)", _fmt(pnl["flete_entregas"]))
        st.metric("Flete Devolución (solo devueltos)", _fmt(pnl["flete_devoluciones"]))
        st.metric("Comisiones", _fmt(pnl["comisiones"]))
        st.caption(f"{pnl['total_devoluciones']:,} devoluciones")

    st.divider()

    # Gráfico waterfall
    labels = ["Ventas Brutas", "Costo Producto", "Flete Envío", "Flete Devolución", "Comisiones", "Venta Neta"]
    values = [
        pnl["ventas_brutas"],
        -pnl["costo_producto"],
        -pnl["flete_entregas"],
        -pnl["flete_devoluciones"],
        -pnl["comisiones"],
        pnl["venta_neta"],
    ]
    measures = ["absolute", "relative", "relative", "relative", "relative", "total"]

    fig = go.Figure(go.Waterfall(
        name="P&L",
        orientation="v",
        measure=measures,
        x=labels,
        y=values,
        text=[_fmt(abs(v)) for v in values],
        textposition="outside",
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "#27ae60"}},
        decreasing={"marker": {"color": "#e74c3c"}},
        totals={"marker": {"color": "#3498db" if pnl["venta_neta"] >= 0 else "#e74c3c"}},
    ))
    fig.update_layout(
        title="Cascada: De Ventas Brutas a Venta Neta",
        height=500,
        margin=dict(t=40, b=40, l=40, r=40),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Sección de publicidad
    st.subheader("Análisis con Publicidad")

    gasto_pub = st.number_input(
        "Gasto total en publicidad ($)",
        min_value=0,
        value=0,
        step=100000,
        format="%d",
        key="gasto_pub_general",
    )

    if gasto_pub > 0:
        rent_final = pnl["venta_neta"] - gasto_pub
        roas = pnl["ventas_brutas"] / gasto_pub if gasto_pub > 0 else 0
        cpa = gasto_pub / pnl["total_entregas"] if pnl["total_entregas"] > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Rentabilidad Final",
                _fmt(rent_final),
                delta="Ganando" if rent_final >= 0 else "Perdiendo",
                delta_color="normal" if rent_final >= 0 else "inverse",
            )
        with col2:
            st.metric("ROAS", f"{roas:.1f}x",
                       help="Por cada $1 en publicidad, cuánto ingresó en ventas")
        with col3:
            st.metric("Costo por Entrega", _fmt(int(cpa)),
                       help="Cuánto costó en publicidad cada entrega exitosa")
        with col4:
            margen = rent_final / pnl["ventas_brutas"] * 100 if pnl["ventas_brutas"] > 0 else 0
            st.metric("Margen Neto", f"{margen:.1f}%")

        # Waterfall con publicidad
        labels2 = labels[:-1] + ["Publicidad", "Rentabilidad Final"]
        values2 = values[:-1] + [-gasto_pub, rent_final]
        measures2 = measures[:-1] + ["relative", "total"]

        fig2 = go.Figure(go.Waterfall(
            name="P&L + Publicidad",
            orientation="v",
            measure=measures2,
            x=labels2,
            y=values2,
            text=[_fmt(abs(v)) for v in values2],
            textposition="outside",
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            increasing={"marker": {"color": "#27ae60"}},
            decreasing={"marker": {"color": "#e74c3c"}},
            totals={"marker": {"color": "#3498db" if rent_final >= 0 else "#e74c3c"}},
        ))
        fig2.update_layout(
            title="Cascada con Publicidad",
            height=500,
            margin=dict(t=40, b=40, l=40, r=40),
        )
        st.plotly_chart(fig2, use_container_width=True)
