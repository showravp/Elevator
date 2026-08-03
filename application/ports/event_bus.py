from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TypeVar

from domain.events import DomainEvent

EventHandler = Callable[[DomainEvent], None]
TDomainEvent = TypeVar("TDomainEvent", bound=DomainEvent)


class IEventBus(ABC):
    @abstractmethod
    def subscribe(
        self, event_type: type[TDomainEvent], handler: Callable[[TDomainEvent], None]
    ) -> None:
        """Generic per-call so a handler typed for a specific event subtype (e.g.
        Callable[[RequestSubmitted], None]) can be registered without widening it to
        Callable[[DomainEvent], None] — narrowing the parameter type that way would be
        type-unsound (the handler could then be invoked with an event it doesn't handle)."""

    @abstractmethod
    def publish(self, event: DomainEvent) -> None: ...
