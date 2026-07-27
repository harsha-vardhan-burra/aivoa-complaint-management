from typing import List, Optional, TypedDict

from app.schemas.complaint import ComplaintBase
from app.schemas.risk_assessment import RiskAssessmentBase


class ComplaintAgentState(TypedDict, total=False):
    """State threaded through the complaint-processing graph.

    total=False because each node only fills in the keys it is
    responsible for; earlier keys persist unchanged as they pass
    through later nodes.
    """

    # Input
    message: str
    current_complaint: Optional[ComplaintBase]

    # determine_intent
    intent: Optional[str]

    # extract_fields
    extracted_patch: Optional[ComplaintBase]

    # merge_patch
    merged_complaint: Optional[ComplaintBase]

    # assess_risk
    risk: Optional[RiskAssessmentBase]
    missing_fields: List[str]

    # Set by any node that fails; downstream nodes check this and
    # skip further Groq calls rather than compounding the failure or
    # fabricating data.
    error: Optional[str]
