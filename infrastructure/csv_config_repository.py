import csv
from pathlib import Path

from application.exceptions import ConfigNotFoundException
from application.repositories import IConfigRepository
from application.simulation_config import SimulationConfig
from application.simulation_run_id import SimulationRunId

_FIELDNAMES = ["num_elevators", "num_floors", "elevator_capacity"]


class CsvConfigRepository(IConfigRepository):
    """The CSV file is the actual source of truth for "has this run been configured",
    not just an export — get() checks the file itself, not any in-memory cache, so a run
    with no config.csv genuinely has no config as far as the rest of the system can tell."""

    def __init__(self, output_dir: Path = Path("output")) -> None:
        self._output_dir = output_dir

    def _path(self, run_id: SimulationRunId) -> Path:
        return self._output_dir / run_id.value / "config.csv"

    def get(self, run_id: SimulationRunId) -> SimulationConfig:
        path = self._path(run_id)
        if not path.exists():
            raise ConfigNotFoundException(f"no config found for simulation run {run_id.value}")
        with path.open(newline="", encoding="utf-8") as file:
            row = next(csv.DictReader(file))
        return SimulationConfig(
            num_elevators=int(row["num_elevators"]),
            num_floors=int(row["num_floors"]),
            elevator_capacity=int(row["elevator_capacity"]),
        )

    def save(self, run_id: SimulationRunId, config: SimulationConfig) -> None:
        run_dir = self._output_dir / run_id.value
        run_dir.mkdir(parents=True, exist_ok=True)
        with self._path(run_id).open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=_FIELDNAMES)
            writer.writeheader()
            writer.writerow(
                {
                    "num_elevators": config.num_elevators,
                    "num_floors": config.num_floors,
                    "elevator_capacity": config.elevator_capacity,
                }
            )
