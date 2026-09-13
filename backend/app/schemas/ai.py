from typing import List, Optional

from pydantic import BaseModel

from app.schemas.complaint import ComplaintBase
from app.schemas.risk_assessment import RiskAssessmentBase


class ProcessComplaintRequest(BaseModel):
    """Request body for POST /api/ai/complaints/process (Phase 5/6/7).

    current_complaint carries what the frontend already knows so the
    backend can merge a patch into it rather than re-extracting a
    brand-new complaint on every message (non-destructive editing).
    current_risk carries the existing risk assessment so no-op messages
    can preserve risk state without re-querying Groq.
    """

    message: str
    current_complaint: Optional[ComplaintBase] = None
    current_risk: Optional[RiskAssessmentBase] = None


class CompletenessResult(BaseModel):
    """Deterministic score and missing field breakdown for complaint intake."""

    score: int
    missing_critical: List[str] = []
    missing_optional: List[str] = []
    ready_to_submit: bool = False


class ProcessComplaintResponse(BaseModel):
    """Response body for POST /api/ai/complaints/process.

    complaint, risk, missing_fields, and changed_fields are returned
    as top-level fields for frontend synchronization and UI feedback.
    completeness provides a weighted score and breakdown of critical
    vs. optional missing fields.
    """

    complaint: ComplaintBase
    risk: Optional[RiskAssessmentBase] = None
    missing_fields: List[str] = []
    changed_fields: List[str] = []
    completeness: Optional[CompletenessResult] = None

