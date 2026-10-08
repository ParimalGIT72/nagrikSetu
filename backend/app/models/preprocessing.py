from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class ComplaintPreprocessing(Base):
    __tablename__ = "complaint_preprocessing"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    complaint_id = Column(
        Integer,
        ForeignKey("complaints.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    pipeline_version = Column(String(32), default="phase2-v1", nullable=False)
    language_model = Column(String(64), default="fasttext-lid176", nullable=False)
    normalization_model = Column(String(64), default="deterministic-v1", nullable=False)
    is_current = Column(Boolean, default=True, index=True, nullable=False)

    detected_language = Column(String(16), nullable=False)
    detected_script = Column(String(16), nullable=False)
    language_confidence = Column(Float, nullable=False)
    is_code_mixed = Column(Boolean, default=False, nullable=False)

    original_text = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=False)
    translation_en = Column(Text, nullable=True)

    processing_method = Column(String(32), default="deterministic", nullable=False)
    status = Column(String(32), default="COMPLETED", nullable=False)
    error_message = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    complaint = relationship("Complaint", back_populates="preprocessing_records")
