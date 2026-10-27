"""
tests/test_llm_normalizer.py

Mock-based unit tests for Gemini semantic normalization and deterministic fallback.
Validates:
  - Successful Gemini response and schema validation
  - Missing API key handling
  - HTTP 4xx (invalid key, bad request)
  - HTTP 429 (quota exhaustion / rate limiting)
  - HTTP 5xx (internal server error)
  - Network timeouts and connection errors
  - Malformed JSON / unexpected schema from LLM
  - Empty or invalid model output safety guard
  - Deterministic fallback contract (preserves complaint, translation_en=None)
  - Conditional invocation logic (no unnecessary Gemini calls for clean complaints)
"""

import json
from unittest.mock import MagicMock, patch
import httpx
import pytest

from app.config import settings
from app.schemas.preprocessing import (
    DeterministicNormResult,
    LanguageDetectionResult,
    LanguageEvidence,
    LLMNormalizationSchema,
)
from app.services.llm_normalizer import call_gemini_api, normalize_with_fallback


@pytest.fixture
def sample_lang_result():
    return LanguageDetectionResult(
        language="mr-en",
        script="latin",
        confidence=0.88,
        is_code_mixed=True,
        evidence=LanguageEvidence(script="latin", script_counts={"latin": 25}, heuristic_markers=["aahe", "madhe"]),
    )


@pytest.fixture
def sample_det_result_clean():
    return DeterministicNormResult(
        normalized_text="Pune madhe road var khup motha pothole aahe please fix.",
        modifications_applied=[],
        needs_semantic_llm=False,
    )


@pytest.fixture
def sample_det_result_noisy():
    return DeterministicNormResult(
        normalized_text="PUNE MADHE ROAD VAR KHUP POTHOLE AAHE!",
        modifications_applied=["whitespace_collapsed", "punctuation_deduplicated", "elongated_characters_reduced"],
        needs_semantic_llm=True,
    )


def _mock_gemini_response(status_code: int = 200, json_data: dict = None, text_data: str = None):
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = status_code
    if json_data is not None:
        mock_resp.json.return_value = json_data
    if text_data is not None:
        mock_resp.text = text_data
    else:
        mock_resp.text = json.dumps(json_data) if json_data else ""
    return mock_resp


def test_gemini_success(monkeypatch):
    """Verifies that a valid Gemini API response is correctly parsed and returned."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "mock-test-key-12345")
    monkeypatch.setattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")

    valid_llm_json = {
        "language": "mr-en",
        "script": "latin",
        "is_code_mixed": True,
        "normalized_text": "Pune madhe road var khup motha pothole aahe please fix.",
        "translation_en": "There is a very big pothole on the road in Pune, please fix it.",
        "confidence": 0.95,
    }

    mock_gemini_api_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": json.dumps(valid_llm_json)}]
                }
            }
        ]
    }

    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value = _mock_gemini_response(200, json_data=mock_gemini_api_payload)

        result = call_gemini_api("Pune madhe road var khupppp pothole aahe!!!!!!")
        assert result is not None
        assert isinstance(result, LLMNormalizationSchema)
        assert result.language == "mr-en"
        assert result.normalized_text == "Pune madhe road var khup motha pothole aahe please fix."
        assert result.translation_en == "There is a very big pothole on the road in Pune, please fix it."
        assert result.confidence == 0.95


def test_gemini_missing_api_key(monkeypatch, sample_lang_result, sample_det_result_noisy):
    """When GEMINI_API_KEY is empty, no external API call is made and fallback is used."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")

    with patch("httpx.Client.post") as mock_post:
        # 1. call_gemini_api returns None immediately
        res = call_gemini_api("Some noisy complaint")
        assert res is None
        mock_post.assert_not_called()

        # 2. normalize_with_fallback returns deterministic fallback
        norm_res, method = normalize_with_fallback(
            "Some noisy complaint",
            lang_result=sample_lang_result,
            deterministic_result=sample_det_result_noisy,
            force_llm=True,
        )
        assert method == "deterministic"
        assert norm_res.normalized_text == sample_det_result_noisy.normalized_text
        assert norm_res.translation_en is None
        mock_post.assert_not_called()


def test_gemini_http_4xx_invalid_api_key(monkeypatch, sample_lang_result, sample_det_result_noisy):
    """HTTP 400/403 (invalid key, bad payload) logs warning and triggers deterministic fallback."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "invalid-key")

    error_payload = {
        "error": {
            "code": 403,
            "message": "API key not valid. Please pass a valid API key.",
            "status": "PERMISSION_DENIED",
        }
    }

    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value = _mock_gemini_response(403, json_data=error_payload)

        res, method = normalize_with_fallback(
            "Some complaint text",
            lang_result=sample_lang_result,
            deterministic_result=sample_det_result_noisy,
            force_llm=True,
        )
        assert method == "deterministic"
        assert res.normalized_text == sample_det_result_noisy.normalized_text
        assert res.translation_en is None


def test_gemini_http_429_quota_exceeded(monkeypatch, sample_lang_result, sample_det_result_noisy):
    """HTTP 429 quota exhaustion safely falls back to deterministic normalization."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "exhausted-key")

    error_payload = {
        "error": {
            "code": 429,
            "message": "Resource has been exhausted (e.g. check quota).",
            "status": "RESOURCE_EXHAUSTED",
        }
    }

    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value = _mock_gemini_response(429, json_data=error_payload)

        res, method = normalize_with_fallback(
            "Some complaint text",
            lang_result=sample_lang_result,
            deterministic_result=sample_det_result_noisy,
            force_llm=True,
        )
        assert method == "deterministic"
        assert res.normalized_text == sample_det_result_noisy.normalized_text


