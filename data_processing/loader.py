"""Carga y limpieza del archivo Excel de órdenes."""

import pandas as pd
import numpy as np
import streamlit as st
from config import COLUMNAS_MONETARIAS


def load_excel(file) -> pd.DataFrame:
    """Lee el archivo Excel y retorna un DataFrame."""
    df = pd.read_excel(file, engine="openpyxl")
    return df


def _parse_date(series: pd.Series) -> pd.Series:
    """Parsea fechas en formatos DD-MM-YYYY y DD/MM/YYYY a datetime."""
    return pd.to_datetime(series, dayfirst=True, errors="coerce")


def _find_column(df: pd.DataFrame, *patterns: str) -> str | None:
    """Busca una columna que contenga alguno de los patrones (case insensitive)."""
    for col in df.columns:
        col_upper = col.upper()
        for p in patterns:
            if p.upper() in col_upper:
                return col
    return None


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia y estandariza el DataFrame de órdenes."""
    df = df.copy()

    # Parsear fechas por nombre exacto o búsqueda parcial
    date_columns = {
        "FECHA DE REPORTE": ["FECHA DE REPORTE"],
        "FECHA": ["FECHA"],
        "FECHA GUIA GENERADA": ["FECHA GUIA GENERADA"],
        "FECHA DE NOVEDAD": ["FECHA DE NOVEDAD"],
    }
    for target, patterns in date_columns.items():
        if target in df.columns:
            df[target] = _parse_date(df[target])

    # Parsear fechas con encoding problemático buscando por patrón
    for col in df.columns:
        col_upper = col.upper()
        if ("FECHA" in col_upper and "SOLUCI" in col_upper) or \
           ("FECHA" in col_upper and "LTIMO" in col_upper):
            df[col] = _parse_date(df[col])

    # Truncar decimales en columnas monetarias (floor)
    for col in COLUMNAS_MONETARIAS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            df[col] = np.floor(df[col]).astype(int)

    # Normalizar ESTATUS a mayúsculas y strip
    if "ESTATUS" in df.columns:
        df["ESTATUS"] = df["ESTATUS"].astype(str).str.strip().str.upper()

    # Normalizar CIUDAD DESTINO
    if "CIUDAD DESTINO" in df.columns:
        df["CIUDAD DESTINO"] = (
            df["CIUDAD DESTINO"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    # Asegurar CANTIDAD es numérica
    if "CANTIDAD" in df.columns:
        df["CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce").fillna(1).astype(int)

    # Flag: tiene guía generada
    df["TIENE_GUIA"] = df["FECHA GUIA GENERADA"].notna()

    return df


@st.cache_data(show_spinner="Cargando y procesando datos...")
def load_and_clean(file_content: bytes, file_name: str) -> pd.DataFrame:
    """Carga y limpia el Excel con cache basado en contenido del archivo."""
    import io
    df = load_excel(io.BytesIO(file_content))
    df = clean_data(df)
    return df
