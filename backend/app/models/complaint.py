import uuid
from datetime import date, datetime

from sqlalchemy import Column, String, Date, Numeric, DateTime, Text, Uuid
from sqlalchemy.orm import relationship

from app.db.database import Base


class Complaint(Base):
    """Persistent structured complaint record.

    Every field is nullable by design: extraction must preserve
    unknown information as unknown rather than fabricating values
    (see PROJECT_CONTEXT.md, Data Integrity Rule 1).
    """

    __tablename__ = "complaints"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    complaint_source = Column(String, nullable=True)
    customer_name = Column(String, nullable=True)

    product_name = Column(String, nullable=True)
    product_strength_grade = Column(String, nullable=True)
    batch_number = Column(String, nullable=True)
    manufacturing_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    quantity_affected = Column(Numeric, nullable=True)

    complaint_type = Column(String, nullable=True)
    complaint_date = Column(Date, nullable=True)
    detailed_complaint_description = Column(Text, nullable=True)

    initial_severity = Column(String, nullable=True)
    priority = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    risk_assessments = relationship(
        "RiskAssessment",
        back_populates="complaint",
        cascade="all, delete-orphan",
    )

