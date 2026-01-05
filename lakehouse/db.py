import duckdb
from config import get_settings
from pathlib import Path
import logging

class Database:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.db_path = Path(self.settings.DATA_DIR) / "lakehouse.duckdb"
        self._ensure_db_dir()
    
    def _ensure_db_dir(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """
        Returns a DuckDB connection. 
        Supports local file or MotherDuck (md:) if token provided.
        """
        if self.settings.MOTHERDUCK_TOKEN:
            # Connect to MotherDuck
            # We assume edgar_alphaops database
            return duckdb.connect(f"md:edgar_alphaops?motherduck_token={self.settings.MOTHERDUCK_TOKEN}")
        
        return duckdb.connect(str(self.db_path))

    def init_schema(self) -> None:
        """
        Applies all schema files in lakehouse/schemas/ to the database.
        """
        conn = self.get_connection()
        schema_dir = Path(__file__).parent / "schemas"
        try:
            for sql_file in schema_dir.glob("*.sql"):
                logging.info(f"Applying schema: {sql_file.name}")
                with open(sql_file, "r") as f:
                    conn.execute(f.read())
            logging.info("Lakehouse schema initialized.")
        except Exception as e:
            logging.error(f"Failed to init schema: {e}")
            raise
        finally:
            conn.close()

if __name__ == "__main__":
    # verification run
    from observability.logging import setup_logging
    setup_logging()
    db = Database()
    db.init_schema()
