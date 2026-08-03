from application.ports import RequestSource
from application.raw_request import RawRequest
from domain.value_objects import Tick


class InMemoryRequestSource(RequestSource):
    def __init__(self, requests: list[RawRequest]) -> None:
        self._remaining = sorted(requests, key=lambda request: request.tick.value)

    def pop_due(self, tick: Tick) -> list[RawRequest]:
        due = [request for request in self._remaining if request.tick.value <= tick.value]
        self._remaining = [
            request for request in self._remaining if request.tick.value > tick.value
        ]
        return due

    def has_more(self) -> bool:
        return len(self._remaining) > 0
