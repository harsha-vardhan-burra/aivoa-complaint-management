import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class RiskAssessmentBase(BaseModel):
    """AI-generated decision support. Kept structurally separate from
    ComplaintBase so risk is never presented as an extracted fact.

    confidence and recommended_action were added during frontend/backend
    reconciliation ahead of Phase 6: both are genuine AI decision-support
    signals the UI surfaces to QA reviewers, not extracted complaint
    facts, so they belong here rather than on ComplaintBase.
    """

    severity: Optional[str] = None
    rationale: Optional[str] = None
    missing_fields: List[str] = []
    confidence: Optional[float] = None
    confidence_factors: Optional[List[str]] = None
    recommended_action: Optional[str] = None


class RiskAssessmentCreate(RiskAssessmentBase):
    complaint_id: uuid.UUID


class RiskAssessmentResponse(RiskAssessmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    complaint_id: uuid.UUID
    created_at: datetime
