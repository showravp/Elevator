from application.commands import ExecuteSimulationRunCommand
from application.orchestrator import SimulationOrchestrator
from application.ports import SimulationRegistry
from application.simulation_status import SimulationStatus


class ExecuteSimulationRunHandler:
    def __init__(self, orchestrator: SimulationOrchestrator, registry: SimulationRegistry) -> None:
        self._orchestrator = orchestrator
        self._registry = registry

    def handle(self, command: ExecuteSimulationRunCommand) -> None:
        run = self._registry.get(command.run_id)
        run.status = SimulationStatus.RUNNING
        try:
            self._orchestrator.run()
        except Exception as error:
            # Deliberately broad: any failure here must land on the run's status for the
            # client to observe via polling, not crash the background task silently.
            run.status = SimulationStatus.FAILED
            run.error_message = str(error)
            return
        run.status = SimulationStatus.COMPLETED
