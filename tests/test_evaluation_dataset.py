import json
from pathlib import Path
import pytest

from app.services.language_detection import detect_language
from app.services.normalization import normalize_text_deterministic


@pytest.fixture(scope="module")
def eval_dataset():
    dataset_path = Path(__file__).resolve().parent.parent / "ml" / "data" / "multilingual_eval_300.json"
    assert dataset_path.exists(), "Multilingual evaluation dataset must exist at ml/data/multilingual_eval_300.json"
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_eval_dataset_accuracy_metrics(eval_dataset):
    """
    Evaluates Phase 2 Language Detection and Deterministic Normalization
    against the 300-case multilingual benchmark.
    Asserts >= 98% accuracy on script detection and language detection.
    """
    total = len(eval_dataset)
    assert total == 300, f"Expected 300 cases, found {total}"

    script_correct = 0
    language_correct = 0
    code_mixed_correct = 0
    norm_exact = 0

    for item in eval_dataset:
        text = item["original_text"]
        expected_lang = item["expected_language"]
        expected_script = item["expected_script"]
        expected_cm = item["is_code_mixed"]
        expected_norm = item["expected_normalized_text"]

        det_lang = detect_language(text)
        det_norm = normalize_text_deterministic(text)

        if det_lang.script == expected_script:
            script_correct += 1
        if det_lang.language == expected_lang:
            language_correct += 1
        if det_lang.is_code_mixed == expected_cm:
            code_mixed_correct += 1
        if det_norm.normalized_text == expected_norm:
            norm_exact += 1

    script_acc = script_correct / total
    lang_acc = language_correct / total
    cm_acc = code_mixed_correct / total
    norm_acc = norm_exact / total

    assert script_acc >= 0.98, f"Script accuracy {script_acc:.2%} is below 98%"
    assert lang_acc >= 0.98, f"Language detection accuracy {lang_acc:.2%} is below 98%"
    assert cm_acc >= 0.98, f"Code-mixed accuracy {cm_acc:.2%} is below 98%"
    assert norm_acc >= 0.98, f"Normalization accuracy {norm_acc:.2%} is below 98%"
