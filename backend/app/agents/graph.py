from typing import Optional

from langgraph.graph import END, StateGraph

from app.agents.nodes import assess_risk, determine_intent, extract_fields, merge_patch
from app.agents.state import ComplaintAgentState
from app.schemas.complaint import ComplaintBase
from app.schemas.risk_assessment import RiskAssessmentBase

# No HTTP-specific logic lives in the nodes themselves -- the graph
# exposes a plain function that the FastAPI service layer can call
# with plain schema objects and get plain schema objects back.

_builder = StateGraph(ComplaintAgentState)

_builder.add_node("determine_intent", determine_intent)
_builder.add_node("extract_fields", extract_fields)
_builder.add_node("merge_patch", merge_patch)
_builder.add_node("assess_risk", assess_risk)

_builder.set_entry_point("determine_intent")
_builder.add_edge("determine_intent", "extract_fields")
_builder.add_edge("extract_fields", "merge_patch")
_builder.add_edge("merge_patch", "assess_risk")
_builder.add_edge("assess_risk", END)

complaint_graph = _builder.compile()


def run_complaint_agent(
    message: str,
    current_complaint: Optional[ComplaintBase] = None,
    current_risk: Optional[RiskAssessmentBase] = None,
    is_document: bool = False,
) -> ComplaintAgentState:
    """Single entry point for the FastAPI service layer.

    Runs the full determine_intent -> extract_fields -> merge_patch ->
    assess_risk pipeline for one incoming message or extracted document
    text and returns the final state. Callers should check state["error"]
    before trusting state["merged_complaint"] / state["risk"].
    """
    initial_state: ComplaintAgentState = {
        "message": message,
        "is_document": is_document,
        "current_complaint": current_complaint,
        "current_risk": current_risk,
    }
    return complaint_graph.invoke(initial_state)


