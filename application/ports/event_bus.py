from abc import ABC, abstractmethod
from typing import Callable

from domain.events import DomainEvent

EventHandler = Callable[[DomainEvent], None]


class IEventBus(ABC):
    @abstractmethod
    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        ...

    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        ...
