"""Cálculos y métricas de negocio sobre el DataFrame clasificado.

REGLAS DE NEGOCIO (dropshipping):
- Flete de envío (T / PRECIO FLETE) se cobra en TODOS los pedidos enviados (entregados + devueltos + en proceso)
- Columna U (COSTO DEVOLUCION FLETE) se IGNORA — dato no confiable
- Si un pedido fue devuelto, la pérdida es el flete T que ya se pagó (envío perdido)
- NO se cobra flete en pedidos que nunca salieron (pendiente, rechazado, cancelado, guía anulada, indemnización)
- Costo de producto solo se paga cuando el pedido es ENTREGADO
- Venta neta = Ventas - Costo producto - Flete envío (todos) - Comisiones - Publicidad
"""

import pandas as pd
import numpy as np
from datetime import datetime
from config import (
    UMBRAL_DEVOLUCION_PAUSAR,
    UMBRAL_DEVOLUCIONES_BLOQUEAR,
    UMBRAL_DIAS_DEMORADO,
    UMBRAL_DIAS_ATASCADO,
    RANGOS_DEMORADOS,
    RANGOS_ATASCADOS,
)


# ============================================================
# HELPERS
# ============================================================

def _entregados(df):
    return df[df["CATEGORIA"] == "ENTREGADO"]

def _devueltos(df):
    return df[df["CATEGORIA"] == "DEVOLUCION"]

def _enviados(df):
    return df[df["TIENE_GUIA"]]


# ============================================================
# GENERAL
# ============================================================

def get_general_metrics(df):
    """KPIs generales del negocio."""
    total = len(df)
    enviados = _enviados(df)
    ent = _entregados(df)
    dev = _devueltos(df)
    n_enviados = len(enviados)
    n_entregados = len(ent)
    n_devoluciones = len(dev)
    n_en_proceso = len(df[df["CATEGORIA"] == "EN PROCESO"])
    n_nunca = len(df[df["CATEGORIA"] == "NUNCA ENVIADO"])
    n_pendientes = len(df[df["CATEGORIA"] == "PENDIENTE ATASCADO"])

    tasa_conversion = n_enviados / total if total > 0 else 0
    tasa_exito = n_entregados / n_enviados if n_enviados > 0 else 0
    tasa_devolucion = n_devoluciones / n_enviados if n_enviados > 0 else 0

    # Flete promedio solo de entregados (lo que realmente se paga)
    flete_prom = int(np.floor(ent["PRECIO FLETE"].mean())) if n_entregados > 0 else 0

    # Pérdida = flete de envío T pagado en devueltos (dinero perdido, el envío no generó venta)
    perdida_total = int(dev["PRECIO FLETE"].sum())

    # Demorados y atascados
    hoy = pd.Timestamp(datetime.now().date())
    en_proc = df[(df["TIENE_GUIA"]) & (df["CATEGORIA"] == "EN PROCESO")].copy()
    if not en_proc.empty and en_proc["FECHA GUIA GENERADA"].notna().any():
        en_proc["DIAS_TRANSITO"] = (hoy - en_proc["FECHA GUIA GENERADA"]).dt.days
        demorados = int((en_proc["DIAS_TRANSITO"] > UMBRAL_DIAS_DEMORADO).sum())
    else:
        demorados = 0

    pend = df[df["CATEGORIA"] == "PENDIENTE ATASCADO"].copy()
    if not pend.empty and pend["FECHA"].notna().any():
        pend["DIAS_ESPERA"] = (hoy - pend["FECHA"]).dt.days
        atascados = int((pend["DIAS_ESPERA"] > UMBRAL_DIAS_ATASCADO).sum())
    else:
        atascados = 0

    return {
        "total_ordenes": total,
        "envios_reales": n_enviados,
        "entregados": n_entregados,
        "devoluciones": n_devoluciones,
        "en_proceso": n_en_proceso,
        "nunca_enviados": n_nunca,
        "pendientes": n_pendientes,
        "tasa_conversion": tasa_conversion,
        "tasa_exito": tasa_exito,
        "tasa_devolucion": tasa_devolucion,
        "flete_promedio": flete_prom,
        "perdida_total": perdida_total,
        "demorados": demorados,
        "atascados": atascados,
    }


