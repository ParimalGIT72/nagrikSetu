import json
import logging
from typing import Optional, Tuple

import httpx

from app.config import settings
from app.schemas.preprocessing import (
    DeterministicNormResult,
    LanguageDetectionResult,
    LLMNormalizationSchema,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert NLP normalization engine for Nagrik Setu, an Indian civic grievance portal in Maharashtra.
Your task is to take citizen grievance text (which may be in English, Marathi, Hindi, Romanized Indic, or Code-mixed) and produce clean, structured normalization.

Rules:
1. DO NOT discard or overwrite the citizen's original language in normalized_text.
2. If the text is in Marathi (Devanagari or Romanized), normalized_text MUST remain in Marathi (cleaned of typos, noise, or strange spacing).
3. If the text is in Hindi, normalized_text MUST remain in Hindi.
4. If the text is in English, normalized_text MUST remain in English.
5. Provide translation_en as an accurate, faithful English translation for downstream semantic search and indexing.
6. Identify language (e.g. 'en', 'mr', 'hi', 'mr-en', 'hi-en'), script ('latin', 'devanagari', 'mixed'), is_code_mixed (true/false), and confidence (0.0 to 1.0).

Return ONLY valid JSON matching this exact structure:
{
  "language": "mr",
  "script": "latin",
  "is_code_mixed": false,
  "normalized_text": "Cleaned complaint in original language",
  "translation_en": "Faithful English translation",
  "confidence": 0.95
}
"""


def call_gemini_api(text: str) -> Optional[LLMNormalizationSchema]:
    """
    Calls the Gemini REST API using httpx to normalize text into structured JSON.
    Returns None if API key is missing or call fails.
    """
    if not settings.GEMINI_API_KEY:
        logger.info("GEMINI_API_KEY not configured. Using deterministic normalizer.")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    prompt = f"{SYSTEM_PROMPT}\n\nCitizen Complaint Text:\n\"\"\"{text}\"\"\""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.1,
        },
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload)
            if response.status_code != 200:
                logger.warning(
                    f"Gemini API returned status {response.status_code}: {response.text}"
                )
                return None

            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return None

            raw_text = candidates[0]["content"]["parts"][0]["text"]
            # Validate with Pydantic
            validated = LLMNormalizationSchema.model_validate_json(raw_text)
            if text.strip() and (not validated.normalized_text or not validated.normalized_text.strip()):
                logger.warning("Gemini returned empty normalized_text for non-empty input; falling back.")
                return None
            return validated
    except Exception as e:
        logger.warning(f"Failed to normalize with Gemini API: {e}. Falling back to deterministic.")
        return None


def normalize_with_fallback(
    text: str,
    lang_result: LanguageDetectionResult,
    deterministic_result: DeterministicNormResult,
    force_llm: bool = False,
) -> Tuple[LLMNormalizationSchema, str]:
    """
    Coordinates normalization:
    - If force_llm or deterministic_result.needs_semantic_llm is True AND Gemini API is available:
      attempts LLM normalization.
    - Otherwise (or on LLM failure/absence): produces deterministic result.
    Returns (LLMNormalizationSchema, processing_method)
    """
    # Check if LLM is warranted
    should_try_llm = (force_llm or deterministic_result.needs_semantic_llm) and bool(settings.GEMINI_API_KEY)

    if should_try_llm:
        llm_res = call_gemini_api(text)
        if llm_res:
            return llm_res, f"gemini_{settings.GEMINI_MODEL}"

    # Deterministic fallback result
    fallback = LLMNormalizationSchema(
        language=lang_result.language,
        script=lang_result.script,
        is_code_mixed=lang_result.is_code_mixed,
        normalized_text=deterministic_result.normalized_text,
        translation_en=None,  # Deterministic mode does not translate
        confidence=lang_result.confidence,
    )
    return fallback, "deterministic"
