from fastapi import HTTPException, status

MIN_TEXT_LENGTH = 10
MAX_TEXT_LENGTH = 2000


def validate_text(text: str | None) -> str:
    """
    Validates complaint text:
    - Must not be None or empty.
    - Must not be whitespace-only.
    - Must have between 10 and 2000 characters.
    """
    if not text or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaint text cannot be empty",
        )

    cleaned = text.strip()

    if len(cleaned) < MIN_TEXT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Complaint text must be at least {MIN_TEXT_LENGTH} characters",
        )

    if len(cleaned) > MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Complaint text exceeds maximum length of {MAX_TEXT_LENGTH} characters",
        )

    return cleaned


def validate_coordinates(latitude: float, longitude: float) -> tuple[float, float]:
    """
    Validates geographic coordinates:
    - Latitude must be between -90 and 90.
    - Longitude must be between -180 and 180.
    """
    if latitude is None or not (-90.0 <= latitude <= 90.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Latitude must be between -90 and 90",
        )

    if longitude is None or not (-180.0 <= longitude <= 180.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Longitude must be between -180 and 180",
        )

    return latitude, longitude
