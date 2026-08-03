from dependency_injector import containers, providers

from application.orchestrator import SimulationOrchestrator
from application.outbox_relay import OutboxRelay
from application.process_managers import DispatchProcessManager
from application.projections import PassengerStatsProjection, PositionLogProjection
from composition.domain_services import DomainServicesContainer
from composition.infrastructure_services import InfrastructureServicesContainer


class ApplicationServicesContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    domain = providers.Container(DomainServicesContainer)
    infrastructure = providers.Container(InfrastructureServicesContainer, config=config)

    outbox_relay = providers.Singleton(
        OutboxRelay,
        outbox_store=infrastructure.event_store,
        event_bus=infrastructure.event_bus,
    )
    position_log_projection = providers.Singleton(
        PositionLogProjection, event_bus=infrastructure.event_bus
    )
    passenger_stats_projection = providers.Singleton(
        PassengerStatsProjection, event_bus=infrastructure.event_bus
    )
    dispatch_process_manager = providers.Singleton(
        DispatchProcessManager,
        elevator_repository=infrastructure.elevator_repository,
        request_repository=infrastructure.request_repository,
        scheduling_policy=domain.scheduling_policy,
        event_bus=infrastructure.event_bus,
    )
    orchestrator = providers.Singleton(
        SimulationOrchestrator,
        request_source=infrastructure.request_source,
        elevator_repository=infrastructure.elevator_repository,
        request_repository=infrastructure.request_repository,
        outbox_relay=outbox_relay,
        passenger_stats_projection=passenger_stats_projection,
        num_elevators=config.num_elevators,
        num_floors=config.num_floors,
        elevator_capacity=config.elevator_capacity,
    )
