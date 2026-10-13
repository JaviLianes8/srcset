"""The descriptor parser step of "parse a srcset attribute" (WHATWG HTML 4.8.4.3.10)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple

from ._numbers import is_floating_point, is_non_negative_integer, parse_floating_point, to_int


class Descriptors(NamedTuple):
    width: int | None
    density: float | None
    height: int | None


def parse_descriptors(tokens: Sequence[str]) -> Descriptors | None:
    """Read descriptor tokens into values, or ``None`` when the candidate is an error.

    Every token is visited even after an error, exactly as the standard reads them; the
    only thing that matters is whether an error was raised at all.
    """
    error = False
    width: int | None = None
    density: float | None = None
    height: int | None = None
    for token in tokens:
        body, suffix = token[:-1], token[-1:]
        if suffix == "w" and is_non_negative_integer(body):
            if width is not None or density is not None:
                error = True
            value = to_int(body)
            if value == 0:
                error = True
            else:
                width = value
        elif suffix == "x" and is_floating_point(body):
            if width is not None or density is not None or height is not None:
                error = True
            number = parse_floating_point(body)
            if number is None or number < 0:
                error = True
            else:
                density = number
        elif suffix == "h" and is_non_negative_integer(body):
            if height is not None or density is not None:
                error = True
            value = to_int(body)
            if value == 0:
                error = True
            else:
                height = value
        else:
            error = True
    if height is not None and width is None:
        error = True
    return None if error else Descriptors(width, density, height)
