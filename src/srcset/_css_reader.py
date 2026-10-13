"""Character-level helpers for the CSS tokenizer: the token type and an input cursor."""

from __future__ import annotations

from typing import NamedTuple


class Token(NamedTuple):
    kind: str  # ident, function, number, dimension, percentage, delim, ws, (, ), ...
    value: str = ""  # name, unit-less text or the delim character
    number: float = 0.0
    unit: str = ""


def preprocess(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x0c", "\n")
    return "".join("\ufffd" if c == "\0" or 0xD800 <= ord(c) <= 0xDFFF else c for c in text)


# Non-ASCII ident code points (CSS Syntax 3, 4.2), as inclusive ranges.
_NON_ASCII_IDENT = (
    (0xB7, 0xB7), (0xC0, 0xD6), (0xD8, 0xF6), (0xF8, 0x37D), (0x37F, 0x1FFF),
    (0x200C, 0x200D), (0x203F, 0x2040), (0x2070, 0x218F), (0x2C00, 0x2FEF),
    (0x3001, 0xD7FF), (0xF900, 0xFDCF), (0xFDF0, 0xFFFD), (0x10000, 0x10FFFF),
)  # fmt: skip


def ident_start(c: str) -> bool:
    if c.isascii():
        return c.isalpha() or c == "_"
    code = ord(c)
    return any(low <= code <= high for low, high in _NON_ASCII_IDENT)


def ident_char(c: str) -> bool:
    return ident_start(c) or (c.isascii() and c.isdigit()) or c == "-"


def digit(c: str) -> bool:
    return c != "" and c in "0123456789"


def is_escape(a: str, b: str) -> bool:
    return a == "\\" and b != "\n"


class Reader:
    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0

    def peek(self, n: int = 0) -> str:
        i = self.pos + n
        return self.text[i] if i < len(self.text) else ""

    def starts_ident(self, n: int = 0) -> bool:
        a, b, c = self.peek(n), self.peek(n + 1), self.peek(n + 2)
        if a == "-":
            return ident_start(b) or b == "-" or is_escape(b, c)
        return ident_start(a) or is_escape(a, b)

    def starts_number(self) -> bool:
        a, b, c = self.peek(), self.peek(1), self.peek(2)
        if a in ("+", "-") and a:
            return digit(b) or (b == "." and digit(c))
        return digit(a) or (a == "." and digit(b))

    def escape(self) -> str:
        """Consume an escape whose backslash is already consumed."""
        c = self.peek()
        if not c:
            return "\ufffd"
        self.pos += 1
        if c not in "0123456789abcdefABCDEF":
            return c
        digits = c
        while len(digits) < 6 and self.peek() and self.peek() in "0123456789abcdefABCDEF":
            digits += self.peek()
            self.pos += 1
        if self.peek() and self.peek() in " \t\n":
            self.pos += 1
        code = int(digits, 16)
        if code == 0 or 0xD800 <= code <= 0xDFFF or code > 0x10FFFF:
            return "\ufffd"
        return chr(code)

    def name(self) -> str:
        out: list[str] = []
        while True:
            c = self.peek()
            if ident_char(c):
                out.append(c)
                self.pos += 1
            elif is_escape(c, self.peek(1)):
                self.pos += 1
                out.append(self.escape())
            else:
                return "".join(out)