def get_status_distribution(df):
    """Distribución por categoría clasificada."""
    dist = df["CATEGORIA"].value_counts().reset_index()
    dist.columns = ["Categoría", "Cantidad"]
    dist["Porcentaje"] = (dist["Cantidad"] / dist["Cantidad"].sum() * 100).round(1)
    return dist


# ============================================================
# P&L GENERAL
# ============================================================

def get_pnl_general(df):
    """Resumen de ganancias y pérdidas generales del negocio.

    Flete envío (T) se cobra en TODOS los enviados.
    Columna U se ignora. Pérdida devoluciones = flete T ya pagado.
    Costo producto solo en entregas (dropshipping).
    """
    enviados = _enviados(df)
    ent = _entregados(df)
    dev = _devueltos(df)

    ventas_brutas = int(ent["TOTAL DE LA ORDEN"].sum())
    costo_producto = int(ent["PRECIO PROVEEDOR X CANTIDAD"].sum()) if "PRECIO PROVEEDOR X CANTIDAD" in ent.columns else int(ent["PRECIO PROVEEDOR"].sum())

    # T se cobra en TODOS los enviados (entregados + devueltos + en proceso)
    flete_envios = int(enviados["PRECIO FLETE"].sum())
    # Pérdida en devueltos = flete T que se pagó pero no generó venta
    flete_devueltos = int(dev["PRECIO FLETE"].sum())

    comisiones = int(enviados["COMISION"].sum()) if "COMISION" in enviados.columns else 0
    ganancia_col = int(ent["GANANCIA"].sum())

    venta_neta = ventas_brutas - costo_producto - flete_envios - comisiones

    return {
        "ventas_brutas": ventas_brutas,
        "costo_producto": costo_producto,
        "flete_envios": flete_envios,
        "flete_devueltos": flete_devueltos,
        "comisiones": comisiones,
        "ganancia_col": ganancia_col,
        "venta_neta": venta_neta,
        "total_entregas": len(ent),
        "total_devoluciones": len(dev),
        "total_envios": len(enviados),
    }


# ============================================================
# PRODUCTOS
# ============================================================

def get_product_analysis(df):
    """Análisis por producto: tasas de devolución."""
    enviados = _enviados(df)

    products = enviados.groupby("PRODUCTO").agg(
        Envíos=("ID", "count"),
        Devoluciones=("CATEGORIA", lambda x: (x == "DEVOLUCION").sum()),
        Entregas=("CATEGORIA", lambda x: (x == "ENTREGADO").sum()),
        Precio_Prom=("PRECIO PROVEEDOR", "mean"),
        Ticket_Venta=("TOTAL DE LA ORDEN", "mean"),
        Flete_Prom=("PRECIO FLETE", "mean"),
        Cantidad_Total=("CANTIDAD", "sum"),
        Ingreso_Total=("TOTAL DE LA ORDEN", "sum"),
    ).reset_index()

    products["% Devolución"] = (products["Devoluciones"] / products["Envíos"] * 100).round(1)
    products["% Éxito"] = (products["Entregas"] / products["Envíos"] * 100).round(1)
    products["Precio Prom"] = np.floor(products["Precio_Prom"]).astype(int)
    products["Ticket Venta"] = np.floor(products["Ticket_Venta"]).astype(int)
    products["Flete Prom"] = np.floor(products["Flete_Prom"]).astype(int)
    products["Precio/Unidad"] = np.where(
        products["Cantidad_Total"] > 0,
        np.floor(products["Ingreso_Total"] / products["Cantidad_Total"]).astype(int),
        0,
    )

    products["Acción"] = products["% Devolución"].apply(
        lambda x: "PAUSAR" if x > UMBRAL_DEVOLUCION_PAUSAR * 100 else "OK"
    )

    products = products.sort_values("% Devolución", ascending=False)

    return products[["PRODUCTO", "Envíos", "Devoluciones", "Entregas",
                      "% Devolución", "% Éxito", "Precio Prom", "Ticket Venta",
                      "Flete Prom", "Precio/Unidad", "Acción"]]


