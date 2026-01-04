from lakehouse.db import Database
import pandas as pd

def check_data():
    db = Database()
    conn = db.get_connection()
    tables = ["companies", "filings", "xbrl_facts", "prices", "features"]
    
    print(">>> Lakehouse Stats <<<")
    for t in tables:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"{t}: {count} rows")
        except Exception as e:
            print(f"{t}: Error ({e})")
            
    conn.close()

if __name__ == "__main__":
    check_data()
