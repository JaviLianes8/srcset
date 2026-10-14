"""Source sets and selection. Hand-written from HTML 4.8.4.3.7, 4.8.4.3.8 and 4.8.4.3.12."""

from __future__ import annotations

import math

import pytest

from srcset import Environment, ImageSource, select, source_set

PHONE = Environment(width=400, height=800, density=3)
DESKTOP = Environment(width=1600, height=900)
WIDTHS = "s.jpg 400w, m.jpg 800w, l.jpg 1600w"


def test_width_candidates_become_densities() -> None:
    assert source_set(WIDTHS, DESKTOP, sizes="50vw") == [
        ImageSource("s.jpg", 0.5),
        ImageSource("m.jpg", 1.0),
        ImageSource("l.jpg", 2.0),
    ]


def test_select_takes_the_smallest_density_that_covers_the_screen() -> None:
    assert select(WIDTHS, DESKTOP, sizes="50vw") == ImageSource("m.jpg", 1.0)
    assert select(WIDTHS, DESKTOP) == ImageSource("l.jpg", 1.0)
    assert select("a.png 1x, b.png 2x, c.png 3x", PHONE) == ImageSource("c.png", 3.0)
    assert select("a.png 1x, b.png 2x", Environment(400, density=1.5)) == ("b.png", 2.0)


def test_select_falls_back_to_the_densest_image() -> None:
    assert select(WIDTHS, PHONE, sizes="100vw") == ImageSource("l.jpg", 4.0)
    assert select("a.png 0.5x, b.png 2x", PHONE) == ImageSource("b.png", 2.0)


def test_sizes_media_conditions_steer_the_choice() -> None:
    sizes = "(max-width: 600px) 100vw, 33vw"
    assert select(WIDTHS, PHONE, sizes=sizes) == ImageSource("l.jpg", 4.0)
    assert select(WIDTHS, DESKTOP, sizes=sizes).url == "m.jpg"  # type: ignore[union-attr]


def test_later_duplicates_are_dropped() -> None:
    assert source_set("a.png, b.png 1x, c.png 2x, d.png 2.0x", DESKTOP) == [
        ImageSource("a.png", 1.0),
        ImageSource("c.png", 2.0),
    ]


def test_src_is_the_one_x_fallback() -> None:
    assert source_set("b.png 2x", DESKTOP, src="a.png") == [
        ImageSource("b.png", 2.0),
        ImageSource("a.png", 1.0),
    ]
    assert source_set("b.png 1x", DESKTOP, src="a.png") == [ImageSource("b.png", 1.0)]
    assert source_set("b.png 100w", DESKTOP, src="a.png") == [ImageSource("b.png", 100 / 1600)]
    assert source_set("b.png", DESKTOP, src="a.png") == [ImageSource("b.png", 1.0)]
    assert select("", DESKTOP, src="a.png") == ImageSource("a.png", 1.0)


def test_zero_size_gives_infinite_density() -> None:
    assert source_set("a 10w, b 20w", DESKTOP, sizes="0px") == [ImageSource("a", math.inf)]


def test_nothing_to_choose() -> None:
    assert select("", DESKTOP) is None
    assert select("a.png 2y", DESKTOP) is None
    assert source_set(", ,", DESKTOP) == []


def test_auto_sizes() -> None:
    assert select(WIDTHS, DESKTOP, sizes="auto, 25vw", auto_width=800) == ("m.jpg", 1.0)
    assert select(WIDTHS, DESKTOP, sizes="auto, 25vw") == ImageSource("s.jpg", 1.0)


def test_bad_arguments() -> None:
    with pytest.raises(TypeError):
        select(WIDTHS, DESKTOP, src=None)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        select(WIDTHS, None)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        source_set(None, DESKTOP)  # type: ignore[arg-type]
