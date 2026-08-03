from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PassengerId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("PassengerId value must not be empty")
