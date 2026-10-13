"""Parse a sizes attribute (WHATWG HTML 4.8.4.3.11) into a width in CSS pixels."""

from __future__ import annotations

import math
from collections.abc import Iterator
from typing import NamedTuple

from ._calc import quantity
from ._css_reader import Token
from ._css_values import Value, comma_separated, ident, strip
from ._media import Invalid, evaluate
from ._model import Environment, SrcsetError

AUTO = "auto"


class SourceSize(NamedTuple):
    """One entry of a sizes list: its size (``None`` when invalid) and its condition."""

    size: float | str | None
    condition: list[Value]


def source_size_value(value: Value, env: Environment) -> float | str | None:
    """A ``<source-size-value>``: px for a length, ``"auto"``, or ``None`` when invalid.

    A literal must not be negative; a math function result is clamped at zero, as CSS
    clamps it for a property that takes no negative lengths.
    """
    if ident(value, AUTO) is not None:
        return AUTO
    found = quantity(value, env)
    if found is None:
        return None
    number, is_length = found
    if not is_length:
        literal = isinstance(value, Token) and value.kind == "number"
        return 0.0 if literal and number == 0 else None
    if isinstance(value, Token):
        return None if number < 0 else number + 0.0
    return max(number, 0.0)


def entries(value: str, env: Environment) -> Iterator[SourceSize]:
    """Each comma-separated entry with its trailing size split off."""
    for group in comma_separated(value):
        group = strip(group)
        if not group:
            yield SourceSize(None, [])
            continue
        yield SourceSize(source_size_value(group[-1], env), strip(group[:-1]))


def parse_sizes(value: str, environment: Environment, *, auto_width: float | None = None) -> float:
    """The layout width in CSS pixels that a sizes attribute gives for an environment.

    Entries are tried in order; the first valid size whose media condition is true wins,
    and ``100vw`` is the fallback. ``auto`` stands for ``auto_width`` when one is given
    and the value is ``auto`` or starts with ``auto,`` (an image that allows auto-sizes,
    rendered at that width); otherwise it is skipped.
    """
    if not isinstance(value, str):
        raise TypeError(f"sizes value must be a str, got {type(value).__name__}")
    if not isinstance(environment, Environment):
        raise TypeError("environment must be an Environment")
    auto_width = _check_width(auto_width) if allows_auto(value) else None
    for entry in entries(value, environment):
        size = entry.size
        if size == AUTO and auto_width is not None:
            size = auto_width
        if size is None:
            continue
        if entry.condition:
            try:
                matched = evaluate(entry.condition, environment)
            except Invalid:
                continue
            if matched is not True:
                continue
        if size != AUTO:
            return float(size)
    return environment.width


def allows_auto(value: str) -> bool:
    """True when the raw value is ``auto`` or starts with ``auto,`` (ASCII any case)."""
    head = value[:5].translate(_ASCII_LOWER)
    return head == AUTO or head == AUTO + ","


_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def _check_width(width: float | None) -> float | None:
    if width is None:
        return None
    if isinstance(width, bool) or not isinstance(width, (int, float)):
        raise TypeError(f"auto_width must be a number, got {type(width).__name__}")
    if not math.isfinite(width) or width < 0:
        raise SrcsetError(f"auto_width must be finite and not negative, got {width}")
    return float(width)
