import uuid
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.complaint import ComplaintBase
from app.schemas.risk_assessment import RiskAssessmentBase


class ComplaintSummary(BaseModel):
    """Plain-language executive summary and key factual bullet points."""

    summary: str
    key_facts: List[str] = Field(default_factory=list, max_length=5)


class ComplaintSummaryRequest(BaseModel):
    """Request payload for on-demand complaint summary."""

    complaint: ComplaintBase


class AIInsightResponse(BaseModel):
    """Serialized representation of a persisted AI decision-support insight."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    insight_type: str
    payload: dict
    created_at: datetime


class DuplicateMatch(BaseModel):
    """Candidate duplicate match detected deterministically."""

    complaint_id: uuid.UUID
    confidence: str  # "high" | "medium" | "low"
    reason: str
    similarity: Optional[float] = None
    explanation: Optional[str] = None
    created_at: Optional[datetime] = None
    product_name: Optional[str] = None
    batch_number: Optional[str] = None


class DuplicateCheckRequest(BaseModel):
    """Request payload for duplicate detection."""

    complaint: ComplaintBase
    window_days: int = 90
    include_explanation: bool = False


class DuplicateCheckResponse(BaseModel):
    """Response containing deterministic candidate duplicates."""

    matches: List[DuplicateMatch] = []


class RootCauseSuggestion(BaseModel):
    """AI-proposed initial root cause hypothesis and investigation steps.

    Decision-support suggestion only; not an approved RCA finding.
    """

    hypothesis: str
    contributing_factors: List[str] = Field(default_factory=list, max_length=5)
    confidence: Literal["low", "medium", "high"]
    recommended_investigation_steps: List[str] = Field(
        default_factory=list, max_length=5
    )


class RootCauseRequest(BaseModel):
    """Request payload for root cause hypothesis recommendation."""

    complaint: ComplaintBase
    risk: Optional[RiskAssessmentBase] = None


class CapaSuggestion(BaseModel):
    """AI-suggested corrective and preventive action proposal.

    Decision-support suggestion only; not an approved CAPA record.
    """

    corrective_actions: List[str] = Field(default_factory=list, max_length=5)
    preventive_actions: List[str] = Field(default_factory=list, max_length=5)
    rationale: str


class CapaRequest(BaseModel):
    """Request payload for CAPA suggestion."""

    complaint: ComplaintBase
    risk: RiskAssessmentBase
    root_cause: Optional[RootCauseSuggestion] = None