def get_product_profitability(df):
    """Rentabilidad real por producto.

    Ganancia = GANANCIA de entregas exitosas
    Pérdida = flete T pagado en devoluciones (envío perdido)
    Rentabilidad = Ganancia - Pérdida
    """
    enviados = _enviados(df)
    entregados = enviados[enviados["CATEGORIA"] == "ENTREGADO"]
    devueltos = enviados[enviados["CATEGORIA"] == "DEVOLUCION"]

    # Ganancia por producto
    gan = entregados.groupby("PRODUCTO")["GANANCIA"].sum().reset_index()
    gan.columns = ["PRODUCTO", "Ganancia Entregas"]

    # Pérdida por producto: flete T pagado en devoluciones
    per = devueltos.groupby("PRODUCTO")["PRECIO FLETE"].sum().reset_index()
    per.columns = ["PRODUCTO", "Pérdida Devoluciones"]

    # Conteos
    conteos = enviados.groupby("PRODUCTO").agg(
        Envíos=("ID", "count"),
        Entregas=("CATEGORIA", lambda x: (x == "ENTREGADO").sum()),
        Devoluciones=("CATEGORIA", lambda x: (x == "DEVOLUCION").sum()),
    ).reset_index()

    result = conteos.merge(gan, on="PRODUCTO", how="left")
    result = result.merge(per, on="PRODUCTO", how="left")
    result["Ganancia Entregas"] = result["Ganancia Entregas"].fillna(0).astype(int)
    result["Pérdida Devoluciones"] = result["Pérdida Devoluciones"].fillna(0).astype(int)
    result["Rentabilidad Real"] = result["Ganancia Entregas"] - result["Pérdida Devoluciones"]
    result["Rent/Envío"] = np.where(
        result["Envíos"] > 0,
        np.floor(result["Rentabilidad Real"] / result["Envíos"]).astype(int),
        0,
    )

    result = result.sort_values("Rentabilidad Real", ascending=True)
    return result


# ============================================================
# CLIENTES
# ============================================================

def get_client_analysis(df):
    """Análisis por cliente (teléfono)."""
    col_tel = None
    for c in df.columns:
        if "FONO" in c.upper() or "TELEFONO" in c.upper():
            col_tel = c
            break
    if col_tel is None:
        col_tel = df.columns[5]

    enviados = _enviados(df)

    clients = enviados.groupby(col_tel).agg(
        Nombre=("NOMBRE CLIENTE", "first"),
        Total_Pedidos=("ID", "count"),
        Devoluciones=("CATEGORIA", lambda x: (x == "DEVOLUCION").sum()),
        Entregas=("CATEGORIA", lambda x: (x == "ENTREGADO").sum()),
    ).reset_index()

    clients.rename(columns={col_tel: "Teléfono"}, inplace=True)
    clients["% Devolución"] = (clients["Devoluciones"] / clients["Total_Pedidos"] * 100).round(1)

    # Pérdida: flete T pagado en devoluciones por cliente
    dev = enviados[enviados["CATEGORIA"] == "DEVOLUCION"]
    dev_loss = dev.groupby(col_tel)["PRECIO FLETE"].sum().reset_index()
    dev_loss.columns = ["Teléfono", "Monto Perdido"]
    clients = clients.merge(dev_loss, on="Teléfono", how="left")
    clients["Monto Perdido"] = clients["Monto Perdido"].fillna(0).astype(int)

    bloquear = clients[clients["Devoluciones"] >= UMBRAL_DEVOLUCIONES_BLOQUEAR].sort_values(
        "Devoluciones", ascending=False
    )
    premiar = clients[clients["Entregas"] > 0].sort_values(
        "Entregas", ascending=False
    ).head(20)

    return {
        "bloquear": bloquear[["Teléfono", "Nombre", "Total_Pedidos", "Devoluciones",
                               "Entregas", "% Devolución", "Monto Perdido"]],
        "premiar": premiar[["Teléfono", "Nombre", "Total_Pedidos", "Entregas",
                             "Devoluciones", "% Devolución"]],
    }


# ============================================================
# CIUDADES
# ============================================================

