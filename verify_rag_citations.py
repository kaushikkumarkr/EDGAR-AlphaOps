from agents.tools import search_sec_docs
from agents.tools import get_rag_components

# Force initialization
store, embedder = get_rag_components()

query = "What are the risk factors for Apple?"
result = search_sec_docs.invoke({"query": query})

print("Query:", query)
print("Result Snippet:\n", result[:500])

if "[Source: AAPL" in result or "[Source: Apple" in result or "10-K" in result:
    print("\n✅ Citation format verified.")
else:
    print("\n❌ Citation format NOT found.")
