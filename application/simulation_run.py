from dataclasses import dataclass

from application.simulation_run_id import SimulationRunId
from application.simulation_status import SimulationStatus


@dataclass(slots=True)
class SimulationRun:
    id: SimulationRunId
    num_elevators: int
    num_floors: int
    elevator_capacity: int
    status: SimulationStatus = SimulationStatus.PENDING
    error_message: str | None = None
