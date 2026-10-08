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

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
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


def test_process_complaint_lifecycle(client):
    # 1. Submit complaint
    submit_res = client.post(
        "/api/complaints",
        data={
            "text": "Pune madhe road var khup motha pothole aahe!!!!!!",
            "latitude": "18.5204",
            "longitude": "73.8567",
        },
    )
    assert submit_res.status_code == 201
    complaint_id = submit_res.json()["complaint_id"]
    assert submit_res.json()["status"] == "SUBMITTED"

    # 2. Trigger preprocessing
    proc_res = client.post(f"/api/complaints/{complaint_id}/process")
    assert proc_res.status_code == 200
    data = proc_res.json()

    assert data["complaint_id"] == complaint_id
    assert data["status"] == "COMPLETED"
    assert data["detected_language"] in ("mr-en", "mr")
    assert data["detected_script"] == "latin"
    assert data["is_code_mixed"] is True
    assert "!!!!!!" not in data["normalized_text"]
    assert "!" in data["normalized_text"]
    assert data["is_current"] is True

    record_id_1 = data["id"]

    # 3. Verify civic Complaint.status remains SUBMITTED
    detail_res = client.get(f"/api/complaints/{complaint_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["status"] == "SUBMITTED"

    # 4. Test Idempotency: second call returns the same preprocessing record
    proc_res_2 = client.post(f"/api/complaints/{complaint_id}/process")
    assert proc_res_2.status_code == 200
    data_2 = proc_res_2.json()
    assert data_2["id"] == record_id_1

    # 5. Test Force Re-processing: generates a new version
    proc_res_force = client.post(f"/api/complaints/{complaint_id}/process?force=true")
    assert proc_res_force.status_code == 200
    data_force = proc_res_force.json()
    assert data_force["id"] != record_id_1
    assert data_force["is_current"] is True

    # 6. Test GET preprocessing endpoint
    get_res = client.get(f"/api/complaints/{complaint_id}/preprocessing")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == data_force["id"]


def test_process_nonexistent_complaint(client):
    res = client.post("/api/complaints/CMP-NONEXISTENT/process")
    assert res.status_code == 404
