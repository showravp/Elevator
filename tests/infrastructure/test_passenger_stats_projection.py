from domain.events import PassengerDroppedOff, PassengerPickedUp, RequestSubmitted
from domain.value_objects import ElevatorId, Floor, PassengerId, Tick
from infrastructure.in_memory_event_bus import InMemoryEventBus
from infrastructure.passenger_stats_projection import PassengerStatsProjection


def test_summary_computes_wait_and_total_time_for_completed_trips_only() -> None:
    bus = InMemoryEventBus()
    projection = PassengerStatsProjection(bus)

    # p1: submitted@0, picked up@2 (wait=2), dropped off@8 (travel=6, total=8)
    bus.publish(
        RequestSubmitted(
            passenger_id=PassengerId("p1"), source=Floor(1), destination=Floor(9), tick=Tick(0)
        )
    )
    bus.publish(
        PassengerPickedUp(
            elevator_id=ElevatorId(0), passenger_id=PassengerId("p1"), floor=Floor(1), tick=Tick(2)
        )
    )
    bus.publish(
        PassengerDroppedOff(
            elevator_id=ElevatorId(0), passenger_id=PassengerId("p1"), floor=Floor(9), tick=Tick(8)
        )
    )

    # p2: submitted@3, still waiting to be picked up (still in progress)
    bus.publish(
        RequestSubmitted(
            passenger_id=PassengerId("p2"), source=Floor(0), destination=Floor(5), tick=Tick(3)
        )
    )

    summary = projection.get_summary()

    assert summary.completed_count == 1
    assert summary.still_in_progress_count == 1
    assert summary.min_wait_time == 2
    assert summary.max_wait_time == 2
    assert summary.avg_wait_time == 2.0
    assert summary.min_total_time == 8
    assert summary.max_total_time == 8
    assert summary.avg_total_time == 8.0


def test_summary_with_no_events_is_all_zero() -> None:
    projection = PassengerStatsProjection(InMemoryEventBus())

    summary = projection.get_summary()

    assert summary.completed_count == 0
    assert summary.still_in_progress_count == 0
    assert summary.avg_wait_time == 0.0
    assert summary.avg_total_time == 0.0
