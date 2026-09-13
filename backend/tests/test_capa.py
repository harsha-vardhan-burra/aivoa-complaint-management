import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db
from app.schemas.ai_insights import CapaSuggestion, RootCauseSuggestion
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


class TestCapaRecommendation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    def setUp(self):
        Base.metadata.create_all(bind=engine)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    @patch("app.api.ai._groq_service.suggest_capa")
    def test_gate_rejects_low_severity(self, mock_suggest):
        """Low severity complaints are gated with a 400, Groq is not called."""
        payload = {
            "complaint": {
                "product_name": "Paracetamol 500mg",
                "detailed_complaint_description": "Minor box scratch.",
            },
            "risk": {
                "severity": "low",
                "rationale": "Cosmetic packaging only.",
            },
            "root_cause": None,
        }
        response = self.client.post("/api/ai/complaints/capa", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("high/critical", response.json()["detail"])
        mock_suggest.assert_not_called()

    @patch("app.api.ai._groq_service.suggest_capa")
    def test_gate_rejects_medium_severity(self, mock_suggest):
        """Medium severity complaints are gated with a 400, Groq is not called."""
        payload = {
            "complaint": {
                "product_name": "Paracetamol 500mg",
                "detailed_complaint_description": "Clumping inside container.",
            },
            "risk": {
                "severity": "medium",
                "rationale": "Physical defect without consumer harm.",
            },
            "root_cause": None,
        }
        response = self.client.post("/api/ai/complaints/capa", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("high/critical", response.json()["detail"])
        mock_suggest.assert_not_called()

    @patch("app.api.ai._groq_service.suggest_capa")
    def test_suggest_capa_high_severity_without_root_cause(self, mock_suggest):
        """High severity proceeds and passes root_cause=None when absent."""
        mock_suggest.return_value = CapaSuggestion(
            corrective_actions=["Quarantine batch in distribution center"],
            preventive_actions=["Recalibrate visual inspection camera"],
            rationale="Immediate containment required for suspected contamination.",
        )

        payload = {
            "complaint": {
                "product_name": "Amoxicillin 500mg",
                "detailed_complaint_description": "Foreign particulate matter in vial.",
            },
            "risk": {
                "severity": "high",
                "rationale": "Potential patient exposure to foreign matter.",
            },
            "root_cause": None,
        }
        response = self.client.post("/api/ai/complaints/capa", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["corrective_actions"]), 1)
        mock_suggest.assert_called_once()
        # Verify root_cause argument was None
        args, kwargs = mock_suggest.call_args
        self.assertIsNone(kwargs.get("root_cause"))

    @patch("app.api.ai._groq_service.suggest_capa")
    def test_suggest_capa_critical_with_root_cause_context(self, mock_suggest):
        """Critical severity proceeds and passes root_cause context when provided."""
        mock_suggest.return_value = CapaSuggestion(
            corrective_actions=["Recall batch from pharmacies immediately"],
            preventive_actions=["Overhaul sealing line heating element"],
            rationale="Critical hazard with confirmed seal failure causing degradation.",
        )

        payload = {
            "complaint": {
                "product_name": "Amoxicillin 500mg",
                "detailed_complaint_description": "Degraded active ingredient causing illness.",
            },
            "risk": {
                "severity": "critical",
                "rationale": "Severe health impact reported.",
            },
            "root_cause": {
                "hypothesis": "Heat element failure on blister sealing line.",
                "contributing_factors": ["Sensor failure"],
                "confidence": "high",
                "recommended_investigation_steps": ["Inspect PLC thermocouple logs"],
            },
        }
        response = self.client.post("/api/ai/complaints/capa", json=payload)
        self.assertEqual(response.status_code, 200)
        mock_suggest.assert_called_once()
        args, kwargs = mock_suggest.call_args
        self.assertIsNotNone(kwargs.get("root_cause"))
        self.assertEqual(kwargs["root_cause"].confidence, "high")

    def test_save_complaint_with_capa_persistence(self):
        """CAPA suggestion persists to complaint_ai_insights with insight_type='capa'."""
        payload = {
            "complaint": {
                "product_name": "Amoxicillin 500mg",
                "batch_number": "BATCH-12345",
                "complaint_type": "Foreign matter",
                "detailed_complaint_description": "Particulate detected in solution.",
            },
            "capa": {
                "corrective_actions": ["Quarantine warehouse inventory"],
                "preventive_actions": ["Install secondary filter"],
                "rationale": "Prevent further contamination of downstream batches.",
            },
        }

        response = self.client.post("/api/complaints", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIsNotNone(data["id"])
        self.assertEqual(len(data["ai_insights"]), 1)
        insight = data["ai_insights"][0]
        self.assertEqual(insight["insight_type"], "capa")
        self.assertIn("Quarantine", insight["payload"]["corrective_actions"][0])
