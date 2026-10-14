"""CSS component values: tokens grouped into matched blocks and functions (CSS Syntax 3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

from ._css_reader import Token
from ._css_tokens import tokenize

_CLOSE = {"(": ")", "[": "]", "{": "}"}
MAX_DEPTH = 32


@dataclass
class Block:
    """A ``(``, ``[`` or ``{`` block, or a function when ``name`` is set."""

    opener: str
    name: str | None = None
    items: list[Value] = field(default_factory=list)


Value: TypeAlias = "Token | Block"


def comma_separated(text: str) -> list[list[Value]]:
    """Parse a comma-separated list of component values; commas in blocks do not split."""
    tokens = tokenize(text)
    tokens.reverse()
    groups: list[list[Value]] = [[]]
    while tokens:
        token = tokens.pop()
        if token.kind == "comma":
            groups.append([])
        else:
            groups[-1].append(_component(token, tokens))
    return groups


def _component(token: Token, stack: list[Token], depth: int = 0) -> Value:
    if token.kind == "function":
        return _block(Block("(", token.value), stack, depth + 1)
    if token.kind in _CLOSE:
        return _block(Block(token.kind), stack, depth + 1)
    return token


def _block(block: Block, stack: list[Token], depth: int) -> Value:
    """Fill a block up to its closing token or the end of input (unclosed is fine).

    Past ``MAX_DEPTH`` levels the block is skipped and replaced by a ``too-deep`` token
    that no grammar accepts, so hostile nesting cannot exhaust the call stack.
    """
    if depth > MAX_DEPTH:
        return _skip(_CLOSE[block.opener], stack)
    close = _CLOSE[block.opener]
    while stack:
        token = stack.pop()
        if token.kind == close:
            return block
        block.items.append(_component(token, stack, depth))
    return block


def _skip(close: str, stack: list[Token]) -> Token:
    closers = [close]
    while stack and closers:
        token = stack.pop()
        if token.kind == closers[-1]:
            closers.pop()
        elif token.kind == "function":
            closers.append(")")
        elif token.kind in _CLOSE:
            closers.append(_CLOSE[token.kind])
    return Token("too-deep")


def is_ws(value: Value) -> bool:
    return isinstance(value, Token) and value.kind == "ws"


def strip(values: list[Value]) -> list[Value]:
    """Drop whitespace tokens at both ends."""
    start, end = 0, len(values)
    while start < end and is_ws(values[start]):
        start += 1
    while end > start and is_ws(values[end - 1]):
        end -= 1
    return values[start:end]


def ident(value: Value, *names: str) -> str | None:
    """The lower-cased name of an identifier, if it is one (and one of ``names``)."""
    if isinstance(value, Token) and value.kind == "ident":
        name = _ascii_lower(value.value)
        return name if not names or name in names else None
    return None


def _ascii_lower(text: str) -> str:
    return "".join(c.lower() if c.isascii() else c for c in text)


def is_any_value(values: list[Value]) -> bool:
    """True when the values match ``<any-value>``: no stray closers, no bad tokens."""
    for value in values:
        if isinstance(value, Block):
            if not is_any_value(value.items):
                return False
        elif value.kind in (")", "]", "}", "bad-string", "bad-url", "too-deep"):
            return False
    return True
