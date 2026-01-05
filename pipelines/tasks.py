
import logging
from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_settings
from pipelines.models import Base, Filing, FilingState
from pipelines.sec.client import SecClient
from pipelines.storage import MinIOClient
import feedparser
from datetime import datetime
from pipelines.reconcile import Reconciler
from pipelines.parse.xbrl import XBRLParser
from pipelines.models import Base, Filing, FilingState, Fact, Company
from pipelines.market.stooq import StooqClient
from pipelines.features import FeatureStore
from pipelines.rag.chunker import Chunker
from pipelines.rag.embedder import Embedder
from pipelines.rag.store import VectorBooster
from pipelines.analytics.event_study import EventStudy

logger = logging.getLogger(__name__)
settings = get_settings()

celery_app = Celery(
    "edgar_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Database Setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Ensure tables exist (Migration logic typically handled by Alembic, but verified here for sprint)
Base.metadata.create_all(bind=engine)

@celery_app.task
def ingest_rss_feed():
    """Fetches SEC RSS Feed and creates Filing entries."""
    url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&company=&dateb=&owner=include&start=0&count=40&output=atom"
    client = SecClient()
    
    logger.info(f"Fetching RSS: {url}")
    try:
        # We bypass rate limit for RSS? No, strict complaince tells us to respect it everywhere.
        resp = client.get(url) 
        feed = feedparser.parse(resp.content)
        
        session = SessionLocal()
        new_count = 0
        
        for entry in feed.entries:
            # Parse Accession (typically in ID or Summary)
            # Entry ID format: urn:tag:sec.gov,2008:accession-number
            # Accession is the last part
            accession = entry.id.split(":")[-1]
            title = entry.title
            
            # Parse Link
            # Atom feed entry has link href
            link = entry.link
            
            # Check if exists
            exists = session.query(Filing).filter_by(accession_number=accession).first()
            if not exists:
                filing = Filing(
                    accession_number=accession,
                    # title=title, 
                    filed_at=datetime.utcnow(), 
                    url=link,
                    state=FilingState.PENDING
                )
                session.add(filing)
                new_count += 1
                
                # Trigger download task
                download_filing.delay(accession)
        
        session.commit()
        session.close()
        logger.info(f"RSS Ingest Complete. New Filings: {new_count}")
        return new_count
        
    except Exception as e:
        logger.error(f"RSS Ingest Failed: {e}")
        raise

@celery_app.task(bind=True, max_retries=3)
def download_filing(self, accession: str):
    """Downloads raw filing text and saves to MinIO."""
    logger.info(f"Downloading Filing: {accession}")
    session = SessionLocal()
    filing = session.query(Filing).filter_by(accession_number=accession).first()
    
    if not filing:
        session.close()
        return "Filing not found in DB"
        
    client = SecClient()
    storage = MinIOClient()
    
    client = SecClient()
    storage = MinIOClient()
    
    try:
        # Download
        # The RSS link is usually the index page. We want the full text.
        # Often the text file is at .txt instead of -index.htm
        # Link: https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/0000320193-23-000106-index.htm
        # Text: https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/0000320193-23-000106.txt
        
        # Simple heuristic replace
        txt_url = filing.url.replace("-index.htm", ".txt").replace("-index.html", ".txt")
        
        resp = client.get(txt_url)
        content = resp.content
        
        # Save to MinIO
        key = f"edgar/{accession}/raw.txt"
        storage.put_object(key, content)
        
        filing.state = FilingState.DOWNLOADED
        filing.s3_path = key
        session.commit()
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        filing.state = FilingState.FAILED
        session.commit()
        raise e
    finally:
        session.close()

    return f"Downloaded {accession}"

@celery_app.task
def reconcile_daily_task(date_str: str):
    """Daily Task to reconcile index."""
    session = SessionLocal()
    try:
        reconciler = Reconciler(session)
        count = reconciler.reconcile_date(date_str)
        session.close()
        return f"Reconciled {count} new filings for {date_str}"
    except Exception as e:
        session.close()
        raise e

@celery_app.task
def process_filing_task(accession: str):
    """Parses downloaded filing and extracts XBRL facts."""
    session = SessionLocal()
    filing = session.query(Filing).filter_by(accession_number=accession).first()
    
    if not filing or filing.state != FilingState.DOWNLOADED: # Only process downloaded
        session.close()
        return "Not ready"
        
    storage = MinIOClient()
    parser = XBRLParser()
    
    try:
        # Get Content
        content = storage.get_object(filing.s3_path)
        
        # Parse
        facts_data = parser.parse(content)
        
        # Save Facts
        for item in facts_data:
            fact = Fact(
                filing_accession=accession,
                concept=item['concept'],
                value=item['value'],
                unit=item['unit']
                # period logic needs context map
            )
            session.add(fact)
            
        filing.state = FilingState.PROCESSED
        session.commit()
        
    except Exception as e:
        logger.error(f"Processing Failed {accession}: {e}")
        # filing.state = FilingState.FAILED # Optional: specific process fail state or just retry
        raise e
    finally:
        session.close()
        
    return f"Processed {len(facts_data)} facts"

@celery_app.task
def ingest_market_data_task(tickers: list[str]):
    """Ingests daily OHLC from Stooq for a list of tickers."""
    client = StooqClient()
    results = {}
    for ticker in tickers:
        try:
            success = client.download_daily_ohlc(ticker)
            results[ticker] = "Success" if success else "No Data"
        except Exception as e:
            results[ticker] = f"Failed: {e}"
    return results

@celery_app.task
def build_features_task():
    """Rebuilds feature store using DuckDB."""
    try:
        store = FeatureStore()
        store.build_financial_ratios()
        return "Features Rebuilt Successfully"
    except Exception as e:
        logger.error(f"Build Features Failed: {e}")
        raise

@celery_app.task
def ingest_rag_task(accession: str):
    """
    RAG Ingestion Pipeline:
    1. Fetch full text from MinIO.
    2. Chunk text with citations.
    3. Embed chunks.
    4. Store in Qdrant.
    """
    session = SessionLocal()
    filing = session.query(Filing).filter_by(accession_number=accession).first()
    
    if not filing or not filing.s3_path:
        session.close()
        return "Filing not ready/found"
        
    storage = MinIOClient()
    chunker = Chunker()
    embedder = Embedder() # Uses all-MiniLM-L6-v2 by default
    vb = VectorBooster()
    
    try:
        # 1. Get Text (Assuming raw.txt is text)
        # TODO: clean html if needed, but for now treat as raw text
        content_bytes = storage.get_object(filing.s3_path)
        text = content_bytes.decode("utf-8", errors="ignore")
        
        # 2. Chunk
        metadata = {
            "accession": accession,
            "cik": filing.cik,
            "form": filing.form_type,
            "date": str(filing.filed_at.date()) if filing.filed_at else ""
        }
        chunks_meta = chunker.chunk(text, metadata)
        
        if not chunks_meta:
            return "No text extracted"
            
        # 3. Embed
        texts = [c["text"] for c in chunks_meta]
        embeddings = embedder.embed_texts(texts)
        
        # 4. Upsert
        # chunks_meta already contains 'text' and offsets.
        vb.upsert_batch(embeddings, chunks_meta)
        
    except Exception as e:
        logger.error(f"RAG Ingest Failed {accession}: {e}")
        raise e
    finally:
        session.close()
        
    return f"Ingested {len(chunks_meta)} chunks to Qdrant"

@celery_app.task
def calculate_car_task(accession: str):
    """Calculates CAR for a filing."""
    session = SessionLocal()
    try:
        study = EventStudy(session)
        result = study.calculate_car(accession)
        return result
    except Exception as e:
        logger.error(f"Event Study Failed {accession}: {e}")
        raise e
    finally:
        session.close()
