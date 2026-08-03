import pytest

from domain.value_objects import ElevatorId, PassengerId


def test_negative_elevator_id_is_rejected() -> None:
    with pytest.raises(ValueError):
        ElevatorId(-1)


def test_empty_passenger_id_is_rejected() -> None:
    with pytest.raises(ValueError):
        PassengerId("")
