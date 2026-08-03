from dataclasses import dataclass


@dataclass(frozen=True, order=True, slots=True)
class Tick:
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError(f"Tick value must be non-negative, got {self.value}")

    def next(self) -> "Tick":
        return Tick(self.value + 1)
