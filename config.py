"""Configuración y constantes del dashboard."""

# --- Categorías de Estatus ---
# Mapeo de estatus originales a categorías de clasificación

ESTATUS_NUNCA_ENVIADO = [
    "CANCELADO",
    "RECHAZADO",
    "ADMITIDA",
    "PENDIENTE CONFIRMACION",
]

ESTATUS_PENDIENTE_ATASCADO = [
    "PENDIENTE",
]

ESTATUS_DEVOLUCION = [
    "DEVOLUCION",
    "DEVOLUCION EN BODEGA",
    "EN PROCESO DE DEVOLUCION",
    "TRANSITO A DEVOLUCION PROVEEDOR",
]

ESTATUS_ENTREGADO = [
    "ENTREGADO",
]

ESTATUS_EN_PROCESO = [
    "GUIA_GENERADA",
    "GUIA_ANULADA",
    "RECOGIDO POR DROPI",
    "PREPARADO PARA TRANSPORTADORA",
    "EN BODEGA DROPI",
    "ENTREGADO A TRANSPORTADORA",
    "EN BODEGA ORIGEN",
    "EN BODEGA TRANSPORTADORA",
    "RECLAME EN OFICINA",
    "EN PROCESAMIENTO",
    "EN REPARTO",
    "EN BODEGA DESTINO",
    "BODEGA DESTINO",
    "DESPACHADA",
    "INTENTO DE ENTREGA",
    "NOVEDAD",
    "NOVEDAD SOLUCIONADA",
    "EN ESPERA DE RUTA DOMESTICA",
    "TELEMERCADEO",
    "REENVÍO",
    "SIN MOVIMIENTOS",
    "EN TERMINAL ORIGEN",
    "EN TERMINAL DESTINO",
    "EN TRANSPORTE",
    "EN RUTA",
    "EN REEXPEDICION",
    "ENTREGADA A CONEXIONES",
    "EN PROCESO DE INDEMNIZACION",
    "EN PUNTO DROOP",
]

# Categorías posibles
CATEGORIAS = [
    "NUNCA ENVIADO",
    "PENDIENTE ATASCADO",
    "DEVOLUCION",
    "ENTREGADO",
    "EN PROCESO",
    "DESCONOCIDO",
    "ERROR DE DATOS",
]

# Colores para cada categoría
COLORES_CATEGORIAS = {
    "NUNCA ENVIADO": "#95a5a6",
    "PENDIENTE ATASCADO": "#f39c12",
    "DEVOLUCION": "#e74c3c",
    "ENTREGADO": "#27ae60",
    "EN PROCESO": "#3498db",
    "DESCONOCIDO": "#9b59b6",
    "ERROR DE DATOS": "#e67e22",
}

# --- Umbrales de Negocio ---
UMBRAL_DEVOLUCION_PAUSAR = 0.30  # >30% devolución = pausar producto
UMBRAL_DEVOLUCIONES_BLOQUEAR = 3  # 3+ devoluciones = bloquear cliente
UMBRAL_DIAS_DEMORADO = 7  # >7 días = envío demorado
UMBRAL_DIAS_ATASCADO = 3  # >3 días = pedido atascado en pendiente

# Rangos para análisis temporal
RANGOS_DEMORADOS = [
    (8, 10, "8-10 días"),
    (11, 15, "11-15 días"),
    (16, 20, "16-20 días"),
    (21, 30, "21-30 días"),
    (31, 9999, "30+ días"),
]

RANGOS_ATASCADOS = [
    (3, 7, "3-7 días"),
    (8, 15, "8-15 días"),
    (16, 30, "16-30 días"),
    (31, 9999, "30+ días"),
]

# --- Columnas esperadas del Excel ---
COLUMNAS_REQUERIDAS = [
    "FECHA DE REPORTE",
    "ID",
    "FECHA",
    "TELÉFONO",
    "ESTATUS",
    "CIUDAD DESTINO",
    "TRANSPORTADORA",
    "TOTAL DE LA ORDEN",
    "GANANCIA",
    "PRECIO FLETE",
    "COSTO DEVOLUCION FLETE",
    "PRECIO PROVEEDOR",
    "PRODUCTO",
    "CANTIDAD",
    "FECHA GUIA GENERADA",
]

# Columnas monetarias (truncar decimales con floor)
COLUMNAS_MONETARIAS = [
    "TOTAL DE LA ORDEN",
    "PRECIO FLETE",
    "COSTO DEVOLUCION FLETE",
    "GANANCIA",
    "PRECIO PROVEEDOR",
    "PRECIO PROVEEDOR X CANTIDAD",
]
