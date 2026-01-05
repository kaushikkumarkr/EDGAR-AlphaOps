
import pytest
from unittest.mock import MagicMock, patch
from pipelines.rag.chunker import Chunker
from pipelines.rag.store import VectorBooster
from apps.api.routers.rag import ask, SearchRequest

def test_chunker_offsets():
    chunker = Chunker(chunk_size=10, chunk_overlap=0)
    text = "Hello World This Is A Test"
    # "Hello Worl" (10 chars), "d This Is " ...
    
    chunks = chunker.chunk(text, {"doc_id": "1"})
    
    assert len(chunks) > 0
    first = chunks[0]
    assert "start_index" in first
    assert first["start_index"] == 0
    assert first["text"] == text[:len(first["text"])]
    
    # Verify offset correctness
    for c in chunks:
        start = c["start_index"]
        end = c["end_index"]
        assert text[start:end] == c["text"]

def test_vector_booster_upsert():
    with patch("pipelines.rag.store.QdrantClient") as MockClient:
        mock_qdrant = MagicMock()
        MockClient.return_value = mock_qdrant
        
        vb = VectorBooster()
        vectors = [[0.1, 0.2]]
        payloads = [{"text": "foo"}]
        
        vb.upsert_batch(vectors, payloads)
        
        mock_qdrant.upsert.assert_called_once()
        
@pytest.mark.anyio
async def test_ask_endpoint_citations():
    # Mock components
    with patch("apps.api.routers.rag.Embedder") as MockEmbedder, \
         patch("apps.api.routers.rag.VectorBooster") as MockVB:
             
        mock_embed = MagicMock()
        mock_embed.embed_texts.return_value = [[0.1, 0.2]] # query vec
        MockEmbedder.return_value = mock_embed
        
        mock_vb = MagicMock()
        # Mock search result
        mock_hit = {
            "score": 0.9, 
            "text": "Answer Text", 
            "metadata": {"accession": "001", "form": "10-K", "start_index": 100}
        }
        mock_vb.search.return_value = [mock_hit]
        MockVB.return_value = mock_vb
        
        req = SearchRequest(query="Question")
        resp = await ask(req)
        
        assert len(resp.results) == 1
        res = resp.results[0]
        assert "citation" in res
        # Check strict format [Source: {accession} ({form}) Start:{offset}]
        assert res["citation"] == "[Source: 001 (10-K) Start:100]"
