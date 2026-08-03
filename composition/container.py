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
    # Event-bus subscribers with no other consumer (process manager, projections) are
    # otherwise never instantiated by the graph, so resolve them explicitly here to
    # trigger their __init__ subscription before the orchestrator starts publishing.
    container.dispatch_process_manager()
    container.position_log_projection()
    container.passenger_stats_projection()
    return container
