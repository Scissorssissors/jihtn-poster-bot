"""Tamil-aware text measurement helpers."""

import html
import regex  # supports \X grapheme clusters


def grapheme_count(text: str) -> int:
    """Tamil vowel signs / pulli are separate code points; count visible clusters."""
    return len(regex.findall(r"\X", text))


def word_count(text: str) -> int:
    return len(text.split())


def to_html(text: str) -> str:
    """Escape, then keep punctuation glued to the previous word with no-break spaces
    so a line never starts with a comma or quote mark."""
    t = html.escape(text, quote=False)
    for p in (",", ".", "!", "?", ";", ":", "”", "’"):
        t = t.replace(f" {p}", f" {p}")
    return t


def size_class(text: str) -> str:
    n = grapheme_count(text)
    if n <= 50:
        return "hero"
    if n <= 95:
        return "large"
    if n <= 180:
        return "medium"
    if n <= 280:
        return "small"
    return "dense"
