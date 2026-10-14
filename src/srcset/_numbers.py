"""HTML number microsyntaxes, restricted to ASCII digits as the standard requires."""

from __future__ import annotations

import math
import re

_NON_NEGATIVE_INTEGER = re.compile(r"[0-9]+")
_FLOATING_POINT = re.compile(r"-?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][-+]?[0-9]+)?")


# Python refuses to convert very long digit strings in one go (the limit can be as low as
# 640 digits); converting in chunks keeps the HTML rule, which sets no length limit.
_CHUNK = 512


def to_int(digits: str) -> int:
    """Exact value of a string of ASCII digits of any length."""
    value = 0
    for start in range(0, len(digits), _CHUNK):
        chunk = digits[start : start + _CHUNK]
        value = value * 10 ** len(chunk) + int(chunk)
    return value


def int_text(value: int) -> str:
    """Decimal text of a non-negative int of any size."""
    parts: list[str] = []
    while value >= 10**_CHUNK:
        value, low = divmod(value, 10**_CHUNK)
        parts.append(str(low).rjust(_CHUNK, "0"))
    return str(value) + "".join(reversed(parts))


def is_non_negative_integer(text: str) -> bool:
    """True for a valid non-negative integer: one or more ASCII digits."""
    return _NON_NEGATIVE_INTEGER.fullmatch(text) is not None


def is_floating_point(text: str) -> bool:
    """True for a valid floating-point number (no ``+``, no bare ``.``, no ``1.``)."""
    return _FLOATING_POINT.fullmatch(text) is not None


def parse_floating_point(text: str) -> float | None:
    """Value of a valid floating-point number; ``None`` when it rounds past the doubles.

    Python rounds to the nearest double with ties to even, as the HTML rules do. The
    rules have no negative zero; ``Candidate`` turns ``-0.0`` into ``0.0``.
    """
    value = float(text)
    if math.isinf(value):
        return None
    return value


def format_density(density: float) -> str:
    """Shortest text for a density that reads back as the same float, with its ``x``."""
    text = repr(density)
    if text.endswith(".0"):
        text = text[:-2]
    return text + "x"
