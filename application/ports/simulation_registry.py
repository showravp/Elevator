from abc import ABC, abstractmethod

from application.simulation_run import SimulationRun
from application.simulation_run_id import SimulationRunId


class ISimulationRegistry(ABC):
    @abstractmethod
    def add(self, run: SimulationRun) -> None:
        ...

    @abstractmethod
    def get(self, run_id: SimulationRunId) -> SimulationRun:
        """Returns the live, mutable SimulationRun instance — callers update status by
        mutating it directly. Raises SimulationRunNotFoundException if unknown."""
