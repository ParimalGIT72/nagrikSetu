import json
from unittest.mock import MagicMock, patch
import httpx
import pytest

from app.config import settings


def _mock_gemini_response(status_code: int = 200, json_data: dict = None):
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = status_code
    if json_data is not None:
        mock_resp.json.return_value = json_data
        mock_resp.text = json.dumps(json_data)
    else:
        mock_resp.text = ""
    return mock_resp


def test_process_complaint_lifecycle(client, citizen_headers):
    # 1. Submit complaint (now auto-preprocesses in Phase 2)
    submit_res = client.post(
        "/api/complaints",
        data={
            "text": "Pune madhe road var khup motha pothole aahe!!!!!!",
            "latitude": "18.5204",
            "longitude": "73.8567",
        },
        headers=citizen_headers,
    )
    assert submit_res.status_code == 201
    complaint_id = submit_res.json()["complaint_id"]
    assert submit_res.json()["status"] == "SUBMITTED"

    # 2. Trigger manual preprocessing (idempotent; reuses auto-generated record)
    proc_res = client.post(f"/api/complaints/{complaint_id}/process", headers=citizen_headers)
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
    detail_res = client.get(f"/api/complaints/{complaint_id}", headers=citizen_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["status"] == "SUBMITTED"

    # 4. Test Idempotency: second call returns the same preprocessing record
    proc_res_2 = client.post(f"/api/complaints/{complaint_id}/process", headers=citizen_headers)
    assert proc_res_2.status_code == 200
    data_2 = proc_res_2.json()
    assert data_2["id"] == record_id_1

    # 5. Test Force Re-processing: generates a new version
    proc_res_force = client.post(
        f"/api/complaints/{complaint_id}/process?force=true", headers=citizen_headers
    )
    assert proc_res_force.status_code == 200
    data_force = proc_res_force.json()
    assert data_force["id"] != record_id_1
    assert data_force["is_current"] is True

    # 6. Test GET preprocessing endpoint
    get_res = client.get(
        f"/api/complaints/{complaint_id}/preprocessing", headers=citizen_headers
    )
    assert get_res.status_code == 200
    assert get_res.json()["id"] == data_force["id"]


def test_process_nonexistent_complaint(client, citizen_headers):
    res = client.post("/api/complaints/CMP-NONEXISTENT/process", headers=citizen_headers)
    assert res.status_code == 404


def test_submit_complaint_automatically_creates_preprocessing_record(client, citizen_headers):
    """
    Submitting a complaint via POST /api/complaints automatically executes
    Phase 2 preprocessing and persists a record in complaint_preprocessing.
    """
    submit_res = client.post(
        "/api/complaints",
        data={
            "text": "Karve road var heavy monsoon nantar deep crater zala aahe.",
            "latitude": "18.5074",
            "longitude": "73.8077",
        },
        headers=citizen_headers,
    )
    assert submit_res.status_code == 201
    complaint_id = submit_res.json()["complaint_id"]

    # Directly fetch preprocessing record without manually calling /process
    prep_res = client.get(f"/api/complaints/{complaint_id}/preprocessing", headers=citizen_headers)
    assert prep_res.status_code == 200
    data = prep_res.json()
    assert data["complaint_id"] == complaint_id
    assert data["status"] == "COMPLETED"
    assert data["is_current"] is True
    assert data["detected_language"] in ("mr-en", "mr")
    assert data["detected_script"] == "latin"
    assert data["is_code_mixed"] is True
    assert data["original_text"] == "Karve road var heavy monsoon nantar deep crater zala aahe."
    assert data["processing_method"] == "deterministic"


def test_submit_marathi_complaint_gemini_success(client, citizen_headers, monkeypatch):
    """
    Submitting a complaint requiring semantic normalization with an active Gemini API
    successfully records language metadata and faithful English translation.
    """
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "mock-gemini-key")
    monkeypatch.setattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")

    from app.schemas.preprocessing import LLMNormalizationSchema
    mock_llm_schema = LLMNormalizationSchema(
        language="mr",
        script="devanagari",
        is_code_mixed=False,
        normalized_text="रस्त्यावर खूप मोठा खड्डा पडला आहे.",
        translation_en="There is a very large pothole on the road.",
        confidence=0.98,
    )

    with patch("app.services.llm_normalizer.call_gemini_api", return_value=mock_llm_schema):
        submit_res = client.post(
            "/api/complaints",
            data={
                "text": "PUNE ROAD KHUPPPPPP MOTHA KHADDA AHE DANGEROUS FIX",  # triggers elongation & ALL-CAPS
                "latitude": "18.5204",
                "longitude": "73.8567",
            },
            headers=citizen_headers,
        )
        assert submit_res.status_code == 201
        complaint_id = submit_res.json()["complaint_id"]

        prep_res = client.get(f"/api/complaints/{complaint_id}/preprocessing", headers=citizen_headers)
        assert prep_res.status_code == 200
        data = prep_res.json()
        assert data["detected_language"] == "mr"
        assert data["detected_script"] == "devanagari"
        assert data["translation_en"] == "There is a very large pothole on the road."
        assert data["processing_method"] == f"gemini_{settings.GEMINI_MODEL}"
        assert data["status"] == "COMPLETED"


