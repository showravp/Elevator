import pytest

from application.exceptions import AggregateNotFoundException
from domain.aggregates import Request
from domain.value_objects import ElevatorId, Floor, PassengerId, Tick
from infrastructure.event_sourced_request_repository import EventSourcedRequestRepository
from infrastructure.in_memory_event_store import InMemoryEventStore


def test_get_on_unknown_request_raises_aggregate_not_found() -> None:
    repository = EventSourcedRequestRepository(InMemoryEventStore())

    with pytest.raises(AggregateNotFoundException):
        repository.get(PassengerId("p1"))


def test_save_then_get_reconstructs_the_same_state() -> None:
    repository = EventSourcedRequestRepository(InMemoryEventStore())
    request = Request.submit(PassengerId("p1"), Floor(1), Floor(5), num_floors=10, tick=Tick(0))
    request.assign(ElevatorId(0), Tick(1))

    repository.save(request)
    reloaded = repository.get(PassengerId("p1"))

    assert reloaded.is_assigned is True
    assert reloaded.assigned_elevator_id == ElevatorId(0)
    assert reloaded.version == request.version
