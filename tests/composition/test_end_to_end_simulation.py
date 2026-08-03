from application.raw_request import RawRequest
from composition.container import build_application
from domain.value_objects import ElevatorId, Floor, PassengerId, Tick


def _raw(passenger: str, source: int, destination: int, tick: int) -> RawRequest:
    return RawRequest(
        passenger_id=PassengerId(passenger),
        source=Floor(source),
        destination=Floor(destination),
        tick=Tick(tick),
    )


def test_simulation_serves_every_passenger_and_computes_sane_stats() -> None:
    requests = [
        _raw("p1", source=0, destination=5, tick=0),
        _raw("p2", source=3, destination=9, tick=0),
        _raw("p3", source=8, destination=1, tick=4),
    ]

    app = build_application(
        requests=requests, num_elevators=2, num_floors=10, elevator_capacity=4
    )
    app.orchestrator().run()

    summary = app.passenger_stats_projection().summary()
    assert summary.completed_count == 3
    assert summary.still_in_progress_count == 0
    assert summary.min_wait_time >= 0
    assert summary.min_total_time >= 1  # travel is never instantaneous when source != dest


def test_position_log_has_a_row_for_every_elevator_at_every_tick_up_to_completion() -> None:
    requests = [_raw("p1", source=0, destination=9, tick=0)]

    app = build_application(
        requests=requests, num_elevators=2, num_floors=10, elevator_capacity=4
    )
    app.orchestrator().run()

    rows = app.position_log_projection().rows
    last_tick = max(row.tick.value for row in rows)
    for tick_value in range(last_tick + 1):
        for elevator_id in (ElevatorId(0), ElevatorId(1)):
            matching = [
                row for row in rows if row.tick.value == tick_value and row.elevator_id == elevator_id
            ]
            assert len(matching) == 1, f"missing/duplicate row for elevator {elevator_id} at tick {tick_value}"


def test_requests_exceeding_a_single_elevators_capacity_are_all_eventually_served() -> None:
    # One elevator, capacity 1: five simultaneous requests force serialization through
    # dispatch's pending-retry path (objective #1 — no request may be dropped).
    requests = [_raw(f"p{i}", source=0, destination=9, tick=0) for i in range(5)]

    app = build_application(
        requests=requests, num_elevators=1, num_floors=10, elevator_capacity=1
    )
    app.orchestrator().run()

    summary = app.passenger_stats_projection().summary()
    assert summary.completed_count == 5
    assert summary.still_in_progress_count == 0


def test_no_requests_still_records_tick_zero_for_every_idle_elevator() -> None:
    app = build_application(requests=[], num_elevators=2, num_floors=10, elevator_capacity=4)

    app.orchestrator().run()

    rows = app.position_log_projection().rows
    assert len(rows) == 2  # one tick-0 row per elevator, both idle at the starting floor
    assert all(row.tick == Tick(0) for row in rows)
