from application.ports import SimulationRegistry
from composition.run_scope import RunScope
from infrastructure.in_memory_simulation_registry import InMemorySimulationRegistry


def bootstrap_api_state() -> tuple[SimulationRegistry, RunScope]:
    """Process-wide state for the life of the server: one registry, one RunScope. This is
    the only place `infrastructure` gets constructed for the API — api/ itself never
    imports infrastructure directly, same rule as everywhere else in the app."""
    registry = InMemorySimulationRegistry()
    return registry, RunScope(registry)
