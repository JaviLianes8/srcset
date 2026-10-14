"""Evaluate one media feature against an environment.

Known features: ``width``, ``height``, ``aspect-ratio``, ``orientation`` and
``resolution``, with ``min-``/``max-`` prefixes and the range syntax. Any other name, or a
value of the wrong type, is unknown, so the condition around it does not match.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from ._calc import quantity
from ._css_reader import Token
from ._css_values import Value, ident, is_ws
from ._model import Environment

_RESOLUTION = {"dppx": 1.0, "x": 1.0, "dpi": 1 / 96, "dpcm": 2.54 / 96}
_RANGE = ("width", "height", "aspect-ratio", "resolution")
_COMPARE: dict[str, Callable[[float, float], bool]] = {
    ":": lambda a, b: a == b,
    "=": lambda a, b: a == b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
}


def evaluate_feature(
    name: str, tests: list[tuple[str, list[Value]]], env: Environment
) -> bool | None:
    """Result of ``(name)``, ``(name: value)`` or a range form; ``None`` when unknown."""
    if name.startswith(("min-", "max-")):
        if len(tests) != 1 or tests[0][0] != ":" or name[4:] not in _RANGE:
            return None
        name, tests = name[4:], [(">=" if name[:3] == "min" else "<=", tests[0][1])]
    actual = _actual(name, env)
    if name == "orientation":
        if any(op != ":" for op, _ in tests):
            return None
        if not tests:
            return True if actual is not None else None
        wanted = ident(tests[0][1][0]) if len(tests[0][1]) == 1 else None
        if wanted not in ("portrait", "landscape") or actual is None:
            return None
        return (wanted == "portrait") == (actual == 1.0)
    if name not in _RANGE:
        return None
    if actual is None:
        return None
    if not tests:
        return actual != 0
    results = []
    for op, values in tests:
        expected = _value(name, values, env)
        if expected is None:
            return None
        results.append(_COMPARE[op](actual, expected))
    return all(results)


def _actual(name: str, env: Environment) -> float | None:
    height = env.height
    if name == "width":
        return env.width
    if name == "resolution":
        return env.density
    if height is None:
        return None
    if name == "height":
        return height
    if name == "orientation":
        return 1.0 if height >= env.width else 0.0
    if name == "aspect-ratio":
        return None if height == 0 else env.width / height
    return None


def _value(name: str, values: list[Value], env: Environment) -> float | None:
    values = [value for value in values if not is_ws(value)]
    if name == "aspect-ratio":
        return _ratio(values, env)
    if len(values) != 1:
        return None
    value = values[0]
    if name == "resolution":
        if isinstance(value, Token) and value.kind == "dimension":
            scale = _RESOLUTION.get(value.unit.lower())
            return None if scale is None else value.number * scale
        return math.inf if ident(value, "infinite") else None
    found = quantity(value, env)
    if found is None or (not found[1] and found[0] != 0):
        return None
    return found[0]


def _ratio(values: list[Value], env: Environment) -> float | None:
    """``<ratio>``: a non-negative number, optionally ``/`` another one."""
    parts = [values] if len(values) == 1 else [values[:1], values[2:]]
    if len(values) not in (1, 3):
        return None
    if len(values) == 3:
        slash = values[1]
        if not (isinstance(slash, Token) and slash.kind == "delim" and slash.value == "/"):
            return None
    numbers = []
    for part in parts:
        found = quantity(part[0], env) if len(part) == 1 else None
        if found is None or found[1] or found[0] < 0:
            return None
        numbers.append(found[0])
    if len(numbers) == 1:
        return numbers[0]
    return None if numbers[1] == 0 else numbers[0] / numbers[1]
