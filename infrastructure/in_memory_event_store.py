from typing import Sequence

from application.exceptions import ConcurrencyConflictException
from application.outbox_entry import OutboxEntry
from application.ports import IEventStore, IOutboxStore
from domain.events import DomainEvent


class InMemoryEventStore(IEventStore, IOutboxStore):
    """Backs both IEventStore and IOutboxStore with the same underlying dict, so append()
    writes the stream and stages the outbox in a single call — atomic by construction,
    no dual-write hazard to guard against."""

    def __init__(self) -> None:
        self._streams: dict[str, list[DomainEvent]] = {}
        self._outbox: list[OutboxEntry] = []
        self._next_sequence: int = 0

    def append(
        self, stream_id: str, expected_version: int, events: Sequence[DomainEvent]
    ) -> None:
        stream = self._streams.setdefault(stream_id, [])
        if len(stream) != expected_version:
            raise ConcurrencyConflictException(
                f"stream {stream_id!r} expected version {expected_version} but was {len(stream)}"
            )
        for event in events:
            stream.append(event)
            self._outbox.append(
                OutboxEntry(sequence=self._next_sequence, stream_id=stream_id, event=event)
            )
            self._next_sequence += 1

    def load_stream(self, stream_id: str) -> list[DomainEvent]:
        return list(self._streams.get(stream_id, []))

    def pending(self) -> list[OutboxEntry]:
        return list(self._outbox)

    def mark_dispatched(self, sequences: list[int]) -> None:
        dispatched = set(sequences)
        self._outbox = [entry for entry in self._outbox if entry.sequence not in dispatched]
