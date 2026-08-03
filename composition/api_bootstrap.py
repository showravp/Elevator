from pathlib import Path

from application.handlers.query import GetSimulationStatusHandler
from application.ports import ISimulationRegistry
from composition.run_scope import RunScope
from infrastructure.in_memory_simulation_registry import InMemorySimulationRegistry


def bootstrap_api_state(
    output_dir: Path = Path("output"),
) -> tuple[ISimulationRegistry, RunScope, GetSimulationStatusHandler]:
    """Process-wide state for the life of the server: one registry, one RunScope, one
    status query handler. This is the only place `infrastructure` gets constructed for the
    API — api/ itself never imports infrastructure directly, same rule as everywhere else
    in the app — and the only place any of these get *constructed* at all. api/ only ever
    receives already-built instances via app.state, never builds its own."""
    registry = InMemorySimulationRegistry()
    run_scope = RunScope(registry, output_dir=output_dir)
    status_handler = GetSimulationStatusHandler(registry)
    return registry, run_scope, status_handler
