"""Sizes values. Hand-written from the HTML algorithm (4.8.4.3.11), CSS Values 4 units and
math functions, and the Media Queries 4 grammar; the browser corpus runs in test_wpt.py."""

from __future__ import annotations

import pytest

from srcset import Environment, SrcsetError, parse_sizes

ENV = Environment(width=1000, height=800, density=2, font_size=20)


@pytest.mark.parametrize(
    ("value", "px"),
    [
        ("10px", 10.0),
        ("1in", 96.0),
        ("2.54cm", 96.0),
        ("25.4mm", 96.0),
        ("101.6Q", 96.0),
        ("72pt", 96.0),
        ("6pc", 96.0),
        ("2em", 40.0),
        ("2rem", 40.0),
        ("2ex", 20.0),
        ("2ch", 20.0),
        ("1lh", 24.0),
        ("50vw", 500.0),
        ("50vh", 400.0),
        ("50vi", 500.0),
        ("50vb", 400.0),
        ("50vmin", 400.0),
        ("50vmax", 500.0),
        ("10svw", 100.0),
        ("10LVH", 80.0),
        ("10dvmax", 100.0),
        ("0", 0.0),
        ("-0", 0.0),
        ("+.5e1px", 5.0),
    ],
)
def test_lengths(value: str, px: float) -> None:
    assert parse_sizes(value, ENV) == pytest.approx(px)


@pytest.mark.parametrize(
    ("value", "px"),
    [
        ("calc(100vw - 2 * 1em)", 960.0),
        ("calc((10px + 5px) / 3)", 5.0),
        ("calc(2 * (1px + 1px))", 4.0),
        ("min(30vw, 200px)", 200.0),
        ("max(1px, 2px, 3px)", 3.0),
        ("clamp(100px, 50vw, 300px)", 300.0),
        ("calc(-5px)", 0.0),
        ("calc(10px", 10.0),
        ("CALC(10PX)", 10.0),
    ],
)
def test_math_functions(value: str, px: float) -> None:
    assert parse_sizes(value, ENV) == pytest.approx(px)


@pytest.mark.parametrize(
    "value",
    [
        "",
        "-1px",
        "1",
        "10%",
        "10deg",
        "calc(1px+2px)",
        "calc(1px -2px)",
        "calc(1px * 2px)",
        "calc(2 / 1px)",
        "calc(1px / 0)",
        "calc(1px + 1)",
        "calc()",
        "min(1px, 1)",
        "clamp(1px, 2px)",
        "sqrt(4px)",
        "calc(1px * infinity)",
        "var(--x)",
        "1px !important",
        "foo",
        "1e999px",
        "calc(1e308px * 10)",
        "(min-width: 1px)",
    ],
)
def test_invalid_entries_fall_back_to_the_viewport(value: str) -> None:
    assert parse_sizes(value, ENV) == 1000.0
    assert parse_sizes(f"{value}, 7px", ENV) == 7.0


@pytest.mark.parametrize(
    ("condition", "matches"),
    [
        ("(min-width: 1000px)", True),
        ("(min-width: 1001px)", False),
        ("(max-width: 50em)", True),
        ("(width: 1000px)", True),
        ("(width >= 1000px)", True),
        ("(width > 1000px)", False),
        ("(900px < width <= 1000px)", True),
        ("(1000px < width)", False),
        ("(1100px > width > 900px)", True),
        ("(width < = 1000px)", False),
        ("(height: 800px) and (orientation: landscape)", True),
        ("(orientation: portrait)", False),
        ("(aspect-ratio: 5/4)", True),
        ("(min-aspect-ratio: 2/1)", False),
        ("(min-resolution: 2dppx) and (max-resolution: 192dpi)", True),
        ("(resolution: 2x)", True),
        ("(width)", True),
        ("(min-width)", False),
        ("not (min-width: 2000px)", True),
        ("(min-width: 2000px) or (max-width: 2000px)", True),
        ("((min-width: 1px) and (max-width: 2px)) or (width: 1000px)", True),
        ("(min-width: 1px) and (max-width: 2px)", False),
        ("(min-width: 1px) and (unknown: 1)", False),
        ("not (unknown: 1)", False),
        ("(prefers-color-scheme: dark)", False),
        ("(min-orientation: portrait)", False),
        ("(width: 10%)", False),
        ("(min-width: 1px) and (min-width: 2px) or (width)", False),
        ("screen and (min-width: 1px)", False),
        ("not(min-width: 1px)", False),
        ("[min-width: 1px]", False),
    ],
)
def test_media_conditions(condition: str, matches: bool) -> None:
    assert (parse_sizes(f"{condition} 5px, 9px", ENV) == 5.0) is matches


def test_unknown_height_makes_height_conditions_unknown() -> None:
    env = Environment(width=500)
    assert parse_sizes("(min-height: 1px) 5px, 9px", env) == 9.0
    assert parse_sizes("not (min-height: 1px) 5px, 9px", env) == 9.0
    assert parse_sizes("50vh, 9px", env) == 9.0
    assert parse_sizes("50vh", env) == 500.0
    assert parse_sizes("(min-width: 1px) 5px, 9px", env) == 5.0


def test_first_matching_entry_wins_and_bare_sizes_are_accepted_early() -> None:
    assert parse_sizes("(min-width: 1px) 5px, (min-width: 1px) 6px, 9px", ENV) == 5.0
    assert parse_sizes("3px, (min-width: 1px) 5px", ENV) == 3.0


def test_auto_needs_a_width() -> None:
    assert parse_sizes("auto, 300px", ENV) == 300.0
    assert parse_sizes("auto, 300px", ENV, auto_width=120) == 120.0
    assert parse_sizes("AUTO", ENV, auto_width=0) == 0.0
    assert parse_sizes("auto", ENV) == 1000.0


def test_bad_arguments() -> None:
    with pytest.raises(TypeError):
        parse_sizes(None, ENV)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        parse_sizes("1px", None)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        parse_sizes("auto", ENV, auto_width="1")  # type: ignore[arg-type]
    for width in (-1.0, float("inf"), float("nan")):
        with pytest.raises(SrcsetError):
            parse_sizes("auto", ENV, auto_width=width)
