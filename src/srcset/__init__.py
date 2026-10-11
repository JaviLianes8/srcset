"""Parse and build the HTML srcset attribute with width and pixel-density descriptors."""

from __future__ import annotations

from ._build import build
from ._model import Candidate, SrcsetError
from ._parse import parse

__version__ = "0.1.0"

__all__ = ["Candidate", "SrcsetError", "build", "parse"]
