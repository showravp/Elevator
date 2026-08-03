import pytest

from application.exceptions import SimulationRunNotFoundException
from application.simulation_run import SimulationRun
from application.simulation_run_id import SimulationRunId
from infrastructure.in_memory_simulation_registry import InMemorySimulationRegistry


def test_get_after_add_returns_the_same_instance() -> None:
    registry = InMemorySimulationRegistry()
    run_id = SimulationRunId.generate()
    run = SimulationRun(id=run_id)

    registry.add(run)

    assert registry.get(run_id) is run


def test_get_unknown_run_raises_not_found() -> None:
    registry = InMemorySimulationRegistry()

    with pytest.raises(SimulationRunNotFoundException):
        registry.get(SimulationRunId.generate())
