from abc import ABC, abstractmethod

from application.raw_request import RawRequest
from domain.value_objects import Tick


class RequestSource(ABC):
    @abstractmethod
    def pop_due(self, tick: Tick) -> list[RawRequest]:
        """Return (and remove) all requests due at or before `tick`. Must never be called
        for a tick ahead of the simulation's current position — that would be peeking ahead."""

    @abstractmethod
    def has_more(self) -> bool:
        ...
