from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class EvidenceItem(BaseModel):
    type: str  # "paper" | "trial" | "moa" | "safety"
    id: str
    title: Optional[str] = None
    snippet: Optional[str] = None
    url: Optional[str] = None
    year: Optional[int] = None
    source: Optional[str] = None

class SafetyInfo(BaseModel):
    boxed_warning: bool = False
    highlights: List[str] = []

class Candidate(BaseModel):
    rank: int
    drug: str
    synonyms: List[str] = []
    ids: Dict[str, str] = {}
    mechanism: Optional[str] = None
    score: float
    kpis: Dict[str, Any]
    safety: SafetyInfo
    evidence: List[EvidenceItem] = []

class SearchFilters(BaseModel):
    min_phase: int = 0
    exclude_boxed_warnings: bool = False
    route: str = "any"
    include_off_label: bool = True

class SearchResponse(BaseModel):
    query: str
    disease_canonical: str
    filters_applied: SearchFilters
    results: List[Candidate] = []
    disclaimer: str = Field(default=(
        "Research prototype for educational use. Not medical advice. "
        "Verify with full texts and clinical experts."
    ))
