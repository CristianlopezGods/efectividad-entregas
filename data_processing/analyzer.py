"""Cálculos y métricas de negocio sobre el DataFrame clasificado."""

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


def get_general_metrics(df: pd.DataFrame) -> dict:
    """KPIs generales del negocio."""
    total = len(df)
    enviados = df[df["TIENE_GUIA"]].shape[0]
    entregados = df[df["CATEGORIA"] == "ENTREGADO"].shape[0]
    devoluciones = df[df["CATEGORIA"] == "DEVOLUCION"].shape[0]
    en_proceso = df[df["CATEGORIA"] == "EN PROCESO"].shape[0]
    nunca_enviados = df[df["CATEGORIA"] == "NUNCA ENVIADO"].shape[0]
    pendientes = df[df["CATEGORIA"] == "PENDIENTE ATASCADO"].shape[0]

    tasa_conversion = enviados / total if total > 0 else 0
    tasa_exito = entregados / enviados if enviados > 0 else 0
    tasa_devolucion = devoluciones / enviados if enviados > 0 else 0

    flete_promedio = int(np.floor(df[df["TIENE_GUIA"]]["PRECIO FLETE"].mean())) if enviados > 0 else 0

    # Pérdida total por devoluciones (flete envío + costo devolución)
    dev_df = df[df["CATEGORIA"] == "DEVOLUCION"]
    perdida_flete = dev_df["PRECIO FLETE"].sum()
    perdida_devolucion = dev_df["COSTO DEVOLUCION FLETE"].sum()
    # Si costo_devolucion_flete = 0, usar flete × 2
    dev_sin_costo = dev_df[dev_df["COSTO DEVOLUCION FLETE"] == 0]
    perdida_devolucion += dev_sin_costo["PRECIO FLETE"].sum()
    perdida_total = int(perdida_flete + perdida_devolucion)

    # Demorados y atascados
    hoy = pd.Timestamp(datetime.now().date())
    enviados_df = df[(df["TIENE_GUIA"]) & (df["CATEGORIA"] == "EN PROCESO")]
    if not enviados_df.empty and enviados_df["FECHA GUIA GENERADA"].notna().any():
        enviados_df = enviados_df.copy()
        enviados_df["DIAS_TRANSITO"] = (hoy - enviados_df["FECHA GUIA GENERADA"]).dt.days
        demorados = int((enviados_df["DIAS_TRANSITO"] > UMBRAL_DIAS_DEMORADO).sum())
    else:
        demorados = 0

    pend_df = df[df["CATEGORIA"] == "PENDIENTE ATASCADO"]
    if not pend_df.empty and pend_df["FECHA"].notna().any():
        pend_df = pend_df.copy()
        pend_df["DIAS_ESPERA"] = (hoy - pend_df["FECHA"]).dt.days
        atascados = int((pend_df["DIAS_ESPERA"] > UMBRAL_DIAS_ATASCADO).sum())
    else:
        atascados = 0

    return {
        "total_ordenes": total,
        "envios_reales": enviados,
        "entregados": entregados,
        "devoluciones": devoluciones,
        "en_proceso": en_proceso,
        "nunca_enviados": nunca_enviados,
        "pendientes": pendientes,
        "tasa_conversion": tasa_conversion,
        "tasa_exito": tasa_exito,
        "tasa_devolucion": tasa_devolucion,
        "flete_promedio": flete_promedio,
        "perdida_total": perdida_total,
        "demorados": demorados,
        "atascados": atascados,
    }


def get_status_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Distribución por categoría clasificada."""
    dist = df["CATEGORIA"].value_counts().reset_index()
    dist.columns = ["Categoría", "Cantidad"]
    dist["Porcentaje"] = (dist["Cantidad"] / dist["Cantidad"].sum() * 100).round(1)
    return dist


def get_product_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Análisis por producto."""
    # Solo considerar órdenes que fueron enviadas
    enviados = df[df["TIENE_GUIA"]]

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

    # Acción recomendada
    products["Acción"] = products["% Devolución"].apply(
        lambda x: "🔴 PAUSAR" if x > UMBRAL_DEVOLUCION_PAUSAR * 100 else "✅ OK"
    )

    products = products.sort_values("% Devolución", ascending=False)

    return products[["PRODUCTO", "Envíos", "Devoluciones", "Entregas",
                      "% Devolución", "% Éxito", "Precio Prom", "Ticket Venta",
                      "Flete Prom", "Precio/Unidad", "Acción"]]


