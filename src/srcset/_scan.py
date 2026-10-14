"""Split a srcset value into raw entries: the splitting loop and descriptor tokenizer.

A URL is a maximal run of non-whitespace, so a comma inside it (a data URI) never splits
the list. Only a comma that ends the URL, or one met while reading descriptors, separates
candidates. The raw entries keep what an authoring check needs to know about the text.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import NamedTuple

# ASCII whitespace in the HTML sense: no vertical tab, no non-ASCII spaces.
WHITESPACE = "\t\n\x0c\r "
_SEPARATORS = WHITESPACE + ","


class RawCandidate(NamedTuple):
    url: str
    tokens: list[str]
    stray_commas: int  # commas eaten by the splitting loop before this URL
    trailing_commas: int  # commas removed from the end of the URL


def scan(value: str) -> Iterator[RawCandidate | int]:
    """Yield each raw candidate, then the number of stray commas left at the end."""
    pos, end = 0, len(value)
    while True:
        start = pos
        while pos < end and value[pos] in _SEPARATORS:
            pos += 1
        commas = value.count(",", start, pos)
        if pos >= end:
            yield commas
            return
        start = pos
        while pos < end and value[pos] not in WHITESPACE:
            pos += 1
        url = value[start:pos]
        stripped = url.rstrip(",")
        if stripped != url:
            yield RawCandidate(stripped, [], commas, len(url) - len(stripped))
            continue
        pos, tokens = _tokenize(value, pos)
        yield RawCandidate(url, tokens, commas, 0)


def _tokenize(value: str, pos: int) -> tuple[int, list[str]]:
    """Collect descriptor tokens up to a separating comma or the end of the input."""
    end = len(value)
    while pos < end and value[pos] in WHITESPACE:
        pos += 1
    tokens: list[str] = []
    current: list[str] = []
    state = "in descriptor"
    while True:
        c = value[pos] if pos < end else ""
        if state == "in descriptor":
            if c in WHITESPACE and c:
                if current:
                    tokens.append("".join(current))
                    current = []
                state = "after descriptor"
            elif c in (",", ""):
                if current:
                    tokens.append("".join(current))
                return (pos + 1 if c else pos), tokens
            else:
                current.append(c)
                if c == "(":
                    state = "in parens"
        elif state == "in parens":
            if not c:
                tokens.append("".join(current))
                return pos, tokens
            current.append(c)
            if c == ")":
                state = "in descriptor"
        else:
            if not c:
                return pos, tokens
            if c not in WHITESPACE:
                state = "in descriptor"
                continue
        pos += 1
