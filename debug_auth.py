
import os
import logging
from dotenv import load_dotenv
from langfuse import Langfuse

logging.basicConfig(level=logging.INFO)
load_dotenv()

def check_auth():
    print("🕵️ Checking Langfuse Auth...")
    try:
        langfuse = Langfuse()
        
        # Check Auth
        print("Calling auth_check()...")
        is_valid = langfuse.auth_check()
        
        if is_valid:
            print("✅ Auth Valid! Keys are correct.")
        else:
            print("❌ Auth Failed. Keys are invalid or project not found.")
            
    except Exception as e:
        print(f"❌ Error during auth check: {e}")

if __name__ == "__main__":
    check_auth()
