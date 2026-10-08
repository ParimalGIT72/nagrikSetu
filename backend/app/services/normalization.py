import re
import unicodedata
from typing import List, Tuple

from app.schemas.preprocessing import DeterministicNormResult

# Invisible Unicode characters to strip
STRIP_UNICODE_CHARS = {
    "\u200b",  # Zero-width space
    "\ufeff",  # Byte order mark
    "\u202a",  # Left-to-right embedding
    "\u202b",  # Right-to-left embedding
    "\u202c",  # Pop directional formatting
    "\u202d",  # Left-to-right override
    "\u202e",  # Right-to-left override
}

# Vowels that commonly appear doubled in English (e.g. 'good', 'soon')
DOUBLE_VOWEL_ALLOWLIST = {"o"}


def clean_unicode(text: str) -> Tuple[str, bool]:
    """
    Applies Unicode NFKC normalization and strips invisible control artifacts.
    """
    normalized = unicodedata.normalize("NFKC", text)
    cleaned_chars = [ch for ch in normalized if ch not in STRIP_UNICODE_CHARS]
    cleaned = "".join(cleaned_chars)
    changed = cleaned != text
    return cleaned, changed


def normalize_whitespace(text: str) -> Tuple[str, bool]:
    """
    Collapses multiple horizontal spaces and tabs into a single space,
    and collapses 3+ consecutive newlines to at most 2.
    """
    # Collapse multiple spaces or tabs into a single space
    cleaned = re.sub(r"[ \t]+", " ", text)
    # Collapse excessive newlines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = cleaned.strip()
    changed = cleaned != text
    return cleaned, changed


def normalize_punctuation(text: str) -> Tuple[str, bool]:
    """
    Deduplicates excessive punctuation conservatively:
    - '!!!!!!' -> '!'
    - '??????' -> '?'
    - '!?!?'   -> '?!'
    - '......' -> '...'
    """
    original = text
    # Multiple exclamation marks to single
    cleaned = re.sub(r"!{2,}", "!", text)
    # Multiple question marks to single
    cleaned = re.sub(r"\?{2,}", "?", cleaned)
    # 4 or more periods to standard ellipsis (3 periods)
    cleaned = re.sub(r"\.{4,}", "...", cleaned)
    # Multiple mixed exclamation/question marks
    cleaned = re.sub(r"([!?]){2,}", r"\1", cleaned)
    changed = cleaned != original
    return cleaned, changed


def normalize_elongated_chars(text: str) -> Tuple[str, bool]:
    """
    Constrained reduction of repeated characters:
    Only reduces runs of 3 or more identical alphabetic letters.
    E.g. 'khupppp' -> 'khup', 'potholessss' -> 'potholes', 'goooood' -> 'good'.
    """
    original = text

    def replacer(match: re.Match) -> str:
        char = match.group(1)
        lower_char = char.lower()
        if lower_char in DOUBLE_VOWEL_ALLOWLIST:
            # e.g., 'goood' -> 'good'
            return char * 2
        return char

    # Match 3 or more consecutive identical alphabetic letters
    cleaned = re.sub(r"([a-zA-Z])\1{2,}", replacer, text)
    changed = cleaned != original
    return cleaned, changed


def assess_semantic_llm_need(text: str, modifications: List[str]) -> bool:
    """
    Assesses whether the text is sufficiently clean or whether it requires
    deeper semantic reconstruction from an LLM.
    """
    # If substantial elongated characters or noisy patterns occurred
    if "elongated_characters_reduced" in modifications:
        return True

    # If the text has high proportion of symbols or odd casing
    alpha_chars = [c for c in text if c.isalpha()]
    if alpha_chars:
        upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
        # All caps screaming complaint
        if upper_ratio > 0.85 and len(alpha_chars) > 20:
            return True

    return False


def normalize_text_deterministic(text: str) -> DeterministicNormResult:
    """
    Performs deterministic text normalization:
    1. Unicode NFKC normalization & invisible character stripping
    2. Whitespace collapse
    3. Conservative punctuation deduplication
    4. Constrained elongated character reduction
    5. Conservative casing preservation
    """
    modifications: List[str] = []
    current_text = text

    # 1. Unicode
    current_text, changed_u = clean_unicode(current_text)
    if changed_u:
        modifications.append("unicode_normalized")

    # 2. Whitespace
    current_text, changed_w = normalize_whitespace(current_text)
    if changed_w:
        modifications.append("whitespace_collapsed")

    # 3. Punctuation
    current_text, changed_p = normalize_punctuation(current_text)
    if changed_p:
        modifications.append("punctuation_deduplicated")

    # 4. Elongated character reduction
    current_text, changed_e = normalize_elongated_chars(current_text)
    if changed_e:
        modifications.append("elongated_characters_reduced")

    # 5. Semantic LLM need assessment
    needs_llm = assess_semantic_llm_need(current_text, modifications)

    return DeterministicNormResult(
        normalized_text=current_text,
        modifications_applied=modifications,
        needs_semantic_llm=needs_llm,
    )
