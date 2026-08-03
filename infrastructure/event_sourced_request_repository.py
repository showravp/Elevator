from application.exceptions import AggregateNotFoundError
from application.ports import EventStore
from application.repositories import RequestRepository
from domain.aggregates import Request
from domain.value_objects import PassengerId


class EventSourcedRequestRepository(RequestRepository):
    def __init__(self, event_store: EventStore) -> None:
        self._event_store = event_store

    @staticmethod
    def _stream_id(passenger_id: PassengerId) -> str:
        return f"request-{passenger_id.value}"

    def get(self, passenger_id: PassengerId) -> Request:
        events = self._event_store.load_stream(self._stream_id(passenger_id))
        if not events:
            raise AggregateNotFoundError(f"request {passenger_id.value} not found")
        return Request.replay(events)

    def save(self, request: Request) -> None:
        uncommitted = request.uncommitted_events
        expected_version = request.version - len(uncommitted)
        self._event_store.append(self._stream_id(request.id), expected_version, uncommitted)
        request.clear_uncommitted_events()
