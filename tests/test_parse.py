"""Parsing srcset values. Cases are hand-written from the WHATWG algorithm (HTML 4.8.4.3.10,
https://html.spec.whatwg.org/multipage/images.html#parse-a-srcset-attribute); the browser
corpus itself runs in test_wpt.py."""

from __future__ import annotations

import pytest

from srcset import Candidate, parse


def test_density_descriptors() -> None:
    assert parse("small.png 1x, large.png 2x") == [
        Candidate("small.png", density=1.0),
        Candidate("large.png", density=2.0),
    ]


def test_width_descriptors() -> None:
    assert parse("a.png 320w, b.png 640w") == [Candidate("a.png", 320), Candidate("b.png", 640)]


def test_width_with_future_height() -> None:
    assert parse("a.png 100w 50h") == [Candidate("a.png", 100, height=50)]
    assert parse("a.png 50h 100w") == [Candidate("a.png", 100, height=50)]


def test_no_descriptor() -> None:
    assert parse("plain.png") == [Candidate("plain.png")]


def test_url_with_comma_is_kept_whole() -> None:
    value = "data:image/png;base64,iVBORw0KGgo 1x, next.png 2x"
    assert [c.url for c in parse(value)] == ["data:image/png;base64,iVBORw0KGgo", "next.png"]


def test_trailing_commas_end_the_url() -> None:
    assert parse("a.png,,, b.png 2x") == [Candidate("a.png"), Candidate("b.png", density=2.0)]


def test_separators_and_whitespace() -> None:
    assert parse(",, \t a.png\n1x ,\x0c, b.png\r2x ,,") == [
        Candidate("a.png", density=1.0),
        Candidate("b.png", density=2.0),
    ]


def test_vertical_tab_and_no_break_space_are_not_whitespace() -> None:
    assert parse("a.png\x0b1x") == [Candidate("a.png\x0b1x")]
    assert parse("a.png \xa01x") == []


def test_empty_values() -> None:
    assert parse("") == []
    assert parse("   ,  , ") == []


@pytest.mark.parametrize(
    ("text", "density"),
    [("0x", 0.0), ("-0x", 0.0), (".5x", 0.5), ("1e1x", 10.0), ("1.5E-1x", 0.15), ("1.0x", 1.0)],
)
def test_valid_densities(text: str, density: float) -> None:
    (candidate,) = parse(f"a.png {text}")
    assert candidate.density == density
    assert str(candidate.density) != "-0.0"


@pytest.mark.parametrize(
    "text",
    ["1.x", "+1x", "-1x", "1X", ".x", "1e400x", "\u0661x", "1x 2x", "Infinityx", "NaNx", "0x1x"],
)
def test_invalid_densities_drop_the_candidate(text: str) -> None:
    assert parse(f"a.png {text}, b.png") == [Candidate("b.png")]


@pytest.mark.parametrize(
    "text",
    ["0w", "-1w", "1.0w", "1e0w", "+1w", "1W", "\u0661w", "1w 1w", "1w 1x", "1x 1w", "1h", "1w 0h"],
)
def test_invalid_widths_drop_the_candidate(text: str) -> None:
    assert parse(f"a.png {text}, b.png") == [Candidate("b.png")]


@pytest.mark.parametrize("text", ["1h 1h 1w", "1x 1h", "1h 1x", "foo", "1w foo"])
def test_contradictory_descriptors_drop_the_candidate(text: str) -> None:
    assert parse(f"a.png {text}") == []


def test_parentheses_keep_commas_inside_a_descriptor() -> None:
    assert parse("a.png (x, y.png 2x), c.png") == [Candidate("c.png")]
    assert parse("a.png (x, c.png") == []


def test_brackets_do_not_group() -> None:
    assert parse("a.png [x, b.png 2x") == [Candidate("b.png", density=2.0)]


def test_huge_width_is_exact() -> None:
    (candidate,) = parse("a.png 123456789012345678901234567890w")
    assert candidate.width == 123456789012345678901234567890


def test_non_string_is_a_type_error() -> None:
    with pytest.raises(TypeError):
        parse(b"a.png 1x")  # type: ignore[arg-type]
