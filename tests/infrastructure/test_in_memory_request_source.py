from application.raw_request import RawRequest
from domain.value_objects import Floor, PassengerId, Tick
from infrastructure.in_memory_request_source import InMemoryRequestSource


def _raw(passenger: str, tick: int) -> RawRequest:
    return RawRequest(
        passenger_id=PassengerId(passenger), source=Floor(0), destination=Floor(5), tick=Tick(tick)
    )


def test_pop_due_returns_only_requests_at_or_before_the_given_tick() -> None:
    source = InMemoryRequestSource([_raw("p1", 0), _raw("p2", 3), _raw("p3", 5)])

    due_at_zero = source.pop_due(Tick(0))

    assert [r.passenger_id.value for r in due_at_zero] == ["p1"]


def test_pop_due_does_not_return_the_same_request_twice() -> None:
    source = InMemoryRequestSource([_raw("p1", 0)])
    source.pop_due(Tick(0))

    assert source.pop_due(Tick(5)) == []


def test_has_more_reflects_remaining_requests() -> None:
    source = InMemoryRequestSource([_raw("p1", 0)])
    assert source.has_more() is True

    source.pop_due(Tick(0))

    assert source.has_more() is False
