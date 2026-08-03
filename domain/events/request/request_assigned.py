from dataclasses import dataclass

from domain.events.domain_event import DomainEvent
from domain.value_objects import ElevatorId, PassengerId, Tick


@dataclass(frozen=True, slots=True)
class RequestAssigned(DomainEvent):
    passenger_id: PassengerId
    elevator_id: ElevatorId
    tick: Tick
