"""Media condition grammar and features, hand-written from Media Queries 4
(https://drafts.csswg.org/mediaqueries-4/): sections 3, 4 and 2.4 (ranges and ratios)."""

from __future__ import annotations

import pytest

from srcset import Environment, parse_sizes

WIDE = Environment(width=1000, height=800, density=2)


@pytest.mark.parametrize(
    ("condition", "matches"),
    [
        ("()", False),
        ("not (width) and (height)", False),
        ("(width) (height)", False),
        ("(width) and (height) and (min-width: 2000px)", False),
        ("(width) and (height) and (width)", True),
        ("(min-width: 2000px) or (max-width: 10px)", False),
        ("(width) or [x]", False),
        ("(width) or f(x)", True),
        ("(2000px > width)", True),
        ("(900px < width < 950px)", False),
        ("(900px < width > 100px)", False),
        ("(1000px <= width < 1100px)", True),
        ("(width <)", False),
        ("(width>=1000px)", True),
        ("(width<=999px)", False),
        ("(1px < width < 2000px < 3000px)", False),
        ("(width = 1000px)", True),
        ("(width = 999px)", False),
        ("(width < 1001px)", True),
        ("(width < 1000px)", False),
        ("(width <= 1000px)", True),
        ("(width > 999px)", True),
        ("(width: 1000)", False),
        ("(width: 0)", False),
        ("(min-width: 0)", True),
        ("(width: 1000px 2px)", False),
        ("(resolution: 192dpi)", True),
        ("(min-resolution: 75dpcm) and (max-resolution: 76dpcm)", True),
        ("(resolution: 2dppx)", True),
        ("(resolution: 2px)", False),
        ("(orientation)", True),
        ("(orientation = landscape)", False),
        ("(orientation: square)", False),
        ("(orientation: landscape)", True),
        ("(aspect-ratio: 1.25)", True),
        ("(aspect-ratio: 5 * 4)", False),
        ("(aspect-ratio: -5/-4)", False),
        ("(aspect-ratio: 0.5/0.4)", True),
        ("(min-aspect-ratio: 0/1)", True),
        ("(aspect-ratio: 5px/4px)", False),
        ("(aspect-ratio: 1.25/1)", True),
        ("(aspect-ratio: 5/0)", False),
        ("(aspect-ratio: 5 / 4 / 1)", False),
    ],
)
def test_conditions(condition: str, matches: bool) -> None:
    assert (parse_sizes(f"{condition} 5px, 9px", WIDE) == 5.0) is matches


def test_square_viewports_are_portrait() -> None:
    square = Environment(width=800, height=800)
    assert parse_sizes("(orientation: portrait) 5px, 9px", square) == 5.0


def test_zero_sized_viewports() -> None:
    empty = Environment(width=0, height=0)
    assert parse_sizes("(width) 5px, 9px", empty) == 9.0
    assert parse_sizes("(aspect-ratio > 1) 5px, 9px", Environment(800, 0)) == 9.0


def test_features_that_need_the_height_are_unknown_without_it() -> None:
    no_height = Environment(width=500)
    for condition in ("(orientation)", "(aspect-ratio: 1)", "(height)", "not (height: 1px)"):
        assert parse_sizes(f"{condition} 5px, 9px", no_height) == 9.0, condition
