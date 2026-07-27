import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Float, Uuid
from sqlalchemy.orm import relationship

from app.db.database import Base


class RiskAssessment(Base):
    """AI-generated risk/decision-support record tied to a complaint.

    Kept as its own table (rather than columns on Complaint) so that
    risk assessment stays conceptually and structurally separate from
    extracted complaint facts, per PROJECT_CONTEXT.md section 7.2.
    """

    __tablename__ = "risk_assessments"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(
        Uuid(as_uuid=True), ForeignKey("complaints.id"), nullable=False
    )

    severity = Column(String, nullable=True)
    rationale = Column(Text, nullable=True)
    missing_fields = Column(JSON, nullable=True, default=list)
    confidence = Column(Float, nullable=True)
    recommended_action = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    complaint = relationship("Complaint", back_populates="risk_assessments")
