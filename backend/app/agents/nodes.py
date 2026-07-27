from app.agents.state import ComplaintAgentState
from app.schemas.complaint import ComplaintBase
from app.services.groq_service import (
    GroqService,
    GroqServiceError,
    GroqValidationError,
)

_groq_service = GroqService()


def determine_intent(state: ComplaintAgentState) -> dict:
    """Classify what the user is trying to do.

    This is a deterministic, non-LLM check: if there is no existing
    complaint (or it carries no known fields yet), the message is
    populating a brand-new complaint. Otherwise it is treated as an
    edit/clarification against the existing complaint. This keeps
    intent classification cheap and predictable rather than adding an
    extra LLM call for a decision the graph itself already needs to
    make deterministically for merge_patch to behave correctly.
    """
    current = state.get("current_complaint")

    has_known_fields = bool(current) and any(
        value is not None for value in current.model_dump().values()
    )

    intent = "update" if has_known_fields else "create"
    return {"intent": intent}


def extract_fields(state: ComplaintAgentState) -> dict:
    """Extract a patch of source-supported fields from the incoming
    message. On failure, record the error and leave extracted_patch
    unset -- merge_patch will then pass the existing complaint through
    unchanged rather than losing data."""
    try:
        patch = _groq_service.extract_fields(state["message"])
        return {"extracted_patch": patch}
    except (GroqServiceError, GroqValidationError) as exc:
        return {"error": str(exc)}


def merge_patch(state: ComplaintAgentState) -> dict:
    """Non-destructively merge extracted_patch into current_complaint.

    Critical rule: existing complaint information must survive unless
    the user's message explicitly supplied a replacement value. A null
    in the patch means "not mentioned in this message", not "clear
    this field" -- so nulls in the patch never overwrite an existing
    value.
    """
    current = state.get("current_complaint") or ComplaintBase()
    patch = state.get("extracted_patch")

    if patch is None:
        # Extraction failed or produced nothing -- preserve current
        # complaint state untouched rather than guessing.
        return {"merged_complaint": current}

    current_dict = current.model_dump()
    patch_dict = patch.model_dump()

    merged_dict = dict(current_dict)
    for field_name, patch_value in patch_dict.items():
        if patch_value is not None:
            merged_dict[field_name] = patch_value

    merged = ComplaintBase.model_validate(merged_dict)
    return {"merged_complaint": merged}


def get_deterministic_missing_fields(complaint: ComplaintBase) -> list[str]:
    """Deterministically compute missing fields from ComplaintBase state.

    The application schema (ComplaintBase) is the sole authority for
    form completeness: any field whose value is strictly None is missing.
    Valid non-None values (including falsy numbers or Booleans) are not
    treated as missing.
    """
    complaint_dict = complaint.model_dump()
    return [
        field_name
        for field_name, value in complaint_dict.items()
        if value is None
    ]


def assess_risk(state: ComplaintAgentState) -> dict:
    """Assess risk on the merged (latest known) complaint state.

    The LLM provides decision support (severity, rationale, confidence,
    and recommended_action), while missing_fields is deterministically
    computed from ComplaintBase state so the AI cannot hallucinate
    external fields or misreport completeness.
    """
    merged = state.get("merged_complaint") or ComplaintBase()
    deterministic_missing = get_deterministic_missing_fields(merged)

    if state.get("error"):
        return {"risk": None, "missing_fields": deterministic_missing}

    try:
        risk = _groq_service.assess_risk(merged)
        risk.missing_fields = deterministic_missing
        return {"risk": risk, "missing_fields": deterministic_missing}
    except (GroqServiceError, GroqValidationError) as exc:
        return {
            "error": str(exc),
            "risk": None,
            "missing_fields": deterministic_missing,
        }

