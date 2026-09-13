import unittest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db
from app.models.complaint import Complaint
from app.schemas.complaint import ComplaintBase
from app.services.duplicate_service import find_candidate_duplicates

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


class TestDuplicateDetection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

        now = datetime.now(timezone.utc)
        # 1. Existing complaint (recent, same product & batch)
        c1 = Complaint(
            product_name="Amoxicillin 500mg",
            batch_number="BATCH-DUP-001",
            detailed_complaint_description="Capsules crushed inside blister pack.",
            created_at=now - timedelta(days=2),
        )
        # 2. Existing complaint (recent, same product, different batch, specific description)
        c2 = Complaint(
            product_name="Ibuprofen 400mg",
            batch_number="BATCH-IBU-999",
            detailed_complaint_description="Severe discoloration and foul odor from tablets.",
            created_at=now - timedelta(days=5),
        )
        # 3. Old complaint outside 90-day window
        c3 = Complaint(
            product_name="Amoxicillin 500mg",
            batch_number="BATCH-DUP-OLD",
            detailed_complaint_description="Historic packaging tearing issue from last quarter.",
            created_at=now - timedelta(days=120),
        )
        self.db.add_all([c1, c2, c3])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=engine)

    def test_exact_batch_and_product_match(self):
        """Exact batch + product returns high confidence match."""
        incoming = ComplaintBase(
            product_name="Amoxicillin 500mg",
            batch_number="BATCH-DUP-001",
            detailed_complaint_description="Completely different defect text",
        )
        matches = find_candidate_duplicates(self.db, incoming, window_days=90)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].confidence, "high")
        self.assertEqual(matches[0].reason, "same_batch_and_product")

    def test_similar_description_medium_confidence(self):
        """Near-identical description on same product returns medium confidence match."""
        incoming = ComplaintBase(
            product_name="Ibuprofen 400mg",
            batch_number="BATCH-DIFFERENT-123",
            detailed_complaint_description="Severe discoloration and foul odor from the tablets.",
        )
        matches = find_candidate_duplicates(self.db, incoming, window_days=90)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].confidence, "medium")
        self.assertEqual(matches[0].reason, "similar_description")
        self.assertGreater(matches[0].similarity, 0.75)

    def test_unrelated_complaint_no_matches(self):
        """Unrelated product and description returns zero matches."""
        incoming = ComplaintBase(
            product_name="Cetirizine 10mg",
            batch_number="BATCH-CET-555",
            detailed_complaint_description="Leaking bottle syrup.",
        )
        matches = find_candidate_duplicates(self.db, incoming, window_days=90)
        self.assertEqual(len(matches), 0)

    def test_outside_window_excluded(self):
        """Matches older than window_days are excluded."""
        incoming = ComplaintBase(
            product_name="Amoxicillin 500mg",
            batch_number="BATCH-DUP-OLD",
            detailed_complaint_description="Historic packaging tearing issue from last quarter.",
        )
        matches = find_candidate_duplicates(self.db, incoming, window_days=90)
        self.assertEqual(len(matches), 0)

    def test_duplicate_endpoint_api(self):
        """POST /api/ai/complaints/duplicates returns candidates via HTTP."""
        payload = {
            "complaint": {
                "product_name": "Amoxicillin 500mg",
                "batch_number": "BATCH-DUP-001",
            }
        }
        response = self.client.post("/api/ai/complaints/duplicates", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["matches"]), 1)
        self.assertEqual(data["matches"][0]["confidence"], "high")
