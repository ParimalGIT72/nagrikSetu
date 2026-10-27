import pytest
from app.services.language_detection import analyze_script, detect_language


def test_analyze_script():
    # Pure Latin
    script, counts = analyze_script("There is a large pothole near FC Road.")
    assert script == "latin"
    assert counts["latin"] > 0
    assert counts["devanagari"] == 0

    # Pure Devanagari
    script, counts = analyze_script("रस्त्यावर खूप मोठा खड्डा आहे.")
    assert script == "devanagari"
    assert counts["devanagari"] > 0
    assert counts["latin"] == 0

    # Mixed
    script, counts = analyze_script("FC Road वर खूप मोठा खड्डा आहे")
    assert script == "mixed"
    assert counts["devanagari"] > 0
    assert counts["latin"] > 0


def test_detect_language_english():
    res = detect_language("There is a large pothole near FC Road.")
    assert res.language == "en"
    assert res.script == "latin"
    assert res.is_code_mixed is False
    assert res.confidence >= 0.80


def test_detect_language_marathi_devanagari():
    res = detect_language("रस्त्यावर खूप मोठा खड्डा आहे.")
    assert res.language == "mr"
    assert res.script == "devanagari"
    assert res.is_code_mixed is False
    assert res.confidence >= 0.85


def test_detect_language_hindi_devanagari():
    res = detect_language("सड़क पर बहुत बड़ा गड्ढा है।")
    assert res.language == "hi"
    assert res.script == "devanagari"
    assert res.is_code_mixed is False
    assert res.confidence >= 0.85


def test_detect_language_romanized_marathi():
    res = detect_language("rastyavar khup motha khadda aahe")
    assert res.language == "mr"
    assert res.script == "latin"
    assert res.is_code_mixed is False
    assert res.confidence >= 0.80


def test_detect_language_code_mixed():
    res = detect_language("Pune madhe road var khup motha pothole aahe")
    assert res.language == "mr-en"
    assert res.script == "latin"
    assert res.is_code_mixed is True
    assert res.confidence >= 0.80


def test_detect_language_short_input():
    res = detect_language("Pothole")
    assert res.language == "en"
    assert res.script == "latin"
    assert res.confidence >= 0.80


def test_detect_language_empty_input():
    res = detect_language("   ")
    assert res.language == "unknown"
    assert res.confidence == 0.0


def test_detect_language_romanized_hindi():
    res = detect_language("Sadak par bahut bada gaddha hai gaadi fis rahi hai.")
    assert res.language == "hi"
    assert res.script == "latin"
    assert res.is_code_mixed is False
    assert res.confidence >= 0.80


def test_detect_language_hindi_english_code_mixed():
    res = detect_language("Yahan road par bahut bada pothole hai please repair karo urgently.")
    assert res.language == "hi-en"
    assert res.script == "latin"
    assert res.is_code_mixed is True
    assert res.confidence >= 0.80


def test_detect_language_mixed_script():
    res = detect_language("FC Road वर खूप मोठा खड्डा आहे")
    assert res.script == "mixed"
    assert res.is_code_mixed is True
    assert res.language == "mr-en"


def test_tokenize_devanagari_preserves_matras_and_viramas():
    from app.services.language_detection import tokenize_words
    tokens = tokenize_words("यहाँ बहुत बड़ा गड्ढा है। खड्डा आहे.")
    assert "गड्ढा" in tokens
    assert "खड्डा" in tokens
    assert "है" in tokens
    assert "आहे" in tokens
