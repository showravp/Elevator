from dataclasses import dataclass

from application.simulation_run_id import SimulationRunId


@dataclass(frozen=True, slots=True)
class GetSimulationStatusQuery:
    run_id: SimulationRunId
