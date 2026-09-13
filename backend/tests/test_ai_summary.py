import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db
from app.models.ai_insight import ComplaintAIInsight
from app.schemas.ai_insights import ComplaintSummary
from app.services.groq_service import GroqServiceError, GroqValidationError

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


class TestComplaintSummary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    def setUp(self):
        Base.metadata.create_all(bind=engine)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    @patch("app.api.ai._groq_service.summarize_complaint")
    def test_summarize_complaint_success(self, mock_summarize):
        """Verify successful summary generation returns 200 with ComplaintSummary."""
        mock_summarize.return_value = ComplaintSummary(
            summary="Customer reported broken seals on Paracetamol bottles.",
            key_facts=["Product: Paracetamol 500mg", "Batch: BATCH-12345", "Defect: Broken seals"],
        )

        payload = {
            "complaint": {
                "product_name": "Paracetamol 500mg",
                "batch_number": "BATCH-12345",
                "detailed_complaint_description": "Broken seals on bottles.",
            }
        }

        response = self.client.post("/api/ai/complaints/summary", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["summary"], "Customer reported broken seals on Paracetamol bottles.")
        self.assertEqual(len(data["key_facts"]), 3)
        mock_summarize.assert_called_once()

    @patch("app.api.ai._groq_service.summarize_complaint")
    def test_summarize_complaint_groq_service_error(self, mock_summarize):
        """Verify GroqServiceError translates to 502 Bad Gateway."""
        mock_summarize.side_effect = GroqServiceError("Connection timed out")

        payload = {
            "complaint": {
                "product_name": "Paracetamol 500mg",
            }
        }

        response = self.client.post("/api/ai/complaints/summary", json=payload)
        self.assertEqual(response.status_code, 502)
        self.assertIn("Complaint summary failed", response.json()["detail"])

    @patch("app.api.ai._groq_service.summarize_complaint")
    def test_summarize_complaint_groq_validation_error(self, mock_summarize):
        """Verify GroqValidationError translates to 502 Bad Gateway."""
        mock_summarize.side_effect = GroqValidationError("Failed schema validation")

        payload = {
            "complaint": {
                "product_name": "Paracetamol 500mg",
            }
        }

        response = self.client.post("/api/ai/complaints/summary", json=payload)
        self.assertEqual(response.status_code, 502)
        self.assertIn("Complaint summary failed", response.json()["detail"])

    def test_save_complaint_with_summary_persistence(self):
        """Verify summary insight is persisted into complaint_ai_insights on Save."""
        payload = {
            "complaint": {
                "customer_name": "Metro Health",
                "product_name": "Paracetamol 500mg",
                "batch_number": "BATCH-12345",
                "complaint_type": "Packaging defect",
                "detailed_complaint_description": "Broken seals on bottles.",
            },
            "summary": {
                "summary": "Customer reported broken seals on Paracetamol bottles.",
                "key_facts": ["Product: Paracetamol 500mg", "Batch: BATCH-12345"],
            },
        }

        response = self.client.post("/api/complaints", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIsNotNone(data["id"])
        self.assertEqual(len(data["ai_insights"]), 1)
        insight = data["ai_insights"][0]
        self.assertEqual(insight["insight_type"], "summary")
        self.assertEqual(insight["payload"]["summary"], "Customer reported broken seals on Paracetamol bottles.")
