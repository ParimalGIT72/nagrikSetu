import pytest
from app.services.normalization import (
    clean_unicode,
    normalize_elongated_chars,
    normalize_punctuation,
    normalize_text_deterministic,
    normalize_whitespace,
)


def test_clean_unicode():
    text_with_zwsp = "रस्ता\u200bवर"
    cleaned, changed = clean_unicode(text_with_zwsp)
    assert cleaned == "रस्तावर"
    assert changed is True


def test_normalize_whitespace():
    raw = "road     var     pothole     aahe   "
    cleaned, changed = normalize_whitespace(raw)
    assert cleaned == "road var pothole aahe"
    assert changed is True


def test_normalize_punctuation():
    raw = "ROAD VAR KHUP POTHOLE AAHE!!!!!!"
    cleaned, changed = normalize_punctuation(raw)
    assert cleaned == "ROAD VAR KHUP POTHOLE AAHE!"
    assert changed is True

    multi_q = "Why is this not fixed?????"
    cleaned_q, _ = normalize_punctuation(multi_q)
    assert cleaned_q == "Why is this not fixed?"


def test_normalize_elongated_chars():
    # 'p' is not standard doubled at word end -> reduced to 1
    raw = "khupppp"
    cleaned, changed = normalize_elongated_chars(raw)
    assert cleaned == "khup"
    assert changed is True

    # 's' runs reduced to 1 -> 'potholes'
    raw2 = "potholessss"
    cleaned2, changed2 = normalize_elongated_chars(raw2)
    assert cleaned2 == "potholes"
    assert changed2 is True


def test_preserve_capitalization():
    raw = "Pune Municipal Corporation on Senapati Bapat Road"
    res = normalize_text_deterministic(raw)
    assert res.normalized_text == "Pune Municipal Corporation on Senapati Bapat Road"


def test_deterministic_pipeline_clean_case():
    raw = "There is a large pothole near FC Road."
    res = normalize_text_deterministic(raw)
    assert res.normalized_text == "There is a large pothole near FC Road."
    assert res.needs_semantic_llm is False


def test_deterministic_pipeline_noisy_case():
    raw = "PUNE MADHE ROAD VAR KHUPPPPPP POTHOLE AAHE!!!!!!"
    res = normalize_text_deterministic(raw)
    assert "!" in res.normalized_text
    assert "!!!!!!" not in res.normalized_text
    assert res.needs_semantic_llm is True


def test_normalize_empty_and_whitespace_only():
    """Empty and whitespace-only text should safely produce empty strings without error."""
    assert normalize_text_deterministic("").normalized_text == ""
    assert normalize_text_deterministic("   \t\n  ").normalized_text == ""


def test_no_accidental_deletion_of_civic_content():
    """Ensures meaningful complaint details like ward numbers, plot info, phone numbers are preserved."""
    raw = "Ward 15, Plot #234, Lane 7: Water leakage since 3 days! Call 9876543210."
    res = normalize_text_deterministic(raw)
    assert "Ward 15" in res.normalized_text
    assert "Plot #234" in res.normalized_text
    assert "9876543210" in res.normalized_text


def test_clean_text_remains_unchanged_indic():
    """Clean Hindi and Marathi text must not be altered by normalization."""
    mr_clean = "रस्त्यावर खूप मोठा खड्डा आहे."
    hi_clean = "सड़क पर बहुत बड़ा गड्ढा है।"
    assert normalize_text_deterministic(mr_clean).normalized_text == mr_clean
    assert normalize_text_deterministic(hi_clean).normalized_text == hi_clean
    assert normalize_text_deterministic(mr_clean).needs_semantic_llm is False
    assert normalize_text_deterministic(hi_clean).needs_semantic_llm is False
