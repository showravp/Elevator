import csv
from pathlib import Path

from application.ports import IPositionLogFileWriter
from application.read_models import PositionLogRow
from application.simulation_run_id import SimulationRunId


class CsvPositionLogFileWriter(IPositionLogFileWriter):
    """Wide format — one row per timestamp, elevator positions as columns — matching the
    take-home brief's literal wording. The JSON API response stays long/tidy (one row per
    tick+elevator pair), which is friendlier to API consumers; this is the file-shaped
    output the brief specifically asked for."""

    def __init__(self, output_dir: Path = Path("output")) -> None:
        self._output_dir = output_dir

    def write(self, run_id: SimulationRunId, rows: list[PositionLogRow]) -> str:
        run_dir = self._output_dir / run_id.value
        run_dir.mkdir(parents=True, exist_ok=True)
        path = run_dir / "position_log.csv"

        elevator_ids = sorted({row.elevator_id.value for row in rows})
        by_tick: dict[int, dict[int, int]] = {}
        for row in rows:
            by_tick.setdefault(row.tick.value, {})[row.elevator_id.value] = row.floor.value

        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["tick"] + [f"elevator_{eid}" for eid in elevator_ids])
            for tick in sorted(by_tick):
                positions = by_tick[tick]
                writer.writerow([tick] + [positions[eid] for eid in elevator_ids])

        return str(path)
