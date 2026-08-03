import pytest

from domain.aggregates import Elevator
from domain.exceptions import CapacityExceededError, InvalidFloorError
from domain.value_objects import Direction, ElevatorId, Floor, PassengerId, Tick


def _provisioned_elevator(capacity: int = 4, num_floors: int = 10) -> Elevator:
    return Elevator.provision(
        elevator_id=ElevatorId(0),
        capacity=capacity,
        num_floors=num_floors,
        starting_floor=Floor(0),
        tick=Tick(0),
    )


def test_provision_sets_initial_state_and_emits_one_event() -> None:
    elevator = _provisioned_elevator()

    assert elevator.id == ElevatorId(0)
    assert elevator.current_floor == Floor(0)
    assert elevator.direction is Direction.IDLE
    assert elevator.onboard_count == 0
    assert elevator.pending_pickup_count == 0
    assert len(elevator.uncommitted_events) == 1
    assert elevator.version == 1


def test_provision_rejects_out_of_bounds_starting_floor() -> None:
    with pytest.raises(InvalidFloorError):
        Elevator.provision(
            elevator_id=ElevatorId(0),
            capacity=4,
            num_floors=10,
            starting_floor=Floor(10),
            tick=Tick(0),
        )


def test_schedule_stop_adds_pending_pickup_and_emits_event() -> None:
    elevator = _provisioned_elevator()
    elevator.clear_uncommitted_events()

    elevator.schedule_stop(PassengerId("p1"), source=Floor(3), destination=Floor(7), tick=Tick(1))

    assert elevator.pending_pickup_count == 1
    assert len(elevator.uncommitted_events) == 1


def test_schedule_stop_rejects_when_at_capacity() -> None:
    elevator = _provisioned_elevator(capacity=1)
    elevator.schedule_stop(PassengerId("p1"), Floor(2), Floor(5), Tick(1))

    with pytest.raises(CapacityExceededError):
        elevator.schedule_stop(PassengerId("p2"), Floor(3), Floor(6), Tick(1))


def test_schedule_stop_rejects_out_of_bounds_floor() -> None:
    elevator = _provisioned_elevator(num_floors=10)

    with pytest.raises(InvalidFloorError):
        elevator.schedule_stop(PassengerId("p1"), Floor(20), Floor(3), Tick(1))


def test_advance_stays_idle_when_no_targets() -> None:
    elevator = _provisioned_elevator()

    elevator.advance(Tick(1))

    assert elevator.current_floor == Floor(0)
    assert elevator.direction is Direction.IDLE


def test_advance_moves_toward_target_then_boards_then_drops_off() -> None:
    elevator = _provisioned_elevator()
    elevator.schedule_stop(PassengerId("p1"), source=Floor(2), destination=Floor(5), tick=Tick(0))

    elevator.advance(Tick(1))
    assert elevator.current_floor == Floor(1)
    assert elevator.direction is Direction.UP
    assert elevator.onboard_count == 0

    elevator.advance(Tick(2))
    assert elevator.current_floor == Floor(2)
    assert elevator.onboard_count == 1
    assert elevator.pending_pickup_count == 0

    elevator.advance(Tick(3))
    elevator.advance(Tick(4))
    elevator.advance(Tick(5))
    assert elevator.current_floor == Floor(5)
    assert elevator.onboard_count == 0


def test_replay_reconstructs_identical_state() -> None:
    elevator = _provisioned_elevator()
    elevator.schedule_stop(PassengerId("p1"), Floor(2), Floor(5), Tick(0))
    elevator.advance(Tick(1))
    elevator.advance(Tick(2))

    replayed = Elevator.replay(elevator.uncommitted_events)

    assert replayed.id == elevator.id
    assert replayed.current_floor == elevator.current_floor
    assert replayed.direction == elevator.direction
    assert replayed.onboard_count == elevator.onboard_count
    assert replayed.pending_pickup_count == elevator.pending_pickup_count
    assert replayed.version == elevator.version
    assert replayed.uncommitted_events == []


def test_clear_uncommitted_events_empties_the_list() -> None:
    elevator = _provisioned_elevator()
    assert elevator.uncommitted_events != []

    elevator.clear_uncommitted_events()

    assert elevator.uncommitted_events == []
