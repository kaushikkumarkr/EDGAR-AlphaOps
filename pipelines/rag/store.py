import logging
import uuid
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from config import get_settings

settings = get_settings()

class VectorBooster:
    def __init__(self, collection_name: str = "sec_filings", embedding_dim: int = 384):
        if settings.QDRANT_API_KEY:
            # Cloud Connection
            self.client = QdrantClient(
                url=settings.QDRANT_HOST, 
                api_key=settings.QDRANT_API_KEY
            )
        else:
            # Local Connection
            self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
            
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            logging.info(f"Creating collection {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=self.embedding_dim, distance=models.Distance.COSINE)
            )

    def upsert_batch(self, vectors: List[List[float]], payloads: List[Dict[str, Any]]):
        """
        Upsert a batch of vectors + metadata.
        """
        if not vectors:
            return

        points = [
            models.PointStruct(
                id=str(uuid.uuid4()), # Unique ID for chunk
                vector=v,
                payload=p
            )
            for v, p in zip(vectors, payloads)
        ]
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logging.info(f"Upserted {len(points)} chunks to Qdrant.")

    def search(self, vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=limit
        ).points
        return [
            {"score": hit.score, "text": hit.payload.get("text"), "metadata": hit.payload}
            for hit in results
        ]
