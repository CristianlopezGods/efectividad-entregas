"""Página: Consejero IA — Análisis y recomendaciones con Claude."""

import streamlit as st


def _build_data_summary(df):
    """Construye un resumen de datos para enviar al modelo."""
    from data_processing.analyzer import (
        get_pnl_general,
        get_product_profitability,
        get_city_profitability,
        get_carrier_analysis,
        get_general_metrics,
    )

    metrics = get_general_metrics(df)
    pnl = get_pnl_general(df)
    products = get_product_profitability(df)
    cities = get_city_profitability(df)
    carriers = get_carrier_analysis(df)

    # Top 15 productos perdiendo
    prod_perdiendo = products[products["Rentabilidad Real"] < 0].head(15)
    prod_perdiendo_text = ""
    for _, r in prod_perdiendo.iterrows():
        prod_perdiendo_text += (
            f"  - {r['PRODUCTO']}: {r['Envíos']} envíos, "
            f"{r['Entregas']} entregas, {r['Devoluciones']} devs, "
            f"Ganancia=${r['Ganancia Entregas']:,}, "
            f"Pérdida=${r['Pérdida Devoluciones']:,}, "
            f"Rentabilidad=${r['Rentabilidad Real']:,}\n"
        )

    # Top 10 productos ganando
    prod_ganando = products[products["Rentabilidad Real"] >= 0].sort_values(
        "Rentabilidad Real", ascending=False
    ).head(10)
    prod_ganando_text = ""
    for _, r in prod_ganando.iterrows():
        prod_ganando_text += (
            f"  - {r['PRODUCTO']}: {r['Envíos']} envíos, "
            f"Rentabilidad=${r['Rentabilidad Real']:,}, "
            f"Rent/Envío=${r['Rent/Envío']:,}\n"
        )

    # Ciudades NO ENVIAR
    cities_no = cities[cities["Veredicto"] == "NO ENVIAR"].head(15)
    cities_no_text = ""
    for _, r in cities_no.iterrows():
        cities_no_text += (
            f"  - {r['CIUDAD DESTINO']}: {r['Envíos']} envíos, "
            f"{r['Devoluciones']} devs, {r['% Devolución']}% dev, "
            f"Rentabilidad=${r['Rentabilidad']:,}\n"
        )

    # Ciudades PRECAUCIÓN
    cities_prec = cities[cities["Veredicto"] == "PRECAUCIÓN"].head(10)
    cities_prec_text = ""
    for _, r in cities_prec.iterrows():
        cities_prec_text += (
            f"  - {r['CIUDAD DESTINO']}: {r['Envíos']} envíos, "
            f"{r['% Devolución']}% dev, Rentabilidad=${r['Rentabilidad']:,}\n"
        )

    # Top ciudades rentables
    cities_ok = cities[cities["Veredicto"] == "OK"].sort_values(
        "Rentabilidad", ascending=False
    ).head(10)
    cities_ok_text = ""
    for _, r in cities_ok.iterrows():
        cities_ok_text += (
            f"  - {r['CIUDAD DESTINO']}: {r['Envíos']} envíos, "
            f"{r['% Devolución']}% dev, Rentabilidad=${r['Rentabilidad']:,}\n"
        )

    # Transportadoras
    carrier_text = ""
    if not carriers.empty:
        for _, r in carriers.iterrows():
            carrier_text += (
                f"  - {r['Transportadora']}: {r['Envíos']} envíos, "
                f"{r['% Éxito']}% éxito, {r['% Devolución']}% dev, "
                f"Rentabilidad=${r['Rentabilidad']:,}\n"
            )

    # Conteos generales
    n_prod_perdiendo = len(products[products["Rentabilidad Real"] < 0])
    n_prod_ganando = len(products[products["Rentabilidad Real"] >= 0])
    n_cities_no = len(cities[cities["Veredicto"] == "NO ENVIAR"])
    n_cities_prec = len(cities[cities["Veredicto"] == "PRECAUCIÓN"])
    perdida_evitable_cities = int(
        cities[cities["Veredicto"] == "NO ENVIAR"]["Pérdida"].sum()
    ) if n_cities_no > 0 else 0
    perdida_evitable_prod = int(
        products[products["Rentabilidad Real"] < 0]["Pérdida Devoluciones"].sum()
    ) if n_prod_perdiendo > 0 else 0

    summary = f"""=== RESUMEN DEL NEGOCIO (DROPSHIPPING COLOMBIA - VEYNORI STORE) ===

MÉTRICAS GENERALES:
- Total órdenes: {metrics['total_ordenes']:,}
- Envíos reales (con guía): {metrics['envios_reales']:,}
- Entregados: {metrics['entregados']:,}
- Devoluciones: {metrics['devoluciones']:,}
- En proceso: {metrics['en_proceso']:,}
- Nunca enviados: {metrics['nunca_enviados']:,}
- Guías demoradas: {metrics['guia_demorada']:,}
- Tasa de éxito: {metrics['tasa_exito']:.1%}
- Tasa de devolución: {metrics['tasa_devolucion']:.1%}
- Flete promedio: ${metrics['flete_promedio']:,}
- Pérdida total por devoluciones (flete): ${metrics['perdida_total']:,}

P&L (GANANCIAS Y PÉRDIDAS):
- Ventas brutas (entregas): ${pnl['ventas_brutas']:,}
- Costo producto: ${pnl['costo_producto']:,}
- Flete entregas: ${pnl['flete_entregados']:,}
- Flete devoluciones (pérdida): ${pnl['flete_devueltos']:,}
- Flete en tránsito: ${pnl['flete_en_transito']:,}
- Venta neta (sin publicidad): ${pnl['venta_neta']:,}
- Utilidad entregas (R-T-Y): ${pnl['utilidad_entregas']:,}
- Pedidos en tránsito: {pnl['proy_en_transito']:,}
- Utilidad proyectada si todo se entrega: ${pnl['proy_utilidad_total']:,}

PRODUCTOS ({n_prod_perdiendo} perdiendo, {n_prod_ganando} ganando):
Top productos PERDIENDO dinero:
{prod_perdiendo_text}
Top productos GANANDO dinero:
{prod_ganando_text}
Pérdida evitable en productos no rentables: ${perdida_evitable_prod:,}

CIUDADES ({n_cities_no} NO ENVIAR, {n_cities_prec} PRECAUCIÓN):
Ciudades donde NO conviene enviar (rentabilidad negativa):
{cities_no_text}
Ciudades en PRECAUCIÓN (>30% devolución pero rentables):
{cities_prec_text}
Top ciudades RENTABLES:
{cities_ok_text}
Pérdida evitable en ciudades NO ENVIAR: ${perdida_evitable_cities:,}

TRANSPORTADORAS:
{carrier_text}"""

    return summary


