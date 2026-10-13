"""The README examples run and print what they say; docs, versions and files agree."""

from __future__ import annotations

import contextlib
import io
import itertools
import re
import shlex
from pathlib import Path

import srcset
from srcset._cli import main

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")


def _python_blocks() -> list[str]:
    return re.findall(r"```python\n(.*?)```", README, flags=re.DOTALL)


def _expected_output(block: str) -> list[str]:
    """Each print is followed by comment lines that hold what it prints."""
    expected: list[str] = []
    for line, following in itertools.pairwise(["", *block.splitlines()]):
        if following.startswith("# ") and (line.startswith(("print(", "    print(", "# "))):
            expected.append(following[2:])
    return expected


def test_every_readme_example_runs_and_prints_its_comments() -> None:
    blocks = _python_blocks()
    assert len(blocks) == 3
    checked = 0
    for block in blocks:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exec(compile(block, "README.md", "exec"), {"__name__": "readme"})
        assert out.getvalue().splitlines() == _expected_output(block)
        checked += len(_expected_output(block))
    assert checked == 9


def test_every_command_line_example_prints_what_it_shows() -> None:
    block = README.split("## Command line", 1)[1].split("```", 2)[1]
    commands = re.findall(r"^\$ srcset (.*)\n((?:[^$\n].*\n)*)", block, flags=re.MULTILINE)
    assert len(commands) == 3
    for command, shown in commands:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            main(shlex.split(command))
        assert out.getvalue() == shown, command


def test_the_api_table_lists_every_public_name() -> None:
    table = README.split("## API", 1)[1].split("\n## ", 1)[0]
    for name in srcset.__all__:
        assert f"`{name}" in table, name


def test_every_issue_code_is_documented() -> None:
    codes = set(re.findall(r'Issue\(\s*f?"([a-z-]+)', _source("_validate.py")))
    codes.discard("duplicate-")
    codes |= {"duplicate-width", "duplicate-density"}
    section = README.split("**Issue codes.**", 1)[1].split("\n## ", 1)[0]
    assert codes == set(re.findall(r"`([a-z-]+)`", section))


def _source(name: str) -> str:
    return (ROOT / "src" / "srcset" / name).read_text(encoding="utf-8")


def test_version_matches_pyproject_and_changelog() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', text, flags=re.MULTILINE)
    assert match is not None and match.group(1) == srcset.__version__
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{srcset.__version__}]" in changelog


def test_no_em_dash_anywhere_in_the_tree() -> None:
    suffixes = {".py", ".md", ".toml", ".ps1", ".txt", ".json", ".yml"}
    for path in ROOT.rglob("*"):
        parts = path.relative_to(ROOT).parts
        if not path.is_file() or path.suffix not in suffixes:
            continue
        if parts[:2] == ("tests", "upstream") and path.name != "MANIFEST.json":
            continue
        if any(part.startswith(".") or part in ("__pycache__", "build", "dist") for part in parts):
            continue
        assert chr(0x2014) not in path.read_text(encoding="utf-8"), path


def test_source_files_stay_under_two_hundred_lines() -> None:
    for path in [*(ROOT / "src").rglob("*.py"), *(ROOT / "tests").glob("*.py")]:
        assert path.read_text(encoding="utf-8").count("\n") <= 200, path