def test_gemini_http_5xx_server_error(monkeypatch, sample_lang_result, sample_det_result_noisy):
    """HTTP 500/503 server error safely falls back to deterministic normalization."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "valid-key")

    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value = _mock_gemini_response(503, text_data="Service Unavailable")

        res, method = normalize_with_fallback(
            "Some complaint text",
            lang_result=sample_lang_result,
            deterministic_result=sample_det_result_noisy,
            force_llm=True,
        )
        assert method == "deterministic"
        assert res.normalized_text == sample_det_result_noisy.normalized_text


def test_gemini_network_timeout(monkeypatch, sample_lang_result, sample_det_result_noisy):
    """Network connection/read timeout safely falls back without raising unhandled exception."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "valid-key")

    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Read timed out")):
        res, method = normalize_with_fallback(
            "Some complaint text",
            lang_result=sample_lang_result,
            deterministic_result=sample_det_result_noisy,
            force_llm=True,
        )
        assert method == "deterministic"
        assert res.normalized_text == sample_det_result_noisy.normalized_text


def test_gemini_malformed_json_response(monkeypatch, sample_lang_result, sample_det_result_noisy):
    """Malformed or invalid JSON inside candidate parts safely falls back."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "valid-key")

    malformed_candidate = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "This is not json {bad_syntax"}]
                }
            }
        ]
    }

    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value = _mock_gemini_response(200, json_data=malformed_candidate)

        res, method = normalize_with_fallback(
            "Some complaint text",
            lang_result=sample_lang_result,
            deterministic_result=sample_det_result_noisy,
            force_llm=True,
        )
        assert method == "deterministic"
        assert res.normalized_text == sample_det_result_noisy.normalized_text


def test_gemini_empty_model_output_safety(monkeypatch, sample_lang_result, sample_det_result_noisy):
    """If Gemini returns an empty normalized_text for a non-empty complaint, it is discarded."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "valid-key")

    empty_output = {
        "language": "mr",
        "script": "latin",
        "is_code_mixed": False,
        "normalized_text": "   ",  # blank output!
        "translation_en": None,
        "confidence": 0.0,
    }

    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": json.dumps(empty_output)}]
                }
            }
        ]
    }

    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value = _mock_gemini_response(200, json_data=payload)

        # Output discarded, falls back to deterministic to prevent data loss
        res, method = normalize_with_fallback(
            "Pothole on Main Road",
            lang_result=sample_lang_result,
            deterministic_result=sample_det_result_noisy,
            force_llm=True,
        )
        assert method == "deterministic"
        assert res.normalized_text == sample_det_result_noisy.normalized_text


def test_deterministic_fallback_contract(monkeypatch, sample_lang_result, sample_det_result_noisy):
    """
    Validates deterministic fallback contract:
    - Never fabricates a translation (translation_en MUST be None)
    - Preserves language detection results (language, script, is_code_mixed, confidence)
    - Returns normalized_text from deterministic result
    """
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    res, method = normalize_with_fallback(
        "PUNE MADHE ROAD VAR KHUPPPPPP POTHOLE AAHE!!!!!!",
        lang_result=sample_lang_result,
        deterministic_result=sample_det_result_noisy,
        force_llm=False,
    )
    assert method == "deterministic"
    assert res.translation_en is None
    assert res.language == sample_lang_result.language
    assert res.script == sample_lang_result.script
    assert res.is_code_mixed == sample_lang_result.is_code_mixed
    assert res.confidence == sample_lang_result.confidence
    assert res.normalized_text == sample_det_result_noisy.normalized_text


def test_decision_path_no_unnecessary_gemini_call(monkeypatch, sample_lang_result, sample_det_result_clean):
    """
    Clean complaints that do not need semantic LLM (needs_semantic_llm=False, force_llm=False)
    do NOT invoke Gemini, saving API quota and reducing latency.
    """
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "valid-key-configured")

    with patch("httpx.Client.post") as mock_post:
        res, method = normalize_with_fallback(
            "There is a large pothole near FC Road.",
            lang_result=sample_lang_result,
            deterministic_result=sample_det_result_clean,
            force_llm=False,
        )
        assert method == "deterministic"
        assert res.normalized_text == sample_det_result_clean.normalized_text
        mock_post.assert_not_called()