def get_product_profitability(df: pd.DataFrame) -> pd.DataFrame:
    """Rentabilidad real por producto: ganancia de entregas - pérdida de devoluciones."""
    enviados = df[df["TIENE_GUIA"]]

    # Ganancia de entregas exitosas (columna GANANCIA del Excel)
    entregados = enviados[enviados["CATEGORIA"] == "ENTREGADO"]
    ganancia_por_prod = entregados.groupby("PRODUCTO")["GANANCIA"].sum().reset_index()
    ganancia_por_prod.columns = ["PRODUCTO", "Ganancia Entregas"]

    # Pérdida por devoluciones: flete envío + costo devolución
    devueltos = enviados[enviados["CATEGORIA"] == "DEVOLUCION"].copy()
    # Si COSTO DEVOLUCION FLETE es 0, usar PRECIO FLETE como costo de retorno
    devueltos["Costo_Devolucion"] = np.where(
        devueltos["COSTO DEVOLUCION FLETE"] > 0,
        devueltos["PRECIO FLETE"] + devueltos["COSTO DEVOLUCION FLETE"],
        devueltos["PRECIO FLETE"] * 2,
    )
    perdida_por_prod = devueltos.groupby("PRODUCTO")["Costo_Devolucion"].sum().reset_index()
    perdida_por_prod.columns = ["PRODUCTO", "Pérdida Devoluciones"]

    # Conteos
    conteos = enviados.groupby("PRODUCTO").agg(
        Envíos=("ID", "count"),
        Entregas=("CATEGORIA", lambda x: (x == "ENTREGADO").sum()),
        Devoluciones=("CATEGORIA", lambda x: (x == "DEVOLUCION").sum()),
    ).reset_index()

    # Merge todo
    result = conteos.merge(ganancia_por_prod, on="PRODUCTO", how="left")
    result = result.merge(perdida_por_prod, on="PRODUCTO", how="left")
    result["Ganancia Entregas"] = result["Ganancia Entregas"].fillna(0).astype(int)
    result["Pérdida Devoluciones"] = result["Pérdida Devoluciones"].fillna(0).astype(int)

    # Rentabilidad real
    result["Rentabilidad Real"] = result["Ganancia Entregas"] - result["Pérdida Devoluciones"]

    # Rentabilidad por envío
    result["Rent/Envío"] = np.where(
        result["Envíos"] > 0,
        np.floor(result["Rentabilidad Real"] / result["Envíos"]).astype(int),
        0,
    )

    result = result.sort_values("Rentabilidad Real", ascending=True)

    return result[["PRODUCTO", "Envíos", "Entregas", "Devoluciones",
                    "Ganancia Entregas", "Pérdida Devoluciones",
                    "Rentabilidad Real", "Rent/Envío"]]


