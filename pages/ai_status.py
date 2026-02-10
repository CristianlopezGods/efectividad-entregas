"""Página: Clasificación IA de Estatus Desconocidos."""

import streamlit as st
from data_processing.classifier import get_unknown_statuses, classify_with_ai, apply_ai_classifications


def render(df):
    """Renderiza la página de clasificación IA."""
    st.subheader("Clasificación IA de Estatus")

    unknown = get_unknown_statuses(df)

    if not unknown:
        st.success("No hay estatus desconocidos. Todos fueron clasificados por reglas.")
        return

    st.warning(f"Se encontraron **{len(unknown)}** estatus no reconocidos:")

    for s in unknown:
        count = len(df[df["ESTATUS"] == s])
        st.write(f"- **{s}** ({count} órdenes)")

    st.divider()

    # Input para API key
    api_key = st.text_input(
        "API Key de Claude (Anthropic)",
        type="password",
        value=st.session_state.get("anthropic_api_key", ""),
        help="Ingresa tu API key de Anthropic para clasificar estatus con IA",
    )

    if api_key:
        st.session_state["anthropic_api_key"] = api_key

    if st.button("Clasificar con IA", disabled=not api_key):
        with st.spinner("Clasificando estatus con Claude..."):
            results = classify_with_ai(unknown, api_key)

        if results:
            st.success("Clasificación completada:")

            # Mostrar resultados
            for estatus, categoria in results.items():
                count = len(df[df["ESTATUS"] == estatus])
                st.write(f"- **{estatus}** → {categoria} ({count} órdenes)")

            # Guardar en session state para aplicar
            st.session_state["ai_classifications"] = results
            st.info("Las clasificaciones se aplicarán al recargar los datos. Usa el botón de abajo.")

            if st.button("Aplicar Clasificaciones"):
                st.session_state["apply_ai"] = True
                st.rerun()
        else:
            st.error("No se obtuvieron resultados de la IA.")

    # Historial
    if "ai_classifications" in st.session_state and st.session_state["ai_classifications"]:
        st.divider()
        st.subheader("Historial de Clasificaciones IA")
        for estatus, categoria in st.session_state["ai_classifications"].items():
            st.write(f"- **{estatus}** → {categoria}")
