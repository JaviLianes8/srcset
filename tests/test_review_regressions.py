"""One test per finding of the independent review; each fails on the code before the fix."""

from __future__ import annotations

import io
import json
import math
import sys

import pytest

from srcset import Candidate, Environment, SrcsetError, build, parse, parse_sizes, select, validate
from srcset._cli import main
from srcset._css_tokens import tokenize

ENV = Environment(width=1000, height=800)


def test_widths_longer_than_the_int_digit_limit_parse_exactly() -> None:
    digits = "1" * 5000
    (candidate,) = parse(f"a.png {digits}w {digits}h")
    assert candidate.width == candidate.height
    assert build([candidate]) == f"a.png {digits}w {digits}h"
    assert build([("a.png", digits + "w")]) == f"a.png {digits}w"


def test_deep_nesting_is_invalid_instead_of_crashing() -> None:
    assert parse_sizes("(" * 5000 + "1px", ENV) == 1000.0
    assert parse_sizes("calc(" + "(" * 5000 + "1px", ENV) == 1000.0
    assert parse_sizes("(" * 5000 + "1px), 7px", ENV) == 1000.0
    assert parse_sizes("[" + "(" * 40 + ")" * 40 + "], 7px", ENV) == 7.0
    assert validate("a 1w", "(" * 5000)[0].code == "invalid-sizes"
    assert parse_sizes("((((((((((1px))))))))) + 0px), 7px", ENV) == 7.0


def test_shallow_nesting_still_evaluates() -> None:
    nested = "calc(" + "(" * 20 + "3px" + ")" * 20 + ")"
    assert parse_sizes(nested, ENV) == 3.0


def test_huge_numbers_do_not_overflow() -> None:
    assert select("a.png 1" + "0" * 400 + "w", ENV) is not None
    big = "1" + "0" * 400
    issues = validate(f"a {big}w, b {big}w", "100vw")
    assert [issue.code for issue in issues] == ["duplicate-width"]
    with pytest.raises(SrcsetError):
        Candidate("a", density=10**400)
    with pytest.raises(SrcsetError):
        Environment(10**400)


def test_auto_only_counts_when_the_value_starts_with_it() -> None:
    assert parse_sizes("auto, 9px", ENV, auto_width=120) == 120.0
    assert parse_sizes("AuTo", ENV, auto_width=120) == 120.0
    assert parse_sizes("(min-width: 5000px) 5px, auto", ENV, auto_width=120) == 1000.0
    assert parse_sizes("(min-width: 1px) auto, 9px", ENV, auto_width=120) == 9.0
    for value in ("auto , 9px", " auto, 9px", "auto/**/, 9px"):
        assert parse_sizes(value, ENV, auto_width=120) == 9.0, value
    assert [i.code for i in validate("a 1w", "auto , 100px")] == ["invalid-sizes"]
    assert validate("a 1w", "Auto,100px") == []


def test_a_trailing_comma_is_an_authoring_error() -> None:
    assert [issue.code for issue in validate("a.png 1x,")] == ["extra-comma"]
    assert [issue.code for issue in validate("a.png,")] == ["extra-comma"]
    assert validate("a.png 1x, b,c 2x") == []


@pytest.mark.parametrize(
    ("value", "px"),
    [
        ("abs(-10px)", 10.0),
        ("calc(sign(-3px) * -4px)", 4.0),
        ("round(17px, 5px)", 15.0),
        ("round(up, 11px, 5px)", 15.0),
        ("round(down, 14px, 5px)", 10.0),
        ("round(to-zero, 9px, 5px)", 5.0),
        ("round(12.5px, 5px)", 15.0),
        ("calc(round(2.5) * 1px)", 3.0),
        ("mod(-7px, 5px)", 3.0),
        ("rem(17px, 5px)", 2.0),
        ("hypot(3px, 4px)", 5.0),
        ("calc(sqrt(16) * pow(2, 3) * 1px)", 32.0),
        ("calc(log(e) * exp(0) * 9px)", 9.0),
        ("calc(log(8, 2) * 1px)", 3.0),
        ("calc(pi * 1px)", math.pi),
        ("round(1px), 7px", 7.0),
        ("mod(1px, 0px), 7px", 7.0),
        ("calc(1px * infinity), 7px", 7.0),
        ("sqrt(-1), 7px", 7.0),
        ("calc(log(0) * 1px), 7px", 7.0),
        ("calc(pow(10, 400) * 1px), 7px", 7.0),
        ("hypot(1px, 1), 7px", 7.0),
    ],
)
def test_all_the_math_functions(value: str, px: float) -> None:
    assert parse_sizes(value, ENV) == pytest.approx(px)
    codes = [issue.code for issue in validate("a 1w", value.removesuffix(", 7px"))]
    assert codes == ([] if px != 7.0 else ["invalid-sizes"]), value


def test_resolution_is_false_in_the_negative_range() -> None:
    assert parse_sizes("not (resolution: -300dpi) 5px, 9px", ENV) == 5.0
    assert parse_sizes("(min-resolution: -1dppx) 5px, 9px", ENV) == 5.0
    assert parse_sizes("(max-resolution: infinite) 5px, 9px", ENV) == 5.0
    assert parse_sizes("(resolution < infinite) 5px, 9px", ENV) == 5.0


def test_cli_survives_a_legacy_console_encoding(monkeypatch: pytest.MonkeyPatch) -> None:
    out = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", out)
    assert main(["select", "\u4e2d.png 1x"]) == 0
    assert main(["parse", "\u4e2d.png 1x, \udcff.png 2x"]) == 0
    assert main(["check", "\u4e2d 1x, \u4e2d 1x"]) == 1
    out.seek(0)
    lines = out.read().splitlines()
    assert lines[0] == "\\u4e2d.png"
    assert json.loads(lines[1])[0]["url"] == "\u4e2d.png"
    assert lines[2].startswith("duplicate-density")


def test_cli_writes_huge_widths(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["parse", "a " + "9" * 5000 + "w"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["width"] == "9" * 5000


def test_validate_refuses_general_enclosed_and_prefixed_booleans() -> None:
    for sizes in ("(foo bar) 5px, 9px", "(min-width) 5px, 9px", "(min-width > 1px) 5px, 9px"):
        assert [i.code for i in validate("a 1w", sizes)] == ["invalid-sizes"], sizes
    assert validate("a 1w", "(prefers-color-scheme: dark) 5px, 9px") == []


def test_ident_code_points_follow_the_current_syntax() -> None:
    # U+00D7 and U+00A0 are not ident code points; U+00E9 and U+10000 are.
    kinds = [token.kind for token in tokenize("a\u00d7b\u00a0c \u00e9\U00010000")]
    assert kinds == ["ident", "delim", "ident", "delim", "ident", "ws", "ident"]
