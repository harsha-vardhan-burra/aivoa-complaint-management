import unittest
from datetime import date
from decimal import Decimal

from app.schemas.complaint import ComplaintBase
from app.services.completeness_service import compute_completeness, CRITICAL_FIELDS, OPTIONAL_FIELDS


class TestCompletenessService(unittest.TestCase):
    def test_all_null_complaint(self):
        """All-null complaint should score 0 and have ready_to_submit as False."""
        complaint = ComplaintBase()
        res = compute_completeness(complaint)

        self.assertEqual(res.score, 0)
        self.assertFalse(res.ready_to_submit)
        self.assertEqual(set(res.missing_critical), set(CRITICAL_FIELDS))
        self.assertEqual(set(res.missing_optional), set(OPTIONAL_FIELDS))

    def test_fully_filled_complaint(self):
        """Fully filled complaint should score 100 with zero missing fields."""
        complaint = ComplaintBase(
            complaint_source="Email",
            customer_name="John Doe",
            product_name="Amoxicillin 500mg",
            product_strength_grade="500mg",
            batch_number="BATCH-999",
            manufacturing_date=date(2023, 1, 1),
            expiry_date=date(2025, 1, 1),
            quantity_affected=Decimal("10"),
            quantity_unit="bottles",
            complaint_type="Packaging Defect",
            complaint_date=date(2023, 5, 1),
            detailed_complaint_description="Broken seals found on multiple bottles.",
            initial_severity="Major",
            priority="High",
        )
        res = compute_completeness(complaint)

        self.assertEqual(res.score, 100)
        self.assertTrue(res.ready_to_submit)
        self.assertEqual(res.missing_critical, [])
        self.assertEqual(res.missing_optional, [])

    def test_missing_only_optional_fields(self):
        """A complaint missing only optional fields is ready_to_submit with a partial score."""
        complaint = ComplaintBase(
            product_name="Amoxicillin 500mg",
            batch_number="BATCH-999",
            complaint_type="Packaging Defect",
            detailed_complaint_description="Broken seals found on multiple bottles.",
        )
        res = compute_completeness(complaint)

        self.assertTrue(res.ready_to_submit)
        self.assertEqual(res.missing_critical, [])
        self.assertEqual(set(res.missing_optional), set(OPTIONAL_FIELDS))
        # Total fields: 14. Critical: 4. Filled: 4.
        # Score = round(100 * (4 + 4) / 18) = round(800 / 18) = 44.
        self.assertEqual(res.score, 44)

    def test_missing_one_critical_field(self):
        """Missing even one critical field prevents ready_to_submit even if all optional fields are filled."""
        complaint = ComplaintBase(
            complaint_source="Email",
            customer_name="John Doe",
            product_name="Amoxicillin 500mg",
            product_strength_grade="500mg",
            # missing batch_number (critical)
            manufacturing_date=date(2023, 1, 1),
            expiry_date=date(2025, 1, 1),
            quantity_affected=Decimal("10"),
            quantity_unit="bottles",
            complaint_type="Packaging Defect",
            complaint_date=date(2023, 5, 1),
            detailed_complaint_description="Broken seals found on multiple bottles.",
            initial_severity="Major",
            priority="High",
        )
        res = compute_completeness(complaint)

        self.assertFalse(res.ready_to_submit)
        self.assertIn("batch_number", res.missing_critical)
        self.assertEqual(res.missing_optional, [])
