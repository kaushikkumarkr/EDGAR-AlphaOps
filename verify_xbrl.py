
import time
from pipelines.tasks import reconcile_daily_task, download_filing, process_filing_task
from pipelines.models import Filing, Fact, FilingState
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)

def verify_xbrl():
    print("🚀 Triggering Reconcile Task (20240103)...")
    # Date with known filings
    # master.20240103.idx
    try:
        res = reconcile_daily_task.apply(args=["20240103"]).get()
        print(f"✅ {res}")
    except Exception as e:
        print(f"❌ Reconcile Failed: {e}")
        return

    session = Session()
    # Pick one 10-K or 10-Q preferred, but any is fine for test
    filing = session.query(Filing).filter(Filing.form_type.in_(['10-K', '10-Q'])).first()
    
    if not filing:
        print("⚠️ No 10-K/Q found in reconciled data. Using any filing.")
        filing = session.query(Filing).first()
        
    if not filing:
        print("❌ No filings found at all.")
        return

    print(f"Dataset Item: {filing.accession_number} ({filing.form_type})")
    
    # Trigger Download
    print("🚀 Triggering Download...")
    download_filing.delay(filing.accession_number)
    
    # Wait
    print("⏳ Waiting 30s for download...")
    time.sleep(30)
    
    session.refresh(filing)
    if filing.state != FilingState.DOWNLOADED:
        print(f"❌ Download failed or pending. State: {filing.state}")
        # Force retry?
        return

    # Trigger Process
    print("🚀 Triggering XBRL/Process Task...")
    process_filing_task.delay(filing.accession_number)
    
    print("⏳ Waiting 20s for processing...")
    time.sleep(20)
    
    # Check Facts
    fact_count = session.query(Fact).filter_by(filing_accession=filing.accession_number).count()
    print(f"📊 Facts Extracted: {fact_count}")
    
    if fact_count > 0:
        facts = session.query(Fact).filter_by(filing_accession=filing.accession_number).limit(5).all()
        for f in facts:
            print(f"  - {f.concept}: {f.value} {f.unit}")
        print("✅ XBRL Pipeline Verified.")
    else:
        print("⚠️ No facts extracted. (Maybe not XBRL or parser issue)")

if __name__ == "__main__":
    verify_xbrl()
