import logging
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import fasttext

from app.config import settings
from app.schemas.preprocessing import LanguageDetectionResult, LanguageEvidence

logger = logging.getLogger(__name__)

# Suppress noisy fasttext warnings
fasttext.FastText.eprint = lambda x: None

# Global cached FastText model instance
_FASTTEXT_MODEL = None


def get_fasttext_model():
    """
    Lazy-loads the FastText language identification model once into memory.
    """
    global _FASTTEXT_MODEL
    if _FASTTEXT_MODEL is None:
        model_path = Path(settings.FASTTEXT_MODEL_PATH)
        if not model_path.exists():
            logger.warning(
                f"FastText model not found at {model_path}. "
                "Run `python scripts/download_models.py` to download it. "
                "Falling back to heuristic script detection."
            )
            return None
        try:
            _FASTTEXT_MODEL = fasttext.load_model(str(model_path))
            logger.info(f"Loaded FastText model from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load FastText model from {model_path}: {e}")
            return None
    return _FASTTEXT_MODEL


# Common Indic markers used in multi-signal heuristic evidence
MARATHI_ROMANIZED_MARKERS: Set[str] = {
    "madhe", "madhye", "aahe", "aahet", "ahe", "ahet", "khup", "motha", "mothi", "mothe",
    "rastya", "rastyavar", "khadda", "khadde", "jhala", "zala", "zhale", "zale",
    "nahi", "nahiet", "kiti", "aani", "ani", "karan", "pani", "paani", "kachra", "karave", "kara",
    "punyat", "var", "varach", "kahi", "tasech", "loker", "dya",
    "che", "cha", "chi", "chya", "javal", "houn", "yete", "yet",
    "kela", "keli", "kele", "kartat", "karto", "karte", "hoto", "hote", "hota", "hoti", "hotoy", "hotaat",
    "mule", "nantar", "pasun", "shakto", "shakte", "aali", "aala", "gela", "geli",
    "thevla", "thevli", "thevle", "tutle", "padla", "padle", "padli", "suddha", "pan", "tar",
    "kuthlya", "kadhun", "kadhe", "baddal", "war", "chalu", "astat", "kelya", "jagi", "dakhavli", "dakhavat",
    "traas", "lokaana", "lokaanna", "chalte", "band", "samasya", "vinaanti", "takraar", "galli",
    "ghya", "aslyamule", "vikat", "ghyave", "lagte", "naala", "saaf", "bhagat", "dukaan", "taktat",
    "gardi", "aste", "karne", "todun", "neele", "ratri", "andhaar", "vaatate", "kartaat", "udat",
    "zop", "banlya", "koni", "uthavat", "todla", "baher", "samor", "ardhavat", "sodla"
}

HINDI_ROMANIZED_MARKERS: Set[str] = {
    "hai", "hain", "bahut", "bada", "badi", "bade",
    "sadak", "gaddha", "gaddhe", "nahi", "karo", "raha", "rahe", "rahi",
    "paani", "kuda", "yahan", "kripya", "kijiye", "hota", "hote", "hoti", "bhi",
    "liye", "gaya", "gaye", "gayi", "diya", "diye", "wala", "wali", "wale", "aur",
    "bijli", "band", "shor", "subah", "shaam", "mein", "par", "se", "ko", "roz",
    "katti", "rehta", "aata", "jaata", "lag", "beh", "gandagi", "aayi", "naali", "fis"
}

