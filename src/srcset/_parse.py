"""Parse a srcset attribute following the WHATWG splitting algorithm.

The hard part is that a URL may itself contain commas: the comma only separates
candidates when it is leading, trailing on a URL, or sits in the descriptor run. A
URL is therefore a maximal run of non-whitespace, and descriptors are tokenised
separately so an inner comma never truncates the URL.
"""

from __future__ import annotations

import re

from ._model import Candidate

_WHITESPACE = "\t\n\x0c\r "
_SEPARATORS = _WHITESPACE + ","
_INT = re.compile(r"\d+")
_FLOAT = re.compile(r"(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")


def parse(value: str) -> list[Candidate]:
    """Return the valid image candidates in a srcset attribute value."""
    candidates: list[Candidate] = []
    pos = 0
    end = len(value)
    while True:
        while pos < end and value[pos] in _SEPARATORS:
            pos += 1
        if pos >= end:
            return candidates
        start = pos
        while pos < end and value[pos] not in _WHITESPACE:
            pos += 1
        url = value[start:pos]
        if url.endswith(","):
            candidate = _make(url.rstrip(","), [])
        else:
            pos, descriptors = _tokenize(value, pos, end)
            candidate = _make(url, descriptors)
        if candidate is not None:
            candidates.append(candidate)


def _tokenize(value: str, pos: int, end: int) -> tuple[int, list[str]]:
    """Collect descriptor tokens, respecting parenthesised groups and inner commas."""
    descriptors: list[str] = []
    current = ""
    state = "descriptor"
    while True:
        c = value[pos] if pos < end else None
        if state == "descriptor":
            if c is None or c == ",":
                if current:
                    descriptors.append(current)
                return (pos + 1 if c == "," else pos), descriptors
            if c in _WHITESPACE:
                if current:
                    descriptors.append(current)
                    current = ""
                state = "after"
            elif c == "(":
                current += c
                state = "parens"
            else:
                current += c
        elif state == "parens":
            if c is None:
                descriptors.append(current)
                return pos, descriptors
            current += c
            if c == ")":
                state = "descriptor"
        else:  # after a descriptor, skipping whitespace
            if c is None:
                return pos, descriptors
            if c not in _WHITESPACE:
                state = "descriptor"
                continue
        pos += 1


def _make(url: str, descriptors: list[str]) -> Candidate | None:
    """Build a candidate, or ``None`` when the URL or descriptor is invalid."""
    descriptor = _single_descriptor(descriptors)
    if not url or descriptor is None:
        return None
    return Candidate(url, descriptor)


def _single_descriptor(descriptors: list[str]) -> str | None:
    """Return the sole valid descriptor, ``""`` for none, or ``None`` on error."""
    if not descriptors:
        return ""
    if len(descriptors) != 1 or not is_descriptor(descriptors[0]):
        return None
    return descriptors[0]


def is_descriptor(token: str) -> bool:
    """True when the token is a valid width (``320w``) or density (``2x``) descriptor."""
    body, suffix = token[:-1], token[-1:]
    if suffix == "w":
        return _INT.fullmatch(body) is not None
    if suffix == "x":
        return _FLOAT.fullmatch(body) is not None
    return False