def get_city_analysis(df):
    """Análisis por ciudad: por tasa % y por cantidad total."""
    enviados = _enviados(df)

    cities = enviados.groupby("CIUDAD DESTINO").agg(
        Envíos=("ID", "count"),
        Devoluciones=("CATEGORIA", lambda x: (x == "DEVOLUCION").sum()),
        Entregas=("CATEGORIA", lambda x: (x == "ENTREGADO").sum()),
        En_Proceso=("CATEGORIA", lambda x: (x == "EN PROCESO").sum()),
        Flete_Prom=("PRECIO FLETE", "mean"),
    ).reset_index()

    cities["% Devolución"] = (cities["Devoluciones"] / cities["Envíos"] * 100).round(1)
    cities["% Éxito"] = (cities["Entregas"] / cities["Envíos"] * 100).round(1)
    cities["Flete Prom"] = np.floor(cities["Flete_Prom"]).astype(int)

    cols = ["CIUDAD DESTINO", "Envíos", "Devoluciones", "Entregas",
            "En_Proceso", "% Devolución", "% Éxito", "Flete Prom"]

    by_rate = cities[cities["Envíos"] >= 10].sort_values("% Devolución", ascending=False)[cols]
    by_total = cities.sort_values("Devoluciones", ascending=False)[cols]

    return {"por_tasa": by_rate, "por_total": by_total}


def get_city_profitability(df):
    """Rentabilidad por ciudad.

    Ganancia = GANANCIA de entregas
    Pérdida = flete T pagado en devoluciones (envío perdido)
    """
    ent = _entregados(df)
    dev = _devueltos(df)

    gan = ent.groupby("CIUDAD DESTINO").agg(
        Entregas=("ID", "count"),
        Ganancia=("GANANCIA", "sum"),
    ).reset_index()

    per = dev.groupby("CIUDAD DESTINO").agg(
        Devoluciones=("ID", "count"),
        Pérdida=("PRECIO FLETE", "sum"),
    ).reset_index()

    env = _enviados(df).groupby("CIUDAD DESTINO").agg(
        Envíos=("ID", "count"),
    ).reset_index()

    result = env.merge(gan, on="CIUDAD DESTINO", how="left")
    result = result.merge(per, on="CIUDAD DESTINO", how="left")
    for col in ["Entregas", "Ganancia", "Devoluciones", "Pérdida"]:
        result[col] = result[col].fillna(0).astype(int)
    result["Rentabilidad"] = result["Ganancia"] - result["Pérdida"]
    result["% Devolución"] = (result["Devoluciones"] / result["Envíos"] * 100).round(1)
    result = result.sort_values("Rentabilidad", ascending=True)
    return result


# ============================================================
# TEMPORAL
# ============================================================

def get_temporal_analysis(df):
    """Análisis temporal: pedidos demorados y atascados."""
    hoy = pd.Timestamp(datetime.now().date())

    en_proceso = df[(df["TIENE_GUIA"]) & (df["CATEGORIA"] == "EN PROCESO")].copy()
    demorados_df = pd.DataFrame()
    if not en_proceso.empty and en_proceso["FECHA GUIA GENERADA"].notna().any():
        en_proceso["Días en Tránsito"] = (hoy - en_proceso["FECHA GUIA GENERADA"]).dt.days
        demorados_df = en_proceso[en_proceso["Días en Tránsito"] > UMBRAL_DIAS_DEMORADO].copy()

    rangos_dem = []
    for min_d, max_d, label in RANGOS_DEMORADOS:
        count = len(demorados_df[
            (demorados_df["Días en Tránsito"] >= min_d) &
            (demorados_df["Días en Tránsito"] <= max_d)
        ]) if not demorados_df.empty else 0
        rangos_dem.append({"Rango": label, "Cantidad": count})

    pendientes = df[df["CATEGORIA"] == "PENDIENTE ATASCADO"].copy()
    atascados_df = pd.DataFrame()
    if not pendientes.empty and pendientes["FECHA"].notna().any():
        pendientes["Días Esperando"] = (hoy - pendientes["FECHA"]).dt.days
        atascados_df = pendientes[pendientes["Días Esperando"] > UMBRAL_DIAS_ATASCADO].copy()

    rangos_atas = []
    for min_d, max_d, label in RANGOS_ATASCADOS:
        count = len(atascados_df[
            (atascados_df["Días Esperando"] >= min_d) &
            (atascados_df["Días Esperando"] <= max_d)
        ]) if not atascados_df.empty else 0
        rangos_atas.append({"Rango": label, "Cantidad": count})

    dem_cols = ["ID", "PRODUCTO", "ESTATUS", "CIUDAD DESTINO", "TRANSPORTADORA",
                "FECHA GUIA GENERADA", "Días en Tránsito"]
    dem_detail = demorados_df[dem_cols].sort_values("Días en Tránsito", ascending=False) if not demorados_df.empty else pd.DataFrame(columns=dem_cols)

    atas_cols = ["ID", "PRODUCTO", "CIUDAD DESTINO", "FECHA", "Días Esperando"]
    atas_detail = atascados_df[atas_cols].sort_values("Días Esperando", ascending=False) if not atascados_df.empty else pd.DataFrame(columns=atas_cols)

    return {
        "rangos_demorados": pd.DataFrame(rangos_dem),
        "rangos_atascados": pd.DataFrame(rangos_atas),
        "detalle_demorados": dem_detail,
        "detalle_atascados": atas_detail,
    }