def get_client_analysis(df: pd.DataFrame) -> dict:
    """Análisis por cliente (teléfono)."""
    col_tel = None
    for c in df.columns:
        if "FONO" in c.upper() or "TELEFONO" in c.upper() or "TELÉFONO" in c.upper():
            col_tel = c
            break
    if col_tel is None:
        col_tel = df.columns[5]  # Fallback to column index 5

    enviados = df[df["TIENE_GUIA"]]

    clients = enviados.groupby(col_tel).agg(
        Nombre=("NOMBRE CLIENTE", "first"),
        Total_Pedidos=("ID", "count"),
        Devoluciones=("CATEGORIA", lambda x: (x == "DEVOLUCION").sum()),
        Entregas=("CATEGORIA", lambda x: (x == "ENTREGADO").sum()),
        Perdida_Flete=("PRECIO FLETE", lambda x: x[enviados.loc[x.index, "CATEGORIA"] == "DEVOLUCION"].sum()),
    ).reset_index()

    clients.rename(columns={col_tel: "Teléfono"}, inplace=True)
    clients["% Devolución"] = (clients["Devoluciones"] / clients["Total_Pedidos"] * 100).round(1)

    # Costo devolución: flete × 2 por cada devolución
    clients["Monto Perdido"] = (clients["Perdida_Flete"] * 2).astype(int)

    # Clientes a bloquear: 3+ devoluciones
    bloquear = clients[clients["Devoluciones"] >= UMBRAL_DEVOLUCIONES_BLOQUEAR].sort_values(
        "Devoluciones", ascending=False
    )

    # Clientes a premiar: más entregas exitosas
    premiar = clients[clients["Entregas"] > 0].sort_values(
        "Entregas", ascending=False
    ).head(20)

    return {
        "bloquear": bloquear[["Teléfono", "Nombre", "Total_Pedidos", "Devoluciones",
                               "Entregas", "% Devolución", "Monto Perdido"]],
        "premiar": premiar[["Teléfono", "Nombre", "Total_Pedidos", "Entregas",
                             "Devoluciones", "% Devolución"]],
    }


def get_city_analysis(df: pd.DataFrame) -> dict:
    """Análisis por ciudad: por tasa % y por cantidad total."""
    enviados = df[df["TIENE_GUIA"]]

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


def get_temporal_analysis(df: pd.DataFrame) -> dict:
    """Análisis temporal: pedidos demorados y atascados."""
    hoy = pd.Timestamp(datetime.now().date())

    # Demorados: enviados en proceso con >7 días
    en_proceso = df[(df["TIENE_GUIA"]) & (df["CATEGORIA"] == "EN PROCESO")].copy()
    demorados_df = pd.DataFrame()
    if not en_proceso.empty and en_proceso["FECHA GUIA GENERADA"].notna().any():
        en_proceso["Días en Tránsito"] = (hoy - en_proceso["FECHA GUIA GENERADA"]).dt.days
        demorados_df = en_proceso[en_proceso["Días en Tránsito"] > UMBRAL_DIAS_DEMORADO].copy()

    # Rangos de demorados
    rangos_dem = []
    for min_d, max_d, label in RANGOS_DEMORADOS:
        count = len(demorados_df[
            (demorados_df["Días en Tránsito"] >= min_d) &
            (demorados_df["Días en Tránsito"] <= max_d)
        ]) if not demorados_df.empty else 0
        rangos_dem.append({"Rango": label, "Cantidad": count})

    # Atascados: pendientes con >3 días
    pendientes = df[df["CATEGORIA"] == "PENDIENTE ATASCADO"].copy()
    atascados_df = pd.DataFrame()
    if not pendientes.empty and pendientes["FECHA"].notna().any():
        pendientes["Días Esperando"] = (hoy - pendientes["FECHA"]).dt.days
        atascados_df = pendientes[pendientes["Días Esperando"] > UMBRAL_DIAS_ATASCADO].copy()

    # Rangos de atascados
    rangos_atas = []
    for min_d, max_d, label in RANGOS_ATASCADOS:
        count = len(atascados_df[
            (atascados_df["Días Esperando"] >= min_d) &
            (atascados_df["Días Esperando"] <= max_d)
        ]) if not atascados_df.empty else 0
        rangos_atas.append({"Rango": label, "Cantidad": count})

    # Detalle de demorados
    dem_cols = ["ID", "PRODUCTO", "ESTATUS", "CIUDAD DESTINO", "TRANSPORTADORA",
                "FECHA GUIA GENERADA", "Días en Tránsito"]
    dem_detail = demorados_df[dem_cols].sort_values("Días en Tránsito", ascending=False) if not demorados_df.empty else pd.DataFrame(columns=dem_cols)

    # Detalle de atascados
    atas_cols = ["ID", "PRODUCTO", "CIUDAD DESTINO", "FECHA", "Días Esperando"]
    atas_detail = atascados_df[atas_cols].sort_values("Días Esperando", ascending=False) if not atascados_df.empty else pd.DataFrame(columns=atas_cols)

    return {
        "rangos_demorados": pd.DataFrame(rangos_dem),
        "rangos_atascados": pd.DataFrame(rangos_atas),
        "detalle_demorados": dem_detail,
        "detalle_atascados": atas_detail,
    }


