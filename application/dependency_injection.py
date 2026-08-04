from dependency_injector import containers, providers

from application.handlers.command import ExecuteSimulationRunHandler
from application.handlers.query import GetPassengerStatsHandler, GetPositionLogHandler
from application.orchestrator import SimulationOrchestrator
from application.outbox_relay import OutboxRelay
from application.ports import (
    IEventBus,
    IOutboxStore,
    IPassengerStatsFileWriter,
    IPositionLogFileWriter,
    IRequestSource,
    ISimulationRegistry,
)
from application.process_managers import DispatchProcessManager
from application.repositories import IPassengerStatsRepository, IPositionLogRepository
from domain.dependency_injection import DomainServicesContainer
from domain.repositories import IElevatorRepository, IRequestRepository


class ApplicationServicesContainer(containers.DeclarativeContainer):
    """Registers only application-owned components. Concrete infrastructure classes are
    never imported here — every port this layer needs but can't construct itself is a
    Dependency provider, supplied by the composition root (api/container.py) at
    construction time. That keeps this file's import list to application/ and domain/
    only, same Dependency Rule every other consumer in this codebase already follows."""

    config = providers.Configuration()

    # Provided from outside at container-construction time — the registry is process-wide
    # (tracks every run), unlike everything else in this container, which is per-run.
    simulation_registry: providers.Dependency[ISimulationRegistry] = providers.Dependency(
        instance_of=ISimulationRegistry
    )
    event_bus: providers.Dependency[IEventBus] = providers.Dependency(instance_of=IEventBus)
    outbox_store: providers.Dependency[IOutboxStore] = providers.Dependency(
        instance_of=IOutboxStore
    )
    elevator_repository: providers.Dependency[IElevatorRepository] = providers.Dependency(
        instance_of=IElevatorRepository
    )
    request_repository: providers.Dependency[IRequestRepository] = providers.Dependency(
        instance_of=IRequestRepository
    )
    request_source: providers.Dependency[IRequestSource] = providers.Dependency(
        instance_of=IRequestSource
    )
    position_log_repository: providers.Dependency[IPositionLogRepository] = providers.Dependency(
        instance_of=IPositionLogRepository
    )
    passenger_stats_repository: providers.Dependency[IPassengerStatsRepository] = (
        providers.Dependency(instance_of=IPassengerStatsRepository)
    )
    position_log_file_writer: providers.Dependency[IPositionLogFileWriter] = providers.Dependency(
        instance_of=IPositionLogFileWriter
    )
    passenger_stats_file_writer: providers.Dependency[IPassengerStatsFileWriter] = (
        providers.Dependency(instance_of=IPassengerStatsFileWriter)
    )

    domain = providers.Container(DomainServicesContainer)

    outbox_relay = providers.Singleton(OutboxRelay, outbox_store=outbox_store, event_bus=event_bus)
    dispatch_process_manager = providers.Singleton(
        DispatchProcessManager,
        elevator_repository=elevator_repository,
        request_repository=request_repository,
        scheduling_policy=domain.scheduling_policy,
        event_bus=event_bus,
    )
    orchestrator = providers.Singleton(
        SimulationOrchestrator,
        request_source=request_source,
        elevator_repository=elevator_repository,
        request_repository=request_repository,
        outbox_relay=outbox_relay,
        passenger_stats_repository=passenger_stats_repository,
        num_elevators=config.num_elevators,
        num_floors=config.num_floors,
        elevator_capacity=config.elevator_capacity,
    )
    execute_run_handler = providers.Singleton(
        ExecuteSimulationRunHandler,
        orchestrator=orchestrator,
        registry=simulation_registry,
        position_log_repository=position_log_repository,
        passenger_stats_repository=passenger_stats_repository,
        position_log_file_writer=position_log_file_writer,
        passenger_stats_file_writer=passenger_stats_file_writer,
    )
    position_log_query_handler = providers.Singleton(
        GetPositionLogHandler, repository=position_log_repository
    )
    passenger_stats_query_handler = providers.Singleton(
        GetPassengerStatsHandler, repository=passenger_stats_repository
    )
