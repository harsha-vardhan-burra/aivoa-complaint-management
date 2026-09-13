from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.agents.graph import run_complaint_agent
from app.db.database import get_db
from app.schemas.ai import ProcessComplaintRequest, ProcessComplaintResponse
from app.schemas.complaint import ComplaintBase
from app.schemas.risk_assessment import RiskAssessmentBase
from app.schemas.ai_insights import (
    ComplaintSummary,
    ComplaintSummaryRequest,
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    RootCauseRequest,
    RootCauseSuggestion,
    CapaRequest,
    CapaSuggestion,
)
from app.services.completeness_service import compute_completeness
from app.services.document_service import (
    DocumentValidationError,
    validate_and_extract_document_text,
)
from app.services.duplicate_service import find_candidate_duplicates
from app.services.groq_service import (
    GroqService,
    GroqServiceError,
    GroqValidationError,
)

router = APIRouter()
_groq_service = GroqService()


@router.post("/ai/complaints/process", response_model=ProcessComplaintResponse)
async def process_complaint_message(payload: ProcessComplaintRequest):
    """Run one conversational message through the complaint agent graph
    (determine_intent -> extract_fields -> merge_patch -> assess_risk)
    and return the merged complaint, risk assessment, and missing
    fields.

    If the graph recorded an error (Groq call failed, or its output
    failed schema validation), this returns a controlled 502 rather
    than silently returning fabricated or partial data -- the existing
    complaint state on the frontend is left untouched either way,
    since we never send back a response that erases it.
    """
    result = run_complaint_agent(
        message=payload.message,
        current_complaint=payload.current_complaint,
        current_risk=payload.current_risk,
        is_document=False,
    )

    if result.get("error"):
        raise HTTPException(
            status_code=502,
            detail=f"Complaint processing failed: {result['error']}",
        )

    merged = result["merged_complaint"]
    completeness = compute_completeness(merged) if merged else None

    return ProcessComplaintResponse(
        complaint=result["merged_complaint"],
        risk=result.get("risk"),
        missing_fields=result.get("missing_fields", []),
        changed_fields=result.get("changed_fields", []),
        completeness=completeness,
    )


@router.post("/ai/complaints/document", response_model=ProcessComplaintResponse)
async def process_complaint_document(
    file: UploadFile = File(...),
    current_complaint_json: Optional[str] = Form(None),
    current_risk_json: Optional[str] = Form(None),
):
    """Upload and process a complaint document (.pdf, .txt, .eml).

    Validates file metadata, extracts raw text, enforces prompt hardening,
    and runs document facts through the existing LangGraph pipeline
    (determine_intent -> extract_fields -> merge_patch -> assess_risk).
    """
    current_complaint = None
    if current_complaint_json:
        try:
            current_complaint = ComplaintBase.model_validate_json(current_complaint_json)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid current_complaint JSON string.")

    current_risk = None
    if current_risk_json:
        try:
            current_risk = RiskAssessmentBase.model_validate_json(current_risk_json)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid current_risk JSON string.")

    content_bytes = await file.read()
    try:
        extracted_text = validate_and_extract_document_text(
            filename=file.filename,
            content_bytes=content_bytes,
        )
    except DocumentValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    result = run_complaint_agent(
        message=extracted_text,
        current_complaint=current_complaint,
        current_risk=current_risk,
        is_document=True,
    )

    if result.get("error"):
        raise HTTPException(
            status_code=502,
            detail=f"Document complaint processing failed: {result['error']}",
        )

    merged = result["merged_complaint"]
    completeness = compute_completeness(merged) if merged else None

    return ProcessComplaintResponse(
        complaint=result["merged_complaint"],
        risk=result.get("risk"),
        missing_fields=result.get("missing_fields", []),
        changed_fields=result.get("changed_fields", []),
        completeness=completeness,
    )


@router.post("/ai/complaints/summary", response_model=ComplaintSummary)
async def summarize_complaint_endpoint(payload: ComplaintSummaryRequest):
    """Generate an executive summary and key factual bullet points for a complaint.

    Stateless round-trip call, on-demand. Returns 502 on Groq failure or validation error.
    """
    try:
        return _groq_service.summarize_complaint(payload.complaint)
    except (GroqServiceError, GroqValidationError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Complaint summary failed: {exc}",
        )


@router.post("/ai/complaints/duplicates", response_model=DuplicateCheckResponse)
def check_duplicates_endpoint(
    payload: DuplicateCheckRequest,
    db: Session = Depends(get_db),
):
    """Check for candidate duplicate complaints deterministically.

    Identifies matching batch/product or similar descriptions in existing records.
    Decision support signal only; never hard-blocks saving.
    """
    matches = find_candidate_duplicates(
        db=db,
        complaint=payload.complaint,
        window_days=payload.window_days,
    )
    return DuplicateCheckResponse(matches=matches)


@router.post("/ai/complaints/root-cause", response_model=RootCauseSuggestion)
async def suggest_root_cause_endpoint(payload: RootCauseRequest):
    """Generate an AI-suggested root cause hypothesis and investigation steps.

    Deterministic gate: complaint_type and detailed_complaint_description must
    both be non-null. Returns 400 otherwise without calling Groq.
    """
    if (
        not payload.complaint.complaint_type
        or not payload.complaint.detailed_complaint_description
    ):
        raise HTTPException(
            status_code=400,
            detail="Root cause suggestion requires both 'complaint_type' and 'detailed_complaint_description' to be provided.",
        )

    try:
        return _groq_service.suggest_root_cause(payload.complaint, payload.risk)
    except (GroqServiceError, GroqValidationError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Root cause suggestion failed: {exc}",
        )


@router.post("/ai/complaints/capa", response_model=CapaSuggestion)
async def suggest_capa_endpoint(payload: CapaRequest):
    """Generate draft CAPA suggestions for high or critical severity complaints.

    Deterministic gate: only allowed when risk.severity is 'high' or 'critical'.
    Returns 400 otherwise without calling Groq.
    """
    severity = (payload.risk.severity or "").lower()
    if severity not in ("high", "critical"):
        raise HTTPException(
            status_code=400,
            detail="CAPA suggestions are only generated for high/critical severity complaints.",
        )

    try:
        return _groq_service.suggest_capa(
            complaint=payload.complaint,
            risk=payload.risk,
            root_cause=payload.root_cause,
        )
    except (GroqServiceError, GroqValidationError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"CAPA suggestion failed: {exc}",
        )


