import streamlit as st
import json
import os

from agent.agent_builder import get_agent

# Leer la plantilla HTML solo una vez
with open("interface.html", "r", encoding="utf-8") as f:
    MAP_TEMPLATE = f.read()

st.set_page_config(page_title="AI Travel Planner 🌍", layout="wide")

st.title("🌍 AI Travel Planner")
st.write("Plan your perfect trip with AI-generated itineraries, maps, and recommendations.")

# Cargar AGENTE solo una vez
agent_executor = get_agent()

# Inicializar historial de mensajes
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar historial
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "map_data_str" in msg and msg["map_data_str"]:
            with st.expander("🗺️ View Discovery Map"):
                html_with_data = MAP_TEMPLATE.replace("%JSON_DATA%", msg["map_data_str"])
                st.components.v1.html(html_with_data, height=600, scrolling=False)

# Entrada del usuario
if query := st.chat_input("Which city would you like to explore? (e.g. 'a cheap plan for Rome')"):

    # Guardar y mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Procesar con el agente
    with st.chat_message("assistant"):
        with st.spinner("Researching and building your plan..."):

            response = agent_executor.invoke({"input": query})

            text_response = response.get("output", "I couldn't generate a response.")

            map_data_str = None
            if "intermediate_steps" in response and response["intermediate_steps"]:
                last_action, tool_output = response["intermediate_steps"][-1]

                if (
                    last_action.tool in [
                        "create_enriched_discovery_plan",
                        "create_budget_focused_plan",
                        "create_interest_focused_plan"
                    ]
                    and isinstance(tool_output, str)
                    and tool_output.strip().startswith("{")
                ):
                    map_data_str = tool_output

            st.markdown(text_response, unsafe_allow_html=True)

            if map_data_str:
                with st.expander("🗺️ View Discovery Map", expanded=True):
                    html_with_data = MAP_TEMPLATE.replace("%JSON_DATA%", map_data_str)
                    st.components.v1.html(html_with_data, height=600, scrolling=False)

            st.session_state.messages.append({
                "role": "assistant",
                "content": text_response,
                "map_data_str": map_data_str
            })
