
import time
import requests
from pipelines.tasks import ingest_rag_task
from pipelines.models import Filing, FilingState
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)

def verify_rag():
    print("🚀 Triggering RAG Ingest for a sample downloaded filing...")
    
    session = Session()
    # Find a downloaded filing
    filing = session.query(Filing).filter(Filing.state == FilingState.DOWNLOADED).first()
    
    if not filing:
         # Try PROCESSED as well
        filing = session.query(Filing).filter(Filing.state == FilingState.PROCESSED).first()
        
    if not filing:
        print("❌ No DOWNLOADED/PROCESSED filing found to ingest.")
        return

    print(f"Target: {filing.accession_number}")
    ingest_rag_task.delay(filing.accession_number)
    
    print("⏳ Waiting 30s for embedding/indexing...")
    time.sleep(30)
    
    # Test API
    print("🚀 Testing /ask API...")
    url = "http://localhost:8000/api/v1/ask"
    query = {"query": "assets", "limit": 2}
    
    try:
        resp = requests.post(url, json=query)
        resp.raise_for_status()
        data = resp.json()
        print("✅ API Response Received:")
        for res in data["results"]:
            print(f"  - Score: {res['score']:.4f}")
            print(f"  - Citation: {res['citation']}")
            print(f"  - Snippet: {res['text'][:100]}...")
    except Exception as e:
        print(f"❌ API Request Failed: {e}")
        if resp:
            print(resp.text)

if __name__ == "__main__":
    verify_rag()
