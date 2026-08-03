from application.exceptions import SimulationRunNotFoundException
from application.ports import ISimulationRegistry
from application.simulation_run import SimulationRun
from application.simulation_run_id import SimulationRunId


class InMemorySimulationRegistry(ISimulationRegistry):
    """Process-wide (not per-run) — tracks every run's status for the life of the server
    process. Does not persist across restarts."""

    def __init__(self) -> None:
        self._runs: dict[SimulationRunId, SimulationRun] = {}

    def add(self, run: SimulationRun) -> None:
        self._runs[run.id] = run

    def get(self, run_id: SimulationRunId) -> SimulationRun:
        try:
            return self._runs[run_id]
        except KeyError:
            raise SimulationRunNotFoundException(
                f"simulation run {run_id.value} not found"
            ) from None
