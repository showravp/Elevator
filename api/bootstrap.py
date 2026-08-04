from pathlib import Path

from api.run_scope import RunScope
from application.handlers.query import GetSimulationStatusHandler
from application.ports import ISimulationRegistry
from infrastructure.csv_config_repository import CsvConfigRepository
from infrastructure.in_memory_simulation_registry import InMemorySimulationRegistry


def bootstrap_api_state(
    output_dir: Path = Path("output"),
) -> tuple[ISimulationRegistry, RunScope, GetSimulationStatusHandler]:
    """Process-wide state for the life of the server: one registry, one RunScope, one
    status query handler. This — together with api/container.py — is where infrastructure
    concrete classes get constructed for the API; routers and schemas never do, same rule
    as everywhere else in the app, just enforced by file boundary within api/ rather than
    by a separate composition/ package. api/routers/ only ever receives already-built
    instances via app.state, never builds its own."""
    registry = InMemorySimulationRegistry()
    config_repository = CsvConfigRepository(output_dir=output_dir)
    run_scope = RunScope(registry, config_repository, output_dir=output_dir)
    status_handler = GetSimulationStatusHandler(registry)
    return registry, run_scope, status_handler
