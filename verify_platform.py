
import os
import requests
import psycopg2
import redis
import boto3
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("platform-verify")

def verify_postgres():
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="postgres",
            dbname="edgar_ops"
        )
        conn.close()
        logger.info("✅ Postgres: Connected")
        return True
    except Exception as e:
        logger.error(f"❌ Postgres: Failed - {e}")
        return False

def verify_redis():
    try:
        r = redis.Redis(host="localhost", port=6379)
        if r.ping():
            logger.info("✅ Redis (Valkey): Ping Success")
            return True
    except Exception as e:
        logger.error(f"❌ Redis: Failed - {e}")
        return False

def verify_minio():
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url="http://localhost:9000",
            aws_access_key_id="minioadmin",
            aws_secret_access_key="minioadmin"
        )
        s3.list_buckets()
        logger.info("✅ MinIO: Connected")
        return True
    except Exception as e:
        logger.error(f"❌ MinIO: Failed - {e}")
        return False

def verify_api():
    try:
        res = requests.get("http://localhost:8000/health")
        if res.status_code == 200:
            logger.info(f"✅ API: {res.json()}")
            return True
        else:
            logger.error(f"❌ API: Status {res.status_code}")
            return False
    except Exception as e:
        # API might take a moment to start
        logger.error(f"❌ API: Connection Error - {e}")
        return False

def verify_phoenix():
    try:
        res = requests.get("http://localhost:6006")
        if res.status_code == 200:
            logger.info("✅ Phoenix: UI Accessible")
            return True
        else:
            logger.error(f"❌ Phoenix: Status {res.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Phoenix: Connection Error - {e}")
        return False

def run_all():
    print("="*40)
    print("🧬 PLATFORM HEALTH CHECK")
    print("="*40)
    pg = verify_postgres()
    rd = verify_redis()
    mn = verify_minio()
    ph = verify_phoenix()
    ap = verify_api()
    
    if all([pg, rd, mn, ph, ap]):
        print("\n🚀 ALL SYSTEMS NOMINAL. READY FOR SPRINT 1.")
    else:
        print("\n⚠️ SOME SYSTEMS FAILED.")

if __name__ == "__main__":
    run_all()
