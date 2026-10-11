import pytest

from srcset import Candidate, parse


def test_density_descriptor() -> None:
    assert parse("small.png 1x, large.png 2x") == [
        Candidate("small.png", "1x"),
        Candidate("large.png", "2x"),
    ]


def test_width_descriptor() -> None:
    assert parse("a.png 320w, b.png 640w") == [
        Candidate("a.png", "320w"),
        Candidate("b.png", "640w"),
    ]


def test_fractional_density() -> None:
    assert parse("hi.png 1.5x") == [Candidate("hi.png", "1.5x")]


def test_no_descriptor() -> None:
    assert parse("plain.png") == [Candidate("plain.png", "")]


def test_url_with_comma_is_kept_whole() -> None:
    value = "data:image/png;base64,iVBORw0KGgo 1x, next.png 2x"
    assert parse(value) == [
        Candidate("data:image/png;base64,iVBORw0KGgo", "1x"),
        Candidate("next.png", "2x"),
    ]


def test_trailing_comma_on_url_separates_candidates() -> None:
    assert parse("a.png, b.png 2x") == [
        Candidate("a.png", ""),
        Candidate("b.png", "2x"),
    ]


def test_whitespace_tolerance() -> None:
    assert parse("  a.png   1x ,\n b.png\t2x  ") == [
        Candidate("a.png", "1x"),
        Candidate("b.png", "2x"),
    ]


def test_leading_and_repeated_commas_are_ignored() -> None:
    assert parse(",, a.png 1x ,, , b.png 2x ,,") == [
        Candidate("a.png", "1x"),
        Candidate("b.png", "2x"),
    ]


def test_empty_value_yields_no_candidates() -> None:
    assert parse("") == []
    assert parse("   ,  , ") == []


def test_invalid_descriptor_drops_the_candidate() -> None:
    assert parse("good.png 2x, bad.png 2z") == [Candidate("good.png", "2x")]


def test_multiple_descriptors_drop_the_candidate() -> None:
    assert parse("x.png 320w 2x") == []


@pytest.mark.parametrize("value", ["pic.png 2X", "pic.png 100W", "pic.png -2x"])
def test_malformed_descriptors_are_rejected(value: str) -> None:
    assert parse(value) == []
