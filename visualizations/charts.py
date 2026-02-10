"""Gráficos Plotly para el dashboard."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from config import COLORES_CATEGORIAS


def funnel_chart(metrics: dict) -> go.Figure:
    """Funnel: Órdenes → Enviados → Entregados."""
    fig = go.Figure(go.Funnel(
        y=["Total Órdenes", "Envíos Reales", "Entregados"],
        x=[metrics["total_ordenes"], metrics["envios_reales"], metrics["entregados"]],
        textinfo="value+percent initial",
        marker=dict(color=["#3498db", "#2ecc71", "#27ae60"]),
    ))
    fig.update_layout(
        title="Funnel de Conversión",
        height=350,
        margin=dict(t=40, b=20, l=20, r=20),
    )
    return fig


def status_pie_chart(df: pd.DataFrame) -> go.Figure:
    """Distribución por categoría de estatus."""
    dist = df["CATEGORIA"].value_counts().reset_index()
    dist.columns = ["Categoría", "Cantidad"]

    colors = [COLORES_CATEGORIAS.get(cat, "#bdc3c7") for cat in dist["Categoría"]]

    fig = go.Figure(go.Pie(
        labels=dist["Categoría"],
        values=dist["Cantidad"],
        marker=dict(colors=colors),
        textinfo="label+percent",
        hole=0.4,
    ))
    fig.update_layout(
        title="Distribución de Estatus",
        height=400,
        margin=dict(t=40, b=20, l=20, r=20),
    )
    return fig


def temporal_line_chart(evolution: pd.DataFrame) -> go.Figure:
    """Evolución temporal de entregas vs devoluciones."""
    if evolution.empty:
        fig = go.Figure()
        fig.update_layout(title="Sin datos temporales")
        return fig

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=evolution["Fecha"], y=evolution["Envíos"],
        name="Envíos", line=dict(color="#3498db"),
    ))
    fig.add_trace(go.Scatter(
        x=evolution["Fecha"], y=evolution["Entregas"],
        name="Entregas", line=dict(color="#27ae60"),
    ))
    fig.add_trace(go.Scatter(
        x=evolution["Fecha"], y=evolution["Devoluciones"],
        name="Devoluciones", line=dict(color="#e74c3c"),
    ))

    fig.update_layout(
        title="Evolución Temporal: Envíos, Entregas y Devoluciones",
        xaxis_title="Fecha",
        yaxis_title="Cantidad",
        height=400,
        margin=dict(t=40, b=40, l=40, r=20),
        hovermode="x unified",
    )
    return fig


def top_products_bar(df: pd.DataFrame, n: int = 10) -> go.Figure:
    """Top N productos con mayor % devolución."""
    top = df.head(n).copy()
    top = top.sort_values("% Devolución", ascending=True)

    colors = ["#e74c3c" if v > 30 else "#f39c12" if v > 20 else "#27ae60"
              for v in top["% Devolución"]]

    fig = go.Figure(go.Bar(
        x=top["% Devolución"],
        y=top["PRODUCTO"],
        orientation="h",
        marker_color=colors,
        text=top["% Devolución"].apply(lambda x: f"{x}%"),
        textposition="outside",
    ))
    fig.update_layout(
        title=f"Top {n} Productos - Mayor % Devolución",
        xaxis_title="% Devolución",
        height=max(350, n * 35),
        margin=dict(t=40, b=40, l=200, r=40),
    )
    return fig


def top_cities_bar(df: pd.DataFrame, n: int = 10) -> go.Figure:
    """Top N ciudades con mayor % devolución."""
    top = df.head(n).copy()
    top = top.sort_values("% Devolución", ascending=True)

    colors = ["#e74c3c" if v > 30 else "#f39c12" if v > 20 else "#27ae60"
              for v in top["% Devolución"]]

    fig = go.Figure(go.Bar(
        x=top["% Devolución"],
        y=top["CIUDAD DESTINO"],
        orientation="h",
        marker_color=colors,
        text=top["% Devolución"].apply(lambda x: f"{x}%"),
        textposition="outside",
    ))
    fig.update_layout(
        title=f"Top {n} Ciudades - Mayor % Devolución",
        xaxis_title="% Devolución",
        height=max(350, n * 35),
        margin=dict(t=40, b=40, l=150, r=40),
    )
    return fig


def top_cities_total_bar(df: pd.DataFrame, n: int = 10) -> go.Figure:
    """Top N ciudades con más devoluciones totales."""
    top = df.head(n).copy()
    top = top.sort_values("Devoluciones", ascending=True)

    fig = go.Figure(go.Bar(
        x=top["Devoluciones"],
        y=top["CIUDAD DESTINO"],
        orientation="h",
        marker_color="#e74c3c",
        text=top["Devoluciones"],
        textposition="outside",
    ))
    fig.update_layout(
        title=f"Top {n} Ciudades - Más Devoluciones Totales",
        xaxis_title="Total Devoluciones",
        height=max(350, n * 35),
        margin=dict(t=40, b=40, l=150, r=40),
    )
    return fig


def delayed_ranges_bar(rangos: pd.DataFrame) -> go.Figure:
    """Demorados por rangos de días."""
    fig = go.Figure(go.Bar(
        x=rangos["Rango"],
        y=rangos["Cantidad"],
        marker_color=["#f39c12", "#e67e22", "#e74c3c", "#c0392b", "#8e44ad"],
        text=rangos["Cantidad"],
        textposition="outside",
    ))
    fig.update_layout(
        title="Envíos Demorados por Rango de Días",
        xaxis_title="Rango de Días",
        yaxis_title="Cantidad",
        height=350,
        margin=dict(t=40, b=40, l=40, r=20),
    )
    return fig


def stuck_ranges_bar(rangos: pd.DataFrame) -> go.Figure:
    """Atascados por rangos de días."""
    fig = go.Figure(go.Bar(
        x=rangos["Rango"],
        y=rangos["Cantidad"],
        marker_color=["#f39c12", "#e67e22", "#e74c3c", "#8e44ad"],
        text=rangos["Cantidad"],
        textposition="outside",
    ))
    fig.update_layout(
        title="Pedidos Atascados en Pendiente por Rango de Días",
        xaxis_title="Rango de Días",
        yaxis_title="Cantidad",
        height=350,
        margin=dict(t=40, b=40, l=40, r=20),
    )
    return fig


def novelty_bar(top_novedades: pd.DataFrame, n: int = 10) -> go.Figure:
    """Top novedades más frecuentes."""
    top = top_novedades.head(n).copy()
    top = top.sort_values("Cantidad", ascending=True)

    fig = go.Figure(go.Bar(
        x=top["Cantidad"],
        y=top["Novedad"],
        orientation="h",
        marker_color="#e74c3c",
        text=top["Cantidad"],
        textposition="outside",
    ))
    fig.update_layout(
        title=f"Top {n} Novedades Más Frecuentes",
        xaxis_title="Cantidad",
        height=max(350, n * 40),
        margin=dict(t=40, b=40, l=300, r=40),
    )
    return fig


def carrier_pie(df: pd.DataFrame) -> go.Figure:
    """Distribución por transportadora."""
    dist = df["TRANSPORTADORA"].value_counts().reset_index()
    dist.columns = ["Transportadora", "Cantidad"]

    fig = go.Figure(go.Pie(
        labels=dist["Transportadora"],
        values=dist["Cantidad"],
        textinfo="label+percent",
        hole=0.4,
    ))
    fig.update_layout(
        title="Distribución por Transportadora",
        height=400,
        margin=dict(t=40, b=20, l=20, r=20),
    )
    return fig


def cost_loss_bar(top_df: pd.DataFrame, title: str, y_col: str) -> go.Figure:
    """Barras horizontales para top pérdidas por ciudad o producto."""
    top = top_df.sort_values("Pérdida Total", ascending=True).copy()

    fig = go.Figure(go.Bar(
        x=top["Pérdida Total"],
        y=top[y_col],
        orientation="h",
        marker_color="#c0392b",
        text=top["Pérdida Total"].apply(lambda x: f"${x:,}"),
        textposition="outside",
    ))
    fig.update_layout(
        title=title,
        xaxis_title="Pérdida Total ($)",
        height=max(350, len(top) * 35),
        margin=dict(t=40, b=40, l=200, r=60),
    )
    return fig
