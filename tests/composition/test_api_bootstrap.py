from composition.api_bootstrap import bootstrap_api_state
from infrastructure.in_memory_simulation_registry import InMemorySimulationRegistry


def test_bootstrap_returns_a_registry_and_a_run_scope_sharing_it() -> None:
    registry, run_scope = bootstrap_api_state()

    assert isinstance(registry, InMemorySimulationRegistry)
    run_id = run_scope.create(requests=[], num_elevators=1, num_floors=5, elevator_capacity=1)

    # RunScope was built with this exact registry instance, not a separate one
    assert registry.get(run_id).id == run_id


def test_each_call_produces_an_independent_registry() -> None:
    registry_a, _ = bootstrap_api_state()
    registry_b, _ = bootstrap_api_state()

    assert registry_a is not registry_b
