"""Build the wheel, install it in a throwaway venv and drive the installed package.

Slow and needs the build backend, so it runs only with SRCSET_E2E=1.
"""

from __future__ import annotations

import os
import subprocess
import sys
import venv
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    os.environ.get("SRCSET_E2E") != "1", reason="set SRCSET_E2E=1 to build and install"
)

PROGRAM = r"""
import importlib.metadata, importlib.resources, pickle
import srcset
from srcset import (
    Candidate, Environment, ImageSource, Issue, SrcsetError, build, parse, parse_sizes,
    select, source_set, validate,
)

assert "site-packages" in srcset.__file__, srcset.__file__
assert importlib.metadata.version("srcset") == srcset.__version__
assert importlib.resources.files("srcset").joinpath("py.typed").is_file()
items = parse("data:,a 1x, b.png 100w 50h, c.png 1.x, d.png -0x")
assert items == [Candidate("data:,a", density=1), Candidate("b.png", 100, height=50),
                 Candidate("d.png", density=0)], items
assert parse(build(items)) == items
assert pickle.loads(pickle.dumps(items[1])) == items[1]
try:
    build([("a b.png", "1x")])
except SrcsetError:
    pass
else:
    raise AssertionError("build accepted whitespace in a URL")
env = Environment(width=390, height=844, density=3)
sizes = "(min-width: 1024px) 33vw, calc(100vw - 2rem)"
assert parse_sizes(sizes, env) == 358.0
chosen = select("s.jpg 480w, m.jpg 960w, l.jpg 1440w", env, sizes=sizes)
assert chosen is not None and chosen.url == "l.jpg", chosen
assert source_set("a 1x, b 1x", env) == [ImageSource("a", 1.0)]
assert validate("a 1x, b 1x") == [Issue("duplicate-density", "2 candidates share the density 1")]
print("e2e ok")
"""


def _run(*cmd: str | Path, cwd: Path | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, check=False)


def test_installed_wheel_end_to_end(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    built = _run(sys.executable, "-m", "build", "--outdir", dist, ROOT)
    assert built.returncode == 0, built.stderr
    (wheel,) = dist.glob("srcset-*.whl")
    (sdist,) = dist.glob("srcset-*.tar.gz")
    names = zipfile.ZipFile(wheel).namelist()
    assert "srcset/py.typed" in names
    assert "srcset/__main__.py" in names
    assert not any(name.startswith("tests/") or name.endswith(".html") for name in names)
    entry_points = next(name for name in names if name.endswith("entry_points.txt"))
    assert "srcset = srcset._cli:main" in zipfile.ZipFile(wheel).read(entry_points).decode()
    listing = _run(sys.executable, "-m", "tarfile", "-l", sdist).stdout.decode()
    assert "IMPROVEMENTS-round" not in listing
    assert "tests/upstream/MANIFEST.json" in listing
    assert ".html" not in listing
    assert "tests/test_wpt.py" in listing
    assert "scripts/fetch_upstream.py" in listing

    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = bindir / "python"
    installed = _run(python, "-m", "pip", "install", "-q", wheel)
    assert installed.returncode == 0, installed.stderr

    # Run from an empty folder so the source tree cannot shadow the install.
    work = tmp_path / "work"
    work.mkdir()
    result = _run(python, "-I", "-c", PROGRAM, cwd=work)
    assert result.returncode == 0, result.stderr
    assert result.stdout.decode().strip() == "e2e ok"
    command = _run(bindir / "srcset", "select", "a.png 1x, b.png 2x", "--dpr", "2", cwd=work)
    assert (command.returncode, command.stdout.decode().strip()) == (0, "b.png")
    module = _run(python, "-I", "-m", "srcset", "check", "a.png 1x, b.png 1x", cwd=work)
    assert module.returncode == 1
    assert module.stdout.decode().startswith("duplicate-density")
