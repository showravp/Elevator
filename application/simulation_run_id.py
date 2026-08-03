import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimulationRunId:
    value: str

    @classmethod
    def generate(cls) -> "SimulationRunId":
        return cls(str(uuid.uuid4()))
