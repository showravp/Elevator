import pytest

from application.exceptions import SimulationRunNotFoundError
from application.simulation_run_id import SimulationRunId
from composition.run_scope import RunScope
from infrastructure.in_memory_simulation_registry import InMemorySimulationRegistry


def test_create_registers_a_pending_run_and_a_container() -> None:
    registry = InMemorySimulationRegistry()
    run_scope = RunScope(registry)

    run_id = run_scope.create(requests=[], num_elevators=2, num_floors=10, elevator_capacity=4)

    assert registry.get(run_id).id == run_id
    assert run_scope.get_container(run_id) is not None


def test_get_container_for_unknown_run_raises_not_found() -> None:
    run_scope = RunScope(InMemorySimulationRegistry())

    with pytest.raises(SimulationRunNotFoundError):
        run_scope.get_container(SimulationRunId.generate())


def test_each_run_gets_an_isolated_container() -> None:
    registry = InMemorySimulationRegistry()
    run_scope = RunScope(registry)

    run_id_a = run_scope.create(requests=[], num_elevators=1, num_floors=10, elevator_capacity=1)
    run_id_b = run_scope.create(requests=[], num_elevators=1, num_floors=10, elevator_capacity=1)

    assert run_scope.get_container(run_id_a) is not run_scope.get_container(run_id_b)
