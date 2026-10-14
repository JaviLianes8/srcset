"""Lengths and math functions (``calc``, ``min``, ``clamp``, ``round``...), resolved to px.

A quantity is ``(value, is_length)``: a plain number or a length in CSS pixels. Font
relative units other than ``em`` and ``rem`` use fixed ratios, because the real values
depend on font metrics a library cannot know.
"""

from __future__ import annotations

import math

from ._css_reader import Token
from ._css_values import Block, Value, ident, is_ws, strip
from ._math_functions import CONSTANTS, STRATEGIES, Quantity, apply
from ._model import Environment

_ABSOLUTE = {"px": 1.0, "in": 96.0, "cm": 96 / 2.54, "mm": 96 / 25.4, "q": 96 / 101.6}
_ABSOLUTE.update({"pt": 96 / 72, "pc": 16.0})
_FONT = {"em": 1.0, "ex": 0.5, "ch": 0.5, "cap": 0.7, "ic": 1.0, "lh": 1.2}
_MATH = frozenset((
    "calc", "min", "max", "clamp", "abs", "sign", "round", "mod", "rem", "hypot", "sqrt",
    "pow", "exp", "log",
))  # fmt: skip


def unit_px(unit: str, env: Environment) -> float | None:
    """Pixels in one ``unit`` (ASCII case-insensitive), or ``None`` if not a length unit."""
    unit = unit.lower() if unit.isascii() else unit
    if unit in _ABSOLUTE:
        return _ABSOLUTE[unit]
    font = unit[1:] if unit.startswith("r") and unit[1:] in _FONT else unit
    if font in _FONT:
        return _FONT[font] * env.font_size
    axis = unit[1:] if unit[:1] in ("s", "l", "d") and len(unit) > 2 else unit
    width, height = env.width, env.height
    sizes = {"vw": width, "vi": width, "vh": height, "vb": height}
    if axis in sizes:
        value = sizes[axis]
        return None if value is None else value / 100
    if axis in ("vmin", "vmax"):
        if height is None:
            return None
        return (min if axis == "vmin" else max)(width, height) / 100
    return None


def quantity(value: Value, env: Environment) -> Quantity | None:
    """A number, a length or a math function as a quantity; ``None`` when invalid."""
    if isinstance(value, Block):
        if value.name is None or value.name.lower() not in _MATH:
            return None
        result = _function(value.name.lower(), value.items, env)
    elif value.kind == "number":
        result = (value.number, False)
    elif value.kind == "dimension":
        scale = unit_px(value.unit, env)
        result = None if scale is None else (value.number * scale, True)
    else:
        return None
    if result is None or not math.isfinite(result[0]):
        return None
    return result


def _function(name: str, items: list[Value], env: Environment) -> Quantity | None:
    args = _split_args(items)
    if name == "calc":
        return _sum(args[0], env) if len(args) == 1 else None
    strategy = "nearest"
    if name == "round" and len(args) > 1 and len(args[0]) == 1:
        word = ident(args[0][0], *STRATEGIES)
        if word is not None:
            strategy, args = word, args[1:]
    values = [_sum(arg, env) for arg in args]
    found = [value for value in values if value is not None]
    if len(found) != len(values):
        return None
    return apply(name, found, strategy)


def _split_args(items: list[Value]) -> list[list[Value]]:
    args: list[list[Value]] = [[]]
    for item in items:
        if isinstance(item, Token) and item.kind == "comma":
            args.append([])
        else:
            args[-1].append(item)
    return [strip(arg) for arg in args]


def _sum(items: list[Value], env: Environment) -> Quantity | None:
    """``<calc-sum>``: products joined by ``+`` or ``-`` with whitespace on both sides."""
    items = strip(items)
    terms: list[list[Value]] = [[]]
    signs = [1.0]
    for i, item in enumerate(items):
        op = item.value if isinstance(item, Token) and item.kind == "delim" else ""
        if op in ("+", "-") and 0 < i < len(items) - 1:
            if not (is_ws(items[i - 1]) and is_ws(items[i + 1])):
                return None
            terms.append([])
            signs.append(1.0 if op == "+" else -1.0)
        else:
            terms[-1].append(item)
    total: Quantity | None = None
    for sign, term in zip(signs, terms, strict=True):
        value = _product(strip(term), env)
        if value is None or (total is not None and total[1] != value[1]):
            return None
        total = (sign * value[0] + (total[0] if total else 0.0), value[1])
    return total


def _product(items: list[Value], env: Environment) -> Quantity | None:
    """``<calc-product>``: values joined by ``*`` or ``/``; a divisor must be a number."""
    operands = [item for item in items if not is_ws(item)]
    if len(operands) % 2 == 0:
        return None
    result = _operand(operands[0], env)
    for op, item in zip(operands[1::2], operands[2::2], strict=True):
        right = _operand(item, env)
        symbol = op.value if isinstance(op, Token) and op.kind == "delim" else ""
        if result is None or right is None or symbol not in ("*", "/"):
            return None
        if symbol == "/":
            if right[1] or right[0] == 0:
                return None
            result = (result[0] / right[0], result[1])
        elif result[1] and right[1]:
            return None
        else:
            result = (result[0] * right[0], result[1] or right[1])
    return result


def _operand(value: Value, env: Environment) -> Quantity | None:
    if isinstance(value, Block) and value.name is None and value.opener == "(":
        return _sum(value.items, env)
    word = ident(value)
    if word is not None:
        return (CONSTANTS[word], False) if word in CONSTANTS else None
    return quantity(value, env)
