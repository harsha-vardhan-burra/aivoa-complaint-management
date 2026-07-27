from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.agents.graph import run_complaint_agent
from app.schemas.ai import ProcessComplaintRequest, ProcessComplaintResponse
from app.schemas.complaint import ComplaintBase
from app.schemas.risk_assessment import RiskAssessmentBase
from app.services.document_service import (
    DocumentValidationError,
    validate_and_extract_document_text,
)

router = APIRouter()


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

    return ProcessComplaintResponse(
        complaint=result["merged_complaint"],
        risk=result.get("risk"),
        missing_fields=result.get("missing_fields", []),
        changed_fields=result.get("changed_fields", []),
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

    return ProcessComplaintResponse(
        complaint=result["merged_complaint"],
        risk=result.get("risk"),
        missing_fields=result.get("missing_fields", []),
        changed_fields=result.get("changed_fields", []),
    )


