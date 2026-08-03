from dataclasses import dataclass

from domain.events import DomainEvent


@dataclass(frozen=True, slots=True)
class OutboxEntry:
    sequence: int
    stream_id: str
    event: DomainEvent
