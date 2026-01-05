
import logging
import time
from dotenv import load_dotenv
from langfuse import Langfuse

logging.basicConfig(level=logging.INFO)
load_dotenv()

def verify_span_creation():
    print("🕵️ Attempting Span Creation via start_span()...")
    try:
        langfuse = Langfuse()
        
        # Try start_span (which might create a trace implicitly or require a trace_id)
        # Note: In some versions, start_span starts a span in the current trace context or new one.
        print("Calling start_span()...")
        span = langfuse.start_span(name="manual-verification-span")
        
        print("Ending span...")
        span.end()
        
        print("Flushing...")
        langfuse.flush()
        print("✅ Flush complete. Check Dashboard for 'manual-verification-span'.")
            
    except Exception as e:
        print(f"❌ Error during span creation: {e}")

if __name__ == "__main__":
    verify_span_creation()
