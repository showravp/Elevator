from pathlib import Path

from application.dependency_injection import ApplicationServicesContainer
from application.ports import ISimulationRegistry
from application.raw_request import RawRequest
from infrastructure.dependency_injection import InfrastructureServicesContainer


def build_application(
    requests: list[RawRequest],
    num_elevators: int,
    num_floors: int,
    elevator_capacity: int,
    simulation_registry: ISimulationRegistry,
    output_dir: Path = Path("output"),
) -> ApplicationServicesContainer:
    """The composition root: the one place application/ and infrastructure/ get wired
    together. Neither layer imports the other — application/dependency_injection.py
    declares Dependency slots typed to ports, and this function is what resolves the
    concrete infrastructure instances and supplies them, one container instance per
    simulation run (how per-run isolation is achieved). Living in api/ (rather than a
    separate composition/ package) mirrors how a .NET Web API project's Program.cs is
    itself the composition root, with a direct project reference to Infrastructure —
    routers and schemas still never import infrastructure directly, only this file does."""
    infrastructure = InfrastructureServicesContainer()
    infrastructure.config.from_dict({"requests": requests, "output_dir": output_dir})

    # Resolving each provider here (rather than letting application pull them lazily on
    # first use) is what guarantees event-bus subscribers (position_log_projection,
    # passenger_stats_projection) exist before the orchestrator starts publishing.
    application = ApplicationServicesContainer(
        simulation_registry=simulation_registry,
        event_bus=infrastructure.event_bus(),
        outbox_store=infrastructure.event_store(),
        elevator_repository=infrastructure.elevator_repository(),
        request_repository=infrastructure.request_repository(),
        request_source=infrastructure.request_source(),
        position_log_repository=infrastructure.position_log_projection(),
        passenger_stats_repository=infrastructure.passenger_stats_projection(),
        position_log_file_writer=infrastructure.position_log_file_writer(),
        passenger_stats_file_writer=infrastructure.passenger_stats_file_writer(),
    )
    application.config.from_dict(
        {
            "num_elevators": num_elevators,
            "num_floors": num_floors,
            "elevator_capacity": elevator_capacity,
        }
    )
    # dispatch_process_manager has no upstream consumer at all — nothing else resolves it,
    # so it relies entirely on this eager resolution to exist and subscribe before the
    # orchestrator runs.
    application.dispatch_process_manager()
    return application
