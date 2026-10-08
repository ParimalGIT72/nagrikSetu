import io
import pytest
from fastapi import HTTPException, UploadFile
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.storage import sanitize_extension, save_complaint_image
from app.config import settings


def test_sanitize_extension():
    assert sanitize_extension("photo.JPG") == ".jpg"
    assert sanitize_extension("doc.png") == ".png"
    assert sanitize_extension("no_ext") == ""
    assert sanitize_extension(None) == ""


@pytest.mark.asyncio
async def test_save_complaint_image_unsupported_ext():
    file = UploadFile(
        filename="malicious.exe",
        file=io.BytesIO(b"executable data"),
    )
    with pytest.raises(HTTPException) as exc_info:
        await save_complaint_image(file, "CMP-TEST-001")
    assert exc_info.value.status_code == 400
    assert "Unsupported image format" in exc_info.value.detail


@pytest.mark.asyncio
async def test_save_complaint_image_empty_file():
    file = UploadFile(
        filename="empty.png",
        file=io.BytesIO(b""),
        headers={"content-type": "image/png"},
    )
    with pytest.raises(HTTPException) as exc_info:
        await save_complaint_image(file, "CMP-TEST-002")
    assert exc_info.value.status_code == 400
    assert "empty" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_save_complaint_image_valid(tmp_path):
    # Temporarily point settings.UPLOAD_DIR to tmp_path
    original_upload_dir = settings.UPLOAD_DIR
    settings.UPLOAD_DIR = tmp_path

    try:
        content = b"fake image bytes data for test"
        file = UploadFile(
            filename="road_pothole.jpg",
            file=io.BytesIO(content),
            headers={"content-type": "image/jpeg"},
        )
        saved_path = await save_complaint_image(file, "CMP-TEST-003")

        saved_file = Path(saved_path)
        assert saved_file.exists()
        assert saved_file.read_bytes() == content
        assert saved_file.suffix == ".jpg"
    finally:
        settings.UPLOAD_DIR = original_upload_dir
