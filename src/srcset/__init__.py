"""Parse, build, check and resolve the HTML srcset and sizes attributes like a browser."""

from __future__ import annotations

from ._build import build
from ._model import Candidate, Environment, ImageSource, Issue, SrcsetError
from ._parse import parse
from ._select import select, source_set
from ._sizes import parse_sizes
from ._validate import validate

__version__ = "0.2.0"

__all__ = [
    "Candidate",
    "Environment",
    "ImageSource",
    "Issue",
    "SrcsetError",
    "build",
    "parse",
    "parse_sizes",
    "select",
    "source_set",
    "validate",
]