# ============================================================
# COSTOS
# ============================================================

def get_cost_analysis(df):
    """Análisis de costos e impacto económico.

    Flete T se cobra en todos los enviados. Columna U se ignora.
    Pérdida de devoluciones = flete T pagado en devueltos.
    """
    enviados = _enviados(df)
    ent = _entregados(df)
    dev = _devueltos(df)

    flete_envios = int(enviados["PRECIO FLETE"].sum())
    flete_devueltos = int(dev["PRECIO FLETE"].sum())

    costo_producto = int(ent["PRECIO PROVEEDOR X CANTIDAD"].sum()) if "PRECIO PROVEEDOR X CANTIDAD" in ent.columns else int(ent["PRECIO PROVEEDOR"].sum())
    ingreso_perdido = int(dev["TOTAL DE LA ORDEN"].sum())

    # Inventario atascado
    en_proceso = df[df["CATEGORIA"].isin(["EN PROCESO", "PENDIENTE ATASCADO"])]
    valor_inventario = int(en_proceso["TOTAL DE LA ORDEN"].sum())

    # Top 10 pérdida por ciudad (flete T de devueltos)
    dev_city = dev.groupby("CIUDAD DESTINO").agg(
        Devoluciones=("ID", "count"),
        Pérdida_Flete=("PRECIO FLETE", "sum"),
    ).reset_index()
    dev_city.rename(columns={"Pérdida_Flete": "Pérdida Total"}, inplace=True)
    top_cities = dev_city.sort_values("Pérdida Total", ascending=False).head(10)

    # Top 10 pérdida por producto (flete T de devueltos)
    dev_prod = dev.groupby("PRODUCTO").agg(
        Devoluciones=("ID", "count"),
        Pérdida_Flete=("PRECIO FLETE", "sum"),
    ).reset_index()
    dev_prod.rename(columns={"Pérdida_Flete": "Pérdida Total"}, inplace=True)
    top_products = dev_prod.sort_values("Pérdida Total", ascending=False).head(10)

    return {
        "flete_envios": flete_envios,
        "flete_devueltos": flete_devueltos,
        "costo_producto": costo_producto,
        "ingreso_perdido": ingreso_perdido,
        "valor_inventario": valor_inventario,
        "top_cities": top_cities,
        "top_products": top_products,
    }


# ============================================================
# NOVEDADES
# ============================================================

