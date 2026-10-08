import pytest
from fastapi import HTTPException
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.validation import validate_text, validate_coordinates


def test_validate_text_valid():
    text = "Pune road has a large pothole near FC Road."
    cleaned = validate_text(text)
    assert cleaned == text


def test_validate_text_empty():
    with pytest.raises(HTTPException) as exc_info:
        validate_text("")
    assert exc_info.value.status_code == 400
    assert "cannot be empty" in exc_info.value.detail


def test_validate_text_whitespace():
    with pytest.raises(HTTPException) as exc_info:
        validate_text("         ")
    assert exc_info.value.status_code == 400
    assert "cannot be empty" in exc_info.value.detail


def test_validate_text_too_short():
    with pytest.raises(HTTPException) as exc_info:
        validate_text("short")
    assert exc_info.value.status_code == 400
    assert "at least 10 characters" in exc_info.value.detail


def test_validate_text_too_long():
    long_text = "a" * 2001
    with pytest.raises(HTTPException) as exc_info:
        validate_text(long_text)
    assert exc_info.value.status_code == 400
    assert "exceeds maximum length" in exc_info.value.detail


def test_validate_coordinates_valid():
    lat, lon = validate_coordinates(18.5204, 73.8567)
    assert lat == 18.5204
    assert lon == 73.8567


def test_validate_coordinates_invalid_latitude():
    with pytest.raises(HTTPException) as exc_info:
        validate_coordinates(95.0, 73.8567)
    assert exc_info.value.status_code == 400
    assert "Latitude must be between -90 and 90" in exc_info.value.detail

    with pytest.raises(HTTPException) as exc_info:
        validate_coordinates(-90.1, 73.8567)
    assert exc_info.value.status_code == 400


def test_validate_coordinates_invalid_longitude():
    with pytest.raises(HTTPException) as exc_info:
        validate_coordinates(18.5204, 185.0)
    assert exc_info.value.status_code == 400
    assert "Longitude must be between -180 and 180" in exc_info.value.detail

    with pytest.raises(HTTPException) as exc_info:
        validate_coordinates(18.5204, -180.5)
    assert exc_info.value.status_code == 400
