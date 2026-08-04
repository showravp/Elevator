from pathlib import Path

from api.program import build_application
from application.dependency_injection import ApplicationServicesContainer
from application.exceptions import SimulationRunNotFoundException
from application.ports import ISimulationRegistry
from application.raw_request import RawRequest
from application.repositories import IConfigRepository
from application.simulation_config import SimulationConfig
from application.simulation_run import SimulationRun
from application.simulation_run_id import SimulationRunId


class RunScope:
    """Owns per-run DI container construction and lookup — a composition-root concern,
    not application logic. `application/` never imports this; it only ever receives an
    already-built orchestrator/handler, injected by whoever calls into it.

    Config and requests are deliberately separate operations: the per-run container
    (which bakes num_elevators/num_floors/elevator_capacity into its DI wiring) can't be
    built until config is final, and config isn't final until the caller has stopped
    editing it — which the API layer enforces by only allowing requests submission (and
    therefore container construction) once, and only while the run is still PENDING."""

    def __init__(
        self,
        registry: ISimulationRegistry,
        config_repository: IConfigRepository,
        output_dir: Path = Path("output"),
    ) -> None:
        self._registry = registry
        self._config_repository = config_repository
        self._output_dir = output_dir
        self._containers: dict[SimulationRunId, ApplicationServicesContainer] = {}

    def create_run(self, config: SimulationConfig) -> SimulationRunId:
        run_id = SimulationRunId.generate()
        self._registry.add(SimulationRun(id=run_id))
        self._config_repository.save(run_id, config)
        return run_id

    def update_config(self, run_id: SimulationRunId, config: SimulationConfig) -> None:
        # Whether this is currently allowed (run must still be PENDING) is checked by the
        # caller — this method just persists. See SimulationConfigLockedException.
        self._config_repository.save(run_id, config)

    def attach_requests(
        self, run_id: SimulationRunId, requests: list[RawRequest]
    ) -> ApplicationServicesContainer:
        config = self._config_repository.get(run_id)
        container = build_application(
            requests=requests,
            num_elevators=config.num_elevators,
            num_floors=config.num_floors,
            elevator_capacity=config.elevator_capacity,
            simulation_registry=self._registry,
            output_dir=self._output_dir,
        )
        self._containers[run_id] = container
        return container

    def get_container(self, run_id: SimulationRunId) -> ApplicationServicesContainer:
        try:
            return self._containers[run_id]
        except KeyError:
            raise SimulationRunNotFoundException(
                f"simulation run {run_id.value} not found"
            ) from None
