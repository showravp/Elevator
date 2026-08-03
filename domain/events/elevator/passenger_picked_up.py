from dataclasses import dataclass

from domain.events.domain_event import DomainEvent
from domain.value_objects import ElevatorId, Floor, PassengerId, Tick


@dataclass(frozen=True, slots=True)
class PassengerPickedUp(DomainEvent):
    elevator_id: ElevatorId
    passenger_id: PassengerId
    floor: Floor
    tick: Tick
