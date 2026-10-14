"""Parse a srcset attribute exactly as browsers do (WHATWG HTML 4.8.4.3.10)."""

from __future__ import annotations

from ._descriptors import parse_descriptors
from ._model import Candidate
from ._scan import RawCandidate, scan


def parse(value: str) -> list[Candidate]:
    """Return the image candidates a browser keeps from a srcset attribute value.

    Candidates whose descriptors are invalid, repeated or contradictory are dropped, as
    browsers drop them; nothing raises for a malformed value.
    """
    if not isinstance(value, str):
        raise TypeError(f"srcset value must be a str, got {type(value).__name__}")
    candidates: list[Candidate] = []
    for raw in scan(value):
        if isinstance(raw, RawCandidate):
            candidate = to_candidate(raw)
            if candidate is not None:
                candidates.append(candidate)
    return candidates


def to_candidate(raw: RawCandidate) -> Candidate | None:
    """The candidate for a raw entry, or ``None`` when the browser drops it."""
    found = parse_descriptors(raw.tokens)
    if not raw.url or found is None:
        return None
    return Candidate(raw.url, found.width, found.density, found.height)
