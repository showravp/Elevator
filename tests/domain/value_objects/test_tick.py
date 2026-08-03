import pytest

from domain.value_objects import Tick


def test_negative_tick_is_rejected() -> None:
    with pytest.raises(ValueError):
        Tick(-1)


def test_next_increments_by_one() -> None:
    assert Tick(0).next() == Tick(1)
    assert Tick(41).next() == Tick(42)
