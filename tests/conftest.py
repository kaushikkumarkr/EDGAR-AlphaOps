
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pipelines.models import Base

@pytest.fixture(scope="function")
def db_session():
    from sqlalchemy.pool import StaticPool
    # In-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
