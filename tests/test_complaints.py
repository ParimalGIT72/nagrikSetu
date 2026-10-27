import io
import uuid
from app.config import settings
from app.models.user import User
from app.services.authentication import create_access_token, hash_password


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_submit_valid_complaint_text_and_gps(client, citizen_headers):
    data = {
        "text": "Pune road has a large pothole near FC Road.",
        "latitude": "18.5204",
        "longitude": "73.8567",
    }
    response = client.post("/api/complaints", data=data, headers=citizen_headers)
    assert response.status_code == 201
    body = response.json()
    assert "complaint_id" in body
    assert body["complaint_id"].startswith("CMP-")
    assert body["status"] == "SUBMITTED"

    # Verify retrieval
    cid = body["complaint_id"]
    get_res = client.get(f"/api/complaints/{cid}", headers=citizen_headers)
    assert get_res.status_code == 200
    complaint = get_res.json()
    assert complaint["complaint_id"] == cid
    assert complaint["text"] == data["text"]
    assert complaint["latitude"] == 18.5204
    assert complaint["longitude"] == 73.8567
    assert complaint["status"] == "SUBMITTED"
    assert complaint["image_path"] is None
    assert complaint["is_flagged"] is False
    history = client.get("/api/auth/me/complaints", headers=citizen_headers)
    assert history.status_code == 200
    assert [item["complaint_id"] for item in history.json()["items"]] == [cid]


def test_complaint_submission_requires_authentication(client):
    response = client.post(
        "/api/complaints",
        data={
            "text": "Pune road has a large pothole near FC Road.",
            "latitude": "18.5204",
            "longitude": "73.8567",
        },
    )
    assert response.status_code == 401


def test_submit_complaint_with_image(client, citizen_headers, tmp_path):
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
        response = client.post("/api/complaints", data=data, files=files, headers=citizen_headers)
        assert response.status_code == 201
        body = response.json()
        cid = body["complaint_id"]

        get_res = client.get(f"/api/complaints/{cid}", headers=citizen_headers)
        assert get_res.status_code == 200
        complaint = get_res.json()
        assert complaint["image_path"] is not None
        assert "garbage" not in complaint["image_path"]  # Safe renamed filename
        assert complaint["image_path"].endswith(".png")
    finally:
        settings.UPLOAD_DIR = orig_upload_dir


def test_complaint_image_requires_owner_or_staff(
    client, citizen_headers, db_session, tmp_path
):
    orig_upload_dir = settings.UPLOAD_DIR
    settings.UPLOAD_DIR = tmp_path
    try:
        response = client.post(
            "/api/complaints",
            data={
                "text": "A damaged streetlight is leaning over the footpath.",
                "latitude": "18.5204",
                "longitude": "73.8567",
            },
            files={"image": ("lamp.png", io.BytesIO(b"image data"), "image/png")},
            headers=citizen_headers,
        )
        assert response.status_code == 201
        complaint_id = response.json()["complaint_id"]
        image_url = f"/api/complaints/{complaint_id}/image"

        assert client.get(image_url).status_code == 401
        owner_response = client.get(image_url, headers=citizen_headers)
        assert owner_response.status_code == 200
        assert owner_response.content == b"image data"

        other_user = User(
            email=f"other-{uuid.uuid4().hex}@example.test",
            password_hash=hash_password("A-long-test-password-123!"),
            role="citizen",
            is_active=True,
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)
        token, _ = create_access_token(other_user)
        other_response = client.get(
            image_url, headers={"Authorization": f"Bearer {token}"}
        )
        assert other_response.status_code == 404
    finally:
        settings.UPLOAD_DIR = orig_upload_dir


def test_submit_complaint_empty_text_rejected(client, citizen_headers):
    data = {
        "text": "   ",
        "latitude": "18.5204",
        "longitude": "73.8567",
    }
    response = client.post("/api/complaints", data=data, headers=citizen_headers)
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]


def test_submit_complaint_invalid_coordinates(client, citizen_headers):
    data = {
        "text": "Valid text description for testing out of range GPS.",
        "latitude": "95.5",
        "longitude": "73.8567",
    }
    response = client.post("/api/complaints", data=data, headers=citizen_headers)
    assert response.status_code == 400
    assert "Latitude must be between -90 and 90" in response.json()["detail"]


def test_list_complaints(client, officer_headers):
    response = client.get("/api/complaints", headers=officer_headers)
    assert response.status_code == 200
    body = response.json()
    assert "total" in body
    assert "items" in body
    assert body["total"] >= len(body["items"])


def test_citizen_cannot_use_global_complaint_list(client, citizen_headers):
    response = client.get("/api/complaints", headers=citizen_headers)
    assert response.status_code == 403


def test_get_nonexistent_complaint_returns_404(client, citizen_headers):
    response = client.get("/api/complaints/CMP-NONEXISTENT-999", headers=citizen_headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
