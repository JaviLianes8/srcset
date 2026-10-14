"""The private CSS tokenizer and component values. Hand-written from CSS Syntax 3
(https://drafts.csswg.org/css-syntax-3/), sections 4.3 and 5."""

from __future__ import annotations

from srcset._css_reader import Token
from srcset._css_tokens import tokenize
from srcset._css_values import Block, comma_separated, is_any_value


def _kinds(text: str) -> list[str]:
    return [token.kind for token in tokenize(text)]


def test_numbers_dimensions_and_percentages() -> None:
    tokens = tokenize("+.5e1px 10% -3 1e")
    assert [(t.kind, t.number, t.unit) for t in tokens if t.kind != "ws"] == [
        ("dimension", 5.0, "px"),
        ("percentage", 10.0, ""),
        ("number", -3.0, ""),
        ("dimension", 1.0, "e"),
    ]


def test_comments_vanish_and_do_not_join_tokens() -> None:
    assert _kinds("1/* x */px") == ["number", "ident"]
    assert _kinds("/* unclosed") == []


def test_escapes_in_names() -> None:
    (token,) = tokenize(r"1\p\x")
    assert (token.kind, token.unit) == ("dimension", "px")
    (token,) = tokenize("\\31 a")
    assert (token.kind, token.value) == ("ident", "1a")
    (token,) = tokenize("a\\0 b")
    assert token.value == "a\ufffdb"
    (token,) = tokenize("a\\110000")
    assert token.value == "a\ufffd"
    (token,) = tokenize("a\\")
    assert token.value == "a\ufffd"
    assert _kinds("\\\n") == ["delim", "ws"]


def test_strings() -> None:
    assert tokenize("'a\\62 c'") == [Token("string", "abc")]
    assert tokenize('"a\\\nb"') == [Token("string", "ab")]
    assert tokenize('"open') == [Token("string", "open")]
    assert _kinds('"a\nb"') == ["bad-string", "ws", "ident", "string"]


def test_url_tokens() -> None:
    assert tokenize("url( a.png )") == [Token("url", "a.png")]
    assert tokenize("URL(a\\)b)") == [Token("url", "a)b")]
    assert _kinds("url(a b)") == ["bad-url"]
    assert _kinds('url(a"b) x') == ["bad-url", "ws", "ident"]
    assert _kinds("url(a\x01)") == ["bad-url"]
    assert _kinds("url( 'a')") == ["function", "ws", "string", ")"]
    assert tokenize("url(a") == [Token("url", "a")]


def test_other_tokens() -> None:
    assert _kinds("#a #1 # @x @ <!-- --> -->x") == [
        "hash", "ws", "hash", "ws", "delim", "ws", "at-keyword", "ws", "delim", "ws",
        "cdo", "ws", "cdc", "ws", "cdc", "ident",
    ]  # fmt: skip
    assert _kinds("--x -x -1 -.5 - .") == [
        "ident", "ws", "ident", "ws", "number", "ws", "number", "ws", "delim", "ws", "delim",
    ]  # fmt: skip


def test_preprocessing() -> None:
    assert _kinds("a\r\nb\x0cc\rd") == ["ident", "ws", "ident", "ws", "ident", "ws", "ident"]
    assert tokenize("a\0") == [Token("ident", "a\ufffd")]


def test_commas_split_only_at_the_top_level() -> None:
    groups = comma_separated("a(1, 2), [b, c], d")
    assert len(groups) == 3
    first = groups[0][0]
    assert isinstance(first, Block) and first.name == "a" and len(first.items) == 4
    assert comma_separated("") == [[]]
    assert len(comma_separated("((),1px")) == 1


def test_any_value_rejects_stray_closers_and_bad_tokens() -> None:
    assert is_any_value(comma_separated("(a !)")[0])
    for text in ("(])", "(})", "[)]", "('a\n)", "(url(a b))"):
        assert not is_any_value(comma_separated(text)[0]), text
