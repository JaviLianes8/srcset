"""Serialize image candidates into a srcset value that parses back to the same list."""

from __future__ import annotations

import re
from collections.abc import Iterable

from ._descriptors import parse_descriptors
from ._model import Candidate, SrcsetError
from ._scan import WHITESPACE


def build(candidates: Iterable[Candidate | tuple[str, str]]) -> str:
    """Join candidates into a srcset value, refusing anything that would not round-trip.

    Items are ``Candidate`` values or ``(url, descriptor)`` pairs such as
    ``("a.png", "320w")``. Raises ``SrcsetError`` for an empty URL, a URL holding ASCII
    whitespace or starting or ending with a comma, and descriptors a browser would drop.
    """
    if isinstance(candidates, (str, bytes)):
        raise TypeError("build takes an iterable of candidates, not a string")
    parts: list[str] = []
    for item in candidates:
        candidate = _candidate(item)
        _check_url(candidate.url)
        descriptor = candidate.descriptor
        parts.append(f"{candidate.url} {descriptor}" if descriptor else candidate.url)
    return ", ".join(parts)


def _candidate(item: object) -> Candidate:
    if isinstance(item, Candidate):
        return item
    if not isinstance(item, tuple) or len(item) != 2:
        raise TypeError(f"expected a Candidate or a (url, descriptor) pair, got {item!r:.80}")
    url, descriptor = item
    if not isinstance(url, str) or not isinstance(descriptor, str):
        raise TypeError("url and descriptor must both be str")
    found = parse_descriptors(_split(descriptor))
    if found is None:
        raise SrcsetError(f"invalid descriptor: {descriptor!r:.80}")
    return Candidate(url, found.width, found.density, found.height)


def _split(descriptor: str) -> list[str]:
    # A comma or a parenthesis would change how the parser cuts the value.
    if any(ch in descriptor for ch in ",()"):
        raise SrcsetError(f"invalid descriptor: {descriptor!r:.80}")
    return [token for token in re.split(r"[\t\n\x0c\r ]+", descriptor) if token]


def _check_url(url: str) -> None:
    if not url:
        raise SrcsetError("candidate URL must not be empty")
    if any(ch in WHITESPACE for ch in url):
        raise SrcsetError(f"candidate URL must not contain ASCII whitespace: {url!r:.80}")
    if url.startswith(",") or url.endswith(","):
        raise SrcsetError(f"candidate URL must not start or end with a comma: {url!r:.80}")
