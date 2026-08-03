from abc import ABC, abstractmethod

from application.simulation_config import SimulationConfig
from application.simulation_run_id import SimulationRunId


class IConfigRepository(ABC):
    @abstractmethod
    def get(self, run_id: SimulationRunId) -> SimulationConfig:
        """Raises ConfigNotFoundException if no config has been saved for this run."""

    @abstractmethod
    def save(self, run_id: SimulationRunId, config: SimulationConfig) -> None: ...
