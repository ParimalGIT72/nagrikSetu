import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.models.preprocessing import ComplaintPreprocessing
from app.services.language_detection import detect_language
from app.services.llm_normalizer import normalize_with_fallback
from app.services.normalization import normalize_text_deterministic

logger = logging.getLogger(__name__)


def process_complaint_record(
    db: Session,
    complaint: Complaint,
    force: bool = False,
    pipeline_version: str = "phase2-v1",
) -> ComplaintPreprocessing:
    """
    Executes the Phase 2 NLP preprocessing pipeline on a complaint record.
    Idempotent: if a current preprocessing record for this pipeline version
    already exists and force=False, reuses and returns it immediately.
    """
    # 1. Idempotency check: Reuse existing active record if not forced
    existing_record = (
        db.query(ComplaintPreprocessing)
        .filter(
            ComplaintPreprocessing.complaint_id == complaint.id,
            ComplaintPreprocessing.pipeline_version == pipeline_version,
            ComplaintPreprocessing.is_current.is_(True),
        )
        .first()
    )

    if existing_record and not force:
        logger.info(
            f"Reusing existing preprocessing record {existing_record.id} for complaint {complaint.complaint_id}"
        )
        return existing_record

    # 2. If forcing re-process, mark any previous current records as inactive
    if force and existing_record:
        existing_record.is_current = False
        db.add(existing_record)

    # 3. Execute NLP Pipeline
    try:
        # Step A: Language & Script Detection
        lang_res = detect_language(complaint.text)

        # Step B: Deterministic Normalization
        det_norm = normalize_text_deterministic(complaint.text)

        # Step C: LLM Normalization (if needed & key present) or Fallback
        norm_res, method = normalize_with_fallback(
            complaint.text,
            lang_result=lang_res,
            deterministic_result=det_norm,
            force_llm=False,
        )

        # Step D: Save Preprocessing Record
        record = ComplaintPreprocessing(
            complaint_id=complaint.id,
            pipeline_version=pipeline_version,
            language_model="fasttext-lid176",
            normalization_model=method,
            is_current=True,
            detected_language=norm_res.language,
            detected_script=norm_res.script,
            language_confidence=norm_res.confidence,
            is_code_mixed=norm_res.is_code_mixed,
            original_text=complaint.text,
            normalized_text=norm_res.normalized_text,
            translation_en=norm_res.translation_en,
            processing_method=method,
            status="COMPLETED",
            error_message=None,
        )
    except Exception as e:
        logger.error(f"Error preprocessing complaint {complaint.complaint_id}: {e}")
        record = ComplaintPreprocessing(
            complaint_id=complaint.id,
            pipeline_version=pipeline_version,
            language_model="fasttext-lid176",
            normalization_model="failed",
            is_current=True,
            detected_language="unknown",
            detected_script="unknown",
            language_confidence=0.0,
            is_code_mixed=False,
            original_text=complaint.text,
            normalized_text=complaint.text,
            translation_en=None,
            processing_method="failed",
            status="FAILED",
            error_message=str(e),
        )

    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_current_preprocessing(
    db: Session, complaint: Complaint
) -> Optional[ComplaintPreprocessing]:
    """
    Fetches the currently active preprocessing record for a given complaint.
    """
    return (
        db.query(ComplaintPreprocessing)
        .filter(
            ComplaintPreprocessing.complaint_id == complaint.id,
            ComplaintPreprocessing.is_current.is_(True),
        )
        .order_by(ComplaintPreprocessing.created_at.desc())
        .first()
    )
