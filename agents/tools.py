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
        context += f"--- [Ticker: {t_ticker}, Score: {score:.2f}] ---\n{text}\n\n"
        
    if not context:
        return "No relevant SEC documents found."
        
    return context
