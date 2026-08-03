import pytest

from application.exceptions import ConcurrencyConflictError
from domain.events import RequestSubmitted
from domain.value_objects import Floor, PassengerId, Tick
from infrastructure.in_memory_event_store import InMemoryEventStore


def _event(passenger: str = "p1") -> RequestSubmitted:
    return RequestSubmitted(
        passenger_id=PassengerId(passenger), source=Floor(0), destination=Floor(3), tick=Tick(0)
    )


def test_append_then_load_stream_returns_events_in_order() -> None:
    store = InMemoryEventStore()
    first, second = _event("p1"), _event("p2")

    store.append("stream-a", expected_version=0, events=[first])
    store.append("stream-a", expected_version=1, events=[second])

    assert store.load_stream("stream-a") == [first, second]


def test_load_stream_for_unknown_stream_returns_empty_list() -> None:
    store = InMemoryEventStore()

    assert store.load_stream("nonexistent") == []


def test_append_with_wrong_expected_version_raises_concurrency_conflict() -> None:
    store = InMemoryEventStore()
    store.append("stream-a", expected_version=0, events=[_event()])

    with pytest.raises(ConcurrencyConflictError):
        store.append("stream-a", expected_version=0, events=[_event()])


def test_append_stages_events_into_outbox_atomically() -> None:
    store = InMemoryEventStore()
    event = _event()

    store.append("stream-a", expected_version=0, events=[event])

    pending = store.pending()
    assert len(pending) == 1
    assert pending[0].event == event
    assert pending[0].stream_id == "stream-a"


def test_mark_dispatched_removes_only_the_given_sequences() -> None:
    store = InMemoryEventStore()
    store.append("stream-a", expected_version=0, events=[_event("p1"), _event("p2")])
    first_sequence = store.pending()[0].sequence

    store.mark_dispatched([first_sequence])

    remaining = store.pending()
    assert len(remaining) == 1
    assert remaining[0].sequence != first_sequence
