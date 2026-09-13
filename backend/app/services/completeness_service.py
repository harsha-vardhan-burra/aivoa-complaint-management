"""Completeness calculation service for complaints.

Provides a deterministic score and categorization of missing fields
(critical vs. optional) without calling an LLM. Critical fields are
weighted 2x so that a complaint lacking core factual identifiers
cannot score as mostly complete.
"""

from typing import List, Set

from app.schemas.ai import CompletenessResult
from app.schemas.complaint import ComplaintBase

# Core factual fields required for minimum actionable complaint triage
CRITICAL_FIELDS: List[str] = [
    "product_name",
    "batch_number",
    "complaint_type",
    "detailed_complaint_description",
]
CRITICAL_FIELDS_SET: Set[str] = set(CRITICAL_FIELDS)
OPTIONAL_FIELDS: List[str] = sorted(
    list(set(ComplaintBase.model_fields.keys()) - CRITICAL_FIELDS_SET)
)


def compute_completeness(complaint: ComplaintBase) -> CompletenessResult:
    """Compute the completeness score and missing field lists for a complaint.

    Critical fields are weighted 2x so a form missing a critical fact never
    scores as mostly done.
    """
    data = complaint.model_dump()
    missing_critical = [f for f in CRITICAL_FIELDS if data.get(f) is None]
    missing_optional = [f for f in OPTIONAL_FIELDS if data.get(f) is None]
    total = len(CRITICAL_FIELDS) + len(OPTIONAL_FIELDS)
    filled = total - len(missing_critical) - len(missing_optional)

    # Critical fields are weighted 2x so a form missing a critical fact never scores as "mostly done"
    score = round(
        100 * (filled + (len(CRITICAL_FIELDS) - len(missing_critical)))
        / (total + len(CRITICAL_FIELDS))
    )
    return CompletenessResult(
        score=score,
        missing_critical=missing_critical,
        missing_optional=missing_optional,
        ready_to_submit=not missing_critical,
    )
