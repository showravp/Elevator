from dataclasses import dataclass

from domain.events.domain_event import DomainEvent
from domain.value_objects import ElevatorId, Floor, Tick


@dataclass(frozen=True, slots=True)
class ElevatorProvisioned(DomainEvent):
    elevator_id: ElevatorId
    capacity: int
    num_floors: int
    starting_floor: Floor
    tick: Tick
