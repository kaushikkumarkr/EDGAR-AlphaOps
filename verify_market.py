
import time
from pipelines.tasks import ingest_market_data_task
from pipelines.storage import MinIOClient
from io import BytesIO
import pandas as pd

def verify_market():
    ticker = "AAPL"
    print(f"🚀 Triggering Market Ingest for {ticker}...")
    
    # Run inline or via celery
    try:
        # We can run the function logic directly if local env has deps, 
        # BUT StooqClient needs MinIO, which is localhost mapped.
        # Let's try celery delay and wait.
        ingest_market_data_task.delay(ticker)
    except Exception as e:
        print(f"Failed to trigger: {e}")
        return

    print("⏳ Waiting 10s...")
    time.sleep(10)
    
    # Check MinIO
    client = MinIOClient()
    key = f"market/{ticker.lower()}.csv"
    try:
        data = client.get_object(key)
        df = pd.read_csv(BytesIO(data))
        print(f"✅ Downloaded {ticker} Data. Rows: {len(df)}")
        print(df.head())
    except Exception as e:
        print(f"❌ Failed to verify MinIO data: {e}")

if __name__ == "__main__":
    verify_market()
