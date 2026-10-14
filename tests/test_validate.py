"""Authoring checks, hand-written from the requirements in HTML 4.8.4.2.1 and 4.8.4.2.2."""

from __future__ import annotations

import pytest

from srcset import Issue, validate


def _codes(srcset: str, sizes: str | None = None) -> list[str]:
    return [issue.code for issue in validate(srcset, sizes)]


@pytest.mark.parametrize(
    ("srcset", "sizes"),
    [
        ("a.png", None),
        ("a.png 1x, b.png 2x", None),
        ("a.png, b.png 1.5x", None),
        ("a.png 100w, b.png 200w", "(min-width: 600px) 50vw, 100vw"),
        ("a.png 100w 50h", "100vw"),
        ("data:,a 1x, b,c 2x", None),
        ("a.png 100w", "auto, (max-width: 30em) 100vw, calc(100vw - 2em)"),
        ("a.png 100w", "auto"),
        ("a.png 100w", "(unknown: 1) 5px, 9px"),
    ],
)
def test_conforming_values_have_no_issues(srcset: str, sizes: str | None) -> None:
    codes = _codes(srcset, sizes)
    assert codes in ([], ["height-descriptor"])
    assert (codes == ["height-descriptor"]) is ("h" in srcset)


def test_each_problem_has_its_code() -> None:
    assert _codes("") == ["empty"]
    assert _codes(" , ") == ["extra-comma", "empty"]
    assert _codes(",a.png") == ["extra-comma"]
    assert _codes("a.png 1x,, b.png 2x") == ["extra-comma"]
    assert _codes("a.png,, b.png 2x") == ["extra-comma"]
    assert _codes("a.png 1x,") == ["extra-comma"]
    assert _codes("a.png, ") == ["extra-comma"]
    assert _codes("a.png 1x, b.png 2x,,") == ["extra-comma"]
    assert _codes("a.png 2y") == ["invalid-descriptor", "empty"]
    assert _codes("a.png 1x, b.png") == ["duplicate-density"]
    assert _codes("a.png 1x, b.png 1.0x") == ["duplicate-density"]
    assert _codes("a 10w, b 10w", "1px") == ["duplicate-width"]
    assert _codes("a.png 0x") == ["zero-density"]
    assert _codes("a 10w, b 2x", "1px") == ["mixed-descriptors", "sizes-without-width"]
    assert _codes("a.png 2x", "100vw") == ["sizes-without-width"]
    assert _codes("a 10w") == ["missing-sizes"]


@pytest.mark.parametrize(
    ("sizes", "message"),
    [
        ("", "does not end with a valid length"),
        ("100vw,", "does not end with a valid length"),
        ("-1px", "does not end with a valid length"),
        ("50%", "does not end with a valid length"),
        ("100vw, auto", "auto must open the value"),
        ("(min-width: 1px) auto, 1px", "auto must open the value"),
        ("(min-width: 1px) 1px", "the last entry takes no condition"),
        ("1px, 2px", "needs a media condition"),
        ("screen 1px, 2px", "has an invalid media condition"),
    ],
)
def test_invalid_sizes(sizes: str, message: str) -> None:
    issues = validate("a.png 100w", sizes)
    assert issues
    assert {issue.code for issue in issues} == {"invalid-sizes"}
    assert any(message in issue.message for issue in issues)


def test_messages_name_the_offending_values() -> None:
    (issue,) = validate("a.png 2y")[:1]
    assert issue == Issue("invalid-descriptor", "'a.png' '2y'")
    duplicate = validate("a 3x, b 3x")[0]
    assert duplicate.message == "2 candidates share the density 3"


def test_messages_are_capped() -> None:
    issue = validate("x" * 10_000 + " 2y")[0]
    assert len(issue.message) < 200


def test_bad_arguments() -> None:
    with pytest.raises(TypeError):
        validate(None)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        validate("a", 3)  # type: ignore[arg-type]
