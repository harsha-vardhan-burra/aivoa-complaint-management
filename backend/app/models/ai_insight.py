import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Uuid
from sqlalchemy.orm import relationship

from app.db.database import Base


class ComplaintAIInsight(Base):
    """Stores AI-generated decision-support artifacts separate from complaint facts.

    Decision-support signals (root-cause suggestions, CAPA suggestions,
    summaries, duplicate match explanations) must be stored separately
    from factual complaint data, matching the pattern used for RiskAssessment.
    """

    __tablename__ = "complaint_ai_insights"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(
        Uuid(as_uuid=True), ForeignKey("complaints.id"), nullable=False
    )
    insight_type = Column(String, nullable=False)  # "root_cause" | "capa" | "summary" | "duplicate_check"
    payload = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    complaint = relationship("Complaint", back_populates="ai_insights")
