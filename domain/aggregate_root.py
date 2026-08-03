from abc import ABC, abstractmethod
from typing import Self


class AggregateRoot[TEvent, TId](ABC):
    """Event-sourced aggregate root. `apply()` is the only path that may change state —
    command methods on subclasses must go through `raise_event()`, never set fields directly,
    so replayed state and freshly-mutated state are always produced the same way."""

    def __init__(self) -> None:
        self._version: int = 0
        self._uncommitted_events: list[TEvent] = []

    @property
    @abstractmethod
    def id(self) -> TId: ...

    @property
    def version(self) -> int:
        return self._version

    @property
    def uncommitted_events(self) -> list[TEvent]:
        return list(self._uncommitted_events)

    def clear_uncommitted_events(self) -> None:
        self._uncommitted_events.clear()

    def raise_event(self, event: TEvent) -> None:
        self.apply(event)
        self._uncommitted_events.append(event)
        self._version += 1

    @abstractmethod
    def apply(self, event: TEvent) -> None: ...

    @classmethod
    def replay(cls, events: list[TEvent]) -> Self:
        aggregate = cls.__new__(cls)
        aggregate._version = 0
        aggregate._uncommitted_events = []
        for event in events:
            aggregate.apply(event)
            aggregate._version += 1
        return aggregate
