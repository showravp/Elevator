from application.commands import ExecuteSimulationRunCommand
from application.orchestrator import SimulationOrchestrator
from application.ports import IPassengerStatsFileWriter, IPositionLogFileWriter, ISimulationRegistry
from application.repositories import IPassengerStatsRepository, IPositionLogRepository
from application.simulation_status import SimulationStatus


class ExecuteSimulationRunHandler:
    def __init__(
        self,
        orchestrator: SimulationOrchestrator,
        registry: ISimulationRegistry,
        position_log_repository: IPositionLogRepository,
        passenger_stats_repository: IPassengerStatsRepository,
        position_log_file_writer: IPositionLogFileWriter,
        passenger_stats_file_writer: IPassengerStatsFileWriter,
    ) -> None:
        self._orchestrator = orchestrator
        self._registry = registry
        self._position_log_repository = position_log_repository
        self._passenger_stats_repository = passenger_stats_repository
        self._position_log_file_writer = position_log_file_writer
        self._passenger_stats_file_writer = passenger_stats_file_writer

    def handle(self, command: ExecuteSimulationRunCommand) -> None:
        run = self._registry.get(command.run_id)
        run.status = SimulationStatus.RUNNING
        try:
            self._orchestrator.run()
            # Writing the required outputs to disk is part of what "completing a run"
            # means — a failure here fails the run rather than being silently swallowed.
            self._position_log_file_writer.write(
                command.run_id, self._position_log_repository.get_rows()
            )
            self._passenger_stats_file_writer.write(
                command.run_id, self._passenger_stats_repository.get_summary()
            )
        except Exception as error:
            # Deliberately broad: any failure here must land on the run's status for the
            # client to observe via polling, not crash the background task silently.
            run.status = SimulationStatus.FAILED
            run.error_message = str(error)
            return
        run.status = SimulationStatus.COMPLETED
