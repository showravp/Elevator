from application.process_managers import DispatchProcessManager
from domain.aggregates import Elevator, Request
from domain.events import RequestSubmitted
from domain.services.strategies import NearestCarSchedulingPolicy
from domain.value_objects import ElevatorId, Floor, PassengerId, Tick
from infrastructure.event_sourced_elevator_repository import EventSourcedElevatorRepository
from infrastructure.event_sourced_request_repository import EventSourcedRequestRepository
from infrastructure.in_memory_event_bus import InMemoryEventBus
from infrastructure.in_memory_event_store import InMemoryEventStore


def _build(
    capacity: int = 4,
) -> tuple[InMemoryEventBus, EventSourcedElevatorRepository, EventSourcedRequestRepository]:
    store = InMemoryEventStore()
    bus = InMemoryEventBus()
    elevator_repository = EventSourcedElevatorRepository(store)
    request_repository = EventSourcedRequestRepository(store)
    DispatchProcessManager(
        elevator_repository, request_repository, NearestCarSchedulingPolicy(), bus
    )
    elevator = Elevator.provision(
        ElevatorId(0), capacity=capacity, num_floors=10, starting_floor=Floor(0), tick=Tick(0)
    )
    elevator_repository.save(elevator)
    return bus, elevator_repository, request_repository


def _submitted_event(request: Request) -> RequestSubmitted:
    return RequestSubmitted(
        passenger_id=request.id,
        source=request.source,
        destination=request.destination,
        tick=request.submitted_at,
    )


def test_request_submitted_with_available_elevator_is_assigned_immediately() -> None:
    bus, elevator_repository, request_repository = _build()
    request = Request.submit(PassengerId("p1"), Floor(2), Floor(6), num_floors=10, tick=Tick(0))
    request_repository.save(request)

    bus.publish(_submitted_event(request))

    reloaded = request_repository.get(PassengerId("p1"))
    assert reloaded.is_assigned is True
    assert reloaded.assigned_elevator_id == ElevatorId(0)
    assert elevator_repository.get(ElevatorId(0)).pending_pickup_count == 1


def test_request_submitted_with_no_capacity_stays_pending() -> None:
    bus, elevator_repository, request_repository = _build(capacity=1)
    blocker = elevator_repository.get(ElevatorId(0))
    blocker.schedule_stop(PassengerId("other"), Floor(0), Floor(9), Tick(0))
    elevator_repository.save(blocker)

    request = Request.submit(PassengerId("p1"), Floor(2), Floor(6), num_floors=10, tick=Tick(0))
    request_repository.save(request)
    bus.publish(_submitted_event(request))

    assert request_repository.get(PassengerId("p1")).is_assigned is False