ENGLISH_COMMON_WORDS: Set[str] = {
    "the", "is", "at", "which", "on", "there", "are", "and", "in", "near", "with", "for", "from",
    "road", "street", "pothole", "potholes", "garbage", "light", "lights", "water",
    "drainage", "traffic", "issue", "problem", "broken", "clean", "please",
    "urgent", "urgently", "complaint", "area", "large", "very", "danger", "dangerous",
    "open", "dump", "dumping", "truck", "pole", "wire", "wires", "cable", "gutter",
    "drain", "trash", "waste", "bin", "bins", "footpath", "sidewalk", "signal",
    "accident", "accidents", "people", "senior", "citizen", "citizens", "hospital",
    "school", "bus", "stop", "station", "depot", "electric", "electricity", "power",
    "cut", "cuts", "blackout", "machine", "factory", "noise", "loud", "music",
    "night", "morning", "hours", "late", "fall", "down", "spill", "smell", "bad",
    "foul", "severe", "irritation", "continuous", "continuously", "blinking",
    "inspection", "chamber", "cracked", "overflow", "overflowing", "rubble",
    "construction", "debris", "public", "park", "repair", "closed", "live", "exposed",
    "balcony", "touch", "touching", "high", "voltage", "surge", "fault", "delay",
    "display", "board", "timetable", "overcrowding", "passenger", "passengers",
    "driver", "conductor", "misbehaves", "shattered", "tyres", "hazard", "risk",
    "after", "before", "front", "gate", "colony", "society", "low", "pressure", "tap",
    "pipeline", "odor", "rot", "rotting", "stray", "cattle", "unpaved", "deep",
    "crater", "monsoon", "rains", "resurfacing", "speed", "breaker", "paint", "marks",
    "asphalt", "washed", "flying", "pebbles", "manhole", "cover", "uneven", "raised",
    "above", "level", "dust", "skidding", "container", "dead", "animals",
    "unattended", "muddy", "drinking", "gallons", "leakage", "darkness", "internal",
    "lane", "wiring", "lamp", "post", "bent", "black", "sewage", "storm", "silt",
    "missing", "choked", "fatal", "trap", "pedestrian", "pedestrians", "commercial",
    "zebra", "crossing", "bottleneck", "delivery", "joggers", "fluctuation", "outages",
    "generator", "horns", "concrete", "mixers", "procession", "ambulance",
    "firecrackers", "workshop", "hammering", "tiles", "lake", "market", "residential",
    "silence", "zone", "loudspeaker", "announcements", "declare", "declared",
    "tanker", "municipality", "supply", "basement", "collection", "office", "regularly",
    "daily", "crowded", "breathe", "residents", "upset", "stink", "unbearable", "highway",
    "condition", "sparks", "secretly", "disgusting", "laboratory", "bore", "well",
    "contaminated", "safe", "correct", "disturbing", "jam"
}

MARATHI_DEVANAGARI_MARKERS: Set[str] = {
    "आहे", "आहेत", "नाही", "नाहीत", "खूप", "रस्ता", "रस्त्यावर", "खड्डा", "खड्डे",
    "झाले", "झाला", "कचरा", "पाणी", "करा", "करावे", "करावी", "करावेत", "येथे", "पाहिजे", "कृपया",
    "तात्काळ", "लवकर", "दुरुस्ती", "नगरपालिकेने", "तक्रार", "कारवाई"
}

HINDI_DEVANAGARI_MARKERS: Set[str] = {
    "है", "हैं", "नहीं", "बहुत", "सड़क", "गड्ढा", "गड्ढे", "हुआ", "गया",
    "पानी", "करो", "चाहिए", "यहाँ", "कृपया", "कीजिए", "हो",
    "तुरंत", "कार्रवाई", "करनी", "समस्या", "गंभीर", "शिकायत"
}


def analyze_script(text: str) -> Tuple[str, Dict[str, int]]:
    """
    Analyzes characters to determine whether the text is written in
    Devanagari, Latin, or Mixed script.
    Preserves Indic combining marks (vowel signs/matras, virama).
    """
    counts = {"devanagari": 0, "latin": 0, "other": 0}

    for ch in text:
        cp = ord(ch)
        cat = unicodedata.category(ch)
        if cat[0] not in ("L", "M", "N"):
            continue
        if 0x0900 <= cp <= 0x097F:
            counts["devanagari"] += 1
        elif (0x0041 <= cp <= 0x005A) or (0x0061 <= cp <= 0x007A) or (0x00C0 <= cp <= 0x024F):
            counts["latin"] += 1
        else:
            counts["other"] += 1

    total_alpha = counts["devanagari"] + counts["latin"]
    if total_alpha == 0:
        return "unknown", counts

    dev_ratio = counts["devanagari"] / total_alpha
    latin_ratio = counts["latin"] / total_alpha

    if (counts["devanagari"] >= 2 and counts["latin"] >= 2) and (dev_ratio >= 0.10 and latin_ratio >= 0.10):
        return "mixed", counts

    if dev_ratio >= 0.85:
        return "devanagari", counts
    if latin_ratio >= 0.85:
        return "latin", counts

    return "devanagari" if dev_ratio > latin_ratio else "latin", counts


def tokenize_words(text: str) -> List[str]:
    """
    Splits text into lowercased tokens without splitting Devanagari words
    on combining marks (matras/viramas).
    """
    tokens = re.findall(r"[\w\u0900-\u097F]+", text, flags=re.UNICODE)
    clean_tokens = [t.strip("।॥_").lower() for t in tokens]
    return [t for t in clean_tokens if t]


