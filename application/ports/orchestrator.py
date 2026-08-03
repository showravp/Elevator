from typing import Protocol


class IOrchestrator(Protocol):
    """Structural, not an ABC — SimulationOrchestrator has exactly one implementation, so
    there's nothing to abstract over. This exists purely so ExecuteSimulationRunHandler
    depends on a narrow contract (run()) rather than the concrete class, letting tests
    substitute a stub/fake without inheritance."""

    def run(self) -> None: ...
