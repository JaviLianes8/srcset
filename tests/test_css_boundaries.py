"""Boundaries of the CSS tokenizer, hand-written from CSS Syntax 3
(https://drafts.csswg.org/css-syntax-3/): 3.3 preprocessing, 4.2 definitions, 4.3.7 escapes,
4.3.6 url tokens."""

from __future__ import annotations

import pytest

from srcset._css_reader import ident_start, preprocess
from srcset._css_tokens import tokenize
from srcset._css_values import comma_separated

# The non-ASCII ident code point ranges, inclusive.
RANGES = [
    (0xB7, 0xB7), (0xC0, 0xD6), (0xD8, 0xF6), (0xF8, 0x37D), (0x37F, 0x1FFF),
    (0x200C, 0x200D), (0x203F, 0x2040), (0x2070, 0x218F), (0x2C00, 0x2FEF),
    (0x3001, 0xD7FF), (0xF900, 0xFDCF), (0xFDF0, 0xFFFD), (0x10000, 0x10FFFF),
]  # fmt: skip


def _inside(code: int) -> bool:
    return any(low <= code <= high for low, high in RANGES)


@pytest.mark.parametrize(("low", "high"), RANGES)
def test_ident_ranges_are_exact(low: int, high: int) -> None:
    assert ident_start(chr(low)) and ident_start(chr(high))
    for code in (low - 1, high + 1):
        if 0x80 <= code <= 0x10FFFF and not 0xD800 <= code <= 0xDFFF:
            assert ident_start(chr(code)) is _inside(code), hex(code)


def test_surrogates_and_nul_are_replaced() -> None:
    text = "\0\ud7ff" + chr(0xD800) + chr(0xDFFF) + "\ue000"
    assert preprocess(text) == "\ufffd\ud7ff\ufffd\ufffd\ue000"


@pytest.mark.parametrize(
    ("css", "name"),
    [
        ("a\\0000417", "aA7"),
        ("a\\41b", "a\u041b"),
        ("a\\41 b", "aAb"),
        ("a\\d7ff", "a\ud7ff"),
        ("a\\d800", "a\ufffd"),
        ("a\\dfff", "a\ufffd"),
        ("a\\e000", "a\ue000"),
        ("a\\10ffff", "a\U0010ffff"),
        ("a\\110000", "a\ufffd"),
    ],
)
def test_escape_boundaries(css: str, name: str) -> None:
    assert [(t.kind, t.value) for t in tokenize(css)] == [("ident", name)]


def _kinds(css: str) -> list[str]:
    return [token.kind for token in tokenize(css)]


def test_escape_lookahead() -> None:
    assert _kinds("a\\\nb") == ["ident", "delim", "ws", "ident"]
    assert _kinds("-\\\nx") == ["delim", "delim", "ws", "ident"]
    assert _kinds("#\\\nx") == ["delim", "delim", "ws", "ident"]
    assert [(t.kind, t.value) for t in tokenize("#\\41 @cd #ab")] == [
        ("hash", "A"), ("at-keyword", "cd"), ("ws", ""), ("hash", "ab"),
    ]  # fmt: skip
    assert [(t.kind, t.value) for t in tokenize('"a\\')] == [("string", "a")]


def test_url_whitespace_and_remnants() -> None:
    assert _kinds("url(  'a')") == ["function", "ws", "string", ")"]
    assert _kinds("url(a ) b") == ["url", "ws", "ident"]
    assert _kinds("url(a   ) b") == ["url", "ws", "ident"]
    assert _kinds("url(a\\\nb) x") == ["bad-url", "ws", "ident"]
    assert _kinds("url(a b\\)c) x") == ["bad-url", "ws", "ident"]


@pytest.mark.parametrize("code", [0x01, 0x08, 0x0B, 0x0E, 0x1F, 0x7F])
def test_non_printable_code_points_make_a_bad_url(code: int) -> None:
    assert _kinds(f"url(a{chr(code)})") == ["bad-url"]


@pytest.mark.parametrize("code", [0x20 + 1, 0x7E, 0x80, 0xE9])
def test_printable_code_points_stay_in_the_url(code: int) -> None:
    assert [(t.kind, t.value) for t in tokenize(f"url(a{chr(code)})")] == [("url", "a" + chr(code))]


def test_skipped_deep_blocks_keep_the_outer_structure() -> None:
    deep = "(" * 40 + "f([{1, 2}])" + ")" * 40
    (group,) = comma_separated(deep + " x")
    assert [getattr(item, "kind", "block") for item in group] == ["block", "ws", "ident"]
    groups = comma_separated(deep + ", y")
    assert len(groups) == 2