def render(df):
    """Renderiza la página de Consejero IA."""
    st.subheader("Consejero IA")
    st.caption(
        "Analiza tus datos con inteligencia artificial y recibe recomendaciones "
        "accionables para mejorar tu negocio de dropshipping"
    )

    # API key
    api_key = st.text_input(
        "API Key de Claude (Anthropic)",
        type="password",
        value=st.session_state.get("anthropic_api_key", ""),
        help="Ingresa tu API key de Anthropic para recibir análisis con IA",
        key="ai_advisor_key",
    )
    if api_key:
        st.session_state["anthropic_api_key"] = api_key

    # Gasto publicitario opcional
    gasto_pub = st.number_input(
        "Gasto en publicidad (opcional, para incluir en el análisis)",
        min_value=0,
        value=st.session_state.get("gasto_pub_advisor", 0),
        step=100000,
        format="%d",
        key="gasto_pub_ia",
    )
    st.session_state["gasto_pub_advisor"] = gasto_pub

    # Pregunta personalizada
    pregunta = st.text_area(
        "Pregunta específica (opcional)",
        placeholder="Ej: ¿Debería pausar los drones? ¿Qué ciudades eliminar primero? ¿Cómo mejorar mi margen?",
        key="ai_advisor_question",
    )

    st.divider()

    if st.button("Analizar y Aconsejar", disabled=not api_key, type="primary"):
        with st.spinner("Recopilando datos del negocio..."):
            data_summary = _build_data_summary(df)

        pub_context = ""
        if gasto_pub > 0:
            from data_processing.analyzer import get_pnl_general
            pnl = get_pnl_general(df)
            rent_final = pnl["venta_neta"] - gasto_pub
            roas = pnl["ventas_brutas"] / gasto_pub if gasto_pub > 0 else 0
            pub_context = f"""
PUBLICIDAD:
- Gasto en publicidad: ${gasto_pub:,}
- Rentabilidad final (después de publicidad): ${rent_final:,}
- ROAS: {roas:.1f}x
- {"PERDIENDO DINERO con publicidad incluida" if rent_final < 0 else "Ganando con publicidad incluida"}
"""

        question_context = ""
        if pregunta:
            question_context = f"\n\nPREGUNTA ESPECÍFICA DEL USUARIO:\n{pregunta}\n"

        prompt = f"""Eres un consultor experto en dropshipping y e-commerce en Colombia.
Analiza los siguientes datos de la tienda "Veynori Store" que opera en la plataforma Dropi.

{data_summary}
{pub_context}
{question_context}

INSTRUCCIONES:
1. Da un DIAGNÓSTICO GENERAL del negocio (2-3 párrafos)
2. Lista las ACCIONES INMEDIATAS (productos a pausar, ciudades a bloquear)
3. Da RECOMENDACIONES ESTRATÉGICAS para mejorar rentabilidad
4. Si hay pregunta específica del usuario, respóndela con datos concretos
5. Usa números y datos específicos del resumen para respaldar cada recomendación
6. Sé directo y práctico — el usuario necesita acciones concretas, no teoría

Responde en español. Usa formato markdown con headers ##, bullets, y **negritas** para resaltar lo importante."""

        with st.spinner("Claude está analizando tu negocio..."):
            try:
                from anthropic import Anthropic

                client = Anthropic(api_key=api_key)
                response = client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}],
                )
                advice = response.content[0].text

                # Guardar en session state
                st.session_state["ai_advice"] = advice
                st.session_state["ai_advice_question"] = pregunta

            except Exception as e:
                st.error(f"Error al consultar la IA: {e}")
                return

    # Mostrar resultado (persistente en session)
    if "ai_advice" in st.session_state and st.session_state["ai_advice"]:
        st.divider()
        if st.session_state.get("ai_advice_question"):
            st.caption(f"Pregunta: {st.session_state['ai_advice_question']}")
        st.markdown(st.session_state["ai_advice"])

        # Botón para copiar
        st.divider()
        st.download_button(
            "Descargar Recomendaciones",
            st.session_state["ai_advice"].encode("utf-8"),
            "recomendaciones_ia.md",
            "text/markdown",
        )
