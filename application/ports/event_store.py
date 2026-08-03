from abc import ABC, abstractmethod
from typing import Sequence

from domain.events import DomainEvent


class IEventStore(ABC):
    @abstractmethod
    def append(
        self, stream_id: str, expected_version: int, events: Sequence[DomainEvent]
    ) -> None:
        """Append `events` to `stream_id` and stage them in the outbox, atomically.
        Raises ConcurrencyConflictException if the stream's current length != expected_version."""

    @abstractmethod
    def load_stream(self, stream_id: str) -> list[DomainEvent]:
        ...
