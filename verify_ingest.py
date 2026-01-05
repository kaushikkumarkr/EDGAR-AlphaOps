
import time
from pipelines.tasks import ingest_rss_feed, download_filing
from pipelines.models import Filing, FilingState
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)

def verify_ingest():
    print("🚀 Triggering RSS Ingest Task...")
    # Run synchronously for test
    # Note: If executed from outside container, it might fail to reach Redis if ports not exposed/networked identically 
    # BUT localhost mapping should work.
    # However, 'client.get' inside task might hit connection issues if not inside container? 
    # No, 'SecClient' uses 'requests', so it runs from wherever python runs.
    
    try:
        count = ingest_rss_feed.apply().get() # Execute locally inline
        print(f"✅ Ingested {count} filings from RSS.")
    except Exception as e:
        print(f"❌ Ingest Failed: {e}")
        return

    # Check DB
    session = Session()
    filings = session.query(Filing).all()
    print(f"📊 Total Filings in DB: {len(filings)}")
    
    if len(filings) > 0:
        f = filings[0]
        print(f"🔍 Sample Filing: {f.accession_number} | State: {f.state} | Link: {f.url}")
        
        if f.state == FilingState.PENDING:
            print("⚠️ Filing is PENDING. Retrying download manually...")
            download_filing.delay(f.accession_number)
        
        print("⏳ Waiting 30s for Celery Worker to process download...")
        time.sleep(30)
        
        # Refresh
        session.refresh(f)
        print(f"🔍 Post-Wait State: {f.state} | S3 Path: {f.s3_path}")
        
        if f.state == FilingState.DOWNLOADED:
             print("✅ Download SUCCESS via Celery.")
        else:
             print("⚠️ Download PENDING/FAILED. Check worker logs.")

if __name__ == "__main__":
    verify_ingest()
