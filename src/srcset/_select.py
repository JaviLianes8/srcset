"""Create a source set and pick an image from it (WHATWG HTML 4.8.4.3.7 to 4.8.4.3.12)."""

from __future__ import annotations

import math

from ._model import Environment, ImageSource
from ._parse import parse
from ._sizes import parse_sizes


def source_set(
    srcset: str,
    environment: Environment,
    *,
    sizes: str = "",
    src: str = "",
    auto_width: float | None = None,
) -> list[ImageSource]:
    """The normalized source set: every candidate with the pixel density it stands for.

    A width candidate gets ``width / size`` where the size comes from ``sizes``; a bare
    candidate is ``1x``. ``src`` joins as ``1x`` when nothing else is ``1x`` and no candidate
    has a width. Later entries with a density already present are dropped.
    """
    if not isinstance(src, str):
        raise TypeError(f"src must be a str, got {type(src).__name__}")
    candidates = parse(srcset)
    size = parse_sizes(sizes, environment, auto_width=auto_width)
    sources: list[ImageSource] = []
    has_one = any(candidate.density == 1 for candidate in candidates)
    has_width = any(candidate.width is not None for candidate in candidates)
    for candidate in candidates:
        if candidate.density is not None:
            density = candidate.density
        elif candidate.width is not None:
            density = _ratio(candidate.width, size)
        else:
            density = 1.0
        sources.append(ImageSource(candidate.url, density))
    if src and not has_one and not has_width:
        sources.append(ImageSource(src, 1.0))
    seen: set[float] = set()
    unique: list[ImageSource] = []
    for source in sources:
        if source.density not in seen:
            seen.add(source.density)
            unique.append(source)
    return unique


def select(
    srcset: str,
    environment: Environment,
    *,
    sizes: str = "",
    src: str = "",
    auto_width: float | None = None,
) -> ImageSource | None:
    """The image a browser would fetch, or ``None`` when there is no candidate at all.

    The standard leaves the final choice to the browser; this picks the lowest density
    that covers ``environment.density`` and, when none does, the highest density, which
    is what browsers do on a first load.
    """
    sources = source_set(srcset, environment, sizes=sizes, src=src, auto_width=auto_width)
    if not sources:
        return None
    covering = [source for source in sources if source.density >= environment.density]
    if covering:
        return min(covering, key=lambda source: source.density)
    return max(sources, key=lambda source: source.density)


def _ratio(width: int, size: float) -> float:
    if not size:
        return math.inf
    try:
        return width / size
    except OverflowError:
        return math.inf
