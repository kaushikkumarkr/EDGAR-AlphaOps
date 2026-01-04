import streamlit as st
import logging
from langchain_core.messages import HumanMessage, AIMessage
from agents.graph import app as agent_app

# Page Config
st.set_page_config(page_title="EDGAR AlphaOps", page_icon="📈", layout="wide")

st.title("📈 EDGAR AlphaOps Analyst")
st.markdown("Ask about financials, risks, or market data for US public companies.")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.markdown(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(msg.content)

# User Input
if prompt := st.chat_input("Enter your question (e.g., 'How is AAPL revenue growing?'):"):
    # Add user message to history
    user_msg = HumanMessage(content=prompt)
    st.session_state.messages.append(user_msg)
    with st.chat_message("user"):
        st.markdown(prompt)

    # Agent Execution
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Prepare state
        # We pass entire history? Or just recent?
        # LangGraph state expects 'messages'
        state_input = {"messages": st.session_state.messages}
        
        try:
            # Stream events if possible, or just invoke
            # For simplicity in Sprint 5, just invoke.
            final_state = agent_app.invoke(state_input)
            last_msg = final_state['messages'][-1]
            
            full_response = last_msg.content
            message_placeholder.markdown(full_response)
            
            # Save assistant message
            st.session_state.messages.append(last_msg)
            
        except Exception as e:
            st.error(f"Error: {e}")
            logging.error(f"Agent failed: {e}")
