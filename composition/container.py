from application.ports import SimulationRegistry
from application.raw_request import RawRequest
from composition.application_services import ApplicationServicesContainer


def build_application(
    requests: list[RawRequest],
    num_elevators: int,
    num_floors: int,
    elevator_capacity: int,
    simulation_registry: SimulationRegistry,
) -> ApplicationServicesContainer:
    container = ApplicationServicesContainer(simulation_registry=simulation_registry)
    container.config.from_dict(
        {
            "requests": requests,
            "num_elevators": num_elevators,
            "num_floors": num_floors,
            "elevator_capacity": elevator_capacity,
        }
    )
    # Event-bus subscribers must exist before the orchestrator starts publishing, so they
    # can't wait for lazy resolution on first use. passenger_stats_projection is also a
    # real constructor dependency of `orchestrator` (via the port) and would resolve
    # anyway, but resolving it here too keeps this list exhaustive and independent of
    # that wiring detail ever changing. dispatch_process_manager and
    # position_log_projection have no upstream consumer at all, so they rely on this
    # entirely.
    container.dispatch_process_manager()
    container.infrastructure.position_log_projection()
    container.infrastructure.passenger_stats_projection()
    return container
