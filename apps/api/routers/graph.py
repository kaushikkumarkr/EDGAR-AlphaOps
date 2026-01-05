
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pipelines.graph.builder import GraphBuilder
from pipelines.tasks import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/graph/network")
def get_network_graph(db: Session = Depends(get_db)):
    """
    Returns the Knowledge Graph in Node-Link JSON format.
    Suitable for D3.js or Cytoscape visualization.
    """
    builder = GraphBuilder(db)
    # Rebuilds on request for now (caching would be better for prod)
    # Limiting to small number for speed
    builder.build_graph(limit=20) 
    return builder.get_network_json()
