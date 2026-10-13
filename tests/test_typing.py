"""The public API is typed: mypy infers the documented types and rejects wrong ones."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"

SNIPPET = """
from srcset import Environment, build, parse, parse_sizes, select, source_set, validate
env = Environment(800)
reveal_type(parse("a 1x"))
reveal_type(parse("a 1x")[0].density)
reveal_type(parse("a 1x")[0].width)
reveal_type(build([("a", "1x")]))
reveal_type(parse_sizes("1px", env))
reveal_type(select("a 1x", env))
reveal_type(source_set("a 1x", env)[0].density)
reveal_type(validate("a 1x")[0].code)
parse(b"a")
build([("a", 2)])
select("a", env, "1px")
Environment("800")
"""


@pytest.fixture(scope="module")
def mypy_output(tmp_path_factory: pytest.TempPathFactory) -> str:
    folder = tmp_path_factory.mktemp("typing")
    target = folder / "snippet.py"
    target.write_text(SNIPPET, encoding="utf-8")
    config = folder / "mypy.ini"
    config.write_text(f"[mypy]\nmypy_path = {SRC.as_posix()}\n", encoding="utf-8")
    cache = str(folder / "cache")
    args = ["--strict", "--config-file", str(config), "--cache-dir", cache, str(target)]
    try:
        from mypy import api
    except ImportError:
        # The interpreter running pytest may lack mypy while the one on PATH has it.
        program = shutil.which("mypy")
        if program is None:
            pytest.skip("mypy is not installed")
        result = subprocess.run([program, *args], capture_output=True, text=True, check=False)
        return result.stdout + result.stderr
    out, err, _ = api.run(args)
    return str(out) + str(err)


def test_functions_return_the_documented_types(mypy_output: str) -> None:
    revealed = [_revealed(mypy_output, line) for line in range(4, 12)]
    # mypy spells a named tuple as its fields plus a fallback, which varies by release.
    chosen = revealed.pop(5)
    assert "ImageSource" in chosen and chosen.endswith("| None"), chosen
    assert revealed == [
        "list[srcset._model.Candidate]",
        "float | None",
        "int | None",
        "str",
        "float",
        "float",
        "str",
    ]


def test_misuse_is_rejected(mypy_output: str) -> None:
    for line, code in ((12, "arg-type"), (13, "list-item"), (14, "call-arg"), (15, "arg-type")):
        assert re.search(rf"snippet\.py:{line}: error: .*\[{code}\]", mypy_output), mypy_output


def _revealed(output: str, line: int) -> str:
    match = re.search(rf"snippet\.py:{line}: note: Revealed type is \"(.+)\"", output)
    assert match, output
    # Older mypy releases spell builtins with their module prefix.
    return match.group(1).replace("builtins.", "")
