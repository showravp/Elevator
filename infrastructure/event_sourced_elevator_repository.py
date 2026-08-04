from application.exceptions import AggregateNotFoundException
from application.ports import IEventStore
from domain.aggregates import Elevator
from domain.repositories import IElevatorRepository
from domain.value_objects import ElevatorId


class EventSourcedElevatorRepository(IElevatorRepository):
    def __init__(self, event_store: IEventStore) -> None:
        self._event_store = event_store
        self._known_ids: set[ElevatorId] = set()

    @staticmethod
    def _stream_id(elevator_id: ElevatorId) -> str:
        return f"elevator-{elevator_id.value}"

    def get(self, elevator_id: ElevatorId) -> Elevator:
        events = self._event_store.load_stream(self._stream_id(elevator_id))
        if not events:
            raise AggregateNotFoundException(f"elevator {elevator_id.value} not found")
        return Elevator.replay(events)

    def save(self, elevator: Elevator) -> None:
        uncommitted = elevator.uncommitted_events
        expected_version = elevator.version - len(uncommitted)
        self._event_store.append(self._stream_id(elevator.id), expected_version, uncommitted)
        elevator.clear_uncommitted_events()
        self._known_ids.add(elevator.id)

    def all_ids(self) -> list[ElevatorId]:
        return sorted(self._known_ids, key=lambda elevator_id: elevator_id.value)
