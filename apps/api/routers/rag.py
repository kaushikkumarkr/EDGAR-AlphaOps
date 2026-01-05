
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from pipelines.rag.embedder import Embedder
from pipelines.rag.store import VectorBooster

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    
class SearchResponse(BaseModel):
    query: str
    results: List[dict]

@router.post("/ask", response_model=SearchResponse)
async def ask(req: SearchRequest):
    """
    Semantic Search Endpoint.
    Returns parsed chunks with citations.
    """
    try:
        # Init components (lazy load or dependency inject ideally)
        embedder = Embedder() 
        vb = VectorBooster()
        
        # 1. Embed Query
        # embed_texts expects list, returns list of list
        query_vec = embedder.embed_texts([req.query])[0]
        
        # 2. Search Qdrant
        hits = vb.search(query_vec, limit=req.limit)
        
        # 3. Format Response
        formatted_results = []
        for hit in hits:
            meta = hit["metadata"]
            citation = f"[Source: {meta.get('accession')} ({meta.get('form')}) Start:{meta.get('start_index')}]"
            formatted_results.append({
                "text": hit["text"],
                "score": hit["score"],
                "citation": citation,
                "metadata": meta
            })
            
        return SearchResponse(query=req.query, results=formatted_results)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
