from application.outbox_relay import OutboxRelay
from domain.events import RequestSubmitted
from domain.value_objects import Floor, PassengerId, Tick
from infrastructure.in_memory_event_bus import InMemoryEventBus
from infrastructure.in_memory_event_store import InMemoryEventStore


def _event(passenger: str) -> RequestSubmitted:
    return RequestSubmitted(
        passenger_id=PassengerId(passenger), source=Floor(0), destination=Floor(3), tick=Tick(0)
    )


def test_drain_publishes_every_pending_event_and_marks_it_dispatched() -> None:
    store = InMemoryEventStore()
    bus = InMemoryEventBus()
    received: list[RequestSubmitted] = []
    bus.subscribe(RequestSubmitted, received.append)
    store.append("stream-a", 0, [_event("p1"), _event("p2")])

    OutboxRelay(store, bus).drain()

    assert received == store.load_stream("stream-a")
    assert store.pending() == []


def test_drain_with_nothing_pending_does_nothing() -> None:
    store = InMemoryEventStore()
    bus = InMemoryEventBus()

    OutboxRelay(store, bus).drain()

    assert store.pending() == []


def test_events_appended_by_a_handler_during_drain_are_not_lost_but_deferred() -> None:
    # A handler reacting to a published event may itself append new events (e.g. the
    # dispatch process manager reacting to RequestSubmitted). Draining a fixed snapshot
    # rather than recursing avoids unbounded recursion; the new events simply wait for
    # the next drain() call instead of being dropped.
    store = InMemoryEventStore()
    bus = InMemoryEventBus()

    def on_first_event(event: RequestSubmitted) -> None:
        store.append("stream-b", 0, [_event("triggered")])

    bus.subscribe(RequestSubmitted, on_first_event)
    store.append("stream-a", 0, [_event("p1")])

    OutboxRelay(store, bus).drain()

    assert len(store.pending()) == 1
    assert store.pending()[0].stream_id == "stream-b"
