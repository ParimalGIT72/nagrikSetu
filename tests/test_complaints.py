import io
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app.db.database import Base, get_db
from app.config import settings

# In-memory SQLite engine for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_submit_valid_complaint_text_and_gps(client):
    data = {
        "text": "Pune road has a large pothole near FC Road.",
        "latitude": "18.5204",
        "longitude": "73.8567",
    }
    response = client.post("/api/complaints", data=data)
    assert response.status_code == 201
    body = response.json()
    assert "complaint_id" in body
    assert body["complaint_id"].startswith("CMP-")
    assert body["status"] == "SUBMITTED"

    # Verify retrieval
    cid = body["complaint_id"]
    get_res = client.get(f"/api/complaints/{cid}")
    assert get_res.status_code == 200
    complaint = get_res.json()
    assert complaint["complaint_id"] == cid
    assert complaint["text"] == data["text"]
    assert complaint["latitude"] == 18.5204
    assert complaint["longitude"] == 73.8567
    assert complaint["status"] == "SUBMITTED"
    assert complaint["image_path"] is None
    assert complaint["is_flagged"] is False


def test_submit_complaint_with_image(client, tmp_path):
    orig_upload_dir = settings.UPLOAD_DIR
    settings.UPLOAD_DIR = tmp_path
    try:
        data = {
            "text": "Garbage dumping site near bus stand is overflowing.",
            "latitude": "18.5314",
            "longitude": "73.8446",
        }
        image_content = b"sample image payload"
        files = {
            "image": ("garbage.png", io.BytesIO(image_content), "image/png"),
        }
        response = client.post("/api/complaints", data=data, files=files)
        assert response.status_code == 201
        body = response.json()
        cid = body["complaint_id"]

        get_res = client.get(f"/api/complaints/{cid}")
        assert get_res.status_code == 200
        complaint = get_res.json()
        assert complaint["image_path"] is not None
        assert "garbage" not in complaint["image_path"]  # Safe renamed filename
        assert complaint["image_path"].endswith(".png")
    finally:
        settings.UPLOAD_DIR = orig_upload_dir


def test_submit_complaint_empty_text_rejected(client):
    data = {
        "text": "   ",
        "latitude": "18.5204",
        "longitude": "73.8567",
    }
    response = client.post("/api/complaints", data=data)
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]


def test_submit_complaint_invalid_coordinates(client):
    data = {
        "text": "Valid text description for testing out of range GPS.",
        "latitude": "95.5",
        "longitude": "73.8567",
    }
    response = client.post("/api/complaints", data=data)
    assert response.status_code == 400
    assert "Latitude must be between -90 and 90" in response.json()["detail"]


def test_list_complaints(client):
    response = client.get("/api/complaints")
    assert response.status_code == 200
    body = response.json()
    assert "total" in body
    assert "items" in body
    assert body["total"] >= 2


def test_get_nonexistent_complaint_returns_404(client):
    response = client.get("/api/complaints/CMP-NONEXISTENT-999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
