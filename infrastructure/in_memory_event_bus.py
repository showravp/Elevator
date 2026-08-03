from collections import defaultdict
from collections.abc import Callable
from typing import TypeVar, cast

from application.ports import EventHandler, IEventBus
from domain.events import DomainEvent

TDomainEvent = TypeVar("TDomainEvent", bound=DomainEvent)


class InMemoryEventBus(IEventBus):
    def __init__(self) -> None:
        self._handlers: dict[type, list[EventHandler]] = defaultdict(list)

    def subscribe(
        self, event_type: type[TDomainEvent], handler: Callable[[TDomainEvent], None]
    ) -> None:
        # The internal dict necessarily erases each handler's specific event subtype —
        # storing heterogeneous handlers together requires one point where the type
        # system can't verify what publish() already guarantees structurally: a handler
        # registered under `event_type` is only ever invoked with an instance of that
        # exact type (see publish() below).
        self._handlers[event_type].append(cast(EventHandler, handler))

    def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers.get(type(event), []):
            handler(event)
