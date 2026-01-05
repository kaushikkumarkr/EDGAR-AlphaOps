
from fastapi import APIRouter, HTTPException, Depends
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pipelines.models import FilingAnalysis
# from apps.api.main import get_db # Circular import avoided

router = APIRouter()

# Simple dependency if not exported
from pipelines.tasks import SessionLocal
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/analytics/filing/{accession}")
def get_filing_analytics(accession: str, db: Session = Depends(get_db)):
    """Get CAR analysis for a filing."""
    analysis = db.query(FilingAnalysis).filter_by(filing_accession=accession).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    return {
        "accession": accession,
        "alpha": analysis.alpha,
        "beta": analysis.beta,
        "car_2d": analysis.car_2d,
        "car_2d": analysis.car_2d,
        "car_5d": analysis.car_5d,
        "risk_score": analysis.risk_score,
        "volatility": analysis.volatility_annual
    }
