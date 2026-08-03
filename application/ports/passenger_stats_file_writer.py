from abc import ABC, abstractmethod

from application.read_models import PassengerStatsSummary
from application.simulation_run_id import SimulationRunId


class IPassengerStatsFileWriter(ABC):
    @abstractmethod
    def write(self, run_id: SimulationRunId, summary: PassengerStatsSummary) -> str:
        """Writes the passenger stats summary to disk and returns the file path written."""
