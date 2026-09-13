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
    message or uploaded document text. On failure, record the error and leave
    extracted_patch unset -- merge_patch will then pass the existing
    complaint through unchanged rather than losing data."""
    try:
        if state.get("is_document"):
            patch = _groq_service.extract_document_fields(state["message"])
        else:
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

    Document rule: Document inputs AUGMENT an active complaint (populating
    missing/null fields), but MUST NOT overwrite existing non-null facts.
    Conversational edits/corrections may update existing non-null values.

    changed_fields contains ONLY field names whose final value actually
    differs from current_complaint.
    """
    current = state.get("current_complaint") or ComplaintBase()
    patch = state.get("extracted_patch")
    is_document = state.get("is_document", False)

    if patch is None:
        return {
            "merged_complaint": current,
            "changed_fields": [],
        }

    current_dict = current.model_dump()
    patch_dict = patch.model_dump()

    merged_dict = dict(current_dict)
    changed_fields = []

    for field_name, patch_value in patch_dict.items():
        if patch_value is not None:
            old_value = current_dict.get(field_name)

            # Document conflict preservation rule: documents augment missing facts
            # but cannot overwrite pre-existing non-null complaint facts.
            if is_document and old_value is not None:
                continue

            if patch_value != old_value:
                merged_dict[field_name] = patch_value
                changed_fields.append(field_name)

    merged = ComplaintBase.model_validate(merged_dict)
    return {
        "merged_complaint": merged,
        "changed_fields": changed_fields,
    }



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

    If intent is 'update' and changed_fields is empty (no-op input),
    Groq risk assessment is skipped to save an extra LLM call while
    preserving existing risk state.
    """
    merged = state.get("merged_complaint") or ComplaintBase()
    deterministic_missing = get_deterministic_missing_fields(merged)
    changed_fields = state.get("changed_fields", [])
    intent = state.get("intent")

    if state.get("error"):
        return {"risk": None, "missing_fields": deterministic_missing}

    # No-op optimization: if updating an existing complaint and no fields changed,
    # preserve existing risk state without making a new Groq API call.
    if intent == "update" and len(changed_fields) == 0:
        return {
            "risk": state.get("current_risk"),
            "missing_fields": deterministic_missing,
        }

    try:
        risk = _groq_service.assess_risk(merged)
        risk.missing_fields = deterministic_missing
        if risk.confidence_factors is None:
            risk.confidence_factors = []
        return {"risk": risk, "missing_fields": deterministic_missing}
    except (GroqServiceError, GroqValidationError) as exc:
        return {
            "error": str(exc),
            "risk": None,
            "missing_fields": deterministic_missing,
        }


