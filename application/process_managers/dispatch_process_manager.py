from application.ports import IEventBus
from domain.events import PassengerDroppedOff, RequestSubmitted
from domain.repositories import IElevatorRepository, IRequestRepository
from domain.services import ElevatorAssigned, ISchedulingPolicy, NoElevatorAvailable
from domain.value_objects import PassengerId, Tick


class DispatchProcessManager:
    """Coordinates the Elevator and Request aggregates for assignment. Neither aggregate
    alone can decide this — the choice of elevator needs a read across the whole fleet,
    and the outcome must be written to both streams. Unassignable requests (no elevator
    currently has capacity) stay pending and are retried whenever an elevator frees up a
    seat, rather than being dropped."""

    def __init__(
        self,
        elevator_repository: IElevatorRepository,
        request_repository: IRequestRepository,
        scheduling_policy: ISchedulingPolicy,
        event_bus: IEventBus,
    ) -> None:
        self._elevator_repository = elevator_repository
        self._request_repository = request_repository
        self._scheduling_policy = scheduling_policy
        self._pending_passenger_ids: list[PassengerId] = []
        event_bus.subscribe(RequestSubmitted, self._on_request_submitted)
        event_bus.subscribe(PassengerDroppedOff, self._on_capacity_possibly_freed)

    def _on_request_submitted(self, event: RequestSubmitted) -> None:
        self._pending_passenger_ids.append(event.passenger_id)
        self._try_assign_pending(event.tick)

    def _on_capacity_possibly_freed(self, event: PassengerDroppedOff) -> None:
        self._try_assign_pending(event.tick)

    def _try_assign_pending(self, tick: Tick) -> None:
        if not self._pending_passenger_ids:
            return
        elevators = [
            self._elevator_repository.get(elevator_id)
            for elevator_id in self._elevator_repository.all_ids()
        ]
        still_pending: list[PassengerId] = []
        for passenger_id in self._pending_passenger_ids:
            request = self._request_repository.get(passenger_id)
            outcome = self._scheduling_policy.select_elevator(request, elevators)
            match outcome:
                case NoElevatorAvailable():
                    still_pending.append(passenger_id)
                    continue
                case ElevatorAssigned(elevator=elevator):
                    elevator.schedule_stop(passenger_id, request.source, request.destination, tick)
                    self._elevator_repository.save(elevator)
                    request.assign(elevator.id, tick)
                    self._request_repository.save(request)
        self._pending_passenger_ids = still_pending
