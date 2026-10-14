"""A CSS Syntax 3 tokenizer, complete enough to read a sizes attribute like a browser.

Comments vanish, escapes are decoded (``1\\p\\x`` is ``1px``) and every bracket becomes
its own token so the component value step can match blocks.
"""

from __future__ import annotations

from ._css_reader import Reader, Token, digit, ident_char, is_escape, preprocess

_SIMPLE = {"(": "(", ")": ")", "[": "[", "]": "]", "{": "{", "}": "}"}
_WS = " \t\n"
_SIMPLE.update({",": "comma", ":": "colon", ";": "semicolon"})


def tokenize(text: str) -> list[Token]:
    """Split CSS text into tokens; comments are dropped."""
    reader = Reader(preprocess(text))
    tokens: list[Token] = []
    while True:
        while reader.peek() == "/" and reader.peek(1) == "*":
            end = reader.text.find("*/", reader.pos + 2)
            reader.pos = len(reader.text) if end < 0 else end + 2
        c = reader.peek()
        if not c:
            return tokens
        tokens.append(_next(reader, c))


def _next(reader: Reader, c: str) -> Token:
    if c in " \t\n":
        while reader.peek() and reader.peek() in " \t\n":
            reader.pos += 1
        return Token("ws")
    if c in "\"'":
        reader.pos += 1
        return _string(reader, c)
    if c in _SIMPLE:
        reader.pos += 1
        return Token(_SIMPLE[c], c)
    if reader.starts_number():
        return _numeric(reader)
    if c == "-" and reader.peek(1) == "-" and reader.peek(2) == ">":
        reader.pos += 3
        return Token("cdc", "-->")
    if reader.starts_ident():
        return _ident_like(reader)
    if c == "#" and (ident_char(reader.peek(1)) or is_escape(reader.peek(1), reader.peek(2))):
        reader.pos += 1
        return Token("hash", reader.name())
    if c == "@" and reader.starts_ident(1):
        reader.pos += 1
        return Token("at-keyword", reader.name())
    if reader.text.startswith("<!--", reader.pos):
        reader.pos += 4
        return Token("cdo", "<!--")
    reader.pos += 1
    return Token("delim", c)


def _string(reader: Reader, quote: str) -> Token:
    out: list[str] = []
    while True:
        c = reader.peek()
        if not c or c == quote:
            reader.pos += 1 if c else 0
            return Token("string", "".join(out))
        if c == "\n":
            return Token("bad-string")
        reader.pos += 1
        if c != "\\":
            out.append(c)
        elif reader.peek() == "\n":
            reader.pos += 1
        elif reader.peek():
            out.append(reader.escape())


def _numeric(reader: Reader) -> Token:
    start = reader.pos
    if reader.peek() in ("+", "-"):
        reader.pos += 1
    while digit(reader.peek()):
        reader.pos += 1
    if reader.peek() == "." and digit(reader.peek(1)):
        reader.pos += 1
        while digit(reader.peek()):
            reader.pos += 1
    e, sign, third = reader.peek(), reader.peek(1), reader.peek(2)
    if e in ("e", "E") and e and (digit(sign) or (sign in ("+", "-") and sign and digit(third))):
        reader.pos += 2
        while digit(reader.peek()):
            reader.pos += 1
    text = reader.text[start : reader.pos]
    number = float(text)
    if reader.starts_ident():
        return Token("dimension", text, number, reader.name())
    if reader.peek() == "%":
        reader.pos += 1
        return Token("percentage", text, number)
    return Token("number", text, number)


def _ident_like(reader: Reader) -> Token:
    name = reader.name()
    if reader.peek() != "(":
        return Token("ident", name)
    reader.pos += 1
    if name.lower() != "url":
        return Token("function", name)
    while reader.peek() in _WS and reader.peek() and reader.peek(1) in _WS and reader.peek(1):
        reader.pos += 1
    after = reader.peek(1) if reader.peek() in _WS and reader.peek() else reader.peek()
    if after and after in "\"'":
        return Token("function", name)
    return _url(reader)


def _url(reader: Reader) -> Token:
    while reader.peek() and reader.peek() in _WS:
        reader.pos += 1
    out: list[str] = []
    while True:
        c = reader.peek()
        reader.pos += 1 if c else 0
        if not c or c == ")":
            return Token("url", "".join(out))
        if c in _WS:
            while reader.peek() and reader.peek() in _WS:
                reader.pos += 1
            if reader.peek() in (")", ""):
                reader.pos += 1 if reader.peek() else 0
                return Token("url", "".join(out))
        elif c == "\\" and is_escape(c, reader.peek()):
            out.append(reader.escape())
            continue
        elif c not in "\"'(\\" and not _non_printable(c):
            out.append(c)
            continue
        while reader.peek() not in (")", ""):
            if is_escape(reader.peek(), reader.peek(1)):
                reader.pos += 1
                reader.escape()
            else:
                reader.pos += 1
        reader.pos += 1 if reader.peek() else 0
        return Token("bad-url")


def _non_printable(c: str) -> bool:
    code = ord(c)
    return code <= 8 or code == 0x0B or 0x0E <= code <= 0x1F or code == 0x7F
