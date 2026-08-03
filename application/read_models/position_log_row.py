from dataclasses import dataclass

from domain.value_objects import ElevatorId, Floor, Tick


@dataclass(frozen=True, slots=True)
class PositionLogRow:
    tick: Tick
    elevator_id: ElevatorId
    floor: Floor
