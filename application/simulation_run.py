from dataclasses import dataclass

from application.simulation_run_id import SimulationRunId
from application.simulation_status import SimulationStatus


@dataclass(slots=True)
class SimulationRun:
    """Purely about run lifecycle (status/error) — configuration lives in
    IConfigRepository, not duplicated here. A run's config can change (while PENDING);
    the run's identity and status tracking don't depend on any particular config value."""

    id: SimulationRunId
    status: SimulationStatus = SimulationStatus.PENDING
    error_message: str | None = None
