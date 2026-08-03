from domain.events import PassengerPickedUp, RequestSubmitted
from domain.value_objects import Floor, PassengerId, Tick
from infrastructure.in_memory_event_bus import InMemoryEventBus


def test_publish_only_invokes_handlers_subscribed_to_that_event_type() -> None:
    bus = InMemoryEventBus()
    received: list[object] = []
    bus.subscribe(RequestSubmitted, received.append)
    bus.subscribe(PassengerPickedUp, received.append)

    event = RequestSubmitted(
        passenger_id=PassengerId("p1"), source=Floor(0), destination=Floor(3), tick=Tick(0)
    )
    bus.publish(event)

    assert received == [event]


def test_publish_with_no_subscribers_does_not_raise() -> None:
    bus = InMemoryEventBus()

    bus.publish(
        RequestSubmitted(
            passenger_id=PassengerId("p1"), source=Floor(0), destination=Floor(3), tick=Tick(0)
        )
    )


def test_multiple_handlers_for_the_same_event_type_all_fire() -> None:
    bus = InMemoryEventBus()
    calls: list[str] = []
    bus.subscribe(RequestSubmitted, lambda event: calls.append("a"))
    bus.subscribe(RequestSubmitted, lambda event: calls.append("b"))

    bus.publish(
        RequestSubmitted(
            passenger_id=PassengerId("p1"), source=Floor(0), destination=Floor(3), tick=Tick(0)
        )
    )

    assert calls == ["a", "b"]
