import pytest

from srcset import Candidate, SrcsetError, build, parse


def test_build_with_descriptors() -> None:
    result = build([("small.png", "1x"), ("large.png", "2x")])
    assert result == "small.png 1x, large.png 2x"


def test_build_without_descriptor() -> None:
    assert build([("plain.png", "")]) == "plain.png"


def test_build_accepts_candidate_tuples() -> None:
    assert build([Candidate("a.png", "320w")]) == "a.png 320w"


def test_round_trip_width_and_density() -> None:
    value = "a.png 320w, b.png 640w, c.png 2x"
    assert build(parse(value)) == value


def test_round_trip_url_with_comma() -> None:
    value = "data:image/png;base64,iVBORw0KGgo 1x, next.png 2x"
    assert build(parse(value)) == value


def test_build_rejects_empty_url() -> None:
    with pytest.raises(SrcsetError):
        build([("", "2x")])


def test_build_rejects_whitespace_in_url() -> None:
    with pytest.raises(SrcsetError):
        build([("has space.png", "2x")])


def test_build_rejects_trailing_comma_url() -> None:
    with pytest.raises(SrcsetError):
        build([("a.png,", "")])


def test_build_rejects_invalid_descriptor() -> None:
    with pytest.raises(SrcsetError):
        build([("a.png", "2z")])