def get_cost_analysis(df: pd.DataFrame) -> dict:
    """Análisis de costos e impacto económico."""
    enviados = df[df["TIENE_GUIA"]]
    dev = df[df["CATEGORIA"] == "DEVOLUCION"]

    # Costo total fletes de envíos reales
    costo_fletes = int(enviados["PRECIO FLETE"].sum())

    # Pérdida por devoluciones
    perdida_flete_envio = int(dev["PRECIO FLETE"].sum())
    perdida_flete_devolucion = int(dev["COSTO DEVOLUCION FLETE"].sum())
    dev_sin_costo = dev[dev["COSTO DEVOLUCION FLETE"] == 0]
    perdida_flete_devolucion += int(dev_sin_costo["PRECIO FLETE"].sum())
    perdida_total_fletes = perdida_flete_envio + perdida_flete_devolucion

    # Valor de productos devueltos (precio proveedor)
    valor_productos_devueltos = int(dev["PRECIO PROVEEDOR X CANTIDAD"].sum()) if "PRECIO PROVEEDOR X CANTIDAD" in dev.columns else int(dev["PRECIO PROVEEDOR"].sum())

    # Inventario atascado (pendientes + en proceso)
    en_proceso = df[df["CATEGORIA"].isin(["EN PROCESO", "PENDIENTE ATASCADO"])]
    valor_inventario_atascado = int(en_proceso["PRECIO PROVEEDOR X CANTIDAD"].sum()) if "PRECIO PROVEEDOR X CANTIDAD" in en_proceso.columns else int(en_proceso["PRECIO PROVEEDOR"].sum())

    # Ingreso perdido por devoluciones (ventas que no se concretaron)
    ingreso_perdido = int(dev["TOTAL DE LA ORDEN"].sum())

    # Top 10 pérdida por ciudad
    dev_city = dev.groupby("CIUDAD DESTINO").agg(
        Devoluciones=("ID", "count"),
        Pérdida_Flete=("PRECIO FLETE", "sum"),
    ).reset_index()
    dev_city["Pérdida Total"] = (dev_city["Pérdida_Flete"] * 2).astype(int)
    top_cities = dev_city.sort_values("Pérdida Total", ascending=False).head(10)

    # Top 10 pérdida por producto
    dev_prod = dev.groupby("PRODUCTO").agg(
        Devoluciones=("ID", "count"),
        Pérdida_Flete=("PRECIO FLETE", "sum"),
        Valor_Producto=("PRECIO PROVEEDOR X CANTIDAD", "sum") if "PRECIO PROVEEDOR X CANTIDAD" in dev.columns else ("PRECIO PROVEEDOR", "sum"),
    ).reset_index()
    dev_prod["Pérdida Total"] = (dev_prod["Pérdida_Flete"] * 2).astype(int)
    top_products = dev_prod.sort_values("Pérdida Total", ascending=False).head(10)

    return {
        "costo_fletes": costo_fletes,
        "perdida_flete_envio": perdida_flete_envio,
        "perdida_flete_devolucion": perdida_flete_devolucion,
        "perdida_total_fletes": perdida_total_fletes,
        "valor_productos_devueltos": valor_productos_devueltos,
        "valor_inventario_atascado": valor_inventario_atascado,
        "ingreso_perdido": ingreso_perdido,
        "top_cities": top_cities,
        "top_products": top_products,
    }


