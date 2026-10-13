from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from srcset._cli import main

SRC = Path(__file__).resolve().parents[1] / "src"


def test_parse_prints_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["parse", "a.png 100w 50h, b,c.png 2x"]) == 0
    assert json.loads(capsys.readouterr().out) == [
        {"url": "a.png", "width": 100, "density": None, "height": 50},
        {"url": "b,c.png", "width": None, "density": 2.0, "height": None},
    ]


def test_select_prints_the_url(capsys: pytest.CaptureFixture[str]) -> None:
    args = ["select", "s.jpg 400w, l.jpg 1600w", "--sizes", "50vw", "--width", "800"]
    assert main(args) == 0
    assert capsys.readouterr().out == "s.jpg\n"
    assert main([*args, "--dpr", "2", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"url": "l.jpg", "density": 4.0}


def test_select_uses_height_and_src(capsys: pytest.CaptureFixture[str]) -> None:
    sizes = "(orientation: portrait) 10px, 1000px"
    args = ["select", "s.jpg 10w, l.jpg 1000w", "--sizes", sizes, "--width", "100"]
    assert main([*args, "--height", "200"]) == 0
    assert capsys.readouterr().out == "s.jpg\n"
    assert main(["select", "b.png 2x", "--src", "a.png"]) == 0
    assert capsys.readouterr().out == "a.png\n"


def test_select_without_candidates_fails(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["select", ""]) == 1
    assert "no image candidate" in capsys.readouterr().err


def test_select_rejects_a_bad_environment(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["select", "a.png", "--dpr", "0"]) == 2
    assert "density" in capsys.readouterr().err


def test_check_reports_issues_and_exit_status(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["check", "a.png 1x, b.png 2x"]) == 0
    assert capsys.readouterr().out == ""
    assert main(["check", "a.png 10w, b.png 10w", "--sizes", "100vw"]) == 1
    assert capsys.readouterr().out == "duplicate-width: 2 candidates share the width 10\n"


def test_usage_errors_exit_two(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        main([])
    assert raised.value.code == 2
    capsys.readouterr()


def test_python_dash_m_runs_the_cli() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "srcset", "select", "a.png 1x, b.png 2x", "--dpr", "2"],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(SRC), "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert (result.returncode, result.stdout) == (0, "b.png\n"), result.stderr
