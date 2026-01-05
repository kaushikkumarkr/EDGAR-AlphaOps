
import logging
import time
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from agents.graph import app
from config import get_settings

# Load env vars
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_agent_trace():
    settings = get_settings()
    logger.info("🚀 Verification via Agent + CallbackHandler")
    
    # Initialize Handler without args (uses env vars) or with public_key
    from langfuse.langchain import CallbackHandler
    handler = CallbackHandler(public_key=settings.LANGFUSE_PUBLIC_KEY)
    
    logger.info("📡 Invoking Agent...")
    try:
        response = app.invoke(
            {"messages": [HumanMessage(content="What is the stock price of AAPL?")]},
            config={"callbacks": [handler]}
        )
        logger.info("✅ Agent execution completed.")
        
        logger.info("⏳ Sleeping 5s to allow async background flush...")
        time.sleep(5)
        
        logger.info("👉 Please check your Langfuse Dashboard for a new trace.")
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        raise e

if __name__ == "__main__":
    verify_agent_trace()
