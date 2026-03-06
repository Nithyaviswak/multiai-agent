"""Small helper utilities shared across backend modules."""

from datetime import datetime, timezone
import re
from typing import Iterable, Optional


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def slugify(value: str, max_length: int = 80) -> str:
    """Create a URL/file-system safe slug from arbitrary text."""
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"[\s_-]+", "-", value).strip("-")
    if max_length > 0:
        value = value[:max_length].rstrip("-")
    return value or "item"


def safe_truncate(text: str, limit: int, suffix: str = "...") -> str:
    """Truncate text to at most ``limit`` characters, preserving word boundary when possible."""
    if limit <= 0:
        return ""

    if len(text) <= limit:
        return text

    cut = max(0, limit - len(suffix))
    truncated = text[:cut].rstrip()

    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]

    return f"{truncated}{suffix}" if truncated else suffix[:limit]


def flatten_strings(items: Iterable[Optional[str]]) -> list[str]:
    """Return non-empty stripped strings from any iterable."""
    return [item.strip() for item in items if item and item.strip()]


def merge_unique_strings(primary: Iterable[str], secondary: Iterable[str]) -> list[str]:
    """Merge two string iterables while preserving order and uniqueness."""
    merged: list[str] = []
    seen: set[str] = set()

    for item in [*primary, *secondary]:
        if item not in seen:
            seen.add(item)
            merged.append(item)

    return merged
