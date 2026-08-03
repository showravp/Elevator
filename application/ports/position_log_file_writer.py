from abc import ABC, abstractmethod

from application.read_models import PositionLogRow
from application.simulation_run_id import SimulationRunId


class IPositionLogFileWriter(ABC):
    @abstractmethod
    def write(self, run_id: SimulationRunId, rows: list[PositionLogRow], /) -> str:
        """Writes the position log to disk and returns the file path written.
        Positional-only: never called with keywords, and it lets one fake implement both
        file-writer ports despite them naming this parameter differently (rows/summary)."""
