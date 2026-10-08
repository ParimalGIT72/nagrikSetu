#!/usr/bin/env python3
"""
scripts/evaluate_dataset.py

Evaluates Nagrik Setu Phase 2 language detection, script detection,
and deterministic normalization against the 300-case multilingual dataset.
"""

import json
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.language_detection import detect_language
from app.services.normalization import normalize_text_deterministic

DATASET_PATH = Path(__file__).resolve().parent.parent / "ml" / "data" / "multilingual_eval_300.json"


def evaluate():
    if not DATASET_PATH.exists():
        print(f"Error: Dataset not found at {DATASET_PATH}. Run scripts/generate_eval_dataset.py first.")
        sys.exit(1)

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)

    total = len(cases)
    script_correct = 0
    language_correct = 0
    code_mix_correct = 0
    norm_exact = 0

    mismatches = []

    for item in cases:
        text = item["original_text"]
        expected_lang = item["expected_language"]
        expected_script = item["expected_script"]
        expected_cm = item["is_code_mixed"]
        expected_norm = item["expected_normalized_text"]

        det_lang = detect_language(text)
        det_norm = normalize_text_deterministic(text)

        s_ok = det_lang.script == expected_script
        l_ok = det_lang.language == expected_lang
        cm_ok = det_lang.is_code_mixed == expected_cm
        norm_ok = det_norm.normalized_text == expected_norm

        if s_ok:
            script_correct += 1
        if l_ok:
            language_correct += 1
        else:
            mismatches.append({
                "id": item["id"],
                "text": text,
                "expected": f"{expected_lang} ({expected_script}) [cm={expected_cm}]",
                "predicted": f"{det_lang.language} ({det_lang.script}) [cm={det_lang.is_code_mixed}]",
                "confidence": det_lang.confidence,
                "evidence": det_lang.evidence.model_dump() if det_lang.evidence else None,
            })
        if cm_ok:
            code_mix_correct += 1
        if norm_ok:
            norm_exact += 1

    print("\n" + "=" * 60)
    print("      NAGRIK SETU PHASE 2 MULTILINGUAL EVALUATION      ")
    print("=" * 60)
    print(f"Total Test Cases:            {total}")
    print(f"Script Accuracy:             {script_correct}/{total} ({script_correct / total * 100:.2f}%)")
    print(f"Language Accuracy:           {language_correct}/{total} ({language_correct / total * 100:.2f}%)")
    print(f"Code-Mixed Flag Accuracy:    {code_mix_correct}/{total} ({code_mix_correct / total * 100:.2f}%)")
    print(f"Deterministic Norm Exact:    {norm_exact}/{total} ({norm_exact / total * 100:.2f}%)")
    print("=" * 60)

    if mismatches:
        print(f"\nMismatches ({len(mismatches)} total):")
        for m in mismatches[:20]:
            print(f"- [{m['id']}] Expected: {m['expected']} | Predicted: {m['predicted']}")
            print(f"  Text: {m['text']}")
            if m["evidence"]:
                print(f"  Evidence: ft={m['evidence'].get('fasttext_label')} (conf={m['evidence'].get('fasttext_confidence'):.2f}), markers={m['evidence'].get('heuristic_markers')}")
        if len(mismatches) > 20:
            print(f"  ... and {len(mismatches) - 20} more.")

    return language_correct / total >= 0.95 and script_correct / total >= 0.98


if __name__ == "__main__":
    success = evaluate()
    sys.exit(0 if success else 1)