def get_novelty_analysis(df: pd.DataFrame) -> dict:
    """Análisis de novedades, soluciones y tasa de resolución."""
    with_novelty = df[df["NOVEDAD"].notna() & (df["NOVEDAD"] != "")]

    if with_novelty.empty:
        return {
            "total_novedades": 0,
            "resueltas": 0,
            "no_resueltas": 0,
            "tasa_resolucion": 0,
            "top_novedades": pd.DataFrame(),
            "top_soluciones": pd.DataFrame(),
            "novedades_por_tipo": pd.DataFrame(),
        }

    total = len(with_novelty)

    # Tasa de resolución
    col_sol = "FUE SOLUCIONADA LA NOVEDAD"
    resueltas = len(with_novelty[with_novelty[col_sol] == "SI"]) if col_sol in with_novelty.columns else 0
    no_resueltas = total - resueltas
    tasa = resueltas / total if total > 0 else 0

    # Top novedades más frecuentes
    top_nov = with_novelty["NOVEDAD"].value_counts().reset_index()
    top_nov.columns = ["Novedad", "Cantidad"]
    top_nov["Porcentaje"] = (top_nov["Cantidad"] / total * 100).round(1)

    # Top soluciones - buscar columna que sea la SOLUCIÓN texto (no hora ni fecha)
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

    # Novedades resueltas vs no resueltas por tipo
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
        "total_novedades": total,
        "resueltas": resueltas,
        "no_resueltas": no_resueltas,
        "tasa_resolucion": tasa,
        "top_novedades": top_nov,
        "top_soluciones": top_sol,
        "novedades_por_tipo": nov_tipo,
    }


def get_pnl_general(df: pd.DataFrame) -> dict:
    """Resumen de ganancias y pérdidas generales del negocio."""
    enviados = df[df["TIENE_GUIA"]]
    entregados = enviados[enviados["CATEGORIA"] == "ENTREGADO"]
    devueltos = enviados[enviados["CATEGORIA"] == "DEVOLUCION"]

    # Ingresos: suma de TOTAL DE LA ORDEN de entregas exitosas
    ingreso_bruto = int(entregados["TOTAL DE LA ORDEN"].sum())

    # Costo productos entregados
    costo_productos = int(entregados["PRECIO PROVEEDOR X CANTIDAD"].sum()) if "PRECIO PROVEEDOR X CANTIDAD" in entregados.columns else int(entregados["PRECIO PROVEEDOR"].sum())

    # Costo fletes de todos los envíos
    costo_fletes_envio = int(enviados["PRECIO FLETE"].sum())

    # Ganancia bruta (columna GANANCIA de entregas)
    ganancia_entregas = int(entregados["GANANCIA"].sum())

    # Pérdida por devoluciones (flete ida + vuelta)
    dev_copy = devueltos.copy()
    dev_copy["perdida_flete"] = np.where(
        dev_copy["COSTO DEVOLUCION FLETE"] > 0,
        dev_copy["PRECIO FLETE"] + dev_copy["COSTO DEVOLUCION FLETE"],
        dev_copy["PRECIO FLETE"] * 2,
    )
    perdida_devoluciones = int(dev_copy["perdida_flete"].sum())

    # Comisiones
    comisiones = int(enviados["COMISION"].sum()) if "COMISION" in enviados.columns else 0

    # Rentabilidad neta
    rentabilidad_neta = ganancia_entregas - perdida_devoluciones

    return {
        "ingreso_bruto": ingreso_bruto,
        "costo_productos": costo_productos,
        "costo_fletes_envio": costo_fletes_envio,
        "ganancia_entregas": ganancia_entregas,
        "perdida_devoluciones": perdida_devoluciones,
        "comisiones": comisiones,
        "rentabilidad_neta": rentabilidad_neta,
        "total_envios": len(enviados),
        "total_entregas": len(entregados),
        "total_devoluciones": len(devueltos),
    }


