import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.moderation import moderate_text


def test_moderate_clean_text():
    is_flagged, reason = moderate_text("Water supply pipeline is broken near main market area.")
    assert is_flagged is False
    assert reason is None


def test_moderate_excessive_repeated_characters():
    is_flagged, reason = moderate_text("Please fix this road immediately aaaaaaa help!!!!!")
    assert is_flagged is True
    assert "excessive_repeated_characters" in reason


def test_moderate_multiple_urls():
    text = "Visit http://spam-link.com and http://another-link.org for quick cash repair"
    is_flagged, reason = moderate_text(text)
    assert is_flagged is True
    assert "multiple_urls_detected" in reason


def test_moderate_profanity():
    text = "The officer is an idiot and doing nonsense work"
    is_flagged, reason = moderate_text(text)
    assert is_flagged is True
    assert "profanity_detected" in reason
