from dataclasses import dataclass


@dataclass(frozen=True, order=True, slots=True)
class Floor:
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError(f"Floor value must be non-negative, got {self.value}")

    def distance_to(self, other: "Floor") -> int:
        return abs(self.value - other.value)
