"""Calling-number allowlist. The voice webhook reads this file and nothing else."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parent / "allowed_callers.json"


def load_allowed_numbers(path: Path | None = None) -> frozenset[str]:
    """Return E.164 numbers from the allowlist file, with surrounding spaces removed."""
    data_path = path or _DATA_PATH
    raw = json.loads(data_path.read_text(encoding="utf-8"))
    numbers = raw.get("numbers", [])
    return frozenset(str(number).strip() for number in numbers if str(number).strip())


def is_caller_allowed(number: str | None, allowed: Iterable[str] | None = None) -> bool:
    """True only when the stripped caller id is an exact member of the allowlist."""
    if number is None:
        return False
    candidate = str(number).strip()
    if not candidate:
        return False
    pool = load_allowed_numbers() if allowed is None else allowed
    return candidate in {str(item).strip() for item in pool if str(item).strip()}
