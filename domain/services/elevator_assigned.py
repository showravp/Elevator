from dataclasses import dataclass

from domain.aggregates import Elevator


@dataclass(frozen=True, slots=True)
class ElevatorAssigned:
    elevator: Elevator
