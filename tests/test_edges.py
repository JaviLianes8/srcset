"""Edge cases that pin details a careless change would get wrong (found by mutation runs)."""

from __future__ import annotations

import json

import pytest

from srcset import Environment, build, parse_sizes
from srcset._cli import main

ENV = Environment(width=1000, height=800, font_size=20)


def test_build_explains_type_errors() -> None:
    with pytest.raises(TypeError, match="not a string"):
        build("a.png 1x")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="must both be str"):
        build([("a.png", 2)])  # type: ignore[list-item]
    with pytest.raises(TypeError, match="must both be str"):
        build([(2, "1x")])  # type: ignore[list-item]


@pytest.mark.parametrize(
    ("value", "px"),
    [
        ("1cap", 14.0),
        ("1ic", 20.0),
        ("1rcap", 14.0),
        ("1xem, 7px", 7.0),
        ("1spx, 7px", 7.0),
        ("min(1px, foo), 7px", 7.0),
        ("calc(1px+ 2px), 7px", 7.0),
        ("calc(1px +(2px)), 7px", 7.0),
        ("calc(2 (3) 4px), 7px", 7.0),
        ("calc(1px (2px)), 7px", 7.0),
        ("calc(2 * 3 * 1px)", 6.0),
        ("calc(12px / 2 / 3)", 2.0),
        ("calc(1px - 2px + 4px)", 3.0),
    ],
)
def test_units_and_math_details(value: str, px: float) -> None:
    assert parse_sizes(value, ENV) == pytest.approx(px)


def test_cli_default_viewport_is_1280_px(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["select", "a.png 1280w, b.png 1281w"]) == 0
    assert capsys.readouterr().out == "a.png\n"


def test_cli_writes_widths_as_numbers_below_the_cutoff(capsys: pytest.CaptureFixture[str]) -> None:
    below, at = 10**400 - 1, 10**400
    assert main(["parse", f"a {below}w, b {at}w"]) == 0
    rows = json.loads(capsys.readouterr().out)
    assert rows[0]["width"] == below
    assert rows[1]["width"] == "1" + "0" * 400