def get_city_profitability(df: pd.DataFrame) -> pd.DataFrame:
    """Rentabilidad por ciudad: ganancia de entregas - pérdida de devoluciones."""
    enviados = df[df["TIENE_GUIA"]]
    entregados = enviados[enviados["CATEGORIA"] == "ENTREGADO"]
    devueltos = enviados[enviados["CATEGORIA"] == "DEVOLUCION"]

    # Ganancia por ciudad
    gan = entregados.groupby("CIUDAD DESTINO").agg(
        Entregas=("ID", "count"),
        Ganancia=("GANANCIA", "sum"),
    ).reset_index()

    # Pérdida por ciudad
    dev_copy = devueltos.copy()
    dev_copy["perdida_flete"] = np.where(
        dev_copy["COSTO DEVOLUCION FLETE"] > 0,
        dev_copy["PRECIO FLETE"] + dev_copy["COSTO DEVOLUCION FLETE"],
        dev_copy["PRECIO FLETE"] * 2,
    )
    per = dev_copy.groupby("CIUDAD DESTINO").agg(
        Devoluciones=("ID", "count"),
        Pérdida=("perdida_flete", "sum"),
    ).reset_index()

    # Envíos totales por ciudad
    env = enviados.groupby("CIUDAD DESTINO").agg(
        Envíos=("ID", "count"),
    ).reset_index()

    # Merge
    result = env.merge(gan, on="CIUDAD DESTINO", how="left")
    result = result.merge(per, on="CIUDAD DESTINO", how="left")
    result["Entregas"] = result["Entregas"].fillna(0).astype(int)
    result["Ganancia"] = result["Ganancia"].fillna(0).astype(int)
    result["Devoluciones"] = result["Devoluciones"].fillna(0).astype(int)
    result["Pérdida"] = result["Pérdida"].fillna(0).astype(int)
    result["Rentabilidad"] = result["Ganancia"] - result["Pérdida"]
    result["% Devolución"] = (result["Devoluciones"] / result["Envíos"] * 100).round(1)

    result = result.sort_values("Rentabilidad", ascending=True)
    return result


def get_agent_cancellations(df: pd.DataFrame) -> pd.DataFrame:
    """Cancelaciones y métricas por agente/vendedor."""
    col_vendedor = "VENDEDOR"
    if col_vendedor not in df.columns:
        return pd.DataFrame()

    # Solo filas con vendedor asignado
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


def get_product_search_metrics(df: pd.DataFrame, productos: list[str]) -> dict:
    """Métricas detalladas para uno o varios productos seleccionados."""
    filtered = df[df["PRODUCTO"].isin(productos)]
    enviados = filtered[filtered["TIENE_GUIA"]]
    entregados = enviados[enviados["CATEGORIA"] == "ENTREGADO"]
    devueltos = enviados[enviados["CATEGORIA"] == "DEVOLUCION"]
    cancelados = filtered[filtered["CATEGORIA"] == "NUNCA ENVIADO"]

    # Pérdida devoluciones
    dev_copy = devueltos.copy()
    if not dev_copy.empty:
        dev_copy["perdida_flete"] = np.where(
            dev_copy["COSTO DEVOLUCION FLETE"] > 0,
            dev_copy["PRECIO FLETE"] + dev_copy["COSTO DEVOLUCION FLETE"],
            dev_copy["PRECIO FLETE"] * 2,
        )
        perdida = int(dev_copy["perdida_flete"].sum())
    else:
        perdida = 0

    ganancia = int(entregados["GANANCIA"].sum())

    return {
        "total_ordenes": len(filtered),
        "envios": len(enviados),
        "entregas": len(entregados),
        "devoluciones": len(devueltos),
        "cancelados": len(cancelados),
        "tasa_exito": len(entregados) / len(enviados) if len(enviados) > 0 else 0,
        "tasa_devolucion": len(devueltos) / len(enviados) if len(enviados) > 0 else 0,
        "ganancia_entregas": ganancia,
        "perdida_devoluciones": perdida,
        "rentabilidad": ganancia - perdida,
        "ingreso_bruto": int(entregados["TOTAL DE LA ORDEN"].sum()),
        "flete_total": int(enviados["PRECIO FLETE"].sum()),
        "ticket_promedio": int(np.floor(filtered["TOTAL DE LA ORDEN"].mean())) if len(filtered) > 0 else 0,
    }


def get_temporal_evolution(df: pd.DataFrame) -> pd.DataFrame:
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
