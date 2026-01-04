from pipelines.rag.store import VectorBooster
from config import get_settings
from qdrant_client import QdrantClient

def reset_collection():
    settings = get_settings()
    client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    collection_name = "sec_filings"
    
    print(f"Deleting collection {collection_name}...")
    client.delete_collection(collection_name)
    print("Collection deleted.")
    
    # Re-init to recreate empty
    vb = VectorBooster(collection_name)
    print("Collection recreated.")

if __name__ == "__main__":
    reset_collection()
