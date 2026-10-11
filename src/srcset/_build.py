"""Serialise image candidates back into a srcset attribute value."""

from __future__ import annotations

from collections.abc import Iterable

from ._model import Candidate, SrcsetError
from ._parse import _WHITESPACE, is_descriptor


def build(candidates: Iterable[tuple[str, str] | Candidate]) -> str:
    """Join candidates into a srcset value, rejecting anything that cannot round-trip."""
    parts: list[str] = []
    for item in candidates:
        url, descriptor = item
        _check(url, descriptor)
        parts.append(f"{url} {descriptor}" if descriptor else url)
    return ", ".join(parts)


def _check(url: str, descriptor: str) -> None:
    if not url:
        raise SrcsetError("candidate URL must not be empty")
    if any(ch in url for ch in _WHITESPACE):
        raise SrcsetError(f"candidate URL must not contain whitespace: {url!r}")
    if url.endswith(","):
        raise SrcsetError(f"candidate URL must not end with a comma: {url!r}")
    if descriptor and not is_descriptor(descriptor):
        raise SrcsetError(f"invalid descriptor: {descriptor!r}")
