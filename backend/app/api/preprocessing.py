from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.models.complaint import Complaint
from app.models.preprocessing import ComplaintPreprocessing
from app.models.user import User
from app.schemas.preprocessing import ComplaintPreprocessingResponse
from app.services.preprocessing import (
    get_current_preprocessing,
    process_complaint_record,
)

router = APIRouter(prefix="/api/complaints", tags=["Preprocessing"])


def format_preprocessing_response(
    record: ComplaintPreprocessing, public_complaint_id: str
) -> ComplaintPreprocessingResponse:
    return ComplaintPreprocessingResponse(
        id=record.id,
        complaint_id=public_complaint_id,
        pipeline_version=record.pipeline_version,
        language_model=record.language_model,
        normalization_model=record.normalization_model,
        is_current=record.is_current,
        detected_language=record.detected_language,
        detected_script=record.detected_script,
        language_confidence=record.language_confidence,
        is_code_mixed=record.is_code_mixed,
        original_text=record.original_text,
        normalized_text=record.normalized_text,
        translation_en=record.translation_en,
        processing_method=record.processing_method,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.post(
    "/{complaint_id}/process",
    response_model=ComplaintPreprocessingResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger Phase 2 NLP preprocessing on a complaint",
)
def process_complaint(
    complaint_id: str,
    force: bool = Query(
        False, description="Force re-generation of preprocessing record even if one exists"
    ),
    pipeline_version: str = Query(
        "phase2-v1", description="Target pipeline version for processing"
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Phase 2 Core Endpoint:
    1. Fetches complaint by public complaint_id.
    2. Checks idempotency (reuses current record unless force=true).
    3. Executes language detection, script analysis, and text normalization.
    4. Persists record in complaint_preprocessing table.
    5. Leaves Complaint.status untouched (preserves civic workflow).
    """
    complaint = (
        db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    )
    if complaint is None or (user.role == "citizen" and complaint.user_id != user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint '{complaint_id}' not found",
        )

    record = process_complaint_record(
        db=db,
        complaint=complaint,
        force=force,
        pipeline_version=pipeline_version,
    )

    return format_preprocessing_response(record, complaint.complaint_id)


@router.get(
    "/{complaint_id}/preprocessing",
    response_model=ComplaintPreprocessingResponse,
    summary="Get current preprocessing details for a complaint",
)
def get_preprocessing(
    complaint_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves the currently active preprocessing record for a given complaint.
    """
    complaint = (
        db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    )
    if complaint is None or (user.role == "citizen" and complaint.user_id != user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint '{complaint_id}' not found",
        )

    record = get_current_preprocessing(db=db, complaint=complaint)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No preprocessing record found for complaint '{complaint_id}'. Call /process first.",
        )

    return format_preprocessing_response(record, complaint.complaint_id)
