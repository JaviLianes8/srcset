from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

import pytest

UPSTREAM = Path(__file__).resolve().parent / "upstream"


def read_upstream(name: str) -> str:
    """Return a third-party test file, checked against its manifest entry.

    The files are not committed: `python scripts/fetch_upstream.py` fetches them. Their
    tests skip while a file is absent and fail if it differs from the manifest.
    """
    path = UPSTREAM / name
    if not path.is_file():
        pytest.skip(f"{name} is not fetched; run python scripts/fetch_upstream.py")
    entry = json.loads((UPSTREAM / "MANIFEST.json").read_text(encoding="utf-8"))[name]
    body = path.read_bytes()
    assert hashlib.sha256(body).hexdigest() == entry["sha256"], f"{name} differs from MANIFEST"
    return body.decode("utf-8")


def _reference(match: re.Match[str]) -> str:
    # Numeric references keep control characters, as the HTML tokenizer does; the html
    # module would drop some of them.
    text = match.group(0)
    if text.startswith("&#"):
        digits = match.group(1)
        return chr(int(digits[1:], 16) if digits[:1] in "xX" else int(digits))
    return html.unescape(text)


def decode_attribute(raw: str) -> str:
    return re.sub(r"&#([xX][0-9a-fA-F]+|[0-9]+);|&[a-zA-Z]+;", _reference, raw)


def img_tags(text: str) -> list[dict[str, str]]:
    """Attributes of every `<img>` in a test page; all values there are single-quoted."""
    tags = []
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    for body in re.findall(r"<img\b([^>]*)>", text):
        attributes = dict(re.findall(r"([\w-]+)='([^']*)'", body))
        bare = re.findall(r"\s([\w-]+)(?=\s|$)", re.sub(r"='[^']*'", "=", body))
        tags.append({**{name: "" for name in bare}, **attributes})
    return [{k: decode_attribute(v) for k, v in tag.items()} for tag in tags]
