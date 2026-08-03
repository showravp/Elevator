from domain.aggregates import Elevator, Request
from domain.services.scheduling_policy import SchedulingPolicy
from domain.value_objects import Direction


class NearestCarSchedulingPolicy(SchedulingPolicy):
    _DIRECTION_MISMATCH_PENALTY = 1000

    def select_elevator(self, request: Request, elevators: list[Elevator]) -> Elevator | None:
        candidates = [elevator for elevator in elevators if elevator.has_capacity_for_new_stop]
        if not candidates:
            return None
        return min(candidates, key=lambda elevator: self._cost(elevator, request))

    def _cost(self, elevator: Elevator, request: Request) -> int:
        distance = elevator.current_floor.distance_to(request.source)
        queue_depth = elevator.pending_pickup_count + elevator.onboard_count
        mismatch_penalty = (
            self._DIRECTION_MISMATCH_PENALTY
            if self._is_direction_mismatch(elevator, request)
            else 0
        )
        return distance + queue_depth + mismatch_penalty

    def _is_direction_mismatch(self, elevator: Elevator, request: Request) -> bool:
        if elevator.direction is Direction.IDLE:
            return False
        travelling_up = elevator.direction is Direction.UP
        request_is_ahead = (
            request.source.value >= elevator.current_floor.value
            if travelling_up
            else request.source.value <= elevator.current_floor.value
        )
        return not request_is_ahead
