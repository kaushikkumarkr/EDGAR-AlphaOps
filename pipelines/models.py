from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, ForeignKey, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime

Base = declarative_base()

class FilingState(str, enum.Enum):
    PENDING = "PENDING"
    DOWNLOADED = "DOWNLOADED"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

class Filing(Base):
    __tablename__ = "filings"

    accession_number = Column(String, primary_key=True)
    cik = Column(String, index=True)
    form_type = Column(String, index=True)
    filed_at = Column(DateTime(timezone=True), index=True)
    url = Column(String, nullable=True)
    
    # State tracking
    state = Column(SQLEnum(FilingState), default=FilingState.PENDING)
    s3_path = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Filing {self.accession_number} ({self.form_type})>"

class Fact(Base):
    __tablename__ = "facts"

    id = Column(Integer, primary_key=True, index=True)
    filing_accession = Column(String, index=True) # FK to Filing.accession_number ideally, but loose coupling ok for now
    concept = Column(String, index=True) # e.g. us-gaap:Assets
    value = Column(String) # Store as string to preserve precision/formatting initially? Or Decimal.
    unit = Column(String) # USD, shares
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FilingAnalysis(Base):
    __tablename__ = "filing_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    filing_accession = Column(String, unique=True, index=True) # One analysis per filing
    alpha = Column(Float)
    beta = Column(Float)
    car_2d = Column(Float) # [-2, +2] window
    car_5d = Column(Float) # [-5, +5] window
    risk_score = Column(Float, nullable=True) # 0-100
    volatility_annual = Column(Float, nullable=True) # Annualized Vol
    r_squared = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Company(Base):
    __tablename__ = "companies"
    
    cik = Column(String, primary_key=True)
    ticker = Column(String, index=True, nullable=True)
    company_name = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())



