from dependency_injector import containers, providers

from infrastructure.event_sourced_elevator_repository import EventSourcedElevatorRepository
from infrastructure.event_sourced_request_repository import EventSourcedRequestRepository
from infrastructure.in_memory_event_bus import InMemoryEventBus
from infrastructure.in_memory_event_store import InMemoryEventStore
from infrastructure.in_memory_request_source import InMemoryRequestSource
from infrastructure.passenger_stats_projection import PassengerStatsProjection
from infrastructure.position_log_projection import PositionLogProjection


class InfrastructureServicesContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Singleton here means "one instance per container instance", not process-wide — a
    # fresh InfrastructureServicesContainer (one per simulation run) gets its own event
    # store/bus, which is how per-run isolation is achieved without threading it manually.
    event_store = providers.Singleton(InMemoryEventStore)
    event_bus = providers.Singleton(InMemoryEventBus)
    request_source = providers.Singleton(InMemoryRequestSource, requests=config.requests)

    elevator_repository = providers.Singleton(
        EventSourcedElevatorRepository, event_store=event_store
    )
    request_repository = providers.Singleton(
        EventSourcedRequestRepository, event_store=event_store
    )

    # These implement application-layer read-repository ports (PositionLogRepository,
    # PassengerStatsRepository) — swapping in a SQL-backed implementation later means
    # replacing these two providers only, nothing upstream (orchestrator, query handlers)
    # changes since they depend on the port, not on these concrete classes.
    position_log_projection = providers.Singleton(PositionLogProjection, event_bus=event_bus)
    passenger_stats_projection = providers.Singleton(
        PassengerStatsProjection, event_bus=event_bus
    )
