from domain.aggregate_root import AggregateRoot
from domain.events import (
    DomainEvent,
    ElevatorPositionRecorded,
    ElevatorProvisioned,
    PassengerDroppedOff,
    PassengerPickedUp,
    PickupStopScheduled,
)
from domain.exceptions import CapacityExceededException, InvalidFloorException
from domain.value_objects import Direction, ElevatorId, Floor, PassengerId, Tick


class Elevator(AggregateRoot[DomainEvent, ElevatorId]):
    _id: ElevatorId
    _capacity: int
    _num_floors: int
    _current_floor: Floor
    _direction: Direction
    _onboard: dict[PassengerId, Floor]
    _pending_pickups: dict[PassengerId, tuple[Floor, Floor]]

    @property
    def id(self) -> ElevatorId:
        return self._id

    @property
    def current_floor(self) -> Floor:
        return self._current_floor

    @property
    def direction(self) -> Direction:
        return self._direction

    @property
    def onboard_count(self) -> int:
        return len(self._onboard)

    @property
    def pending_pickup_count(self) -> int:
        return len(self._pending_pickups)

    @property
    def has_capacity_for_new_stop(self) -> bool:
        return self.onboard_count + self.pending_pickup_count < self._capacity

    @classmethod
    def provision(
        cls,
        elevator_id: ElevatorId,
        capacity: int,
        num_floors: int,
        starting_floor: Floor,
        tick: Tick,
    ) -> "Elevator":
        if not (0 <= starting_floor.value < num_floors):
            raise InvalidFloorException(
                f"starting_floor {starting_floor.value} is out of bounds for a "
                f"{num_floors}-floor building"
            )
        elevator = cls()
        elevator.raise_event(
            ElevatorProvisioned(
                elevator_id=elevator_id,
                capacity=capacity,
                num_floors=num_floors,
                starting_floor=starting_floor,
                tick=tick,
            )
        )
        return elevator

    def schedule_stop(
        self, passenger_id: PassengerId, source: Floor, destination: Floor, tick: Tick
    ) -> None:
        if not (0 <= source.value < self._num_floors) or not (
            0 <= destination.value < self._num_floors
        ):
            raise InvalidFloorException(
                f"source {source.value} / destination {destination.value} out of bounds "
                f"for a {self._num_floors}-floor building"
            )
        if not self.has_capacity_for_new_stop:
            raise CapacityExceededException(
                f"elevator {self._id.value} at capacity ({self._capacity}); "
                f"cannot accept passenger {passenger_id.value}"
            )
        self.raise_event(
            PickupStopScheduled(
                elevator_id=self._id,
                passenger_id=passenger_id,
                source=source,
                destination=destination,
                tick=tick,
            )
        )

    def advance(self, tick: Tick) -> None:
        target = self._next_target_floor()
        direction = self._direction_toward(target)
        next_floor = self._current_floor
        if direction is not Direction.IDLE:
            step = 1 if direction is Direction.UP else -1
            next_floor = Floor(self._current_floor.value + step)
        self.raise_event(
            ElevatorPositionRecorded(
                elevator_id=self._id, floor=next_floor, direction=direction, tick=tick
            )
        )
        self._board_and_alight(tick)

    def apply(self, event: DomainEvent) -> None:
        match event:
            case ElevatorProvisioned():
                self._id = event.elevator_id
                self._capacity = event.capacity
                self._num_floors = event.num_floors
                self._current_floor = event.starting_floor
                self._direction = Direction.IDLE
                self._onboard = {}
                self._pending_pickups = {}
            case ElevatorPositionRecorded():
                self._current_floor = event.floor
                self._direction = event.direction
            case PickupStopScheduled():
                self._pending_pickups[event.passenger_id] = (event.source, event.destination)
            case PassengerPickedUp():
                _, destination = self._pending_pickups.pop(event.passenger_id)
                self._onboard[event.passenger_id] = destination
            case PassengerDroppedOff():
                del self._onboard[event.passenger_id]
            case _:
                raise TypeError(f"Elevator cannot apply event of type {type(event).__name__}")

    def _board_and_alight(self, tick: Tick) -> None:
        for passenger_id, destination in list(self._onboard.items()):
            if destination == self._current_floor:
                self.raise_event(
                    PassengerDroppedOff(
                        elevator_id=self._id,
                        passenger_id=passenger_id,
                        floor=self._current_floor,
                        tick=tick,
                    )
                )
        for passenger_id, (source, _) in list(self._pending_pickups.items()):
            if source == self._current_floor:
                self.raise_event(
                    PassengerPickedUp(
                        elevator_id=self._id,
                        passenger_id=passenger_id,
                        floor=self._current_floor,
                        tick=tick,
                    )
                )

    def _next_target_floor(self) -> Floor | None:
        targets = list(self._onboard.values())
        targets += [source for source, _ in self._pending_pickups.values()]
        if not targets:
            return None
        return min(targets, key=self._current_floor.distance_to)

    def _direction_toward(self, target: Floor | None) -> Direction:
        if target is None or target == self._current_floor:
            return Direction.IDLE
        return Direction.UP if target.value > self._current_floor.value else Direction.DOWN
