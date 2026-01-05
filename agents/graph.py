from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from agents.state import AgentState
from agents.tools import get_financial_metrics, search_sec_docs, search_knowledge_graph
from config import get_settings

settings = get_settings()

# Tools list
tools = [get_financial_metrics, search_sec_docs, search_knowledge_graph]

# Model
# We need an OpenAI compatible model.
# Using local MLX Server (Llama-3.2-3B-Instruct-4bit or similar)
llm = ChatOpenAI(
    base_url=settings.OPENAI_BASE_URL,
    api_key=settings.OPENAI_API_KEY,
    model=settings.MODEL_NAME, 
    temperature=0
) 

llm_with_tools = llm.bind_tools(tools)

# Nodes
import json
from langchain_core.messages import AIMessage, SystemMessage

def agent_node(state: AgentState):
    messages = state['messages']
    
    # Prepend System Prompt if not present
    if not isinstance(messages[0], SystemMessage):
        system_prompt = SystemMessage(content="""You are an expert financial agent named 'AlphaOps'.
        You have access to the following tools:
        1. `search_sec_docs`: For specific claims, facts, segments in SEC filings (10-K, 10-Q).
        2. `get_financial_metrics`: For quantitative data like Cumulative Abnormal Returns (CAR), Risk (VaR), and Volatility Regimes.
        3. `search_knowledge_graph`: For exploring relationships between entities (People, Companies, Risks), management structure, and conflicts.
        
        ROUTER LOGIC:
        - If asked about "risk numbers", "impact", "returns", or "volatility", USE `get_financial_metrics`.
        - If asked about "relationships", "conflicts", "who works with who", or "entity connections", USE `search_knowledge_graph`.
        - If asked about specific text, policies, or detailed facts in filings, USE `search_sec_docs`.
        - If the query is complex, you can call multiple tools in sequence.
        
        Always cite your sources efficiently.
        """)
        messages = [system_prompt] + messages
    
    # Trace with Langfuse if configured
    callbacks = []
    if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
        try:
            from langfuse.langchain import CallbackHandler
            langfuse_handler = CallbackHandler(
                public_key=settings.LANGFUSE_PUBLIC_KEY
            )
            callbacks.append(langfuse_handler)
        except ImportError:
            pass
        
    response = llm_with_tools.invoke(messages, config={"callbacks": callbacks})
    
    # Patch: If local LLM returns raw JSON string instead of tool_calls
    import re
    raw_content = response.content.strip()
    # Regex to strip all <|...|> tokens and markdown code blocks
    clean_content = re.sub(r'<\|.*?\|>', '', raw_content)
    clean_content = clean_content.replace("```json", "").replace("```", "").strip()
    
    if not response.tool_calls and clean_content.startswith("{") and "name" in clean_content:
        try:
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
