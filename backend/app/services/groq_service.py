import json
from typing import Optional

from groq import Groq

from app.core.config import settings
from app.schemas.complaint import ComplaintBase
from app.schemas.risk_assessment import RiskAssessmentBase
from app.services.prompts import build_extraction_messages, build_risk_messages
from app.services.schema_utils import COMPLAINT_EXTRACTION_SCHEMA, RISK_ASSESSMENT_SCHEMA


class GroqServiceError(Exception):
    """Raised when the Groq API call itself fails: network error, auth
    failure, rate limit, timeout, etc. Callers must surface this as a
    controlled backend error and must not fabricate fallback data."""


class GroqValidationError(GroqServiceError):
    """Raised when Groq's response cannot be parsed as JSON, or parses
    but does not satisfy the target Pydantic schema. Never trust
    free-form model output -- this exception is the enforcement point
    for that rule."""


class GroqService:
    """Thin wrapper around the Groq API for structured complaint field
    extraction and risk assessment.

    Uses Groq's Structured Outputs (response_format="json_schema",
    strict=True) rather than plain JSON mode: this constrains the
    model at the token level so a numeric field like quantity_affected
    or a date field cannot come back as a free-form string such as
    "three bottles" or "18 April 2026" in the first place. Pydantic
    validation (see ComplaintBase's field_validators) remains the
    final safety net in case a model doesn't fully honor strict mode.

    Out of scope for this service (by design, per project phase
    boundaries):
    - Merging an extracted patch into an existing complaint
      (LangGraph's merge_patch node, Phase 5).
    - Persisting anything (Phase 3 models + later API layer).
    - PDF text extraction (Phase 8).
    """

    def __init__(self, client: Optional[Groq] = None, model: Optional[str] = None):
        self._client = client or Groq(api_key=settings.GROQ_API_KEY)
        self._model = model or settings.GROQ_MODEL

    def _chat_json(self, messages: list[dict], schema: dict) -> dict:
        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                response_format={"type": "json_schema", "json_schema": schema},
                temperature=0,
            )
        except Exception as exc:
            raise GroqServiceError(f"Groq API call failed: {exc}") from exc

        raw_content = completion.choices[0].message.content

        try:
            return json.loads(raw_content)
        except (json.JSONDecodeError, TypeError) as exc:
            raise GroqValidationError(
                f"Groq did not return valid JSON: {exc}"
            ) from exc

    def extract_fields(self, message: str) -> ComplaintBase:
        """Extract source-supported complaint fields from a natural
        language message. Fields not explicitly supported remain null."""
        raw = self._chat_json(
            build_extraction_messages(message), COMPLAINT_EXTRACTION_SCHEMA
        )

        try:
            return ComplaintBase.model_validate(raw)
        except Exception as exc:
            raise GroqValidationError(
                f"Extraction output failed schema validation: {exc}"
            ) from exc

    def assess_risk(self, complaint: ComplaintBase) -> RiskAssessmentBase:
        """Produce a risk assessment from already-known complaint facts.
        This is decision support and must stay distinguishable from
        extracted complaint facts -- it is never merged back into the
        complaint itself."""
        raw = self._chat_json(
            build_risk_messages(complaint), RISK_ASSESSMENT_SCHEMA
        )

        try:
            return RiskAssessmentBase.model_validate(raw)
        except Exception as exc:
            raise GroqValidationError(
                f"Risk assessment output failed schema validation: {exc}"
            ) from exc
