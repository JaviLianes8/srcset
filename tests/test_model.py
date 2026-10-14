from __future__ import annotations

import math
import pickle

import pytest

from srcset import Candidate, Environment, ImageSource, Issue, SrcsetError


def test_descriptor_property() -> None:
    assert Candidate("a").descriptor == ""
    assert Candidate("a", 320).descriptor == "320w"
    assert Candidate("a", 320, height=10).descriptor == "320w 10h"
    assert Candidate("a", density=2).descriptor == "2x"
    assert Candidate("a", density=0.1).descriptor == "0.1x"
    assert Candidate("a", density=1e-7).descriptor == "1e-07x"


def test_density_is_stored_as_float_without_negative_zero() -> None:
    candidate = Candidate("a", density=-0.0)
    assert isinstance(candidate.density, float)
    assert math.copysign(1.0, candidate.density) == 1.0
    assert Candidate("a", density=2) == Candidate("a", density=2.0)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"width": 0},
        {"width": -5},
        {"height": 3},
        {"width": 3, "height": 0},
        {"density": -1.0},
        {"density": math.inf},
        {"density": math.nan},
        {"width": 3, "density": 1.0},
    ],
)
def test_candidate_rejects_impossible_descriptors(kwargs: dict[str, float]) -> None:
    with pytest.raises(SrcsetError):
        Candidate("a", **kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "kwargs", [{"width": 1.5}, {"width": True}, {"height": "2"}, {"density": "2"}, {"url": 3}]
)
def test_candidate_rejects_wrong_types(kwargs: dict[str, object]) -> None:
    arguments: dict[str, object] = {"url": "a", **kwargs}
    with pytest.raises(TypeError):
        Candidate(**arguments)  # type: ignore[arg-type]


def test_values_are_frozen_hashable_and_picklable() -> None:
    candidate = Candidate("a", 10, height=5)
    env = Environment(800, 600, 2)
    with pytest.raises(AttributeError):
        candidate.url = "b"  # type: ignore[misc]
    assert {candidate, Candidate("a", 10, height=5)} == {candidate}
    assert pickle.loads(pickle.dumps(candidate)) == candidate
    assert pickle.loads(pickle.dumps(env)) == env
    assert ImageSource("a", 1.0) == ("a", 1.0)
    assert Issue("empty", "m").code == "empty"


def test_environment_coerces_numbers() -> None:
    env = Environment(800, 600, 2, 20)
    assert (env.width, env.height, env.density, env.font_size) == (800.0, 600.0, 2.0, 20.0)
    assert all(isinstance(v, float) for v in (env.width, env.height, env.density))
    assert Environment(0).height is None


@pytest.mark.parametrize(
    "args",
    [(-1,), (1, -1), (1, None, 0), (1, None, -2), (1, None, 1, 0), (math.inf,), (1, math.nan)],
)
def test_environment_rejects_out_of_range_values(args: tuple[float, ...]) -> None:
    with pytest.raises(SrcsetError):
        Environment(*args)


def test_environment_rejects_wrong_types() -> None:
    with pytest.raises(TypeError):
        Environment("800")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        Environment(800, density=True)


def test_srcset_error_is_a_value_error() -> None:
    assert issubclass(SrcsetError, ValueError)
