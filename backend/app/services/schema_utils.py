"""Strict JSON Schema payloads for Groq's Structured Outputs feature
(response_format={"type": "json_schema", "json_schema": ..., "strict": True}).

Built by hand rather than derived from Pydantic's model_json_schema()
because Groq's strict mode requires every property to be listed under
"required" and additionalProperties: false at every level -- Pydantic's
default anyOf/$defs output for Optional fields doesn't match that shape
cleanly, and getting this wrong is exactly the kind of silent mismatch
that caused the original bug. Hand-written schemas keep the type
contract explicit and auditable.

Each JSON type constraint below is the *first* line of defense: it
prevents the model from emitting a free-form string like "three
bottles" for a numeric field at the token level (constrained decoding),
rather than relying on prompt wording alone. Pydantic validation (see
app/schemas/complaint.py field_validators) remains the second, final
safety net in case a model or provider doesn't honor strict mode.
"""

from app.schemas.complaint import ComplaintBase

_COMPLAINT_FIELDS = list(ComplaintBase.model_fields.keys())

COMPLAINT_EXTRACTION_SCHEMA = {
    "name": "complaint_extraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "complaint_source",
            "customer_name",
            "product_name",
            "product_strength_grade",
            "batch_number",
            "manufacturing_date",
            "expiry_date",
            "quantity_affected",
            "complaint_type",
            "complaint_date",
            "detailed_complaint_description",
            "initial_severity",
            "priority",
        ],
        "properties": {
            "complaint_source": {"type": ["string", "null"]},
            "customer_name": {"type": ["string", "null"]},
            "product_name": {"type": ["string", "null"]},
            "product_strength_grade": {"type": ["string", "null"]},
            "batch_number": {"type": ["string", "null"]},
            "manufacturing_date": {
                "type": ["string", "null"],
                "description": (
                    "ISO 8601 date, exactly YYYY-MM-DD. Null if the source "
                    "does not give enough information to determine a "
                    "complete date."
                ),
            },
            "expiry_date": {
                "type": ["string", "null"],
                "description": (
                    "ISO 8601 date, exactly YYYY-MM-DD. Null if the source "
                    "does not give enough information to determine a "
                    "complete date."
                ),
            },
            "quantity_affected": {
                "type": ["number", "null"],
                "description": (
                    "A definite numeric quantity only, with no unit or "
                    "words attached. Null if the source gives an "
                    "indefinite amount (e.g. 'several', 'many', 'some') "
                    "rather than a specific number."
                ),
            },
            "complaint_type": {"type": ["string", "null"]},
            "complaint_date": {
                "type": ["string", "null"],
                "description": (
                    "ISO 8601 date, exactly YYYY-MM-DD. Null if the source "
                    "does not give enough information to determine a "
                    "complete date."
                ),
            },
            "detailed_complaint_description": {"type": ["string", "null"]},
            "initial_severity": {"type": ["string", "null"]},
            "priority": {"type": ["string", "null"]},
        },
    },
}

RISK_ASSESSMENT_SCHEMA = {
    "name": "risk_assessment",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "severity",
            "rationale",
            "missing_fields",
            "confidence",
            "recommended_action",
        ],
        "properties": {
            "severity": {
                "type": ["string", "null"],
                "enum": ["low", "medium", "high", "critical", None],
            },
            "rationale": {"type": ["string", "null"]},
            "missing_fields": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": _COMPLAINT_FIELDS,
                },
            },
            "confidence": {
                "type": ["number", "null"],
                "description": "A value between 0 and 1.",
            },
            "recommended_action": {"type": ["string", "null"]},
        },
    },
}

