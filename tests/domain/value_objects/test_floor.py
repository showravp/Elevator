import pytest

from domain.value_objects import Floor


def test_negative_floor_is_rejected() -> None:
    with pytest.raises(ValueError):
        Floor(-1)


def test_distance_to_is_symmetric_absolute_difference() -> None:
    assert Floor(3).distance_to(Floor(9)) == 6
    assert Floor(9).distance_to(Floor(3)) == 6
    assert Floor(4).distance_to(Floor(4)) == 0


def test_equality_and_ordering_are_by_value() -> None:
    assert Floor(5) == Floor(5)
    assert Floor(2) < Floor(7)