def detect_language(text: str) -> LanguageDetectionResult:
    """
    Multi-signal language and script detection combining:
    1. Unicode character script inspection
    2. FastText language identification model
    3. Romanized and Code-mixed linguistic evidence signals
    """
    normalized_input = unicodedata.normalize("NFKC", text.strip())
    if not normalized_input:
        return LanguageDetectionResult(
            language="unknown",
            script="unknown",
            confidence=0.0,
            is_code_mixed=False,
            evidence=LanguageEvidence(script="unknown", script_counts={}, heuristic_markers=[]),
        )

    # 1. Script Analysis
    script, script_counts = analyze_script(normalized_input)

    # 2. FastText LID
    model = get_fasttext_model()
    ft_label: Optional[str] = None
    ft_conf: Optional[float] = None

    if model:
        # FastText expects single line input
        single_line = " ".join(normalized_input.split())
        try:
            labels, probs = model.predict(single_line, k=1)
            if labels and len(labels) > 0:
                ft_label = labels[0].replace("__label__", "")
                ft_conf = float(probs[0])
        except Exception as e:
            logger.warning(f"FastText prediction error: {e}")

    # 3. Tokenize words & collect heuristic markers
    tokens = tokenize_words(normalized_input)
    token_set = set(tokens)

    matched_mr_roman = list(token_set.intersection(MARATHI_ROMANIZED_MARKERS))
    matched_hi_roman = list(token_set.intersection(HINDI_ROMANIZED_MARKERS))
    matched_en_words = list(token_set.intersection(ENGLISH_COMMON_WORDS))
    matched_mr_dev = list(token_set.intersection(MARATHI_DEVANAGARI_MARKERS))
    matched_hi_dev = list(token_set.intersection(HINDI_DEVANAGARI_MARKERS))

    all_heuristic_markers = (
        matched_mr_roman + matched_hi_roman + matched_mr_dev + matched_hi_dev
    )

    evidence = LanguageEvidence(
        script=script,
        script_counts=script_counts,
        fasttext_label=ft_label,
        fasttext_confidence=ft_conf,
        heuristic_markers=all_heuristic_markers,
    )

    # 4. Synthesize final decision based on script and signals

    # CASE A: Devanagari Script
    if script == "devanagari":
        # FastText or vocabulary signals
        if matched_mr_dev and not matched_hi_dev:
            return LanguageDetectionResult(
                language="mr",
                script="devanagari",
                confidence=max(0.92, ft_conf or 0.85),
                is_code_mixed=False,
                evidence=evidence,
            )
        if matched_hi_dev and not matched_mr_dev:
            return LanguageDetectionResult(
                language="hi",
                script="devanagari",
                confidence=max(0.92, ft_conf or 0.85),
                is_code_mixed=False,
                evidence=evidence,
            )
        if ft_label in ("mr", "hi"):
            return LanguageDetectionResult(
                language=ft_label,
                script="devanagari",
                confidence=ft_conf or 0.85,
                is_code_mixed=False,
                evidence=evidence,
            )
        # Default for Devanagari civic complaints in Maharashtra
        return LanguageDetectionResult(
            language="mr" if len(matched_mr_dev) >= len(matched_hi_dev) else "hi",
            script="devanagari",
            confidence=0.80,
            is_code_mixed=False,
            evidence=evidence,
        )

    # CASE B: Mixed Script (Devanagari + Latin characters)
    if script == "mixed":
        lang = "mr-en" if (matched_mr_dev or matched_mr_roman or ft_label == "mr") else "hi-en"
        return LanguageDetectionResult(
            language=lang,
            script="mixed",
            confidence=0.88,
            is_code_mixed=True,
            evidence=evidence,
        )

    # CASE C: Latin Script
    has_indic_roman = len(matched_mr_roman) > 0 or len(matched_hi_roman) > 0
    has_english = len(matched_en_words) > 0 or (ft_label == "en" and (ft_conf or 0) > 0.6)

    # Code-mixed Latin (Indic Romanized + English)
    if has_indic_roman and has_english:
        lang = "mr-en" if len(matched_mr_roman) >= len(matched_hi_roman) else "hi-en"
        return LanguageDetectionResult(
            language=lang,
            script="latin",
            confidence=0.89,
            is_code_mixed=True,
            evidence=evidence,
        )

    # Pure Romanized Indic (no substantial English)
    if has_indic_roman and not has_english:
        lang = "mr" if len(matched_mr_roman) >= len(matched_hi_roman) else "hi"
        return LanguageDetectionResult(
            language=lang,
            script="latin",
            confidence=0.85,
            is_code_mixed=False,
            evidence=evidence,
        )

    # Pure English
    if ft_label == "en" or has_english:
        confidence = max(0.80, ft_conf or 0.80) if has_english else (ft_conf or 0.80)
        return LanguageDetectionResult(
            language="en",
            script="latin",
            confidence=confidence,
            is_code_mixed=False,
            evidence=evidence,
        )

    # Fallback Latin
    if ft_label in ("en", "hi", "mr"):
        return LanguageDetectionResult(
            language=ft_label,
            script="latin",
            confidence=ft_conf or 0.60,
            is_code_mixed=False,
            evidence=evidence,
        )

    return LanguageDetectionResult(
        language="unknown",
        script="latin",
        confidence=0.50,
        is_code_mixed=False,
        evidence=evidence,
    )
