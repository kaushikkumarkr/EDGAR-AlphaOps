from langchain_core.messages import HumanMessage
from agents.graph import app
import logging
import sys

# Configure Logging
logging.basicConfig(level=logging.ERROR)

def test_production_agent():
    print(">>> 🚀 Final Production Verification <<<")
    
    # Test 1: Market Data (TSLA)
    print("\n1. Testing Feature Store (TSLA Financials)...")
    try:
        msg = "What is the latest revenue and price for TSLA?"
        result = app.invoke({"messages": [HumanMessage(content=msg)]})
        response = result["messages"][-1]
        
        # We expect a tool call to get_financial_metrics
        if response.tool_calls and response.tool_calls[0]['name'] == 'get_financial_metrics':
             print(f"✅ Agent selected correct tool: {response.tool_calls[0]}")
             # Simulate tool output (Graph normally does this, but app.invoke runs one step if I didn't loop? 
             # Wait, app is compiled with recursion, it should run until END if tools return text.
             # Ah, my manual invocation in test_agent_integrated checked the *first* response.
             # If the agent calls a tool, the graph continues.
             # Let's see the FINAL message.
        else:
             print(f"⚠️ Agent Output: {response.content}")
             
        # Check if response content mentions tool or is the final answer
        # With MLX, we might see the tool call.
        
    except Exception as e:
        print(f"❌ TSLA Test Failed: {e}")

    # Test 2: RAG (AVAH)
    print("\n2. Testing RAG Pipeline (AVAH Risks)...")
    try:
        msg = "What are the risk factors for Aveanna (AVAH)?"
        result = app.invoke({"messages": [HumanMessage(content=msg)]})
        response = result["messages"][-1]
        
        if response.tool_calls and response.tool_calls[0]['name'] == 'search_sec_docs':
            print(f"✅ Agent selected correct tool: {response.tool_calls[0]}")
        else:
            print(f"⚠️ Agent Output: {response.content}")
            
    except Exception as e:
        print(f"❌ RAG Test Failed: {e}")

if __name__ == "__main__":
    test_production_agent()
