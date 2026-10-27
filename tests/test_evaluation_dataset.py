import json
from pathlib import Path
import pytest

from app.services.language_detection import detect_language
from app.services.normalization import normalize_text_deterministic

REQUIRED_FIELDS = {
    "id",
    "category",
    "eval_group",
    "original_text",
    "expected_language",
    "expected_script",
    "is_code_mixed",
    "expected_normalized_text",
    "label_source",
}

VALID_LANGUAGES = {"en", "mr", "hi", "mr-en", "hi-en", "unknown"}
VALID_SCRIPTS = {"latin", "devanagari", "mixed", "unknown"}
VALID_SOURCES = {"unambiguous", "curated", "review_needed"}


@pytest.fixture(scope="module")
def eval_dataset():
    dataset_path = Path(__file__).resolve().parent.parent / "ml" / "data" / "multilingual_eval_300.json"
    assert dataset_path.exists(), "Multilingual evaluation dataset must exist at ml/data/multilingual_eval_300.json"
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_eval_dataset_schema_and_integrity(eval_dataset):
    """
    Validates dataset structural integrity, completeness, and schema conformance.
    """
    total = len(eval_dataset)
    assert total == 300, f"Expected 300 cases, found {total}"

    seen_ids = set()
    for idx, c in enumerate(eval_dataset):
        cid = c.get("id")
        assert cid, f"Record at index {idx} missing 'id'"
        assert cid not in seen_ids, f"Duplicate ID found: {cid}"
        seen_ids.add(cid)

        missing = REQUIRED_FIELDS - set(c.keys())
        assert not missing, f"Case {cid} missing required fields: {missing}"

        assert c["expected_language"] in VALID_LANGUAGES, f"Invalid language in {cid}: {c['expected_language']}"
        assert c["expected_script"] in VALID_SCRIPTS, f"Invalid script in {cid}: {c['expected_script']}"
        assert isinstance(c["is_code_mixed"], bool), f"is_code_mixed must be boolean in {cid}"
        assert c["label_source"] in VALID_SOURCES, f"Invalid label_source in {cid}: {c['label_source']}"


def test_eval_dataset_non_circular_normalization(eval_dataset):
    """
    Confirms that the dataset contains non-trivial, non-circular normalization ground truth.
    At least 25 records must require actual transformation (original != expected_norm).
    """
    transformed = [
        c for c in eval_dataset
        if c["original_text"] != c["expected_normalized_text"]
    ]
    assert len(transformed) >= 25, (
        f"Expected at least 25 non-trivial normalization stress cases, found {len(transformed)}. "
        "Evaluation dataset must not circularly equate all expected outputs to raw inputs."
    )


def test_eval_dataset_script_detection_accuracy(eval_dataset):
    """
    Evaluates script detection across all 300 benchmark cases.
    Benchmark threshold: >= 98%.
    """
    total = len(eval_dataset)
    script_correct = sum(
        1 for c in eval_dataset
        if detect_language(c["original_text"]).script == c["expected_script"]
    )
    script_acc = script_correct / total
    assert script_acc >= 0.98, f"Script accuracy {script_acc:.2%} is below 98%"


def test_eval_dataset_language_detection_accuracy(eval_dataset):
    """
    Evaluates language classification across unambiguous and curated cases.
    Genuinely ambiguous cases (label_source='review_needed') are excluded from denominator.
    Benchmark threshold: >= 95%.
    """
    eval_cases = [c for c in eval_dataset if c.get("label_source") != "review_needed"]
    total = len(eval_cases)
    assert total >= 290, f"Expected at least 290 non-ambiguous cases, got {total}"

    lang_correct = sum(
        1 for c in eval_cases
        if detect_language(c["original_text"]).language == c["expected_language"]
    )
    lang_acc = lang_correct / total
    assert lang_acc >= 0.95, f"Language detection accuracy {lang_acc:.2%} is below 95%"


def test_eval_dataset_code_mixed_detection_accuracy(eval_dataset):
    """
    Evaluates boolean code-mixed flag accuracy across all 300 benchmark cases.
    Benchmark threshold: >= 95%.
    """
    total = len(eval_dataset)
    cm_correct = sum(
        1 for c in eval_dataset
        if detect_language(c["original_text"]).is_code_mixed == c["is_code_mixed"]
    )
    cm_acc = cm_correct / total
    assert cm_acc >= 0.95, f"Code-mixed accuracy {cm_acc:.2%} is below 95%"


def test_eval_dataset_normalization_accuracy(eval_dataset):
    """
    Evaluates deterministic text normalization exact-match against independently
    defined expected outputs.
    Benchmark threshold: >= 95%.
    """
    total = len(eval_dataset)
    norm_exact = sum(
        1 for c in eval_dataset
        if normalize_text_deterministic(c["original_text"]).normalized_text == c["expected_normalized_text"]
    )
    norm_acc = norm_exact / total
    assert norm_acc >= 0.95, f"Deterministic normalization exact-match {norm_acc:.2%} is below 95%"


def test_eval_dataset_ambiguous_provenance_handling(eval_dataset):
    """
    Validates that genuinely ambiguous Hindi/Marathi records are tracked
    with label_source='review_needed'.
    """
    ambiguous = [c for c in eval_dataset if c.get("label_source") == "review_needed"]
    assert len(ambiguous) >= 1, "Expected at least 1 record with review_needed provenance"
    for c in ambiguous:
        assert c["expected_script"] == "devanagari"
        assert c["expected_language"] in ("hi", "mr")
