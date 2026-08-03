from abc import ABC, abstractmethod

from application.outbox_entry import OutboxEntry


class IOutboxStore(ABC):
    @abstractmethod
    def pending(self) -> list[OutboxEntry]:
        ...

    @abstractmethod
    def mark_dispatched(self, sequences: list[int]) -> None:
        ...
