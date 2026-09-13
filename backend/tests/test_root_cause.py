import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db
from app.schemas.ai_insights import RootCauseSuggestion
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


class TestRootCauseRecommendation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    def setUp(self):
        Base.metadata.create_all(bind=engine)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    @patch("app.api.ai._groq_service.suggest_root_cause")
    def test_gate_rejects_missing_complaint_type(self, mock_suggest):
        """Deterministic gate returns 400 if complaint_type is missing, without calling Groq."""
        payload = {
            "complaint": {
                "product_name": "Paracetamol 500mg",
                "detailed_complaint_description": "Broken seals found.",
                "complaint_type": None,
            },
            "risk": None,
        }
        response = self.client.post("/api/ai/complaints/root-cause", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("complaint_type", response.json()["detail"])
        mock_suggest.assert_not_called()

    @patch("app.api.ai._groq_service.suggest_root_cause")
    def test_gate_rejects_missing_description(self, mock_suggest):
        """Deterministic gate returns 400 if detailed_complaint_description is missing, without calling Groq."""
        payload = {
            "complaint": {
                "product_name": "Paracetamol 500mg",
                "complaint_type": "Packaging Defect",
                "detailed_complaint_description": None,
            },
            "risk": None,
        }
        response = self.client.post("/api/ai/complaints/root-cause", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("detailed_complaint_description", response.json()["detail"])
        mock_suggest.assert_not_called()

    @patch("app.api.ai._groq_service.suggest_root_cause")
    def test_suggest_root_cause_success(self, mock_suggest):
        """Gated check passes and Groq output returns 200 with RootCauseSuggestion."""
        mock_suggest.return_value = RootCauseSuggestion(
            hypothesis="Heat sealer calibration drift during packaging line run.",
            contributing_factors=["Temperature fluctuation", "Tooling wear"],
            confidence="high",
            recommended_investigation_steps=["Inspect sealing temperature logs", "Examine retain samples"],
        )

        payload = {
            "complaint": {
                "product_name": "Paracetamol 500mg",
                "complaint_type": "Packaging Defect",
                "detailed_complaint_description": "Broken seals on bottles.",
            },
            "risk": {
                "severity": "medium",
                "rationale": "Packaging defect without contamination.",
            },
        }
        response = self.client.post("/api/ai/complaints/root-cause", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["confidence"], "high")
        self.assertIn("Heat sealer", data["hypothesis"])
        mock_suggest.assert_called_once()

    @patch("app.api.ai._groq_service.suggest_root_cause")
    def test_suggest_root_cause_groq_error(self, mock_suggest):
        """Groq failure returns 502 Bad Gateway."""
        mock_suggest.side_effect = GroqServiceError("Service unavailable")
        payload = {
            "complaint": {
                "complaint_type": "Packaging Defect",
                "detailed_complaint_description": "Broken seals.",
            }
        }
        response = self.client.post("/api/ai/complaints/root-cause", json=payload)
        self.assertEqual(response.status_code, 502)

    def test_save_complaint_with_root_cause_persistence(self):
        """Root cause suggestion persists to complaint_ai_insights with insight_type='root_cause'."""
        payload = {
            "complaint": {
                "product_name": "Paracetamol 500mg",
                "batch_number": "BATCH-12345",
                "complaint_type": "Packaging defect",
                "detailed_complaint_description": "Broken seals on bottles.",
            },
            "root_cause": {
                "hypothesis": "Heat sealer calibration drift during packaging line run.",
                "contributing_factors": ["Temperature fluctuation"],
                "confidence": "high",
                "recommended_investigation_steps": ["Inspect sealing logs"],
            },
        }

        response = self.client.post("/api/complaints", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIsNotNone(data["id"])
        self.assertEqual(len(data["ai_insights"]), 1)
        insight = data["ai_insights"][0]
        self.assertEqual(insight["insight_type"], "root_cause")
        self.assertEqual(insight["payload"]["confidence"], "high")
