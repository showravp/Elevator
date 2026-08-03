from pathlib import Path

from application.handlers.query import GetSimulationStatusHandler
from application.queries import GetSimulationStatusQuery
from application.simulation_config import SimulationConfig
from composition.api_bootstrap import bootstrap_api_state
from infrastructure.in_memory_simulation_registry import InMemorySimulationRegistry

_CONFIG = SimulationConfig(num_elevators=1, num_floors=5, elevator_capacity=1)


def test_bootstrap_returns_a_registry_and_a_run_scope_sharing_it(tmp_path: Path) -> None:
    registry, run_scope, _status_handler = bootstrap_api_state(output_dir=tmp_path)

    assert isinstance(registry, InMemorySimulationRegistry)
    run_id = run_scope.create_run(_CONFIG)

    # RunScope was built with this exact registry instance, not a separate one
    assert registry.get(run_id).id == run_id


def test_status_handler_shares_the_same_registry_as_run_scope(tmp_path: Path) -> None:
    _registry, run_scope, status_handler = bootstrap_api_state(output_dir=tmp_path)
    run_id = run_scope.create_run(_CONFIG)

    status = status_handler.handle(GetSimulationStatusQuery(run_id))

    assert status.id == run_id
    assert isinstance(status_handler, GetSimulationStatusHandler)


def test_each_call_produces_an_independent_registry(tmp_path: Path) -> None:
    registry_a, _, _ = bootstrap_api_state(output_dir=tmp_path)
    registry_b, _, _ = bootstrap_api_state(output_dir=tmp_path)

    assert registry_a is not registry_b
