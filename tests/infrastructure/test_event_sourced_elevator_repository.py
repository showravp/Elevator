import pytest

from application.exceptions import AggregateNotFoundError
from domain.aggregates import Elevator
from domain.value_objects import ElevatorId, Floor, PassengerId, Tick
from infrastructure.event_sourced_elevator_repository import EventSourcedElevatorRepository
from infrastructure.in_memory_event_store import InMemoryEventStore


def test_get_on_unknown_elevator_raises_aggregate_not_found() -> None:
    repository = EventSourcedElevatorRepository(InMemoryEventStore())

    with pytest.raises(AggregateNotFoundError):
        repository.get(ElevatorId(0))


def test_save_then_get_reconstructs_the_same_state() -> None:
    repository = EventSourcedElevatorRepository(InMemoryEventStore())
    elevator = Elevator.provision(ElevatorId(0), capacity=4, num_floors=10, starting_floor=Floor(0), tick=Tick(0))
    elevator.schedule_stop(PassengerId("p1"), Floor(2), Floor(5), Tick(0))

    repository.save(elevator)
    reloaded = repository.get(ElevatorId(0))

    assert reloaded.id == elevator.id
    assert reloaded.pending_pickup_count == 1
    assert reloaded.version == elevator.version


def test_save_clears_uncommitted_events() -> None:
    repository = EventSourcedElevatorRepository(InMemoryEventStore())
    elevator = Elevator.provision(ElevatorId(0), capacity=4, num_floors=10, starting_floor=Floor(0), tick=Tick(0))

    repository.save(elevator)

    assert elevator.uncommitted_events == []


def test_incremental_saves_accumulate_in_the_stream() -> None:
    store = InMemoryEventStore()
    repository = EventSourcedElevatorRepository(store)
    elevator = Elevator.provision(ElevatorId(0), capacity=4, num_floors=10, starting_floor=Floor(0), tick=Tick(0))
    repository.save(elevator)

    elevator.advance(Tick(1))
    repository.save(elevator)

    reloaded = repository.get(ElevatorId(0))
    assert reloaded.version == elevator.version


def test_all_ids_returns_every_saved_elevator() -> None:
    repository = EventSourcedElevatorRepository(InMemoryEventStore())
    for index in range(3):
        elevator = Elevator.provision(
            ElevatorId(index), capacity=4, num_floors=10, starting_floor=Floor(0), tick=Tick(0)
        )
        repository.save(elevator)

    assert repository.all_ids() == [ElevatorId(0), ElevatorId(1), ElevatorId(2)]
