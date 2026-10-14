"""Public data types shared by the parser, the builder and the selector."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import NamedTuple

from ._numbers import format_density, int_text


class SrcsetError(ValueError):
    """Raised when a value cannot be expressed as, or read from, a srcset attribute."""


def _positive_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int, got {type(value).__name__}")
    if value <= 0:
        raise SrcsetError(f"{name} must be greater than zero")


def _number(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number, got {type(value).__name__}")
    try:
        number = float(value)
    except OverflowError:
        raise SrcsetError(f"{name} is too large") from None
    if not math.isfinite(number):
        raise SrcsetError(f"{name} must be finite, got {number}")
    return number


@dataclass(frozen=True)
class Candidate:
    """One image candidate: a URL with at most a width or a density descriptor.

    ``height`` is the future-compatible ``h`` descriptor, which browsers accept only next
    to a width. A candidate with no descriptor stands for ``1x``.
    """

    url: str
    width: int | None = None
    density: float | None = None
    height: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.url, str):
            raise TypeError(f"url must be a str, got {type(self.url).__name__}")
        if self.width is not None:
            _positive_int("width", self.width)
        if self.height is not None:
            _positive_int("height", self.height)
        if self.density is not None:
            density = _number("density", self.density)
            if density < 0:
                raise SrcsetError(f"density must not be negative, got {density}")
            object.__setattr__(self, "density", density + 0.0)
            if self.width is not None or self.height is not None:
                raise SrcsetError("a candidate has either a density or a width, not both")
        if self.height is not None and self.width is None:
            raise SrcsetError("a height descriptor needs a width descriptor")

    @property
    def descriptor(self) -> str:
        """The descriptors as written in a srcset value, ``""`` when there are none."""
        if self.density is not None:
            return format_density(self.density)
        parts = [int_text(self.width) + "w"] if self.width is not None else []
        if self.height is not None:
            parts.append(int_text(self.height) + "h")
        return " ".join(parts)


@dataclass(frozen=True)
class Environment:
    """What a browser knows when it picks an image: viewport, pixel ratio and font size.

    Lengths are CSS pixels. ``height`` may be ``None`` when it is not known; media
    conditions that need it then evaluate to unknown and do not match.
    """

    width: float
    height: float | None = None
    density: float = 1.0
    font_size: float = 16.0

    def __post_init__(self) -> None:
        for name in ("width", "height", "density", "font_size"):
            value = getattr(self, name)
            if value is None and name == "height":
                continue
            number = _number(name, value)
            if number < 0 or (number == 0 and name in ("density", "font_size")):
                raise SrcsetError(f"{name} is out of range: {number}")
            object.__setattr__(self, name, number + 0.0)


class ImageSource(NamedTuple):
    """A URL from a normalized source set and the pixel density it stands for."""

    url: str
    density: float


class Issue(NamedTuple):
    """An authoring error: a stable ``code`` and a readable ``message``."""

    code: str
    message: str
