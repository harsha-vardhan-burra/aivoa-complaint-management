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
            "quantity_unit",
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
            "quantity_unit": {
                "type": ["string", "null"],
                "enum": ["Units", "kg", "g", "mg", "ml", "L", None],
                "description": (
                    "The unit of measurement for quantity_affected, matching "
                    "one of the allowed enum values. Null if no unit is specified."
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
            # Explicit enum matching frontend ComplaintForm.jsx dropdown options exactly
            "initial_severity": {
                "type": ["string", "null"],
                "enum": ["Critical", "Major", "Minor", None],
            },
            "priority": {
                "type": ["string", "null"],
                "enum": ["High", "Medium", "Low", None],
            },
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
            "confidence_factors",
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
            "confidence_factors": {
                "type": "array",
                "maxItems": 4,
                "items": {"type": "string"},
                "description": (
                    "Up to 4 concise bullet phrases explaining why confidence is "
                    "high or low (e.g. 'Batch number confirmed', 'Missing detailed description')."
                ),
            },
            "recommended_action": {"type": ["string", "null"]},
        },
    },
}

COMPLAINT_SUMMARY_SCHEMA = {
    "name": "complaint_summary",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "summary",
            "key_facts",
        ],
        "properties": {
            "summary": {
                "type": "string",
                "description": "A 1-2 sentence plain language summary of the complaint.",
            },
            "key_facts": {
                "type": "array",
                "maxItems": 5,
                "items": {"type": "string"},
                "description": "Up to 5 short bullet fragments highlighting key facts (e.g. 'Batch CHG260712A').",
            },
        },
    },
}

ROOT_CAUSE_SCHEMA = {
    "name": "root_cause_suggestion",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "hypothesis",
            "contributing_factors",
            "confidence",
            "recommended_investigation_steps",
        ],
        "properties": {
            "hypothesis": {
                "type": "string",
                "description": "Starting hypothesis for a human investigator.",
            },
            "contributing_factors": {
                "type": "array",
                "maxItems": 5,
                "items": {"type": "string"},
                "description": "Up to 5 contributing factors.",
            },
            "confidence": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "Confidence level in this hypothesis.",
            },
            "recommended_investigation_steps": {
                "type": "array",
                "maxItems": 5,
                "items": {"type": "string"},
                "description": "Up to 5 investigation steps for human QA.",
            },
        },
    },
}

CAPA_SUGGESTION_SCHEMA = {
    "name": "capa_suggestion",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "corrective_actions",
            "preventive_actions",
            "rationale",
        ],
        "properties": {
            "corrective_actions": {
                "type": "array",
                "maxItems": 5,
                "items": {"type": "string"},
                "description": "Up to 5 immediate corrective actions.",
            },
            "preventive_actions": {
                "type": "array",
                "maxItems": 5,
                "items": {"type": "string"},
                "description": "Up to 5 preventive actions to prevent recurrence.",
            },
            "rationale": {
                "type": "string",
                "description": "Technical rationale justifying these CAPA actions.",
            },
        },
    },
}

