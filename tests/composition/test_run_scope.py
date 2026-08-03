from pathlib import Path

import pytest

from application.exceptions import ConfigNotFoundException, SimulationRunNotFoundException
from application.simulation_config import SimulationConfig
from application.simulation_run import SimulationRun
from application.simulation_run_id import SimulationRunId
from composition.run_scope import RunScope
from infrastructure.csv_config_repository import CsvConfigRepository
from infrastructure.in_memory_simulation_registry import InMemorySimulationRegistry

_CONFIG = SimulationConfig(num_elevators=2, num_floors=10, elevator_capacity=4)


def _run_scope(tmp_path: Path) -> RunScope:
    return RunScope(InMemorySimulationRegistry(), CsvConfigRepository(output_dir=tmp_path))


def test_create_run_registers_a_pending_run_and_persists_config(tmp_path: Path) -> None:
    registry = InMemorySimulationRegistry()
    run_scope = RunScope(registry, CsvConfigRepository(output_dir=tmp_path))

    run_id = run_scope.create_run(_CONFIG)

    assert registry.get(run_id).id == run_id
    assert (tmp_path / run_id.value / "config.csv").exists()


def test_create_run_does_not_build_a_container_yet(tmp_path: Path) -> None:
    run_scope = _run_scope(tmp_path)
    run_id = run_scope.create_run(_CONFIG)

    with pytest.raises(SimulationRunNotFoundException):
        run_scope.get_container(run_id)


def test_attach_requests_builds_a_container_using_the_saved_config(tmp_path: Path) -> None:
    run_scope = _run_scope(tmp_path)
    run_id = run_scope.create_run(_CONFIG)

    container = run_scope.attach_requests(run_id, [])

    assert run_scope.get_container(run_id) is container


def test_attach_requests_for_a_run_with_no_config_raises_config_not_found(tmp_path: Path) -> None:
    # RunScope.attach_requests() reads config via IConfigRepository rather than trusting
    # any cached value — a run that was never through create_run() (or whose config.csv
    # was otherwise never written) has no config to build a container from.
    registry = InMemorySimulationRegistry()
    run_id = SimulationRunId.generate()
    registry.add(SimulationRun(id=run_id))
    run_scope = RunScope(registry, CsvConfigRepository(output_dir=tmp_path))

    with pytest.raises(ConfigNotFoundException):
        run_scope.attach_requests(run_id, [])


def test_update_config_overwrites_the_persisted_config(tmp_path: Path) -> None:
    config_repository = CsvConfigRepository(output_dir=tmp_path)
    run_scope = RunScope(InMemorySimulationRegistry(), config_repository)
    run_id = run_scope.create_run(_CONFIG)

    new_config = SimulationConfig(num_elevators=5, num_floors=20, elevator_capacity=8)
    run_scope.update_config(run_id, new_config)

    assert config_repository.get(run_id) == new_config


def test_get_container_for_unknown_run_raises_not_found(tmp_path: Path) -> None:
    run_scope = _run_scope(tmp_path)

    with pytest.raises(SimulationRunNotFoundException):
        run_scope.get_container(SimulationRunId.generate())


def test_each_run_gets_an_isolated_container(tmp_path: Path) -> None:
    run_scope = _run_scope(tmp_path)

    run_id_a = run_scope.create_run(_CONFIG)
    run_id_b = run_scope.create_run(_CONFIG)
    run_scope.attach_requests(run_id_a, [])
    run_scope.attach_requests(run_id_b, [])

    assert run_scope.get_container(run_id_a) is not run_scope.get_container(run_id_b)
