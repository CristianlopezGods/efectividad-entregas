"""Clasificación de estatus de órdenes: reglas deterministas + IA."""

import pandas as pd
import streamlit as st
from config import (
    ESTATUS_NUNCA_ENVIADO,
    ESTATUS_PENDIENTE_ATASCADO,
    ESTATUS_DEVOLUCION,
    ESTATUS_ENTREGADO,
    ESTATUS_EN_PROCESO,
)


def classify_status(estatus: str, tiene_guia: bool) -> str:
    """
    Clasifica un estatus individual usando reglas deterministas.

    Lógica:
    - Sin guía + estatus de cancelación/rechazo → NUNCA ENVIADO
    - Sin guía + PENDIENTE → PENDIENTE ATASCADO
    - Con guía + estatus de devolución → DEVOLUCION
    - Con guía + ENTREGADO → ENTREGADO
    - Con guía + otros estatus de tránsito → EN PROCESO
    - Sin guía + ENTREGADO → ERROR DE DATOS
    - Cualquier otro → DESCONOCIDO
    """
    estatus_upper = estatus.strip().upper()

    # Sin guía generada
    if not tiene_guia:
        if estatus_upper in ESTATUS_NUNCA_ENVIADO:
            return "NUNCA ENVIADO"
        if estatus_upper in ESTATUS_PENDIENTE_ATASCADO:
            return "PENDIENTE ATASCADO"
        if estatus_upper == "ENTREGADO":
            return "ERROR DE DATOS"
        # Sin guía pero con estatus de proceso (raro, pero puede pasar)
        if estatus_upper in ESTATUS_EN_PROCESO:
            return "NUNCA ENVIADO"
        if estatus_upper in ESTATUS_DEVOLUCION:
            return "NUNCA ENVIADO"
        return "DESCONOCIDO"

    # Con guía generada
    if estatus_upper in ESTATUS_DEVOLUCION:
        return "DEVOLUCION"
    if estatus_upper in ESTATUS_ENTREGADO:
        return "ENTREGADO"
    if estatus_upper in ESTATUS_EN_PROCESO:
        return "EN PROCESO"
    if estatus_upper in ESTATUS_NUNCA_ENVIADO:
        # Tiene guía pero estatus es cancelado/rechazado (cancelación post-envío)
        return "NUNCA ENVIADO"
    if estatus_upper in ESTATUS_PENDIENTE_ATASCADO:
        return "PENDIENTE ATASCADO"

    return "DESCONOCIDO"


def classify_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clasifica todos los estatus del DataFrame."""
    df = df.copy()
    df["CATEGORIA"] = df.apply(
        lambda row: classify_status(row["ESTATUS"], row["TIENE_GUIA"]),
        axis=1,
    )
    return df


def get_unknown_statuses(df: pd.DataFrame) -> list:
    """Retorna lista de estatus únicos clasificados como DESCONOCIDO."""
    unknown = df[df["CATEGORIA"] == "DESCONOCIDO"]["ESTATUS"].unique().tolist()
    return sorted(unknown)


def classify_with_ai(statuses: list, api_key: str) -> dict:
    """
    Llama a Claude API para clasificar estatus desconocidos.

    Retorna dict {estatus_original: categoria_sugerida}.
    """
    if not statuses or not api_key:
        return {}

    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)

        statuses_text = "\n".join(f"- {s}" for s in statuses)
        prompt = f"""Eres un experto en logística de e-commerce en Colombia (plataforma Dropi).
Clasifica cada uno de estos estatus de orden en UNA de estas categorías:
- NUNCA_ENVIADO: La orden nunca fue enviada (cancelada, rechazada, sin guía)
- DEVOLUCION: El paquete fue devuelto o está en proceso de devolución
- ENTREGADO: El paquete fue entregado exitosamente al cliente
- EN_PROCESO: El paquete está en tránsito o en algún punto del proceso de envío

Estatus a clasificar:
{statuses_text}

Responde SOLO con formato JSON como: {{"ESTATUS": "CATEGORIA", ...}}
Sin explicaciones adicionales."""

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        import json
        text = response.content[0].text.strip()
        # Extract JSON from response
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        result = json.loads(text)

        # Map AI categories back to our internal names
        category_map = {
            "NUNCA_ENVIADO": "NUNCA ENVIADO",
            "DEVOLUCION": "DEVOLUCION",
            "ENTREGADO": "ENTREGADO",
            "EN_PROCESO": "EN PROCESO",
        }

        return {
            k: category_map.get(v, v)
            for k, v in result.items()
        }

    except Exception as e:
        st.error(f"Error al clasificar con IA: {e}")
        return {}


def apply_ai_classifications(df: pd.DataFrame, ai_results: dict) -> pd.DataFrame:
    """Aplica las clasificaciones de IA al DataFrame."""
    if not ai_results:
        return df
    df = df.copy()
    for estatus, categoria in ai_results.items():
        mask = (df["ESTATUS"] == estatus) & (df["CATEGORIA"] == "DESCONOCIDO")
        df.loc[mask, "CATEGORIA"] = categoria
    return df
