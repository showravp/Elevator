from domain.aggregates import Elevator, Request
from domain.services import ElevatorAssigned, NoElevatorAvailable
from domain.services.strategies import NearestCarSchedulingPolicy
from domain.value_objects import Direction, ElevatorId, Floor, PassengerId, Tick

_POLICY = NearestCarSchedulingPolicy()


def _elevator(id_: int, starting_floor: int, capacity: int = 4) -> Elevator:
    return Elevator.provision(
        elevator_id=ElevatorId(id_),
        capacity=capacity,
        num_floors=20,
        starting_floor=Floor(starting_floor),
        tick=Tick(0),
    )


def _request(source: int = 5, destination: int = 10) -> Request:
    return Request.submit(
        PassengerId("p1"), Floor(source), Floor(destination), num_floors=20, tick=Tick(0)
    )


def test_selects_the_closest_elevator_with_capacity() -> None:
    near = _elevator(0, starting_floor=4)
    far = _elevator(1, starting_floor=15)
    request = _request(source=5, destination=10)

    chosen = _POLICY.select_elevator(request, [near, far])

    assert chosen == ElevatorAssigned(near)


def test_excludes_elevators_without_capacity() -> None:
    full = _elevator(0, starting_floor=4, capacity=1)
    full.schedule_stop(PassengerId("other"), Floor(4), Floor(6), Tick(0))
    far_but_available = _elevator(1, starting_floor=15)
    request = _request(source=5, destination=10)

    chosen = _POLICY.select_elevator(request, [full, far_but_available])

    assert chosen == ElevatorAssigned(far_but_available)


def test_returns_no_elevator_available_when_no_elevator_has_capacity() -> None:
    full = _elevator(0, starting_floor=4, capacity=1)
    full.schedule_stop(PassengerId("other"), Floor(4), Floor(6), Tick(0))
    request = _request(source=5, destination=10)

    chosen = _POLICY.select_elevator(request, [full])

    assert chosen == NoElevatorAvailable()


def test_returns_no_elevator_available_for_empty_elevator_list() -> None:
    request = _request()

    assert _POLICY.select_elevator(request, []) == NoElevatorAvailable()


def test_prefers_same_direction_elevator_over_a_closer_opposing_one() -> None:
    request = _request(source=10, destination=15)

    # source floors deliberately differ from each elevator's starting floor, otherwise
    # the elevator boards immediately on tick 1 and never actually starts moving
    travelling_away = _elevator(0, starting_floor=9)
    travelling_away.schedule_stop(PassengerId("other"), Floor(7), Floor(0), Tick(0))
    travelling_away.advance(Tick(1))  # now moving down, away from floor 10

    travelling_toward = _elevator(1, starting_floor=3)
    travelling_toward.schedule_stop(PassengerId("other2"), Floor(6), Floor(12), Tick(0))
    travelling_toward.advance(Tick(1))  # now moving up, toward floor 10

    chosen = _POLICY.select_elevator(request, [travelling_away, travelling_toward])

    assert chosen == ElevatorAssigned(travelling_toward)


def test_direction_mismatch_boundary_when_source_equals_current_floor() -> None:
    # source == current_floor must resolve as "ahead" (no mismatch penalty), not
    # "behind" — a strict > / < comparison here (instead of >= / <=) would wrongly
    # penalize an elevator that's already exactly where the pickup is. Tested through
    # the public API (not by reaching into the private _is_direction_mismatch helper):
    # far_idle only wins if the boundary is handled *incorrectly*, since a correctly
    # unpenalized moving_up (cost 1) beats far_idle (cost 10) either way distance alone
    # wouldn't decide it — the 1000-point mismatch penalty is what would flip the result.
    moving_up = _elevator(0, starting_floor=0)
    moving_up.schedule_stop(PassengerId("other"), Floor(1), Floor(10), Tick(0))
    for tick in range(1, 6):
        moving_up.advance(Tick(tick))
    assert moving_up.current_floor == Floor(5)
    assert moving_up.direction is Direction.UP

    far_idle = _elevator(1, starting_floor=15)
    request_at_current_floor = _request(source=5, destination=8)

    chosen = _POLICY.select_elevator(request_at_current_floor, [moving_up, far_idle])

    assert chosen == ElevatorAssigned(moving_up)


def test_selection_is_deterministic_on_exact_cost_ties() -> None:
    first = _elevator(0, starting_floor=5)
    second = _elevator(1, starting_floor=5)
    request = _request(source=5, destination=9)

    # Identical distance, queue depth, and direction (both idle) — cost is exactly equal.
    # min() over the input list keeps the first-seen minimum, so the winner is
    # positional; asserting it here locks in that this is deterministic, not
    # incidental, behavior.
    assert _POLICY.select_elevator(request, [first, second]) == ElevatorAssigned(first)
    assert _POLICY.select_elevator(request, [second, first]) == ElevatorAssigned(second)


def test_prefers_lower_queue_depth_when_distance_and_direction_are_equal() -> None:
    empty_queue = _elevator(0, starting_floor=5)
    busier = _elevator(1, starting_floor=5)
    busier.schedule_stop(PassengerId("other"), Floor(8), Floor(12), Tick(0))
    request = _request(source=5, destination=9)

    # Correct answer deliberately placed second, so a false pass from list-position
    # bias (rather than genuinely comparing queue depth) would be caught.
    chosen = _POLICY.select_elevator(request, [busier, empty_queue])

    assert chosen == ElevatorAssigned(empty_queue)