def get_novelty_analysis(df):
    """Análisis de novedades, soluciones y tasa de resolución."""
    with_novelty = df[df["NOVEDAD"].notna() & (df["NOVEDAD"] != "")]

    if with_novelty.empty:
        return {
            "total_novedades": 0, "resueltas": 0, "no_resueltas": 0,
            "tasa_resolucion": 0, "top_novedades": pd.DataFrame(),
            "top_soluciones": pd.DataFrame(), "novedades_por_tipo": pd.DataFrame(),
        }

    total = len(with_novelty)
    col_sol = "FUE SOLUCIONADA LA NOVEDAD"
    resueltas = len(with_novelty[with_novelty[col_sol] == "SI"]) if col_sol in with_novelty.columns else 0
    no_resueltas = total - resueltas
    tasa = resueltas / total if total > 0 else 0

    top_nov = with_novelty["NOVEDAD"].value_counts().reset_index()
    top_nov.columns = ["Novedad", "Cantidad"]
    top_nov["Porcentaje"] = (top_nov["Cantidad"] / total * 100).round(1)

    # Buscar columna SOLUCIÓN (texto, no hora ni fecha)
    col_solucion = None
    for c in df.columns:
        c_upper = c.upper()
        if "SOLUCI" in c_upper and "HORA" not in c_upper and "FECHA" not in c_upper and "FUE" not in c_upper:
            col_solucion = c
            break

    top_sol = pd.DataFrame()
    if col_solucion:
        with_sol = with_novelty[with_novelty[col_solucion].notna() & (with_novelty[col_solucion] != "")]
        if not with_sol.empty:
            top_sol = with_sol[col_solucion].value_counts().head(5).reset_index()
            top_sol.columns = ["Solución", "Cantidad"]

    if col_sol in with_novelty.columns:
        nov_tipo = with_novelty.groupby("NOVEDAD").agg(
            Total=("ID", "count"),
            Resueltas=(col_sol, lambda x: (x == "SI").sum()),
        ).reset_index()
        nov_tipo["No Resueltas"] = nov_tipo["Total"] - nov_tipo["Resueltas"]
        nov_tipo["% Resolución"] = (nov_tipo["Resueltas"] / nov_tipo["Total"] * 100).round(1)
        nov_tipo = nov_tipo.sort_values("Total", ascending=False)
    else:
        nov_tipo = pd.DataFrame()

    return {
        "total_novedades": total, "resueltas": resueltas,
        "no_resueltas": no_resueltas, "tasa_resolucion": tasa,
        "top_novedades": top_nov, "top_soluciones": top_sol,
        "novedades_por_tipo": nov_tipo,
    }


# ============================================================
# TRANSPORTADORAS
# ============================================================

def get_carrier_analysis(df):
    """Análisis detallado por transportadora: fletes, tasas, costos."""
    enviados = _enviados(df)

    carriers = []
    for t in df["TRANSPORTADORA"].unique():
        sub = enviados[enviados["TRANSPORTADORA"] == t]
        if len(sub) < 5:
            continue

        sub_ent = sub[sub["CATEGORIA"] == "ENTREGADO"]
        sub_dev = sub[sub["CATEGORIA"] == "DEVOLUCION"]
        sub_proc = sub[sub["CATEGORIA"] == "EN PROCESO"]

        n_env = len(sub)
        n_ent = len(sub_ent)
        n_dev = len(sub_dev)
        n_proc = len(sub_proc)

        flete_envio_prom = int(np.floor(sub["PRECIO FLETE"].mean()))
        flete_dev_prom = int(np.floor(sub_dev["PRECIO FLETE"].mean())) if n_dev > 0 else 0

        flete_envio_total = int(sub["PRECIO FLETE"].sum())
        flete_dev_total = int(sub_dev["PRECIO FLETE"].sum())

        ganancia_total = int(sub_ent["GANANCIA"].sum())
        rentabilidad = ganancia_total - flete_dev_total

        carriers.append({
            "Transportadora": t,
            "Envíos": n_env,
            "Entregas": n_ent,
            "Devoluciones": n_dev,
            "En Proceso": n_proc,
            "% Éxito": round(n_ent / n_env * 100, 1) if n_env > 0 else 0,
            "% Devolución": round(n_dev / n_env * 100, 1) if n_env > 0 else 0,
            "Flete Envío Prom": flete_envio_prom,
            "Flete Dev Prom": flete_dev_prom,
            "Flete Envío Total": flete_envio_total,
            "Flete Dev Total": flete_dev_total,
            "Ganancia": ganancia_total,
            "Rentabilidad": rentabilidad,
        })

    return pd.DataFrame(carriers).sort_values("Envíos", ascending=False) if carriers else pd.DataFrame()


# ============================================================
# AGENTES / VENDEDORES
# ============================================================

