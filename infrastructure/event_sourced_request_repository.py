from application.exceptions import AggregateNotFoundException
from application.ports import IEventStore
from domain.aggregates import Request
from domain.repositories import IRequestRepository
from domain.value_objects import PassengerId


class EventSourcedRequestRepository(IRequestRepository):
    def __init__(self, event_store: IEventStore) -> None:
        self._event_store = event_store

    @staticmethod
    def _stream_id(passenger_id: PassengerId) -> str:
        return f"request-{passenger_id.value}"

    def get(self, passenger_id: PassengerId) -> Request:
        events = self._event_store.load_stream(self._stream_id(passenger_id))
        if not events:
            raise AggregateNotFoundException(f"request {passenger_id.value} not found")
        return Request.replay(events)

    def save(self, request: Request) -> None:
        uncommitted = request.uncommitted_events
        expected_version = request.version - len(uncommitted)
        self._event_store.append(self._stream_id(request.id), expected_version, uncommitted)
        request.clear_uncommitted_events()
