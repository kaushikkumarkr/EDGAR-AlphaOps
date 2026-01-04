from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from agents.state import AgentState
from agents.tools import get_financial_metrics, search_sec_docs
from config import get_settings

settings = get_settings()

# Tools list
tools = [get_financial_metrics, search_sec_docs]

# Model
# We need an OpenAI compatible model.
# If using local model (e.g. vLLM serving standard OpenAI API), we set base_url.
# But settings has SEC_USER_AGENT, not LLM config explicitly yet.
# Assuming env vars OPENAI_API_KEY and OPENAI_BASE_URL are set or defaults used.
# For this Sprint, we assume User has OpenAI key or local compatible setup.
# We will use 'gpt-4o' or 'gpt-3.5-turbo' as default if not local.
# Using local MLX Server (Llama-3.2-3B-Instruct-4bit or similar)
llm = ChatOpenAI(
    base_url="http://localhost:8080/v1",
    api_key="EMPTY",
    model="mlx-community/Llama-3.2-3B-Instruct-4bit", # Model name is illustrative for logging
    temperature=0
) 
# Ideally load from settings.

llm_with_tools = llm.bind_tools(tools)

# Nodes
import json
from langchain_core.messages import AIMessage

def agent_node(state: AgentState):
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    
    # Patch: If local LLM returns raw JSON string instead of tool_calls
    content = response.content.strip()
    if not response.tool_calls and content.startswith("{") and "name" in content:
        try:
            # Clean up potential artifacts
            clean_content = content.replace("<|eom_id|>", "").replace("<|eot_id|>", "").replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_content)
            if "name" in data and "parameters" in data:
                # Reconstruct tool call
                response.tool_calls = [{
                    "name": data["name"],
                    "args": data["parameters"],
                    "id": "call_" + data["name"]
                }]
                # Clear content to avoid confusion but keep for debugging if needed
                # response.content = "" 
        except Exception as e:
            # fallback or log error
            pass 

    return {"messages": [response]}

def should_continue(state: AgentState) -> Literal["tools", END]:
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# Graph Construction
workflow = StateGraph(AgentState)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
)

workflow.add_edge("tools", "agent")

app = workflow.compile()
