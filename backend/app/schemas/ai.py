from typing import List, Optional

from pydantic import BaseModel

from app.schemas.complaint import ComplaintBase
from app.schemas.risk_assessment import RiskAssessmentBase


class ProcessComplaintRequest(BaseModel):
    """Request body for POST /api/ai/complaints/process (Phase 5/6).

    current_complaint carries what the frontend already knows so the
    backend can merge a patch into it rather than re-extracting a
    brand-new complaint on every message (non-destructive editing,
    PROJECT_CONTEXT.md section 14).
    """

    message: str
    current_complaint: Optional[ComplaintBase] = None


class ProcessComplaintResponse(BaseModel):
    """Response body for POST /api/ai/complaints/process.

    complaint, risk, and missing_fields are kept as separate top-level
    fields -- extraction, risk assessment, and missing information are
    distinct concepts that must not be conflated (section 7.2/7.3).
    """

    complaint: ComplaintBase
    risk: Optional[RiskAssessmentBase] = None
    missing_fields: List[str] = []
