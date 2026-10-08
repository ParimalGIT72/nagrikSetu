import re

# Basic profane / abusive keywords (extensible)
PROFANITY_KEYWORDS = {
    "abuse",
    "idiot",
    "scam",
    "fraudster",
    "bastard",
    "damn",
    "nonsense",
}

# Regex to detect links/URLs
URL_REGEX = re.compile(
    r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+|www\.[-\w.]+",
    re.IGNORECASE,
)

# Regex to detect excessively repeated single character (>= 5 in a row, e.g. "aaaaa", "!!!!!")
REPEATED_CHAR_REGEX = re.compile(r"(.)\1{4,}")


def moderate_text(text: str) -> tuple[bool, str | None]:
    """
    Lightweight deterministic rule-based spam and profanity checking.
    Does NOT reject or delete complaints, but flags them for officer review.

    Returns:
        (is_flagged, flag_reason)
    """
    reasons = []

    # 1. Check excessive repeated characters
    if REPEATED_CHAR_REGEX.search(text):
        reasons.append("excessive_repeated_characters")

    # 2. Check for multiple URLs (spam pattern in civic complaints)
    urls = URL_REGEX.findall(text)
    if len(urls) >= 2:
        reasons.append("multiple_urls_detected")

    # 3. Check for repetitive words / low lexical diversity
    words = [w.lower() for w in re.findall(r"\b\w+\b", text)]
    if len(words) >= 10:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.25:
            reasons.append("highly_repetitive_tokens")

    # 4. Check profanity keywords
    found_profanity = [w for w in set(words) if w in PROFANITY_KEYWORDS]
    if found_profanity:
        reasons.append(f"profanity_detected({','.join(found_profanity[:3])})")

    if reasons:
        return True, "; ".join(reasons)

    return False, None
