from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.complaint import Complaint
from app.models.risk_assessment import RiskAssessment
from app.schemas.complaint import SaveComplaintRequest, ComplaintResponse

router = APIRouter()


@router.post(
    "/complaints",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_complaint(
    payload: SaveComplaintRequest,
    db: Session = Depends(get_db),
):
    """Create and persist a new complaint record along with any genuine AI risk assessment.

    Both are persisted transactionally in a single DB session commit.
    Validates that at least one meaningful complaint field is provided.
    Unknown fields remain null.
    """
    complaint_data = payload.complaint
    meaningful_fields = [
        complaint_data.complaint_source,
        complaint_data.customer_name,
        complaint_data.product_name,
        complaint_data.product_strength_grade,
        complaint_data.batch_number,
        complaint_data.manufacturing_date,
        complaint_data.expiry_date,
        complaint_data.quantity_affected,
        complaint_data.complaint_type,
        complaint_data.complaint_date,
        complaint_data.detailed_complaint_description,
        complaint_data.initial_severity,
        complaint_data.priority,
    ]
    if not any(field is not None for field in meaningful_fields):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaint must contain at least one meaningful field. All fields cannot be null.",
        )

    try:
        db_complaint = Complaint(
            complaint_source=complaint_data.complaint_source,
            customer_name=complaint_data.customer_name,
            product_name=complaint_data.product_name,
            product_strength_grade=complaint_data.product_strength_grade,
            batch_number=complaint_data.batch_number,
            manufacturing_date=complaint_data.manufacturing_date,
            expiry_date=complaint_data.expiry_date,
            quantity_affected=complaint_data.quantity_affected,
            complaint_type=complaint_data.complaint_type,
            complaint_date=complaint_data.complaint_date,
            detailed_complaint_description=complaint_data.detailed_complaint_description,
            initial_severity=complaint_data.initial_severity,
            priority=complaint_data.priority,
        )

        db.add(db_complaint)
        db.flush()

        # Check if genuine AI risk assessment is present
        risk_data = payload.risk_assessment
        if risk_data and any(
            v is not None
            for v in [
                risk_data.severity,
                risk_data.rationale,
                risk_data.confidence,
                risk_data.recommended_action,
            ]
        ):
            db_risk = RiskAssessment(
                complaint_id=db_complaint.id,
                severity=risk_data.severity,
                rationale=risk_data.rationale,
                missing_fields=risk_data.missing_fields,
                confidence=risk_data.confidence,
                recommended_action=risk_data.recommended_action,
            )
            db.add(db_risk)

        db.commit()
        db.refresh(db_complaint)

        return db_complaint

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist complaint: {str(e)}",
        )