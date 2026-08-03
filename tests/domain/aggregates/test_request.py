import pytest

from domain.aggregates import Request
from domain.exceptions import DuplicateAssignmentException, InvalidFloorException, SameFloorRequestException
from domain.value_objects import ElevatorId, Floor, PassengerId, Tick


def _submitted_request() -> Request:
    return Request.submit(
        passenger_id=PassengerId("p1"),
        source=Floor(1),
        destination=Floor(5),
        num_floors=10,
        tick=Tick(0),
    )


def test_submit_sets_initial_state_and_is_unassigned() -> None:
    request = _submitted_request()

    assert request.id == PassengerId("p1")
    assert request.source == Floor(1)
    assert request.destination == Floor(5)
    assert request.submitted_at == Tick(0)
    assert request.is_assigned is False
    assert request.assigned_elevator_id is None
    assert len(request.uncommitted_events) == 1


def test_submit_rejects_same_source_and_destination() -> None:
    with pytest.raises(SameFloorRequestException):
        Request.submit(PassengerId("p1"), Floor(3), Floor(3), num_floors=10, tick=Tick(0))


def test_submit_rejects_out_of_bounds_floor() -> None:
    with pytest.raises(InvalidFloorException):
        Request.submit(PassengerId("p1"), Floor(1), Floor(50), num_floors=10, tick=Tick(0))


def test_assign_sets_elevator_and_marks_assigned() -> None:
    request = _submitted_request()

    request.assign(ElevatorId(2), tick=Tick(1))

    assert request.is_assigned is True
    assert request.assigned_elevator_id == ElevatorId(2)


def test_assign_twice_raises_duplicate_assignment_error() -> None:
    request = _submitted_request()
    request.assign(ElevatorId(2), tick=Tick(1))

    with pytest.raises(DuplicateAssignmentException):
        request.assign(ElevatorId(3), tick=Tick(2))


def test_replay_reconstructs_identical_state() -> None:
    request = _submitted_request()
    request.assign(ElevatorId(2), tick=Tick(1))

    replayed = Request.replay(request.uncommitted_events)

    assert replayed.id == request.id
    assert replayed.source == request.source
    assert replayed.destination == request.destination
    assert replayed.is_assigned == request.is_assigned
    assert replayed.assigned_elevator_id == request.assigned_elevator_id
    assert replayed.version == request.version
