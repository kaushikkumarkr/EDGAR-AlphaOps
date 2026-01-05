
import time
import requests
from pipelines.tasks import ingest_market_data_task, calculate_car_task
from pipelines.models import Filing, FilingState
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)

def verify_event_study():
    print("🚀 Triggering Market Data Ingest (SPY & AAPL)...")
    ingest_market_data_task.delay("SPY")
    ingest_market_data_task.delay("AAPL")
    
    print("⏳ Waiting 15s for market data...")
    time.sleep(15)
    
    # Use the filing we worked on previously
    session = Session()
    filing = session.query(Filing).filter_by(accession_number="0001213900-24-000769").first()
    
    # NOTE: The filing date for this accession might be recent (2024).
    # Stooq AAPL/SPY data needs to cover [-120 days] window relative to filing date.
    # Stooq usually has daily updates.
    
    if not filing:
        print("❌ Sample filing 0001213900-24-000769 not found.")
        # Try finding ANY filing
        filing = session.query(Filing).first()
        if not filing:
            print("❌ No filings in DB.")
            return

    print(f"🚀 Calculating CAR for {filing.accession_number} (Date: {filing.filed_at})...")
    # For MVP logic, we hardcoded Ticker=AAPL inside EventStudy.
    # So we are effectively calculating "How AAPL price reacted to this filing date"
    # Even if the filing isn't AAPL. This is acceptable for pipeline test.
    
    calculate_car_task.delay(filing.accession_number)
    
    print("⏳ Waiting 10s for analysis...")
    time.sleep(10)
    
    
    # Check API
    url = f"http://localhost:8000/api/v1/analytics/filing/{filing.accession_number}"
    resp = None
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        print("✅ Analysis Result:")
        print(f"  - Alpha: {data['alpha']:.4f}")
        print(f"  - Beta: {data['beta']:.4f}")
        print(f"  - CAR (2d): {data['car_2d']:.4f}")
    except Exception as e:
        print(f"❌ Analysis Verification Failed: {e}")
        if resp:
            print(resp.text)

if __name__ == "__main__":
    verify_event_study()
