from dataclasses import dataclass


@dataclass(frozen=True, order=True, slots=True)
class ElevatorId:
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError(f"ElevatorId value must be non-negative, got {self.value}")
