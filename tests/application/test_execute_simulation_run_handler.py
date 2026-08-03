from application.commands import ExecuteSimulationRunCommand
from application.handlers.command import ExecuteSimulationRunHandler
from application.ports import IOrchestrator, IPassengerStatsFileWriter, IPositionLogFileWriter
from application.read_models import PassengerStatsSummary, PositionLogRow
from application.repositories import IPassengerStatsRepository, IPositionLogRepository
from application.simulation_run import SimulationRun
from application.simulation_run_id import SimulationRunId
from application.simulation_status import SimulationStatus
from infrastructure.in_memory_simulation_registry import InMemorySimulationRegistry

_EMPTY_SUMMARY = PassengerStatsSummary(0, 0, 0, 0, 0.0, 0, 0, 0.0)


class _StubOrchestrator:
    """No inheritance needed — IOrchestrator is a Protocol, satisfied structurally by
    having a matching run() method."""

    def __init__(self, raise_error: Exception | None = None) -> None:
        self._raise_error = raise_error
        self.ran = False

    def run(self) -> None:
        self.ran = True
        if self._raise_error is not None:
            raise self._raise_error


class _StubPositionLogRepository(IPositionLogRepository):
    def get_rows(self) -> list[PositionLogRow]:
        return []


class _StubPassengerStatsRepository(IPassengerStatsRepository):
    def get_summary(self) -> PassengerStatsSummary:
        return _EMPTY_SUMMARY


class _RecordingFileWriter(IPositionLogFileWriter, IPassengerStatsFileWriter):
    def __init__(self, raise_error: Exception | None = None) -> None:
        self._raise_error = raise_error
        self.written_with: object | None = None

    def write(self, run_id: SimulationRunId, payload: object) -> str:
        if self._raise_error is not None:
            raise self._raise_error
        self.written_with = payload
        return "/fake/path"


def _build_handler(
    orchestrator: IOrchestrator,
    registry: InMemorySimulationRegistry,
    position_log_file_writer: _RecordingFileWriter | None = None,
    passenger_stats_file_writer: _RecordingFileWriter | None = None,
) -> ExecuteSimulationRunHandler:
    return ExecuteSimulationRunHandler(
        orchestrator=orchestrator,
        registry=registry,
        position_log_repository=_StubPositionLogRepository(),
        passenger_stats_repository=_StubPassengerStatsRepository(),
        position_log_file_writer=position_log_file_writer or _RecordingFileWriter(),
        passenger_stats_file_writer=passenger_stats_file_writer or _RecordingFileWriter(),
    )


def test_handle_marks_run_completed_on_success() -> None:
    registry = InMemorySimulationRegistry()
    run_id = SimulationRunId.generate()
    registry.add(SimulationRun(id=run_id, num_elevators=1, num_floors=10, elevator_capacity=1))
    orchestrator = _StubOrchestrator()
    handler = _build_handler(orchestrator, registry)

    handler.handle(ExecuteSimulationRunCommand(run_id))

    assert orchestrator.ran is True
    assert registry.get(run_id).status is SimulationStatus.COMPLETED


def test_handle_writes_position_log_and_passenger_stats_files_on_success() -> None:
    registry = InMemorySimulationRegistry()
    run_id = SimulationRunId.generate()
    registry.add(SimulationRun(id=run_id, num_elevators=1, num_floors=10, elevator_capacity=1))
    position_writer = _RecordingFileWriter()
    stats_writer = _RecordingFileWriter()
    handler = _build_handler(_StubOrchestrator(), registry, position_writer, stats_writer)

    handler.handle(ExecuteSimulationRunCommand(run_id))

    assert position_writer.written_with == []
    assert stats_writer.written_with is _EMPTY_SUMMARY


def test_handle_marks_run_failed_with_error_message_on_exception() -> None:
    registry = InMemorySimulationRegistry()
    run_id = SimulationRunId.generate()
    registry.add(SimulationRun(id=run_id, num_elevators=1, num_floors=10, elevator_capacity=1))
    orchestrator = _StubOrchestrator(raise_error=ValueError("boom"))
    handler = _build_handler(orchestrator, registry)

    handler.handle(ExecuteSimulationRunCommand(run_id))

    run = registry.get(run_id)
    assert run.status is SimulationStatus.FAILED
    assert run.error_message == "boom"


def test_handle_marks_run_failed_when_file_writing_fails() -> None:
    registry = InMemorySimulationRegistry()
    run_id = SimulationRunId.generate()
    registry.add(SimulationRun(id=run_id, num_elevators=1, num_floors=10, elevator_capacity=1))
    failing_writer = _RecordingFileWriter(raise_error=OSError("disk full"))
    handler = _build_handler(_StubOrchestrator(), registry, failing_writer)

    handler.handle(ExecuteSimulationRunCommand(run_id))

    run = registry.get(run_id)
    assert run.status is SimulationStatus.FAILED
    assert run.error_message == "disk full"


def test_run_status_is_running_while_orchestrator_executes() -> None:
    registry = InMemorySimulationRegistry()
    run_id = SimulationRunId.generate()
    registry.add(SimulationRun(id=run_id, num_elevators=1, num_floors=10, elevator_capacity=1))
    observed_status = {}

    class _ObservingOrchestrator:
        def run(self) -> None:
            observed_status["status"] = registry.get(run_id).status

    handler = _build_handler(_ObservingOrchestrator(), registry)
    handler.handle(ExecuteSimulationRunCommand(run_id))

    assert observed_status["status"] is SimulationStatus.RUNNING
