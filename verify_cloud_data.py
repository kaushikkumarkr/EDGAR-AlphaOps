
import logging
from dotenv import load_dotenv
from config import get_settings
from lakehouse.db import Database
from pipelines.rag.store import VectorBooster

# Load env vars
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_cloud():
    settings = get_settings()
    print("="*40)
    print("☁️  CLOUD DATA VERIFICATION")
    print("="*40)
    
    # 1. SQL (MotherDuck)
    print("\n1️⃣  SQL LAYER")
    if settings.MOTHERDUCK_TOKEN:
        print(f"✅ MotherDuck Token found: {settings.MOTHERDUCK_TOKEN[:5]}...")
        try:
            db = Database()
            conn = db.get_connection()
            res = conn.execute("SELECT 'Hello MotherDuck'").fetchall()
            print(f"✅ Connection Success! Result: {res}")
            conn.close()
        except Exception as e:
            print(f"❌ MotherDuck Connection Failed: {e}")
    else:
        print("⚠️  No MOTHERDUCK_TOKEN found. Using Local DuckDB.")
        
    # 2. Vector (Qdrant)
    print("\n2️⃣  VECTOR LAYER")
    if settings.QDRANT_API_KEY:
        print(f"✅ Qdrant API Key found.")
        print(f"Target Host: {settings.QDRANT_HOST}")
        try:
            vb = VectorBooster()
            colls = vb.client.get_collections()
            print(f"✅ Connection Success! Collections: {len(colls.collections)}")
        except Exception as e:
            print(f"❌ Qdrant Cloud Connection Failed: {e}")
    else:
        print("⚠️  No QDRANT_API_KEY found. Using Local Qdrant.")

if __name__ == "__main__":
    verify_cloud()
