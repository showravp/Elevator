from application.commands import ExecuteSimulationRunCommand
from application.handlers.command import ExecuteSimulationRunHandler
from application.simulation_run import SimulationRun
from application.simulation_run_id import SimulationRunId
from application.simulation_status import SimulationStatus
from infrastructure.in_memory_simulation_registry import InMemorySimulationRegistry


class _StubOrchestrator:
    def __init__(self, raise_error: Exception | None = None) -> None:
        self._raise_error = raise_error
        self.ran = False

    def run(self) -> None:
        self.ran = True
        if self._raise_error is not None:
            raise self._raise_error


def test_handle_marks_run_completed_on_success() -> None:
    registry = InMemorySimulationRegistry()
    run_id = SimulationRunId.generate()
    registry.add(SimulationRun(id=run_id, num_elevators=1, num_floors=10, elevator_capacity=1))
    orchestrator = _StubOrchestrator()
    handler = ExecuteSimulationRunHandler(orchestrator, registry)

    handler.handle(ExecuteSimulationRunCommand(run_id))

    assert orchestrator.ran is True
    assert registry.get(run_id).status is SimulationStatus.COMPLETED


def test_handle_marks_run_failed_with_error_message_on_exception() -> None:
    registry = InMemorySimulationRegistry()
    run_id = SimulationRunId.generate()
    registry.add(SimulationRun(id=run_id, num_elevators=1, num_floors=10, elevator_capacity=1))
    orchestrator = _StubOrchestrator(raise_error=ValueError("boom"))
    handler = ExecuteSimulationRunHandler(orchestrator, registry)

    handler.handle(ExecuteSimulationRunCommand(run_id))

    run = registry.get(run_id)
    assert run.status is SimulationStatus.FAILED
    assert run.error_message == "boom"


def test_run_status_is_running_while_orchestrator_executes() -> None:
    registry = InMemorySimulationRegistry()
    run_id = SimulationRunId.generate()
    registry.add(SimulationRun(id=run_id, num_elevators=1, num_floors=10, elevator_capacity=1))
    observed_status = {}

    class _ObservingOrchestrator:
        def run(self) -> None:
            observed_status["status"] = registry.get(run_id).status

    handler = ExecuteSimulationRunHandler(_ObservingOrchestrator(), registry)
    handler.handle(ExecuteSimulationRunCommand(run_id))

    assert observed_status["status"] is SimulationStatus.RUNNING
