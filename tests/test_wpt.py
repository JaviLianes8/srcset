"""The web-platform-tests srcset and sizes cases, resolved like a browser.

Files (URL, commit, size and sha256 in tests/upstream/MANIFEST.json), all from
`html/semantics/embedded-content/the-img-element/`: `srcset/parse-a-srcset-attribute.html`,
`srcset/select-an-image-source.html` and `sizes/support/sizes-iframed.sub.html`. They are
not committed; these tests skip until `python scripts/fetch_upstream.py` has fetched them.

The srcset pages give, per `<img>`, the URL a browser shows as `currentSrc` (empty when no
candidate survives). The sizes page groups `<img>` elements in paragraphs: each must pick
the same image as the first one of its paragraph, inside a 1000 by 1000 px frame.
"""

from __future__ import annotations

import re

import pytest
from conftest import img_tags, read_upstream

from srcset import Environment, select

FRAME = Environment(width=1000, height=1000)


def _chosen(tag: dict[str, str]) -> str:
    found = select(tag["srcset"], FRAME, sizes=tag.get("sizes", ""))
    return "" if found is None else found.url


@pytest.mark.parametrize(
    "name", ["wpt-parse-a-srcset-attribute.html", "wpt-select-an-image-source.html"]
)
def test_every_srcset_case_picks_the_browser_image(name: str) -> None:
    tags = img_tags(read_upstream(name))
    assert len(tags) > 10
    wrong = [(tag["srcset"], tag["data-expect"], _chosen(tag)) for tag in tags]
    wrong = [case for case in wrong if case[1] != case[2]]
    assert wrong == []


def test_the_srcset_corpus_covers_both_outcomes() -> None:
    tags = img_tags(read_upstream("wpt-parse-a-srcset-attribute.html"))
    assert len(tags) == 236
    assert any(tag["data-expect"] == "" for tag in tags)
    assert any("data-resolve" in tag for tag in tags)
    assert sum(tag["data-expect"] != "" for tag in tags) > 40


def _paragraphs() -> list[list[dict[str, str]]]:
    text = read_upstream("wpt-sizes-iframed.sub.html")
    # The page opens with a comment that mentions a paragraph tag.
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    return [img_tags(chunk) for chunk in text.split("<p>")[1:]]


def _image(tag: dict[str, str]) -> str:
    return _chosen(tag).split("?")[0]


def test_every_sizes_case_matches_its_reference() -> None:
    paragraphs = _paragraphs()
    assert len(paragraphs) == 6
    wrong = []
    for tags in paragraphs:
        reference = _image(tags[0])
        wrong += [tag["sizes"] for tag in tags[1:] if _image(tag) != reference]
    assert wrong == []


def test_the_sizes_references_pick_different_images() -> None:
    # The 1px paragraph must load the small image and the 100vw ones the large image,
    # or the comparisons above would pass for a parser that ignores sizes.
    references = [_image(tags[0]) for tags in _paragraphs()]
    assert references == ["/images/green-16x16.png"] * 4 + [
        "/images/green-1x1.png",
        "/images/green-16x16.png",
    ]
    assert sum(len(tags) - 1 for tags in _paragraphs()) == 179
