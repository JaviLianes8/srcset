"""The CSS math functions applied to already evaluated arguments (CSS Values 4, 10).

A quantity is ``(value, is_length)``. Each function checks the argument types the way the
grammar does and returns ``None`` for a mismatch; a non-finite result is rejected later.
"""

from __future__ import annotations

import math
from collections.abc import Callable

Quantity = tuple[float, bool]

STRATEGIES = ("nearest", "up", "down", "to-zero")
CONSTANTS = {"e": math.e, "pi": math.pi, "infinity": math.inf, "-infinity": -math.inf}
CONSTANTS["nan"] = math.nan


def _same(args: list[Quantity]) -> bool:
    return bool(args) and len({kind for _, kind in args}) == 1


def _numbers(args: list[Quantity]) -> bool:
    return bool(args) and not any(kind for _, kind in args)


def _round(strategy: str, a: float, b: float) -> float:
    # A zero step divides by zero; apply() turns that into NaN, which is invalid.
    ratio = a / b
    if strategy == "up":
        steps = math.ceil(ratio)
    elif strategy == "down":
        steps = math.floor(ratio)
    elif strategy == "to-zero":
        steps = math.trunc(ratio)
    else:
        # Halfway values round up (towards positive infinity), as CSS specifies.
        steps = math.floor(ratio + 0.5)
    return steps * b


def _modulo(a: float, b: float, truncate: bool) -> float:
    steps = math.trunc(a / b) if truncate else math.floor(a / b)
    return a - b * steps


_UNARY_NUMBER: dict[str, Callable[[float], float]] = {"sqrt": math.sqrt, "exp": math.exp}


def apply(name: str, args: list[Quantity], strategy: str = "nearest") -> Quantity | None:
    """Result of math function ``name``, or ``None`` when the arguments do not fit."""
    values = [value for value, _ in args]
    kind = args[0][1] if args else False
    try:
        if name in ("min", "max", "hypot") and _same(args):
            if name == "hypot":
                return (math.hypot(*values), kind)
            return ((min if name == "min" else max)(values), kind)
        if name == "clamp" and len(args) == 3 and _same(args):
            return (max(values[0], min(values[1], values[2])), kind)
        if name in ("abs", "sign") and len(args) == 1:
            if name == "abs":
                return (abs(values[0]), kind)
            return (float((values[0] > 0) - (values[0] < 0)), False)
        if name == "round" and len(args) in (1, 2) and _same(args):
            if len(args) == 1 and kind:
                return None
            step = values[1] if len(args) == 2 else 1.0
            return (_round(strategy, values[0], step), kind)
        if name in ("mod", "rem") and len(args) == 2 and _same(args):
            return (_modulo(values[0], values[1], name == "rem"), kind)
        if name in _UNARY_NUMBER and len(args) == 1 and _numbers(args):
            return (_UNARY_NUMBER[name](values[0]), False)
        if name == "pow" and len(args) == 2 and _numbers(args):
            return (math.pow(values[0], values[1]), False)
        if name == "log" and len(args) in (1, 2) and _numbers(args):
            base = values[1] if len(args) == 2 else math.e
            return (math.log(values[0]) / math.log(base), False)
    except (ValueError, OverflowError, ZeroDivisionError):
        return (math.nan, kind)
    return None
