"""Public data types shared by the parser and the builder."""

from __future__ import annotations

from typing import NamedTuple


class SrcsetError(ValueError):
    """Raised when a candidate cannot be expressed as a srcset attribute."""


class Candidate(NamedTuple):
    """One image candidate: a URL and its optional descriptor (``""`` for none)."""

    url: str
    descriptor: str = ""