def test_submit_marathi_complaint_gemini_fallback(client, citizen_headers, monkeypatch):
    """
    When Gemini API fails (e.g. HTTP 429 quota exhaustion returning None), the pipeline safely falls
    back to deterministic normalization without claiming translation.
    """
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "mock-gemini-key")

    with patch("app.services.llm_normalizer.call_gemini_api", return_value=None):
        submit_res = client.post(
            "/api/complaints",
            data={
                "text": "PUNE MADHE ROAD VAR KHUPPPPPP POTHOLE AAHE!!!!!!",
                "latitude": "18.5204",
                "longitude": "73.8567",
            },
            headers=citizen_headers,
        )
        assert submit_res.status_code == 201
        complaint_id = submit_res.json()["complaint_id"]

        prep_res = client.get(f"/api/complaints/{complaint_id}/preprocessing", headers=citizen_headers)
        assert prep_res.status_code == 200
        data = prep_res.json()
        assert data["status"] == "COMPLETED"
        assert data["processing_method"] == "deterministic"
        assert data["translation_en"] is None
        assert "KHUP" in data["normalized_text"]
        assert "!" in data["normalized_text"]
        assert "!!!!!!" not in data["normalized_text"]


def test_submit_complaint_preprocessing_failure_resilience(client, citizen_headers):
    """
    If the preprocessing service crashes unexpectedly, complaint submission MUST NOT fail.
    The complaint record is safely committed with status SUBMITTED, and preprocessing
    can be re-triggered later via the manual /process endpoint.
    """
    with patch(
        "app.api.complaints.process_complaint_record",
        side_effect=RuntimeError("Simulated unexpected preprocessing crash"),
    ):
        submit_res = client.post(
            "/api/complaints",
            data={
                "text": "Water pipeline burst near Swargate station area.",
                "latitude": "18.5018",
                "longitude": "73.8586",
            },
            headers=citizen_headers,
        )
        # Complaint creation succeeds regardless of preprocessing failure
        assert submit_res.status_code == 201
        complaint_id = submit_res.json()["complaint_id"]
        assert submit_res.json()["status"] == "SUBMITTED"

    # Verify complaint itself is intact in the database
    detail_res = client.get(f"/api/complaints/{complaint_id}", headers=citizen_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["complaint_id"] == complaint_id

    # No preprocessing record exists yet because the auto-call was intercepted
    prep_res = client.get(f"/api/complaints/{complaint_id}/preprocessing", headers=citizen_headers)
    assert prep_res.status_code == 404

    # Manual retry succeeds cleanly
    retry_res = client.post(f"/api/complaints/{complaint_id}/process", headers=citizen_headers)
    assert retry_res.status_code == 200
    assert retry_res.json()["status"] == "COMPLETED"
    assert retry_res.json()["complaint_id"] == complaint_id


def test_manual_process_idempotency_preserves_auto_record(client, citizen_headers):
    """
    Calling POST /api/complaints/{id}/process on an already preprocessed complaint
    does not create duplicate records; force=true properly versions it.
    """
    submit_res = client.post(
        "/api/complaints",
        data={
            "text": "Drainage gutter overflow near market place.",
            "latitude": "18.5100",
            "longitude": "73.8500",
        },
        headers=citizen_headers,
    )
    assert submit_res.status_code == 201
    complaint_id = submit_res.json()["complaint_id"]

    # Initial auto-created record
    auto_res = client.get(f"/api/complaints/{complaint_id}/preprocessing", headers=citizen_headers)
    assert auto_res.status_code == 200
    auto_id = auto_res.json()["id"]

    # Manual trigger without force returns same record
    manual_res = client.post(f"/api/complaints/{complaint_id}/process", headers=citizen_headers)
    assert manual_res.status_code == 200
    assert manual_res.json()["id"] == auto_id

    # Manual trigger with force=true creates new version
    force_res = client.post(f"/api/complaints/{complaint_id}/process?force=true", headers=citizen_headers)
    assert force_res.status_code == 200
    assert force_res.json()["id"] != auto_id
    assert force_res.json()["is_current"] is True
