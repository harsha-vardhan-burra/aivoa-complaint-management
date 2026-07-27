import json

from app.schemas.complaint import ComplaintBase
from app.schemas.risk_assessment import RiskAssessmentBase

_COMPLAINT_FIELDS = list(ComplaintBase.model_fields.keys())
_RISK_FIELDS = list(RiskAssessmentBase.model_fields.keys())

EXTRACTION_SYSTEM_PROMPT = f"""You are a structured information extractor for a \
pharmaceutical quality complaint intake system. You behave like a precise \
information extractor, not a creative assistant.

Rules you must follow exactly:
- Extract ONLY facts explicitly stated in the user's message.
- Never guess, infer, or invent values -- this includes dates, batch \
numbers, quantities, product identifiers, and severity indicators.
- If a field is not explicitly supported by the message, its value MUST \
be null.
- "quantity_affected" must be a plain number with no unit or words \
attached, converting spelled-out numbers to digits: "three bottles" -> \
3, "48 capsules" -> 48, "3.5 kg" -> 3.5. If the message gives an \
indefinite amount instead of a specific count -- "several bottles", \
"many capsules", "some tablets" -- there is no definite number to \
extract, so the value MUST be null. Never round or guess a number for \
an indefinite amount.
- "manufacturing_date", "expiry_date", and "complaint_date" must each be \
a complete ISO 8601 date, exactly YYYY-MM-DD: "18 April 2026" -> \
"2026-04-18", "25 July 2026" -> "2026-07-25". If the message does not \
give enough information to determine a complete date (missing day, \
month, or year), the value MUST be null rather than a partial or \
guessed date.
- Respond with a single JSON object containing EXACTLY these keys, no \
others: {json.dumps(_COMPLAINT_FIELDS)}.
- Output JSON only. No markdown, no explanations, no surrounding text.
"""

RISK_SYSTEM_PROMPT = f"""You are a pharmaceutical quality risk-assessment \
assistant. You analyze only the complaint facts you are given; you never \
invent new complaint facts.

Rules you must follow exactly:
- Base your assessment solely on the complaint fields provided below.
- "severity" must be one of "low", "medium", "high", "critical", or null \
if there is not enough information to assess it.
- "rationale" is a short explanation grounded only in the given facts.
- "missing_fields" lists the complaint field names that are null/missing \
and matter for a complete risk assessment.
- "confidence" is a number between 0 and 1 representing how confident \
you are in this assessment given the available facts -- lower it when \
important fields are missing or the message is ambiguous.
- "recommended_action" is one short, concrete next step for the quality \
team (e.g. "Route to QA investigation"). It is decision support, not a \
complaint fact, and must never introduce new information about the \
complaint itself.
- Respond with a single JSON object containing EXACTLY these keys, no \
others: {json.dumps(_RISK_FIELDS)}.
- Output JSON only. No markdown, no explanations, no surrounding text.
"""


def build_extraction_messages(message: str) -> list[dict]:
    """Build the chat messages for a single extraction call.

    Deliberately stateless with respect to any existing complaint --
    merging a patch into current_complaint is the LangGraph
    merge_patch node's responsibility (Phase 5), not this service's.
    """
    return [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]


def build_risk_messages(complaint: ComplaintBase) -> list[dict]:
    """Build the chat messages for a risk-assessment call over
    already-known complaint facts (which may contain nulls)."""
    complaint_json = complaint.model_dump(mode="json")
    user_content = (
        "Known complaint facts (already-extracted, may contain nulls):\n"
        f"{json.dumps(complaint_json, indent=2)}"
    )
    return [
        {"role": "system", "content": RISK_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
