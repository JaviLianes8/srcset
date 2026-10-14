"""Authoring checks for srcset and sizes (WHATWG HTML 4.8.4.2.1 and 4.8.4.2.2).

Browsers forgive a lot; these checks report what the standard asks authors not to write.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Sequence
from typing import TypeVar

from ._media import Invalid, evaluate
from ._model import Candidate, Environment, Issue
from ._numbers import format_density, int_text
from ._parse import to_candidate
from ._scan import WHITESPACE, RawCandidate, scan
from ._sizes import AUTO, SourceSize, allows_auto, entries

T = TypeVar("T", int, float)

# Any environment works: validity never depends on the viewport.
_PROBE = Environment(width=1000, height=1000)


def validate(srcset: str, sizes: str | None = None) -> list[Issue]:
    """List the authoring errors in a srcset value and, if given, its sizes value.

    ``sizes=None`` means the attribute is absent. An empty list means the pair conforms.
    """
    if not isinstance(srcset, str):
        raise TypeError(f"srcset value must be a str, got {type(srcset).__name__}")
    if sizes is not None and not isinstance(sizes, str):
        raise TypeError(f"sizes value must be a str or None, got {type(sizes).__name__}")
    issues: list[Issue] = []
    candidates: list[Candidate] = []
    for raw in scan(srcset):
        stray = raw if isinstance(raw, int) else raw.stray_commas
        if stray:
            issues.append(Issue("extra-comma", "a comma with no image candidate before it"))
        elif isinstance(raw, int) and srcset.rstrip(WHITESPACE).endswith(","):
            issues.append(Issue("extra-comma", "a comma after the last image candidate"))
        if isinstance(raw, RawCandidate):
            if raw.trailing_commas > 1:
                issues.append(Issue("extra-comma", f"more than one comma after {raw.url!r:.80}"))
            candidate = to_candidate(raw)
            if candidate is None:
                text = " ".join(raw.tokens)
                issues.append(Issue("invalid-descriptor", f"{raw.url!r:.80} {text!r:.80}"))
            else:
                candidates.append(candidate)
    issues.extend(_candidate_issues(candidates, sizes))
    if sizes is not None:
        issues.extend(_sizes_issues(sizes))
    return issues


def _candidate_issues(candidates: list[Candidate], sizes: str | None) -> list[Issue]:
    if not candidates:
        return [Issue("empty", "srcset needs at least one image candidate")]
    issues: list[Issue] = []
    widths = [c.width for c in candidates if c.width is not None]
    densities = [1.0 if c.density is None else c.density for c in candidates if not c.width]
    issues.extend(_duplicates("width", widths, int_text))
    issues.extend(_duplicates("density", densities, lambda d: format_density(d)[:-1]))
    if any(c.density == 0 for c in candidates):
        issues.append(Issue("zero-density", "a density descriptor must be greater than zero"))
    if any(c.height is not None for c in candidates):
        issues.append(Issue("height-descriptor", "the h descriptor is reserved, not standard"))
    if widths and len(widths) != len(candidates):
        issues.append(Issue("mixed-descriptors", "if one candidate has a width, all must"))
    if sizes is not None and len(widths) != len(candidates):
        issues.append(Issue("sizes-without-width", "with sizes, every candidate needs a width"))
    if sizes is None and widths:
        issues.append(Issue("missing-sizes", "width descriptors need a sizes attribute"))
    return issues


def _duplicates(kind: str, values: Sequence[T], text: Callable[[T], str]) -> list[Issue]:
    counts = Counter(values)
    return [
        Issue(f"duplicate-{kind}", f"{count} candidates share the {kind} {text(value):.80}")
        for value, count in counts.items()
        if count > 1
    ]


def _sizes_issues(sizes: str) -> list[Issue]:
    found = list(entries(sizes, _PROBE))
    issues: list[Issue] = []
    for index, entry in enumerate(found):
        where = f"sizes entry {index + 1}"
        last = index == len(found) - 1
        if entry.size is None:
            issues.append(Issue("invalid-sizes", f"{where} does not end with a valid length"))
        elif entry.size == AUTO and (index or entry.condition or not allows_auto(sizes)):
            issues.append(Issue("invalid-sizes", f"{where}: auto must open the value as auto,"))
        elif last and entry.condition:
            issues.append(Issue("invalid-sizes", f"{where}: the last entry takes no condition"))
        elif not last and not entry.condition and entry.size != AUTO:
            issues.append(Issue("invalid-sizes", f"{where} needs a media condition"))
        elif entry.condition and not _parses(entry):
            issues.append(Issue("invalid-sizes", f"{where} has an invalid media condition"))
    return issues


def _parses(entry: SourceSize) -> bool:
    try:
        evaluate(entry.condition, _PROBE, strict=True)
    except Invalid:
        return False
    return True
