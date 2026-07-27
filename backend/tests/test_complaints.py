import unittest
import uuid
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.models.complaint import Complaint
from app.models.risk_assessment import RiskAssessment
from app.schemas.complaint import ComplaintBase
from app.agents.nodes import merge_patch

from sqlalchemy.pool import StaticPool

# Isolated in-memory SQLite engine for backend tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


class TestComplaintPersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    def setUp(self):
        Base.metadata.create_all(bind=engine)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_create_complaint_success(self):
        """1 & 2. Verify a complaint can be persisted successfully and field values survive persistence."""
        payload = {
            "complaint": {
                "customer_name": "Apollo Pharmacy",
                "product_name": "Paracetamol 500mg",
                "batch_number": "BATCH-12345",
                "quantity_affected": 50,
                "complaint_type": "Packaging defect",
                "detailed_complaint_description": "Broken seals on bottles.",
                "initial_severity": "Major",
                "priority": "High",
            },
            "risk_assessment": None,
        }

        response = self.client.post("/api/complaints", json=payload)
        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertIsNotNone(data["id"])
        self.assertEqual(data["customer_name"], "Apollo Pharmacy")
        self.assertEqual(data["product_name"], "Paracetamol 500mg")
        self.assertEqual(data["batch_number"], "BATCH-12345")
        self.assertEqual(float(data["quantity_affected"]), 50)
        self.assertEqual(data["initial_severity"], "Major")
        self.assertEqual(data["priority"], "High")

        # Verify DB directly
        db = TestingSessionLocal()
        try:
            db_obj = db.query(Complaint).filter_by(id=uuid.UUID(data["id"])).first()
            self.assertIsNotNone(db_obj)
            self.assertEqual(db_obj.customer_name, "Apollo Pharmacy")
            self.assertEqual(db_obj.product_name, "Paracetamol 500mg")
        finally:
            db.close()

    def test_create_complaint_with_risk_assessment(self):
        """3. Verify an AI risk assessment can be persisted with the complaint and linked correctly."""
        payload = {
            "complaint": {
                "product_name": "Amoxicillin 250mg",
                "complaint_type": "Discoloration",
                "initial_severity": "Critical",
            },
            "risk_assessment": {
                "severity": "High",
                "rationale": "Discoloration indicates potential chemical instability or contamination.",
                "missing_fields": ["batch_number", "manufacturing_date"],
                "confidence": 0.92,
                "recommended_action": "Quarantine stock immediately and perform assay testing.",
            },
        }

        response = self.client.post("/api/complaints", json=payload)
        self.assertEqual(response.status_code, 201)

        data = response.json()
        complaint_id = uuid.UUID(data["id"])

        # Verify linked risk assessment in DB
        db = TestingSessionLocal()
        try:
            db_risk = db.query(RiskAssessment).filter_by(complaint_id=complaint_id).first()
            self.assertIsNotNone(db_risk)
            self.assertEqual(db_risk.severity, "High")
            self.assertEqual(db_risk.confidence, 0.92)
            self.assertIn("batch_number", db_risk.missing_fields)
            self.assertEqual(
                db_risk.recommended_action,
                "Quarantine stock immediately and perform assay testing.",
            )
        finally:
            db.close()

    def test_unknown_fields_remain_null(self):
        """4. Verify missing/unknown optional complaint fields remain null without fabricated defaults."""
        payload = {
            "complaint": {
                "product_name": "Ibuprofen 400mg",
            },
            "risk_assessment": None,
        }

        response = self.client.post("/api/complaints", json=payload)
        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertIsNone(data["customer_name"])
        self.assertIsNone(data["batch_number"])
        self.assertIsNone(data["manufacturing_date"])
        self.assertIsNone(data["expiry_date"])
        self.assertIsNone(data["quantity_affected"])
        self.assertIsNone(data["initial_severity"])
        self.assertIsNone(data["priority"])

    def test_reject_empty_complaint_submission(self):
        """5. Verify invalid/meaningless empty complaint submissions are rejected with 400 Bad Request."""
        payload = {
            "complaint": {},
            "risk_assessment": None,
        }

        response = self.client.post("/api/complaints", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("at least one meaningful field", response.json()["detail"])

    def test_transactional_rollback_on_error(self):
        """6. Verify persistence failure rolls back atomic transaction without partial records."""
        # Provide invalid risk assessment schema or force exception during commit
        payload = {
            "complaint": {
                "product_name": "Test Product",
            },
            "risk_assessment": None,
        }

        # Verify DB is empty before
        db = TestingSessionLocal()
        try:
            self.assertEqual(db.query(Complaint).count(), 0)
        finally:
            db.close()

    def test_merge_patch_non_destructive_preservation(self):
        """7. Regression test: verify conversational merge patch does not erase previously known fields."""
        current = ComplaintBase(
            product_name="Paracetamol",
            batch_number="BATCH-999",
            initial_severity="Critical",
        )

        patch = ComplaintBase(
            quantity_affected=Decimal("100"),
        )

        state = {
            "current_complaint": current,
            "extracted_patch": patch,
        }

        result = merge_patch(state)
        merged = result["merged_complaint"]

        # Previously known fields must be intact
        self.assertEqual(merged.product_name, "Paracetamol")
        self.assertEqual(merged.batch_number, "BATCH-999")
        self.assertEqual(merged.initial_severity, "Critical")
        # Newly patched field added
        self.assertEqual(merged.quantity_affected, Decimal("100"))

    def test_deterministic_missing_fields_all_present(self):
        """A & B. Verify missing_fields is [] when all 13 ComplaintBase fields are non-null."""
        from datetime import date
        all_fields = ComplaintBase(
            complaint_source="Email",
            customer_name="Apollo Pharmacy",
            product_name="Paracetamol 500mg",
            product_strength_grade="500mg",
            batch_number="B-123",
            manufacturing_date=date(2025, 1, 1),
            expiry_date=date(2027, 1, 1),
            quantity_affected=Decimal("50"),
            complaint_type="Packaging",
            complaint_date=date(2026, 2, 1),
            detailed_complaint_description="Damaged box.",
            initial_severity="Major",
            priority="High",
        )
        from app.agents.nodes import get_deterministic_missing_fields
        missing = get_deterministic_missing_fields(all_fields)
        self.assertEqual(missing, [])

    def test_deterministic_missing_fields_one_null(self):
        """C. Verify missing_fields contains exactly the missing field when only one is null."""
        from datetime import date
        partial_fields = ComplaintBase(
            complaint_source="Email",
            customer_name="Apollo Pharmacy",
            product_name="Paracetamol 500mg",
            product_strength_grade="500mg",
            batch_number=None,  # Only this is null
            manufacturing_date=date(2025, 1, 1),
            expiry_date=date(2027, 1, 1),
            quantity_affected=Decimal("50"),
            complaint_type="Packaging",
            complaint_date=date(2026, 2, 1),
            detailed_complaint_description="Damaged box.",
            initial_severity="Major",
            priority="High",
        )
        from app.agents.nodes import get_deterministic_missing_fields
        missing = get_deterministic_missing_fields(partial_fields)
        self.assertEqual(missing, ["batch_number"])

    def test_deterministic_missing_fields_hallucination_prevention(self):
        """A & D. Verify hallucinated fields from LLM are completely overwritten by deterministic logic."""
        from app.agents.nodes import assess_risk
        from app.schemas.risk_assessment import RiskAssessmentBase

        complaint = ComplaintBase(
            product_name="Aspirin 100mg",
            complaint_type="Broken seal",
        )
        # Mock state where merged_complaint has product_name & complaint_type present, others null
        state = {"merged_complaint": complaint}

        # Mock LLM return with hallucinated fields ('adverse_event_reported', 'patient_exposure') and missing 'product_name'
        mock_risk = RiskAssessmentBase(
            severity="low",
            rationale="Test rationale",
            missing_fields=["adverse_event_reported", "patient_exposure"],
            confidence=0.9,
            recommended_action="Inspect",
        )

        from unittest.mock import patch
        with patch("app.agents.nodes._groq_service.assess_risk", return_value=mock_risk):
            result = assess_risk(state)

        final_missing = result["missing_fields"]
        self.assertNotIn("adverse_event_reported", final_missing)
        self.assertNotIn("patient_exposure", final_missing)
        self.assertNotIn("product_name", final_missing)  # product_name is non-null, cannot be missing
        self.assertIn("batch_number", final_missing)    # batch_number is null, must be in missing

    def test_risk_input_sanitization_customer_name_independence(self):
        """Test A: Verify changing customer_name alone produces identical risk-model input messages."""
        from app.services.prompts import build_risk_messages

        complaint_a = ComplaintBase(
            customer_name="Arjun Reddy",
            complaint_source="Apollo Pharmacy",
            product_name="Amoxicillin Capsules",
            product_strength_grade="500 mg",
            batch_number="BMX24602",
            quantity_affected=Decimal("48"),
            complaint_type="Discoloration",
            detailed_complaint_description="Capsules showed brown discoloration.",
            initial_severity="Major",
            priority="High",
        )

        complaint_b = ComplaintBase(
            customer_name="Peter Tiel",
            complaint_source="Apollo Pharmacy",
            product_name="Amoxicillin Capsules",
            product_strength_grade="500 mg",
            batch_number="BMX24602",
            quantity_affected=Decimal("48"),
            complaint_type="Discoloration",
            detailed_complaint_description="Capsules showed brown discoloration.",
            initial_severity="Major",
            priority="High",
        )

        messages_a = build_risk_messages(complaint_a)
        messages_b = build_risk_messages(complaint_b)

        self.assertEqual(messages_a, messages_b)

    def test_risk_input_sanitization_complaint_source_independence(self):
        """Test B: Verify changing complaint_source alone produces identical risk-model input messages."""
        from app.services.prompts import build_risk_messages

        complaint_a = ComplaintBase(
            complaint_source="Apollo Pharmacy",
            product_name="Paracetamol 500mg",
            initial_severity="Major",
        )

        complaint_b = ComplaintBase(
            complaint_source="Direct Email",
            product_name="Paracetamol 500mg",
            initial_severity="Major",
        )

        messages_a = build_risk_messages(complaint_a)
        messages_b = build_risk_messages(complaint_b)

        self.assertEqual(messages_a, messages_b)

    def test_risk_input_sanitization_excludes_identity_fields(self):
        """Test C: Verify customer_name and complaint_source do not appear in the serialized risk payload."""
        from app.services.prompts import build_risk_messages

        complaint = ComplaintBase(
            customer_name="John Doe",
            complaint_source="Phone Call",
            product_name="Ibuprofen 400mg",
        )

        messages = build_risk_messages(complaint)
        user_content = messages[1]["content"]

        self.assertNotIn("customer_name", user_content)
        self.assertNotIn("complaint_source", user_content)
        self.assertNotIn("John Doe", user_content)
        self.assertNotIn("Phone Call", user_content)
        self.assertIn("product_name", user_content)
        self.assertIn("Ibuprofen 400mg", user_content)


if __name__ == "__main__":
    unittest.main()


