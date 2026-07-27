from fastapi import APIRouter, HTTPException

from app.agents.graph import run_complaint_agent
from app.schemas.ai import ProcessComplaintRequest, ProcessComplaintResponse

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
        message=payload.message, current_complaint=payload.current_complaint
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
    )
