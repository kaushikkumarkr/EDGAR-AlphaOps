
import os
import logging
import requests
import json
from dotenv import load_dotenv

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_langfuse")
load_dotenv()

def mask(s):
    return s[:4] + "..." + s[-4:] if s and len(s) > 8 else "MISSING"

def run_diagnostics():
    print("="*50)
    print("🕵️ LANGFUSE DEEP DIAGNOSTICS")
    print("="*50)

    # 1. ENV VAR CHECK
    pk = os.getenv("LANGFUSE_PUBLIC_KEY")
    sk = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    print("\n1️⃣  ENVIRONMENT VARIABLES")
    print(f"LANGFUSE_PUBLIC_KEY: {mask(pk)}")
    print(f"LANGFUSE_SECRET_KEY: {mask(sk)}")
    print(f"LANGFUSE_HOST:       {host}")
    
    if not pk or not sk:
        print("❌ CRITICAL: Keys are missing from environment.")
        return

    # 2. NETWORK CHECK (Raw HTTP)
    print("\n2️⃣  NETWORK CONNECTIVITY")
    try:
        health_url = f"{host.rstrip('/')}/api/public/health"
        print(f"Pinging {health_url}...")
        res = requests.get(health_url, timeout=5)
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.text}")
        if res.status_code == 200:
            print("✅ Connectivity OK")
        else:
            print("⚠️ Connectivity Warning: Non-200 response")
    except Exception as e:
        print(f"❌ Network Error: {e}")

    # 3. SDK INSPECTION
    print("\n3️⃣  SDK INSPECTION")
    try:
        import langfuse
        print(f"langfuse version: {getattr(langfuse, '__version__', 'unknown')}")
        print(f"langfuse file: {langfuse.__file__}")
        
        from langfuse import Langfuse
        print(f"Langfuse class: {Langfuse}")
        client = Langfuse()
        print(f"Client attributes: {dir(client)}")
        
        # 4. TRACE ATTEMPT
        print("\n4️⃣  TRACE ATTEMPT (Core SDK)")
        if hasattr(client, 'trace'):
            trace = client.trace(name="debug-trace-deep")
            print("Trace object created.")
            span = trace.span(name="debug-span")
            span.end()
            trace.update(output="success")
            print("Trace updated.")
            
            print("Flushing...")
            client.flush()
            print("Flush called.")
        else:
            print("❌ Client has no 'trace' method. SDK might be corrupted or incompatible.")

    except ImportError:
        print("❌ Could not import langfuse.")
    except Exception as e:
        print(f"❌ SDK Error: {e}")

if __name__ == "__main__":
    run_diagnostics()
