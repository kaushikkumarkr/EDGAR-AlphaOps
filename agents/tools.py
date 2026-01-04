from typing import List, Optional
from langchain_core.tools import tool
from lakehouse.db import Database
from pipelines.rag.store import VectorBooster
from pipelines.rag.embedder import Embedder
import pandas as pd

# Global instances for tools to reuse
_db = Database()
_store = None
_embedder = None

def get_rag_components():
    global _store, _embedder
    if _store is None:
        _store = VectorBooster()
    if _embedder is None:
        _embedder = Embedder()
    return _store, _embedder

@tool
def get_financial_metrics(ticker: str, period_year: Optional[int] = None) -> str:
    """
    Get financial metrics (Revenue, Net Income, Margins, Growth) for a company from the features table.
    Use this for questions about financials, numbers, growth, or stock performance.
    """
    conn = _db.get_connection()
    try:
        query = f"""
            SELECT asof_date, revenue_ttm, net_income_ttm, revenue_growth_yoy, net_margin, price_close 
            FROM features 
            WHERE ticker = ? 
            ORDER BY asof_date DESC LIMIT 5
        """
        if period_year:
            # Simple filter if year provided, but generally showing recent history is better
            pass
            
        df = conn.execute(query, [ticker.upper()]).fetchdf()
        if df.empty:
            return f"No financial data found for {ticker}. Try ingesting market/XBRL data."
        
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Error querying financials: {e}"
    finally:
        conn.close()

@tool
def search_sec_docs(query: str, ticker: Optional[str] = None) -> str:
    """
    Search SEC filings for qualitative information, risk factors, management discussion, etc.
    Use this for questions about "risks", "strategy", "why", "management", "AI", "litigation".
    """
    store, embedder = get_rag_components()
    
    # Embed query
    vector = embedder.embed_texts([query])[0]
    
    # Search
    # TODO: Filter by ticker if provided (Qdrant filter)
    # For now, global search or simple limit
    
    results = store.search(vector, limit=3)
    
    context = ""
    for r in results:
        meta = r['metadata']
        text = r['text']
        score = r['score']
        t_ticker = meta.get('ticker', 'Unknown')
        filing_date = meta.get('filing_date', 'N/A')
        form = meta.get('form', 'Doc')
        # V2 Requirement: [Source: Filename (Frame)] or similar
        # We'll use: [Source: {Form} {Date} (Score: {score:.2f})]
        context += f"--- [Source: {t_ticker} {form} {filing_date} | Score: {score:.2f}] ---\n{text}\n\n"
        
    if not context:
        return "No relevant SEC documents found."
        
    return context

@tool
def search_knowledge_graph(query_entities: str) -> str:
    """
    Search the knowledge graph for relationships between entities.
    Input should be a comma-separated list of entity names (e.g. "Apple, Tim Cook, Risk").
    Use this for questions about "relationships", "entities", "connections", or "graph".
    """
    from rag.graphrag.retriever import GraphRetriever
    retriever = GraphRetriever()
    
    # Clean input
    entities = [e.strip() for e in query_entities.split(",")]
    return retriever.retrieve_context(entities)

@tool
def get_financial_metrics(ticker: str) -> str:
    """
    Get calculated financial metrics (Event Study CAR, Risk VaR, Volatility Regime) for a ticker.
    Use this when asked about "risk", "impact", "abnormal returns", "volatility", or "metrics".
    """
    conn = Database().get_connection()
    try:
        # 1. Event Study (Latest)
        es_res = conn.execute(f"SELECT event_date, car_value, alpha, beta FROM event_studies WHERE ticker='{ticker}' ORDER BY event_date DESC LIMIT 1").fetchdf()
        
        # 2. Risk Metrics (Latest)
        rm_res = conn.execute(f"SELECT asof_date, volatility_regime, var_95, cvar_95 FROM risk_metrics WHERE ticker='{ticker}' ORDER BY asof_date DESC LIMIT 1").fetchdf()
        
        output = []
        if not es_res.empty:
            r = es_res.iloc[0]
            output.append(f"Event Study (Date: {r['event_date']}): CAR={r['car_value']:.4f}, Alpha={r['alpha']:.4f}, Beta={r['beta']:.4f}")
        
        if not rm_res.empty:
            r = rm_res.iloc[0]
            output.append(f"Risk Metrics (Date: {r['asof_date']}): Regime={r['volatility_regime']}, VaR95={r['var_95']:.2%}, CVaR95={r['cvar_95']:.2%}")
            
        if not output:
             return "No calculated metrics found. Please run 'compute-ds' or 'compute-risk' first."
             
        return "\n".join(output)
    finally:
        conn.close()
