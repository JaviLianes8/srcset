from __future__ import annotations

import random

import pytest

from srcset import Candidate, SrcsetError, build, parse


def test_build_with_descriptors() -> None:
    assert build([("small.png", "1x"), ("large.png", "2x")]) == "small.png 1x, large.png 2x"


def test_build_from_candidates() -> None:
    items = [Candidate("a.png", 320, height=200), Candidate("b.png", density=1.5)]
    assert build(items) == "a.png 320w 200h, b.png 1.5x"


def test_build_without_descriptor() -> None:
    assert build([("plain.png", ""), Candidate("next.png")]) == "plain.png, next.png"


def test_descriptor_text_is_normalized() -> None:
    assert build([("a.png", " 2.0x\t")]) == "a.png 2x"
    assert build([("a.png", "50h 100w")]) == "a.png 100w 50h"


def test_round_trip_keeps_a_url_with_commas() -> None:
    value = "data:image/png;base64,iVBORw0KGgo 1x, next.png 2x"
    assert build(parse(value)) == value


@pytest.mark.parametrize(
    "url", ["", "has space.png", "tab\t.png", "a.png,", ",a.png", "line\n.png", "ff\x0c.png"]
)
def test_build_rejects_urls_the_parser_would_split(url: str) -> None:
    with pytest.raises(SrcsetError):
        build([(url, "2x")])


def test_build_keeps_characters_that_are_not_ascii_whitespace() -> None:
    assert parse(build([("a\x0bb\xa0.png", "1x")])) == [Candidate("a\x0bb\xa0.png", density=1)]


@pytest.mark.parametrize("descriptor", ["2z", "1.x", "0w", "1w 1x", "1h", "(2x)", "1x,", "2X"])
def test_build_rejects_descriptors_the_parser_drops(descriptor: str) -> None:
    with pytest.raises(SrcsetError):
        build([("a.png", descriptor)])


def test_build_rejects_wrong_types() -> None:
    with pytest.raises(TypeError):
        build("a.png 1x")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        build([("a.png", "1x", "extra")])  # type: ignore[list-item]
    with pytest.raises(TypeError):
        build([("a.png", 2)])  # type: ignore[list-item]
    with pytest.raises(TypeError):
        build(["a.png"])  # type: ignore[list-item]


def _random_candidate(rng: random.Random) -> Candidate:
    url = "".join(rng.choice("ab,;:/()=\x0b\xa0\u00e9") for _ in range(rng.randint(1, 6)))
    url = "u" + url + "v"
    kind = rng.randrange(4)
    if kind == 0:
        return Candidate(url)
    if kind == 1:
        return Candidate(url, density=rng.choice([0.0, 0.5, 1.0, 2.0, 1e-7, 3e16, rng.random()]))
    width = rng.randint(1, 10**20)
    return Candidate(url, width, height=rng.randint(1, 5000) if kind == 3 else None)


def test_parse_reads_back_whatever_build_writes() -> None:
    # Hand-written property check with a fixed seed, so a failure is reproducible.
    rng = random.Random(20261013)
    for _ in range(500):
        items = [_random_candidate(rng) for _ in range(rng.randint(1, 5))]
        assert parse(build(items)) == items
