from pathlib import Path

from application.exceptions import SimulationRunNotFoundException
from application.ports import ISimulationRegistry
from application.raw_request import RawRequest
from application.simulation_run import SimulationRun
from application.simulation_run_id import SimulationRunId
from composition.application_services import ApplicationServicesContainer
from composition.container import build_application


class RunScope:
    """Owns per-run DI container construction and lookup — a composition-root concern,
    not application logic. `application/` never imports this; it only ever receives an
    already-built orchestrator/handler, injected by whoever calls into it."""

    def __init__(self, registry: ISimulationRegistry, output_dir: Path = Path("output")) -> None:
        self._registry = registry
        self._output_dir = output_dir
        self._containers: dict[SimulationRunId, ApplicationServicesContainer] = {}

    def create(
        self,
        requests: list[RawRequest],
        num_elevators: int,
        num_floors: int,
        elevator_capacity: int,
    ) -> SimulationRunId:
        run_id = SimulationRunId.generate()
        self._registry.add(
            SimulationRun(
                id=run_id,
                num_elevators=num_elevators,
                num_floors=num_floors,
                elevator_capacity=elevator_capacity,
            )
        )
        self._containers[run_id] = build_application(
            requests=requests,
            num_elevators=num_elevators,
            num_floors=num_floors,
            elevator_capacity=elevator_capacity,
            simulation_registry=self._registry,
            output_dir=self._output_dir,
        )
        return run_id

    def get_container(self, run_id: SimulationRunId) -> ApplicationServicesContainer:
        try:
            return self._containers[run_id]
        except KeyError:
            raise SimulationRunNotFoundException(f"simulation run {run_id.value} not found") from None
