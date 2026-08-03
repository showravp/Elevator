from dataclasses import dataclass

from domain.events.domain_event import DomainEvent
from domain.value_objects import Direction, ElevatorId, Floor, Tick


@dataclass(frozen=True, slots=True)
class ElevatorPositionRecorded(DomainEvent):
    elevator_id: ElevatorId
    floor: Floor
    direction: Direction
    tick: Tick
