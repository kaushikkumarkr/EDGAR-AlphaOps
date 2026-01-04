from langchain_core.messages import HumanMessage
from agents.graph import app
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)

def test_financial_query():
    print(">>> Testing Financial Query (SQL Tool)...")
    inputs = {"messages": [HumanMessage(content="What was the revenue and net margin for AAPL in the last period?")]}
    result = app.invoke(inputs)
    
    last_msg = result["messages"][-1]
    print(f"Agent Response:\n{last_msg.content}")
    
    if "revenue" in last_msg.content.lower() or "margin" in last_msg.content.lower():
        print("✅ Financial Query Passed")
    else:
        print("❌ Financial Query Failed (Check logic)")

def test_rag_query():
    print("\n>>> Testing RAG Query (Vector Tool)...")
    # Using AVAH since we indexed it in Sprint 4
    inputs = {"messages": [HumanMessage(content="What does AVAH (Aveanna Healthcare) say about risks?")]}
    result = app.invoke(inputs)
    
    last_msg = result["messages"][-1]
    print(f"Agent Response:\n{last_msg.content}")
    
    if "risk" in last_msg.content.lower() or "aveanna" in last_msg.content.lower() or "documents" in last_msg.content.lower():
        print("✅ RAG Query Passed")
    else:
        print("❌ RAG Query Failed (Check logic)")

if __name__ == "__main__":
    try:
        test_financial_query()
        test_rag_query()
    except Exception as e:
        print(f"❌ Test Failed with Exception: {e}")
        exit(1)
