import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_staff
from app.db.database import get_db
from app.models.complaint import Complaint
from app.models.user import User
from app.schemas.complaint import (
    ComplaintListResponse,
    ComplaintResponse,
    ComplaintSubmissionResponse,
)
from app.services.moderation import moderate_text
from app.services.storage import save_complaint_image
from app.services.validation import validate_coordinates, validate_text

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])


def generate_complaint_id() -> str:
    """
    Generates a citizen-facing unique complaint identifier,
    e.g. CMP-20260921-A1B2C3
    """
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    short_token = uuid.uuid4().hex[:6].upper()
    return f"CMP-{date_str}-{short_token}"


@router.post(
    "",
    response_model=ComplaintSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new citizen complaint",
)
async def submit_complaint(
    text: str = Form(..., description="Complaint description (10-2000 chars)"),
    latitude: float = Form(..., description="GPS latitude (-90 to 90)"),
    longitude: float = Form(..., description="GPS longitude (-180 to 180)"),
    image: Optional[UploadFile] = File(None, description="Optional supporting photo (max 5MB, jpg/png/webp)"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Phase 1 Core Endpoint:
    1. Validates text content and length.
    2. Validates GPS coordinates.
    3. Runs deterministic rule-based spam/profanity moderation (flags if triggered).
    4. Validates and saves uploaded image (if provided).
    5. Saves immutable record in PostgreSQL.
    6. Returns generated public complaint ID.
    """
    # 1. Validation
    cleaned_text = validate_text(text)
    lat, lon = validate_coordinates(latitude, longitude)

    # 2. Moderation check
    is_flagged, flag_reason = moderate_text(cleaned_text)

    # 3. Generate unique citizen-facing ID
    complaint_id = generate_complaint_id()

    # 4. Handle optional image storage
    saved_image_path: Optional[str] = None
    if image and image.filename:
        saved_image_path = await save_complaint_image(image, complaint_id)

    # 5. Persist in database
    db_complaint = Complaint(
        user_id=user.id,
        complaint_id=complaint_id,
        text=cleaned_text,
        latitude=lat,
        longitude=lon,
        image_path=saved_image_path,
        status="SUBMITTED",
        is_flagged=is_flagged,
        flag_reason=flag_reason,
    )
    db.add(db_complaint)
    db.commit()
    db.refresh(db_complaint)

    return ComplaintSubmissionResponse(
        complaint_id=db_complaint.complaint_id,
        status=db_complaint.status,
        message="Complaint successfully registered.",
    )


@router.get(
    "",
    response_model=ComplaintListResponse,
    summary="List complaints",
)
def list_complaints(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (e.g. SUBMITTED)"),
    limit: int = Query(50, ge=1, le=100, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    _: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """
    Returns list of complaints ordered newest first, with optional status filter.
    """
    query = db.query(Complaint)
    if status_filter:
        query = query.filter(Complaint.status == status_filter.upper())

    total = query.count()
    items = query.order_by(Complaint.created_at.desc()).offset(offset).limit(limit).all()

    return ComplaintListResponse(total=total, items=items)


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    summary="Get complaint details by ID",
)
def get_complaint(
    complaint_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Fetches full details of a single complaint by its public complaint ID.
    """
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if complaint is None or (user.role == "citizen" and complaint.user_id != user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint '{complaint_id}' not found",
        )
    return complaint