def get_agent_cancellations(df):
    """Cancelaciones y métricas por agente/vendedor."""
    col_vendedor = "VENDEDOR"
    if col_vendedor not in df.columns:
        return pd.DataFrame()

    with_agent = df[df[col_vendedor].notna() & (df[col_vendedor].astype(str).str.strip() != "")]
    if with_agent.empty:
        return pd.DataFrame()

    agents = with_agent.groupby(col_vendedor).agg(
        Total_Pedidos=("ID", "count"),
        Cancelados=("CATEGORIA", lambda x: (x == "NUNCA ENVIADO").sum()),
        Enviados=("TIENE_GUIA", "sum"),
        Entregados=("CATEGORIA", lambda x: (x == "ENTREGADO").sum()),
        Devoluciones=("CATEGORIA", lambda x: (x == "DEVOLUCION").sum()),
    ).reset_index()

    agents.rename(columns={col_vendedor: "Agente"}, inplace=True)
    agents["% Cancelación"] = (agents["Cancelados"] / agents["Total_Pedidos"] * 100).round(1)
    agents["% Éxito"] = np.where(
        agents["Enviados"] > 0,
        (agents["Entregados"] / agents["Enviados"] * 100).round(1),
        0,
    )
    agents["% Devolución"] = np.where(
        agents["Enviados"] > 0,
        (agents["Devoluciones"] / agents["Enviados"] * 100).round(1),
        0,
    )

    return agents.sort_values("Cancelados", ascending=False)


# ============================================================
# BUSCADOR DE PRODUCTOS
# ============================================================

def get_product_search_metrics(df, productos) -> dict:
    """Métricas detalladas para uno o varios productos seleccionados."""
    filtered = df[df["PRODUCTO"].isin(productos)]
    enviados = _enviados(filtered)
    ent = enviados[enviados["CATEGORIA"] == "ENTREGADO"]
    dev = enviados[enviados["CATEGORIA"] == "DEVOLUCION"]
    cancelados = filtered[filtered["CATEGORIA"] == "NUNCA ENVIADO"]

    ganancia = int(ent["GANANCIA"].sum())
    perdida = int(dev["PRECIO FLETE"].sum())
    flete_envios = int(enviados["PRECIO FLETE"].sum())
    costo_producto = int(ent["PRECIO PROVEEDOR X CANTIDAD"].sum()) if "PRECIO PROVEEDOR X CANTIDAD" in ent.columns else int(ent["PRECIO PROVEEDOR"].sum())
    ventas_brutas = int(ent["TOTAL DE LA ORDEN"].sum())

    return {
        "total_ordenes": len(filtered),
        "envios": len(enviados),
        "entregas": len(ent),
        "devoluciones": len(dev),
        "cancelados": len(cancelados),
        "tasa_exito": len(ent) / len(enviados) if len(enviados) > 0 else 0,
        "tasa_devolucion": len(dev) / len(enviados) if len(enviados) > 0 else 0,
        "ventas_brutas": ventas_brutas,
        "ingreso_bruto": ventas_brutas,
        "costo_producto": costo_producto,
        "flete_envios": flete_envios,
        "flete_devueltos": perdida,
        "ganancia_entregas": ganancia,
        "perdida_devoluciones": perdida,
        "rentabilidad": ganancia - perdida,
        "ticket_promedio": int(np.floor(filtered["TOTAL DE LA ORDEN"].mean())) if len(filtered) > 0 else 0,
    }


# ============================================================
# EVOLUCIÓN TEMPORAL
# ============================================================

def get_temporal_evolution(df):
    """Evolución temporal de entregas vs devoluciones por fecha de guía generada."""
    enviados = df[df["TIENE_GUIA"] & df["FECHA GUIA GENERADA"].notna()].copy()
    if enviados.empty:
        return pd.DataFrame()

    enviados["Fecha"] = enviados["FECHA GUIA GENERADA"].dt.date

    evolution = enviados.groupby("Fecha").agg(
        Envíos=("ID", "count"),
        Entregas=("CATEGORIA", lambda x: (x == "ENTREGADO").sum()),
        Devoluciones=("CATEGORIA", lambda x: (x == "DEVOLUCION").sum()),
    ).reset_index()

    evolution["Fecha"] = pd.to_datetime(evolution["Fecha"])
    return evolution.sort_values("Fecha")
