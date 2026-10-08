from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class LanguageEvidence(BaseModel):
    script: str
    script_counts: Dict[str, int] = Field(default_factory=dict)
    fasttext_label: Optional[str] = None
    fasttext_confidence: Optional[float] = None
    heuristic_markers: List[str] = Field(default_factory=list)


class LanguageDetectionResult(BaseModel):
    language: str = Field(description="ISO code: en, hi, mr, mr-en, hi-en, or unknown")
    script: str = Field(description="devanagari, latin, or mixed")
    confidence: float = Field(ge=0.0, le=1.0)
    is_code_mixed: bool = False
    evidence: Optional[LanguageEvidence] = None


class DeterministicNormResult(BaseModel):
    normalized_text: str
    modifications_applied: List[str] = Field(default_factory=list)
    needs_semantic_llm: bool = False


class LLMNormalizationSchema(BaseModel):
    language: str
    script: str
    is_code_mixed: bool
    normalized_text: str
    translation_en: Optional[str] = None
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)


class ComplaintPreprocessingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    complaint_id: str  # Public business ID (e.g. CMP-...)
    pipeline_version: str
    language_model: str
    normalization_model: str
    is_current: bool
    detected_language: str
    detected_script: str
    language_confidence: float
    is_code_mixed: bool
    original_text: str
    normalized_text: str
    translation_en: Optional[str] = None
    processing_method: str
    status: str
    created_at: datetime
    updated_at: datetime
