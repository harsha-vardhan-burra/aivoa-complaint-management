import re
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from dateutil import parser as date_parser
from pydantic import BaseModel, ConfigDict, field_validator
from word2number import w2n


class ComplaintBase(BaseModel):
    """Shared complaint fields. Every field is optional: an unknown
    value must remain null rather than being guessed by the AI.

    The field_validators below are a safety net, not the primary fix:
    Groq's Structured Outputs (see app/services/schema_utils.py)
    already constrain quantity_affected to a JSON number and the date
    fields to strings at the API boundary, which is what stops the
    model from emitting "three bottles" or "18 April 2026" in the
    first place. These validators just make sure that if a value
    somehow arrives as an unparsed string anyway (a different model, a
    provider that ignores strict mode, manual API use), we normalize
    it the same general way rather than raising -- and if it can't be
    normalized, we fall back to null instead of guessing.
    """

    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None

    product_name: Optional[str] = None
    product_strength_grade: Optional[str] = None
    batch_number: Optional[str] = None
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    quantity_affected: Optional[Decimal] = None

    complaint_type: Optional[str] = None
    complaint_date: Optional[date] = None
    detailed_complaint_description: Optional[str] = None

    initial_severity: Optional[str] = None
    priority: Optional[str] = None

    @field_validator("quantity_affected", mode="before")
    @classmethod
    def _normalize_quantity(cls, value):
        """Accept a plain number as-is. If given a string, first look
        for a definite numeric digit sequence (e.g. "48 capsules" ->
        48, "3.5 kg" -> 3.5). If there are no digits, the quantity may
        still be spelled out in words (e.g. "three bottles") -- try a
        general word-to-number parse for that case. If neither finds a
        definite quantity (e.g. "several bottles", "many capsules"),
        the amount is indefinite -- return None rather than inventing
        a number."""
        if value is None or isinstance(value, (int, float, Decimal)):
            return value
        if isinstance(value, str):
            match = re.search(r"[-+]?\d*\.?\d+", value)
            if match:
                try:
                    return Decimal(match.group(0))
                except InvalidOperation:
                    return None
            try:
                return Decimal(w2n.word_to_num(value))
            except ValueError:
                return None
        return value

    @field_validator("manufacturing_date", "expiry_date", "complaint_date", mode="before")
    @classmethod
    def _normalize_date(cls, value):
        """Accept a date object or an ISO string as-is (Pydantic parses
        ISO strings natively). If given some other string format,
        attempt a general date parse; if that fails or the string is
        too incomplete to resolve to a full date, return None rather
        than guessing at missing day/month/year components."""
        if value is None or isinstance(value, (date, datetime)):
            return value
        if isinstance(value, str):
            try:
                return date_parser.parse(value).date()
            except (ValueError, OverflowError):
                return None
        return value


class ComplaintCreate(ComplaintBase):
    """Schema used when persisting a complaint via POST /api/complaints."""

    pass


class ComplaintResponse(ComplaintBase):
    """Schema returned to the frontend for a persisted complaint."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
