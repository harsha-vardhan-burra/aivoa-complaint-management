"""Deterministic duplicate detection service for customer complaints.

Uses exact batch/product matching and sequence similarity (difflib)
over descriptions. Code, not LLM, determines candidate duplicate status.
"""

from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from typing import List

from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.schemas.ai_insights import DuplicateMatch
from app.schemas.complaint import ComplaintBase


def find_candidate_duplicates(
    db: Session,
    complaint: ComplaintBase,
    window_days: int = 90,
) -> List[DuplicateMatch]:
    """Deterministically find candidate duplicates within a time window.

    Exact batch + product match -> high confidence.
    Similar description (> 0.75 ratio) on the same product -> medium confidence.
    """
    candidates: List[DuplicateMatch] = []

    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    cutoff_naive = cutoff.replace(tzinfo=None)

    # In SQLite DateTime columns can be stored naive or aware
    try:
        query = db.query(Complaint).filter(Complaint.created_at >= cutoff)
        _ = query.first()
    except Exception:
        db.rollback()
        query = db.query(Complaint).filter(Complaint.created_at >= cutoff_naive)

    if complaint.batch_number and complaint.product_name:
        batch_matches = query.filter(
            Complaint.batch_number == complaint.batch_number,
            Complaint.product_name == complaint.product_name,
        ).all()
        for row in batch_matches:
            candidates.append(
                DuplicateMatch(
                    complaint_id=row.id,
                    confidence="high",
                    reason="same_batch_and_product",
                    created_at=row.created_at,
                    product_name=row.product_name,
                    batch_number=row.batch_number,
                )
            )

    if complaint.detailed_complaint_description and complaint.product_name:
        seen_ids = {c.complaint_id for c in candidates}
        product_rows = query.filter(
            Complaint.product_name == complaint.product_name
        ).all()

        for row in product_rows:
            if row.id in seen_ids:
                continue
            if row.detailed_complaint_description:
                ratio = SequenceMatcher(
                    None,
                    complaint.detailed_complaint_description,
                    row.detailed_complaint_description,
                ).ratio()
                if ratio > 0.75:
                    candidates.append(
                        DuplicateMatch(
                            complaint_id=row.id,
                            confidence="medium",
                            reason="similar_description",
                            similarity=round(ratio, 2),
                            created_at=row.created_at,
                            product_name=row.product_name,
                            batch_number=row.batch_number,
                        )
                    )

    return candidates
