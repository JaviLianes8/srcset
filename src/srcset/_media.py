"""Media conditions (Media Queries 4) with Kleene three-valued logic.

``True`` and ``False`` are the usual results and ``None`` is unknown: an unknown feature,
a value of the wrong type or ``<general-enclosed>`` syntax kept for future extensions.
A condition that does not match the grammar at all raises ``Invalid``.
"""

from __future__ import annotations

from ._css_reader import Token
from ._css_values import Block, Value, ident, is_any_value, is_ws, strip
from ._media_features import evaluate_feature
from ._model import Environment

Truth = bool | None


class Invalid(Exception):
    """The values do not form a ``<media-condition>``."""


def evaluate(values: list[Value], env: Environment, *, strict: bool = False) -> Truth:
    """Evaluate a ``<media-condition>``; raises ``Invalid`` on a grammar mismatch.

    ``strict`` also refuses ``<general-enclosed>``, which authors must not write.
    """
    items = [value for value in values if not is_ws(value)]
    if not items:
        raise Invalid
    if ident(items[0], "not") is not None:
        if len(items) != 2:
            raise Invalid
        inner = _in_parens(items[1], env, strict)
        return None if inner is None else not inner
    results = [_in_parens(items[0], env, strict)]
    joiner = ident(items[1], "and", "or") if len(items) > 1 else "and"
    if len(items) % 2 == 0 or joiner is None:
        raise Invalid
    for word, item in zip(items[1::2], items[2::2], strict=True):
        if ident(word) != joiner:
            raise Invalid
        results.append(_in_parens(item, env, strict))
    if joiner == "and":
        return False if False in results else (None if None in results else True)
    return True if True in results else (None if None in results else False)


def _in_parens(value: Value, env: Environment, strict: bool) -> Truth:
    """``<media-in-parens>``: a nested condition, a feature, or general-enclosed."""
    if not isinstance(value, Block):
        raise Invalid
    if value.name is None and value.opener == "(":
        try:
            return evaluate(value.items, env, strict=strict)
        except Invalid:
            pass
        feature = _feature(strip(value.items))
        if feature is not None:
            return evaluate_feature(*feature, env)
    general = value.name is not None or value.opener == "("
    if general and not strict and is_any_value(value.items):
        return None
    raise Invalid


Feature = tuple[str, list[tuple[str, list[Value]]]]
_FLIP = {"<": ">", "<=": ">=", ">": "<", ">=": "<=", "=": "="}


def _feature(items: list[Value]) -> Feature | None:
    """Split ``<media-feature>`` into its name and ``(operator, value)`` comparisons.

    The operator is ``:`` for the plain form; the boolean form has no comparison. Range
    forms are turned around so the name comes first: ``10px < width`` is ``width > 10px``.
    """
    split = _split_operators(items)
    if split is None:
        return None
    operands, ops = split
    names = [_name(operand) for operand in operands]
    if not ops:
        # A min- or max- prefix is only valid in the plain form.
        prefixed = names[0] is not None and names[0].startswith(("min-", "max-"))
        return None if names[0] is None or prefixed else (names[0], [])
    if ops == [":"]:
        return None if names[0] is None else (names[0], [(":", operands[1])])
    if ":" in ops or any(name and name.startswith(("min-", "max-")) for name in names):
        return None
    if len(ops) == 1:
        if names[0] is not None:
            return (names[0], [(ops[0], operands[1])])
        return None if names[1] is None else (names[1], [(_FLIP[ops[0]], operands[0])])
    if len(ops) == 2 and ops[0][0] == ops[1][0] != "=" and names[1] is not None:
        return (names[1], [(_FLIP[ops[0]], operands[0]), (ops[1], operands[2])])
    return None


def _name(operand: list[Value]) -> str | None:
    return ident(operand[0]) if len(operand) == 1 else None


def _split_operators(items: list[Value]) -> tuple[list[list[Value]], list[str]] | None:
    """Operands and the operators between them; ``None`` when an operand is empty."""
    operands: list[list[Value]] = [[]]
    ops: list[str] = []
    i = 0
    while i < len(items):
        symbol = _symbol(items[i])
        if symbol is None:
            operands[-1].append(items[i])
        else:
            # "<=" must be written without whitespace between its two characters.
            if symbol in "<>" and i + 1 < len(items) and _symbol(items[i + 1]) == "=":
                symbol += "="
                i += 1
            ops.append(symbol)
            operands.append([])
        i += 1
    operands = [strip(operand) for operand in operands]
    if not all(operands) or len(ops) > 2:
        return None
    return operands, ops


def _symbol(item: Value) -> str | None:
    if isinstance(item, Token) and item.kind == "colon":
        return ":"
    if isinstance(item, Token) and item.kind == "delim" and item.value in "<>=":
        return item.value
    return None
