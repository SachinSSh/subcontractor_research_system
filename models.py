from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Optional, Any
from datetime import datetime

class Subcontractor(BaseModel):
    """Model representing a researched subcontractor"""
    name: str
    website: str
    email: Optional[str] = None
    phone_number: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    lic_active: Optional[bool] = None
    lic_number: Optional[str] = None
    bond_amount: Optional[int] = None
    tx_projects_past_5yrs: Optional[int] = None
    score: int
    evidence_url: str
    evidence_text: str
    last_checked: str  # ISO date string

class ResearchRequest(BaseModel):
    """Model for research job requests"""
    trade: str
    city: str
    state: str
    min_bond: int
    keywords: List[str] = []

class ResearchResults(BaseModel):
    """Model for research job results"""
    subcontractors: List[Subcontractor]

class ResearchJob(BaseModel):
    """Model for a complete research job"""
    job_id: str
    status: str  # QUEUED, PROCESSING, SUCCEEDED, FAILED
    request: ResearchRequest
    created_at: datetime
    completed_at: Optional[datetime] = None
    results: Optional[ResearchResults] = None
    error: Optional[str] = None
