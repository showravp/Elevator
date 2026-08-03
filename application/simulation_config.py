from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    num_elevators: int
    num_floors: int
    elevator_capacity: int
