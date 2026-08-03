from domain.aggregate_root import AggregateRoot
from domain.events import DomainEvent, RequestAssigned, RequestSubmitted
from domain.exceptions import DuplicateAssignmentException, InvalidFloorException, SameFloorRequestException
from domain.value_objects import ElevatorId, Floor, PassengerId, Tick


class Request(AggregateRoot[DomainEvent, PassengerId]):
    _id: PassengerId
    _source: Floor
    _destination: Floor
    _submitted_at: Tick
    _assigned_elevator_id: ElevatorId | None
    _assigned_at: Tick | None

    @property
    def id(self) -> PassengerId:
        return self._id

    @property
    def source(self) -> Floor:
        return self._source

    @property
    def destination(self) -> Floor:
        return self._destination

    @property
    def submitted_at(self) -> Tick:
        return self._submitted_at

    @property
    def is_assigned(self) -> bool:
        return self._assigned_elevator_id is not None

    @property
    def assigned_elevator_id(self) -> ElevatorId | None:
        return self._assigned_elevator_id

    @classmethod
    def submit(
        cls,
        passenger_id: PassengerId,
        source: Floor,
        destination: Floor,
        num_floors: int,
        tick: Tick,
    ) -> "Request":
        if not (0 <= source.value < num_floors) or not (0 <= destination.value < num_floors):
            raise InvalidFloorException(
                f"source {source.value} / destination {destination.value} out of bounds "
                f"for a {num_floors}-floor building"
            )
        if source == destination:
            raise SameFloorRequestException(
                f"passenger {passenger_id.value} requested source and destination "
                f"both floor {source.value}"
            )
        request = cls()
        request.raise_event(
            RequestSubmitted(
                passenger_id=passenger_id, source=source, destination=destination, tick=tick
            )
        )
        return request

    def assign(self, elevator_id: ElevatorId, tick: Tick) -> None:
        if self.is_assigned:
            raise DuplicateAssignmentException(
                f"passenger {self._id.value} is already assigned to elevator "
                f"{self._assigned_elevator_id.value}"  # type: ignore[union-attr]
            )
        self.raise_event(
            RequestAssigned(passenger_id=self._id, elevator_id=elevator_id, tick=tick)
        )

    def apply(self, event: DomainEvent) -> None:
        match event:
            case RequestSubmitted():
                self._id = event.passenger_id
                self._source = event.source
                self._destination = event.destination
                self._submitted_at = event.tick
                self._assigned_elevator_id = None
                self._assigned_at = None
            case RequestAssigned():
                self._assigned_elevator_id = event.elevator_id
                self._assigned_at = event.tick
            case _:
                raise TypeError(f"Request cannot apply event of type {type(event).__name__}")
