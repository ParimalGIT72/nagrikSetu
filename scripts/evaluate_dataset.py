#!/usr/bin/env python3
"""
scripts/evaluate_dataset.py

Nagrik Setu Phase 2 — Comprehensive Multilingual Benchmark Evaluator.
Evaluates Language Detection, Script Identification, Code-Mixed Classification,
and Deterministic Text Normalization against the curated 300-case multilingual dataset.

Produces:
  1. Dataset Schema & Integrity Validation
  2. Script Detection Evaluation & Breakdown
  3. Language Classification (Per-Class Precision, Recall, F1 & Confusion Analysis)
  4. Code-Mixed Classification (Precision, Recall, F1)
  5. Deterministic Text Normalization (Category Breakdown & Exact Match)
  6. Detailed Diagnostic Reporting for Failures
  7. Synthetic Benchmark Methodology Disclaimers
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Ensure UTF-8 console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.language_detection import detect_language
from app.services.normalization import normalize_text_deterministic

DATASET_PATH = Path(__file__).resolve().parent.parent / "ml" / "data" / "multilingual_eval_300.json"

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
VALID_LABEL_SOURCES = {"unambiguous", "curated", "review_needed"}


def validate_schema(cases: List[Dict[str, Any]]) -> List[str]:
    """Validates dataset integrity, required fields, and schema constraints."""
    errors = []
    seen_ids: Set[str] = set()

    for idx, c in enumerate(cases):
        case_id = c.get("id", f"INDEX-{idx}")
        if not c.get("id"):
            errors.append(f"Record at index {idx} is missing 'id'")
        elif case_id in seen_ids:
            errors.append(f"Duplicate case id: {case_id}")
        seen_ids.add(case_id)

        missing = REQUIRED_FIELDS - set(c.keys())
        if missing:
            errors.append(f"Case {case_id} missing required fields: {missing}")

        lang = c.get("expected_language")
        if lang not in VALID_LANGUAGES:
            errors.append(f"Case {case_id} invalid expected_language '{lang}'")

        script = c.get("expected_script")
        if script not in VALID_SCRIPTS:
            errors.append(f"Case {case_id} invalid expected_script '{script}'")

        if not isinstance(c.get("is_code_mixed"), bool):
            errors.append(f"Case {case_id} 'is_code_mixed' must be boolean")

        source = c.get("label_source")
        if source not in VALID_LABEL_SOURCES:
            errors.append(f"Case {case_id} invalid label_source '{source}'")

    return errors


def compute_prf1(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    """Computes precision, recall, and F1 given TP, FP, and FN."""
    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0
    return p, r, f1


def evaluate() -> bool:
    if not DATASET_PATH.exists():
        print(f"Error: Dataset not found at {DATASET_PATH}. Run scripts/generate_eval_dataset.py first.")
        return False

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)

    total_cases = len(cases)
    print("=" * 70)
    print("       NAGRIK SETU PHASE 2 MULTILINGUAL EVALUATION BENCHMARK       ")
    print("=" * 70)
    print(f"Dataset Path:    {DATASET_PATH}")
    print(f"Total Cases:     {total_cases}")

    # 1. Schema Validation
    schema_errors = validate_schema(cases)
    if schema_errors:
        print(f"\n[FAIL] Schema validation failed with {len(schema_errors)} errors:")
        for err in schema_errors[:10]:
            print(f"  - {err}")
        return False
    print("[PASS] Dataset schema validation passed: all required fields and constraints valid.")

    # Counters and data structures
    script_correct = 0
    script_counts = Counter()
    script_tp = Counter()
    script_fp = Counter()
    script_fn = Counter()

    lang_correct = 0
    lang_tp = Counter()
    lang_fp = Counter()
    lang_fn = Counter()
    lang_eval_total = 0
    lang_excluded_ambiguous = 0

    cm_correct = 0
    cm_tp = 0
    cm_fp = 0
    cm_fn = 0
    cm_tn = 0

    norm_exact_total = 0
    norm_by_group = defaultdict(lambda: {"total": 0, "exact": 0})

    mismatches = []

    for item in cases:
        cid = item["id"]
        text = item["original_text"]
        exp_lang = item["expected_language"]
        exp_script = item["expected_script"]
        exp_cm = item["is_code_mixed"]
        exp_norm = item["expected_normalized_text"]
        group = item.get("eval_group", "unknown")
        provenance = item.get("label_source", "curated")

        # Run pipeline under test
        det_lang = detect_language(text)
        det_norm = normalize_text_deterministic(text)

        pred_script = det_lang.script
        pred_lang = det_lang.language
        pred_cm = det_lang.is_code_mixed
        pred_norm = det_norm.normalized_text

        # --- A. Script Detection ---
        script_counts[exp_script] += 1
        if pred_script == exp_script:
            script_correct += 1
            script_tp[exp_script] += 1
        else:
            script_fp[pred_script] += 1
            script_fn[exp_script] += 1
            mismatches.append({
                "id": cid, "field": "script", "text": text,
                "expected": exp_script, "predicted": pred_script,
            })

        # --- B. Language Detection ---
        if provenance == "review_needed":
            # Genuinely ambiguous cases are reported separately
            lang_excluded_ambiguous += 1
        else:
            lang_eval_total += 1
            if pred_lang == exp_lang:
                lang_correct += 1
                lang_tp[exp_lang] += 1
            else:
                lang_fp[pred_lang] += 1
                lang_fn[exp_lang] += 1
                mismatches.append({
                    "id": cid, "field": "language", "text": text,
                    "expected": exp_lang, "predicted": pred_lang,
                    "confidence": det_lang.confidence,
                    "markers": det_lang.evidence.heuristic_markers if det_lang.evidence else [],
                })

        # --- C. Code-Mixed Classification ---
        if pred_cm == exp_cm:
            cm_correct += 1
            if exp_cm:
                cm_tp += 1
            else:
                cm_tn += 1
        else:
            if pred_cm and not exp_cm:
                cm_fp += 1
            else:
                cm_fn += 1
            mismatches.append({
                "id": cid, "field": "is_code_mixed", "text": text,
                "expected": exp_cm, "predicted": pred_cm,
            })

        # --- D. Deterministic Normalization ---
        norm_by_group[group]["total"] += 1
        if pred_norm == exp_norm:
            norm_exact_total += 1
            norm_by_group[group]["exact"] += 1
        else:
            mismatches.append({
                "id": cid, "field": "normalization", "text": text,
                "expected": exp_norm, "predicted": pred_norm,
                "modifications": det_norm.modifications_applied,
            })

    # ──────────────────────────────────────────────────────────────────
    # SECTION 2: SCRIPT DETECTION RESULTS
    # ──────────────────────────────────────────────────────────────────
    script_acc = script_correct / total_cases
    print("\n" + "-" * 70)
    print("1. SCRIPT IDENTIFICATION (Evaluated independently of language)")
    print("-" * 70)
    print(f"Overall Script Accuracy: {script_correct}/{total_cases} ({script_acc:.2%})")
    print(f"{'Script':<15} {'Cases':<8} {'Precision':<12} {'Recall':<12} {'F1-Score':<10}")
    for s in sorted(script_counts.keys()):
        p, r, f1 = compute_prf1(script_tp[s], script_fp[s], script_fn[s])
        print(f"{s:<15} {script_counts[s]:<8} {p:<12.2%} {r:<12.2%} {f1:<10.2%}")

    # ──────────────────────────────────────────────────────────────────
    # SECTION 3: LANGUAGE CLASSIFICATION RESULTS
    # ──────────────────────────────────────────────────────────────────
    lang_acc = lang_correct / lang_eval_total if lang_eval_total > 0 else 0.0
    print("\n" + "-" * 70)
    print("2. LANGUAGE CLASSIFICATION (Unambiguous + Curated Records)")
    print("-" * 70)
    print(f"Evaluated Cases:         {lang_eval_total}/{total_cases} (Excluded ambiguous: {lang_excluded_ambiguous})")
    print(f"Language Accuracy:       {lang_correct}/{lang_eval_total} ({lang_acc:.2%})")
    print(f"{'Class':<12} {'Precision':<12} {'Recall':<12} {'F1-Score':<10}")
    for l in sorted(VALID_LANGUAGES):
        if l in ("unknown",) and (lang_tp[l] + lang_fp[l] + lang_fn[l] == 0):
            continue
        p, r, f1 = compute_prf1(lang_tp[l], lang_fp[l], lang_fn[l])
        print(f"{l:<12} {p:<12.2%} {r:<12.2%} {f1:<10.2%}")

    # ──────────────────────────────────────────────────────────────────
    # SECTION 4: CODE-MIXED DETECTION RESULTS
    # ──────────────────────────────────────────────────────────────────
    cm_acc = cm_correct / total_cases
    cm_p, cm_r, cm_f1 = compute_prf1(cm_tp, cm_fp, cm_fn)
    print("\n" + "-" * 70)
    print("3. CODE-MIXED CLASSIFICATION")
    print("-" * 70)
    print(f"Code-Mixed Accuracy:     {cm_correct}/{total_cases} ({cm_acc:.2%})")
    print(f"Code-Mixed Precision:    {cm_p:.2%}")
    print(f"Code-Mixed Recall:       {cm_r:.2%}")
    print(f"Code-Mixed F1-Score:     {cm_f1:.2%}")
    print(f"Confusion: TP={cm_tp}, TN={cm_tn}, FP={cm_fp}, FN={cm_fn}")

    # ──────────────────────────────────────────────────────────────────
    # SECTION 5: DETERMINISTIC NORMALIZATION EXACT-MATCH
    # ──────────────────────────────────────────────────────────────────
    norm_acc = norm_exact_total / total_cases
    print("\n" + "-" * 70)
    print("4. DETERMINISTIC TEXT NORMALIZATION (Non-Circular Ground Truth)")
    print("-" * 70)
    print(f"Overall Exact-Match:     {norm_exact_total}/{total_cases} ({norm_acc:.2%})")
    print("\nBreakdown by Evaluation Group:")
    print(f"{'Group':<35} {'Exact Match':<15} {'Percentage':<10}")
    for grp, stats in sorted(norm_by_group.items()):
        g_tot = stats["total"]
        g_ex = stats["exact"]
        print(f"{grp:<35} {g_ex}/{g_tot:<12} {g_ex/g_tot:.1%}")

    # ──────────────────────────────────────────────────────────────────
    # SECTION 6: DIAGNOSTICS & MISMATCH REPORT
    # ──────────────────────────────────────────────────────────────────
    if mismatches:
        print("\n" + "=" * 70)
        print(f"DIAGNOSTIC REPORT — {len(mismatches)} MISMATCHES")
        print("=" * 70)
        for m in mismatches[:20]:
            print(f"- [{m['id']}] Field: {m['field']}")
            print(f"  Input:    {m['text']}")
            print(f"  Expected: {m['expected']}")
            print(f"  Actual:   {m['predicted']}")
            if "confidence" in m:
                print(f"  Conf:     {m.get('confidence', 0.0):.2f} | Markers: {m.get('markers')}")
            if "modifications" in m:
                print(f"  Modifications: {m.get('modifications')}")
        if len(mismatches) > 20:
            print(f"  ... and {len(mismatches) - 20} more.")
    else:
        print("\n[OK] Zero mismatches detected across all 300 benchmark cases!")

    # ──────────────────────────────────────────────────────────────────
    # SECTION 7: METHODOLOGY DISCLAIMER
    # ──────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("METHODOLOGICAL CONTEXT & BENCHMARK TRANSPARENCY:")
    print("  - This evaluation measures performance against a synthetic/curated")
    print("    300-case dataset designed to stress-test supported Phase 2 rules.")
    print("  - It confirms absence of regressions in deterministic transformations,")
    print("    LID routing, and FastText heuristics.")
    print("  - It is NOT equivalent to an independently audited real-world field study.")
    print("=" * 70)

    # Valid criteria check: high accuracy on synthetic benchmark without regression
    passed = (
        script_acc >= 0.98
        and lang_acc >= 0.95
        and cm_acc >= 0.95
        and norm_acc >= 0.98
    )
    return passed


if __name__ == "__main__":
    success = evaluate()
    sys.exit(0 if success else 1)
