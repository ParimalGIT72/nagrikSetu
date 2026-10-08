import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile, status
from app.config import settings


def sanitize_extension(filename: str | None) -> str:
    if not filename:
        return ""
    suffix = Path(filename).suffix.lower()
    return suffix


async def save_complaint_image(file: UploadFile, complaint_id: str) -> str:
    """
    Validates and stores an uploaded complaint image:
    1. Checks allowed file extensions and MIME types.
    2. Reads and checks file size against MAX_FILE_SIZE_MB limit.
    3. Generates a secure, non-guessable filename tied to complaint_id.
    4. Saves to disk in settings.UPLOAD_DIR.
    5. Returns the stored relative file path.
    """
    ext = sanitize_extension(file.filename)

    # 1. Validate file extension
    if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image format: '{ext}'. Allowed extensions are {', '.join(sorted(settings.ALLOWED_IMAGE_EXTENSIONS))}",
        )

    # 2. Validate MIME type
    if file.content_type and file.content_type.lower() not in settings.ALLOWED_IMAGE_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image format: MIME type '{file.content_type}' is not allowed",
        )

    # 3. Read content and validate file size
    contents = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB",
        )

    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image file is empty",
        )

    # 4. Generate safe unique filename
    random_token = uuid.uuid4().hex[:8]
    safe_filename = f"{complaint_id}_{random_token}{ext}"

    # 5. Ensure upload directory exists
    upload_dir = settings.UPLOAD_DIR
    upload_dir.mkdir(parents=True, exist_ok=True)

    dest_path = upload_dir / safe_filename
    with open(dest_path, "wb") as f:
        f.write(contents)

    # Return posix path string (e.g. "uploads/CMP-xxx_yyy.jpg")
    return dest_path.as_posix()
