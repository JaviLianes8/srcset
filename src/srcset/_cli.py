"""Command line: ``srcset parse``, ``srcset select`` and ``srcset check``."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from ._model import Environment, SrcsetError
from ._numbers import int_text
from ._parse import parse
from ._select import select
from ._validate import validate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="srcset", description="Read HTML srcset and sizes.")
    commands = parser.add_subparsers(dest="command", required=True)
    read = commands.add_parser("parse", help="print the candidates as JSON")
    read.add_argument("srcset")
    pick = commands.add_parser("select", help="print the URL a browser would fetch")
    pick.add_argument("srcset")
    pick.add_argument("--sizes", default="", help="the sizes attribute")
    pick.add_argument("--src", default="", help="the src attribute, used as 1x")
    pick.add_argument("--width", type=float, default=1280.0, help="viewport width in px")
    pick.add_argument("--height", type=float, default=None, help="viewport height in px")
    pick.add_argument("--dpr", type=float, default=1.0, help="device pixel ratio")
    pick.add_argument("--json", action="store_true", help="print URL and density as JSON")
    check = commands.add_parser("check", help="list authoring errors; exit 1 if any")
    check.add_argument("srcset")
    check.add_argument("--sizes", default=None, help="the sizes attribute, if present")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line; returns the exit status."""
    args = _parser().parse_args(argv)
    if args.command == "parse":
        rows = [
            {"url": c.url, "width": _int(c.width), "density": c.density, "height": _int(c.height)}
            for c in parse(args.srcset)
        ]
        _say(json.dumps(rows))
        return 0
    if args.command == "select":
        try:
            env = Environment(args.width, args.height, args.dpr)
        except SrcsetError as error:
            print(f"srcset: {error}", file=sys.stderr)
            return 2
        chosen = select(args.srcset, env, sizes=args.sizes, src=args.src)
        if chosen is None:
            print("srcset: no image candidate", file=sys.stderr)
            return 1
        if args.json:
            _say(json.dumps({"url": chosen.url, "density": chosen.density}))
        else:
            _say(chosen.url)
        return 0
    issues = validate(args.srcset, args.sizes)
    for issue in issues:
        _say(f"{issue.code}: {issue.message}")
    return 1 if issues else 0


def _int(value: int | None) -> int | str | None:
    # json cannot write an int past the interpreter's digit limit; such a width is text.
    return int_text(value) if value is not None and value >= 10**400 else value


def _say(text: str) -> None:
    """Print a line that the console encoding may not cover, escaping what it cannot hold.

    A URL can hold any character, and a Windows pipe defaults to a legacy code page.
    """
    encoding = sys.stdout.encoding or "utf-8"
    print(text.encode(encoding, "backslashreplace").decode(encoding))
