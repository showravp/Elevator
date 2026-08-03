from application.queries import GetPassengerStatsQuery, GetPositionLogQuery
from application.raw_request import RawRequest
from composition.container import build_application
from domain.value_objects import ElevatorId, Floor, PassengerId, Tick
from infrastructure.in_memory_simulation_registry import InMemorySimulationRegistry


def _raw(passenger: str, source: int, destination: int, tick: int) -> RawRequest:
    return RawRequest(
        passenger_id=PassengerId(passenger),
        source=Floor(source),
        destination=Floor(destination),
        tick=Tick(tick),
    )


def _build(requests: list[RawRequest], num_elevators: int, num_floors: int, elevator_capacity: int):
    return build_application(
        requests=requests,
        num_elevators=num_elevators,
        num_floors=num_floors,
        elevator_capacity=elevator_capacity,
        simulation_registry=InMemorySimulationRegistry(),
    )


def test_simulation_serves_every_passenger_and_computes_sane_stats() -> None:
    requests = [
        _raw("p1", source=0, destination=5, tick=0),
        _raw("p2", source=3, destination=9, tick=0),
        _raw("p3", source=8, destination=1, tick=4),
    ]

    app = _build(requests, num_elevators=2, num_floors=10, elevator_capacity=4)
    app.orchestrator().run()

    summary = app.passenger_stats_query_handler().handle(GetPassengerStatsQuery())
    assert summary.completed_count == 3
    assert summary.still_in_progress_count == 0
    assert summary.min_wait_time >= 0
    assert summary.min_total_time >= 1  # travel is never instantaneous when source != dest


def test_request_at_the_elevators_starting_floor_has_zero_wait_time() -> None:
    # Regression test: the orchestrator used to drain the outbox only after advancing
    # elevators each tick, so a request assigned this tick could never influence this
    # tick's movement — even an elevator already idling on the requested floor would
    # still wait a full tick before picking up. Assignment must now happen (drain) before
    # movement (advance) within the same tick, so pickup can happen at tick 0 here.
    requests = [_raw("p1", source=0, destination=5, tick=0)]

    app = _build(requests, num_elevators=1, num_floors=10, elevator_capacity=4)
    app.orchestrator().run()

    summary = app.passenger_stats_query_handler().handle(GetPassengerStatsQuery())
    assert summary.completed_count == 1
    assert summary.min_wait_time == 0


def test_position_log_has_a_row_for_every_elevator_at_every_tick_up_to_completion() -> None:
    requests = [_raw("p1", source=0, destination=9, tick=0)]

    app = _build(requests, num_elevators=2, num_floors=10, elevator_capacity=4)
    app.orchestrator().run()

    rows = app.position_log_query_handler().handle(GetPositionLogQuery())
    last_tick = max(row.tick.value for row in rows)
    for tick_value in range(last_tick + 1):
        for elevator_id in (ElevatorId(0), ElevatorId(1)):
            matching = [
                row
                for row in rows
                if row.tick.value == tick_value and row.elevator_id == elevator_id
            ]
            assert len(matching) == 1, (
                f"missing/duplicate row for elevator {elevator_id} at tick {tick_value}"
            )


def test_requests_exceeding_a_single_elevators_capacity_are_all_eventually_served() -> None:
    # One elevator, capacity 1: five simultaneous requests force serialization through
    # dispatch's pending-retry path (objective #1 — no request may be dropped).
    requests = [_raw(f"p{i}", source=0, destination=9, tick=0) for i in range(5)]

    app = _build(requests, num_elevators=1, num_floors=10, elevator_capacity=1)
    app.orchestrator().run()

    summary = app.passenger_stats_query_handler().handle(GetPassengerStatsQuery())
    assert summary.completed_count == 5
    assert summary.still_in_progress_count == 0


def test_no_requests_still_records_tick_zero_for_every_idle_elevator() -> None:
    app = _build([], num_elevators=2, num_floors=10, elevator_capacity=4)

    app.orchestrator().run()

    rows = app.position_log_query_handler().handle(GetPositionLogQuery())
    assert len(rows) == 2  # one tick-0 row per elevator, both idle at the starting floor
    assert all(row.tick == Tick(0) for row in rows)
